#!/usr/bin/env python3
"""Manual control of the one-off W47N8 probe (src/roles/probe.js, docs/PROBE.md).
  python3 tools/probe.py status            status + hostiles in W47N8 (room-objects API) + last log lines
  python3 tools/probe.py cmd observe|steal|attack|retreat|guard
  python3 tools/probe.py cmd hold [x y [room]]   (default room W47N8; no coords = keep/ default W46N8 3,20)
  python3 tools/probe.py spawn             sets Memory.ops.probe.spawn=true (spawns once when storage>=3100)
  python3 tools/probe.py watch [sec]       poll and print changes (status, new log events, hostiles)"""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts')); import api
CMDS = {'observe', 'hold', 'steal', 'attack', 'retreat', 'guard'}

def _js_literal(value):
    if isinstance(value, bool): return 'true' if value else 'false'
    if value is None: return 'null'
    if isinstance(value, (int, float)): return str(value)
    return json.dumps(value, separators=(',', ':'))

def setm(path, value, timeout=15):
    """Set Memory.<path>=value via console, ensuring parent objects exist first.
    The memory POST API silently fails (returns ok) when a parent is missing;
    console TypeError is invisible to the API. Poll until the value is visible."""
    parts = path.split('.')
    expr_parts = []
    cur = 'Memory'
    for p in parts[:-1]:
        cur = f'{cur}.{p}'
        expr_parts.append(f'{cur}={cur}||{{}}')
    leaf = f'Memory.{".".join(parts)}'
    expr_parts.append(f'{leaf}={_js_literal(value)}')
    expr = ';'.join(expr_parts)
    r = api.req('user/console', {'expression': expr, 'shard': api.SHARD})
    if not r.get('ok'):
        print('console write failed:', r, file=sys.stderr)
        sys.exit(1)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            got = api.memory(path)
            if got == value:
                return {'ok': 1, 'path': path, 'value': value, 'verified': True}
        except KeyError:
            pass
        time.sleep(1)
    print(f'ERROR: Memory.{path} did not become {value!r} within {timeout}s', file=sys.stderr)
    try:
        print(f'  last read: {api.memory(path)!r}', file=sys.stderr)
    except Exception as ex:
        print(f'  last read error: {ex}', file=sys.stderr)
    sys.exit(1)

def probe():
    try: p = api.memory('ops.probe')
    except KeyError: return {}   # 'Incorrect memory path': Memory.ops.probe not created yet
    return p if isinstance(p, dict) else {}
def hostiles(room='W47N8'):
    objs = api.req(f'game/room-objects?room={room}&shard={api.SHARD}')
    users = {k: v.get('username') for k, v in (objs.get('users') or {}).items()}
    out = []
    for o in objs.get('objects', []):
        if o.get('type') == 'creep':
            body = {}
            for p in o.get('body', []): body[p['type']] = body.get(p['type'], 0) + 1
            out.append((users.get(o.get('user'), o.get('user')), o.get('name'), o['x'], o['y'], o.get('hits'), body))
        elif o.get('type') == 'tower': out.append((users.get(o.get('user')), 'TOWER', o['x'], o['y'], (o.get('store') or {}).get('energy'), {}))
    return out
def status(n_log=15):
    p = probe(); print('status', json.dumps(p.get('status')), '| cmd', p.get('cmd'), '| spawn', p.get('spawn'), '| spawned', p.get('spawned'), '| auto', p.get('auto'), '| stolen', p.get('stolen'))
    for h in hostiles(): print('  W47N8', h)
    for e in (p.get('log') or [])[-n_log:]: print('  log', json.dumps(e))
def main(a):
    if not a or a[0] == 'status': return status()
    if a[0] == 'spawn': print(setm('ops.probe.spawn', True)); return
    if a[0] == 'cmd':
        c = a[1]
        if c not in CMDS: sys.exit(f'unknown cmd {c}; one of {sorted(CMDS)}')
        if c == 'hold' and len(a) >= 4: print(setm('ops.probe.pos', {'x': int(a[2]), 'y': int(a[3]), 'room': a[4] if len(a) > 4 else 'W47N8'}))
        print(setm('ops.probe.cmd', c)); return
    if a[0] == 'watch':
        dt = float(a[1]) if len(a) > 1 else 5; last_t, last_st, last_h = None, None, None
        while True:
            try:
                p = probe(); st = p.get('status') or {}; key = (st.get('room'), tuple(st.get('pos') or []), st.get('hits'), st.get('cmd'))
                if key != last_st: print(time.strftime('%H:%M:%S'), 'status', json.dumps(st)); last_st = key
                for e in p.get('log') or []:
                    if last_t is None or e['t'] > last_t: print(time.strftime('%H:%M:%S'), 'LOG', json.dumps(e))
                if p.get('log'): last_t = p['log'][-1]['t']
                h = hostiles(); hk = sorted((x[0], x[1]) for x in h)
                if hk != last_h: print(time.strftime('%H:%M:%S'), 'W47N8 creeps:', [f'{x[0]}:{x[1]}@{x[2]},{x[3]} {x[5]}' for x in h]); last_h = hk
            except Exception as ex: print('err', ex)
            time.sleep(dt)
    sys.exit(__doc__)
if __name__ == '__main__': main(sys.argv[1:])
