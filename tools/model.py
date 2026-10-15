"""Ideal max-efficiency model for W46N8 (+ remote W45N8), from real terrain + live objects, compared with DB actuals.
  .venv/bin/python tools/model.py            full run: fetch terrain/objects, compute, compare 6h, write
                                             metrics/model.json, docs/model_routes.png, DB table model_params
  .venv/bin/python tools/model.py --hours 3  actual window
Movement model: PathFinder costs road 1 / plain 2 / swamp 10 (same as src/utils/move.js).
Ticks/tile for a body: fatigue = terrain(road1,plain2,swamp10) x non-MOVE weighted parts; each MOVE removes 2/tick."""
import os, sys, json, heapq, math, time, argparse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts')); sys.path.insert(0, os.path.join(ROOT, 'tools'))
import api, db
HOME, REMOTE = 'W46N8', 'W45N8'          # W45N8 is east of W46N8: combined grid x = 50 + rx
OFF = {HOME: 0, REMOTE: 50}
WALKABLE = {'road', 'container', 'rampart', 'constructionSite', 'creep', 'tombstone', 'ruin', 'energy', 'powerCreep'}
PROG = {4: 135000, 5: 405000, 6: 1215000}  # progress needed to reach level+1 from level (key = current level+1)
BODY_COST = {'move': 50, 'work': 100, 'carry': 50, 'attack': 80, 'ranged_attack': 150, 'heal': 250, 'claim': 600, 'tough': 10}

def terrain(room):
    p = os.path.join(ROOT, 'data', f'terrain_{room}.txt')
    if not os.path.exists(p):
        t = api.req(f'game/room-terrain?room={room}&encoded=1&shard=shard3')['terrain'][0]['terrain']; open(p, 'w').write(t)
    return open(p).read().strip()

def load():
    T, objs = {}, {}
    for r in (HOME, REMOTE):
        t = terrain(r)
        for i, ch in enumerate(t):
            T[(OFF[r] + i % 50, i // 50)] = 'wall' if int(ch) & 1 else ('swamp' if int(ch) & 2 else 'plain')
        objs[r] = api.req(f'game/room-objects?room={r}&shard=shard3')['objects']
    roads, block = set(), set()
    for r, ol in objs.items():
        for o in ol:
            p = (OFF[r] + o['x'], o['y'])
            if o['type'] == 'road': roads.add(p)
            elif o['type'] not in WALKABLE and not (o['type'] == 'rampart'): block.add(p)
    # columns x=49/50 are the shared exit: only connect where both edge tiles are walkable
    return T, objs, roads, block

def step_cost(T, roads, p):
    return 1 if p in roads else (10 if T[p] == 'swamp' else 2)

def dijkstra(T, roads, block, start, goals, rng=1, extra_block=()):
    goalset = {(gx + dx, gy + dy) for gx, gy in goals for dx in range(-rng, rng + 1) for dy in range(-rng, rng + 1)}
    dist, prev, pq = {start: 0}, {}, [(0, start)]
    while pq:
        d, p = heapq.heappop(pq)
        if p in goalset and p != start or (p in goalset and rng == 0):
            path = [p]
            while path[-1] in prev: path.append(prev[path[-1]])
            return d, path[::-1][1:]
        if d > dist.get(p, 1e9): continue
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                q = (p[0] + dx, p[1] + dy)
                if q == p or q not in T or T[q] == 'wall' or q in block or q in extra_block: continue
                if q[1] in (0, 49) and q[0] not in (49, 50): pass
                # crossing between rooms only straight east/west through the x=49|50 seam
                if (p[0] <= 49) != (q[0] <= 49) and dy != 0: continue
                nd = d + step_cost(T, roads, q)
                if nd < dist.get(q, 1e9): dist[q] = nd; prev[q] = p; heapq.heappush(pq, (nd, q))
    return None, []

def ticks_per_tile(T, roads, p, body, loaded):
    moves = body.count('move'); heavy = sum(1 for b in body if b != 'move' and (b != 'carry' or loaded))
    f = (1 if p in roads else 10 if T[p] == 'swamp' else 2) * heavy
    return max(1, math.ceil(f / (2 * moves))) if moves else 99

def path_ticks(T, roads, path, body, loaded):
    return sum(ticks_per_tile(T, roads, p, body, loaded) for p in path)

def body_cost(b): return sum(BODY_COST[x] for x in b)

def q(c, sql, *a):
    r = c.execute(sql, a).fetchall(); return r

def actuals(hours, routes_tiles):
    c = db.connect(); H = f"{hours} hours"; A = {}
    # only rows at the current RCL: progress resets on level-up, a window spanning it would give None/garbage
    rs = q(c, f"SELECT min(tick),max(tick),min(progress),max(progress),avg(cpu),avg(energy::float/nullif(energy_cap,0)),max(rcl),min(rcl) FROM room_stats WHERE room=%s AND ts>now()-interval '{H}' AND rcl=(SELECT rcl FROM room_stats WHERE room=%s ORDER BY ts DESC LIMIT 1)", HOME, HOME)[0]
    A['ticks'] = (rs[1] - rs[0]) if rs[0] else 0
    ts = q(c, f"SELECT extract(epoch from max(ts)-min(ts))/nullif(max(tick)-min(tick),0) FROM room_stats WHERE room=%s AND ts>now()-interval '{H}'", HOME)[0][0]
    A['tick_s'] = float(ts) if ts else None
    sd = q(c, f"SELECT (array_agg(storage ORDER BY ts DESC))[1]-(array_agg(storage ORDER BY ts))[1] FROM room_stats WHERE room=%s AND ts>now()-interval '{H}'", HOME)[0][0]
    A['storage_delta'] = (sd or 0) / A['ticks'] if A['ticks'] else 0  # measured server tick time (was hard-coded 3.9; 10-15 measured 4.08)
    A['upgrade_per_tick'] = (rs[3] - rs[2]) / A['ticks'] if A['ticks'] and rs[6] == rs[7] else None
    A['cpu'] = float(rs[4] or 0); A['energy_fill'] = float(rs[5] or 0)
    # 1h recent upgrade rate as well
    r1 = q(c, f"SELECT max(tick)-min(tick), max(progress)-min(progress) FROM room_stats WHERE room=%s AND ts>now()-interval '1 hour'", HOME)[0]
    A['upgrade_per_tick_1h'] = r1[1] / r1[0] if r1[0] else None
    # store deltas per creep (pickups +, drops -), located by tile
    rows = q(c, f"""WITH s AS (SELECT creep, role, room, x, y, tick, store, store - lag(store) OVER w d, tick - lag(tick) OVER w dt
        FROM creep_ticks WHERE ts>now()-interval '{H}' WINDOW w AS (PARTITION BY creep ORDER BY tick))
        SELECT role, room, x, y, sum(d) FILTER (WHERE d>0), -sum(d) FILTER (WHERE d<0) FROM s WHERE dt<=3 GROUP BY 1,2,3,4""")
    src = {'A': (HOME, 32, 11), 'B': (HOME, 39, 33), 'R': (REMOTE, 14, 12)}
    inc = {k: 0 for k in src}; spent = {}; deliv = {'hub': 0, 'ctl': 0, 'other': 0}
    for role, room, x, y, pos, neg in rows:
        pos, neg = pos or 0, neg or 0
        for k, (rr, sx, sy) in src.items():
            if room == rr and max(abs(x - sx), abs(y - sy)) <= 2 and role in ('hauler', 'rhauler', 'queen', 'builder', 'upgrader'): inc[k] += pos
        spent[role] = spent.get(role, 0) + neg
        if role in ('hauler', 'rhauler') and room == HOME:
            if max(abs(x - 30), abs(y - 30)) <= 1: deliv['ctl'] += neg
            elif 32 <= x <= 37 and 23 <= y <= 29: deliv['hub'] += neg
            else: deliv['other'] += neg
    T_ = max(1, A['ticks'])
    cov = q(c, f"SELECT count(DISTINCT tick)::float/nullif(max(tick)-min(tick)+1,0) FROM creep_ticks WHERE ts>now()-interval '{H}'")[0][0] or 1
    T_ = T_ * cov  # store deltas are only seen on ingested ticks (dt<=3); normalise by tick coverage
    A['income'] = {k: v / T_ for k, v in inc.items()}
    # Home sources: harvested energy, not carrier pickups (after storage miner B transfers straight in, which pickups never see).
    # One 'w' state tick of a miner = one harvest of 2x5 WORK (miner only acts while the source has energy). Normalised by
    # the creep_cpu window coverage (segment ring), independent of websocket gaps.
    mrows = q(c, f"""WITH p AS (SELECT creep, mode() WITHIN GROUP (ORDER BY x*100+y) xy FROM creep_ticks
          WHERE ts>now()-interval '{H}' AND role='miner' AND room=%s GROUP BY 1)
        SELECT p.xy, sum(length(k.codes) - length(replace(k.codes, 'w', ''))) FROM creep_cpu k JOIN p USING (creep)
        WHERE k.ts>now()-interval '{H}' GROUP BY 1""", HOME)
    wt = q(c, f"SELECT count(DISTINCT tick)*5 FROM creep_cpu WHERE ts>now()-interval '{H}'")[0][0] or 1
    for k in ('A', 'B'):
        _, sx, sy = src[k]
        A['income'][k] = sum(10 * n for xy, n in mrows if max(abs(xy // 100 - sx), abs(xy % 100 - sy)) <= 1) / wt
    A['spent'] = {k: v / T_ for k, v in spent.items()}
    A['delivered'] = {k: v / T_ for k, v in deliv.items()}
    A['coverage'] = q(c, f"SELECT count(DISTINCT tick)::float/nullif(max(tick)-min(tick)+1,0) FROM creep_ticks WHERE ts>now()-interval '{H}'")[0][0]
    A['roles'] = {r: dict(cpu_t=float(a or 0), idle=float(b or 0), rp100=float(d or 0)) for r, a, b, d in q(c, f"""SELECT role, sum(cpu_ms)/(count(*)*5), avg((acts=0)::int), sum(repaths)*100.0/(count(*)*5)
        FROM creep_cpu WHERE ts>now()-interval '{H}' GROUP BY 1""")}
    A['paths'] = {r: dict(n=n, planned=float(p), actual=float(a)) for r, n, p, a in q(c, f"SELECT role, count(*), avg(planned), avg(actual) FROM path_arrivals WHERE ts>now()-interval '{H}' AND planned>0 GROUP BY 1")}
    # hauler cycle: ticks between successive pickups (store rises from <=10% to more)
    cyc = q(c, f"""WITH s AS (SELECT creep, role, tick, store, lag(store) OVER w ps FROM creep_ticks WHERE ts>now()-interval '{H}' AND role IN ('hauler','rhauler') WINDOW w AS (PARTITION BY creep ORDER BY tick)),
        e AS (SELECT creep, role, tick, tick - lag(tick) OVER (PARTITION BY creep ORDER BY tick) cy FROM s WHERE ps=0 AND store>0)
        SELECT role, percentile_cont(0.5) WITHIN GROUP (ORDER BY cy), count(*) FROM e WHERE cy BETWEEN 10 AND 600 GROUP BY 1""")
    A['cycle_median'] = {r: float(m) for r, m, n in cyc}
    # traffic: share of hauling ticks on ideal-route tiles (+-1 tile)
    tr = q(c, f"SELECT room, x, y, count(*) FROM creep_ticks WHERE ts>now()-interval '{H}' AND role IN ('hauler','rhauler','queen') GROUP BY 1,2,3")
    on = off = 0; heat = {}; offtiles = []
    near = {(x + dx, y + dy) for (x, y) in routes_tiles for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
    for room, x, y, n in tr:
        if room not in OFF: continue
        p = (OFF[room] + x, y); heat[p] = n
        if p in near: on += n
        else: off += n; offtiles.append((n, room, x, y))
    A['on_route'] = on / max(1, on + off); A['offroute_top'] = sorted(offtiles, reverse=True)[:10]
    A['_heat'] = heat
    return A

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--hours', type=float, default=6); ap.add_argument('--no-db', action='store_true'); a = ap.parse_args()
    T, objs, roads, block = load()
    O = lambda r, t: [o for o in objs[r] if o['type'] == t]
    P = lambda r, o: (OFF[r] + o['x'], o['y'])
    ctl = O(HOME, 'controller')[0]; rcl = ctl['level']; prog = ctl['progress']
    cap = 300 * len(O(HOME, 'spawn')) + 50 * len(O(HOME, 'extension')) if rcl < 7 else None
    srcs = {'A': (HOME, (32, 11), (31, 12)), 'B': (HOME, (39, 33), (38, 32)), 'R': (REMOTE, (14, 12), (13, 11))}
    hub, ctlc, storage = (35, 24), (30, 30), (37, 31)
    # Ideal routes: container -> drop targets (range 1)
    R = {}
    for k, (r, s, cont) in srcs.items():
        st = (OFF[r] + cont[0], cont[1])
        for tn, tg in (('hub', hub), ('ctl', ctlc), ('storage', storage), ('spawn', (35, 28))):
            d, path = dijkstra(T, roads, block - {tg}, st, [tg], 1)
            R[f'{k}->{tn}'] = dict(cost=d, tiles=len(path), path=path,
                                   swamp=sum(T[p] == 'swamp' for p in path), unpaved=sum(p not in roads for p in path))
    # also "ideal if fully paved" lengths are the same tiles; travel ticks per body
    hauler_body = ['carry'] * 8 + ['move'] * 8
    # live bodies per route (src/roles): home A hauler 14C7M (2:1, needs roads), remote hauler 8C8M (1:1, plain-speed)
    route_body = {'A': ['carry'] * 14 + ['move'] * 7, 'B': hauler_body, 'R': hauler_body}
    REMOTE_AVAIL = 1.0    # steady state; Invader downtime now lives in tools/flow.py stochastic layer (was 0.93)   # measured 10-13/14: Invader pauses ~105 min/24h (04:56-06:41) => ~7% remote downtime
    road_body = lambda e: (['carry'] * (2 * min(16, e // 150)) + ['move'] * min(16, e // 150))
    M = {'rcl': rcl, 'progress': prog, 'energy_cap': cap, 'sources': {}}
    upkeep_creeps = 0; spawn_time = 0; bodies = {}
    for r in (HOME, REMOTE):
        for o in O(r, 'creep'):
            if o.get('user') and o['user'] != O(HOME, 'controller')[0].get('user'): continue
            b = [x['type'] for x in o['body']]; life = 600 if 'claim' in b else 1500
            upkeep_creeps += body_cost(b) / life; spawn_time += 3 * len(b) / life
            bodies.setdefault(''.join(o['name'].rstrip('0123456789')), []).append(''.join(x[0] for x in b))
    M['bodies_live'] = bodies
    M['upkeep_creeps'] = upkeep_creeps; M['spawn_util'] = spawn_time
    tot_income = 0; carry_need = 0; route_tiles = set()
    for k, (r, s, cont) in srcs.items():
        cap_src = 3000 if r == HOME or True else 1500   # reserved remote = 3000
        inc = cap_src / 300 * (REMOTE_AVAIL if r == REMOTE else 1)
        # Live topology (src/roles/hauler.js): with storage A -> ctl container (14C7M road hauler), B's miner transfers
        # straight into the adjacent storage (no hauling; the queen ferries the surplus to ctl, short leg not modelled here),
        # remote -> ctl. Pre-storage: the shorter of hub/ctl.
        has_st = bool(O(HOME, 'storage'))
        tgt = {'A': 'ctl', 'B': 'storage', 'R': 'ctl'}[k] if has_st else min(('hub', 'ctl'), key=lambda t: R[f'{k}->{t}']['tiles'])
        adjacent = tgt == 'storage' and max(abs(cont[0] - storage[0]), abs(cont[1] - storage[1])) <= 1
        dist = 0 if adjacent else R[f'{k}->{tgt}']['tiles']
        rt_ticks_11 = 0 if adjacent else path_ticks(T, roads, R[f'{k}->{tgt}']['path'], route_body[k], True) + path_ticks(T, roads, R[f'{k}->{tgt}']['path'], route_body[k], False)  # loaded + empty back
        carry = 0 if adjacent else inc * (rt_ticks_11 + 4) / 50     # +4 ticks pickup/transfer overhead
        M['sources'][k] = dict(room=r, income=inc, target=tgt, dist=dist, swamp=R[f'{k}->{tgt}']['swamp'], unpaved=R[f'{k}->{tgt}']['unpaved'],
                               roundtrip_1to1=rt_ticks_11 + 4, carry_need=carry, carry_need_paved_formula=2 * dist * inc / 50,
                               work_need=math.ceil(inc / 2), container_decay_e=(0.1 if r == HOME else 0.5))
        tot_income += inc; carry_need += carry
        if not adjacent: route_tiles |= set(R[f'{k}->{tgt}']['path'])
    route_tiles |= set(R['A->ctl']['path']) | set(R['B->ctl']['path'])
    # remote fixed costs: reserver (CLAIM2 at 1300 or 2xCLAIM1 overlap) + container repair
    reserver = (1300 / 600) if rcl >= 4 else (650 / 600)
    road_decay = sum((5 if T[p] == 'swamp' else 1) * 100 / 1000 / 100 for p in roads)  # energy/tick to repair roads
    M['hauler_carry_need'] = carry_need
    M['hauler_carry_live'] = sum(b.count('c') for n in ('hauler', 'rhauler') for b in bodies.get(n, []))
    M['income_theoretical'] = tot_income
    overhead_min = upkeep_creeps + road_decay + sum(s['container_decay_e'] for s in M['sources'].values())
    M['overhead_live'] = overhead_min; M['road_decay'] = road_decay; M['reserver_cost'] = reserver
    # ideal minimal composition (RCL4, 1300 cap): 2x miner 5W1C3M(700), haulers 2C:1M on roads, CLAIM2 reserver,
    # rminer 6W1C3M (800: repair ticks block harvest, 5W only ~9/t), upgraders WORK-heavy; cost/tick:
    ideal_haul_cost = carry_need * 75 / 1500  # 2C+1M per 100 cap => 1.5x50 per carry
    ideal_overhead = 2 * 700 / 1500 + 800 / 1500 + ideal_haul_cost + 1300 / 600 + 650 / 1500 + 600 / 1500 + road_decay + 0.7  # miners, rminer, haulers, reserver, queen, builder-lite, decay
    # Upgraders are creeps too: 12W1C1M = 1300 per 1500 ticks buys 12 upgrade/t, so each upgrade/t carries 1300/1500/12
    # upkeep. Live overhead already counts them; the ideal left them out (~1.6/t too optimistic, patrol 10-14 15:25).
    up_upkeep = 1300 / 1500 / 12
    M['ideal_overhead'] = ideal_overhead
    M['upgrade_max_ideal'] = (tot_income - ideal_overhead) / (1 + up_upkeep)
    M['upgrade_max_live_comp'] = tot_income - overhead_min
    work_up = sum(b.count('w') for b in bodies.get('upgrader', []))
    M['upgrader_work'] = work_up; M['upgrader_bound'] = 'energy' if work_up > M['upgrade_max_live_comp'] else 'WORK'
    M['build_rate_max'] = sum(b.count('w') for b in bodies.get('builder', [])) * 5
    left = PROG.get(rcl + 1, 0) - prog
    eta = {}; tick_s = 3.9; cur = left
    for lv in range(rcl + 1, 7):
        need = cur if lv == rcl + 1 else PROG[lv]
        eta[lv] = need / M['upgrade_max_ideal']
        cur = 0
    cum = 0; M['eta_ideal'] = {}
    for lv, t_ in eta.items(): cum += t_; M['eta_ideal'][lv] = dict(ticks=round(cum), hours=round(cum * tick_s / 3600, 1))
    M['cpu_budget_per_creep'] = 20 / max(1, sum(len(v) for v in bodies.values()))
    M['routes'] = {k: {kk: vv for kk, vv in v.items() if kk != 'path'} for k, v in R.items()}
    # road plan: unpaved tiles on chosen ideal routes, swamp first
    unp = sorted({p for p in route_tiles if p not in roads}, key=lambda p: (T[p] != 'swamp', p))
    M['pave'] = [dict(room=HOME if p[0] < 50 else REMOTE, x=p[0] % 50 if p[0] >= 50 else p[0], y=p[1], terrain=T[p]) for p in unp]
    if not a.no_db:
        A = actuals(a.hours, route_tiles); heat = A.pop('_heat')
        M['actual'] = A
        actual_up = A['upgrade_per_tick']
        M['eta_actual'] = {}
        if A.get('tick_s'):
            tick_s = A['tick_s']
            for v in M['eta_ideal'].values(): v['hours'] = round(v['ticks'] * tick_s / 3600, 1)
        if actual_up:
            cum = 0
            for lv in range(rcl + 1, 7):
                cum += ((PROG[lv] - prog) if lv == rcl + 1 else PROG[lv]) / actual_up
                M['eta_actual'][lv] = dict(ticks=round(cum), hours=round(cum * tick_s / 3600, 1))
    else: heat = {}
    import flow
    n_ramp = len(O(HOME, 'rampart'))
    M['flow'] = flow.steady(M, n_ramp)
    if not a.no_db:
        c = db.connect(); eps, span, nd = flow.events(c, q)
        M['flow']['stochastic'] = st = flow.stochastic(eps, span, nd, M['actual'].get('tick_s') or 4.08)
        M['flow']['upgrade_expected'] = round((M['flow']['net'] - st['expected_loss']) / (1 + flow.UP_UPKEEP), 2)
        A = M['actual']; M['flow']['measured_sinks'] = dict(upgrade=A['upgrade_per_tick'], build=A['spent'].get('builder', 0), storage_delta=A.get('storage_delta', 0))
    json.dump(M, open(os.path.join(ROOT, 'metrics', 'model.json'), 'w'), indent=1, default=str)
    render(T, roads, block, objs, R, srcs, heat, route_tiles)
    if not a.no_db and 'actual' in M: write_db(M)
    report(M)

def write_db(M):
    A = M['actual']; c = db.connect()
    c.execute("""CREATE TABLE IF NOT EXISTS model_params(ts timestamptz NOT NULL DEFAULT now(), key text, ideal double precision, actual double precision, unit text)""")
    inc = A['income']
    rows = [('income_total', M['income_theoretical'], sum(inc.values()), 'e/t'),
            ('income_A', 10, inc['A'], 'e/t'), ('income_B', 10, inc['B'], 'e/t'), ('income_R', 10, inc['R'], 'e/t'),
            ('upgrade', M['upgrade_max_ideal'], A['upgrade_per_tick'], 'e/t'),
            ('hauler_carry', M['hauler_carry_need'], M['hauler_carry_live'], 'parts'),
            ('on_route_share', 1, A['on_route'], 'ratio'), ('cpu', 20, A['cpu'], 'ms/t')]
    for r, d in A['paths'].items(): rows.append((f'path_{r}', d['planned'], d['actual'], 'ticks'))
    for r, d in A['roles'].items(): rows.append((f'idle_{r}', 0, d['idle'], 'ratio'))
    for k, s in M['sources'].items():
        if s['room'] == HOME or True:
            role = 'rhauler' if s['room'] == REMOTE else 'hauler'
            if role in A['cycle_median']: rows.append((f'cycle_{k}_{role}', s['roundtrip_1to1'], A['cycle_median'][role], 'ticks'))
    with c.cursor() as cur:
        cur.executemany("INSERT INTO model_params(ts,key,ideal,actual,unit) VALUES (now(),%s,%s,%s,%s)", [(k, i, a, u) for k, i, a, u in rows])

def render(T, roads, block, objs, R, srcs, heat, route_tiles):
    from PIL import Image, ImageDraw
    S = 14; W, H = 100 * S, 50 * S + 40
    im = Image.new('RGB', (W, H), (20, 20, 20)); d = ImageDraw.Draw(im, 'RGBA')
    col = {'wall': (45, 45, 45), 'plain': (120, 120, 105), 'swamp': (60, 90, 40)}
    for (x, y), t in T.items(): d.rectangle([x * S, y * S, x * S + S - 1, y * S + S - 1], fill=col[t])
    mx = max(heat.values()) if heat else 1
    for (x, y), n in heat.items():
        a = int(40 + 200 * min(1, math.log1p(n) / math.log1p(mx))); d.rectangle([x * S, y * S, x * S + S - 1, y * S + S - 1], fill=(255, 140, 0, a))
    for x, y in roads: d.rectangle([x * S + 4, y * S + 4, x * S + S - 5, y * S + S - 5], fill=(220, 220, 220))
    for x, y in block: d.rectangle([x * S + 2, y * S + 2, x * S + S - 3, y * S + S - 3], outline=(80, 160, 255), width=2)
    colors = {'A': (255, 60, 60), 'B': (60, 200, 255), 'R': (255, 255, 0)}
    for k, v in R.items():
        if not (k.endswith('->hub') or k.endswith('->ctl')): continue
        c = colors[k[0]] + ((255,) if k.endswith('hub') else (150,))
        pts = [(x * S + S // 2, y * S + S // 2) for x, y in v['path']]
        r, s, cont = srcs[k[0]]; pts = [((OFF[r] + cont[0]) * S + S // 2, cont[1] * S + S // 2)] + pts
        d.line(pts, fill=c, width=3 if k.endswith('hub') else 2)
    for p in route_tiles:
        if p not in roads: d.rectangle([p[0] * S + 5, p[1] * S + 5, p[0] * S + S - 6, p[1] * S + S - 6], fill=(255, 0, 255))
    d.line([(50 * S, 0), (50 * S, 50 * S)], fill=(255, 255, 255, 120), width=1)
    d.text((5, 50 * S + 5), 'W46N8 | W45N8   ideal routes: red=A yellow=Remote blue=B (thick->hub 35,24, thin->ctl container 30,30)  '
           'orange=6h hauler/queen traffic  white=road  magenta=route tile to pave  blue box=obstacle', fill=(255, 255, 255))
    im.save(os.path.join(ROOT, 'docs', 'model_routes.png'))

def report(M):
    print(f"RCL{M['rcl']} progress {M['progress']}  cap {M['energy_cap']}")
    for k, s in M['sources'].items(): print(f" src {k}: dist {s['dist']} -> {s['target']} swamp {s['swamp']} unpaved {s['unpaved']} rt {s['roundtrip_1to1']} carry {s['carry_need']:.1f}")
    for k in ('income_theoretical', 'upkeep_creeps', 'overhead_live', 'ideal_overhead', 'upgrade_max_ideal', 'upgrade_max_live_comp', 'upgrader_work', 'upgrader_bound', 'hauler_carry_need', 'hauler_carry_live', 'spawn_util', 'build_rate_max', 'cpu_budget_per_creep', 'eta_ideal', 'eta_actual'):
        if k in M: print(f" {k}: {M[k]}")
    if 'flow' in M: print(' flow:', json.dumps(M['flow'], default=str))
    if 'actual' in M: print(' actual:', json.dumps(M['actual'], default=str)[:3000])
    print(' pave:', len(M['pave']), M['pave'][:30])
if __name__ == '__main__': main()
