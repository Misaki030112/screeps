"""Read-only neighbour scan (BustJetter, Fandalah, W47N6 battle). Run every 10-60 min from a routine.
Writes events(kind='neighbor', severity, data incl. alert=true/false) and prints "<sev> <ALERT|same> <reasons>".
Rules (classify(), pure, tested in tests/neighbor_scan.py):
- high: any BJ/FD combat creep (ATTACK/RANGED/HEAL) in a room adjacent to W46N8/W45N8 or on the way (TRANSIT);
        W47N6 squad present while its safe mode is over, or W47N6 structure hits dropping (fight started);
        any single creep with >=5 ATTACK+RANGED in TRANSIT.
- medium: combat squad (>=3 combat creeps) staged in W47N6 or a BJ/FD home room; BJ towers in W47N9/W48N9 refilled (>500).
- low otherwise. Dedup: alert=true only when (severity, reasons) differ from the last scan (state/neighbor_scan.json).
"""
import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OWNERS = ('BustJetter', 'Fandalah')
HOME = ['W47N9', 'W48N9', 'W49N9', 'W44N8', 'W47N5']
TRANSIT = ['W47N8', 'W47N7', 'W46N7', 'W46N9', 'W45N9', 'W45N7', 'W45N8', 'W46N8']
WATCH = ['W47N6']
COMBAT = ('attack', 'ranged_attack', 'heal')
STATE = os.path.join(ROOT, 'state', 'neighbor_scan.json')

def snap(api, r):
    o = api.req(f'game/room-objects?room={r}&shard=shard3'); U = {k: v.get('username') for k, v in o.get('users', {}).items()}
    t = api.req('game/time?shard=shard3').get('time', 0)
    cs, hits, towers, safe = [], 0, [], None
    for x in o['objects']:
        if x['type'] == 'creep' and U.get(x.get('user')) in OWNERS:
            b = collections.Counter(p['type'] for p in x['body'])
            cs.append(dict(owner=U.get(x['user']), name=x['name'], body=dict(b), x=x['x'], y=x['y'], hits=x['hits']))
        elif x['type'] == 'tower' and U.get(x.get('user')) in OWNERS: towers.append(x.get('store', {}).get('energy', 0))
        elif x['type'] == 'controller': safe = x.get('safeMode')
        if x['type'] in ('spawn', 'constructedWall', 'rampart', 'tower', 'extension') and x.get('hits') is not None: hits += x['hits']
    return dict(room=r, time=t, creeps=cs, towers=towers, safe_until=safe, struct_hits=hits)

def combat(c): return any(c['body'].get(k, 0) for k in COMBAT)

def classify(S, prev=None):
    """S: {room: snap}. Returns (severity, sorted reasons)."""
    prev = prev or {}; hi, med = [], []
    for r in TRANSIT:
        s = S.get(r)
        if not s: continue
        cc = [c for c in s['creeps'] if combat(c)]
        if cc: hi.append(f"{r}: {len(cc)} combat creeps ({','.join(sorted({c['owner'] for c in cc}))})")
    w = S.get('W47N6')
    if w:
        cc = [c for c in w['creeps'] if combat(c)]
        p = prev.get('W47N6') or {}
        if cc and (not w['safe_until'] or w['safe_until'] <= w['time']): hi.append(f"W47N6: safe mode over, {len(cc)} combat creeps present")
        if p.get('struct_hits') and w['struct_hits'] < p['struct_hits'] - 1000: hi.append('W47N6: structures losing hits (fight started)')
        if len(cc) >= 3: med.append(f"W47N6: squad of {len(cc)} staged (safe mode until {w['safe_until']})")
    for r in HOME:
        s = S.get(r)
        if not s: continue
        cc = [c for c in s['creeps'] if combat(c)]
        if len(cc) >= 3: med.append(f'{r}: {len(cc)} combat creeps at home')
        if r in ('W47N9', 'W48N9') and s['towers'] and min(s['towers']) > 500: med.append(f'{r}: towers refilled')
    return ('high' if hi else 'medium' if med else 'low'), sorted(hi + med)

def main():
    sys.path.insert(0, os.path.join(ROOT, 'scripts')); sys.path.insert(0, HERE)
    import api, db
    S = {r: snap(api, r) for r in HOME + TRANSIT + WATCH}
    prev = json.load(open(STATE)) if os.path.exists(STATE) else {}
    sev, why = classify(S, prev.get('snaps'))
    alert = [sev, why] != prev.get('key')
    json.dump(dict(key=[sev, why], snaps={r: {k: v for k, v in s.items() if k != 'creeps'} for r, s in S.items()}), open(STATE, 'w'))
    data = dict(alert=alert, reasons=why, rooms={r: dict(creeps=[c for c in s['creeps'] if combat(c) or c['body'].get('tough', 0) >= 4], towers=s['towers'], safe_until=s['safe_until']) for r, s in S.items()})
    c = db.connect()
    c.execute("INSERT INTO events(ts,kind,room,severity,msg,data) VALUES (now(),'neighbor','W46N8',%s,%s,%s)", (sev, 'neighbor scan' + (' ALERT' if alert else ''), json.dumps(data)))
    print(sev, 'ALERT' if alert else 'same', '; '.join(why) or '-')

if __name__ == '__main__': main()
