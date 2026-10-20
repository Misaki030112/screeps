"""W47N8 road plan v4 (10-20 post spawn move): old west base (spawn 15,18 + its extension cluster) is gone.
Prune the previous plan to a Steiner-style tree: seed = hub/strips/exit corridors, then add the cheapest path from the
tree to each goal (prefer existing plan roads, then live roads). Plan tiles off the tree but hot (>=TKEEP creep-ticks/6h
and adjacent to the tree) are kept. usage: w47n8_roads_v4.py [png] [out_js]   (reads /tmp/w8obj.json)"""
import sys, json, heapq, collections
sys.path.insert(0, 'tools'); from model import terrain
import db
from PIL import Image, ImageDraw
T = terrain('W47N8'); WALL = lambda x, y: int(T[y*50+x]) & 1; SW = lambda x, y: int(T[y*50+x]) & 2
N8 = [(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b]
OLD = {tuple(p) for p in json.loads(open('src/rooms/w47n8/roads.js').read().split('module.exports = ', 1)[1].rstrip().rstrip(';'))['ROADS']}
MIN = json.loads(open('src/rooms/w47n8/roads.js').read().split('module.exports = ', 1)[1].rstrip().rstrip(';'))['MINERAL']
L = json.loads(open('src/rooms/w47n8/layout.js').read().split('module.exports = ', 1)[1].rstrip().rstrip(';'))
obj = json.load(open('/tmp/w8obj.json'))
live = {(o['x'], o['y']) for o in obj if o['type'] == 'road'}
block = {(o['x'], o['y']) for o in obj if o['type'] in ('constructedWall', 'extension', 'spawn', 'tower', 'storage', 'link', 'controller', 'source', 'mineral', 'constructionSite')}
for t, ps in L['ORDER'].items():
    if t not in ('road', 'container', 'rampart', 'extractor'): block |= {tuple(p) for p in ps}
block -= OLD  # never let layout slots block an already-planned road tile
EAST = [(38, 30), (39, 30), (40, 31), (41, 30), (42, 29), (43, 28), (44, 27), (45, 26), (46, 25), (47, 24), (48, 23)]
SOUTH = [(17, 47), (18, 48), (18, 49)]
# seed: hub ring + x38 fill strip + y35 fill row + x31 fill column (all serve built extensions) + exit corridors
SEED = {p for p in OLD if (abs(p[0]-35) <= 3 and abs(p[1]-32) <= 3) or (p[0] == 38 and 29 <= p[1] <= 36) or (p[1] == 35 and 26 <= p[0] <= 33)
        or (p[0] == 31 and 23 <= p[1] <= 28) or p == (37, 29)} | set(EAST)
tree = set(SEED)
def cost(p): return 1 if p in OLD else 50  # only re-use planned tiles; new tiles only if no planned path exists
def connect(goal):
    D = {p: 0 for p in tree}; pq = [(0, p) for p in tree]; heapq.heapify(pq); prev = {}
    while pq:
        d, p = heapq.heappop(pq)
        if d > D[p]: continue
        if goal(p): break
        for a, b in N8:
            n = (p[0]+a, p[1]+b)
            if not (0 < n[0] < 49 and 0 < n[1] <= 49) or WALL(*n) or n in block: continue
            nd = d + cost(n)
            if nd < D.get(n, 1e9): D[n] = nd; prev[n] = p; heapq.heappush(pq, (nd, n))
    path = []
    while p in prev: path.append(p); p = prev[p]
    tree.update(path); return len(path)
ch = lambda c, r: (lambda p: max(abs(p[0]-c[0]), abs(p[1]-c[1])) <= r)
GOALS = [('southExit', lambda p: p == (17, 47)), ('ctl', ch((13, 26), 1)), ('srcS', ch((11, 43), 1)), ('srcN', ch((26, 11), 1)), ('tower24_8', ch((24, 8), 1)),
         ('gate29_3', lambda p: p == (29, 3)), ('wallE', ch((25, 6), 0)), ('wallW', lambda p: 8 <= p[0] <= 11 and p[1] <= 6)]
added = {k: connect(g) for k, g in GOALS}; tree |= set(SOUTH)
c = db.connect()
tr = collections.Counter({(x, y): n for x, y, n in c.execute("select x,y,count(*) from creep_ticks where room='W47N8' and ts>now()-interval '6 hours' group by x,y")})
TKEEP = 150
for _ in range(3):
    hot = {p for p in OLD - tree if tr[p] >= TKEEP and any((p[0]+a, p[1]+b) in tree for a, b in N8) and not (abs(p[0]-15) <= 7 and abs(p[1]-18) <= 7)}
    tree |= hot
keep = tree & OLD; drop = OLD - tree; new = tree - OLD
print(json.dumps({'old': len(OLD), 'plan': len(tree), 'keep': len(keep), 'drop': len(drop), 'new': sorted(new), 'added': added, 'dropTraffic6h': sum(tr[p] for p in drop), 'keepTraffic6h': sum(tr[p] for p in keep)}))
print('DROP', sorted(drop)); print('DROPHOT', sorted((p, tr[p]) for p in drop if tr[p] >= 50))
if len(sys.argv) > 1 and sys.argv[1]:
    S = 14; im = Image.new('RGB', (50*S, 50*S+40), 'white'); d = ImageDraw.Draw(im)
    for y in range(50):
        for x in range(50): d.rectangle([x*S, y*S, x*S+S-1, y*S+S-1], fill=(40, 40, 40) if WALL(x, y) else ((150, 170, 120) if SW(x, y) else (225, 225, 215)))
    for o in obj:
        col = {'extension': (255, 200, 0), 'spawn': (255, 0, 255), 'tower': (220, 30, 30), 'storage': (0, 120, 0), 'container': (200, 120, 50), 'constructionSite': (255, 240, 150), 'source': (255, 255, 0), 'controller': (0, 0, 0), 'mineral': (120, 120, 255), 'link': (90, 90, 90), 'constructedWall': (100, 60, 30)}.get(o['type'])
        if col: d.rectangle([o['x']*S+3, o['y']*S+3, o['x']*S+S-4, o['y']*S+S-4], fill=col)
    for p, cl in [(keep, (0, 190, 0)), (drop, (230, 0, 0)), (new, (0, 90, 255))]:
        for x, y in p: d.rectangle([x*S+1, y*S+1, x*S+S-2, y*S+S-2], outline=cl, width=3)
    d.text((4, 50*S+4), 'W47N8 roads v4 (post spawn move): green keep %d, red decaying %d, blue newly planned %d' % (len(keep), len(drop), len(new)), fill='black')
    d.text((4, 50*S+20), 'yellow ext / light-yellow ext sites, magenta spawn 34,30, red tower, dark green storage; links: ' + json.dumps(added), fill='black')
    im.save(sys.argv[1])
if len(sys.argv) > 2:
    open(sys.argv[2], 'w').write('// GENERATED by tools/w47n8_roads_v4.py (10-20 post spawn move, Misaki 20:5x "abandon the old west-base roads").\n'
        '// Only these roads are placed/repaired; others decay naturally. Exit corridors (W46N8 east, W47N7 south), gate 29,3 and both\n'
        '// north wall segments are goals of the tree; tests/w47n8_roads_connected.js asserts them + ONE connected network.\n'
        'module.exports = ' + json.dumps({'MINERAL': MIN, 'ROADS': sorted([list(p) for p in tree])}, separators=(',', ':')) + ';\n')
