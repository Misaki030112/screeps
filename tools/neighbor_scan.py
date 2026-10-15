"""Read-only scan of neighbour rooms (BustJetter, Fandalah): creeps with combat parts, tower/storage energy, spawning.
Writes one events row (kind='neighbor', severity low/medium/high) and prints a summary. Run hourly from a routine.
high: any creep with >=5 ATTACK/RANGED_ATTACK/WORK+TOUGH-heavy, or >=3 combat creeps in one room, or towers refilled >500 in BJ W47N9/W48N9.
"""
import sys, os, json, collections
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts')); sys.path.insert(0, os.path.dirname(__file__))
import api, db
ROOMS = {'W47N9': 'BustJetter', 'W48N9': 'BustJetter', 'W49N9': 'BustJetter', 'W44N8': 'Fandalah', 'W47N5': 'Fandalah'}
COMBAT = ('attack', 'ranged_attack', 'heal', 'claim')
out, sev = {}, 'low'
for r, owner in ROOMS.items():
    o = api.req(f'game/room-objects?room={r}&shard=shard3'); U = {k: v.get('username') for k, v in o.get('users', {}).items()}
    cs = []
    for x in o['objects']:
        if x['type'] == 'creep' and U.get(x.get('user')) == owner:
            b = collections.Counter(p['type'] for p in x['body']); cp = sum(b[t] for t in COMBAT)
            if cp or b['tough'] >= 4: cs.append(dict(name=x['name'], body=dict(b)))
            if b['attack'] + b['ranged_attack'] >= 5: sev = 'high'
    tw = [x.get('store', {}).get('energy', 0) for x in o['objects'] if x['type'] == 'tower']
    st = [x.get('store', {}).get('energy', 0) for x in o['objects'] if x['type'] == 'storage']
    if sum(1 for c in cs if any(c['body'].get(t, 0) for t in ('attack', 'ranged_attack'))) >= 3: sev = 'high'
    if owner == 'BustJetter' and r != 'W49N9' and tw and min(tw) > 500 and sev == 'low': sev = 'medium'
    out[r] = dict(owner=owner, combat_or_tough=cs, towers=tw, storage=st)
print(sev, json.dumps(out))
c = db.connect()
c.execute("INSERT INTO events(ts,kind,room,severity,msg,data) VALUES (now(),'neighbor','W46N8',%s,'neighbor scan',%s)", (sev, json.dumps(out)))
