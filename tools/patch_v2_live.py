#!/usr/bin/env python3
"""Adapt layout v2 to the live room (approved 2026-10-13): keep tower (36,29) and controller container (30,30).
- tower (36,29) RCL3 takes the hub power-spawn slot; power spawn moves to the old v2 RCL3 tower slot (36,33) at RCL8.
- controller: container (30,30) RCL2 (upgrader stands on it), link (30,31) RCL7, upgrader spots around it,
  (31,29) becomes the hauler drop tile (road, end of the controller route).
- filler A centre (35,26): temporary container RCL2-4 is NOT used; pre-RCL5 a 'queen' hauler walks the 4 filler tiles.
Idempotent: works on the planner output."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = f'{ROOT}/data/layout_W46N8_v2.json'
p = json.load(open(F))
def remove(pos, typ=None):
    for r, lv in p['rcl'].items():
        for t in list(lv):
            if typ and t != typ: continue
            lv[t] = [q for q in lv[t] if q != list(pos)]
            if not lv[t]: del lv[t]
def add(pos, typ, rcl):
    p['rcl'][str(rcl)].setdefault(typ, [])
    if list(pos) not in p['rcl'][str(rcl)][typ]: p['rcl'][str(rcl)][typ].append(list(pos))
if not p.get('liveAdjusted'):
    # tower / power spawn swap
    remove((36, 29), 'powerSpawn'); remove((36, 33), 'tower')
    add((36, 29), 'tower', 3); add((36, 33), 'powerSpawn', 8)
    # towers by RCL: 3:(36,29) 5:(37,33) 7:(35,34) 8:(36,34),(32,30),(32,31)
    for q in [(37, 33), (35, 34), (36, 34), (32, 30), (32, 31)]: remove(q, 'tower')
    for q, r in [((37, 33), 5), ((35, 34), 7), ((36, 34), 8), ((32, 30), 8), ((32, 31), 8)]: add(q, 'tower', r)
    # ramparts: move with the structures (rampart RCL3 for tower 36,29; power spawn 36,33 at 8)
    remove((36, 29), 'rampart'); remove((36, 33), 'rampart'); add((36, 29), 'rampart', 3); add((36, 33), 'rampart', 8)
    for q, r in [((37, 33), 5), ((35, 34), 7)]: remove(q, 'rampart'); add(q, 'rampart', r)
    # controller area
    remove((31, 29), 'container'); remove((30, 30), 'link')
    add((30, 30), 'container', 2); add((30, 31), 'link', 7); add((31, 29), 'road', 2)
    p['positions']['upgraders'] = [[30, 30], [31, 30], [29, 30], [31, 31], [29, 31]]
    p['positions']['controllerContainer'] = [30, 30]; p['positions']['controllerLink'] = [30, 31]
    p['positions']['controllerDrop'] = [31, 29]
    p['routes']['ctl'] = p['routes']['ctl'] + [[31, 29]]
    p['remove'] = {k: [x for x in v if x['pos'] != [31, 29]] for k, v in p['remove'].items()}
    p['remove'].setdefault('7', []).append({'type': 'container', 'pos': [30, 30], 'why': 'optional after controller link; keep while container cap allows'})
    p['remove']['7'] = [x for x in p['remove']['7'] if not (x['pos'] == [30, 30])] or []
    # fixed filler-route for the pre-RCL5 queen hauler and fixed fill neighbours
    p['positions']['queenRoute'] = [[35, 24], [34, 25], [35, 26], [36, 25], [36, 27], [35, 26], [34, 27], [35, 26], [34, 25], [35, 24]]
    p['positions']['fillerContainerA'] = [35, 24]
    p['liveAdjusted'] = '2026-10-13: tower 36,29 + ctl container 30,30 kept'
from collections import Counter
cnt = Counter()
for r, lv in p['rcl'].items():
    for t, l in lv.items(): cnt[t] += len(l)
p['counts'] = cnt
json.dump(p, open(F, 'w'), indent=1); print(dict(cnt))
open(f'{ROOT}/src/layouts/W46N8.js', 'w').write('// GENERATED from data/layout_W46N8_v2.json (layout v2, live-adjusted)\nmodule.exports = ' + json.dumps(p) + ';\n')
