"""Final (RCL8) base plan image for W46N8: layout v2 + link plan A + defense v6. Output docs/final_layout_rcl8.png."""
import json, os, collections
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L = json.loads(open(os.path.join(ROOT, 'src/layouts/W46N8.js')).read().split('=', 1)[1].strip().rstrip(';'))
TER = open(os.path.join(ROOT, 'data/terrain_W46N8.txt')).read().strip()
D = L['defense']
LIMIT8 = dict(container=5, spawn=3, extension=60, tower=6, link=6, storage=1, terminal=1, lab=10, factory=1, powerSpawn=1, nuker=1, observer=1, extractor=1)
S = 52; M = 70; W = 50 * S + 2 * M + 700; H = 50 * S + 2 * M + 60
F = lambda n: ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', n, index=2)  # SC
im = Image.new('RGB', (W, H), (18, 18, 22)); d = ImageDraw.Draw(im, 'RGBA')
TC = {'0': (92, 92, 84), '1': (30, 30, 30), '2': (54, 78, 40), '3': (30, 30, 30)}
def box(x, y, pad=0): X, Y = M + x * S, M + 40 + y * S; return [X + pad, Y + pad, X + S - 1 - pad, Y + S - 1 - pad]
def ctr(x, y): b = box(x, y); return ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
for i, ch in enumerate(TER[:2500]): x, y = i % 50, i // 50; d.rectangle(box(x, y), fill=TC.get(ch, (92, 92, 84)))
# structures by type (final), with RCL
st = {}
for r, lv in L['rcl'].items():
    for t, ps in lv.items():
        for x, y in ps:
            if t == 'rampart': continue
            st[(x, y)] = (t, int(r))
# link plan A (RCL5 hub 37,29, ctl 30,31; RCL6 srcA 30,11) replaces v2 RCL5 link 35,26
st.pop((35, 26), None)
for (x, y, r) in [(37, 29, 5), (30, 31, 5), (30, 11, 6)]: st[(x, y)] = ('link', r)
links = [k for k, v in st.items() if v[0] == 'link']
if len(links) < 6: st[(35, 26)] = ('link', 8)  # 6th link at RCL8 (v2 hub-adjacent slot)
for lv in L['remove'].values():  # planned removals (B container -> storage, A container once its link is up)
    for rm in lv: st.pop(tuple(rm['pos']), None)
roads = {tuple(p) for lv in L['rcl'].values() for p in lv.get('road', [])}
for rt in L['routes'].values(): roads |= {tuple(p) for p in rt}
trunk = set(); [trunk.update(map(tuple, t['path'])) for t in D['trunks'].values()]
spur = set(); [spur.update(map(tuple, v['spur'])) for v in D['repair'].values()]
roads |= trunk | spur
import sys
VARIANT = sys.argv[1] if len(sys.argv) > 1 else 'v6'
walls = {tuple(p) for p in D['walls_in_build_order']}
gates = {tuple(p) for g in D['gates'].values() for p in g}
if VARIANT == 'misaki':  # Misaki 10-15: outer W/SW chokepoints x=6 (y24-32), x=10 (y46-48), x=20 (y44-47) replace W/SW v6 segment
    old = {p for p in walls | gates if p[0] <= 23 and p[1] >= 26}
    walls -= old; gates -= old
    walls |= {(6, y) for y in range(24, 33) if y != 28} | {(10, y) for y in (46, 47, 48)} | {(20, y) for y in (44, 45, 46, 47)}
    gates |= {(6, 28)}
ramp_over = {tuple(p) for lv in L['rcl'].values() for p in lv.get('rampart', []) if tuple(p) in st}
stand = {tuple(p) for p in L['positions']['fillers']} | {tuple(L['positions']['manager'])}
repstand = {tuple(p) for v in D['repair'].values() for p in v['stand']}
# draw roads
for p in roads:
    if p in st and st[p][0] not in ('road', 'container'): continue
    c = (230, 210, 120) if p in spur and p not in trunk else (205, 205, 205); d.ellipse(box(*p, 18), fill=c)
COL = dict(spawn=(255, 215, 0), extension=(250, 250, 250), tower=(230, 40, 40), storage=(255, 140, 0), terminal=(170, 80, 255),
           link=(0, 200, 255), lab=(255, 90, 200), factory=(150, 110, 60), powerSpawn=(255, 60, 60), nuker=(120, 255, 120),
           observer=(80, 120, 255), extractor=(200, 200, 200), container=(140, 100, 60))
for p in walls: d.rectangle(box(*p, 1), fill=(105, 70, 40), outline=(60, 40, 20), width=3)
for p in gates: d.rectangle(box(*p, 1), fill=(0, 230, 200, 200), outline=(0, 120, 100), width=4)
for (x, y), (t, r) in st.items():
    if t == 'road': continue
    b = box(x, y, 6); c = COL.get(t, (255, 255, 255))
    if t == 'extension': d.ellipse(box(x, y, 12), fill=c, outline=(80, 80, 80), width=2)
    elif t == 'spawn': d.ellipse(box(x, y, 3), fill=c, outline=(120, 90, 0), width=4)
    elif t == 'tower': cx, cy = ctr(x, y); d.polygon([(cx, b[1]), (b[2], b[3]), (b[0], b[3])], fill=c, outline=(80, 0, 0))
    elif t == 'link': cx, cy = ctr(x, y); d.polygon([(cx, b[1]), (b[2], cy), (cx, b[3]), (b[0], cy)], fill=c, outline=(0, 60, 80))
    elif t == 'lab': d.ellipse(b, fill=c, outline=(90, 0, 60), width=3)
    elif t == 'container': d.rectangle(box(x, y, 10), fill=c, outline=(60, 40, 20), width=3)
    else: d.rectangle(b, fill=c, outline=(30, 30, 30), width=3)
    if t != 'extension': d.text((b[0] + 1, b[1] - 2), str(r), fill=(0, 0, 0), font=F(16))
    else: d.text((ctr(x, y)[0] - 5, ctr(x, y)[1] - 9), str(r), fill=(0, 0, 0), font=F(14))
for p in ramp_over: d.rectangle(box(*p, 2), outline=(40, 255, 80), width=5)
for p in stand: d.ellipse(box(*p, 19), outline=(255, 255, 0), width=3)
for p in repstand: cx, cy = ctr(*p); d.line([(cx - 14, cy - 14), (cx + 14, cy + 14)], fill=(255, 230, 0), width=5); d.line([(cx - 14, cy + 14), (cx + 14, cy - 14)], fill=(255, 230, 0), width=5)
for (x, y), lab in [((32, 11), '矿 A'), ((39, 33), '矿 B')]: d.ellipse(box(x, y, 4), fill=(255, 240, 60), outline=(120, 100, 0), width=4); d.text((box(x, y)[0] - 4, box(x, y)[1] - 22), lab, fill=(255, 240, 60), font=F(18))
d.rectangle(box(28, 32, 3), fill=(90, 90, 255), outline=(255, 255, 255), width=4); d.text((box(28, 32)[0] - 10, box(28, 32)[3] + 2), '控制器', fill=(170, 170, 255), font=F(18))
d.polygon([ctr(40, 24)[0:1] + (box(40, 24)[1] + 2,), (box(40, 24)[2] - 2, ctr(40, 24)[1]), (ctr(40, 24)[0], box(40, 24)[3] - 2), (box(40, 24)[0] + 2, ctr(40, 24)[1])], outline=(220, 220, 220), width=4)
# grid
for i in range(0, 51, 5):
    d.line([(M + i * S, M + 40), (M + i * S, M + 40 + 50 * S)], fill=(255, 255, 255, 70), width=2)
    d.line([(M, M + 40 + i * S), (M + 50 * S, M + 40 + i * S)], fill=(255, 255, 255, 70), width=2)
    if i < 50: d.text((M + i * S + 4, M + 14), str(i), fill=(220, 220, 220), font=F(22)); d.text((14, M + 40 + i * S + 4), str(i), fill=(220, 220, 220), font=F(22))
d.text((M, 12), ('W46N8（shard3）RCL8 最终布局：布局 v2 + link 方案 A + 防御 v6' + ('（Misaki 外移墙线方案）' if VARIANT == 'misaki' else '')), fill=(255, 255, 255), font=F(30))
cnt = collections.Counter(t for t, r in st.values() if t != 'road')
lx = M + 50 * S + 30; ly = M + 50
def leg(draw_fn, text):
    global ly; draw_fn(lx, ly); d.text((lx + 50, ly + 4), text, fill=(235, 235, 235), font=F(22)); ly += 46
def mk(t):
    def f(x, y):
        c = COL[t]
        if t in ('extension', 'spawn', 'lab'): d.ellipse([x, y, x + 34, y + 34], fill=c)
        elif t == 'tower': d.polygon([(x + 17, y), (x + 34, y + 34), (x, y + 34)], fill=c)
        elif t == 'link': d.polygon([(x + 17, y), (x + 34, y + 17), (x + 17, y + 34), (x, y + 17)], fill=c)
        else: d.rectangle([x, y, x + 34, y + 34], fill=c)
    return f
CN = dict(spawn='spawn', extension='扩展', tower='塔', storage='仓库', link='link', terminal='终端', lab='实验室', factory='工厂',
          powerSpawn='能量核心', nuker='核弹', observer='观察者', extractor='矿物提取器', container='容器')
rcls = collections.defaultdict(list)
for t, r in st.values(): rcls[t].append(r)
for t in ['spawn', 'extension', 'tower', 'storage', 'link', 'terminal', 'lab', 'factory', 'powerSpawn', 'nuker', 'observer', 'extractor', 'container']:
    lim = LIMIT8.get(t); n = cnt.get(t, 0)
    rs = ','.join(f'{r}:{c}' for r, c in sorted(collections.Counter(rcls[t]).items()))
    leg(mk(t), f"{CN[t]} {n}" + (f"/{lim}" if lim else '') + f"（等级:数量 {rs}）")
leg(lambda x, y: d.rectangle([x, y, x + 34, y + 34], fill=(105, 70, 40)), f'实心墙 {len(walls)}')
leg(lambda x, y: d.rectangle([x, y, x + 34, y + 34], fill=(0, 230, 200)), f'rampart 门 {len(gates)}')
leg(lambda x, y: d.rectangle([x, y, x + 34, y + 34], outline=(40, 255, 80), width=5), f'建筑上的 rampart {len(ramp_over)}')
leg(lambda x, y: d.ellipse([x + 8, y + 8, x + 26, y + 26], fill=(205, 205, 205)), f'道路/干道 {len(roads)}')
leg(lambda x, y: d.ellipse([x + 8, y + 8, x + 26, y + 26], fill=(230, 210, 120)), f'修墙支路 {len(spur - trunk)}')
leg(lambda x, y: (d.line([(x + 4, y + 4), (x + 30, y + 30)], fill=(255, 230, 0), width=5), d.line([(x + 4, y + 30), (x + 30, y + 4)], fill=(255, 230, 0), width=5)), f'修墙站位 {len(repstand)}')
leg(lambda x, y: d.ellipse([x + 4, y + 4, x + 30, y + 30], outline=(255, 255, 0), width=3), f'补能员/管理员站位（未来，不建 rampart）{len(stand)}')
leg(lambda x, y: d.ellipse([x, y, x + 34, y + 34], fill=(255, 240, 60)), '能量矿 2')
leg(lambda x, y: d.rectangle([x, y, x + 34, y + 34], fill=(90, 90, 255)), '控制器 (28,32)')
leg(lambda x, y: d.polygon([(x + 17, y), (x + 34, y + 17), (x + 17, y + 34), (x, y + 17)], outline=(220, 220, 220), width=4), '矿物 (40,24)')
ly += 10
for t, c in [('平地', TC['0']), ('沼泽', TC['2']), ('天然石壁', (30, 30, 30))]: leg(lambda x, y, c=c: d.rectangle([x, y, x + 34, y + 34], fill=c, outline=(120, 120, 120)), t)
d.text((lx, ly + 10), '格子上的数字 = 在第几级建造', fill=(200, 200, 200), font=F(20))
out = os.path.join(ROOT, 'docs', 'final_layout_rcl8.png' if VARIANT == 'v6' else 'final_layout_rcl8_misaki.png'); im.save(out); print(out, im.size, dict(cnt))
bad = {t: (cnt.get(t, 0), l) for t, l in LIMIT8.items() if cnt.get(t, 0) != l}; print('limit mismatch', bad)
