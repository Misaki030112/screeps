#!/usr/bin/env python3
"""Websocket listener: streams console + cpu + room objects from screeps.com into metrics/.
  metrics/console.log   every console line (UTC+8 stamp)      metrics/errors.log  error lines only
  metrics/metrics.jsonl STATS lines (every 10 ticks)            metrics/live.json   latest snapshot for dashboard
Run via tools/run_listener.sh (auto-restart)."""
import json, os, sys, time, threading, zlib, base64, html
import websocket
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))
from api import TOKEN, ROOT, req
ROOM, SHARD = 'W46N8', 'shard3'
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
    """alerts.jsonl: one line per new episode, severity escalation, or end. alerts_state.json: episodes keyed by id."""
    path = os.path.join(M, 'alerts_state.json')
    st = json.load(open(path)) if os.path.exists(path) else {}
    ep = st.get(a['episode'])
    a['seen'] = stamp()
    if ep is None:
        ep = st[a['episode']] = {'first': a, 'latest': a, 'severity': a.get('severity'), 'acked': False, 'ended': False, 'seen': stamp()}
        append('alerts.jsonl', json.dumps({'kind': 'new', **a}))
    else:
        if SEV.get(a.get('severity'), 0) > SEV.get(ep['severity'], 0):
            ep['severity'] = a['severity']; ep['acked'] = False
            append('alerts.jsonl', json.dumps({'kind': 'escalated', **a}))
        if a.get('ended'):
            ep['ended'] = True; append('alerts.jsonl', json.dumps({'kind': 'ended', **a}))
        ep['latest'] = a
    tmp = path + '.tmp'; json.dump(st, open(tmp, 'w'), indent=1); os.replace(tmp, path)

def decode(msg):
    if msg.startswith('gz:'): return zlib.decompress(base64.b64decode(msg[3:]), 15 + 32).decode()
    return msg
def on_message(ws, msg):
    msg = decode(msg)
    if msg.startswith('auth ok'):
        for ch in (f'user:{UID}/console', f'user:{UID}/cpu', f'room:{SHARD}/{ROOM}'): ws.send('subscribe ' + ch)
        append('console.log', f'{stamp()} [listener] subscribed'); return
    if msg.startswith('auth failed'): append('errors.log', f'{stamp()} [listener] auth failed'); ws.close(); return
    if not msg.startswith('['): return
    ch, data = json.loads(msg)
    if ch.endswith('/console'):
        if data.get('shard') not in (None, SHARD): return
        lines = (data.get('messages') or {}).get('log', []) + [f'< {r}' for r in (data.get('messages') or {}).get('results', [])]
        if data.get('error'): lines.append('[ERR] ' + data['error'])
        for l in map(html.unescape, lines):
            if l.startswith('ALERT '):
                try: handle_alert(json.loads(l[6:]))
                except Exception as ex: append('errors.log', f'{stamp()} [listener] bad ALERT {ex}: {l[:200]}')
                continue
            if l.startswith('STATS '):
                try:
                    st = json.loads(l[6:]); live['stats'] = st
                    append('metrics.jsonl', json.dumps({'ts': int(time.time()), 'src': 'ws', 'stats': st}))
                except Exception as ex: append('errors.log', f'{stamp()} [listener] bad STATS {ex}: {l[:200]}')
                continue
            append('console.log', f'{stamp()} {l}'); live['console_tail'] = (live['console_tail'] + [f'{stamp()} {l}'])[-40:]
            if '[ERR]' in l or 'Error' in l:
                append('errors.log', f'{stamp()} {l}'); live['errors_tail'] = (live['errors_tail'] + [f'{stamp()} {l}'])[-20:]
        write_live()
    elif ch.endswith('/cpu'):
        live['cpu'] = data; 
    elif ch.startswith('room:'):
        with lock:
            for oid, o in (data.get('objects') or {}).items():
                if o is None: live['objects'].pop(oid, None)
                else: live['objects'].setdefault(oid, {}).update(o)
            live['gameTime'] = data.get('gameTime', live['gameTime'])
        write_live()
def on_open(ws): ws.send('auth ' + TOKEN)
def on_error(ws, e): append('errors.log', f'{stamp()} [listener] ws error {e}')
if __name__ == '__main__':
    ws = websocket.WebSocketApp('wss://screeps.com/socket/websocket', on_open=on_open, on_message=on_message, on_error=on_error)
    ws.run_forever(ping_interval=30, ping_timeout=10)
