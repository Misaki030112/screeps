#!/usr/bin/env python3
"""W47N8 north tower slots (Misaki 17:52). Scores every inside-the-seal tile for tower damage on the north approach (tiles y<=2
from which an enemy can hit a seal wall), safety (enemy outside the seal cannot reach the tower with RA: range >= 4 from every
y<=2 tile), energy haul (walking steps from source A container 26,11 / storage 35,32), and plan conflicts (planned roads, v3b
structures, links, W47N8<->W46N8 link road, defender wall posts). usage: python3 tools/w47n8_tower_plan.py [--json]"""
import sys, os, json, subprocess, collections
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H); ROOT = os.path.join(H, '..')
from model import terrain
T = terrain('W47N8'); wall = lambda x, y: not (0 <= x < 50 and 0 <= y < 50) or int(T[y * 50 + x]) & 1
js = lambda e: json.loads(subprocess.run(['node', '-e', f'console.log(JSON.stringify({e}))'], capture_output=True, text=True, cwd=ROOT).stdout)
L = js("require('./src/rooms/w47n8/layout.js').ORDER"); ROADS = set(map(tuple, js("require('./src/rooms/w47n8/roads.js').ROADS")))
LINK = set(map(tuple, js("require('./src/layouts/w8link.js').W47N8")))
SEAL = [(x, 3) for x in [24, 25, 26, 27, 28, 29, 30, 31]], [(x, 3) for x in [8, 9, 10, 11]]
POSTS = {(x, 4) for x in [24, 25, 26, 28, 29, 30, 31, 8, 9, 10, 11]} | {(28, 5), (29, 5), (25, 5), (30, 5)}
FIXED = {(26, 11): 'srcA cont', (27, 11): 'source A', (26, 12): 'link A', (13, 25): 'ctl link', (13, 26): 'ctl cont', (15, 18): 'Spawn2', (33, 33): 'hub cont', (11, 43): 'srcB cont'}
OCC = {tuple(p): k for k, v in L.items() if k not in ('road', 'rampart') for p in v}
cheb = lambda a, b: max(abs(a[0] - b[0]), abs(a[1] - b[1]))
tdmg = lambda r: 600 if r <= 5 else 150 if r >= 20 else 600 - (r - 5) * 30
OUT = [(x, y) for y in range(3) for x in range(50) if not wall(x, y)]
EXT = [[e for e in OUT if any(cheb(e, s) <= 3 for s in seg)] for seg in SEAL]  # where attackers of each seal segment stand
def bfs(src):
    d = {src: 0}; q = collections.deque([src])
    while q:
        p = q.popleft()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                n = (p[0] + dx, p[1] + dy)
                if n in d or wall(*n) or n[1] <= 3 and n not in SEAL[0] + SEAL[1] and n[1] < 4: continue
                if n[1] <= 3: continue  # never walk through/north of the seal
                if n in OCC and OCC[n] not in ('container',) and n != src: continue
                d[n] = d[p] + 1; q.append(n)
    return d
DA, DS = bfs((26, 11)), bfs((35, 32))
def score(c):
    e, w = [tdmg(cheb(c, x)) for x in EXT[0]], [tdmg(cheb(c, x)) for x in EXT[1]]
    return {'pos': list(c), 'east_min': min(e), 'east_avg': round(sum(e) / len(e)), 'west_min': min(w), 'west_avg': round(sum(w) / len(w)),
            'ra_safe': min(cheb(c, o) for o in OUT) >= 4, 'haul_srcA': DA.get(c), 'haul_storage': DS.get(c),
            'conflict': (OCC.get(c) or FIXED.get(c) or ('road' if c in ROADS else 'linkroad' if c in LINK else 'post' if c in POSTS else ''))}
def connected_ok(c):  # placing a tower on c must not cut any wall post / idle tile / road off from storage
    global OCC
    OCC[c] = 'tower'; d = bfs((35, 32)); del OCC[c]
    return all(p in d for p in POSTS | (ROADS - {c}) if p[1] >= 4 and p in DS)
cands = [score((x, y)) for y in range(4, 16) for x in range(4, 34) if not wall(x, y)]
ok = [s for s in cands if s['ra_safe'] and not s['conflict'] and s['haul_srcA'] is not None and connected_ok(tuple(s['pos']))]
east = sorted(ok, key=lambda s: (-s['east_min'], s['haul_srcA']))[:8]
both = sorted(ok, key=lambda s: (-(min(s['east_min'], s['west_min'])), s['haul_srcA']))[:8]
old = [score(tuple(p)) for p in [(33, 35), (34, 31)]]
if '--json' in sys.argv: print(json.dumps({'old': old, 'east': east, 'both': both}, indent=1))
else:
    for k, v in [('old', old), ('east (best east_min)', east), ('both segments', both)]:
        print(k); [print('  ', s) for s in v]
