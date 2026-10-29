"""W47N8 energy-flow model (like tools/model.py + tools/flow.py for home), with W47N7 remote; ideal vs DB actuals per stage.
  .venv/bin/python tools/model_w8.py [--hours 6] [--no-db]
Outputs metrics/model_w47n8.json, DB model_params rows 'w8.*' (ideal, actual), and a stage table on stdout.
Grid: W47N8 (x, y) on top of W47N7 (x, y+50); the exit seam is W47N8 y=49 <-> W47N7 y=0, crossed straight (dx=0).
Movement: road 1 / plain 2 / swamp 10 cost for paths; ticks per tile from the real hauler body (fatigue vs MOVE).
Flow per source: gross 10/t (owned or reserved) - container decay (0.1 owned, 0.5 remote) - miner/hauler upkeep (body/1500)
  = net delivered. Shared: roads (0.001 plain, 0.005 swamp, 0.15 on wall per tile), ramparts 0.03/t each, builder-lite, defenders 0.
  Upgrade = net / (1 + upgrader upkeep per e/t). Hauler CARRY need = income x (round trip x 1.10 + 4) / 50 (home-measured congestion).
RCL5: 1800 cap, 2 links (3% loss): best of (source A link -> ctl link) or (hub/storage link -> ctl link)."""
import os, sys, json, heapq, math, argparse, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts')); sys.path.insert(0, os.path.join(ROOT, 'tools'))
import api
ROOM, REM = 'W47N8', 'W47N7'; OFF = {ROOM: 0, REM: 50}; ME = 'Misaki'
WALKABLE = {'road', 'container', 'rampart', 'constructionSite', 'creep', 'tombstone', 'ruin', 'energy', 'powerCreep'}
COST = {'move': 50, 'work': 100, 'carry': 50, 'attack': 80, 'ranged_attack': 150, 'heal': 250, 'claim': 600, 'tough': 10}
CONG, LINK_LOSS = 1.10, 0.03
CTL_CONT, HUB, SPAWN = (13, 26), (33, 33), (15, 18)
SRC = {'A': (ROOM, (26, 11)), 'B': (ROOM, (11, 43)), 'R1': (REM, (18, 17)), 'R2': (REM, (31, 34))}
# Live link tiles (config CTL_LINK 13,25 + source-A 26,12). When both exist, Memory.ops.w8model
# must use the link-aware flow (A carry=0), not the no-link F4 (which still prices A haul).
LINK_A, LINK_CTL = (26, 12), (13, 25)

def live_links(objs):
    tiles = {(x['x'], x['y']) for x in objs.get(ROOM, {}).get('objects', []) if x.get('type') == 'link'}
    return LINK_A in tiles and LINK_CTL in tiles
PROG = {4: 405000, 5: 1215000, 6: 3645000, 7: 10935000}

def terrain(room):
    p = os.path.join(ROOT, 'data', f'terrain_{room}.txt')
    if not os.path.exists(p): open(p, 'w').write(api.req(f'game/room-terrain?room={room}&encoded=1&shard={api.SHARD}')['terrain'][0]['terrain'])
    return open(p).read().strip()

def load():
    T, objs, roads, block = {}, {}, set(), set()
    for r in (ROOM, REM):
        for i, ch in enumerate(terrain(r)): T[(i % 50, OFF[r] + i // 50)] = 'wall' if int(ch) & 1 else 'swamp' if int(ch) & 2 else 'plain'
        o = api.req(f'game/room-objects?room={r}&shard={api.SHARD}'); objs[r] = o
        for x in o['objects']:
            p = (x['x'], OFF[r] + x['y'])
            if x['type'] == 'road': roads.add(p)
            elif x['type'] not in WALKABLE: block.add(p)
    return T, objs, roads, block

def dijkstra(T, roads, block, start, goal, rng=1):
    gs = {(goal[0] + dx, goal[1] + dy) for dx in range(-rng, rng + 1) for dy in range(-rng, rng + 1)}
    dist, prev, pq = {start: 0}, {}, [(0, start)]
    while pq:
        d, p = heapq.heappop(pq)
        if p in gs and p != start:
            path = [p]
            while path[-1] in prev: path.append(prev[path[-1]])
            return path[::-1][1:]
        if d > dist.get(p, 1e9): continue
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                q = (p[0] + dx, p[1] + dy)
                if q == p or q not in T or T[q] == 'wall' or (q in block and q not in gs): continue
                if (p[1] <= 49) != (q[1] <= 49) and dx != 0: continue
                nd = d + (1 if q in roads else 10 if T[q] == 'swamp' else 2)
                if nd < dist.get(q, 1e9): dist[q] = nd; prev[q] = p; heapq.heappush(pq, (nd, q))
    return []

def tpt(T, roads, p, body, loaded):
    mv = body.count('move'); heavy = sum(1 for b in body if b != 'move' and (b != 'carry' or loaded))
    f = (1 if p in roads else 10 if T[p] == 'swamp' else 2) * heavy
    return max(1, math.ceil(f / (2 * mv))) if mv else 99

def rt(T, roads, path, body):
    return sum(tpt(T, roads, p, body, True) for p in path) + sum(tpt(T, roads, p, body, False) for p in path)

def bodycost(b): return sum(COST[x] for x in b)

def model(T, objs, roads, block):
    M = {'routes': {}, 'sources': {}}
    mine = {}
    for r in (ROOM, REM):
        U = {k: v.get('username') for k, v in objs[r].get('users', {}).items()}
        for x in objs[r]['objects']:
            if x['type'] == 'creep' and U.get(x['user']) == ME: mine[x['name']] = [p['type'] for p in x['body']]
    ctl = next(x for x in objs[ROOM]['objects'] if x['type'] == 'controller')
    M['rcl'], M['progress'] = ctl['level'], ctl.get('progress', 0)
    cap = 300 + 50 * sum(1 for x in objs[ROOM]['objects'] if x['type'] == 'extension')
    M['energy_cap'] = cap
    hb = [b for n, b in mine.items() if n.startswith('w8hauler')] or [['carry'] * 10 + ['move'] * 10]
    rb = [b for n, b in mine.items() if n.startswith('w8rhauler')] or [['carry'] * 16 + ['move'] * 8]
    hbody, rbody = max(hb, key=len), max(rb, key=len)
    for k, (r, (x, y)) in SRC.items():
        s = (x, OFF[r] + y); body = hbody if r == ROOM else rbody
        per = {}
        for tn, tg in (('ctl', CTL_CONT), ('hub', HUB)):
            pa = dijkstra(T, roads, block, s, tg)
            per[tn] = dict(dist=len(pa), swamp=sum(1 for p in pa if T[p] == 'swamp' and p not in roads), unpaved=sum(1 for p in pa if p not in roads),
                           rt=rt(T, roads, pa, body))
        M['routes'][k] = per
    # creep upkeep (live fleet), per role
    up = collections.defaultdict(float)
    for n, b in mine.items():
        role = ''.join(ch for ch in n if not ch.isdigit()); up[role] += bodycost(b) / (600 if 'claim' in b else 1500)
    M['upkeep_live'] = {k: round(v, 2) for k, v in up.items()}
    # shared decay
    rd = 0.0
    for p in roads: rd += {'plain': 0.001, 'swamp': 0.005, 'wall': 0.15}[T[p]]
    nram = sum(1 for x in objs[ROOM]['objects'] if x['type'] == 'rampart')
    M['roads_e'], M['ramparts_e'] = round(rd, 3), round(0.03 * nram, 2)
    return M, mine, hbody, rbody

def flow(M, hbody, rbody, cap, mix_ctl=0.75, links=None):
    """steady state at capacity `cap`; mix_ctl = share of each load that goes to the ctl container (rest to spawn/ext at the hub)"""
    up_body = min(10, (cap - 150) // 100); up_e = (100 * up_body + 150) / 1500 / up_body  # 10W1C2M: upkeep per e/t of upgrading
    S = {}
    for k, per in M['routes'].items():
        remote = k.startswith('R')
        rtt = mix_ctl * per['ctl']['rt'] + (1 - mix_ctl) * per['hub']['rt']
        link = links and k in links.get('src', ())
        if links and links.get('hub') and not remote:  # hub->ctl link: haulers go to the hub, ctl leg by link
            rtt = per['hub']['rt']
        carry = 0 if link else 10 * (rtt * CONG + 4) / 50
        cpc = (bodycost(rbody) / rbody.count('carry')) if remote else (bodycost(hbody) / hbody.count('carry'))
        loss = (0.5 if remote else 0.1) + (10 * LINK_LOSS * (1 if link or (links and links.get('hub')) else 0) * (mix_ctl if not link else 1))
        miner = (800 if remote else 550 + (100 if link else 0)) / 1500  # 10-19 21:4x: w8rminer 6W1C3M (repair blocks harvest; 5W mined ~9/t)
        net = 10 - loss - miner - carry * cpc / 1500
        S[k] = dict(rt=round(rtt), carry=round(carry, 1), hauler_e=round(carry * cpc / 1500, 2), miner_e=round(miner, 2), loss=round(loss, 2), net=round(net, 2))
    shared = {'roads': M['roads_e'], 'ramparts': M['ramparts_e'], 'builder_lite': 1000 / 1500, 'reserver(home-paid)': 0.0}
    net = sum(v['net'] for v in S.values()) - sum(shared.values())
    upg = net / (1 + up_e)
    return dict(sources=S, shared={k: round(v, 3) for k, v in shared.items()}, gross=40.0, net=round(net, 2), upgrade=round(upg, 2),
                upgrader_work=math.ceil(upg), carry_local=round(sum(v['carry'] for k, v in S.items() if not k.startswith('R')), 1),
                carry_remote=round(sum(v['carry'] for k, v in S.items() if k.startswith('R')), 1))

def actuals(hours):
    import db
    c = db.connect(); H = f"{hours} hours"; A = {}
    rs = c.execute(f"""SELECT min(tick),max(tick),min(progress),max(progress),
        extract(epoch from max(ts)-min(ts))/nullif(max(tick)-min(tick),0), (array_agg(storage ORDER BY ts DESC))[1]-(array_agg(storage ORDER BY ts))[1]
        FROM room_stats WHERE room=%s AND ts>now()-interval '{H}' AND rcl=(SELECT rcl FROM room_stats WHERE room=%s ORDER BY ts DESC LIMIT 1)""", (ROOM, ROOM)).fetchone()
    tk = (rs[1] - rs[0]) if rs[0] else 0
    A['ticks'], A['tick_s'] = tk, float(rs[4] or 0)
    A['upgrade'] = round((rs[3] - rs[2]) / tk, 2) if tk else None
    A['storage_delta'] = round((rs[5] or 0) / tk, 2) if tk else None
    cov = c.execute(f"SELECT count(DISTINCT tick)::float/nullif(max(tick)-min(tick)+1,0) FROM creep_ticks WHERE room IN ('W47N8','W47N7') AND ts>now()-interval '{H}'").fetchone()[0] or 1
    rows = c.execute(f"""WITH s AS (SELECT role, room, x, y, store - lag(store) OVER w d, tick - lag(tick) OVER w dt
        FROM creep_ticks WHERE room IN ('W47N8','W47N7') AND ts>now()-interval '{H}' WINDOW w AS (PARTITION BY creep ORDER BY tick))
        SELECT role, room, x, y, sum(d) FILTER (WHERE d>0), -sum(d) FILTER (WHERE d<0) FROM s WHERE dt<=3 GROUP BY 1,2,3,4""").fetchall()
    T_ = max(1, tk) * cov
    pick = collections.Counter(); spent = collections.Counter(); deliv = collections.Counter()
    for role, room, x, y, pos, neg in rows:
        pos, neg = float(pos or 0), float(neg or 0)
        for k, (r, (sx, sy)) in SRC.items():
            if room == r and max(abs(x - sx), abs(y - sy)) <= 1 and role in ('whauler', 'wrhauler', 'wbuilder', 'wupgrader'): pick[k] += pos
        spent[role] += neg
        if role in ('whauler', 'wrhauler') and room == ROOM:
            deliv['ctl' if max(abs(x - CTL_CONT[0]), abs(y - CTL_CONT[1])) <= 1 else 'hub' if max(abs(x - HUB[0]), abs(y - HUB[1])) <= 6 else 'other'] += neg
    A['pickup'] = {k: round(v / T_, 2) for k, v in pick.items()}
    A['spent'] = {k: round(v / T_, 2) for k, v in spent.items()}
    A['delivered'] = {k: round(v / T_, 2) for k, v in deliv.items()}
    A['coverage'] = round(cov, 3)
    ib = c.execute(f"SELECT role, reason, sum(ticks) FROM idle_by_reason WHERE bucket>now()-interval '{H}' AND creep LIKE 'w8%%' GROUP BY 1,2").fetchall()
    tot = collections.Counter(); 
    for role, reason, n in ib: tot[role] += float(n)
    A['idle'] = {role: {} for role in tot}
    for role, reason, n in ib: A['idle'][role][reason] = round(float(n) / tot[role], 2)
    return A

def write_db(rows):
    import db
    with db.connect() as c, c.cursor() as cur:
        cur.executemany("INSERT INTO model_params(ts,key,ideal,actual,unit) VALUES (now(),%s,%s,%s,%s)", rows)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--hours', type=float, default=6); ap.add_argument('--no-db', action='store_true'); a = ap.parse_args()
    T, objs, roads, block = load()
    M, mine, hb, rb = model(T, objs, roads, block)
    F4 = flow(M, hb, rb, M['energy_cap'])
    best5 = None
    for name, ln in (('linkA->ctl', {'src': ('A',)}), ('hub->ctl', {'hub': True})):
        f = flow(M, hb, rb, 1800, links=ln); f['links'] = name
        if not best5 or f['upgrade'] > best5['upgrade']: best5 = f
    live = {'carry_local': sum(b.count('carry') for n, b in mine.items() if n.startswith('w8hauler')),
            'carry_remote': sum(b.count('carry') for n, b in mine.items() if n.startswith('w8rhauler')),
            'upgrader_work': sum(b.count('work') for n, b in mine.items() if n.startswith('w8upgrader')),
            'builder_work': sum(b.count('work') for n, b in mine.items() if n.startswith('w8builder'))}
    st = {}
    for r in (ROOM, REM):
        for x in objs[r]['objects']:
            if x['type'] in ('container', 'storage'): st[f"{r}:{x['type'][:4]}{x['x']},{x['y']}"] = (x.get('store') or {}).get('energy', 0)
    M.update(flow_rcl4=F4, flow_rcl5=best5, live=live, stores=st)
    if not a.no_db:
        A = actuals(a.hours); M['actual'] = A
    rem = max(0, PROG.get(M['rcl'], 0) - M['progress'])
    tick_s = (M.get('actual') or {}).get('tick_s') or 4.2
    # eta_rcl5_h kept as key for Grafana; at RCL6+ it is hours to the next level (PROG[rcl]).
    ideal_up = (best5['upgrade'] if best5 and live_links(objs) else F4['upgrade']) if rem else None
    M['eta_rcl5_h'] = {'ideal': round(rem / ideal_up * tick_s / 3600, 1) if ideal_up else None,
                       'actual': round(rem / M['actual']['upgrade'] * tick_s / 3600, 1) if M.get('actual', {}).get('upgrade') and rem else None}
    os.makedirs(os.path.join(ROOT, 'metrics'), exist_ok=True)
    json.dump(M, open(os.path.join(ROOT, 'metrics', 'model_w47n8.json'), 'w'), indent=1, default=str)
    A = M.get('actual', {})
    P = A.get('pickup', {})
    # 2026-10-29 11:4x strategy: when A→ctl links are live, spawn must see link-era lcarry (~9, B only),
    # not F4's no-link ~22 (A haul still priced). Ideal upgrade/Grafana row also switches to best5.
    use = best5 if (best5 and live_links(objs)) else F4
    rows = [('w8.upgrade', use['upgrade'], A.get('upgrade'), 'e/t'), ('w8.net', use['net'], None, 'e/t'),
            ('w8.carry_local', use['carry_local'], live['carry_local'], 'CARRY'), ('w8.carry_remote', use['carry_remote'], live['carry_remote'], 'CARRY'),
            ('w8.upgrader_work', use['upgrader_work'], live['upgrader_work'], 'WORK'), ('w8.upgrade_rcl5', best5['upgrade'], None, 'e/t'),
            ('w8.eta_rcl5_h', M['eta_rcl5_h']['ideal'], M['eta_rcl5_h']['actual'], 'h')]
    for k in SRC: rows.append((f'w8.src_{k}', use['sources'][k]['net'] + use['sources'][k]['hauler_e'] + use['sources'][k]['miner_e'], P.get(k), 'e/t'))
    if not a.no_db:
        write_db(rows)
        # feed the spawn rules (src/rooms/w47n8/index.js): remote CARRY need and upgrader WORK cap; read back (Misaki: verify writes)
        import subprocess
        v = json.dumps({'rcarry': round(use['carry_remote']), 'lcarry': round(use['carry_local']), 'upw': use['upgrader_work'],
                        'links': bool(use is best5), 't': None})
        expr = f"(Memory.ops.w8model=Object.assign({v},{{t:Game.time}}),JSON.stringify(Memory.ops.w8model))"
        r = subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'q.py'), expr], capture_output=True, text=True, timeout=60)
        print(' Memory.ops.w8model <-', (r.stdout or r.stderr).strip()[:200])
    print(f"W47N8 RCL{M['rcl']} {M['progress']}/{PROG.get(M['rcl'])} cap {M['energy_cap']}  tick {tick_s:.2f}s  window {A.get('ticks')}t cov {A.get('coverage')}")
    print(f"{'stage':<22}{'ideal':>9}{'actual':>9}")
    for k, i, ac, u in rows: print(f"{k:<22}{i if i is not None else '-':>9}{ac if ac is not None else '-':>9} {u}")
    for k, s in F4['sources'].items(): print(f" {k}: rt {s['rt']}t carry {s['carry']} hauler {s['hauler_e']} miner {s['miner_e']} loss {s['loss']} net {s['net']}  routes {M['routes'][k]}")
    print(' shared', F4['shared'], ' upkeep_live', M['upkeep_live'])
    print(' rcl5', best5['links'], best5['upgrade'], ' stores', st)
    if A:  # 15:10 (Misaki): balanced allocation of harvested energy, not only upgrade
        I = A.get('idle', {}); wk = lambda r: (I.get(r) or {}).get('working', 0)
        # 10-19 21:4x: 6W miners mine 12/t and wait for regen (working ~0.83 at a full 10/t), so 10 x working under-read them;
        # per source min(10, 2 x WORK x working). 'working' includes repair ticks, so a 5W rminer still reads ~9.1 (true ~9).
        wavg = lambda p: (lambda b: sum(x.count('work') for x in b) / len(b) if b else 5)([b for n, b in mine.items() if n.startswith(p)])
        harv = 2 * min(10, 2 * wavg('w8miner') * wk('wminer')) + 2 * min(10, 2 * wavg('w8rminer') * wk('wrminer'))
        up = sum(v for k, v in M['upkeep_live'].items() if k != 'reserve')
        al = dict(harvest=round(harv, 1), upgrade=A.get('upgrade'), build_repair=A.get('spent', {}).get('wbuilder'), storage=A.get('storage_delta'), upkeep=round(up, 1))
        al['waste_other'] = round(harv - sum(v or 0 for k, v in al.items() if k != 'harvest'), 1)
        M['alloc'] = al; json.dump(M, open(os.path.join(ROOT, 'metrics', 'model_w47n8.json'), 'w'), indent=1, default=str)
        print(' alloc e/t', al, ' (waste_other = decay + container/stock change + tower + unmeasured)')
    if A: print(' delivered', A.get('delivered'), ' spent', A.get('spent'), ' storage_delta', A.get('storage_delta')); print(' idle', A.get('idle'))
if __name__ == '__main__': main()
