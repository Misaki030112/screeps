"""North watch (Misaki 14:23): W47N8 / W47N9 / W48N9 via the room-objects API (read-only), wired into alerts.py.
MEDIUM alert episodes (alert_state) for:
  - any non-our creep with ATTACK/RANGED_ATTACK/WORK or boosted parts inside W47N8
  - a combat group >= 2 armed (ATTACK/RANGED_ATTACK) creeps in W47N9 or W48N9
  - boost stock rise (UH/KO/LO + their T2/T3 compounds, storage+terminal+labs) >= 300 since the last scan
Also sets Memory.ops.w8threatN = Game.time (console) when W47N9 holds an armed or drain (TOUGH>=5 / HEAL) group, which keeps W47N8
in wall threat mode (src/rooms/w47n8/threat.js). Never attacks, never touches safe mode.
usage: north_watch.py [--quiet]"""
import sys, os, json, subprocess, collections
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(H, '..', 'scripts')); sys.path.insert(0, H)
import api, ingest
ME = 'Misaki'; ROOMS = ['W47N8', 'W47N9', 'W48N9']; STATE = os.path.join(H, '..', 'state', 'north_watch.json')
BOOST = ('UH', 'KO', 'LO', 'UH2O', 'KHO2', 'LHO2', 'XUH2O', 'XKHO2', 'XLHO2')
st = json.load(open(STATE)) if os.path.exists(STATE) else {}
tick = api.req('game/time?shard=' + api.SHARD).get('time', 0)
alerts, summary, threatN = [], {}, False
for r in ROOMS:
    o = api.req(f'game/room-objects?room={r}&shard={api.SHARD}'); U = {k: v.get('username') for k, v in o.get('users', {}).items()}
    cs = [x for x in o['objects'] if x['type'] == 'creep' and U.get(x['user']) != ME]
    stock = collections.Counter()
    for x in o['objects']:
        if x['type'] in ('storage', 'terminal', 'lab') and U.get(x.get('user')) != ME:
            for k, v in (x.get('store') or {}).items():
                if k in BOOST and v: stock[k] += v
    armed, drain, intr = [], [], []
    for x in cs:
        b = collections.Counter(p['type'] for p in x['body']); boosted = any(p.get('boost') for p in x['body'])
        info = {'owner': U.get(x['user']), 'pos': [x['x'], x['y']], 'body': dict(b), 'boosted': boosted}
        if b['attack'] or b['ranged_attack']: armed.append(info)
        if b['heal'] or b['tough'] >= 5: drain.append(info)
        if r == 'W47N8' and (b['attack'] or b['ranged_attack'] or b['work'] or boosted): intr.append(info)
    summary[r] = {'creeps': len(cs), 'armed': len(armed), 'drain': len(drain), 'boost': dict(stock)}
    def add(kind, cre, extra=None):
        own = (cre[0]['owner'] if cre else None) or '?'
        ep = f'north-{r}-{kind}-{tick // 1500}'
        a = {'episode': ep, 'severity': 'medium', 'room': r, 'owner': own, 'tick': tick, 'creeps': len(cre), 'kind': kind,
             'body': [c['body'] for c in cre][:6], 'positions': [c['pos'] for c in cre][:6], 'totalDamage': 0, 'structureHitLoss': 0, 'damaged': []}
        if extra: a.update(extra)
        alerts.append((a, ingest.alert_state(a, None)))
    if intr: add('intrusion', intr)
    if r in ('W47N9', 'W48N9') and len(armed) >= 2: add('group', armed)
    prev = st.get(r, {}).get('boost', {})
    rise = {k: v - prev.get(k, 0) for k, v in stock.items() if v - prev.get(k, 0) >= 300}
    if prev and rise: add('boost', [], {'owner': (U.get(next((x.get('user') for x in o['objects'] if x['type'] == 'controller' and x.get('user')), None)) or '?'), 'rise': rise})
    if r == 'W47N9' and (armed or drain): threatN = True
    st[r] = {'tick': tick, 'boost': dict(stock)}
json.dump(st, open(STATE, 'w'))
if threatN:
    subprocess.run([sys.executable, os.path.join(H, 'q.py'), '(Memory.ops.w8threatN=Game.time,"ok")'], capture_output=True, timeout=60)
if '--quiet' not in sys.argv:
    print(json.dumps({'tick': tick, 'rooms': summary, 'threatN': threatN, 'alerts': [(a['episode'], s) for a, s in alerts]}))
