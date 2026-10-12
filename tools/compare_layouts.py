#!/usr/bin/env python3
"""Compare v1 (checkerboard), v2 (hub + fast fillers) and bunker feasibility on W46N8."""
import json, os, sys, heapq
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = open(f'{ROOT}/data/terrain_W46N8.txt').read()
wall = lambda p: not (0 <= p[0] < 50 and 0 <= p[1] < 50) or T[p[1]*50+p[0]] in '13'
N8 = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
cheb = lambda a, b: max(abs(a[0]-b[0]), abs(a[1]-b[1]))
def bfs(start, blocked):
    D = {start: 0}; q = [start]
    for u in q:
        for dx, dy in N8:
            v = (u[0]+dx, u[1]+dy)
            if v not in D and not wall(v) and v not in blocked: D[v] = D[u] + 1; q.append(v)
    return D
def load(fn):
    p = json.load(open(fn)); S = {}; roads = set()
    for r, lv in p['rcl'].items():
        for t, l in lv.items():
            for q in l:
                if t == 'road': roads.add(tuple(q))
                elif t != 'rampart': S[tuple(q)] = t
    return p, S, roads
def fill_tour(S, roads, start):
    """Greedy tour over road tiles so that every extension/spawn is adjacent to a visited tile (hauler refill walk)."""
    blocked = {p for p, t in S.items() if t not in ('container',)}
    need = {p for p, t in S.items() if t in ('extension', 'spawn')}
    pos = start; total = 0
    while need:
        D = bfs(pos, blocked)
        best = None
        for v, d in D.items():
            k = sum(1 for n in need if cheb(n, v) == 1)
            if k and (not best or d / k < best[0]): best = (d / k, v, d)
        if not best: break
        _, v, d = best; total += d; pos = v; need -= {n for n in need if cheb(n, v) <= 1}
    return total
out = {}
p1, S1, R1 = load(f'{ROOT}/data/layout_W46N8.json')
spawn = (35, 28)
blk1 = {p for p, t in S1.items() if t != 'container'}
D1 = bfs(spawn, blk1 - {spawn})
def dist_to(D, targ): return min(D.get((targ[0]+dx, targ[1]+dy), 999) for dx, dy in N8)
out['v1_checkerboard'] = {'road_tiles': len(R1), 'spawn_to_srcA': dist_to(D1, (32, 11)), 'spawn_to_srcB': dist_to(D1, (39, 33)),
    'spawn_to_controller_range3': min(d for q, d in D1.items() if cheb(q, (28, 32)) <= 3),
    'refill_walk_60ext': fill_tour(S1, R1, (36, 29)), 'stationary_creeps': 0}
p2, S2, R2 = load(f'{ROOT}/data/layout_W46N8_v2.json')
pos = p2['positions']
out['v2_hub_fastfiller'] = {'road_tiles': len(R2), 'route_tiles': {k: len(v) for k, v in p2['routes'].items()},
    'storage_to_srcB': 0, 'refill_walk_60ext': 0, 'stationary_creeps': {'fillers': len(pos['fillers']), 'manager': 1, 'upgraders': len(pos['upgraders'])}}
# bunker feasibility: 13x13 / 11x11 squares with no walls and not within 1 of sources/controller/mineral
objs = [(28, 32), (32, 11), (39, 33), (40, 24)]
for n in (13, 11):
    ok = []
    for x in range(2, 49-n):
        for y in range(2, 49-n):
            sq = [(x+i, y+j) for i in range(n) for j in range(n)]
            walls = sum(wall(q) for q in sq)
            if walls <= 2 and not any(cheb(q, o) <= 1 for q in sq for o in objs): ok.append(((x, y), walls))
    ok.sort(key=lambda a: cheb((a[0][0]+n//2, a[0][1]+n//2), spawn))
    out[f'bunker_{n}x{n}'] = {'feasible_positions(<=2 walls)': len(ok), 'nearest_to_spawn': ok[:3],
                              'contains_existing_spawn': any(o[0][0] <= spawn[0] < o[0][0]+n and o[0][1] <= spawn[1] < o[0][1]+n for o in ok)}
json.dump(out, open(f'{ROOT}/data/layout_compare.json', 'w'), indent=1, default=str)
print(json.dumps(out, indent=1, default=str))
