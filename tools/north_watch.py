"""North watch (Misaki 14:23): W47N8 / W47N9 / W48N9 via the room-objects API (read-only), wired into alerts.py.
MEDIUM alert episodes (alert_state) for:
  - any non-our creep with ATTACK/RANGED_ATTACK/WORK or boosted parts inside W47N8
  - a combat group >= 2 armed (ATTACK/RANGED_ATTACK) creeps in W47N9 or W48N9
  - boost stock rise (UH/KO/LO + their T2/T3 compounds, storage+terminal+labs) >= 300 since the last scan
Also sets Memory.ops.w8threatN = Game.time (console) when W47N9 holds an armed or HEAL group (TOUGH-only decoys ignored) or W48N9 holds >=2 armed, which keeps W47N8
in wall threat mode (src/rooms/w47n8/threat.js). Never attacks, never touches safe mode.
usage: north_watch.py [--quiet]"""
import sys, os, json, subprocess, collections
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(H, '..', 'scripts')); sys.path.insert(0, H)
import api, ingest
ME = 'Misaki'; ROOMS = ['W47N8', 'W47N9', 'W48N9']; STATE = os.path.join(H, '..', 'state', 'north_watch.json')
BOOST = ('UH', 'KO', 'LO', 'UH2O', 'KHO2', 'LHO2', 'XUH2O', 'XKHO2', 'XLHO2')
def hostile_creeps(objs, U):
    """creeps not owned by ME (our own never count as armed/drain/intrusion)"""
    return [x for x in objs if x['type'] == 'creep' and U.get(x.get('user')) != ME]
def triggers(room, armed, drain): return (room == 'W47N9' and bool(armed or drain)) or (room == 'W48N9' and len(armed) >= 2)
SEAL_FIGHT = (27, 3)  # centre of the east seal (src/rooms/w47n8/index.js SEAL_FIGHT)
def seal_ranges(objs, U):
    """ranges from our live W47N8 towers to the seal fight point (RCL5 adds 24,8 -> r5); [] when none seen"""
    return [max(abs(x['x'] - SEAL_FIGHT[0]), abs(x['y'] - SEAL_FIGHT[1])) for x in objs if x['type'] == 'tower' and U.get(x.get('user')) == ME]
def verdict(bodies, inside=False, tr=None):
    """towers-only / towers + 2 defenders outcome at the seal (tr = live tower ranges, RCL4 fallback 1 tower r32; inside: at Spawn2, r19).
    bodies must include the group's healers (05:4x: healers were left out, so 2RA+2H read 'towers win' while the sim says towers lose). Advice only."""
    import combat_sim as S
    mk = lambda: [S.Cr(str(i), S.body(**{k: v for k, v in b.items() if k in ('tough', 'move', 'attack', 'ranged_attack', 'heal')})) for i, b in enumerate(bodies)]
    tr = [19] if inside else (tr or [32])
    a, d = S.fight(mk(), tr, 0), S.fight(mk(), tr, 2)
    v = 'towers win' if a['result'] == 'win' else 'towers+2 defenders win' if d['result'] == 'win' else 'unwinnable' + (' -> recommend safe mode to Misaki if it pushes past the seal' if not inside else ' inside -> recommend safe mode to Misaki')
    return f"{v} (towers {a['result']}, +2def {d['result']})"
TR = []  # live W47N8 tower ranges to SEAL_FIGHT, filled from the W47N8 scan (first in ROOMS)
def main():
    global st, invN
    st = json.load(open(STATE)) if os.path.exists(STATE) else {}
    tick = api.req('game/time?shard=' + api.SHARD).get('time', 0)
    alerts, summary, threatN, invN, n9, x9 = [], {}, False, False, [], 29
    for r in ROOMS:
        o = api.req(f'game/room-objects?room={r}&shard={api.SHARD}'); U = {k: v.get('username') for k, v in o.get('users', {}).items()}
        cs = hostile_creeps(o['objects'], U)
        stock = collections.Counter()
        for x in o['objects']:
            if x['type'] in ('storage', 'terminal', 'lab') and U.get(x.get('user')) != ME:
                for k, v in (x.get('store') or {}).items():
                    if k in BOOST and v: stock[k] += v
        armed, drain, intr, heal = [], [], [], []
        if r == 'W47N8': TR[:] = seal_ranges(o['objects'], U)
        for x in cs:
            b = collections.Counter(p['type'] for p in x['body']); boosted = any(p.get('boost') for p in x['body'])
            info = {'owner': U.get(x['user']), 'pos': [x['x'], x['y']], 'body': dict(b), 'boosted': boosted}
            if b['attack'] or b['ranged_attack']: armed.append(info)
            if b['heal']: drain.append(info)  # 10-20 06:2x: TOUGH-only decoys ignored (Misaki: no influence on threat/roster sim)
            if b['heal']: heal.append(info)
            if r == 'W47N8' and (b['attack'] or b['ranged_attack'] or b['work'] or boosted): intr.append(info)
        summary[r] = {'creeps': len(cs), 'armed': len(armed), 'drain': len(drain), 'boost': dict(stock)}
        def add(kind, cre, extra=None):
            own = (cre[0]['owner'] if cre else None) or '?'
            ep = f'north-{r}-{kind}-{tick // 1500}'
            a = {'episode': ep, 'severity': 'medium', 'room': r, 'owner': own, 'tick': tick, 'creeps': len(cre), 'kind': kind,
                 'body': [c['body'] for c in cre][:6], 'positions': [c['pos'] for c in cre][:6], 'totalDamage': 0, 'structureHitLoss': 0, 'damaged': []}
            if extra: a.update(extra)
            if cre and kind in ('intrusion', 'group'):  # 17:3x: combat-model verdict for Misaki (tools/combat_sim.py); 05:4x: + same-room healers, live tower ranges
                sup = [c for c in heal if c not in cre and any(max(abs(c['pos'][0] - g['pos'][0]), abs(c['pos'][1] - g['pos'][1])) <= 3 for g in cre)]  # healers escorting the group (<=3 tiles), not the room's own
                if sup: a['support'] = len(sup)
                try: a['verdict'] = verdict([c['body'] for c in cre + sup], inside=(kind == 'intrusion'), tr=TR)
                except Exception as ex: a['verdict'] = 'sim error ' + str(ex)[:60]
            alerts.append((a, ingest.alert_state(a, None)))
        if intr: add('intrusion', intr)
        if r in ('W47N9', 'W48N9') and len(armed) >= 2: add('group', armed)
        prev = st.get(r, {}).get('boost', {})
        rise = {k: v - prev.get(k, 0) for k, v in stock.items() if v - prev.get(k, 0) >= 300}
        if prev and rise: add('boost', [], {'owner': (U.get(next((x.get('user') for x in o['objects'] if x['type'] == 'controller' and x.get('user')), None)) or '?'), 'rise': rise})
        if triggers(r, armed, drain): threatN = True  # W47N9 armed/drain, or W48N9 >=2 armed (Misaki 14:27)
        if r == 'W47N9' and len(armed) >= 2: invN = True  # 14:46 armed group at the W47N9 border -> border defenders
        if r == 'W47N9': g9 = list({id(i): i for i in armed + drain}.values()); n9 = [i['body'] for i in g9][:12]; x9 = round(sum(i['pos'][0] for i in g9) / len(g9)) if g9 else 29  # 17:3x: bodies + mean x for the in-game assessment / staging
        st[r] = {'tick': tick, 'boost': dict(stock)}
    json.dump(st, open(STATE, 'w'))
    if threatN:
        nb = json.dumps([{k: v for k, v in b.items() if k in ('attack', 'ranged_attack', 'heal', 'tough', 'move', 'work', 'claim')} for b in n9], separators=(',', ':'))
        uh = sum(v for r2 in ('W47N9', 'W48N9') for k, v in st.get(r2, {}).get('boost', {}).items() if 'UH' in k)  # 17:58: UH stock -> plan assumes boosted melee
        expr = f'(Memory.ops.w8uh={uh},Memory.ops.w8threatN=Game.time,' + (f'Memory.ops.w8invN=Game.time,Memory.ops.w8invNb={nb},Memory.ops.w8invNx={x9},' if invN else '') + '"ok")'  # w8invN: armed group at the W47N9 border -> W47N8 border defenders
        subprocess.run([sys.executable, os.path.join(H, 'q.py'), expr], capture_output=True, timeout=60)
    if '--quiet' not in sys.argv:
        print(json.dumps({'tick': tick, 'rooms': summary, 'threatN': threatN, 'alerts': [(a['episode'], s) for a, s in alerts]}))

if __name__ == '__main__': main()