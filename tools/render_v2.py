#!/usr/bin/env python3
import pickle, json, os, sys
from PIL import Image, ImageDraw
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
res = pickle.load(open('/tmp/v2_res.pkl', 'rb')); T = open(f'{ROOT}/data/terrain_W46N8.txt').read()
occ = res['occ']
S = 20
RAMPS = set()
COL = {'spawn': (255, 215, 0), 'extension': (235, 235, 235), 'tower': (230, 40, 40), 'storage': (255, 150, 0), 'terminal': (0, 200, 200),
       'link': (90, 110, 255), 'container': (150, 95, 45), 'lab': (190, 70, 250), 'factory': (90, 190, 90), 'powerSpawn': (255, 0, 120),
       'nuker': (110, 110, 110), 'observer': (0, 255, 170), 'extractor': (200, 200, 0), 'road': (140, 140, 140)}
def draw(structs, roads, title, fname, creeps=True, routes=None, scale=S, label=True):
    img = Image.new('RGB', (50*scale, 50*scale + (110 if label else 22)), (15, 15, 15)); d = ImageDraw.Draw(img)
    for i, c in enumerate(T):
        x, y = i % 50, i // 50
        d.rectangle([x*scale, y*scale, x*scale+scale-1, y*scale+scale-1], fill=(0, 0, 0) if c in '13' else (38, 54, 22) if c == '2' else (48, 48, 48))
    for p in roads: d.rectangle([p[0]*scale+scale//3, p[1]*scale+scale//3, p[0]*scale+scale-1-scale//3, p[1]*scale+scale-1-scale//3], fill=COL['road'])
    if routes:
        for n, pts in routes.items():
            for a, b in zip(pts, pts[1:]): d.line([a[0]*scale+scale//2, a[1]*scale+scale//2, b[0]*scale+scale//2, b[1]*scale+scale//2], fill=(255, 200, 60), width=2)
    for (x, y), (t, r) in structs.items():
        if t == 'road': continue
        d.rectangle([x*scale+2, y*scale+2, x*scale+scale-3, y*scale+scale-3], fill=COL[t])
        if label and scale >= 16: d.text((x*scale+5, y*scale+4), str(r), fill=(0, 0, 0))
    for p in RAMPS: d.rectangle([p[0]*scale, p[1]*scale, p[0]*scale+scale-1, p[1]*scale+scale-1], outline=(0, 200, 0), width=2)
    if creeps:
        for p, t in creeps.items():
            col = {'F': (0, 220, 255), 'M': (255, 60, 255), 'U': (60, 255, 60), 'Mi': (255, 255, 0)}[t]
            d.ellipse([p[0]*scale+3, p[1]*scale+3, p[0]*scale+scale-4, p[1]*scale+scale-4], outline=col, width=3)
    for s in [(32, 11), (39, 33)]: d.ellipse([s[0]*scale+2, s[1]*scale+2, s[0]*scale+scale-3, s[1]*scale+scale-3], fill=(255, 255, 0))
    d.rectangle([28*scale, 32*scale, 28*scale+scale-1, 32*scale+scale-1], outline=(255, 255, 255), width=3)
    d.polygon([(40*scale+scale//2, 24*scale), (41*scale, 25*scale), (40*scale, 25*scale)], fill=(0, 255, 255))
    y0 = 50*scale + 4; d.text((6, y0), title, fill=(255, 255, 255))
    if label:
        x = 6; y = y0 + 18
        for t, c in COL.items():
            d.rectangle([x, y, x+12, y+12], fill=c); d.text((x+16, y), t, fill=(255, 255, 255)); x += 30 + 7*len(t)
            if x > 50*scale - 120: x = 6; y += 18
        y += 20
        for t, c, n in [('F', (0, 220, 255), 'filler (stationary)'), ('M', (255, 60, 255), 'hub manager'), ('U', (60, 255, 60), 'upgrader spot'), ('Mi', (255, 255, 0), 'miner spot')]:
            d.ellipse([x, y, x+12, y+12], outline=c, width=3); d.text((x+16, y), n, fill=(255, 255, 255)); x += 30 + 7*len(n)
        d.text((6, y + 20), 'number = RCL built; yellow line = hauler/traffic routes; white square = controller; yellow dot = source; cyan = mineral', fill=(200, 200, 200))
    img.save(fname); return img
if __name__ == '__main__':
    plan = json.load(open(f'{ROOT}/data/layout_W46N8_v2.json'))
    structs = {}; roads = set(); ramps = set()
    for r, lv in plan['rcl'].items():
        for t, lst in lv.items():
            for p in lst:
                if t == 'road': roads.add(tuple(p))
                elif t == 'rampart': ramps.add(tuple(p))
                else: structs[tuple(p)] = (t, int(r))
    RAMPS.update(ramps)
    creeps = {tuple(p): 'F' for p in plan['positions']['fillers']}
    creeps[tuple(plan['positions']['manager'])] = 'M'
    for p in plan['positions']['upgraders']: creeps[tuple(p)] = 'U'
    for p in plan['positions']['miners']: creeps[tuple(p)] = 'Mi'
    routes = {k: [tuple(p) for p in v] for k, v in plan['routes'].items()}
    draw(structs, roads, 'W46N8 layout v2 (final RCL8) — hub + 3 fast-filler stamps + link economy', f'{ROOT}/docs/layout_W46N8_v2.png', creeps, routes)
    # per-RCL strip
    tiles = []
    for R in range(1, 9):
        RAMPS.clear(); RAMPS.update(tuple(p) for r, lv in plan['rcl'].items() if int(r) <= R for p in lv.get('rampart', []))
        st = {p: v for p, v in structs.items() if v[1] <= R}
        rd = {tuple(p) for r, lv in plan['rcl'].items() if int(r) <= R for p in lv.get('road', [])}
        tiles.append(draw(st, rd, f'RCL{R}', f'/tmp/rcl{R}.png', None, None, scale=8, label=False).crop((18*8, 8*8, 46*8, 42*8)))
    w, h = tiles[0].size; strip = Image.new('RGB', (w*4 + 30, h*2 + 40), (15, 15, 15)); dd = ImageDraw.Draw(strip)
    for i, t in enumerate(tiles):
        strip.paste(t, ((i % 4) * (w + 10), (i // 4) * (h + 20) + 16)); dd.text(((i % 4) * (w + 10) + 4, (i // 4) * (h + 20) + 2), f'RCL{i+1}', fill=(255, 255, 255))
    strip.save(f'{ROOT}/docs/layout_W46N8_v2_rcl.png')
