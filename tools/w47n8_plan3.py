"""W47N8 plan v3: 3 filler pods (5x5, 18 ext + 4 fixed fillers + central link, 2 entrance roads) + compact core. Review only.
usage: w47n8_plan3.py MINEX HUBMODE [png]"""
import sys, json, heapq
from collections import deque
sys.path.insert(0, 'tools'); from model import terrain
from PIL import Image, ImageDraw
MINEX = int(sys.argv[1]); HUBMODE = sys.argv[2]; PNG = sys.argv[3] if len(sys.argv) > 3 else None
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
for p in [(13, 16), (14, 15), (16, 15), (17, 16), (12, 16)]: used[p] = 'extension'  # RCL2 set (built/in progress)
reserved = lambda p: p in used or any(cheb(p, s) <= 1 for s in SRC + CONT + [CTLC, MIN]) or cheb(p, CTL) <= 3
# pod stamp (dx,dy)->type ; entrances N/S at (0,-2),(0,2)
POD = {}
for dx in range(-2, 3):
    for dy in range(-2, 3):
        POD[(dx, dy)] = 'road' if dx == 0 else ('filler' if abs(dx) == 1 and abs(dy) == 1 else 'extension')  # through-road pod: hauler on (0,0) feeds all 4 fillers
KMIN = int(sys.argv[4]) if len(sys.argv) > 4 else 18
def cell(c, rot, dx, dy): return (c[0]+(dy if rot else dx), c[1]+(dx if rot else dy))
def pod_ext(c, rot):
    n = 0
    for (dx, dy), t in POD.items():
        p = cell(c, rot, dx, dy)
        if t == 'extension':
            if safe(p) and not reserved(p): n += 1
            elif opn(p): return -1  # open but blocked (reserved/unsafe) -> skip candidate (keeps pods clean)
        elif t in ('road', 'filler') and (not safe(p) or reserved(p)): return -1
    return n
def pod_ok(c, rot):
    if pod_ext(c, rot) < KMIN: return False
    ents = [cell(c, rot, 0, -2), cell(c, rot, 0, 2)]
    return any(safe(e) and not reserved(e) for e in ents)
def stamp(c, rot):
    for (dx, dy), t in POD.items():
        p = cell(c, rot, dx, dy)
        if t == 'road' and not (safe(p) and not reserved(p)): continue
        if opn(p): used[p] = t
def lostn():
    free = [(x, y) for x in range(1, 49) for y in range(4, 49) if opn((x, y)) and (used.get((x, y)) in (None, 'road', 'filler'))]
    D = bfs([SPAWN], lambda p: opn(p) and (used.get(p) in (None, 'road', 'filler') or p == SPAWN))
    return sum(1 for f in free if f not in D)
def connected(slack=4): return lostn() <= slack
cands = [((x, y), r) for x in range(2, 48) for y in range(2, 48) for r in (0, 1) if pod_ok((x, y), r)]
WD = bfs([SPAWN], lambda p: opn(p) and p not in used or p == SPAWN)
# choose hub area
if HUBMODE == 'spawn': ANCHOR = SPAWN
else:  # densest safe area: anchor = candidate pod centre with most other pod candidates within 9
    ANCHOR = max({c for c, r in cands}, key=lambda c: sum(1 for d, r in cands if cheb(c, d) <= 9) - 0.15 * WD.get(c, 99))
PODS = []
MAN = json.loads(sys.argv[6]) if len(sys.argv) > 6 else None   # manual: {"pods":[[x,y,rot],..],"core":[x,y]}
if MAN:
    for x, y, r in MAN['pods']:
        stamp((x, y), r); PODS.append(((x, y), r))
    ANCHOR = tuple(MAN['core'])
else:
  for _ in range(int(sys.argv[5]) if len(sys.argv) > 5 else 3):
    ok = [(c, r) for c, r in cands if pod_ok(c, r)]
    if not ok: break
    D = bfs([ANCHOR], lambda p: opn(p))
    ok.sort(key=lambda cr: D.get(cr[0], 999) + (0 if not PODS else 0.5 * min(cheb(cr[0], q) for q, _ in PODS)))
    placed = False
    for c, r in ok[:60]:
        snap = dict(used); stamp(c, r)
        if connected(): PODS.append((c, r)); placed = True; break
        used.clear(); used.update(snap)
    if not placed: break
# core (storage, terminal, hub link, factory, power, 6 towers, nuker, observer, 2 spawns) checkerboard around the core stand
CORE = ANCHOR if (HUBMODE == 'spawn' or MAN) else min([p for p in bfs([PODS[0][0]], opn) if safe(p) and not reserved(p) and sum(1 for a, b in N8 if safe((p[0]+a, p[1]+b)) and not reserved((p[0]+a, p[1]+b))) >= 7],
                                            key=lambda p: sum(cheb(p, q) for q, _ in PODS))
if HUBMODE != 'spawn': used[CORE] = 'road'
if HUBMODE == 'spawn' and not MAN:
    CORE = max([(SPAWN[0]+a, SPAWN[1]+b) for a, b in N8 if opn((SPAWN[0]+a, SPAWN[1]+b)) and (SPAWN[0]+a, SPAWN[1]+b) not in used], key=lambda p: sum(opn((p[0]+a, p[1]+b)) and (p[0]+a, p[1]+b) not in used for a, b in N8))
    used[CORE] = 'road'
order = ['storage', 'link', 'terminal', 'factory', 'powerSpawn']
ring = sorted([p for p in bfs([CORE], lambda p: opn(p) and (p not in used or used[p] == 'road')) if safe(p) and not reserved(p)], key=lambda p: (cheb(p, CORE), -sum(opn((p[0]+a, p[1]+b)) for a, b in N8)))
coreT = {}
for a, b in ((0, 1), (0, -1), (1, 0), (-1, 0)):
    q = (CORE[0]+a, CORE[1]+b)
    if opn(q) and q not in used: used[q] = 'road'
for t in order:
    p = next(q for q in ring if q not in used and cheb(q, CORE) == 1) if any(q not in used and cheb(q, CORE) == 1 for q in ring) else next(q for q in ring if q not in used)
    used[p] = t; coreT[t] = p
par = (CORE[0] + CORE[1]) % 2
BASE_LOST = lostn()
rest = [p for p in ring if p not in used and (p[0]+p[1]) % 2 != par]
EXTRA = {'tower': 6, 'spawn': 2, 'nuker': 1, 'observer': 1}
ext_needed = 60 - sum(1 for p, t in used.items() if t == 'extension')
for t, n in list(EXTRA.items()) + [('extension', ext_needed)]:
    for _ in range(max(0, n)):
        if not rest: break
        p = rest.pop(0); used[p] = t
        if lostn() > BASE_LOST: del used[p]; continue
# roads: core -> each pod entrance, -> source containers, -> ctl container, -> Spawn2
roads = set()
def road(a, goal):
    near = {(goal[0]+x, goal[1]+y) for x, y in N8} | {goal}
    D = {a: 0}; pq = [(0, a)]; prev = {}; end = None
    while pq:
        d, p = heapq.heappop(pq)
        if p in near: end = p; break
        if d > D[p]: continue
        for x, y in N8:
            n = (p[0]+x, p[1]+y)
            if not opn(n) or (n in used and used[n] != 'road' and n not in near): continue
            c = 1 if used.get(n) == 'road' else (5 if SW(*n) else 2)
            if d+c < D.get(n, 1e9): D[n] = d+c; prev[n] = p; heapq.heappush(pq, (d+c, n))
    p = end; L = 0
    while p in prev:
        if p not in used: used[p] = 'road'; roads.add(p)
        p = prev[p]; L += 1
    return L
pl = [road(CORE, next(e for e in [cell(c, r, 0, -2), cell(c, r, 0, 2)] if used.get(e) == 'road')) for c, r in PODS]
sl = [road(CORE, g) for g in CONT + [CTLC]]; s2 = road(CORE, SPAWN)
ext_all = [p for p, t in used.items() if t == 'extension']
tdmg = lambda d: 600 if d <= 5 else (150 if d >= 20 else 600 - (d-5)*30)
TOW = [p for p, t in used.items() if t == 'tower']
M = {'MINEX': MINEX, 'hub': HUBMODE, 'pods': len(PODS), 'extInPods': sum(1 for p, t in used.items() if t == 'extension') - 5 - max(0, ext_needed), 'extTotal': len(ext_all), 'fillers': 4*len(PODS), 'blocks': len(PODS) + (1 if ext_needed > 0 else 0) + 1,
     'minExitDist': min(EXD[p] for p in ext_all + TOW + [coreT['storage']]), 'core': CORE, 'podCenters': [c for c, r in PODS], 'coreToPodWalk': pl, 'roadsTotal': len(roads),
     'coreToSrcCtl': sl, 'coreToSpawn2': s2, 'towerMinDmgAtExit': min(sum(tdmg(cheb(t, e)) for t in TOW) for e in EXITS) if TOW else 0,
     'refillWalk': 'pods: 0 (fillers static, link-fed); hub extras: ~%d tiles' % (2 * max(1, ext_needed // 6)), 'ramparts(core+towers+spawns)': 1 + len(coreT) + len(TOW) + 2}
M['podExt'] = [sum(1 for (dx, dy), t in POD.items() if t == 'extension' and used.get(cell(c, r, dx, dy)) == 'extension') for c, r in PODS]
M['lostTiles'] = lostn()
print(json.dumps(M))
if PNG:
    S = 14; im = Image.new('RGB', (50*S, 50*S+48), 'white'); d = ImageDraw.Draw(im)
    COL = {'extension': (255, 200, 0), 'spawn': (255, 0, 255), 'tower': (220, 30, 30), 'storage': (0, 160, 0), 'terminal': (0, 100, 200), 'link': (0, 220, 220), 'filler': (60, 60, 255),
           'road': (150, 150, 150), 'container': (200, 120, 50), 'factory': (120, 60, 0), 'powerSpawn': (255, 100, 100), 'nuker': (60, 60, 60), 'observer': (0, 0, 120)}
    for y in range(50):
        for x in range(50):
            e = EXD[(x, y)]
            c = (40, 40, 40) if WALL(x, y) else ((235, 150, 150) if e < 6 else ((240, 210, 170) if e < 8 else (225, 230, 210)))
            d.rectangle([x*S, y*S, x*S+S-1, y*S+S-1], fill=c)
    for (x, y), t in used.items():
        if t == 'filler': d.ellipse([x*S+2, y*S+2, x*S+S-3, y*S+S-3], fill=COL[t])
        else: d.rectangle([x*S+1, y*S+1, x*S+S-2, y*S+S-2], fill=COL.get(t, (0, 0, 0)))
    for x in list(range(24, 32)) + list(range(8, 12)): d.rectangle([x*S+1, 3*S+1, x*S+S-2, 3*S+S-2], fill='black')
    for (x, y), l in [(SRC[0], 'S'), (SRC[1], 'S'), (CTL, 'C'), (MIN, 'M'), (SPAWN, '2')]: d.text((x*S+4, y*S+1), l, fill='black')
    lx = 4
    for t, c in COL.items(): d.rectangle([lx, 50*S+4, lx+10, 50*S+14], fill=c); d.text((lx+12, 50*S+3), t[:5], fill='black'); lx += 53
    d.text((4, 50*S+20), 'W47N8 v3 (review): 3 filler pods (blue dot = fixed filler, cyan = pod link), core hub; red <6 tan 6-7 from exits', fill='black')
    d.text((4, 50*S+32), ('pods %d, ext %d, roads %d, min exit %d, core %s' % (M['pods'], M['extTotal'], M['roadsTotal'], M['minExitDist'], M['core'])), fill='black')
    im.save(PNG)
