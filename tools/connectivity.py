#!/usr/bin/env python3
"""W46N8 connectivity review: Dijkstra from storage door to every key node (road 1, plain 2, swamp 10; obstacles blocked;
planned road sites count as road with --plan). Prints off-road tiles on each path (missing road segments)."""
import sys, json, heapq; sys.path.insert(0, 'tools'); from q import q; from ring_check import T, gates
v = q("(function(){const r=Game.rooms.W46N8;return {S:r.find(FIND_STRUCTURES).map(s=>[s.structureType,s.pos.x,s.pos.y]),C:r.find(FIND_MY_CONSTRUCTION_SITES).map(s=>[s.structureType,s.pos.x,s.pos.y]),src:r.find(FIND_SOURCES).map(s=>[s.pos.x,s.pos.y]),min:r.find(FIND_MINERALS).map(s=>[s.pos.x,s.pos.y]),ctl:[r.controller.pos.x,r.controller.pos.y]}})()")['v']
WALK = {'road', 'container', 'rampart'}; road = set(); block = set()
for k, x, y in v['S']:
    if k == 'road': road.add((x, y))
    elif k not in WALK: block.add((x, y))
for k, x, y in v['C']:
    if k == 'road': road.add((x, y))
def cost(x, y):
    if (x, y) in road: return 1
    return 10 if T[y*50+x] == '2' else 2
def path(a, goal, rng):
    D = {a: 0}; P = {}; h = [(0, a)]
    while h:
        d, (x, y) = heapq.heappop(h)
        if max(abs(x-goal[0]), abs(y-goal[1])) <= rng: n = (x, y); out = []
        else: n = None
        if n:
            while n in P: out.append(n); n = P[n]
            return d, out[::-1]
        if d > D[(x, y)]: continue
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                m = (x+dx, y+dy)
                if not (0 < m[0] < 49 and 0 < m[1] < 49) or T[m[1]*50+m[0]] in '13' or m in block: continue
                nd = d + cost(*m)
                if nd < D.get(m, 1e9): D[m] = nd; P[m] = (x, y); heapq.heappush(h, (nd, m))
    return None, []
S = {}
for k, x, y in v['S']: S.setdefault(k, []).append((x, y))
nodes = {'spawn': (S['spawn'][0], 1), 'ctl container 30,30': ((30, 30), 0), 'controller': (tuple(v['ctl']), 3)}
for i, s in enumerate(v['src']): nodes[f'source {s}'] = (tuple(s), 1)
for m in v['min']: nodes[f'mineral {m}'] = (tuple(m), 1)
for t in S.get('tower', []): nodes[f'tower {t}'] = (t, 1)
for l in S.get('link', []): nodes[f'link {l}'] = (l, 1)
for g in gates: nodes[f'gate {g}'] = (g, 0)
nodes['exit E (W45N8) 49,14'] = ((48, 14), 0)
for k, x, y in v['C']: pass
start = (36, 32)
for name, (g, r) in nodes.items():
    d, p = path(start, g, r); off = [t for t in p if t not in road]
    print(f"{name:28s} len {len(p):3d} cost {d}  off-road {len(off)}: {off[:20]}")
