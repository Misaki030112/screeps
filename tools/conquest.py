#!/usr/bin/env python3
"""Manual control of the W47N8 conquest (src/roles/conquest.js, docs/CONQUEST.md).

  python3 tools/conquest.py status
  python3 tools/conquest.py cmd hold|go|retreat
  python3 tools/conquest.py spawn          # Memory.ops.cq.spawn=true  (squad of cq.squadMax, default 2)
  python3 tools/conquest.py claim          # Memory.ops.cq.claim=true   (breakers + workers)
  python3 tools/conquest.py autoSafe on|off
  python3 tools/conquest.py set <key> <json-value>   # e.g. set squadMax 2, set breakers 3, set workers 4
  python3 tools/conquest.py watch [sec]

Writes always create parent keys (Memory.ops, Memory.ops.cq) and poll until the value is visible.
Nothing is deployed by this tool; the in-game code must already be live.
"""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts')); import api
CMDS = {'hold', 'go', 'retreat'}

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
        print('console write failed:', r, file=sys.stderr); sys.exit(1)
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
    try: print(f'  last read: {api.memory(path)!r}', file=sys.stderr)
    except Exception as ex: print(f'  last read error: {ex}', file=sys.stderr)
    sys.exit(1)

def cq():
    try: p = api.memory('ops.cq')
    except KeyError: return {}
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
        elif o.get('type') == 'controller':
            out.append(('ctrl', o.get('reservation'), o.get('level'), o.get('owner'), o.get('safeModeAvailable'), o.get('safeMode')))
        elif o.get('type') == 'tower':
            out.append((users.get(o.get('user')), 'TOWER', o['x'], o['y'], (o.get('store') or {}).get('energy'), {}))
    return out

def status(n_log=20):
    p = cq()
    print('cmd', p.get('cmd'), '| spawn', p.get('spawn'), '| claim', p.get('claim'),
          '| autoSafe', p.get('autoSafe'), '| respawn', p.get('respawn'),
          '| squadMax', p.get('squadMax'), '| breakers', p.get('breakers'), '| workers', p.get('workers'),
          '| claimed', p.get('claimed'), '| broke', p.get('broke'), '| auto', p.get('auto'))
    st = p.get('status') or {}
    for role, creeps in st.items():
        if isinstance(creeps, dict):
            for name, s in creeps.items():
                print(f'  {role} {name}', json.dumps(s))
    for h in hostiles(): print('  W47N8', h)
    for e in (p.get('log') or [])[-n_log:]: print('  log', json.dumps(e))

def main(a):
    if not a or a[0] == 'status': return status()
    if a[0] == 'spawn': print(setm('ops.cq.spawn', True)); return
    if a[0] == 'claim': print(setm('ops.cq.claim', True)); return
    if a[0] == 'autoSafe':
        if len(a) < 2 or a[1] not in ('on', 'off'): sys.exit('autoSafe on|off')
        print(setm('ops.cq.autoSafe', a[1] == 'on')); return
    if a[0] == 'cmd':
        c = a[1] if len(a) > 1 else ''
        if c not in CMDS: sys.exit(f'unknown cmd {c}; one of {sorted(CMDS)}')
        print(setm('ops.cq.cmd', c)); return
    if a[0] == 'set':
        if len(a) < 3: sys.exit('set <key> <json-value>')
        key, raw = a[1], a[2]
        try: val = json.loads(raw)
        except Exception:
            if raw in ('true', 'false'): val = raw == 'true'
            elif raw.isdigit(): val = int(raw)
            else: val = raw
        print(setm(f'ops.cq.{key}', val)); return
    if a[0] == 'watch':
        dt = float(a[1]) if len(a) > 1 else 5; last_t, last_st, last_h = None, None, None
        while True:
            try:
                p = cq(); st = p.get('status') or {}
                key = json.dumps(st, sort_keys=True)
                if key != last_st: print(time.strftime('%H:%M:%S'), 'status', key[:300]); last_st = key
                for e in p.get('log') or []:
                    if last_t is None or e['t'] > last_t: print(time.strftime('%H:%M:%S'), 'LOG', json.dumps(e))
                if p.get('log'): last_t = p['log'][-1]['t']
                h = hostiles(); hk = str(h)
                if hk != last_h: print(time.strftime('%H:%M:%S'), 'W47N8:', h); last_h = hk
            except Exception as ex: print('err', ex)
            time.sleep(dt)
    sys.exit(__doc__)

if __name__ == '__main__':
    main(sys.argv[1:])
