#!/usr/bin/env python3
"""Render metrics/live.json (websocket room snapshot) to metrics/room_live.png."""
import json, os
from PIL import Image, ImageDraw
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(f'{ROOT}/metrics/live.json')); T = open(f'{ROOT}/data/terrain_W46N8.txt').read()
S = 12; img = Image.new('RGB', (600, 620), (0, 0, 0)); g = ImageDraw.Draw(img)
for i, c in enumerate(T):
    g.rectangle([i % 50*S, i//50*S, i % 50*S+S-1, i//50*S+S-1], fill=(0, 0, 0) if c in '13' else (40, 56, 24) if c == '2' else (43, 43, 43))
COL = {'spawn': (255, 220, 0), 'extension': (238, 238, 238), 'tower': (255, 50, 50), 'road': (120, 120, 120), 'container': (170, 100, 50),
       'constructionSite': (0, 255, 0), 'source': (255, 255, 0), 'controller': (255, 255, 255), 'mineral': (0, 255, 255), 'rampart': (0, 160, 0)}
for o in d['objects'].values():
    if o.get('x') is None: continue
    c = (50, 200, 255) if o['type'] == 'creep' and o.get('user') == d.get('uid') else (255, 0, 255) if o['type'] == 'creep' else COL.get(o['type'], (200, 0, 200))
    p = 4 if o['type'] == 'road' else 2 if o['type'] in ('creep', 'constructionSite') else 1
    g.rectangle([o['x']*S+p, o['y']*S+p, o['x']*S+S-1-p, o['y']*S+S-1-p], fill=c)
s = d.get('stats') or {}
g.text((4, 603), f"tick {d.get('gameTime')}  {d.get('updated')} UTC+8  creeps {s.get('creeps')}  errors {s.get('nerr')}", fill=(255, 255, 255))
img.save(f'{ROOT}/metrics/room_live.png'); print(f'{ROOT}/metrics/room_live.png')
