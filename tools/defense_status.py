#!/usr/bin/env python3
"""Defence snapshot for strategy/patrol: tower energy, ramparts, safe mode, remote pause, invaderHarvested, neighbours."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import api

RAMPART_TARGET = [0, 0, 0, 20000, 50000, 100000, 300000, 1000000, 3000000]
HOME, REMOTE = 'W46N8', 'W45N8'

def main():
    t = api.req('game/time?shard=shard3')['time']
    home = api.req(f'game/room-objects?room={HOME}&shard=shard3').get('objects', [])
    remote = api.req(f'game/room-objects?room={REMOTE}&shard=shard3').get('objects', [])
    try: mem_r = api.memory('remote') or {}
    except Exception: mem_r = {}
    out = {'tick': t, 'home': HOME, 'remote': REMOTE}
    ctl = next((o for o in home if o.get('type') == 'controller'), {})
    rcl = ctl.get('level') or 0
    out['rcl'] = rcl
    out['progress'] = ctl.get('progress')
    out['safeMode'] = max(0, (ctl.get('safeMode') or 0) - t) if ctl.get('safeMode') else 0
    out['safeModeAvailable'] = ctl.get('safeModeAvailable') or 0
    out['safeModeRule'] = 'NEVER auto-activate; alert Misaki'
    towers = [o for o in home if o.get('type') == 'tower']
    out['towers'] = [{'x': o['x'], 'y': o['y'], 'energy': (o.get('store') or {}).get('energy', 0)} for o in towers]
    target = RAMPART_TARGET[rcl] if rcl < len(RAMPART_TARGET) else RAMPART_TARGET[-1]
    ramps = [o for o in home if o.get('type') == 'rampart']
    out['ramparts'] = [{'x': o['x'], 'y': o['y'], 'hits': o.get('hits'), 'target': target} for o in ramps]
    out['rampartTarget'] = target
    out['homeInvaderHarvested'] = [o.get('invaderHarvested') for o in home if o.get('type') == 'source']
    inv = [o for o in remote if o.get('type') == 'creep' and str(o.get('user')) == '2']
    out['remoteInvaders'] = [{'x': o['x'], 'y': o['y'], 'hits': o.get('hits'), 'ttl': o.get('ticksToLive'),
                              'body': [p.get('type') for p in (o.get('body') or [])]} for o in inv]
    rctl = next((o for o in remote if o.get('type') == 'controller'), {})
    out['remoteReservation'] = rctl.get('reservation')
    rsrc = next((o for o in remote if o.get('type') == 'source'), {})
    out['remoteInvaderHarvested'] = rsrc.get('invaderHarvested')
    out['memoryRemote'] = mem_r.get(REMOTE) or mem_r
    # light neighbour glance
    rooms = [HOME, REMOTE, 'W47N8', 'W44N8', 'W45N7', 'W47N9']
    ms = api.req('game/map-stats', {'rooms': rooms, 'statName': 'owner0', 'shard': 'shard3'})
    users = ms.get('users', {}); stats = ms.get('stats', {})
    out['neighbours'] = {}
    for room in rooms:
        st = stats.get(room, {}); own = st.get('own') or {}
        uid = own.get('user'); name = users.get(uid, {}).get('username') if uid else None
        out['neighbours'][room] = {'owner': name, 'level': own.get('level'), 'novice': st.get('novice')}
    print(json.dumps(out, indent=2))
    Path(os.path.join(ROOT, 'metrics', 'defense.json')).write_text(json.dumps(out, indent=2))

if __name__ == '__main__':
    main()
