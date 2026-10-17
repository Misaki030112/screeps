"""Read-only scan of neighbour rooms (BustJetter, Fandalah): creeps with combat parts, tower/storage energy, spawning.
Writes one events row (kind='neighbor', severity low/medium/high) and prints a summary. Run hourly from a routine.
high: any creep with >=5 ATTACK/RANGED_ATTACK/WORK+TOUGH-heavy, or >=3 combat creeps in one room, or towers refilled >500 in BJ W47N9/W48N9.
Line 2 ("trend ...") compares each room's combat-creep count with its own last-48h band from earlier scans and flags
what is actually new: above the 48h max, combat creeps in the approach rooms next to us (W47N8/W47N7), or boosted parts.
W48N9 has swung 4-15 combat creeps all of 10-16/10-17 with towers unfed (~0), so "high" alone is its normal state
(strategy review 10-17). Owner None = any player except us (W48N8 Evans_702, approach rooms).
"""
import sys, os, json, collections
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts')); sys.path.insert(0, os.path.dirname(__file__))
import api, db
ROOMS = {'W47N9': 'BustJetter', 'W48N9': 'BustJetter', 'W49N9': 'BustJetter', 'W44N8': 'Fandalah', 'W47N5': 'Fandalah',
         'W48N8': None, 'W47N8': None, 'W47N7': None}
APPROACH = ('W47N8', 'W47N7')
ME = 'Misaki'
COMBAT = ('attack', 'ranged_attack', 'heal', 'claim')
out, sev = {}, 'low'
for r, owner in ROOMS.items():
    o = api.req(f'game/room-objects?room={r}&shard=shard3'); U = {k: v.get('username') for k, v in o.get('users', {}).items()}
    cs = []; ctl = next((x for x in o['objects'] if x['type'] == 'controller'), None)
    cown = U.get((ctl or {}).get('user')) or ((ctl or {}).get('reservation') or {}).get('user') and 'res:' + U.get(ctl['reservation']['user'], '?')
    for x in o['objects']:
        u = U.get(x.get('user'))
        if x['type'] == 'creep' and (u == owner if owner else u not in (None, ME, 'Invader', 'Source Keeper')):
            b = collections.Counter(p['type'] for p in x['body']); cp = sum(b[t] for t in COMBAT if t != 'claim')
            nb = sum(1 for p in x['body'] if p.get('boost'))
            if cp or b['tough'] >= 4: cs.append(dict(name=x['name'], user=u, boosted=nb, body=dict(b)))
            if b['attack'] + b['ranged_attack'] >= 5: sev = 'high'
    tw = [x.get('store', {}).get('energy', 0) for x in o['objects'] if x['type'] == 'tower']
    st = [x.get('store', {}).get('energy', 0) for x in o['objects'] if x['type'] == 'storage']
    if sum(1 for c in cs if any(c['body'].get(t, 0) for t in ('attack', 'ranged_attack'))) >= 3: sev = 'high'
    if owner == 'BustJetter' and r != 'W49N9' and tw and min(tw) > 500 and sev == 'low': sev = 'medium'
    out[r] = dict(owner=owner or cown, combat_or_tough=cs, towers=tw, storage=st)
print(sev, json.dumps(out))
c = db.connect()
ncomb = lambda cs: sum(1 for x in cs if any(x['body'].get(t, 0) for t in ('attack', 'ranged_attack', 'heal')))
hist = collections.defaultdict(list)
for (d,) in c.execute("SELECT data FROM events WHERE kind='neighbor' AND ts > now()-interval '48 hours'").fetchall():
    for r, v in (d or {}).items(): hist[r].append(ncomb(v.get('combat_or_tough', [])))
trend, new = {}, []
for r, v in out.items():
    n, h = ncomb(v['combat_or_tough']), sorted(hist.get(r, []))
    trend[r] = dict(now=n, lo=h[0], med=h[len(h) // 2], hi=h[-1], scans=len(h)) if h else dict(now=n, scans=0)
    boosted = sum(x['boosted'] for x in v['combat_or_tough'])
    if h and n > h[-1]: new.append(f'{r} {n} combat > 48h max {h[-1]}')
    if r in APPROACH and n: new.append(f'{r} (next to W46N8) has {n} combat creeps')
    if boosted: new.append(f'{r} {boosted} boosted parts')
print('trend', 'NEW: ' + '; '.join(new) if new else 'no change vs 48h band', json.dumps(trend))
c.execute("INSERT INTO events(ts,kind,room,severity,msg,data) VALUES (now(),'neighbor','W46N8',%s,'neighbor scan',%s)", (sev, json.dumps(out)))
