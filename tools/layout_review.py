#!/usr/bin/env python3
"""Layout review of v2 on real terrain: fill reach, hub distances, tower damage, lab reach, rampart min-cut.
Writes metrics/layout_review.json and docs/layout_review.png.  Usage: .venv/bin/python tools/layout_review.py"""
import json, os, heapq, itertools
import networkx as nx
from PIL import Image, ImageDraw
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = open(f'{ROOT}/data/terrain_W46N8.txt').read()
L = json.load(open(f'{ROOT}/data/layout_W46N8_v2.json'))
wall = lambda x, y: not (0 <= x < 50 and 0 <= y < 50) or T[y*50+x] in '13'
swamp = lambda x, y: T[y*50+x] == '2'
SRC, CTL, MIN = [(32, 11), (39, 33)], (28, 32), (40, 24)
S = {}  # (x,y) -> (type, rcl)
for r, d in L['rcl'].items():
    for t, ps in d.items():
        for p in ps:
            if t == 'rampart': continue
            S.setdefault(tuple(p), (t, int(r)))
RAMP = {tuple(p) for d in L['rcl'].values() for p in d.get('rampart', [])}
P = L['positions']; fillers = [tuple(p) for p in P['fillers']]; manager = tuple(P['manager'])
OBST = {'spawn', 'extension', 'tower', 'storage', 'link', 'terminal', 'lab', 'factory', 'powerSpawn', 'nuker', 'observer', 'extractor'}
def dist(a, goals, rng=1):
    """road-aware walking ticks for a loaded 1:1 hauler (road/plain 1, swamp 5) from a to within rng of any goal"""
    g = set(goals); D = {a: 0}; q = [(0, a)]
    while q:
        d, (x, y) = heapq.heappop(q)
        if any(max(abs(x-gx), abs(y-gy)) <= rng for gx, gy in g): return d
        if d > D[(x, y)]: continue
        for dx, dy in itertools.product((-1, 0, 1), repeat=2):
            n = (x+dx, y+dy)
            if n == (x, y) or wall(*n) or (n in S and S[n][0] in OBST): continue
            nd = d + (1 if (n in S and S[n][0] == 'road') or not swamp(*n) else 5)
            if nd < D.get(n, 1e9): D[n] = nd; heapq.heappush(q, (nd, n))
    return None
ch = lambda a, b: max(abs(a[0]-b[0]), abs(a[1]-b[1]))
R = {}
ext = [p for p, (t, _) in S.items() if t in ('extension', 'spawn')]
standers = set(fillers) | {manager}
R['energy_structs'] = len(ext)
R['energy_structs_touching_a_stationary_creep'] = sum(any(ch(p, f) <= 1 for f in standers) for p in ext)
# per filler: structures served, and refill ticks for a stamp (1 transfer per tick per creep)
serve = {f: [p for p in ext if ch(p, f) <= 1] for f in fillers}
R['max_structs_per_filler'] = max(len(v) for v in serve.values())
# full refill (RCL8: ext 200, spawn 300): bounded by the busiest filler: one transfer per tick + 1 withdraw per 1-2 transfers
R['full_refill_ticks_rcl8_estimate'] = 2 * R['max_structs_per_filler']
# comparison: one queen walking a bunker ring (classic 13x13): ~60 ext + 3 spawns, ~50 tiles of walking, withdraw every ~4 ext at RCL8 (carry 1600/200=8)
R['bunker_queen_refill_ticks_rcl8_reference'] = 60 + 50
stor = next(p for p, (t, _) in S.items() if t == 'storage')
R['storage'] = stor
R['storage_to'] = {'srcA': dist(stor, [SRC[0]]), 'srcB': dist(stor, [SRC[1]]), 'controller': dist(stor, [CTL], 3), 'mineral': dist(stor, [MIN]),
                   'manager_tile': ch(stor, manager)}
for nm, f in (('fillerA_container', (35, 24)), ('fillerB_link', (32, 34)), ('fillerC_link', (30, 25))):
    R['storage_to'][nm] = dist(stor, [f])
labs = [p for p, (t, _) in S.items() if t == 'lab']
R['labs'] = len(labs)
R['labs_in_range2_of_two_inputs'] = max(sum(all(ch(l, i) <= 2 for i in pair) for l in labs if l not in pair) for pair in itertools.combinations(labs, 2))
towers = [p for p, (t, _) in S.items() if t == 'tower']
def tdmg(p):  # TOWER_POWER_ATTACK 600, falloff from range 5 to 20 down to 25%
    tot = 0
    for t in towers:
        r = ch(p, t); tot += 600 if r <= 5 else 150 if r >= 20 else 600 - 450*(r-5)/15
    return round(tot)
open_tiles = [(x, y) for x in range(1, 49) for y in range(1, 49) if not wall(x, y)]
R['towers'] = len(towers)
R['tower_dmg_min_open_tile_rcl8'] = min(tdmg(p) for p in open_tiles)
R['tower_dmg_min_at_core_ramparts'] = min(tdmg(p) for p in RAMP) if RAMP else None
# min-cut: protect every non-road/container structure + manager/filler/upgrader tiles, with a 2-tile buffer (ranged attack range 3 => enemies at the wall
# can still shoot inside within 3; buffer 2 keeps key tiles ≥3 from any rampart-adjacent attacker tile). Sink = exits + tiles within 1 of an exit (unbuildable).
def mincut(buffer):
    prot = {p for p, (t, _) in S.items() if t not in ('road', 'container', 'extractor')} | standers | {tuple(p) for p in P['upgraders']}
    core = {(x+dx, y+dy) for (x, y) in prot for dx in range(-buffer, buffer+1) for dy in range(-buffer, buffer+1) if not wall(x+dx, y+dy)}
    G = nx.DiGraph(); INF = 10**9
    exits = [(x, y) for x in range(50) for y in range(50) if (x in (0, 49) or y in (0, 49)) and not wall(x, y)]
    nearexit = {(x+dx, y+dy) for (x, y) in exits for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
    for x in range(50):
        for y in range(50):
            if wall(x, y): continue
            cap = INF if (x, y) in core or (x, y) in nearexit else 1
            G.add_edge(('i', x, y), ('o', x, y), capacity=cap)
            for dx, dy in itertools.product((-1, 0, 1), repeat=2):
                if (dx or dy) and not wall(x+dx, y+dy): G.add_edge(('o', x, y), ('i', x+dx, y+dy), capacity=INF)
            if (x, y) in core: G.add_edge('S', ('i', x, y), capacity=INF)
            if (x, y) in nearexit: G.add_edge(('o', x, y), 'T', capacity=INF)
    val, (A, _) = nx.minimum_cut(G, 'S', 'T')
    cut = sorted({(n[1], n[2]) for n in A if n != 'S' and n[0] == 'i' and ('o', n[1], n[2]) not in A})
    inside = {(n[1], n[2]) for n in A if n != 'S' and n[0] == 'o'}
    outside = [p for p, (t, _) in S.items() if t not in ('road',) and p not in inside and p not in cut]
    return val, cut, outside
R['mincut'] = {}
cuts = {}
for b in (0, 2):
    v, cut, outside = mincut(b); cuts[b] = cut
    R['mincut'][f'buffer{b}'] = {'ramparts': v, 'structures_outside': len(outside), 'outside_sample': outside[:12]}
R['v2_point_ramparts'] = len(RAMP)
R['roads'] = sum(1 for t, _ in S.values() if t == 'road')
R['road_tiles_on_swamp'] = sum(1 for p, (t, _) in S.items() if t == 'road' and swamp(*p))
json.dump(R, open(f'{ROOT}/metrics/layout_review.json', 'w'), indent=1, default=list)
print(json.dumps(R, indent=1, default=list))
# render
SC = 18; COL = {'spawn': (255, 215, 0), 'extension': (235, 235, 235), 'tower': (230, 40, 40), 'storage': (255, 150, 0), 'terminal': (0, 200, 200),
 'link': (90, 110, 255), 'container': (150, 95, 45), 'lab': (190, 70, 250), 'factory': (90, 190, 90), 'powerSpawn': (255, 0, 120),
 'nuker': (110, 110, 110), 'observer': (0, 255, 170), 'extractor': (200, 200, 0), 'road': (140, 140, 140)}
W = 50*SC; img = Image.new('RGB', (W + 360, 50*SC), (15, 15, 15)); d = ImageDraw.Draw(img)
for i, c in enumerate(T):
    x, y = i % 50, i // 50
    d.rectangle([x*SC, y*SC, x*SC+SC-1, y*SC+SC-1], fill=(0, 0, 0) if c in '13' else (38, 54, 22) if c == '2' else (48, 48, 48))
for p in cuts[2]: d.rectangle([p[0]*SC, p[1]*SC, p[0]*SC+SC-1, p[1]*SC+SC-1], fill=(0, 90, 0))
for (x, y), (t, r) in S.items():
    if t == 'road': d.rectangle([x*SC+6, y*SC+6, x*SC+SC-7, y*SC+SC-7], fill=COL[t]); continue
    d.rectangle([x*SC+2, y*SC+2, x*SC+SC-3, y*SC+SC-3], fill=COL[t]); d.text((x*SC+5, y*SC+3), str(r), fill=(0, 0, 0))
for p in RAMP: d.rectangle([p[0]*SC, p[1]*SC, p[0]*SC+SC-1, p[1]*SC+SC-1], outline=(0, 230, 0), width=2)
for f in fillers: d.ellipse([f[0]*SC+3, f[1]*SC+3, f[0]*SC+SC-4, f[1]*SC+SC-4], outline=(0, 220, 255), width=3)
d.ellipse([manager[0]*SC+3, manager[1]*SC+3, manager[0]*SC+SC-4, manager[1]*SC+SC-4], outline=(255, 60, 255), width=3)
for u in P['upgraders']: d.ellipse([u[0]*SC+4, u[1]*SC+4, u[0]*SC+SC-5, u[1]*SC+SC-5], outline=(60, 255, 60), width=2)
for s in SRC: d.ellipse([s[0]*SC+2, s[1]*SC+2, s[0]*SC+SC-3, s[1]*SC+SC-3], fill=(255, 255, 0))
d.rectangle([CTL[0]*SC, CTL[1]*SC, CTL[0]*SC+SC-1, CTL[1]*SC+SC-1], outline=(255, 255, 255), width=3)
x0 = W + 10; y = 10
lines = ['W46N8 layout review (v2, RCL8 final)', 'number = RCL the structure is built', '',
 'green fill = min-cut rampart line (buffer 2)', 'green outline = v2 point ramparts', 'cyan ring = filler, magenta = manager,', 'green ring = upgrader, yellow = source', '',
 f"energy structs: {R['energy_structs']}, touching a", f"  stationary creep: {R['energy_structs_touching_a_stationary_creep']}",
 f"full refill RCL8 ~{R['full_refill_ticks_rcl8_estimate']} ticks (bunker queen ~{R['bunker_queen_refill_ticks_rcl8_reference']})",
 f"storage->srcA {R['storage_to']['srcA']}  srcB {R['storage_to']['srcB']}", f"storage->ctl(r3) {R['storage_to']['controller']}  mineral {R['storage_to']['mineral']}",
 f"labs reachable: {R['labs_in_range2_of_two_inputs']}/{R['labs']-2}", f"tower dmg min (whole room): {R['tower_dmg_min_open_tile_rcl8']}",
 f"min-cut ramparts: b0={R['mincut']['buffer0']['ramparts']}, b2={R['mincut']['buffer2']['ramparts']}", f"v2 point ramparts: {R['v2_point_ramparts']}", f"roads: {R['roads']}"]
for ln in lines: d.text((x0, y), ln, fill=(255, 255, 255)); y += 16
for t, c in COL.items(): d.rectangle([x0, y, x0+12, y+12], fill=c); d.text((x0+18, y), t, fill=(255, 255, 255)); y += 16
img.save(f'{ROOT}/docs/layout_review.png')
