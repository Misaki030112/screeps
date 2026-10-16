"""Remote evaluation (docs/REMOTE_EVAL.md): A) fully paving storage->W45N8, B) adding W45N7 as a reserved remote.
Analysis only: reads terrain + live objects via API, trip times from TimescaleDB. Writes metrics/remote_eval.json + docs/remote_eval.png."""
import os, sys, json, math
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts')); sys.path.insert(0, os.path.join(ROOT, 'tools'))
import api, db, heapq
OFF = {'W46N8': (0, 0), 'W45N8': (50, 0), 'W45N7': (50, 50)}
ME = '6010ee96cbca26e9512da6f0'
T, roads, block, objs = {}, set(), set(), {}
for r, (ox, oy) in OFF.items():
    p = os.path.join(ROOT, 'data', f'terrain_{r}.txt')
    if not os.path.exists(p): open(p, 'w').write(api.req(f'game/room-terrain?room={r}&encoded=1&shard=shard3')['terrain'][0]['terrain'])
    t = open(p).read().strip()
    for i, ch in enumerate(t): T[(ox + i % 50, oy + i // 50)] = 'wall' if int(ch) & 1 else ('swamp' if int(ch) & 2 else 'plain')
    objs[r] = api.req(f'game/room-objects?room={r}&shard=shard3')['objects']
    for o in objs[r]:
        q = (ox + o['x'], oy + o['y'])
        if o['type'] == 'road': roads.add(q)
        elif o['type'] not in ('container', 'rampart', 'constructionSite', 'creep', 'tombstone', 'ruin', 'energy'): block.add(q)
def room_of(p): return next(r for r, (ox, oy) in OFF.items() if ox <= p[0] < ox + 50 and oy <= p[1] < oy + 50)
def cost(q, paved=False): return 1 if (q in roads or paved) else (10 if T[q] == 'swamp' else 2)
def seam_ok(p, q):
    rp, rq = room_of(p), room_of(q)
    if rp == rq: return True
    return (p[0] == q[0]) or (p[1] == q[1])  # straight crossings only
def path(a, goal, rng=1, assume_paved=False):
    goals = {(goal[0] + dx, goal[1] + dy) for dx in range(-rng, rng + 1) for dy in range(-rng, rng + 1)}
    dist, prev, pq = {a: 0}, {}, [(0, a)]
    while pq:
        d, p = heapq.heappop(pq)
        if p in goals:
            out = [p]
            while out[-1] in prev: out.append(prev[out[-1]])
            return d, out[::-1][1:]
        if d > dist[p]: continue
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                q = (p[0] + dx, p[1] + dy)
                if q == p or q not in T or T[q] == 'wall' or q in block or not seam_ok(p, q): continue
                nd = d + cost(q, assume_paved and T[q] != 'swamp' or (assume_paved and True))
                if nd < dist.get(q, 1e9): dist[q] = nd; prev[q] = p; heapq.heappush(pq, (nd, q))
def tpt(q, body, loaded, paved=False):
    m = body.count('m'); heavy = sum(1 for b in body if b != 'm' and (b != 'c' or loaded))
    f = cost(q, paved) * heavy; return max(1, math.ceil(f / (2 * m)))
def trip(pth, body, paved=False): return sum(tpt(q, body, True, paved) for q in pth) + sum(tpt(q, body, False, paved) for q in pth)
EDGE = {'road': 5000}
def tiles_summary(pth):
    s = {}
    for q in pth:
        k = (room_of(q), 'road' if q in roads else T[q]); s[k] = s.get(k, 0) + 1
    return {f'{a}:{b}': n for (a, b), n in sorted(s.items())}
def build_cost(pth): return sum(0 if q in roads else (1500 if T[q] == 'swamp' else 300) for q in pth)
def decay_e(pth):  # energy/tick: 100 hits/1000t (swamp road decays 500), repair 100 hits per energy
    return sum((5 if T[q] == 'swamp' else 1) * 100 / 1000 / 100 for q in pth)
def wear_e(pth, parts_per_tick):  # ROAD_WEAROUT 1 hit per body part per step
    return len(pth) * parts_per_tick / 100

STORAGE, CTL = (37, 31), (30, 30)
R8 = (50 + 13, 11)       # W45N8 container
src7 = [o for o in objs['W45N7'] if o['type'] == 'source'][0]
R7 = (50 + 22, 50 + 15)  # BustJetter container site next to source 21,16
M = {}
# ---------- A
c = db.connect(); qq = lambda s: c.execute(s).fetchall()
cyc = qq("""WITH s AS (SELECT creep, tick, room, store, lag(store) OVER w ps FROM creep_ticks WHERE ts>now()-interval '24 hours' AND role='rhauler' WINDOW w AS (PARTITION BY creep ORDER BY tick)),
 e AS (SELECT tick - lag(tick) OVER (PARTITION BY creep ORDER BY tick) cy FROM s WHERE ps=0 AND store>0 AND room='W45N8')
 SELECT percentile_cont(array[0.25,0.5,0.75]) WITHIN GROUP (ORDER BY cy), count(*) FROM e WHERE cy BETWEEN 40 AND 400""")[0]
legs = qq("SELECT split_part(target,':',1), count(*), avg(planned)::float, avg(actual)::float FROM path_arrivals WHERE role='rhauler' AND ts>now()-interval '24 hours' GROUP BY 1")
states = dict(qq("SELECT state, count(*)::float/sum(count(*)) over () FROM creep_ticks WHERE role='rhauler' AND ts>now()-interval '24 hours' GROUP BY 1"))
cpu_creep = qq("SELECT sum(cpu_ms)/(count(*)*5) FROM creep_cpu WHERE ts>now()-interval '6 hours' AND role='rhauler'")[0][0]
spt = qq("SELECT extract(epoch from max(ts)-min(ts))/(max(tick)-min(tick)) FROM room_stats WHERE ts>now()-interval '6 hours'")[0][0]
_, pA = path(R8, CTL)          # current target: ctl container
_, pAs = path(R8, STORAGE)
M['A'] = dict(route_ctl=tiles_summary(pA), len_ctl=len(pA), route_storage=tiles_summary(pAs), len_storage=len(pAs),
              build_cost=build_cost(pA), unpaved=sum(q not in roads for q in pA), swamp_unpaved=sum(q not in roads and T[q] == 'swamp' for q in pA),
              cycle_q=[float(x) for x in cyc[0]] if cyc[0] else None, cycles=cyc[1], legs=legs, states=states,
              cpu_per_creep=float(cpu_creep or 0.23), sec_per_tick=float(spt or 4))
bodies = {'8C8M (live, 800e, 400cap)': 'c' * 8 + 'm' * 8, '16C8M (roads, 1200e, 800cap)': 'c' * 16 + 'm' * 8, '12C6M (roads, 900e, 600cap)': 'c' * 12 + 'm' * 6}
inc = 10.0  # reserved source 3000/300
opts = {}
for name, b in bodies.items():
    for paved in (False, True):
        rt = trip(pA, b, paved) + 4
        capa = 50 * b.count('c'); costb = 50 * len(b)
        need = inc * rt / capa                     # haulers needed (fractional)
        n = math.ceil(need)
        haul_cost = n * costb / 1500
        cpu = n * float(cpu_creep or 0.23)
        opts[f'{name} | {"paved" if paved else "today"}'] = dict(rt=rt, cap=capa, need=round(need, 2), n=n, e_per_t=round(haul_cost, 3),
            spawn=round(n * 3 * len(b) / 1500, 4), cpu=round(cpu, 3), cpu_per_kE=round(cpu / inc * 1000, 2),
            delivered_per_hauler=round(capa / rt, 2), feasible=(not paved and b.count('m') * 2 >= b.count('c')) or paved)
M['A']['options'] = opts
parts_per_tick = 10 * 2 * 24 / 800  # 16C8M carrying 10/t: tiles traversed per tick both ways x parts / cap
M['A']['decay_e'] = round(decay_e(pA), 3); M['A']['wear_e'] = round(wear_e(pA, 24 * 10 / 800 * 2), 3)
# ---------- B
_, pB = path(R7, CTL); _, pBs = path(R7, STORAGE)
ctl7 = [o for o in objs['W45N7'] if o['type'] == 'controller'][0]
_, pRes = path((35, 28), (50 + ctl7['x'], 50 + ctl7['y']))
_, pRes8 = path((35, 28), (50 + 7, 36))
M['B'] = dict(source=dict(x=src7['x'], y=src7['y'], cap=src7['energyCapacity'], invaderHarvested=src7.get('invaderHarvested')),
              controller=dict(x=ctl7['x'], y=ctl7['y'], level=ctl7['level'], reservation=ctl7.get('reservation'), sign=ctl7.get('sign')),
              others=[(o['type'], o.get('structureType'), o['x'], o['y'], o.get('user'), o.get('progress'), o.get('off')) for o in objs['W45N7'] if o['type'] in ('constructionSite', 'spawn', 'creep', 'container', 'road')],
              route_ctl=tiles_summary(pB), len_ctl=len(pB), build_cost=build_cost(pB), len_storage=len(pBs),
              shared_with_A=len(set(pB) & set(pA)), reserver_walk=len(pRes), reserver_walk_W45N8=len(pRes8))
newtiles = [q for q in pB if q not in roads and q not in set(pA)]
B = M['B']; B['new_build_cost'] = sum(1500 if T[q] == 'swamp' else 300 for q in newtiles); B['new_tiles'] = len(newtiles)
B['decay_e_new'] = round(decay_e(newtiles), 3)
for paved in (False, True):
    b = 'c' * 16 + 'm' * 8 if paved else 'c' * 8 + 'm' * 8
    rt = trip(pB, b, paved) + 4; capa = 50 * b.count('c'); need = 10 * rt / capa; n = math.ceil(need)
    res_life = 600 - len(pRes)  # CLAIM creep lives 600, walk eats into it
    # CLAIM2 adds 2/t while on site, reservation decays 1/t always -> one 2-CLAIM reserver every 2*res_life ticks
    reserve_need = 600 / (2 * res_life)  # reservers per 600 ticks
    cst = dict(hauler=n * 50 * len(b) / 1500, miner=700 / 1500, reserver=1300 * reserve_need / 600, container=0.5,
                roads=decay_e(pB if paved else []) if paved else 0, defender=280 * 1 / 10000 * 10)  # ~1 dispatch/wave
    spawn = (n * 3 * len(b) + 9 * 3) / 1500 + 4 * 3 * reserve_need / 600
    gross = 10.0
    net = gross - sum(cst.values())
    B['paved' if paved else 'unpaved'] = dict(rt=rt, haulers=n, need=round(need, 2), costs={k: round(v, 3) for k, v in cst.items()},
        net=round(net, 2), spawn=round(spawn, 3), cpu=round((n + 2 + 0.5) * float(cpu_creep or 0.23), 2))
# unreserved alternative (1500 cap, no reserver)
B['unreserved_net'] = round(5 - (math.ceil(5 * B['unpaved']['rt'] / 400) * 800 / 1500 + 450 / 1500 + 0.5 + 0.28), 2); B['unreserved_haulers'] = math.ceil(5 * B['unpaved']['rt'] / 400)
# current spawn utilisation from live bodies
live = []
for r in ('W46N8', 'W45N8'):
    for o in objs[r]:
        if o['type'] == 'creep' and o.get('user') == ME: live.append((o['name'], len(o['body']), any(x['type'] == 'claim' for x in o['body'])))
M['spawn_now'] = round(sum(3 * n / (600 if cl else 1500) for _, n, cl in live), 3); M['live'] = live
json.dump(M, open(os.path.join(ROOT, 'metrics', 'remote_eval.json'), 'w'), indent=1, default=str)
print(json.dumps(M, indent=1, default=str))

# ---------- render
from PIL import Image, ImageDraw
S = 9; W, H = 100 * S, 100 * S
im = Image.new('RGB', (W + 360, H), (15, 15, 15)); d = ImageDraw.Draw(im, 'RGBA')
col = {'wall': (40, 40, 40), 'plain': (125, 125, 110), 'swamp': (55, 95, 40)}
for (x, y), t in T.items(): d.rectangle([x * S, y * S, x * S + S - 1, y * S + S - 1], fill=col[t])
for x, y in roads: d.rectangle([x * S + 2, y * S + 2, x * S + S - 3, y * S + S - 3], fill=(230, 230, 230))
for r, (ox, oy) in OFF.items():
    for o in objs[r]:
        x, y = ox + o['x'], oy + o['y']
        c_ = {'source': (255, 220, 0), 'controller': (170, 80, 255), 'spawn': (255, 80, 80), 'constructedWall': (90, 90, 90), 'storage': (0, 200, 255), 'constructionSite': (255, 0, 0), 'container': (255, 160, 0)}.get(o['type'])
        if c_: d.rectangle([x * S, y * S, x * S + S - 1, y * S + S - 1], fill=c_)
    d.text((ox * S + 4, oy * S + 4), r, fill=(255, 255, 255))
d.rectangle([0, 50 * S, 50 * S, 100 * S], fill=(25, 25, 35)); d.text((10, 52 * S), 'W46N7 (FungousCoast245 RCL8)\nno exit north/east: not reachable', fill=(200, 200, 200))
def line(p, c_, w=3): d.line([(x * S + S // 2, y * S + S // 2) for x, y in p], fill=c_, width=w)
line([R8] + pA, (255, 255, 0, 220)); line([R7] + pB, (0, 255, 255, 200), 2)
for q in pA:
    if q not in roads: d.rectangle([q[0] * S + 2, q[1] * S + 2, q[0] * S + S - 3, q[1] * S + S - 3], outline=(255, 0, 255), width=2)
d.line([(50 * S, 0), (50 * S, 50 * S)], fill=(255, 255, 255)); d.line([(50 * S, 50 * S), (100 * S, 50 * S)], fill=(255, 255, 255))
A = M['A']; o1 = A['options']['8C8M (live, 800e, 400cap) | today']; o2 = A['options']['16C8M (roads, 1200e, 800cap) | paved']
txt = [f"A) pave W45N8 -> ctl container", f" route {A['len_ctl']} tiles, unpaved {A['unpaved']} (swamp {A['swamp_unpaved']})",
       f" build {A['build_cost']} e", f" decay {A['decay_e']} e/t (+wear {A['wear_e']})",
       f" today 8C8M: rt {o1['rt']}t x{o1['n']} = {o1['e_per_t']} e/t", f" paved 16C8M: rt {o2['rt']}t x{o2['n']} = {o2['e_per_t']} e/t",
       f" measured cycle q25/50/75 {A['cycle_q']}", '',
       f"B) W45N7 (1 source {B['source']['cap']} now)", f" route {B['len_ctl']} tiles via W45N8 S edge", f" net unpaved {B['unpaved']['net']} e/t",
       f" net paved {B['paved']['net']} e/t (+{B['new_build_cost']} e build)", f" spawn +{B['unpaved']['spawn']*100:.0f}% (now {M['spawn_now']*100:.0f}%)",
       ' BustJetter container site at 22,15', f"  progress {[o[5] for o in B['others'] if o[0]=='constructionSite']}/5000",
       f" invaderHarvested {B['source']['invaderHarvested']}", ' east edge walled (novice border)', '',
       'yellow = W45N8 route, magenta box = unpaved', 'cyan = W45N7 route', 'white = road']
for i, s in enumerate(txt): d.text((W + 10, 10 + i * 16), s, fill=(255, 255, 255))
im.save(os.path.join(ROOT, 'docs', 'remote_eval.png'))
