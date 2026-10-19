#!/usr/bin/env python3
"""W47N8 hub refill route (fill.js) -> /workspace/w47n8_refill_route.png, Chinese labels.
Inputs: /tmp/fill_geo.json (layout + routes, node dump), /tmp/fill_trace.json (FILL_TRACE=... node tests/w47n8_filler.js),
data/w47n8_fill_snapshot.json (live structures), data/terrain_W47N8.txt. Optional argv[1] = stats text (one line per '|')."""
import json, sys, os
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
G = json.load(open('/tmp/fill_geo.json')); TR = json.load(open('/tmp/fill_trace.json'))
SN = [r.split(' ') for r in json.load(open(os.path.join(ROOT, 'data/w47n8_fill_snapshot.json')))['s']]
T = open(os.path.join(ROOT, 'data/terrain_W47N8.txt')).read().strip()
X0, X1, Y0, Y1, S, M = 9, 43, 12, 44, 40, 40
W, H = (X1 - X0 + 1) * S + 2 * M + 430, (Y1 - Y0 + 1) * S + 2 * M + 30
FN = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
if not os.path.exists(FN): FN = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
f = lambda n: ImageFont.truetype(FN, n)
im = Image.new('RGB', (W, H), 'white'); d = ImageDraw.Draw(im)
px = lambda x, y: (M + (x - X0) * S, M + (y - Y0) * S)
ctr = lambda x, y: (M + (x - X0) * S + S // 2, M + (y - Y0) * S + S // 2)
def box(x, y, fill, out=None, inset=0, w=1):
    a, b = px(x, y); d.rectangle([a + inset, b + inset, a + S - inset, b + S - inset], fill=fill, outline=out, width=w)
for y in range(Y0, Y1 + 1):
    for x in range(X0, X1 + 1):
        t = int(T[y * 50 + x]); box(x, y, (40, 40, 40) if t & 1 else (190, 210, 160) if t & 2 else (236, 232, 222), (215, 210, 200))
live = {}
for t, x, y, *_ in SN: live.setdefault((int(x), int(y)), []).append(t)
inside = lambda x, y: X0 <= x <= X1 and Y0 <= y <= Y1
for (x, y), ts in live.items():
    if 'roa' in ts and inside(x, y): box(x, y, (170, 170, 170), None, 11)
# future v3b extensions (outline only)
liveExt = {k for k, ts in live.items() if 'ext' in ts}
for x, y in G['L']['ORDER']['extension']:
    if (x, y) not in liveExt and X0 <= x <= X1 and Y0 <= y <= Y1: box(x, y, None, (205, 170, 40), 7, 2)
COL = [(220, 60, 60), (40, 120, 220), (30, 160, 90), (150, 70, 200)]
NAME = ['B1 东条', 'B2 南条', 'B3 北条', 'B4 西北条']
# strip roads coloured, entry marked
for i, road in enumerate(G['routes']):
    for x, y in road: box(x, y, tuple(min(255, c + 150) for c in COL[i]), None, 6)
    e = road[-1] if G['entry'][i] else road[0]; a = ctr(*e); d.ellipse([a[0] - 8, a[1] - 8, a[0] + 8, a[1] + 8], outline=COL[i], width=4)
    s0, s1 = (road[-1], road[0]) if G['entry'][i] else (road[0], road[-1])
    d.line([ctr(*s0), ctr(*s1)], fill=COL[i], width=3)
    tip = ctr(*s1); dx, dy = (s1[0] - s0[0]), (s1[1] - s0[1]); n = max(abs(dx), abs(dy)) or 1; ux, uy = dx / n, dy / n
    d.polygon([(tip[0] + ux * 12, tip[1] + uy * 12), (tip[0] - uy * 9, tip[1] + ux * 9), (tip[0] + uy * 9, tip[1] - ux * 9)], fill=COL[i])
# live structures
temp = {tuple(p) for p in G['L']['TEMP_EXT']}
for (x, y), ts in live.items():
    if not (X0 <= x <= X1 and Y0 <= y <= Y1): continue
    if 'ext' in ts: box(x, y, (250, 150, 40) if (x, y) in temp else (250, 210, 40), (120, 90, 0), 6, 2)
    if 'spa' in ts: box(x, y, (230, 80, 160), (90, 0, 60), 3, 2)
    if 'tow' in ts: box(x, y, (120, 120, 230), (30, 30, 120), 4, 2)
    if 'sto' in ts: box(x, y, (60, 170, 200), (0, 60, 90), 2, 3)
    if 'con' in ts: box(x, y, (150, 110, 70), (70, 40, 10), 8, 2)
# post
a = ctr(*G['post']); d.regular_polygon((a[0], a[1], 13), 5, fill=(0, 90, 255), outline='white')
# simulated full refill path (750 energy, from the trace with n=800)
tr = [t for t in TR['traces'] if t['n'] == 800][0]['tr']
pts = [ctr(p[0], p[1]) for p in tr]
for k in range(1, len(pts)):
    o = 3 if k % 2 else -3
    d.line([(pts[k - 1][0] + o, pts[k - 1][1] + o), (pts[k][0] + o, pts[k][1] + o)], fill=(0, 0, 0), width=2)
for k, p in enumerate(tr):
    if k and tr[k][3] > (tr[k - 1][3] if len(tr[k - 1]) > 3 else 0):
        c = ctr(tr[k - 1][0], tr[k - 1][1]); d.ellipse([c[0] - 4, c[1] - 4, c[0] + 4, c[1] + 4], fill=(0, 0, 0))
# labels
def lab(x, y, s, c=(0, 0, 0), n=15):
    p = px(x, y); bb = d.textbbox(p, s, font=f(n)); d.rectangle([bb[0] - 3, bb[1] - 2, bb[2] + 3, bb[3] + 2], fill=(255, 255, 255), outline=c)
    d.text(p, s, fill=c, font=f(n))
lab(39.6, 38.5, 'B1 东条', COL[0], 17); lab(39.6, 39.3, '北口 38,30 进', COL[0], 14); lab(39.6, 40.0, '向南扫', COL[0], 14)
lab(21.0, 37.3, 'B2 南条：东口 32,35 进，向西扫', COL[1], 17)
lab(33.2, 24.0, 'B3 北条：南口 31,28 进，向北扫', COL[2], 17)
lab(18.5, 22.2, 'B4 西北条：东口 28,25 进，向西扫', COL[3], 17)
lab(39.8, 28.4, '待命点 34,32（满载等候）', (0, 60, 200), 15)
lab(39.8, 29.2, 'storage 35,32', (0, 60, 90), 14); lab(26.0, 33.0, '中心容器 33,33', (70, 40, 10), 14)
lab(19.2, 17.2, 'Spawn2 15,18 + 5 个临时扩展：搬运工负责', (180, 70, 0), 15)
lab(19.2, 17.9, '（filler 只在 spawn 等能量且中心全满时去）', (180, 70, 0), 13)
lab(26.0, 31.0, '中心扩展 32,31（定点补）', (120, 90, 0), 14)
# legend
LX = M + (X1 - X0 + 1) * S + 18; ly = M
d.text((LX, ly), 'W47N8 补能路线（v3b 条带）', fill='black', font=f(22)); ly += 36
items = [((250, 210, 40), '已建中心扩展（filler 负责）'), ((250, 150, 40), '临时扩展（搬运工负责）'), (None, '规划中扩展（未建，虚框）'),
         ((230, 80, 160), 'Spawn'), ((120, 120, 230), '塔（spawn 能量满后顺路补）'), ((60, 170, 200), 'storage（filler 的能量来源）'),
         ((150, 110, 70), '容器'), ((170, 170, 170), '道路'), ((40, 40, 40), '墙'), ((190, 210, 160), '沼泽')]
for col, s in items:
    if col: d.rectangle([LX, ly, LX + 22, ly + 22], fill=col, outline='black')
    else: d.rectangle([LX + 3, ly + 3, LX + 19, ly + 19], outline=(205, 170, 40), width=2)
    d.text((LX + 32, ly), s, fill='black', font=f(15)); ly += 28
d.regular_polygon((LX + 11, ly + 11, 11), 5, fill=(0, 90, 255)); d.text((LX + 32, ly), '待命点：满载停在 storage 旁', fill='black', font=f(15)); ly += 28
for i in range(4):
    d.line([(LX, ly + 11), (LX + 22, ly + 11)], fill=COL[i], width=4); d.ellipse([LX - 4, ly + 4, LX + 10, ly + 18], outline=COL[i], width=3)
    d.text((LX + 32, ly), NAME[i] + '：圆圈=入口，箭头=扫的方向', fill='black', font=f(15)); ly += 28
d.line([(LX, ly + 11), (LX + 22, ly + 11)], fill='black', width=2); d.ellipse([LX + 7, ly + 7, LX + 15, ly + 15], fill='black')
d.text((LX + 32, ly), '模拟：750 能量全空→补满的路线', fill='black', font=f(15)); ly += 22
d.text((LX + 32, ly), '黑点 = 这一格做了一次补能', fill='black', font=f(15)); ly += 40
rules = ['规则：', '1. spawn 一用能量，filler 立刻出发（满载待命）', '2. 走条带中间的路，每 tick 给旁边一个扩展补能，',
         '   同时往前走一格（补能和移动同一 tick）', '3. 只在「再走就够不着」的扩展没补满时停一下',
         '4. 走到最远一个空扩展就折返；身后又被用掉的，', '   回程顺手补', '5. 先补离自己最近的条带；没能量就回 storage 补满',
         '6. Spawn2 那 6 个结构由搬运工补（离矿近）']
for s in rules: d.text((LX, ly), s, fill='black', font=f(15)); ly += 24
ly += 12
for s in (sys.argv[1].split('|') if len(sys.argv) > 1 else []): d.text((LX, ly), s, fill=(150, 0, 0), font=f(15)); ly += 24
gx = M
for x in range(X0, X1 + 1, 2): d.text((M + (x - X0) * S + 8, M - 20), str(x), fill='gray', font=f(12))
for y in range(Y0, Y1 + 1, 2): d.text((6, M + (y - Y0) * S + 8), str(y), fill='gray', font=f(12))
im.save('/workspace/w47n8_refill_route.png'); print('saved', im.size)
