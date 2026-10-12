#!/usr/bin/env python3
"""Generate a checkerboard ("diagonal road grid") stamp layout around the existing spawn.
Output: data/layout_<room>.json + docs/layout_<room>.png. Usage: plan_layout.py W46N8 35 28"""
import json, sys, heapq, collections, os
from PIL import Image, ImageDraw
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
room, SX, SY = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
info = next(g for g in json.load(open(f'{ROOT}/data/good.json')) if g['room'] == room)
T = open(f'{ROOT}/data/terrain_{room}.txt').read()
wall = lambda x, y: not (0 <= x < 50 and 0 <= y < 50) or T[y*50+x] in '13'
swamp = lambda x, y: T[y*50+x] == '2'
N8 = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
srcs = [tuple(s) for s in info['src']]; ctl = tuple(info['ctl']); mineral = tuple(info['min'][0][1:])
cheb = lambda a, b: max(abs(a[0]-b[0]), abs(a[1]-b[1]))

def path(a, goal, rng, block=set()):
    """Dijkstra from a to any tile within rng of goal; plain 2, swamp 10, existing road 1."""
    D = {a: 0}; P = {}; pq = [(0, a)]
    while pq:
        d, u = heapq.heappop(pq)
        if cheb(u, goal) <= rng: break
        if d > D[u]: continue
        for dx, dy in N8:
            v = (u[0]+dx, u[1]+dy)
            if wall(*v) or v in block or not (1 <= v[0] <= 48 and 1 <= v[1] <= 48): continue
            nd = d + (1 if v in roads else 10 if swamp(*v) else 2)
            if nd < D.get(v, 1e9): D[v] = nd; P[v] = u; heapq.heappush(pq, (nd, v))
    out = []
    while u != a: out.append(u); u = P[u]
    return out[::-1]

roads = set(); struct = {}  # (x,y)->(type, rcl)
def put(p, t, rcl): struct[p] = (t, rcl)
put((SX, SY), 'spawn', 1)
avoid = set(srcs + [ctl, mineral])
# 1) Source containers/links + controller container/link; logistic roads
for i, s in enumerate(srcs):
    p = path((SX, SY), s, 1, avoid); roads.update(p[:-1]); cont = p[-1]
    put(cont, 'container', 2)
    link = next(((cont[0]+dx, cont[1]+dy) for dx, dy in N8 if not wall(cont[0]+dx, cont[1]+dy)
                 and (cont[0]+dx, cont[1]+dy) not in roads and (cont[0]+dx, cont[1]+dy) not in struct
                 and (cont[0]+dx, cont[1]+dy) not in avoid), None)
    if link: put(link, 'link', 6 + i)  # source links RCL6/7
p = path((SX, SY), ctl, 2, avoid); roads.update(p[:-1]); put(p[-1], 'container', 2)
cl = next(((p[-1][0]+dx, p[-1][1]+dy) for dx, dy in N8 if not wall(p[-1][0]+dx, p[-1][1]+dy)
           and (p[-1][0]+dx, p[-1][1]+dy) not in roads and (p[-1][0]+dx, p[-1][1]+dy) not in struct
           and cheb((p[-1][0]+dx, p[-1][1]+dy), ctl) <= 3), None)
if cl: put(cl, 'link', 5)
pm = path((SX, SY), mineral, 1, avoid); minroad = pm[:-1]; put(pm[-1], 'container', 6); put(mineral, 'extractor', 6)

# 2) Checkerboard: parity of spawn = building tiles, other parity = roads. BFS over road grid.
par = (SX + SY) % 2
def buildable(p):
    x, y = p
    return 2 <= x <= 47 and 2 <= y <= 47 and not wall(x, y) and p not in roads and p not in struct \
        and all(cheb(p, a) > 1 for a in avoid) and cheb(p, ctl) > 2
grid_road = lambda p: 1 <= p[0] <= 48 and 1 <= p[1] <= 48 and not wall(*p) and (p[0]+p[1]) % 2 != par and p not in struct
dist = {}; q = collections.deque()
for dx, dy in N8:
    v = (SX+dx, SY+dy)
    if grid_road(v): dist[v] = 1; q.append(v)
while q:
    u = q.popleft()
    for dx, dy in N8:
        v = (u[0]+dx, u[1]+dy)
        if v not in dist and grid_road(v) and cheb(v, (SX, SY)) <= 12: dist[v] = dist[u]+1; q.append(v)
slots = {}
for r, d in dist.items():
    for dx, dy in N8:
        v = (r[0]+dx, r[1]+dy)
        if (v[0]+v[1]) % 2 == par and buildable(v): slots[v] = min(slots.get(v, 99), d)
order = sorted(slots, key=lambda v: (slots[v], cheb(v, (SX, SY))))
used = []
def take(t, rcl):
    v = order.pop(0); put(v, t, rcl); used.append(v); return v
# core
take('storage', 4); take('link', 5); take('tower', 3); take('spawn', 7); take('terminal', 6)
for r in (5, 7, 8, 8, 8): take('tower', r)
take('spawn', 8); take('factory', 7); take('powerSpawn', 8)
# labs: 4x4 stamp, diagonal road (i==j), 10 labs (corners (0,3),(3,0) left free), inputs at (1,2),(2,1)
best = None
for bx in range(2, 45):
    for by in range(2, 45):
        tiles = [(bx+i, by+j) for i in range(4) for j in range(4)]
        if any(wall(*t) or t in struct or t in roads or any(cheb(t, a) <= 1 for a in avoid) or cheb(t, ctl) <= 2 for t in tiles): continue
        dd = min((slots.get(t, dist.get(t, 99)) for t in tiles))
        if dd < 3 or dd > 20: continue
        if not best or dd < best[0]: best = (dd, bx, by)
if best:
    _, bx, by = best
    k = 0
    for i, j in [(1, 2), (2, 1)] + [(i, j) for i in range(4) for j in range(4) if i != j and (i, j) not in ((1, 2), (2, 1), (0, 3), (3, 0))]:
        v = (bx+i, by+j); put(v, 'lab', 6 if k < 3 else 7 if k < 6 else 8); used.append(v); k += 1
        if v in order: order.remove(v)
        dist.pop(v, None)
    for i in range(4): roads.add((bx+i, by+i)); dist.pop((bx+i, by+i), None)
    for t in [(bx, by+3), (bx+3, by)]:
        if t in order: order.remove(t)
ext_rcl = [(2, 5), (3, 5), (4, 10), (5, 10), (6, 10), (7, 10), (8, 10)]
for rcl, n in ext_rcl:
    for _ in range(n): take('extension', rcl)
take('nuker', 8); take('observer', 8)
# 3) Grid roads actually adjacent to used structures; RCL = min RCL of neighbours (>=2)
for r in dist:
    ns = [struct[(r[0]+dx, r[1]+dy)][1] for dx, dy in N8 if (r[0]+dx, r[1]+dy) in used]
    if ns: roads.add(r); struct.setdefault(('road',) + r, ('road', max(2, min(ns))))
road_rcl = {}
for k, v in list(struct.items()):
    if k[0] == 'road': road_rcl[k[1:]] = v[1]; del struct[k]
for p in roads: road_rcl.setdefault(p, 2)
for p in minroad: road_rcl[p] = 6; roads.add(p)
# 4) Ramparts on critical structures
ramparts = {p: (3 if t in ('spawn', 'tower') else 4) for p, (t, r) in struct.items() if t in ('spawn', 'tower', 'storage', 'terminal')}
for p, (t, r) in list(struct.items()):
    if t in ('spawn', 'tower', 'storage', 'terminal'): ramparts[p] = max(r, ramparts[p])

plan = {'room': room, 'spawn': [SX, SY], 'generatedBy': 'tools/plan_layout.py', 'rcl': {}}
for r in range(1, 9):
    lvl = plan['rcl'][str(r)] = {}
    for p, (t, rr) in struct.items():
        if rr == r: lvl.setdefault(t, []).append(list(p))
    lvl['road'] = [list(p) for p, rr in road_rcl.items() if rr == r and p not in struct]
    lvl['rampart'] = [list(p) for p, rr in ramparts.items() if rr == r]
    lvl = {k: v for k, v in lvl.items() if v}; plan['rcl'][str(r)] = lvl
json.dump(plan, open(f'{ROOT}/data/layout_{room}.json', 'w'), indent=1)
open(f'{ROOT}/src/layouts/{room}.js', 'w').write(f'// GENERATED by tools/plan_layout.py from data/layout_{room}.json\nmodule.exports = ' + json.dumps(plan) + ';\n')
from collections import Counter
print(Counter(t for t, _ in struct.values()), 'roads', len(road_rcl), 'ramparts', len(ramparts))

# 5) Render
S = 16; img = Image.new('RGB', (50*S, 50*S + 40), (20, 20, 20)); d = ImageDraw.Draw(img)
COL = {'spawn': (255, 220, 0), 'extension': (240, 240, 240), 'tower': (255, 60, 60), 'storage': (255, 160, 0),
       'terminal': (0, 200, 200), 'link': (120, 120, 255), 'container': (160, 110, 60), 'lab': (200, 80, 255),
       'factory': (100, 200, 100), 'powerSpawn': (255, 0, 120), 'nuker': (90, 90, 90), 'observer': (0, 255, 180), 'extractor': (200, 200, 0)}
for y in range(50):
    for x in range(50):
        c = (0, 0, 0) if wall(x, y) else (40, 60, 30) if swamp(x, y) else (50, 50, 50)
        d.rectangle([x*S, y*S, x*S+S-1, y*S+S-1], fill=c)
for p, r in road_rcl.items(): d.rectangle([p[0]*S+5, p[1]*S+5, p[0]*S+S-6, p[1]*S+S-6], fill=(130, 130, 130))
for p, (t, r) in struct.items():
    d.rectangle([p[0]*S+2, p[1]*S+2, p[0]*S+S-3, p[1]*S+S-3], fill=COL[t]); d.text((p[0]*S+4, p[1]*S+2), str(r), fill=(0, 0, 0))
for p in ramparts: d.rectangle([p[0]*S, p[1]*S, p[0]*S+S-1, p[1]*S+S-1], outline=(0, 255, 0), width=2)
for s in srcs: d.ellipse([s[0]*S+1, s[1]*S+1, s[0]*S+S-2, s[1]*S+S-2], fill=(255, 255, 0))
d.ellipse([ctl[0]*S, ctl[1]*S, ctl[0]*S+S-1, ctl[1]*S+S-1], outline=(255, 255, 255), width=3)
d.polygon([(mineral[0]*S+8, mineral[1]*S), (mineral[0]*S+16, mineral[1]*S+16), (mineral[0]*S, mineral[1]*S+16)], fill=(0, 255, 255))
x = 4
for t, c in COL.items(): d.rectangle([x, 50*S+8, x+10, 50*S+18], fill=c); d.text((x+13, 50*S+7), t, fill=(255, 255, 255)); x += 13 + 7*len(t) + 8
d.text((4, 50*S+24), f'{room} layout: number = RCL; green outline = rampart; grey = road', fill=(255, 255, 255))
img.save(f'{ROOT}/docs/layout_{room}.png')
