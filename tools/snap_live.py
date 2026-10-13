#!/usr/bin/env python3
"""Write a sim snapshot from the websocket live state (metrics/live.json) + creep memory (API).
Usage: python3 tools/snap_live.py [out.json] [--complete x,y ...]  (--complete turns a construction site into a built structure)
Then: SIM_SNAP=out.json node scripts/sim.js 600"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import api
args = sys.argv[1:]
out = args[0] if args and not args[0].startswith('--') else os.path.join(ROOT, 'data/sim_snapshot_live.json')
done = {tuple(map(int, a.split(','))) for a in args[args.index('--complete') + 1:]} if '--complete' in args else set()
live = json.load(open(os.path.join(ROOT, 'metrics/live.json')))
objs = []
for o in live['objects'].values():
    if o.get('room') != 'W46N8': continue
    if o.get('type') == 'constructionSite' and (o['x'], o['y']) in done:
        o = dict(o, type=o['structureType'], store={'energy': 0}, hits=1000)
    objs.append(o)
mem = api.memory('creeps') or {}
json.dump({'uid': live['uid'], 'objects': objs, 'creepMem': mem}, open(out, 'w'))
print(f'wrote {out}: {len(objs)} objects, {len(mem)} creep memories, completed {sorted(done)}')
