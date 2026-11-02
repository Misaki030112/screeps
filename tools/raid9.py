#!/usr/bin/env python3
"""Manual control for the W47N9 wartime raid (src/roles/raid9.js, docs/RAID_W47N9.md).

  python3 tools/raid9.py status                 intel + Memory.ops.w47n9 + living raid9
  python3 tools/raid9.py defaults               print the arm payload (no Memory write)
  python3 tools/raid9.py arm                    RESET ops.w47n9 to the wartime knobs (NEEDS APPROVAL)
  python3 tools/raid9.py abort                  on=false, garrison, flee.why=abort
  python3 tools/raid9.py set phase=punch max.d=4 pullSoft=0.7 pauseSpawn=false
  python3 tools/raid9.py set 'mouths=[{"x":38,"y":42}]'
  python3 tools/raid9.py pause                  pauseCivilians=true
  python3 tools/raid9.py resume-civ             pauseCivilians=false
  python3 tools/raid9.py order NAME moveTo=38,43,W47N9 dismantle=38,42 until=500
  python3 tools/raid9.py clear NAME             raidOrder={clear:true}

Does NOT deploy code. arm/set/order/abort write Memory only.
Do not run arm without Misaki/parent approval. The bot never activates safe mode.
"""
import sys, os, json, time, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
import api

# Spec healer is 18H18M (5400). RCL7 cap is 5300, so the room spawns 17H17M until cap >= 5400.
DEFAULT_OPS = {
    'on': True,
    'n': 0,
    'phase': 'breach',
    'need': {'d': 2, 'm': 0, 'r': 0, 'h': 0},
    'max': {'d': 4, 'm': 6, 'r': 6, 'h': 10},
    'mouths': [{'x': 38, 'y': 42}, {'x': 39, 'y': 42}],
    'focusSeal': {'x': 38, 'y': 42},
    'minDps': 1240,
    'towerOrder': [{'x': 39, 'y': 37}, {'x': 34, 'y': 28}],
    'prio': ['fight', 'filler', 'towerRampart', 'tower', 'blocker', 'econ'],
    'kite': True,
    'pullSoft': 0.70,
    'pullHard': 0.45,
    'maxY43': 2,
    'pauseSpawn': False,
    'pauseCivilians': True,
    'note': 'wartime east line; arm after deploy; no auto safe mode',
}

def _js_literal(value):
    if isinstance(value, bool): return 'true' if value else 'false'
    if value is None: return 'null'
    if isinstance(value, (int, float)): return str(value)
    return json.dumps(value, separators=(',', ':'))

def parse_value(s):
    if s in ('true', 'True'): return True
    if s in ('false', 'False'): return False
    if s in ('null', 'None'): return None
    if s[:1] in '[{': return json.loads(s)
    try:
        if '.' in s: return float(s)
        return int(s)
    except ValueError:
        return s

def setm(path, value, timeout=20):
    parts = path.split('.')
    expr_parts, cur = [], 'Memory'
    for p in parts[:-1]:
        cur = f'{cur}.{p}'
        expr_parts.append(f'{cur}={cur}||{{}}')
    leaf = f'Memory.{".".join(parts)}'
    expr_parts.append(f'{leaf}={_js_literal(value)}')
    r = api.req('user/console', {'expression': ';'.join(expr_parts), 'shard': api.SHARD})
    if not r.get('ok'):
        print('console write failed:', r, file=sys.stderr); sys.exit(1)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            got = api.memory(path)
            if got == value: return {'ok': 1, 'path': path, 'value': value}
        except KeyError: pass
        time.sleep(1)
    print(f'ERROR: Memory.{path} did not become {value!r}', file=sys.stderr); sys.exit(1)

def ops():
    try:
        o = api.memory('ops.w47n9')
        return o if isinstance(o, dict) else {}
    except KeyError:
        return {}

def room_intel(room='W47N9'):
    o = api.req(f'game/room-objects?room={room}&shard={api.SHARD}')
    U = {k: v.get('username') for k, v in (o.get('users') or {}).items()}
    by = collections.defaultdict(list)
    for x in o.get('objects', []): by[x['type']].append(x)
    ctl = (by.get('controller') or [{}])[0]
    tw = [(t['x'], t['y'], (t.get('store') or {}).get('energy', 0)) for t in by.get('tower', [])]
    walls = by.get('constructedWall', []); ramps = by.get('rampart', [])
    wh = [w.get('hits', 0) for w in walls]; rh = [r.get('hits', 0) for r in ramps]
    combat = []
    for c in by.get('creep', []):
        b = collections.Counter(p['type'] for p in c.get('body', []))
        if any(b[t] for t in ('attack', 'ranged_attack', 'heal', 'work')):
            combat.append({'name': c['name'], 'user': U.get(c.get('user')), 'body': dict(b), 'x': c['x'], 'y': c['y']})
    ext_e = sum((x.get('store') or {}).get('energy', 0) for x in by.get('extension', []))
    sp_e = sum((x.get('store') or {}).get('energy', 0) for x in by.get('spawn', []))
    st = by.get('storage') or []
    return {
        'owner': U.get(ctl.get('user')), 'rcl': ctl.get('level'),
        'safeMode': ctl.get('safeMode'), 'safeModeAvailable': ctl.get('safeModeAvailable'),
        'safeModeCooldown': ctl.get('safeModeCooldown'),
        'towers': tw, 'walls': len(walls), 'wMin': min(wh) if wh else None,
        'ramps': len(ramps), 'rMin': min(rh) if rh else None, 'rMed': sorted(rh)[len(rh)//2] if rh else None,
        'extE': ext_e, 'spawnE': sp_e,
        'storageE': (st[0].get('store') or {}).get('energy') if st else None,
        'creeps': len(by.get('creep', [])), 'combat': combat,
    }

def status():
    print('ops', json.dumps(ops(), separators=(',', ':')))
    for room in ('W47N9', 'W48N9'):
        print(room, json.dumps(room_intel(room), separators=(',', ':')))
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import q as Q
    m = Q.q("(function(){return JSON.stringify({t:Game.time,ops:Memory.ops&&Memory.ops.w47n9,raid:_.filter(Game.creeps,c=>c.memory.role==='raid9').map(c=>({n:c.name,k:c.memory.kind,rm:c.room.name,x:c.pos.x,y:c.pos.y,ttl:c.ticksToLive,ord:c.memory.raidOrder||null})),bkt:Game.cpu.bucket})})()")
    print('live', m.get('v'))

def arm():
    print('WARNING: arming W47N9 wartime field d4 m6 r6 h10 from W46N8+W47N8. Civilians pause. No safe mode.', file=sys.stderr)
    print('Healer spec 18H18M=5400; RCL7 spawns 17H17M=5100. This writes Memory only.', file=sys.stderr)
    print(setm('ops.w47n9', DEFAULT_OPS))

def abort():
    cur = ops()
    print(setm('ops.w47n9', {
        'on': False, 'n': cur.get('n', 0), 'garrison': True,
        'flee': {'t': 0, 'why': 'abort'}, 'phase': 'fallback', 'pauseSpawn': True,
        'note': cur.get('note', ''),
    }))

def cmd_set(args):
    if not args: sys.exit('set key=value ...')
    for a in args:
        if '=' not in a: sys.exit('expected key=value: ' + a)
        k, v = a.split('=', 1)
        print(setm('ops.w47n9.' + k, parse_value(v)))

def _xy(v):
    parts = v.split(',')
    if len(parts) >= 2 and parts[0].lstrip('-').isdigit():
        o = {'x': int(parts[0]), 'y': int(parts[1])}
        if len(parts) >= 3: o['room'] = parts[2]
        return o
    return v

def cmd_order(args):
    if len(args) < 2: sys.exit('order CREEP moveTo=38,43,W47N9 [attack=ID|x,y] [dismantle=] [heal=self|lowest|ID] [hold=true] [until=TICK]')
    name, order = args[0], {}
    for a in args[1:]:
        if '=' not in a: sys.exit('expected key=value: ' + a)
        k, v = a.split('=', 1)
        if k in ('moveTo', 'attack', 'dismantle', 'heal') and ',' in v:
            order[k] = _xy(v)
        elif k in ('hold', 'clear'):
            order[k] = parse_value(v)
        elif k == 'until':
            order[k] = int(v)
        else:
            order[k] = parse_value(v)
    print(setm('creeps.' + name + '.raidOrder', order))

def cmd_clear(args):
    if not args: sys.exit('clear CREEP')
    print(setm('creeps.' + args[0] + '.raidOrder', {'clear': True}))

def main(a):
    if not a or a[0] == 'status': return status()
    if a[0] == 'defaults': return print(json.dumps(DEFAULT_OPS, indent=2))
    if a[0] == 'arm': return arm()
    if a[0] == 'abort': return abort()
    if a[0] == 'set': return cmd_set(a[1:])
    if a[0] == 'pause': return print(setm('ops.w47n9.pauseCivilians', True))
    if a[0] == 'resume-civ': return print(setm('ops.w47n9.pauseCivilians', False))
    if a[0] == 'order': return cmd_order(a[1:])
    if a[0] == 'clear': return cmd_clear(a[1:])
    sys.exit(__doc__)

if __name__ == '__main__':
    main(sys.argv[1:])
