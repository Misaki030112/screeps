#!/usr/bin/env python3
"""Road route justification (roads v2): Dijkstra on real terrain W46N8+W45N8, 30-day total cost model.
tile cost = build (plain 300 / swamp 1500, 0 if road exists) + 30d decay repair (plain 100 hits/1000t, swamp x5; 0.01 e/hit)
          + 30d traffic * (wear 1 hit/body part/step * 0.01 e + hauler time value e/tick)."""
import json, heapq, sys
TPD = 20700; DAYS = 30
TR = {r: open(f'data/terrain_{r}.txt').read().strip() for r in ['W46N8', 'W45N8']}
L = json.load(open('metrics/live.json'))
road = set(); obs = set()
for o in L['objects'].values():
    if o.get('room') != 'W46N8': continue
    t = o.get('type')
    if t == 'road': road.add(('W46N8', o['x'], o['y']))
    elif t in ('spawn','extension','tower','storage','link','lab','terminal','wall','constructedWall','observer','powerSpawn','nuker','factory','extractor','source','mineral','controller'): obs.add(('W46N8', o['x'], o['y']))
for x, y, _ in json.load(open('/tmp/planobs.json')): obs.add(('W46N8', x, y))
road.add(('W45N8', 2, 12))  # built earlier (78f9114 builder); W45N8 not in live.json
obs |= {('W45N8', 14, 12)}  # source
def terr(r, x, y): return TR[r][y * 50 + x]
def ok(n): r, x, y = n; return 0 <= x < 50 and 0 <= y < 50 and terr(r, x, y) != '1' and n not in obs
def build(n): return 0 if n in road else (1500 if terr(*n) == '2' else 300)
def decay_day(n): return TPD / 1000 * 100 * (5 if terr(*n) == '2' else 1) * 0.01
def tile_cost(n, steps, parts, tval):
    return build(n) + DAYS * (decay_day(n) + steps * (parts * 0.01 + tval))
def nbrs(n):
    r, x, y = n
    if r == 'W46N8' and x == 49: yield ('W45N8', 0, y)
    if r == 'W45N8' and x == 0: yield ('W46N8', 49, y)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx or dy:
                m = (r, x + dx, y + dy)
                if ok(m) and not (m[1] in (0, 49) and x in (0, 49)) and not (m[2] in (0, 49) and y in (0, 49)): yield m
def dijkstra(starts, goals, w, forbid=lambda n: False):
    D = {s: w(s) for s in starts}; prev = {}; pq = [(D[s], s) for s in starts]; heapq.heapify(pq)
    while pq:
        d, n = heapq.heappop(pq)
        if d > D.get(n, 1e18): continue
        if n in goals:
            p = [n]
            while p[-1] in prev: p.append(prev[p[-1]])
            return p[::-1]
        for m in nbrs(n):
            if forbid(m): continue
            nd = d + w(m)
            if nd < D.get(m, 1e18): D[m] = nd; prev[m] = n; heapq.heappush(pq, (nd, m))
def stats(p, steps, parts, tval):
    sw = sum(terr(*n) == '2' for n in p); b = sum(build(n) for n in p)
    up = sum(decay_day(n) for n in p); tot = sum(tile_cost(n, steps, parts, tval) for n in p)
    return dict(len=len(p), swamp=sw, new_swamp=sum(terr(*n) == '2' and n not in road for n in p), build=b, decay_day=round(up, 1),
                wear_day=round(len(p) * steps * parts * 0.01, 1), time_day=round(len(p) * steps * tval, 1), total30=round(tot),
                exit=next((n for n in p if n[0] == 'W46N8' and n[1] == 49), None))
def ring(r, x, y): return {(r, x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx or dy) and ok((r, x + dx, y + dy))}
out = {}
# ---- haul: storage 37,31 -> W45N8 container 13,11 (1x 16C8M after swap: 259 loaded + 259 empty trips/day, 24 parts, 0.8 e/tick)
H = dict(steps=518, parts=24, tval=0.8)
S0, G0 = ring('W46N8', 37, 31), ring('W45N8', 13, 11)
w = lambda n: tile_cost(n, **H)
alts = {}
alts['optimal(min 30d cost)'] = dijkstra(S0, G0, w)
alts['shortest-by-tiles'] = dijkstra(S0, G0, lambda n: 1)
alts['swamp-avoiding'] = dijkstra(S0, G0, w, forbid=lambda n: terr(*n) == '2' and n not in road)
v1 = json.loads(open('src/layouts/remote_routes.js').read().split('=', 1)[1].strip().rstrip(';'))['W45N8']
alts['v1 plan'] = [tuple(t) for t in v1]
v2leg = [(0, 14), (1, 13), (2, 12), (3, 11), (4, 11), (5, 11), (6, 10), (7, 9), (8, 9), (9, 9), (10, 9), (11, 9), (12, 10)]
alts['v2 branch (walked)'] = [tuple(t) for t in v1 if t[0] == 'W46N8'] + [('W45N8', x, y) for x, y in v2leg]
print({k: (p is None) for k,p in alts.items()}); out["haul"] = {k: dict(stats(p, **H), path=p) for k, p in alts.items() if p}
# exit choice: force each exit y
ex = {}
for y in range(50):
    e = ('W46N8', 49, y)
    if not ok(e) or not ok(('W45N8', 0, y)): continue
    a = dijkstra(S0, {e}, w); b = dijkstra({('W45N8', 0, y)}, G0, w)
    if a and b: ex[y] = stats(a + b, **H)
out['exits'] = ex
json.dump(out, open('out/road_justify.json', 'w'), default=str, indent=1)
for k, v in out['haul'].items(): print(f"{k:22} " + ' '.join(f'{a}={b}' for a, b in v.items() if a != 'path'))
print('exits:', sorted(((v['total30'], y, v['len'], v['swamp'], v['new_swamp']) for y, v in ex.items()))[:8])
fa = dijkstra(S0, G0, lambda n: 1, forbid=lambda n: terr(*n) == '2')
print('all-swamp-forbidden:', fa and stats(fa, **H), fa and [n[1:] for n in fa])
# RCL8-ignoring optimal (allow planned rcl>6 tiles) to quantify the conflict
po = {('W46N8', x, y) for x, y, t in json.load(open('/tmp/planobs.json'))}
obs -= po
t = dijkstra(S0, G0, w); print('optimal if RCL7-8 plan ignored:', stats(t, **H)['len'], [n[1:] for n in t if (n in po)])
obs |= po
print('optimal path:', [(n[0][-2:],)+n[1:] for n in out['haul']['optimal(min 30d cost)']['path']])
