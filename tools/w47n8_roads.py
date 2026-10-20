"""W47N8 road audit: target network (shared trunks over v3b) vs live roads + 24h traffic -> keep / deprecate / missing.
usage: w47n8_roads.py ROUND_PARAMS_JSON [png] [out_js]"""
import sys, json, heapq, collections
sys.path.insert(0, 'tools'); from model import terrain
import db
from PIL import Image, ImageDraw
T = terrain('W47N8'); WALL = lambda x, y: int(T[y*50+x]) & 1; SW = lambda x, y: int(T[y*50+x]) & 2
N8 = [(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b]
P = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
REUSE = P.get('reuse', 1.5); SWAMP = P.get('swamp', 10); PLAIN = P.get('plain', 2); MINERAL = P.get('mineral', True); TRAFFIC_KEEP = P.get('tkeep', 400)
obj = json.load(open('/tmp/w8obj.json'))
L = json.loads(open('src/rooms/w47n8/layout.js').read().split('module.exports = ', 1)[1].rstrip().rstrip(';'))
live = {(o['x'], o['y']) for o in obj if o['type'] == 'road'}
block = set()
for o in obj:
    if o['type'] in ('constructedWall', 'extension', 'spawn', 'tower', 'storage', 'link', 'terminal', 'lab', 'controller', 'source', 'mineral'): block.add((o['x'], o['y']))
for t, ps in L['ORDER'].items():
    if t not in ('road', 'container', 'rampart', 'extractor'): block |= {tuple(p) for p in ps}
# base: strip spines + hub cross (part of the v3b design itself)
target = set()
for s in L['STRIPS']: target |= {tuple(p) for p in s['road']}
CX, CY = L['CORE']; target |= {(CX+a, CY+b) for a, b in ((0, 0), (0, 1), (0, -1), (1, 0), (-1, 0)) if not WALL(CX+a, CY+b) and (CX+a, CY+b) not in block}
target = {p for p in target if not WALL(*p) and p not in block}
def cost(p):
    if p in target: return 1
    if p in live: return REUSE
    return SWAMP if SW(*p) else PLAIN
def trunk(goals, rng=1):
    near = set()
    for g in goals:
        for a in range(-rng, rng+1):
            for b in range(-rng, rng+1): near.add((g[0]+a, g[1]+b))
    D = {p: 0 for p in target}; pq = [(0, p) for p in target]; heapq.heapify(pq); prev = {}
    while pq:
        d, p = heapq.heappop(pq)
        if p in near and p not in block: break
        if d > D[p]: continue
        for a, b in N8:
            n = (p[0]+a, p[1]+b)
            if not (0 < n[0] < 49 and 0 < n[1] <= 49) or WALL(*n) or n in block: continue
            nd = d + cost(n)
            if nd < D.get(n, 1e9): D[n] = nd; prev[n] = p; heapq.heappush(pq, (nd, n))
    if not (p in near and p not in block): print("UNREACHED", goals, file=sys.stderr); return -1
    path = []
    while p in prev: path.append(p); p = prev[p]
    for q in path: target.add(q)
    return len(path)
# 10-20 13:39 (Misaki): spawn moves to 32,32 -> no spawn2 trunk; tower 24,8 refill trunk instead (param spawn2=1 restores)
GOALS = [('ctl', [(13, 26)], 1), ('srcN', [(26, 11)], 1)] + ([('spawn2', [(15, 18)], 1)] if P.get('spawn2') else [('tower2', [(24, 8)], 1)]) + [ ('exitS', [(18, 49), (19, 49)], 0), ('srcS', [(11, 43)], 1)]
if MINERAL: GOALS.append(('mineral', [(37, 45)], 1))
if P.get('order') == 'far': GOALS.sort(key=lambda g: -abs(g[1][0][0]-CX)-abs(g[1][0][1]-CY))
added = {k: trunk(g, r) for k, g, r in GOALS}
c = db.connect()
tr = collections.Counter({(x, y): n for x, y, n in c.execute("select x,y,count(*) from creep_ticks where room='W47N8' and ts>now()-interval '24 hours' group by x,y")})
keep = live & target
hot = {p for p in live - target if tr[p] >= TRAFFIC_KEEP and (P.get('spawn2') or not (abs(p[0]-15) <= 6 and abs(p[1]-18) <= 6))}  # spawn-cluster traffic ends with the move
target |= hot; keep |= hot
dep = live - target; miss = target - live
swamp_t = sum(1 for p in target if SW(*p))
edge = min(min(p[0], p[1], 49-p[0], 49-p[1]) for p in target - {p for p in target if p[1] >= 46 and 15 <= p[0] <= 21})
# road decay: 100 hits/1000t plain (swamp x5); repair 1 energy per 100 hits -> 0.001 e/t plain, 0.005 swamp
repE = lambda S: sum(0.005 if SW(*p) else 0.001 for p in S)
spawn2_only = {p for p in dep if abs(p[0]-15) <= 6 and abs(p[1]-18) <= 6}
M = {'params': P, 'live': len(live), 'target': len(target), 'keep': len(keep), 'keepHot': len(hot), 'deprecate': len(dep), 'missing': len(miss),
     'swampInTarget': swamp_t, 'trunkAdded': added, 'repairE_live': round(repE(live), 3), 'repairE_target': round(repE(target), 3),
     'savedE': round(repE(dep), 3), 'depTraffic': sum(tr[p] for p in dep), 'keepTraffic': sum(tr[p] for p in keep), 'edgeMin': edge, 'depNearSpawn2': len(spawn2_only)}
print(json.dumps(M))
if len(sys.argv) > 2 and sys.argv[2]:
    S = 14; im = Image.new('RGB', (50*S, 50*S+40), 'white'); d = ImageDraw.Draw(im)
    mx = max(tr.values()) if tr else 1
    for y in range(50):
        for x in range(50):
            col = (40, 40, 40) if WALL(x, y) else ((150, 170, 120) if SW(x, y) else (225, 225, 215))
            d.rectangle([x*S, y*S, x*S+S-1, y*S+S-1], fill=col)
    for t, ps in L['ORDER'].items():
        if t in ('road', 'rampart'): continue
        for x, y in ps: d.rectangle([x*S+3, y*S+3, x*S+S-4, y*S+S-4], fill={'extension': (255, 200, 0), 'spawn': (255, 0, 255), 'tower': (220, 30, 30), 'storage': (0, 120, 0), 'container': (200, 120, 50)}.get(t, (90, 90, 90)))
    for p, cl in [(keep, (0, 190, 0)), (dep, (230, 0, 0)), (miss, (0, 90, 255))]:
        for x, y in p: d.rectangle([x*S+1, y*S+1, x*S+S-2, y*S+S-2], outline=cl, width=3)
    for (x, y), n in tr.items():
        if n >= 200: d.ellipse([x*S+5, y*S+5, x*S+9, y*S+9], fill=(0, 0, 0))
    for x, y in [(15, 18)]: d.text((x*S+3, y*S+1), '2', fill='black')
    d.text((4, 50*S+4), 'W47N8 roads: green keep %d, red deprecate %d, blue missing %d (target %d). yellow=v3b ext, magenta=spawns, dot=>=200 creep-ticks/24h' % (len(keep), len(dep), len(miss), len(target)), fill='black')
    d.text((4, 50*S+20), 'swamp shade green-grey; trunks: ' + json.dumps(added), fill='black')
    im.save(sys.argv[2])
if len(sys.argv) > 3:
    open(sys.argv[3], 'w').write('// GENERATED by tools/w47n8_roads.py: target road network (v3b + shared trunks). Only these roads are placed/repaired;\n'
        '// others are deprecated (decay naturally, never dismantled).\nmodule.exports = ' + json.dumps({'ROADS': sorted([list(p) for p in target]), 'DEPRECATED': sorted([list(p) for p in dep])}, separators=(',', ':')) + ';\n')
