#!/usr/bin/env python3
"""Websocket listener: streams console + cpu + room objects from screeps.com into metrics/.
  metrics/console.log   every console line (UTC+8 stamp)      metrics/errors.log  error lines only
  TimescaleDB (tools/ingest.py): creep_ticks, creep_cpu, path_arrivals, room_stats, events, alert_state            metrics/live.json   latest snapshot for dashboard
Run via tools/run_listener.sh (auto-restart)."""
import json, os, sys, time, threading, zlib, base64, html
import websocket
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ingest
from ingest import now as utcnow
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))
from api import TOKEN, ROOT, req
ROOM, SHARD = 'W46N8', 'shard3'
WATCH = 'W45N8'  # remote: watch events + creep trail
TRAIL = ('W45N7', 'W47N8')  # other remotes: creep trail only (creep_ticks), not mixed into live.json
# The server delivers at most 2 room subscriptions per user per tick: with 3 it answers 'err@room:… subscribe limit reached'
# in rotation and every room loses ~25-60% of ticks (test 10-17 01:35: 2 rooms 10/10 ticks, 3 rooms 7-8/10 each; home coverage
# fell ~95% -> 35-70% after W45N7 was added 16:25). So: ROOM always, plus ONE remote slot rotating WATCH / TRAIL rooms.
# W47N8 (claimed 10-18 15:18, developing) gets the longest slot: Misaki diagnoses its creeps from DB trajectory history,
# and it was missing from ROT (0 creep_ticks rows for W47N8 until 10-18 16:2x).
ROT = (('W47N8', 600), (WATCH, 300), ('W45N7', 150))  # (room, seconds held)
rot = {'i': 0}
watch = {'objects': {}, 'last': None}
M = os.path.join(ROOT, 'metrics'); os.makedirs(M, exist_ok=True)
UID = req('auth/me')['_id']
live = {'uid': None, 'stats': None, 'cpu': None, 'objects': {}, 'gameTime': None, 'console_tail': [], 'errors_tail': [], 'updated': None}
live['uid'] = UID
lock = threading.Lock()
stamp = lambda: time.strftime('%F %T')
def write_live():
    tmp = os.path.join(M, 'live.json.tmp')
    with lock:
        live['updated'] = stamp()
        json.dump(live, open(tmp, 'w'))
    os.replace(tmp, os.path.join(M, 'live.json'))
def append(fn, line):
    with open(os.path.join(M, fn), 'a') as f: f.write(line + '\n')
SEV = {'low': 0, 'medium': 1, 'high': 2}
def handle_alert(a):
    """alert episodes -> alert_state table (alerts.py) + events table"""
    kind = ingest.alert_state(a, stamp())
    if kind != 'update': ingest.put('events', (utcnow(), a.get('tick'), 'alert_' + kind, a.get('room'), a.get('severity'), a.get('episode'), a.get('owner'), json.dumps(a)))

def decode(msg):
    if msg.startswith('gz:'): return zlib.decompress(base64.b64decode(msg[3:]), 15 + 32).decode()
    return msg
def on_message(ws, msg):
    msg = decode(msg)
    if msg.startswith('auth ok'):
        for ch in (f'user:{UID}/console', f'user:{UID}/cpu', f'room:{SHARD}/{ROOM}'): ws.send('subscribe ' + ch)
        sub_remote(ws, ROT[rot['i']][0])
        append('console.log', f'{stamp()} [listener] subscribed'); return
    if msg.startswith('auth failed'): append('errors.log', f'{stamp()} [listener] auth failed'); ws.close(); return
    if not msg.startswith('['): return
    ch, data = json.loads(msg)
    if not isinstance(data, dict):  # e.g. ['err@room:shard3/W45N7', 'subscribe limit reached']
        errs[ch] = errs.get(ch, 0) + 1
        if errs[ch] in (1, 100) or errs[ch] % 1000 == 0: append('errors.log', f'{stamp()} [listener] {ch}: {str(data)[:100]} (x{errs[ch]})')
        return
    if ch.endswith('/console'):
        if data.get('shard') not in (None, SHARD): return
        lines = (data.get('messages') or {}).get('log', []) + [f'< {r}' for r in (data.get('messages') or {}).get('results', [])]
        if data.get('error'): lines.append('[ERR] ' + data['error'])
        for l in map(html.unescape, lines):
            if l.startswith('ALERT '):
                try: handle_alert(json.loads(l[6:]))
                except Exception as ex: append('errors.log', f'{stamp()} [listener] bad ALERT {ex}: {l[:200]}')
                continue
            if l.startswith('INCIDENT '):
                try:
                    a = json.loads(l[9:])
                    ingest.put('incidents', (utcnow(), a.get('tick'), a.get('remote'), a.get('inc'), a.get('ev'), a.get('from'), a.get('state'), a.get('why'),
                        a.get('inv'), a.get('invTtl'), a.get('def'), a.get('dur'), json.dumps(a)))
                except Exception as ex: append('errors.log', f'{stamp()} [listener] bad INCIDENT {ex}: {l[:200]}')
                append('console.log', f'{stamp()} {l}'); continue
            if l.startswith('CS '):
                append('creep_samples.jsonl', l[3:]); continue
            if l.startswith('STATS '):
                try:
                    st = json.loads(l[6:]); live['stats'] = st; last_stats[0] = time.time()
                    for rn, rm in (st.get('rooms') or {}).items():
                        ingest.put('room_stats', (utcnow(), st.get('t'), rn, rm.get('rcl'), rm.get('progress'), rm.get('progressTotal'), rm.get('energy'), rm.get('energyCap'),
                            rm.get('sites'), rm.get('hostiles'), rm.get('safeMode'), st.get('cpu'), st.get('b'), st.get('tr'), (st.get('gcl') or {}).get('progress'), json.dumps(st.get('creeps')), ingest.commit(), rm.get('storage'), rm.get('ctl'), rm.get('ctlEma')))
                except Exception as ex: append('errors.log', f'{stamp()} [listener] bad STATS {ex}: {l[:200]}')
                continue
            k = l.split(' ', 1)[0]
            if k in ('STUCK', 'LAYOUT') or '[ERR]' in l or 'Error' in l:
                ingest.put('events', (utcnow(), live.get('gameTime'), 'error' if k not in ('STUCK', 'LAYOUT') else k.lower(), None, None, None, l[:2000], None))
            append('console.log', f'{stamp()} {l}'); live['console_tail'] = (live['console_tail'] + [f'{stamp()} {l}'])[-40:]
            if '[ERR]' in l or 'Error' in l:
                append('errors.log', f'{stamp()} {l}'); live['errors_tail'] = (live['errors_tail'] + [f'{stamp()} {l}'])[-20:]
        write_live()
    elif ch.endswith('/cpu'):
        live['cpu'] = data; 
    elif ch == f'room:{SHARD}/{WATCH}':
        record_room(WATCH, data)
        for oid, o in (data.get('objects') or {}).items():
            if o is None: watch['objects'].pop(oid, None)
            else: watch['objects'].setdefault(oid, {}).update(o)
        cre = sorted((o.get('user'), o.get('name')) for o in watch['objects'].values() if o.get('type') == 'creep')
        cont = [(o.get('store') or {}).get('energy') for o in watch['objects'].values() if o.get('type') == 'container']
        ctl = [o.get('reservation') for o in watch['objects'].values() if o.get('type') == 'controller']
        snap = json.dumps({'creeps': cre, 'container': cont, 'reservation': ctl})
        if snap != watch['last']:
            watch['last'] = snap
            ingest.put('events', (utcnow(), data.get('gameTime'), 'watch', WATCH, None, None, None, json.dumps({'creeps': cre, 'container': cont, 'reservation': ctl})))
    elif ch.split('/')[-1] in TRAIL:
        record_room(ch.split('/')[-1], data)
    elif ch.startswith('room:'):
        record_room(ch.split('/')[-1], data)
        with lock:
            for oid, o in (data.get('objects') or {}).items():
                if o is None: live['objects'].pop(oid, None)
                else: live['objects'].setdefault(oid, {}).update(o)
            live['gameTime'] = data.get('gameTime', live['gameTime'])
        write_live()
last_stats = [time.time()]
errs = {}
def sub_remote(ws, room):
    """(re)subscribe the single remote slot; drop cached objects so a returning room never replays stale creeps"""
    rooms_state.pop(room, None)
    if room == WATCH: watch['objects'] = {}
    ws.send(f'subscribe room:{SHARD}/{room}')
def rotator(ws):
    while True:
        time.sleep(ROT[rot['i']][1])
        old = ROT[rot['i']][0]; rot['i'] = (rot['i'] + 1) % len(ROT)
        try: ws.send(f'unsubscribe room:{SHARD}/{old}'); sub_remote(ws, ROT[rot['i']][0])
        except Exception as ex: append('errors.log', f'{stamp()} [listener] rotate {ex}')
# ---- continuous telemetry: every creep, every room update (no in-game CPU) ----
rooms_state = {}  # room -> {oid: obj}
role_of = lambda n: ''.join(ch for ch in (n or '') if ch.isalpha()) or None
def record_room(room, data):
    st = rooms_state.setdefault(room, {})
    for oid, o in (data.get('objects') or {}).items():
        if o is None: st.pop(oid, None)
        elif oid in st: st[oid].update(o)
        else: st[oid] = dict(o)
    t = data.get('gameTime')
    if t is None: return
    ts, cm = utcnow(), ingest.commit()
    for o in st.values():
        if o.get('type') == 'creep' and o.get('user') == UID:
            e = (o.get('store') or {}).get('energy') or 0
            ingest.put('creep_ticks', (ts, t, room, o.get('name'), role_of(o.get('name')), o.get('x'), o.get('y'), o.get('hits'), e,
                                       'spawning' if o.get('spawning') else ('loaded' if e else 'empty'), cm))
SEG = 90
polls = [0]
# The ring buffer holds the last 300 ticks and is re-read every 60 s, and ts is part of the hypertable unique key,
# so dedup happens here: only windows/arrivals newer than the last ingested tick are written.
seen = {'cpu': None, 'arr': None}
def seed_seen():
    try:
        with ingest.db.connect() as c:
            seen['cpu'] = c.execute("SELECT max(tick) FROM creep_cpu WHERE ts > now() - interval '2 hours'").fetchone()[0] or 0
            seen['arr'] = c.execute("SELECT max(tick) FROM path_arrivals WHERE ts > now() - interval '2 hours'").fetchone()[0] or 0
    except Exception as ex: append('errors.log', f'{stamp()} [listener] seed_seen {ex}'); seen['cpu'] = seen['arr'] = 0
def segment_poller():
    """in-game per-creep CPU/intent windows: memory segment 90 ring buffer, polled every 60 s (dedup by last tick)."""
    while True:
        try:
            if seen['cpu'] is None: seed_seen()
            d = req(f'user/memory-segment?segment={SEG}&shard={SHARD}').get('data')
            if d:
                j = json.loads(d); ts, cm = utcnow(), ingest.commit()
                mc, ma = seen['cpu'], seen['arr']
                for t, rows in j.get('s', []):
                    if t <= mc: continue
                    for r in rows:
                        n, cpu, acts, work, rp, stk, tgt = r[:7]
                        ingest.put('creep_cpu', (ts, t, n, role_of(n), cpu / 100, acts, work, rp, stk, tgt, cm, r[7] if len(r) > 7 else None, r[8] if len(r) > 8 else None,
                                                  r[9] if len(r) > 9 else None, r[10] / 100 if len(r) > 10 else None))
                    seen['cpu'] = max(seen['cpu'], t)
                # arrivals are appended in tick order; same-tick arrivals arrive in the same poll
                for t, n, role, tgt, plan, act in j.get('a', []):
                    if t <= ma: continue
                    ingest.put('path_arrivals', (ts, t, n, role, tgt, plan, act, cm)); seen['arr'] = max(seen['arr'], t)
        except Exception as ex: append('errors.log', f'{stamp()} [listener] segment poll {ex}')
        time.sleep(60)
        polls[0] += 1
        if polls[0] % PROF_EVERY == 0: prof_poll()
        if polls[0] % 10 == 0:  # creep audit + heatmaps every ~10 min (prune once a day)
            import subprocess
            subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'creep_audit.py')], capture_output=True, timeout=300)
# GET user/memory is capped at 1440/day for the whole account (patrols, alerts and tools share it). 3 calls every 5 min here
# were 864/day, so the budget ran out at ~19:55 on 10-20 (HTTP 429 for ~50 min, patrols blind). Now 1 call every 15 min
# (96/day); tick and bucket come from the websocket STATS line, which is free (strategy review 10-20 20:4x, docs/CPU.md).
PROF_EVERY = 15
def prof_poll():
    """Memory.stats.prof (per-section CPU EMA) -> cpu_prof every ~15 min; was only readable live (docs/CPU.md 2026-10-20)."""
    try:
        from api import memory
        st = live.get('stats') or {}
        p, t, b = memory('stats.prof') or {}, st.get('t'), st.get('b')
        ts, cm = utcnow(), ingest.commit()
        for k, v in p.items():
            if isinstance(v, (int, float)): ingest.put('cpu_prof', (ts, t, k, v, b, cm))
    except Exception as ex: append('errors.log', f'{stamp()} [listener] prof poll {ex}')
STALE_S = 180  # STATS arrive every 10 ticks (~40 s); a silent-but-alive socket gets closed so run_listener.sh reconnects
def watchdog(ws):
    while True:
        time.sleep(30)
        if time.time() - last_stats[0] > STALE_S:
            append('errors.log', f'{stamp()} [listener] no STATS for {int(time.time()-last_stats[0])}s, reconnecting')
            ws.close(); os._exit(0)
def on_open(ws): ws.send('auth ' + TOKEN)
def on_error(ws, e): append('errors.log', f'{stamp()} [listener] ws error {e}')
if __name__ == '__main__':
    # One listener only (10-19 23:05-23:35 a second listener.py doubled creep_ticks/creep_cpu rows and raced live.json).
    # To restart, kill the running listener.py; tools/run_listener.sh relaunches it within 10 s.
    import fcntl
    _single = open(os.path.join(M, 'listener.lock'), 'w')
    try: fcntl.flock(_single, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError: print(f'{stamp()} another listener.py holds metrics/listener.lock; exiting', flush=True); sys.exit(0)
    ws = websocket.WebSocketApp('wss://screeps.com/socket/websocket', on_open=on_open, on_message=on_message, on_error=on_error)
    threading.Thread(target=watchdog, args=(ws,), daemon=True).start()
    threading.Thread(target=rotator, args=(ws,), daemon=True).start()
    ingest.start(lambda m: append('errors.log', f'{stamp()} [listener] {m}'))
    threading.Thread(target=segment_poller, daemon=True).start()
    ws.run_forever(ping_interval=30, ping_timeout=10)
