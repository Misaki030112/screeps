#!/usr/bin/env python3
"""out/walls_ring.png: W46N8 enclosure status (live via console). green=built wall, cyan=gate rampart(hits), yellow=site, red=missing."""
import json, sys, os
sys.path.insert(0, 'tools'); from q import q; from ring_check import T, gates, walls, flood
from PIL import Image, ImageDraw
v = q("(function(){const r=Game.rooms.W46N8;return {S:r.find(FIND_STRUCTURES).filter(s=>s.structureType=='constructedWall'||s.structureType=='rampart'||s.structureType=='road'||s.structureType=='spawn'||s.structureType=='storage').map(s=>[s.structureType,s.pos.x,s.pos.y,s.hits]),C:r.find(FIND_MY_CONSTRUCTION_SITES).map(s=>[s.structureType,s.pos.x,s.pos.y])}})()")
t = v['t']; v = v['v']; Z = 16; im = Image.new('RGB', (50*Z, 50*Z+40), 'black'); d = ImageDraw.Draw(im)
for y in range(50):
    for x in range(50):
        c = T[y*50+x]; d.rectangle([x*Z, y*Z, x*Z+Z-1, y*Z+Z-1], fill=(20,20,20) if c in '13' else (60,75,40) if c == '2' else (110,110,110))
S = {(x, y): (k, h) for k, x, y, h in v['S']}; C = {(x, y) for k, x, y in v['C']}
for (x, y), (k, h) in S.items():
    if k == 'road': d.rectangle([x*Z+5, y*Z+5, x*Z+Z-6, y*Z+Z-6], fill=(160,150,120))
    if k in ('spawn', 'storage'): d.rectangle([x*Z+2, y*Z+2, x*Z+Z-3, y*Z+Z-3], fill=(255,255,255))
built = set(); n = {'built': 0, 'site': 0, 'missing': 0}
for (x, y) in walls + gates:
    want = 'rampart' if (x, y) in gates else 'constructedWall'; s = S.get((x, y))
    if s and s[0] == want: col = (0,200,255) if want == 'rampart' else (0,220,0); built.add((x, y)); n['built'] += 1
    elif (x, y) in C: col = (255,220,0); n['site'] += 1
    else: col = (230,0,0); n['missing'] += 1
    d.rectangle([x*Z+1, y*Z+1, x*Z+Z-2, y*Z+Z-2], fill=col)
    if want == 'rampart' and s: d.text((x*Z+Z, y*Z), f"{s[1]//1000}k", fill='white')
sealed = (37, 31) not in flood(built)
d.text((5, 50*Z+5), f"W46N8 ring t={t}  built {n['built']}/47  sites {n['site']}  missing {n['missing']}  sealed={sealed}   green wall / cyan gate / yellow site / red missing", fill='white')
os.makedirs('out', exist_ok=True); im.save('out/walls_ring.png'); print(n, 'sealed', sealed, 't', t)
