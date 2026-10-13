"""One-off: migrate metrics/ts.sqlite + metrics/*.jsonl + alerts_state.json into TimescaleDB (idempotent-ish via ON CONFLICT)."""
import os, sys, json, sqlite3
from datetime import datetime, timezone, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import db
M = os.path.join(db.ROOT, 'metrics'); c = db.connect(autocommit=False); cur = c.cursor()
role_of = lambda n: ''.join(ch for ch in (n or '') if ch.isalpha()) or None
U = lambda t: datetime.fromtimestamp(t, timezone.utc)
L = lambda s: datetime.strptime(s, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone(timedelta(hours=8)))
s = sqlite3.connect(os.path.join(M, 'ts.sqlite'))
deps = s.execute('SELECT tick, ts, gitcommit, note FROM deploys').fetchall()
for t, ts, h, note in deps: cur.execute('INSERT INTO deploys VALUES (%s,%s,%s,%s)', (U(ts), t, h, note))
cm = lambda tick: next((h for t, _, h, _ in sorted(deps, reverse=True) if tick >= t), None)
rows = s.execute('SELECT tick, room, name, x, y, hits, e, ts FROM pos').fetchall()
cur.executemany('INSERT INTO creep_ticks (ts,tick,room,creep,role,x,y,hits,store,state,commit) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING',
                [(U(ts), t, r, n, role_of(n), x, y, h, e, 'loaded' if e else 'empty', cm(t)) for t, r, n, x, y, h, e, ts in rows]); print('creep_ticks', len(rows))
# tick -> ts map from pos for cpu rows
tmap = dict(s.execute('SELECT tick, min(ts) FROM pos GROUP BY tick').fetchall()); ticks = sorted(tmap)
def tts(t):
    import bisect; i = min(bisect.bisect_left(ticks, t), len(ticks) - 1); return U(tmap[ticks[i]] + (t - ticks[i]) * 3)
rows = s.execute('SELECT tick, name, cpu, acts, work, rp, st, tgt FROM cpu').fetchall()
cur.executemany('INSERT INTO creep_cpu (ts,tick,creep,role,cpu_ms,acts,work,repaths,stuck,target,commit) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING',
                [(tts(t), t, n, role_of(n), cp / 100, a, w, rp, st, tg, cm(t)) for t, n, cp, a, w, rp, st, tg in rows]); print('creep_cpu', len(rows))
rows = s.execute('SELECT tick, name, role, tgt, plan, actual FROM arr').fetchall()
cur.executemany('INSERT INTO path_arrivals VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING', [(tts(t), t, n, r, tg, p, a, cm(t)) for t, n, r, tg, p, a in rows]); print('arrivals', len(rows))
n = 0
for line in open(os.path.join(M, 'metrics.jsonl')):
    try: r = json.loads(line)
    except Exception: continue
    st = r.get('stats') or {}; t = st.get('t') or st.get('time'); ts = U(r['ts'])
    for rn, rm in (st.get('rooms') or {}).items():
        cur.execute('INSERT INTO room_stats (ts,tick,room,rcl,progress,progress_total,energy,energy_cap,sites,hostiles,safe_mode,cpu,bucket,trace_cpu,gcl_progress,creeps,commit) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING',
            (ts, t, rn, rm.get('rcl'), rm.get('progress'), rm.get('progressTotal'), rm.get('energy'), rm.get('energyCap'), rm.get('sites'), rm.get('hostiles'), rm.get('safeMode'),
             st.get('cpu'), st.get('b', st.get('bucket')), st.get('tr'), (st.get('gcl') or {}).get('progress'), json.dumps(st.get('creeps')), None)); n += 1
    if 'world' in r: cur.execute('INSERT INTO events (ts,tick,kind,msg,data) VALUES (%s,%s,%s,%s,%s)', (ts, t, 'collect', r['world'], json.dumps({'errors': st.get('errors')})))
print('room_stats', n)
p = os.path.join(M, 'alerts.jsonl')
if os.path.exists(p):
    for line in open(p):
        a = json.loads(line); cur.execute('INSERT INTO events (ts,tick,kind,room,severity,episode,msg,data) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',
            (L(a['seen']) if a.get('seen') else U(0), a.get('tick'), 'alert_' + a.get('kind', 'new'), a.get('room'), a.get('severity'), a.get('episode'), a.get('owner'), line))
p = os.path.join(M, 'alerts_state.json')
if os.path.exists(p):
    for k, v in json.load(open(p)).items():
        cur.execute('INSERT INTO alert_state VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (episode) DO NOTHING', (k, v['severity'], json.dumps(v['first']), json.dumps(v['latest']), v['acked'], v['ended'], L(v['seen'])))
p = os.path.join(M, 'w45n8_activity.jsonl')
if os.path.exists(p):
    for line in open(p):
        a = json.loads(line); cur.execute('INSERT INTO events (ts,tick,kind,room,msg,data) VALUES (%s,%s,%s,%s,%s,%s)', (L(a['t']), a.get('tick'), 'watch', 'W45N8', None, line))
c.commit(); print('done')
