#!/usr/bin/env python3
"""Turn the planner result into a per-RCL build plan + fixed creep positions/routes (data/layout_W46N8_v2.json)."""
import pickle, json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
res = pickle.load(open('/tmp/v2_res.pkl', 'rb')); occ = res['occ']
S = {}  # pos -> (type, rcl)
def put(p, t, r): S[tuple(p)] = (t, r)
A, B, C = res['fillers']['A'], res['fillers'].get('B'), res['fillers'].get('C')
fillers = []
# extension order: filler A first (RCL2-4), then hub ext, B, C, loose
ext_rcl_cap = [0, 0, 5, 10, 20, 30, 40, 50, 60]
ext_slots = []
for name, st in (('A', A), ('B', B), ('C', C)):
    if not st: continue
    for p, t in st.items():
        if t == 'F': fillers.append(p)
        elif t == 'L': put(p, 'link', {'A': 5, 'B': 8, 'C': 8}[name])
        elif t == 'K': put(p, 'container', {'A': 2, 'B': 5, 'C': 7}[name])
        elif t == 'S': put(p, 'spawn', {'A': 1, 'B': 7, 'C': 8}[name])
        else: ext_slots.append((name, p))
hub_ext = [p for p, t in occ.items() if t == 'hubext']; loose = [p for p, t in occ.items() if t == 'single_ext']
# spawn C slot unused if spawn3 is in the hub: C's S slot becomes an extension
spawn3 = next(p for p, t in occ.items() if t == 'spawn3')
if C:
    cs = next(p for p, t in C.items() if t == 'S'); S.pop(cs); ext_slots.append(('C', cs))
order = [p for n, p in ext_slots if n == 'A'] + hub_ext + [p for n, p in ext_slots if n == 'B'] + [p for n, p in ext_slots if n == 'C'] + loose
for i, p in enumerate(order[:60]):
    r = next(R for R in range(2, 9) if i < ext_rcl_cap[R]); put(p, 'extension', r)
put(spawn3, 'spawn', 8)
for t, r in [('storage', 4), ('hub_terminal', 6), ('hub_link', 5), ('hub_factory', 7), ('hub_powerSpawn', 8)]:
    p = next(q for q, v in occ.items() if v == (t if t == 'storage' else t)); put(p, t.replace('hub_', ''), r)
put(res['srcA_link'], 'link', 6); put(res['CL'], 'link', 7)
put(res['ctl_cont'], 'container', 2); put(res['miners'][0], 'container', 2)
if not res['bonusB']: put(res['miners'][1], 'container', 2)
else: put(res['miners'][1], 'container', 2)  # temporary until storage (RCL4), then removed
put(res['mm'], 'container', 6); put((40, 24), 'extractor', 6)
for k, p in enumerate(res['labs']): put(p, 'lab', 6 if k < 3 else 7 if k < 6 else 8)
tw = [p for p, t in occ.items() if t == 'single_tower']
for k, p in enumerate(tw): put(p, 'tower', [3, 5, 7, 8, 8, 8][k])
put(next(p for p, t in occ.items() if t == 'single_nuker'), 'nuker', 8)
put(next(p for p, t in occ.items() if t == 'single_observer'), 'observer', 8)
# roads: per route, RCL when the route is first needed
need = {'srcA': 2, 'ctl': 2, 'fillerA': 2, 'hubdoor': 4, 'srcB': 2, 'fillerB': 5, 'fillerC': 7, 'mineral': 6, 'labs': 6}
road_rcl = {}
for n, pts in res['routes'].items():
    for p in pts:
        if p in S: continue
        road_rcl[p] = min(road_rcl.get(p, 9), need.get(n, 4))
for i in range(4):
    pass
# ramparts: spawns, towers, storage, terminal, manager tile, filler tiles, nuker, power spawn, factory
ramp = {}
for p, (t, r) in S.items():
    if t in ('spawn', 'tower', 'storage', 'terminal', 'nuker', 'powerSpawn', 'factory'): ramp[p] = max(r, 3)
ramp[res['M']] = 4
for f in fillers: ramp[f] = 4
# removals per RCL (container replaced by direct storage delivery / links)
remove = {}
if res['bonusB']: remove.setdefault('4', []).append({'type': 'container', 'pos': list(res['miners'][1]), 'why': 'source B miner transfers straight into storage'})
remove.setdefault('6', []).append({'type': 'container', 'pos': list(res['miners'][0]), 'why': 'source A link built; optional — keep as overflow buffer if container cap allows'})
remove.setdefault('7', []).append({'type': 'container', 'pos': list(res['ctl_cont']), 'why': 'controller link built; optional'})
plan = {'room': 'W46N8', 'version': 2, 'generatedBy': 'tools/plan_v2.py + tools/export_v2.py', 'rcl': {}, 'remove': remove,
        'positions': {'manager': list(res['M']), 'fillers': [list(p) for p in fillers], 'upgraders': [list(p) for p in res['ups']],
                      'miners': [list(res['miners'][0]), list(res['miners'][1])], 'mineralMiner': list(res['mm']),
                      'storageDoor': list(res['start'])},
        'routes': {k: [list(p) for p in v] for k, v in res['routes'].items()},
        'stamps': {n: {'tiles': {f'{p[0]},{p[1]}': t for p, t in st.items()}} for n, st in res['fillers'].items()}}
for R in range(1, 9):
    lv = {}
    for p, (t, r) in S.items():
        if r == R: lv.setdefault(t, []).append(list(p))
    rd = [list(p) for p, r in road_rcl.items() if r == R]
    if rd: lv['road'] = rd
    rp = [list(p) for p, r in ramp.items() if r == R]
    if rp: lv['rampart'] = rp
    plan['rcl'][str(R)] = lv
from collections import Counter
cnt = Counter(t for t, r in S.values()); cnt['road'] = len(road_rcl); cnt['rampart'] = len(ramp)
plan['counts'] = cnt
json.dump(plan, open(f'{ROOT}/data/layout_W46N8_v2.json', 'w'), indent=1)
print(dict(cnt))
