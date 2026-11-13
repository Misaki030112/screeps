"""W47N8 v3b: extension STRIPS (3 wide: ext | road | ext, one walking filler per strip, head container/link) around a hub.
usage: w47n8_plan3b.py CORE_X CORE_Y MINEX LMAX [png]"""
import sys, json, heapq
from collections import deque
sys.path.insert(0, 'tools'); from model import terrain
from PIL import Image, ImageDraw
CX, CY, MINEX, LMAX = map(int, sys.argv[1:5]); PNG = sys.argv[5] if len(sys.argv) > 5 and sys.argv[5] else None; DMAX = int(sys.argv[6]) if len(sys.argv) > 6 else 12
T = terrain('W47N8'); WALL = lambda x, y: int(T[y*50+x]) & 1; SW = lambda x, y: int(T[y*50+x]) & 2
N8 = [(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b]
opn = lambda p: 0 <= p[0] < 50 and 0 <= p[1] < 50 and not WALL(*p)
cheb = lambda a, b: max(abs(a[0]-b[0]), abs(a[1]-b[1]))
SPAWN = (15, 18); SRC = [(27, 11), (11, 44)]; CONT = [(26, 11), (11, 43)]; CTL = (15, 25); CTLC = (13, 26); MIN = (37, 45)
EXITS = [(x, y) for x in range(50) for y in range(50) if (x in (0, 49) or y in (0, 49)) and opn((x, y))]
EXD = {(x, y): min(cheb((x, y), e) for e in EXITS) for x in range(50) for y in range(50)}
safe = lambda p: opn(p) and EXD[p] >= MINEX
def bfs(starts, ok):
    D = {p: 0 for p in starts}; q = deque(starts)
    while q:
        p = q.popleft()
        for a, b in N8:
            n = (p[0]+a, p[1]+b)
            if n not in D and ok(n): D[n] = D[p]+1; q.append(n)
    return D
used = {SPAWN: 'spawn', CONT[0]: 'container', CONT[1]: 'container', CTLC: 'container'}
for p in [(13, 16), (14, 15), (16, 15), (17, 16), (12, 16)]: used[p] = 'rcl2ext'  # temporary RCL2 set (recycled later, not counted)
reserved = lambda p: p in used or any(cheb(p, s) <= 1 for s in SRC + CONT + [CTLC, MIN]) or cheb(p, CTL) <= 3
WALK = lambda p: opn(p) and used.get(p) in (None, 'road', 'filler', 'rcl2ext' if False else None)
def lostn():
    free = [(x, y) for x in range(1, 49) for y in range(4, 49) if opn((x, y)) and used.get((x, y)) in (None, 'road')]
    D = bfs([SPAWN], lambda p: opn(p) and (used.get(p) in (None, 'road') or p == SPAWN or used.get(p) == 'rcl2ext'))
    return sum(1 for f in free if f not in D)
CORE = (CX, CY)
# core: stand + 4 orthogonal roads + storage/terminal/link/factory on diagonals; powerSpawn/towers/spawns/nuker/observer in a ring later
# 2026-11-13 (Misaki): do not regen src/rooms/w47n8/layout.js over the hand edit. The live hub link is 32,33,
# not the diagonal below (core + (-1, +1) = 33,34). 33,34 is the container–tower road.
used[CORE] = 'road'
for a, b in ((0, 1), (0, -1), (1, 0), (-1, 0)):
    if opn((CX+a, CY+b)): used[(CX+a, CY+b)] = 'road'
for t, (a, b) in zip(['storage', 'link', 'terminal', 'factory'], [(1, -1), (-1, 1), (-1, -1), (1, 1)]):
    if safe((CX+a, CY+b)) and not reserved((CX+a, CY+b)): used[(CX+a, CY+b)] = t
BASE = lostn()
def strip_cells(x, y, L, vert):
    # road from (x,y) length L along axis; box 3 x (L+2): ends are ext caps
    cells = {}
    for i in range(-1, L+1):
        for j in (-1, 0, 1):
            p = (x+j, y+i) if vert else (x+i, y+j)
            cells[p] = 'road' if j == 0 else 'extension'  # road runs through both ends (keeps crossroads open)
    return cells
def strip_ok(cells):
    ne = 0
    for p, t in cells.items():
        if t == 'road' and (not safe(p) or (p in used and used[p] != 'road')): return -1
        if t == 'extension':
            if safe(p) and not reserved(p): ne += 1
            elif opn(p) and used.get(p) != 'road': return -1   # don't leave open odd tiles inside a block
    return ne
D = bfs([CORE], opn)
cands = []
for x in range(2, 48):
    for y in range(2, 48):
        for vert in (0, 1):
            for L in range(4, LMAX+1):
                c = strip_cells(x, y, L, vert); n = strip_ok(c)
                if n >= 2*L + 1:
                    road = [p for p, t in c.items() if t == 'road']
                    cands.append((min(D.get(p, 999) for p in road), -n, x, y, L, vert, c, n))
cands.sort(key=lambda z: (z[0] > 6, -z[7] / (1 + 0.15*z[0]), z[0]))
STRIPS = []; total = 0
for z in cands:
    if total >= 60 or len(STRIPS) >= 4: break
    c = z[6]
    if strip_ok(c) < 2*z[4] + 1: continue
    snap = dict(used)
    for p, t in c.items():
        if t == 'road' or (safe(p) and not reserved(p)): used[p] = t
    if lostn() > BASE or z[0] > DMAX: used.clear(); used.update(snap); continue
    STRIPS.append(z); total += sum(1 for p, t in c.items() if used.get(p) == 'extension' and snap.get(p) is None)
# trim to 60 extensions (drop farthest from core)
ext = sorted([p for p, t in used.items() if t == 'extension'], key=lambda p: D.get(p, 999))
for p in ext[60:]: del used[p]
ext = ext[:60]
# 60th (and any missing) extension: safe free tile touching a strip/hub structure, nearest core, keeping connectivity
blk = {p for z in STRIPS for p in z[6]} | {(CX+a, CY+b) for a in (-1, 0, 1) for b in (-1, 0, 1)}
for p in sorted([p for p in D if safe(p) and not reserved(p) and p not in used and any((p[0]+a, p[1]+b) in blk for a, b in N8)], key=lambda p: (D[p], p)):
    if len(ext) >= 60: break
    used[p] = 'extension'
    if lostn() > BASE: del used[p]; continue
    ext.append(p); print('extra extension', p, file=sys.stderr)
# fillers: one per strip, parked at road tile nearest the strip middle; head container (RCL<5) at strip head
FILL = []
for z in STRIPS:
    road = sorted([p for p, t in z[6].items() if t == 'road'], key=lambda p: (p[0], p[1]))
    FILL.append(road[len(road)//2])
roads = set()
def road_to(goal):
    near = {(goal[0]+a, goal[1]+b) for a, b in N8} | {goal}
    Dd = {CORE: 0}; pq = [(0, CORE)]; prev = {}; end = None
    while pq:
        d, p = heapq.heappop(pq)
        if p in near: end = p; break
        if d > Dd[p]: continue
        for a, b in N8:
            n = (p[0]+a, p[1]+b)
            if not opn(n) or (n in used and used[n] != 'road' and n not in near): continue
            c = 1 if used.get(n) == 'road' else (5 if SW(*n) else 2)
            if d+c < Dd.get(n, 1e9): Dd[n] = d+c; prev[n] = p; heapq.heappush(pq, (d+c, n))
    L = 0; p = end
    while p in prev:
        if p not in used: used[p] = 'road'; roads.add(p)
        p = prev[p]; L += 1
    return L
dist = {k: road_to(g) for k, g in [('srcN', CONT[0]), ('srcS', CONT[1]), ('ctl', CTLC), ('spawn2', SPAWN)]}
for z in STRIPS:
    head = min([p for p, t in z[6].items() if t == 'road'], key=lambda p: D.get(p, 999)); dist.setdefault('strips', []).append(road_to(head))
# ring structures: towers 6, spawns 2, powerSpawn, nuker, observer on safe free tiles nearest core keeping connectivity
ring = sorted([p for p in D if safe(p) and not reserved(p) and p not in used], key=lambda p: (D[p], p))
for t, n in [('spawn', 2), ('tower', 6), ('powerSpawn', 1), ('factory', 0 if 'factory' in used.values() else 1), ('lab', 10), ('nuker', 1), ('observer', 1)]:
    k = 0
    for p in list(ring):
        if k >= n: break
        if p in used: continue
        used[p] = t
        if lostn() > BASE: del used[p]; continue
        k += 1; ring.remove(p)
TOW = [p for p, t in used.items() if t == 'tower']
tdmg = lambda d: 600 if d <= 5 else (150 if d >= 20 else 600 - (d-5)*30)
blockroads = sum(1 for z in STRIPS for p, t in z[6].items() if t == 'road')
M = {'core': CORE, 'MINEX': MINEX, 'strips': [(z[2], z[3], z[4], 'V' if z[5] else 'H', sum(1 for p, t in z[6].items() if used.get(p) == 'extension')) for z in STRIPS],
     'ext': len([1 for t in used.values() if t == 'extension']), 'looseExt': 0, 'fillers': len(STRIPS), 'fillerWalkMax': max([z[4]-1 for z in STRIPS] or [0]),
     'minExit': min(EXD[p] for p, t in used.items() if t in ('extension', 'tower', 'storage', 'spawn')), 'roadsInBlocks': blockroads, 'roadsOutside': len(roads),
     'walk': dist, 'towerMinDmgAtExit': min(sum(tdmg(cheb(t, e)) for t in TOW) for e in EXITS) if TOW else 0, 'ramparts': 1 + 4 + len(TOW) + 2, 'cutTiles': lostn() - BASE}
print(json.dumps(M))
if len(sys.argv) > 7:
    order = lambda t: [list(p) for p in sorted([p for p, u in used.items() if u == t], key=lambda p: (D.get(p, 999), p))]
    out = {t: order(t) for t in ['spawn', 'extension', 'tower', 'storage', 'link', 'terminal', 'lab', 'factory', 'powerSpawn', 'nuker', 'observer', 'road']}
    out['extractor'] = [list(MIN)]; out['container'] = [list(CTLC)]
    # 17:52 (Misaki): north tower slots first (tools/w47n8_tower_plan.py): 24,8 (Misaki 18:06; was 27,6) east seal (540-600 on the east approach, 5 steps from the
    # source A container, outside enemy RA reach), then the built core tower 33,35 (kept, never destroyed), 22,7 (covers both seal
    # segments, RCL7), then 3 core slots for RCL8
    out['tower'] = [[24, 8], [33, 35], [22, 7], [34, 31], [36, 31], [36, 33]]
    out['rampart'] = [list(p) for p, u in used.items() if u in ('spawn', 'storage', 'terminal', 'tower')] + [list(SPAWN)]
    J = {'CORE': list(CORE), 'TEMP_EXT': [[13, 16], [14, 15], [16, 15], [17, 16], [12, 16]], 'ORDER': out,
         'STRIPS': [{'fill': list(f), 'road': [list(p) for p, t in z[6].items() if t == 'road'], 'ext': [list(p) for p, t in z[6].items() if used.get(p) == 'extension']} for z, f in zip(STRIPS, FILL)]}
    # 09:26 (Misaki link road): ext 39,30 -> 29,26 so the W47N8<->W46N8 road passes the B1 strip top
    if [39, 30] in out['extension']:
        out['extension'] = [e for e in out['extension'] if e != [39, 30]] + [[29, 26]]
        J['STRIPS'][0]['ext'] = [e for e in J['STRIPS'][0]['ext'] if e != [39, 30]]; J['STRIPS'][3]['ext'].append([29, 26])
    open(sys.argv[7], 'w').write('// GENERATED by tools/w47n8_plan3b.py (v3b, approved by Misaki 20:11). ORDER lists are nearest-core first;\n// placement walks them per type and stops at the RCL limit (CONTROLLER_STRUCTURES).\n// 09:26 (Misaki link road): ext 39,30 -> 29,26 so the W47N8<->W46N8 road passes the B1 strip top (38,30 -> 39,30 -> 40,31).\nmodule.exports = ' + json.dumps(J, separators=(',', ':')) + ';\n')
if PNG:
    S = 14; im = Image.new('RGB', (50*S, 50*S+50), 'white'); d = ImageDraw.Draw(im)
    COL = {'extension': (255, 200, 0), 'spawn': (255, 0, 255), 'tower': (220, 30, 30), 'storage': (0, 160, 0), 'terminal': (0, 100, 200), 'link': (0, 220, 220), 'road': (150, 150, 150),
           'container': (200, 120, 50), 'factory': (120, 60, 0), 'powerSpawn': (255, 100, 100), 'nuker': (60, 60, 60), 'observer': (0, 0, 120), 'rcl2ext': (255, 235, 150)}
    for y in range(50):
        for x in range(50):
            e = EXD[(x, y)]; c = (40, 40, 40) if WALL(x, y) else ((235, 150, 150) if e < 6 else ((240, 210, 170) if e < 8 else (225, 230, 210)))
            d.rectangle([x*S, y*S, x*S+S-1, y*S+S-1], fill=c)
    for (x, y), t in used.items(): d.rectangle([x*S+1, y*S+1, x*S+S-2, y*S+S-2], fill=COL.get(t, (0, 0, 0)))
    for i, z in enumerate(STRIPS):
        box = list(z[6]); xs = [p[0] for p in box]; ys = [p[1] for p in box]
        d.rectangle([min(xs)*S, min(ys)*S, max(xs)*S+S-1, max(ys)*S+S-1], outline=(0, 0, 255), width=2); d.text((min(xs)*S+2, min(ys)*S-11), 'B%d' % (i+1), fill='blue')
    for (x, y) in FILL: d.ellipse([x*S+3, y*S+3, x*S+S-4, y*S+S-4], fill=(60, 60, 255))
    for x in list(range(24, 32)) + list(range(8, 12)): d.rectangle([x*S+1, 3*S+1, x*S+S-2, 3*S+S-2], fill='black')
    for (x, y), l in [(SRC[0], 'S'), (SRC[1], 'S'), (CTL, 'C'), (MIN, 'M'), (SPAWN, '2')]: d.text((x*S+4, y*S+1), l, fill='black')
    lx = 4
    for t, c in COL.items(): d.rectangle([lx, 50*S+4, lx+10, 50*S+14], fill=c); d.text((lx+12, 50*S+3), t[:5], fill='black'); lx += 53
    d.text((4, 50*S+20), 'W47N8 v3b: extension strips B1..Bn (ext|road|ext), blue dot = walking filler, pale = temp RCL2 ext; red<6 tan 6-7 from exits', fill='black')
    d.text((4, 50*S+34), 'ext %d in %d blocks, fillers %d, roads %d+%d, min exit %d, core %s' % (M['ext'], len(STRIPS), M['fillers'], blockroads, len(roads), M['minExit'], CORE), fill='black')
    im.save(PNG)
