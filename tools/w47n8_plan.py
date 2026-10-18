"""Generate W47N8 base plan (checkerboard extension field + core hub + lab block + roads), fitted to terrain.
Writes src/rooms/w47n8/layout.js and /workspace/w47n8_layout.png."""
import sys, json, heapq
sys.path.insert(0, 'tools'); from model import terrain
from PIL import Image, ImageDraw
T = terrain('W47N8'); WALL = lambda x, y: int(T[y*50+x]) & 1; SW = lambda x, y: int(T[y*50+x]) & 2
SPAWN = (15, 18); SRC = [(27, 11), (11, 44)]; CONT = [(26, 11), (11, 43)]; CTL = (15, 25); CTLC = (13, 26); MIN = (37, 45)
KEEP_EXT = [(13, 16), (14, 15), (16, 15), (17, 16), (12, 16)]  # built / in progress, kept
SEAL = [(x, 3) for x in list(range(24, 32)) + list(range(8, 12))]
N8 = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
inb = lambda x, y: 0 <= x < 50 and 0 <= y < 50
opn = lambda x, y: inb(x, y) and not WALL(x, y)
used = {}  # (x,y) -> type
def put(p, t): used[p] = t
put(SPAWN, 'spawn'); [put(c, 'container') for c in CONT]; put(CTLC, 'container'); [put(p, 'constructedWall') for p in SEAL]
def dij(src, goal, cost_road=1):
    D = {src: 0}; pq = [(0, src)]; prev = {}
    while pq:
        d, p = heapq.heappop(pq)
        if p == goal: break
        if d > D[p]: continue
        for dx, dy in N8:
            q = (p[0]+dx, p[1]+dy)
            if not opn(*q) or (used.get(q) not in (None, 'road') and q != goal): continue
            c = 1 if used.get(q) == 'road' else (5 if SW(*q) else 2)
            if d + c < D.get(q, 1e9): D[q] = d + c; prev[q] = p; heapq.heappush(pq, (d + c, q))
    path = []; p = goal
    while p in prev: path.append(p); p = prev[p]
    return path[::-1]
# hub: open tile at range 2 of spawn with most open neighbours; storage/terminal/link/factory/powerSpawn around it
cand = sorted([(x, y) for x in range(SPAWN[0]-3, SPAWN[0]+4) for y in range(SPAWN[1]-3, SPAWN[1]+4) if opn(x, y) and (x, y) not in used and (x, y) not in KEEP_EXT],
              key=lambda p: (-sum(opn(p[0]+dx, p[1]+dy) and (p[0]+dx, p[1]+dy) not in KEEP_EXT for dx, dy in N8), abs(p[0]-SPAWN[0])+abs(p[1]-SPAWN[1])))
HUB = cand[0]; put(HUB, 'road')
ring = [(HUB[0]+dx, HUB[1]+dy) for dx, dy in N8 if opn(HUB[0]+dx, HUB[1]+dy) and (HUB[0]+dx, HUB[1]+dy) not in used and (HUB[0]+dx, HUB[1]+dy) not in KEEP_EXT]
core = {}
for t, p in zip(['storage', 'link', 'terminal', 'factory', 'powerSpawn'], ring): put(p, t); core[t] = p
for p in KEEP_EXT: put(p, 'extension')
# roads: spawn/hub -> containers, controller container, east exit (home), mineral
roads = []
for g in CONT + [CTLC, (49, 20), (37, 44)]:
    path = dij(HUB, g)
    for p in path:
        if p != g and used.get(p) in (None, 'road'): put(p, 'road'); roads.append(p)
# walking distance from hub for ordering
D = {HUB: 0}; Q = [HUB]
for p in Q:
    for dx, dy in N8:
        q = (p[0]+dx, p[1]+dy)
        if opn(*q) and q not in D and used.get(q) in (None, 'road', 'extension') or q == SPAWN and q not in D: D[q] = D[p]+1; Q.append(q)
def free(p, margin=1):
    x, y = p
    if not opn(x, y) or p in used or x < 2 or y < 5 or x > 47 or y > 47: return False
    if any(max(abs(x-a), abs(y-b)) <= 1 for a, b in SRC + CONT + [MIN]): return False
    if max(abs(x-CTLC[0]), abs(y-CTLC[1])) <= 1 or max(abs(x-CTL[0]), abs(y-CTL[1])) <= 2: return False
    return sum(opn(x+dx, y+dy) for dx, dy in N8) >= 6  # never plug a corridor
order = sorted([p for p in D if free(p)], key=lambda p: D[p])
# lab block 4x4 nearest hub: diagonal road, 10 labs, sources at (1,2),(2,1)
LABS = []
for p in order:
    blk = [(p[0]+i, p[1]+j) for i in range(4) for j in range(4)]
    if all(q in D and free(q) for q in blk if True) and all(free(q) for q in blk):
        for i in range(4):
            for j in range(4):
                q = (p[0]+i, p[1]+j)
                if i == j: put(q, 'road')
                elif (i, j) not in ((0, 3), (3, 0)): LABS.append(q); put(q, 'lab')
        LABS.sort(key=lambda q: (q != (p[0]+1, p[1]+2) and q != (p[0]+2, p[1]+1)))  # 2 source labs first
        break
# towers (6) + spawns (2 more) + nuker + observer near hub, then 55 more extensions: checkerboard parity of spawn (odd)
par = (SPAWN[0]+SPAWN[1]) % 2
field = [p for p in sorted(D, key=lambda p: D[p]) if free(p) and (p[0]+p[1]) % 2 == par]
take = lambda n, t: [put(p, t) or p for p in [f for f in field if f not in used][:n]]
TOW = take(6, 'tower'); SP = take(2, 'spawn'); EXT = KEEP_EXT + take(55, 'extension'); NUK = take(1, 'nuker'); OBS = take(1, 'observer')
# links: source links next to miner stands, controller link next to ctl container
def adj_free(c):
    for dx, dy in N8:
        q = (c[0]+dx, c[1]+dy)
        if opn(*q) and q not in used: return q
LSRC = [adj_free(c) for c in CONT]; [put(q, 'link') for q in LSRC]; LCTL = adj_free(CTLC); put(LCTL, 'link')
# per-RCL lists (cumulative counts from CONTROLLER_STRUCTURES)
EXTN = [0, 0, 5, 10, 20, 30, 40, 50, 60]; TOWN = [0, 0, 0, 1, 1, 2, 2, 3, 6]; LABN = [0]*6 + [3, 6, 10]; SPN = [0, 1, 1, 1, 1, 1, 1, 2, 3]
BUILD = {}
for r in range(2, 9):
    b = {'extension': EXT[:EXTN[r]], 'tower': TOW[:TOWN[r]]}
    if r >= 4: b['storage'] = [core['storage']]
    if r >= 5: b['link'] = [core['link'], LCTL]
    if r >= 6: b['link'].append(LSRC[0]); b['terminal'] = [core['terminal']]; b['extractor'] = [MIN]; b['lab'] = LABS[:3]; b['container'] = [CTLC]
    if r >= 7: b['link'].append(LSRC[1]); b['lab'] = LABS[:6]; b['factory'] = [core['factory']]; b['spawn'] = SP[:1]
    if r >= 8: b['lab'] = LABS[:10]; b['spawn'] = SP[:2]; b['powerSpawn'] = [core['powerSpawn']]; b['nuker'] = NUK; b['observer'] = OBS
    b.setdefault('container', [CTLC])
    if r >= 3: b['road'] = roads
    BUILD[r] = {k: [list(p) for p in v if p] for k, v in b.items()}
RAMP = [list(SPAWN)] + [list(p) for p in [core['storage'], core['terminal']] + TOW + SP]
open('src/rooms/w47n8/layout.js', 'w').write('// GENERATED by tools/w47n8_plan.py (checkerboard extension field + hub core + 4x4 lab block). Cumulative per RCL.\n'
    'module.exports = ' + json.dumps({'HUB': list(HUB), 'BUILD': BUILD, 'RAMPARTS_RCL4': RAMP}) + ';\n')
# render
S = 14; im = Image.new('RGB', (50*S, 50*S + 40), 'white'); d = ImageDraw.Draw(im)
COL = {'extension': (255, 200, 0), 'spawn': (255, 0, 255), 'tower': (220, 30, 30), 'storage': (0, 160, 0), 'terminal': (0, 100, 200), 'link': (0, 220, 220), 'lab': (150, 80, 200),
       'factory': (120, 60, 0), 'powerSpawn': (255, 100, 100), 'nuker': (60, 60, 60), 'observer': (0, 0, 120), 'road': (170, 170, 170), 'container': (200, 120, 50), 'constructedWall': (0, 0, 0)}
rcl_of = {}
for r in range(8, 1, -1):
    for k, v in BUILD[r].items():
        for p in v: rcl_of[(tuple(p), k)] = r
for y in range(50):
    for x in range(50):
        d.rectangle([x*S, y*S, x*S+S-1, y*S+S-1], fill=(40, 40, 40) if WALL(x, y) else ((150, 170, 110) if SW(x, y) else (225, 225, 210)))
for p, t in used.items():
    x, y = p; d.rectangle([x*S+1, y*S+1, x*S+S-2, y*S+S-2], fill=COL.get(t, (0, 0, 0)))
    r = rcl_of.get((p, t))
    if r and t != 'road': d.text((x*S+3, y*S+1), str(r), fill='black')
for (x, y), lab in [(SRC[0], 'S'), (SRC[1], 'S'), (CTL, 'C'), (MIN, 'M')]: d.ellipse([x*S, y*S, x*S+S, y*S+S], fill=(255, 255, 255), outline='black'); d.text((x*S+4, y*S+1), lab, fill='black')
lx = 4
for t, c in COL.items(): d.rectangle([lx, 50*S+8, lx+10, 50*S+18], fill=c); d.text((lx+13, 50*S+7), t[:6], fill='black'); lx += 50
d.text((4, 50*S+24), 'W47N8 plan: number = RCL the structure unlocks at', fill='black')
im.save('/workspace/w47n8_layout.png')
print('HUB', HUB, 'core', core, 'labs', LABS[:2], 'towers', TOW, 'spawns', SP, 'links', LSRC, LCTL, 'ext', len(EXT), 'roads', len(roads))
