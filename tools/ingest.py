"""Batched writer into TimescaleDB for the listener: one background thread, flush every 2 s or 2000 rows.
Rows are tagged with the commit of the latest deploy (refreshed every 60 s)."""
import threading, queue, time, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import db
from datetime import datetime, timezone
Q = queue.Queue()
SQL = {
 'creep_ticks': 'INSERT INTO creep_ticks (ts,tick,room,creep,role,x,y,hits,store,state,commit) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING',
 'creep_cpu': 'INSERT INTO creep_cpu (ts,tick,creep,role,cpu_ms,acts,work,repaths,stuck,target,commit) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING',
 'path_arrivals': 'INSERT INTO path_arrivals (ts,tick,creep,role,target,planned,actual,commit) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING',
 'room_stats': 'INSERT INTO room_stats (ts,tick,room,rcl,progress,progress_total,energy,energy_cap,sites,hostiles,safe_mode,cpu,bucket,trace_cpu,gcl_progress,creeps,commit) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING',
 'events': 'INSERT INTO events (ts,tick,kind,room,severity,episode,msg,data) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',
}
state = {'commit': None, 'commit_at': 0, 'rows': 0, 'last_flush': None, 'err': None}
now = lambda: datetime.now(timezone.utc)
def put(table, row): Q.put((table, row))
def commit():
    return state['commit']
def _loop(log):
    c = None
    while True:
        batch = {}; t0 = time.time(); n = 0
        while time.time() - t0 < 2 and n < 2000:
            try: t, r = Q.get(timeout=0.5); batch.setdefault(t, []).append(r); n += 1
            except queue.Empty: pass
        try:
            if c is None or c.closed: c = db.connect(autocommit=False)
            if time.time() - state['commit_at'] > 60: state['commit'] = db.current_commit(c); state['commit_at'] = time.time(); c.commit()
            if batch:
                with c.cursor() as cur:
                    for t, rows in batch.items(): cur.executemany(SQL[t], rows)
                c.commit(); state['rows'] += n; state['last_flush'] = time.time()
        except Exception as ex:
            state['err'] = str(ex)[:200]; log(f'[ingest] {ex}')
            try: c.close()
            except Exception: pass
            c = None
            for t, rows in batch.items():  # retry once later
                for r in rows: Q.put((t, r))
            time.sleep(5)
def start(log): threading.Thread(target=_loop, args=(log,), daemon=True).start()
def alert_state(a, stamp):
    """upsert alert episode (alerts.py reads alert_state)"""
    with db.connect() as c:
        r = c.execute('SELECT severity FROM alert_state WHERE episode=%s', (a['episode'],)).fetchone()
        SEV = {'low': 0, 'medium': 1, 'high': 2}
        if r is None:
            c.execute('INSERT INTO alert_state VALUES (%s,%s,%s,%s,false,%s,now())', (a['episode'], a.get('severity'), json.dumps(a), json.dumps(a), bool(a.get('ended'))))
            return 'new'
        esc = SEV.get(a.get('severity'), 0) > SEV.get(r[0], 0)
        c.execute('UPDATE alert_state SET latest=%s, severity=CASE WHEN %s THEN %s ELSE severity END, acked=CASE WHEN %s THEN false ELSE acked END, ended=ended OR %s WHERE episode=%s',
                  (json.dumps(a), esc, a.get('severity'), esc, bool(a.get('ended')), a['episode']))
        return 'escalated' if esc else 'ended' if a.get('ended') else 'update'
