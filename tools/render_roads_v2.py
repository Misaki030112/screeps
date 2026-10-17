#!/usr/bin/env python3
"""Render roads v2 plan: out/roads_v2_W46N8.png, out/roads_v2_W45N8.png"""
import json
from PIL import Image, ImageDraw
S = 16
TR = {r: open(f'data/terrain_{r}.txt').read().strip() for r in ['W46N8', 'W45N8']}
L = json.load(open('metrics/live.json'))
roads = {(o['x'], o['y']) for o in L['objects'].values() if o.get('room') == 'W46N8' and o.get('type') == 'road'}
structs = {(o['x'], o['y']): o['type'] for o in L['objects'].values() if o.get('room') == 'W46N8' and o.get('type') not in ('road', 'creep', 'constructionSite', 'tombstone', 'energy', 'ruin', 'rampart')}
plan8 = [(x, y, t) for x, y, t in json.load(open('/tmp/planobs.json'))]
haul = [(38,30),(38,29),(38,28),(38,27),(38,26),(38,25),(39,24),(40,23),(41,22),(42,21),(43,20),(44,19),(45,18),(46,17),(47,16),(48,15),(49,14)]
leg = [(0,14),(1,13),(2,12),(3,11),(4,11),(5,11),(6,10),(7,9),(8,9),(9,9),(10,9),(11,9),(12,10)]
v1leg = [(4,10),(5,9),(6,8),(7,7),(8,7),(9,8),(10,8)]
rcl8alt = [(38,24),(37,23),(38,22),(39,21),(40,21)]
econ = [(35,26),(36,25),(34,25),(35,31)]
W = [(30,30),(29,31),(29,32),(28,33),(27,34),(26,34),(25,34),(24,34),(23,35),(22,35),(21,34),(20,33),(19,32),(18,31),(17,30),(16,29),(15,28),(14,27),(13,26),(12,25),(11,24),(10,24),(9,25),(8,26),(7,27),(6,28)]
Sx = [(22,36),(21,37),(20,38),(19,39),(18,40),(17,41),(18,42),(19,43),(20,44)]
COL = {'0': (232,226,205), '1': (40,40,40), '2': (110,160,60)}
def base(r):
    im = Image.new('RGB', (50*S, 50*S + 70), 'white'); d = ImageDraw.Draw(im)
    for y in range(50):
        for x in range(50): d.rectangle([x*S, y*S, x*S+S-1, y*S+S-1], fill=COL[TR[r][y*50+x]])
    return im, d
def cell(d, x, y, fill=None, outline=None, w=1, inset=0): d.rectangle([x*S+inset, y*S+inset, x*S+S-1-inset, y*S+S-1-inset], fill=fill, outline=outline, width=w)
def legend(d, items):
    x = 6
    for i, (c, t) in enumerate(items):
        yy = 50*S + 6 + (i // 4) * 20; xx = 6 + (i % 4) * 200
        d.rectangle([xx, yy, xx+14, yy+14], fill=c, outline='black'); d.text((xx+20, yy+2), t, fill='black')
im, d = base('W46N8')
for (x, y) in roads: cell(d, x, y, fill=(150,150,150), inset=3)
for x, y, t in plan8: cell(d, x, y, outline=(160,0,160), w=2)
for (x, y), t in structs.items(): cell(d, x, y, fill={'tower':(200,0,0),'storage':(255,200,0),'spawn':(0,120,255)}.get(t,(90,90,140)), inset=2)
for x, y in W + Sx: cell(d, x, y, outline=(120,120,255), w=3)
for x, y in rcl8alt: cell(d, x, y, outline=(255,140,0), w=2, inset=4)
for x, y in econ: cell(d, x, y, outline=(0,200,200), w=3)
for x, y in haul: cell(d, x, y, outline=(220,0,0), w=3)
d.text((5,5), 'W46N8 roads v2  (swamp=green, wall=black)', fill='white')
legend(d, [((220,0,0),'1 haul route (red)'),((0,200,200),'3 econ tiles'),((120,120,255),'4 W/S trunks (last/drop?)'),((150,150,150),'existing road'),
           ((255,140,0),'RCL8 detour (40,23 tower)'),((160,0,160),'planned RCL7-8 bldg'),((200,0,0),'tower'),((255,200,0),'storage')])
im.save('out/roads_v2_W46N8.png')
im, d = base('W45N8')
for x, y in v1leg: cell(d, x, y, outline=(80,80,80), w=2, inset=4)
for x, y in leg: cell(d, x, y, outline=(220,0,0), w=3)
cell(d, 13, 11, fill=(255,200,0), inset=2); cell(d, 14, 12, fill=(255,255,0), inset=1)
d.text((5,5), 'W45N8 haul leg v2 (all new tiles plain; 2,12 swamp already built)', fill='white')
legend(d, [((220,0,0),'2 W45N8 leg v2 (red)'),((80,80,80),'v1 rejected (2 new swamp)'),((255,200,0),'container 13,11'),((255,255,0),'source 14,12')])
im.save('out/roads_v2_W45N8.png')
