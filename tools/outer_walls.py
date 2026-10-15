"""Final defense (Misaki 2026-10-15 16:5x): outer W/SW chokepoints x=6 y24-32, x=10 y46-48, x=20 y44-47 replace v6 west walls
(23,27-29),(23,36-38) + gate (23,35). Gates: W (6,28), S (20,44). Re-plans BL/S trunks + repair spurs. Writes src/layouts/W46N8.js defense."""
import json, os, heapq
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LP = os.path.join(ROOT, 'src/layouts/W46N8.js')
L = json.loads(open(LP).read().split('=', 1)[1].strip().rstrip(';')); D = L['defense']
T = open(os.path.join(ROOT, 'data/terrain_W46N8.txt')).read().strip()
ter = lambda x, y: T[y * 50 + x]
OLD = {(23, 27), (23, 28), (23, 29), (23, 35), (23, 36), (23, 37), (23, 38)}
NEWW = [(6, y) for y in range(24, 33) if y != 28] + [(10, y) for y in (46, 47, 48)] + [(20, y) for y in (45, 46, 47)]
GW, GS = (6, 28), (20, 44)
block = set()
for lv in L['rcl'].values():
    for t, ps in lv.items():
        if t not in ('road', 'container', 'rampart'): block |= {tuple(p) for p in ps}
UPG = {tuple(p) for p in L['positions']['upgraders']}  # upgrader stand tiles: passable but penalised (stationary creeps)
roads = {tuple(p) for lv in L['rcl'].values() for p in lv.get('road', [])}
for r in L['routes'].values(): roads |= {tuple(p) for p in r}
for n, t in D['trunks'].items():
    if n != 'BL': roads |= {tuple(p) for p in t['path']}
walls = ({tuple(p) for p in D['walls_in_build_order']} - OLD) | set(NEWW)
def path(src, goal, extra=set()):
    rd = roads | extra
    dist = {src: 0}; prev = {}; h = [(0, src)]
    while h:
        d, p = heapq.heappop(h)
        if p == goal: break
        if d > dist[p]: continue
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                n = (p[0] + dx, p[1] + dy)
                if n == p or not (0 < n[0] < 49 and 0 < n[1] < 49) or ter(*n) == '1' or n in block: continue
                if n in walls and n != goal: continue
                c = 1 if n in rd else (2 if ter(*n) == '0' else 10)
                if n in UPG: c += 8
                if d + c < dist.get(n, 1e9): dist[n] = d + c; prev[n] = p; heapq.heappush(h, (d + c, n))
    out = [goal]
    while out[-1] != src: out.append(prev[out[-1]])
    return out[::-1], dist[goal]
def trunk(goal):
    p, c = path((36, 32), goal); new = [q for q in p if q not in roads]
    build = sum(300 if ter(*q) == '0' else 1500 for q in new)
    return dict(gate=[list(goal)], path=[list(q) for q in p], new_tiles=[list(q) for q in new], build=build, cost=c, mode='with_gate')
D['trunks'].pop('BL')
D['trunks']['W'] = trunk(GW); roads |= {tuple(q) for q in D['trunks']['W']['path']}
D['trunks']['S'] = trunk(GS); roads |= {tuple(q) for q in D['trunks']['S']['path']}
D['gates'].pop('BL'); D['gates']['W'] = [list(GW)]; D['gates']['S'] = [list(GS)]
# build order: keep v6 order minus OLD; new outer segments go after NW/NE (they are the weakest-covered, so before E/SE)
order = [tuple(p) for p in D['walls_in_build_order'] if tuple(p) not in OLD]
i = order.index((47, 14)); order[i:i] = NEWW
D['walls_in_build_order'] = [list(p) for p in order]
# repair access: stands within range 3 of every wall of the segment, on/near trunks; spur = new road tiles to the stand
def rng(a, b): return max(abs(a[0] - b[0]), abs(a[1] - b[1]))
for k in ('W_23_27-29', 'SW_23_35-38'): D['repair'].pop(k, None)
def seg(name, ws, stands):
    spur = []
    for s in stands:
        assert all(min(rng(s, w) for s in stands) <= 3 for w in ws)
        if s in roads: continue
        p, _ = path((36, 32), s); spur += [q for q in p if q not in roads and q not in spur]
    roads.update(spur)
    D['repair'][name] = dict(walls=[list(w) for w in ws], stand=[list(s) for s in stands], spur=[list(q) for q in spur],
        spur_build=sum(300 if ter(*q) == '0' else 1500 for q in spur), build_with='same wall phase', access='W/S trunk' + (' + spur' if spur else ''))
def best_stands(ws, n):
    trunkt = {tuple(q) for t in ('W', 'S') for q in D['trunks'][t]['path']}
    cand = [(x, y) for x in range(1, 49) for y in range(1, 49) if ter(x, y) != '1' and (x, y) not in walls and (x, y) not in block and (x, y) not in OUT and (x, y) not in GATES]
    import itertools
    best = None
    for combo in itertools.combinations([c for c in cand if any(rng(c, w) <= 3 for w in ws)], n):
        if not all(min(rng(s, w) for s in combo) <= 3 for w in ws): continue
        sc = sum(0 if s in trunkt else min(rng(s, t) for t in trunkt) * 10 for s in combo) + sum(path((36, 32), s)[1] for s in combo) / 100
        if best is None or sc < best[0]: best = (sc, combo)
    return list(best[1])
GATES = {tuple(q) for g in D['gates'].values() for q in g}
# outside set (flood from exits) so stands are inside
from collections import deque
pas = lambda x, y: 0 <= x < 50 and 0 <= y < 50 and ter(x, y) != '1' and (x, y) not in walls and (x, y) not in GATES
q = deque((x, y) for x in range(50) for y in range(50) if (x in (0, 49) or y in (0, 49)) and pas(x, y)); OUT = set(q)
while q:
    x, y = q.popleft()
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            n = (x + dx, y + dy)
            if n not in OUT and pas(*n): OUT.add(n); q.append(n)
assert (35, 28) not in OUT
segs = {'W_6_24-32': [(6, y) for y in range(24, 33)], 'S_10_46-48': [(10, y) for y in (46, 47, 48)], 'S_20_44-47': [(20, y) for y in (44, 45, 46, 47)]}
for nm, ws in segs.items(): seg(nm, ws, best_stands(ws, 2 if len(ws) > 7 else 1))
D['version'] = 'final: v4 gates (TR/TL/BR) + outer W/S walls (Misaki 2026-10-15 16:5x) + v3 towers'
D['policy']['order'][0] = 'gates (6 rampart: TR x2, TL, BR, W, S) + TR trunk road'
L['defense'] = D
open(LP, 'w').write('module.exports = ' + json.dumps(L, ensure_ascii=False, separators=(',', ':')) + ';\n')
# tower coverage
TW = [tuple(p) for lv in L['rcl'].values() for p in lv.get('tower', [])]
dmg = lambda p: sum(600 if rng(p, t) <= 5 else 150 if rng(p, t) >= 20 else 600 - (rng(p, t) - 5) * 30 for t in TW)
allb = [tuple(p) for p in D['walls_in_build_order']] + [tuple(p) for g in D['gates'].values() for p in g]
print('walls', len(D['walls_in_build_order']), 'gates', sum(len(g) for g in D['gates'].values()), 'total', len(allb))
for nm in ('W', 'S'): t = D['trunks'][nm]; print(nm, t['gate'], 'len', len(t['path']), 'new', t['new_tiles'], 'build', t['build'], 'cost', t['cost'])
for nm in segs: r = D['repair'][nm]; print(nm, 'stand', r['stand'], 'spur', r['spur'], r['spur_build'])
print('min tower dmg new segs', {nm: min(dmg(p) for p in ws) for nm, ws in segs.items()}, 'overall min', min(map(dmg, allb)), min(allb, key=dmg))
