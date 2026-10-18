"""W47N8 plan v2 (iterative rounds). Usage: w47n8_plan2.py ROUND  -> metrics; ROUND=final writes layout.js + PNG.
Rules grow per round (see ROUND_LOG at bottom)."""
import sys, json, heapq
from collections import deque
sys.path.insert(0, 'tools'); from model import terrain
from PIL import Image, ImageDraw
R = sys.argv[1] if len(sys.argv) > 1 else 'final'; RN = 10 if R == 'final' else int(R)
T = terrain('W47N8'); WALL = lambda x, y: int(T[y*50+x]) & 1; SW = lambda x, y: int(T[y*50+x]) & 2
N8 = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
inb = lambda x, y: 0 <= x < 50 and 0 <= y < 50; opn = lambda p: inb(*p) and not WALL(*p)
SPAWN = (15, 18); SRC = [(27, 11), (11, 44)]; CONT = [(26, 11), (11, 43)]; CTL = (15, 25); CTLC = (13, 26); MIN = (37, 45)
KEEP = [(13, 16), (14, 15), (16, 15), (17, 16), (12, 16)]
EXITS = [(x, y) for x in range(50) for y in range(50) if (x in (0, 49) or y in (0, 49)) and opn((x, y))]
def bfs(starts, ok=opn):
    D = {p: 0 for p in starts}; q = deque(starts)
    while q:
        p = q.popleft()
        for dx, dy in N8:
            n = (p[0]+dx, p[1]+dy)
            if n not in D and ok(n): D[n] = D[p]+1; q.append(n)
    return D
EXD = bfs(EXITS); cheb = lambda a, b: max(abs(a[0]-b[0]), abs(a[1]-b[1]))
MINEX = 0 if RN < 2 else (8 if RN >= 10 else (7 if RN >= 6 else 6))
safe = lambda p: EXD.get(p, 0) >= MINEX and min(cheb(p, e) for e in EXITS) >= MINEX
used = {SPAWN: 'spawn', CONT[0]: 'container', CONT[1]: 'container', CTLC: 'container'}
for x in list(range(24, 32)) + list(range(8, 12)): used[(x, 3)] = 'constructedWall'
for p in KEEP: used[p] = 'extension'
# core: storage + link + terminal around hub stand 14,17? choose stand adjacent to spawn with most free neighbours
def nfree(p): return sum(opn((p[0]+dx, p[1]+dy)) and (p[0]+dx, p[1]+dy) not in used for dx, dy in N8)
HUB = max([(SPAWN[0]+dx, SPAWN[1]+dy) for dx, dy in N8 if opn((SPAWN[0]+dx, SPAWN[1]+dy)) and (SPAWN[0]+dx, SPAWN[1]+dy) not in used], key=nfree)
used[HUB] = 'road'
core = {}
for t in ['storage', 'link', 'terminal']:
    c = [(HUB[0]+dx, HUB[1]+dy) for dx, dy in N8 if opn((HUB[0]+dx, HUB[1]+dy)) and (HUB[0]+dx, HUB[1]+dy) not in used]
    if c: p = max(c, key=lambda q: -cheb(q, SPAWN)); used[p] = t; core[t] = p
def dij(a, goal_set, avoid):
    D = {a: 0}; pq = [(0, a)]; prev = {}
    while pq:
        d, p = heapq.heappop(pq)
        if p in goal_set: break
        if d > D[p]: continue
        for dx, dy in N8:
            n = (p[0]+dx, p[1]+dy)
            if not opn(n) or (n in avoid and n not in goal_set): continue
            c = 1 if used.get(n) == 'road' else (5 if SW(*n) else 2)
            if d+c < D.get(n, 1e9): D[n] = d+c; prev[n] = p; heapq.heappush(pq, (d+c, n))
    path = []; p = p
    while p in prev: path.append(p); p = prev[p]
    return path[::-1]
block = lambda: {p for p, t in used.items() if t != 'road'}
roads = set()
def road_to(g):
    near = {(g[0]+dx, g[1]+dy) for dx, dy in N8}
    for p in dij(HUB, near, block()):
        if p not in used: used[p] = 'road'; roads.add(p)
for g in CONT + [CTLC]: road_to(g)
if RN < 4: road_to((48, 20))
if RN >= 9: HUBROADS = set(roads)  # rounds 4+: no east road (creeps path fine without; saves ~35 roads upkeep)
HDMAX = int(sys.argv[2]) if len(sys.argv) > 2 else 13
# extension candidates
HD = bfs([HUB], lambda p: opn(p) and used.get(p) in (None, 'road'))
def ok_ext(p):
    if not opn(p) or p in used or not safe(p): return False
    if any(cheb(p, s) <= 1 for s in SRC + CONT + [MIN, CTLC]) or cheb(p, CTL) <= 3: return False
    if RN >= 9 and (p[0] + p[1]) % 2 != (SPAWN[0] + SPAWN[1]) % 2: return False  # checkerboard: every ext keeps a walkable neighbour
    if 3 <= RN < 9 and not any(used.get((p[0]+dx, p[1]+dy)) == 'road' for dx, dy in N8): return False  # must touch the refill spine
    if 6 <= RN < 9 and HD.get(p, 99) > HDMAX: return False
    return nfree(p) >= (5 if RN >= 5 else 4)
def grow_spine(n_ext):
    # rounds 3+: extensions only along road spines; extend spine greedily toward densest free safe area near hub
    exts = []
    while len(exts) < n_ext:
        cand = sorted([p for p in HD if ok_ext(p)], key=lambda p: HD[p])
        if cand: p = cand[0]; used[p] = 'extension'; exts.append(p); continue
        if RN < 3 or RN >= 9: break
        # add one road tile: free safe tile adjacent to an existing road, with most free safe neighbours, nearest hub
        rc = [ (r[0]+dx, r[1]+dy) for r in list(roads)+[HUB] for dx, dy in N8]
        rc = [p for p in set(rc) if opn(p) and p not in used and safe(p) and p in HD and (RN < 6 or (HD[p] <= HDMAX and sum(opn((p[0]+a, p[1]+b)) and (p[0]+a, p[1]+b) not in used and safe((p[0]+a, p[1]+b)) for a, b in N8) >= 4))]
        if not rc: break
        p = max(rc, key=lambda q: (sum(opn((q[0]+a, q[1]+b)) and (q[0]+a, q[1]+b) not in used and safe((q[0]+a, q[1]+b)) for a, b in N8) - 0.5*HD[q]))
        used[p] = 'road'; roads.add(p)
    return exts
# round 4+: filler pod: 2 filler stands next to spawn/storage; their free neighbours become extensions first (zero-walk refill)
PODS = []
if 4 <= RN < 9:
    for p in sorted([q for q in HD if opn(q) and q not in used and safe(q) and cheb(q, SPAWN) <= 3], key=lambda q: -nfree(q))[:2]:
        if p in used: continue
        used[p] = 'road'; roads.add(p); PODS.append(p)
        for dx, dy in N8:
            n = (p[0]+dx, p[1]+dy)
            if opn(n) and n not in used and safe(n) and n not in SRC: used[n] = 'extension'
EXT = [p for p, t in used.items() if t == 'extension']
EXT += grow_spine(60 + 6 + 2 - len(EXT))  # extras become towers/spawns
SEEDS = []
while 8 <= RN < 9 and len(EXT) < 68 and len(SEEDS) < 4:
    # round 8: next compact cluster at the densest safe open area (free safe tiles within r4), nearest hub as tiebreak
    dens = lambda q: sum(1 for a in range(-4, 5) for b in range(-4, 5) if opn((q[0]+a, q[1]+b)) and (q[0]+a, q[1]+b) not in used and safe((q[0]+a, q[1]+b)))
    cs = [q for q in HD if opn(q) and q not in used and safe(q) and HD[q] <= 30 and min(cheb(q, z) for z in SEEDS + [HUB]) > 6]
    if not cs: break
    sd = max(cs, key=lambda q: dens(q) - 0.6 * HD[q]); SEEDS.append(sd)
    for pth in dij(HUB, {sd}, block()) + [sd]:
        if pth not in used: used[pth] = 'road'; roads.add(pth)
    HD2 = bfs([sd], lambda p: opn(p) and used.get(p) in (None, 'road'))
    HDsave = dict(HD); HD.clear(); HD.update({k: v for k, v in HD2.items()}); HDMAX_s = HDMAX; HDMAX = 6
    EXT += grow_spine(68 - len(EXT))
    HD.clear(); HD.update(HDsave); HD.update({k: HDsave.get(k, 99) for k in HD2}); HDMAX = HDMAX_s
EXT.sort(key=lambda p: (p not in KEEP, HD.get(p, 99)))
# towers: pick 6 ext slots maximizing min damage over exit tiles (round 5), else nearest hub
def tdmg(d): return 600 if d <= 5 else (150 if d >= 20 else 600 - (d-5)*30)
pool = [p for p in EXT if p not in KEEP]
if RN >= 5:
    TOW = []
    for _ in range(6):
        best = max([p for p in pool if p not in TOW and (RN < 7 or HD.get(p, 99) <= 7)][:40] or [p for p in pool if p not in TOW][:1], key=lambda p: min(sum(tdmg(cheb(t, e)) for t in TOW+[p]) for e in EXITS))
        TOW.append(best)
else: TOW = pool[:6]
for p in TOW: used[p] = 'tower'
left = [p for p in EXT if used[p] == 'extension']
SP = [p for p in left if p not in KEEP][-2:] if RN < 10 else [p for p in left if p not in KEEP and nfree(p) >= 3][:2]  # r10: spawns beside the hub
for p in SP: used[p] = 'spawn'
EXT = [p for p in EXT if used[p] == 'extension'][:60]
for p, t in list(used.items()):
    if t == 'extension' and p not in EXT: used[p] = None; del used[p]
# connectivity check: every open non-structure tile reachable from hub
walk = lambda p: opn(p) and used.get(p) in (None, 'road', 'container', 'constructedWall' if False else None)
reach = bfs([HUB], lambda p: opn(p) and used.get(p) in (None, 'road', 'container'))
lost = [p for p in [(x, y) for x in range(50) for y in range(4, 50)] if opn(p) and used.get(p) in (None, 'road') and p not in reach and EXD.get(p, 0) > 0 and p[1] > 3]
# refill tour: stops = road tiles touching extensions; greedy nearest-neighbour from storage stand
stops = {}
for e in EXT:
    for dx, dy in N8:
        n = (e[0]+dx, e[1]+dy)
        if used.get(n) == 'road' or n == HUB: stops.setdefault(n, set()).add(e)
need = set(EXT); tour = 0; cur = HUB; RD = None; nst = 0
while need:
    Dc = bfs([cur], lambda p: opn(p) and used.get(p) in (None, 'road', 'container'))
    s = max(stops, key=lambda q: (len(stops[q] & need) > 0, len(stops[q] & need) / (1 + Dc.get(q, 99))))
    if not stops[s] & need: break
    tour += Dc.get(s, 99); need -= stops[s]; cur = s; nst += 1
podserved = sum(1 for e in EXT if any(cheb(e, p) == 1 for p in PODS))
M = {'round': RN, 'minExitDist(ext)': min(min(cheb(e, x) for x in EXITS) for e in EXT), 'ext': len(EXT), 'roads': len(roads), 'refillTourTiles': tour, 'stops': nst,
     'podServedExt': podserved, 'towerMinDmgAtExit': min(sum(tdmg(cheb(t, e)) for t in TOW) for e in EXITS), 'ramparts': 1 + len(core) + len(TOW) + len(SP),
     'unreachableTiles': len(lost), 'unplacedExt': max(0, 60 - len(EXT))}
print(json.dumps(M))
if R == 'final':
    EXTN = [0, 0, 5, 10, 20, 30, 40, 50, 60]; TOWN = [0, 0, 0, 1, 1, 2, 2, 3, 6]; SPN = [0, 0, 0, 0, 0, 0, 0, 1, 2]
    LS = [next(((c[0]+a, c[1]+b) for a, b in N8 if opn((c[0]+a, c[1]+b)) and (c[0]+a, c[1]+b) not in used), None) for c in CONT + [CTLC]]
    for p in LS:
        if p: used[p] = 'link'
    rl = sorted(roads, key=lambda p: HD.get(p, 99))
    B = {}
    for r in range(2, 9):
        b = {'extension': EXT[:EXTN[r]], 'tower': TOW[:TOWN[r]], 'container': [CTLC]}
        if r >= 3: b['road'] = rl
        if r >= 4: b['storage'] = [core['storage']]
        if r >= 5: b['link'] = [core['link'], LS[2]]
        if r >= 6: b['link'] = b['link'] + [LS[0]]; b['terminal'] = [core['terminal']]; b['extractor'] = [MIN]
        if r >= 7: b['link'] = b['link'] + [LS[1]]; b['spawn'] = SP[:1]
        if r >= 8: b['spawn'] = SP[:2]
        B[r] = {k: [list(p) for p in v if p] for k, v in b.items()}
    RAMP = [list(SPAWN)] + [list(p) for p in list(core.values()) + TOW + SP]
    open('src/rooms/w47n8/layout.js', 'w').write('// GENERATED by tools/w47n8_plan2.py (v2: exit dist >=6, road-spine extensions, 2 filler pods, tower min-dmg). Cumulative per RCL.\n'
        'module.exports = ' + json.dumps({'HUB': list(HUB), 'PODS': [list(p) for p in PODS], 'BUILD': B, 'RAMPARTS_RCL4': RAMP, 'METRICS': M}) + ';\n')
    S = 14; im = Image.new('RGB', (50*S, 50*S+44), 'white'); d = ImageDraw.Draw(im)
    COL = {'extension': (255, 200, 0), 'spawn': (255, 0, 255), 'tower': (220, 30, 30), 'storage': (0, 160, 0), 'terminal': (0, 100, 200), 'link': (0, 220, 220),
           'road': (150, 150, 150), 'container': (200, 120, 50), 'constructedWall': (0, 0, 0)}
    rof = {}
    for r in range(8, 1, -1):
        for k, v in B[r].items():
            for p in v: rof[(tuple(p), k)] = r
    for y in range(50):
        for x in range(50):
            if WALL(x, y): c = (40, 40, 40)
            else: e = min(cheb((x, y), q) for q in EXITS); c = (235, 150, 150) if e < 6 else ((240, 210, 170) if e < 9 else (225, 230, 210))
            d.rectangle([x*S, y*S, x*S+S-1, y*S+S-1], fill=c)
    for p, t in used.items():
        if not t: continue
        x, y = p; d.rectangle([x*S+1, y*S+1, x*S+S-2, y*S+S-2], fill=COL.get(t, (0, 0, 0)))
        r = rof.get((p, t))
        if r and t not in ('road',): d.text((x*S+3, y*S+1), str(r), fill='black')
    for p in PODS: d.ellipse([p[0]*S+3, p[1]*S+3, p[0]*S+S-3, p[1]*S+S-3], fill=(0, 0, 255))
    for (x, y), l in [(SRC[0], 'S'), (SRC[1], 'S'), (CTL, 'C'), (MIN, 'M')]: d.ellipse([x*S, y*S, x*S+S, y*S+S], fill='white', outline='black'); d.text((x*S+4, y*S+1), l, fill='black')
    lx = 4
    for t, c in COL.items(): d.rectangle([lx, 50*S+6, lx+10, 50*S+16], fill=c); d.text((lx+13, 50*S+5), t[:6], fill='black'); lx += 60
    d.text((4, 50*S+22), 'W47N8 v2: number=RCL; blue dot=filler stand; red shade <6 tiles from exit, tan 6-8', fill='black')
    d.text((4, 50*S+32), json.dumps(M)[:115], fill='black')
    im.save('/workspace/w47n8_layout_v2_final.png')
