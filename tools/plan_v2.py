#!/usr/bin/env python3
"""Layout v2 planner for W46N8: hub (stationary manager) + 3 fast-filler stamps + link economy.
Writes data/layout_W46N8_v2.json, docs/layout_W46N8_v2.png, docs/layout_W46N8_v2_rcl.png and prints metrics."""
import json, heapq, itertools, os, collections
from PIL import Image, ImageDraw
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOM = 'W46N8'; T = open(f'{ROOT}/data/terrain_{ROOM}.txt').read()
SPAWN1 = (35, 28); CTL = (28, 32); SRC = [(32, 11), (39, 33)]; MIN = (40, 24)
N8 = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
def wall(p): x, y = p; return not (0 <= x < 50 and 0 <= y < 50) or T[y*50+x] in '13'
def swamp(p): return T[p[1]*50+p[0]] == '2'
cheb = lambda a, b: max(abs(a[0]-b[0]), abs(a[1]-b[1]))
def inner(p): return 2 <= p[0] <= 47 and 2 <= p[1] <= 47
NEAR_OBJ = [CTL, MIN] + SRC

def dijkstra(starts, blocked, roads=frozenset(), goal=None):
    D = {s: 0 for s in starts}; P = {}; pq = [(0, s) for s in starts]; heapq.heapify(pq)
    while pq:
        d, u = heapq.heappop(pq)
        if d > D[u]: continue
        if goal and goal(u): return D, P, u
        for dx, dy in N8:
            v = (u[0]+dx, u[1]+dy)
            if wall(v) or v in blocked or not (1 <= v[0] <= 48 and 1 <= v[1] <= 48): continue
            nd = d + (1 if v in roads else 10 if swamp(v) else 2)
            if nd < D.get(v, 1e9): D[v] = nd; P[v] = u; heapq.heappush(pq, (nd, v))
    return D, P, None
def path_to(start, goal_fn, blocked, roads):
    D, P, end = dijkstra([start], blocked, roads, goal_fn)
    if end is None: return None
    out = [end]
    while out[-1] != start: out.append(P[out[-1]])
    return out[::-1]

# ---- fast-filler stamp (5x5): F = stationary fillers, L = link (centre), K = container (entrance, walkable),
# S = spawn slot (opposite K), E = extension. Fillers on F(1,1)/(3,1) enter via K; F(1,3)/(3,3) are spawned in place.
BASE = {(1, 1): 'F', (3, 1): 'F', (1, 3): 'F', (3, 3): 'F', (2, 2): 'L', (2, 0): 'K', (2, 4): 'S'}
def rot(i, j, r):
    for _ in range(r): i, j = 4 - j, i
    return i, j
def stamp(ox, oy, r):
    out = {}
    for i in range(5):
        for j in range(5):
            out[(ox + rot(i, j, r)[0], oy + rot(i, j, r)[1])] = BASE.get((i, j), 'E')
    return out
def stamp_ok(st, occ):
    return all(not wall(p) and inner(p) and p not in occ and all(cheb(p, o) > 1 for o in NEAR_OBJ) for p in st)
def entry_tile(st):  # outside tile adjacent to the container K, on the side away from the stamp
    k = next(p for p, t in st.items() if t == 'K')
    return [(k[0]+dx, k[1]+dy) for dx, dy in N8 if (k[0]+dx, k[1]+dy) not in st and not wall((k[0]+dx, k[1]+dy))]

def connected(blocked, pts):
    D, _, _ = dijkstra([pts[0]], blocked)
    return all(any((p[0]+dx, p[1]+dy) in D for dx, dy in N8) or p in D for p in pts[1:])

def plan(rA):
    occ = {}  # pos -> (type, rcl, note)
    # Filler A containing SPAWN1 on its S slot
    sA = None
    for r in range(4):
        for ox in range(SPAWN1[0]-4, SPAWN1[0]+1):
            for oy in range(SPAWN1[1]-4, SPAWN1[1]+1):
                st = stamp(ox, oy, r)
                if r == rA and st.get(SPAWN1) == 'S' and stamp_ok(st, occ): sA = st
    if not sA: return None
    fillers = {'A': sA}
    for p, t in sA.items(): occ[p] = t
    # distance fields from key objects (no roads yet)
    def field(targets): return dijkstra([q for t in targets for q in [(t[0]+dx, t[1]+dy) for dx, dy in N8] if not wall(q)], set())[0]
    dS0, dC, dB = field([SRC[0]]), field([CTL]), field([SRC[1]])
    dA = dijkstra(entry_tile(sA), set(sA))[0]
    # Hub: manager M with 8 neighbours. Storage on a neighbour that is adjacent to a source-B miner spot gets a big bonus.
    best = None
    minerB_spots = [q for q in [(SRC[1][0]+dx, SRC[1][1]+dy) for dx, dy in N8] if not wall(q)]
    for mx in range(3, 47):
        for my in range(3, 47):
            M = (mx, my); box = [M] + [(mx+dx, my+dy) for dx, dy in N8]
            if any(wall(p) or p in occ or any(cheb(p, o) <= 1 for o in NEAR_OBJ) for p in box): continue
            if M not in dA or M not in dS0 or M not in dC: continue
            for sp in box[1:]:
                bonusB = any(cheb(sp, q) == 1 and q not in box for q in minerB_spots)
                # storage needs an outside neighbour (hauler door)
                doors = [(sp[0]+dx, sp[1]+dy) for dx, dy in N8 if (sp[0]+dx, sp[1]+dy) not in box and not wall((sp[0]+dx, sp[1]+dy)) and (sp[0]+dx, sp[1]+dy) not in occ]
                if not doors: continue
                sc = dA[M] * 1.0 + dS0[M] * 1.0 + dC[M] * 1.5 + (0 if bonusB else dB.get(M, 99) * 1.0 + 40)
                if not best or sc < best[0]: best = (sc, M, sp, bonusB, box)
    if not best: return None
    _, M, SP, bonusB, box = best
    hub = {'manager': M, 'storage': SP}
    occ[M] = 'M'; occ[SP] = 'storage'
    rest = [p for p in box[1:] if p != SP]
    # spawn3/door: the hub neighbour with the best outside access, so the manager can walk in before RCL8
    def outside(p): return [(p[0]+dx, p[1]+dy) for dx, dy in N8 if (p[0]+dx, p[1]+dy) not in box and not wall((p[0]+dx, p[1]+dy))]
    rest.sort(key=lambda p: -len(outside(p)))
    door = rest.pop(0); occ[door] = 'spawn3'
    for name in ['terminal', 'link', 'factory', 'powerSpawn', 'ext', 'ext']:
        p = rest.pop(0); occ[p] = 'hub_' + name if name != 'ext' else 'hubext'
    # Source miner spots (+container/link). Source B: adjacent to storage if possible.
    miners = {}
    for i, s in enumerate(SRC):
        spots = [q for q in [(s[0]+dx, s[1]+dy) for dx, dy in N8] if not wall(q) and q not in occ]
        if i == 1 and bonusB:
            spots = [q for q in spots if cheb(q, SP) == 1]
        D = dijkstra([SP], set(occ))[0]
        spots.sort(key=lambda q: D.get(q, 1e9))
        miners[i] = spots[0]; occ[spots[0]] = f'miner{i}'
    # source link next to miner A spot (not on the road side)
    # Controller: link L + upgrader spots (range<=3 of controller, adjacent to L); container on one upgrader spot
    best = None
    for lx in range(CTL[0]-4, CTL[0]+5):
        for ly in range(CTL[1]-4, CTL[1]+5):
            L = (lx, ly)
            if wall(L) or L in occ or cheb(L, CTL) > 3 or cheb(L, CTL) < 2: continue
            U = [(lx+dx, ly+dy) for dx, dy in N8 if not wall((lx+dx, ly+dy)) and (lx+dx, ly+dy) not in occ and cheb((lx+dx, ly+dy), CTL) <= 3 and cheb((lx+dx, ly+dy), CTL) >= 1]
            sc = -len(U) * 10 + dijkstra([SP], set(occ))[0].get(L, 999) * 0.1
            if len(U) >= 3 and (not best or sc < best[0]): best = (sc, L, U)
    _, CL, U = best
    occ[CL] = 'ctl_link'
    Dsp = dijkstra([SP], set(occ))[0]
    U.sort(key=lambda q: Dsp.get(q, 999))
    ups = U[:4]; ctl_cont = ups[0]
    for q in ups: occ[q] = 'upgrader'
    # Fillers B and C: nearest valid stamps to storage, keep everything connected
    for name in ['B', 'C']:
        cand = []
        D = dijkstra([SP], set(occ))[0]
        for r in range(4):
            for ox in range(2, 44):
                for oy in range(2, 44):
                    st = stamp(ox, oy, r)
                    if not stamp_ok(st, occ): continue
                    e = [q for q in entry_tile(st) if q in D]
                    if not e: continue
                    cand.append((min(D[q] for q in e), st))
        cand.sort(key=lambda c: c[0])
        for _, st in cand:
            blocked = set(occ) | set(st)
            keys = [miners[0], miners[1], ctl_cont, MIN] + entry_tile(fillers['A'])
            if connected(blocked - {miners[0], miners[1], ctl_cont}, [next(iter(outside(door)))] + keys):
                fillers[name] = st
                for p, t in st.items(): occ[p] = t
                break
    # Source A link (adjacent to miner spot), mineral container + extractor
    mA = miners[0]
    sl = [q for q in [(mA[0]+dx, mA[1]+dy) for dx, dy in N8] if not wall(q) and q not in occ and q not in SRC]
    Dsp = dijkstra([SP], set(occ))[0]
    sl.sort(key=lambda q: -Dsp.get(q, 0))  # away from the road side
    srcA_link = sl[0]; occ[srcA_link] = 'srcA_link'
    mm = sorted([q for q in [(MIN[0]+dx, MIN[1]+dy) for dx, dy in N8] if not wall(q) and q not in occ], key=lambda q: Dsp.get(q, 999))[0]
    occ[mm] = 'mineral_cont'
    # Roads: from storage door to every traffic endpoint, merged (planned road cost 1)
    roads = set(); routes = {}
    doorsS = [(SP[0]+dx, SP[1]+dy) for dx, dy in N8 if (SP[0]+dx, SP[1]+dy) not in occ and not wall((SP[0]+dx, SP[1]+dy))]
    hub_door = outside(door)
    targets = [('srcA', lambda u: cheb(u, mA) <= 1 and u != mA, True), ('ctl', lambda u: cheb(u, ctl_cont) <= 1, True),
               ('mineral', lambda u: cheb(u, mm) <= 1, True)]
    for n, st in fillers.items():
        e = set(entry_tile(st)); targets.append((f'filler{n}', lambda u, e=e: u in e, True))
    if not bonusB: targets.append(('srcB', lambda u: cheb(u, miners[1]) <= 1, True))
    targets.append(('hubdoor', lambda u: u in hub_door, True))
    start = doorsS[0]
    for n, g, _ in targets:
        blocked = set(occ)
        p = path_to(start, g, blocked, roads)
        routes[n] = p; roads.update(p)
    for p in roads: occ.setdefault(p, 'road')
    # Labs (4x4, diagonal road, inputs (1,2),(2,1)), towers, nuker, observer: nearest free spots by road distance
    D = dijkstra(list(roads), set(o for o, t in occ.items() if t != 'road'), roads)[0]
    def adj_road(p): return any((p[0]+dx, p[1]+dy) in roads for dx, dy in N8)
    labs = None
    for bx in range(2, 45):
        for by in range(2, 45):
            tiles = [(bx+i, by+j) for i in range(4) for j in range(4)]
            if any(wall(t) or (t in occ and occ[t] != 'road') or any(cheb(t, o) <= 1 for o in NEAR_OBJ) for t in tiles): continue
            if any(occ.get((bx+i, by+j)) == 'road' for i in range(4) for j in range(4) if i != j): continue
            sc = min(D.get(t, 999) for t in tiles) + 0.3 * cheb((bx+1, by+1), occ_pos(occ, 'hub_terminal'))
            if not labs or sc < labs[0]: labs = (sc, bx, by)
    _, bx, by = labs
    lab_list = []
    for k, (i, j) in enumerate([(1, 2), (2, 1)] + [(i, j) for i in range(4) for j in range(4) if i != j and (i, j) not in ((1, 2), (2, 1), (0, 3), (3, 0))]):
        occ[(bx+i, by+j)] = 'lab'; lab_list.append((bx+i, by+j))
    for i in range(4): occ[(bx+i, by+i)] = 'road'; roads.add((bx+i, by+i))
    p = path_to(start, lambda u: u in {(bx+i, by+i) for i in range(4)}, set(o for o, t in occ.items() if t not in ('road',)) - {(bx+i, by+i) for i in range(4)}, roads)
    routes['labs'] = p; roads.update(p)
    for q in p: occ.setdefault(q, 'road')
    # singles: towers (6), nuker, observer, 3 loose extensions — free tiles adjacent to roads, closest to storage, not on roads
    keyset = [miners[0], miners[1], ctl_cont, mm]
    singles = []
    Dsp = dijkstra([SP], set(o for o, t in occ.items() if t != 'road'), roads)[0]
    free = sorted([p for p in Dsp if p not in occ and adj_road(p) and inner(p) and all(cheb(p, o) > 1 for o in NEAR_OBJ)], key=lambda p: Dsp[p])
    want = ['tower'] * 6 + ['ext'] * 3 + ['nuker', 'observer']
    for p in free:
        if not want: break
        blocked = set(o for o, t in occ.items() if t != 'road') | {p}
        if connected(blocked - set(keyset), [start] + keyset):
            occ[p] = 'single_' + want.pop(0); singles.append(p)
    return dict(occ=occ, fillers=fillers, hub=hub, door=door, SP=SP, M=M, miners=miners, bonusB=bonusB, CL=CL, ups=ups,
                ctl_cont=ctl_cont, srcA_link=srcA_link, mm=mm, roads=roads, routes=routes, labs=lab_list, start=start)
def occ_pos(occ, t): return next(p for p, v in occ.items() if v == t)

results = {}
for r in range(4):
    try: res = plan(r)
    except Exception as e: res = None; print('rotation', r, 'failed', e)
    if res: results[r] = res
def metrics(res):
    R = res['routes']; L = {k: len(v) for k, v in R.items()}
    return {'road_tiles': len(res['roads']), 'route_tiles': L, 'sourceB_direct_to_storage': res['bonusB']}
for r, res in results.items(): print('rotation', r, metrics(res))
best_r = min(results, key=lambda r: len(results[r]['roads']) + 2 * sum(len(v) for k, v in results[r]['routes'].items() if k in ('srcA', 'ctl')) - (30 if results[r]['bonusB'] else 0))
res = results[best_r]; print('chosen rotation', best_r)
json.dump({'rotations': {r: metrics(v) for r, v in results.items()}, 'chosen': best_r}, open('/tmp/v2_candidates.json', 'w'))
import pickle; pickle.dump(res, open('/tmp/v2_res.pkl', 'wb'))
