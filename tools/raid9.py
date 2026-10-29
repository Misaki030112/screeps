#!/usr/bin/env python3
"""Manual control for W47N9 raid9 (src/roles/raid9.js, docs/RAID_W47N9.md).
  python3 tools/raid9.py status   room-objects intel + Memory.ops.w47n9 + living raid9
  python3 tools/raid9.py arm      RESET Memory.ops.w47n9={on:true,n:0}; continuous waves until SM/abort (NEEDS APPROVAL)
  python3 tools/raid9.py abort    on=false, garrison=true (stop spawn; living fall back to W47N8 wall)
go is set in-game once ≥2 melee, or ≥2 melee+ranged, are on the W47N8 north lip (y≤3) or already in W47N9.
Healers do not have to stand on rally slots. go clears only when W47N9 is empty and no melee/ranged remain on that lip.
Does NOT deploy code. arm writes Memory only — do not run without Misaki/parent approval.
"""
import sys, os, json, time, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
import api

def _js_literal(value):
    if isinstance(value, bool): return 'true' if value else 'false'
    if value is None: return 'null'
    if isinstance(value, (int, float)): return str(value)
    return json.dumps(value, separators=(',', ':'))

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
        if any(b[t] for t in ('attack', 'ranged_attack', 'heal')):
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

def living_raid9():
    # via console — cheap
    from tools import q as Q
    # avoid circular: use api console like q.py
    return None

def status():
    print('ops', json.dumps(ops(), separators=(',', ':')))
    for room in ('W47N9', 'W48N9'):
        print(room, json.dumps(room_intel(room), separators=(',', ':')))
    # living count via console expression through q
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import q as Q
    m = Q.q("(function(){return JSON.stringify({t:Game.time,raid:_.filter(Game.creeps,c=>c.memory.role==='raid9').map(c=>({n:c.name,rm:c.room.name,x:c.pos.x,y:c.pos.y,ttl:c.ticksToLive,k:c.memory.k})),storH:Game.rooms.W46N8.storage.store.energy,bkt:Game.cpu.bucket})})()")
    print('live', m.get('v'))

def arm():
    """Fresh wave: wipe prior safe/garrison/flee/go/n."""
    print('WARNING: arming continuous waves: 2m+2r+2h (~13200E/wave) from W46N8+W47N8 until SM/abort.', file=sys.stderr)
    print(setm('ops.w47n9', {'on': True, 'n': 0}))

def abort():
    print(setm('ops.w47n9', {'on': False, 'n': ops().get('n', 4), 'garrison': True, 'flee': {'t': 0, 'why': 'abort'}}))

def main(a):
    if not a or a[0] == 'status': return status()
    if a[0] == 'arm': return arm()
    if a[0] == 'abort': return abort()
    sys.exit(__doc__)

if __name__ == '__main__':
    main(sys.argv[1:])
