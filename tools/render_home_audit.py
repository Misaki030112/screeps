#!/usr/bin/env python3
"""out/home_layout_audit.png: W46N8 core (x26-41,y19-38) live structures; magenta = v5 new road tiles (site/built), numbers = queen stops."""
import sys; sys.path.insert(0, 'tools'); from q import q; from ring_check import T
from PIL import Image, ImageDraw
v = q("(function(){const r=Game.rooms.W46N8;return {S:r.find(FIND_STRUCTURES).filter(s=>s.pos.x>=26&&s.pos.x<=41&&s.pos.y>=19&&s.pos.y<=38).map(s=>[s.structureType,s.pos.x,s.pos.y]),C:r.find(FIND_MY_CONSTRUCTION_SITES).map(s=>[s.structureType,s.pos.x,s.pos.y])}})()")['v']
X0, Y0, Z = 26, 19, 40; im = Image.new('RGB', (16*Z, 20*Z+30), 'black'); d = ImageDraw.Draw(im)
COL = {'extension': (240,200,0), 'spawn': (255,255,255), 'storage': (255,140,0), 'container': (150,90,30), 'link': (0,150,255), 'tower': (255,0,0), 'controller': (200,200,255)}
NEW = {(31,26),(30,27),(31,28),(32,34),(35,29),(41,24)}; STOPS = [(34,25),(34,27),(36,25),(36,27),(33,33),(31,33),(33,35),(31,35),(31,26),(36,30)]
for y in range(Y0, Y0+20):
    for x in range(X0, X0+16):
        c = T[y*50+x]; d.rectangle([(x-X0)*Z, (y-Y0)*Z, (x-X0)*Z+Z-1, (y-Y0)*Z+Z-1], fill=(20,20,20) if c in '13' else (60,75,40) if c == '2' else (100,100,100), outline=(40,40,40))
for k, x, y in v['S']:
    if k == 'road': d.rectangle([(x-X0)*Z+12, (y-Y0)*Z+12, (x-X0)*Z+Z-13, (y-Y0)*Z+Z-13], fill=(255,0,255) if (x, y) in NEW else (190,180,150))
for k, x, y in v['S']:
    if k in COL: d.rectangle([(x-X0)*Z+4, (y-Y0)*Z+4, (x-X0)*Z+Z-5, (y-Y0)*Z+Z-5], outline=COL[k], width=3); d.text(((x-X0)*Z+6, (y-Y0)*Z+6), k[:2], fill=COL[k])
for k, x, y in v['C']:
    if X0 <= x < X0+16 and Y0 <= y < Y0+20: d.rectangle([(x-X0)*Z+10, (y-Y0)*Z+10, (x-X0)*Z+Z-11, (y-Y0)*Z+Z-11], outline=(255,0,255) if (x,y) in NEW else (255,255,0), width=2)
for i, (x, y) in enumerate(STOPS): d.text(((x-X0)*Z+26, (y-Y0)*Z+24), str(i+1), fill=(0,255,0))
d.text((5, 20*Z+8), "W46N8 core audit: magenta = v5 new roads (outline=site), green n = queen stop, tan = road", fill='white')
im.save('out/home_layout_audit.png'); print('ok', sum((x,y) in NEW for k,x,y in v['C']), 'new road sites')
