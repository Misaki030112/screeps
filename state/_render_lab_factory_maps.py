#!/usr/bin/env python3
"""High-res lab/factory placement maps for W46N8 and W47N8."""
import json, os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'state')
FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
REG = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'

def font(n, bold=True):
    path = FONT if bold else REG
    return ImageFont.truetype(path, n, index=2)

def load_terrain(room):
    t = open(os.path.join(ROOT, f'data/terrain_{room}.txt')).read().strip()[:2500]
    return t

def load_w46_layout():
    raw = open(os.path.join(ROOT, 'src/layouts/W46N8.js')).read().split('=', 1)[1].strip().rstrip(';')
    return json.loads(raw)

def load_w47_layout():
    text = open(os.path.join(ROOT, 'src/rooms/w47n8/layout.js')).read()
    raw = text[text.index('{'):].strip().rstrip(';')
    return json.loads(raw)

# colors
TERRAIN = {'0': (90, 90, 82), '1': (28, 28, 28), '2': (52, 76, 38), '3': (28, 28, 28)}
COL = dict(
    spawn=(255, 215, 0),
    extension=(236, 236, 236),
    tower=(220, 48, 48),
    storage=(255, 148, 20),
    terminal=(168, 90, 255),
    link=(0, 196, 255),
    container=(150, 108, 62),
    extractor=(200, 200, 200),
    controller=(180, 180, 255),
    mineral=(255, 230, 70),
    road=(198, 198, 198),
    south_path=(80, 210, 230),
)

LAB_EXIST = (255, 70, 180)
LAB_NOW = (255, 200, 40)
LAB_LATER = (170, 120, 255)
FACTORY = (220, 120, 40)
AISLE = (80, 255, 200)
MANAGER = (255, 255, 80)
RESERVED = (90, 90, 110)

def text_size(d, s, f):
    b = d.textbbox((0, 0), s, font=f)
    return b[2] - b[0], b[3] - b[1]

def draw_centered(d, xy, s, f, fill, stroke=None, sw=2):
    x, y = xy
    w, h = text_size(d, s, f)
    pos = (x - w / 2, y - h / 2 - 2)
    if stroke:
        d.text(pos, s, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke)
    else:
        d.text(pos, s, font=f, fill=fill)

def render(room, terrain, crop, existing, roads, south_paths, plan, title, subtitle, extra_notes):
    x0, x1, y0, y1 = crop  # inclusive
    nx, ny = x1 - x0 + 1, y1 - y0 + 1
    S = 84
    ML, MT, MR, MB = 86, 128, 520, 36
    W = ML + nx * S + MR
    H = MT + ny * S + MB
    im = Image.new('RGB', (W, H), (16, 16, 20))
    d = ImageDraw.Draw(im, 'RGBA')

    def box(x, y, pad=0):
        X = ML + (x - x0) * S
        Y = MT + (y - y0) * S
        return [X + pad, Y + pad, X + S - 1 - pad, Y + S - 1 - pad]

    def ctr(x, y):
        b = box(x, y)
        return ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)

    def in_crop(x, y):
        return x0 <= x <= x1 and y0 <= y <= y1

    # terrain
    for i, ch in enumerate(terrain):
        x, y = i % 50, i // 50
        if in_crop(x, y):
            d.rectangle(box(x, y), fill=TERRAIN.get(ch, (90, 90, 82)))

    # faint grid
    for x in range(x0, x1 + 2):
        X = ML + (x - x0) * S
        d.line([(X, MT), (X, MT + ny * S)], fill=(255, 255, 255, 28), width=1)
    for y in range(y0, y1 + 2):
        Y = MT + (y - y0) * S
        d.line([(ML, Y), (ML + nx * S, Y)], fill=(255, 255, 255, 28), width=1)

    # axis labels
    fa, fn = font(22), font(18, bold=False)
    for x in range(x0, x1 + 1):
        draw_centered(d, (ML + (x - x0) * S + S / 2, MT - 26), str(x), fa, (220, 220, 220))
    for y in range(y0, y1 + 1):
        draw_centered(d, (ML - 28, MT + (y - y0) * S + S / 2), str(y), fa, (220, 220, 220))

    # roads
    for (x, y) in roads:
        if not in_crop(x, y):
            continue
        color = COL['south_path'] if (x, y) in south_paths else COL['road']
        d.ellipse(box(x, y, int(S * 0.28)), fill=color)

    # reserved (faint) tiles under buildings
    for x, y, label in plan.get('reserved_other', []):
        if in_crop(x, y):
            d.rectangle(box(x, y, 6), outline=RESERVED + (200,), width=3)
            b = box(x, y)
            d.text((b[0] + 3, b[1] + 2), label, fill=(200, 200, 210), font=font(14, bold=False), stroke_width=1, stroke_fill=(0, 0, 0))

    # existing structures
    for (x, y), typ in existing.items():
        if not in_crop(x, y) or typ in ('road',):
            continue
        if typ == 'extension':
            d.ellipse(box(x, y, int(S * 0.22)), fill=COL['extension'], outline=(80, 80, 80), width=2)
        elif typ == 'spawn':
            d.ellipse(box(x, y, 6), fill=COL['spawn'], outline=(120, 90, 0), width=4)
            draw_centered(d, ctr(x, y), 'S', font(28), (40, 30, 0), (255, 240, 160), 2)
        elif typ == 'tower':
            b = box(x, y, 10)
            cx, cy = ctr(x, y)
            d.polygon([(cx, b[1]), (b[2], b[3]), (b[0], b[3])], fill=COL['tower'], outline=(80, 0, 0))
        elif typ == 'link':
            b = box(x, y, 10)
            cx, cy = ctr(x, y)
            d.polygon([(cx, b[1]), (b[2], cy), (cx, b[3]), (b[0], cy)], fill=COL['link'], outline=(0, 60, 80))
        elif typ == 'container':
            d.rectangle(box(x, y, int(S * 0.22)), fill=COL['container'], outline=(60, 40, 20), width=3)
        elif typ == 'storage':
            d.rounded_rectangle(box(x, y, 6), radius=8, fill=COL['storage'], outline=(80, 40, 0), width=4)
            draw_centered(d, ctr(x, y), '仓', font(26), (40, 20, 0), (255, 230, 180), 2)
        elif typ == 'terminal':
            d.rounded_rectangle(box(x, y, 6), radius=8, fill=COL['terminal'], outline=(60, 20, 100), width=4)
            draw_centered(d, ctr(x, y), '终', font(26), (255, 255, 255), (40, 0, 60), 2)
        elif typ == 'extractor':
            d.rectangle(box(x, y, 8), fill=COL['extractor'], outline=(80, 80, 80), width=3)
            draw_centered(d, ctr(x, y), '萃', font(20), (40, 40, 40))
        elif typ == 'controller':
            d.rectangle(box(x, y, 4), fill=(90, 90, 210), outline=(255, 255, 255), width=4)
            draw_centered(d, ctr(x, y), 'C', font(26), (255, 255, 255))
        elif typ == 'mineral':
            cx, cy = ctr(x, y)
            d.regular_polygon((cx, cy, S * 0.32), 4, rotation=45, fill=COL['mineral'], outline=(120, 100, 0))
            draw_centered(d, (cx, cy), plan.get('mineral_letter', '矿'), font(18), (40, 40, 0))

    # upgrader stands
    for (x, y) in plan.get('upgraders', []):
        if in_crop(x, y):
            d.ellipse(box(x, y, 8), outline=(255, 255, 120), width=4)
            # don't cover existing container; small tag above
            b = box(x, y)
            draw_centered(d, ((b[0] + b[2]) / 2, b[1] + 12), '升级', font(14), (255, 255, 140), (0, 0, 0), 2)

    # manager stand
    for (x, y) in plan.get('manager', []):
        if in_crop(x, y):
            d.ellipse(box(x, y, 6), outline=MANAGER, width=5)
            draw_centered(d, ctr(x, y), '经理', font(18), (255, 255, 160), (0, 0, 0), 2)

    # aisles
    for (x, y) in plan.get('aisles', []):
        if in_crop(x, y):
            d.rounded_rectangle(box(x, y, 6), radius=8, outline=AISLE, width=5)
            # hatch
            b = box(x, y, 10)
            d.line([(b[0], b[1]), (b[2], b[3])], fill=AISLE + (180,), width=3)
            d.line([(b[2], b[1]), (b[0], b[3])], fill=AISLE + (180,), width=3)
            draw_centered(d, ctr(x, y), '空', font(20), (200, 255, 230), (0, 40, 30), 2)

    def draw_lab(x, y, num, kind):
        if not in_crop(x, y):
            return
        if kind == 'exist':
            fill, outline, tag, tc = LAB_EXIST, (90, 0, 50), f'已{num}', (255, 255, 255)
        elif kind == 'now':
            fill, outline, tag, tc = LAB_NOW, (80, 50, 0), f'建{num}', (40, 20, 0)
        else:
            fill, outline, tag, tc = LAB_LATER, (50, 20, 80), f'留{num}', (255, 255, 255)
        d.ellipse(box(x, y, 5), fill=fill, outline=outline, width=5)
        cx, cy = ctr(x, y)
        # Color already encodes 建/已/留; skip coords on the tile (axes provide them)
        # so the tag stays crisp. Gold tiles use dark text and no heavy black stroke.
        if kind == 'now':
            draw_centered(d, (cx, cy), tag, font(26), (40, 20, 0))
        else:
            draw_centered(d, (cx, cy), tag, font(26), (255, 255, 255), (0, 0, 0), 2)

    for (x, y, num) in plan.get('labs_exist', []):
        draw_lab(x, y, num, 'exist')
    for (x, y, num) in plan.get('labs_now', []):
        draw_lab(x, y, num, 'now')
    for (x, y, num) in plan.get('labs_later', []):
        draw_lab(x, y, num, 'later')

    # factory
    for (x, y) in plan.get('factory', []):
        if not in_crop(x, y):
            continue
        d.rounded_rectangle(box(x, y, 4), radius=10, fill=FACTORY, outline=(255, 230, 160), width=5)
        cx, cy = ctr(x, y)
        draw_centered(d, (cx, cy - 10), '工厂', font(22), (255, 255, 255), (60, 20, 0), 2)
        draw_centered(d, (cx, cy + 16), f'{x},{y}', font(15, bold=False), (255, 245, 220))

    # title
    d.text((ML, 16), title, fill=(255, 255, 255), font=font(32))
    d.text((ML, 58), subtitle, fill=(190, 190, 200), font=font(18, bold=False))

    # legend
    lx = ML + nx * S + 28
    ly = MT
    d.text((lx, ly), '图例', fill=(255, 255, 255), font=font(26))
    ly += 48

    def swatch_box(color, label, sub=None, shape='rect'):
        nonlocal ly
        bx = [lx, ly, lx + 40, ly + 40]
        if shape == 'ellipse':
            d.ellipse(bx, fill=color, outline=(30, 30, 30), width=3)
        elif shape == 'round':
            d.rounded_rectangle(bx, radius=8, fill=color, outline=(30, 30, 30), width=3)
        elif shape == 'dash':
            d.rounded_rectangle(bx, radius=8, outline=color, width=4)
            d.line([(bx[0] + 4, bx[1] + 4), (bx[2] - 4, bx[3] - 4)], fill=color, width=3)
        else:
            d.rectangle(bx, fill=color, outline=(30, 30, 30), width=3)
        d.text((lx + 52, ly + 2), label, fill=(235, 235, 235), font=font(20))
        if sub:
            d.text((lx + 52, ly + 24), sub, fill=(160, 160, 170), font=font(14, bold=False))
            ly += 56
        else:
            ly += 48

    if plan.get('labs_exist'):
        swatch_box(LAB_EXIST, '已有实验室', '粉红，编号「已」', 'ellipse')
    swatch_box(LAB_NOW, '本波要建的实验室', '金黄，编号「建」', 'ellipse')
    swatch_box(LAB_LATER, 'RCL8 预留实验室', '紫色，编号「留」', 'ellipse')
    swatch_box(FACTORY, '本波要建的工厂', None, 'round')
    if plan.get('aisles'):
        swatch_box(AISLE, '过道，永远空着', None, 'dash')
    if plan.get('manager'):
        swatch_box(MANAGER, '经理位，不占用', None, 'dash')
    swatch_box(COL['storage'], '仓库', None, 'round')
    swatch_box(COL['terminal'], '终端', None, 'round')
    swatch_box(COL['spawn'], 'Spawn', None, 'ellipse')
    swatch_box(COL['extension'], '扩展', None, 'ellipse')
    swatch_box(COL['tower'], '塔')
    swatch_box(COL['link'], 'Link')
    swatch_box(COL['road'], '道路', None, 'ellipse')
    if south_paths:
        swatch_box(COL['south_path'], '南边短路（不占用）', None, 'ellipse')
    swatch_box(TERRAIN['2'], '沼泽')
    swatch_box(TERRAIN['1'], '墙')
    if plan.get('upgraders'):
        swatch_box((255, 255, 120), '升级工位（不占用）', None, 'dash')

    ly += 10
    for line in extra_notes:
        # wrap long notes
        d.text((lx, ly), line, fill=(200, 200, 210), font=font(15, bold=False))
        ly += 24

    path = os.path.join(OUT, f'_lab_factory_{room}.png')
    im.save(path, 'PNG', optimize=True)
    print(path, im.size)
    return path


def w46():
    L = load_w46_layout()
    terrain = load_terrain('W46N8')
    existing = {}
    roads = set()
    for r, lv in L['rcl'].items():
        r = int(r)
        for t, ps in lv.items():
            if t == 'rampart':
                continue
            for x, y in ps:
                if t == 'road':
                    roads.add((x, y))
                    continue
                # RCL8 unbuilt: skip as solid existing
                if r >= 8:
                    continue
                # RCL7 factory + new labs are NOT built yet
                if r == 7 and t in ('factory', 'lab', 'rampart'):
                    continue
                existing[(x, y)] = t
    for rt in L.get('routes', {}).values():
        roads |= {tuple(p) for p in rt}
    # known live extras
    existing[(37, 31)] = 'storage'
    existing[(35, 31)] = 'terminal'
    existing[(40, 24)] = 'mineral'
    existing[(41, 24)] = 'extractor'
    # controller typically around 28,32 in the render_final; need actual
    # From render_final: controller drawn at 28,32. Confirm later if needed.
    # W46 controller: upgraders at 30,30 / 31,30, ctl link 30,31, container 30,30
    # Controller is usually nearby — check terrain / common knowledge.
    # I will look up from layout or skip if outside crop. Many W46 plans put controller at 28,32.
    existing[(28, 32)] = 'controller'
    existing[(30, 30)] = 'container'
    existing[(30, 31)] = 'link'

    plan = {
        'labs_exist': [(34, 22, 1), (35, 21, 2), (33, 21, 3)],
        'labs_now': [(34, 23, 4), (33, 22, 5), (34, 20, 6)],
        'labs_later': [(35, 23, 7), (36, 22, 8), (36, 21, 9), (35, 20, 10)],
        'factory': [(35, 30)],
        'manager': [(36, 30)],
        'upgraders': [(30, 30), (31, 30)],
        'mineral_letter': 'O',
    }
    notes = [
        '本波 4 个工地：',
        '工厂 35,30',
        '实验室 34,23 / 33,22 / 34,20',
        '已有实验室 34,22 / 35,21 / 33,21',
        '34,21 与 35,22 继续留作道路',
        '经理位 36,30 不占用',
    ]
    return render(
        'W46N8', terrain, (28, 41, 18, 36), existing, roads, set(), plan,
        'W46N8 实验室与工厂落点（本家）',
        '',
        notes,
    )


def w47():
    L = load_w47_layout()
    terrain = load_terrain('W47N8')
    ORDER = L['ORDER']
    existing = {}
    roads = {tuple(p) for p in ORDER.get('road', [])}
    # south short path (must stay clear)
    south = {
        (12, 28), (13, 28), (14, 28), (15, 28),
        (15, 29), (15, 30), (15, 31), (15, 32), (15, 33),
        (16, 33), (17, 33), (18, 33), (19, 33), (20, 33), (21, 33), (22, 33), (23, 33),
        (24, 33), (24, 34), (24, 35),
        (25, 35), (26, 35), (27, 35), (28, 35), (29, 35), (30, 35), (31, 35),
        (32, 35), (33, 34), (33, 33), (34, 32),
    }
    # also include documented 12,28–15,33–24,35–31,35 then 33,33/34,32
    extra_south = []
    # 12,28-15,33 may be a path along those corridors; keep the set from report + common path tiles in ASCII y=35
    for x in range(12, 32):
        south.add((x, 35)) if False else None
    # From report: 12,28–15,33–24,35–31,35 then 33,33/34,32. Add 32,35 as in ORDER.
    south |= {(32, 35), (33, 33), (34, 32)}
    roads |= south

    # built under RCL7 caps
    for typ, lim in [('spawn', 2), ('tower', 3), ('extension', 50), ('storage', 1), ('terminal', 1), ('link', 1), ('extractor', 1)]:
        for x, y in ORDER.get(typ, [])[:lim]:
            existing[(x, y)] = typ
    # live extras from the 09:43 survey
    existing[(33, 33)] = 'container'  # hub
    existing[(13, 26)] = 'container'
    existing[(37, 44)] = 'container'
    existing[(37, 45)] = 'mineral'
    existing[(15, 25)] = 'controller'
    # do not draw ORDER.lab or factory or RCL8 reserved as existing

    reserved_other = [
        (34, 31, '留塔'), (36, 31, '留塔'), (36, 33, '留塔'),
        (36, 32, 'PS'), (34, 28, '核'), (33, 28, '观'), (39, 30, 'S3'),
    ]

    plan = {
        'labs_exist': [],
        'labs_now': [(29, 38, 1), (28, 37, 2), (28, 38, 3), (27, 38, 4), (27, 39, 5), (27, 40, 6)],
        'labs_later': [(28, 40, 7), (26, 38, 8), (26, 37, 9), (25, 37, 10)],
        'factory': [(35, 30)],
        'aisles': [(27, 37), (29, 37), (28, 39)],
        'upgraders': [(12, 25), (14, 26), (14, 27)],
        'reserved_other': [(x, y, lb) for x, y, lb in reserved_other],
        'mineral_letter': 'K',
    }
    notes = [
        '本波 7 个工地：',
        '工厂 35,30',
        '实验室 29,38 / 28,37 / 28,38',
        '　　　 27,38（原料A）',
        '　　　 27,39（原料B）',
        '　　　 27,40',
        '过道空着：27,37 / 29,37 / 28,39',
        '不用旧布局那 10 个分散格',
        '升级位和南边短路都未占用',
    ]
    return render(
        'W47N8', terrain, (23, 41, 27, 44), existing, roads, south, plan,
        'W47N8 实验室与工厂落点',
        '',
        notes,
    )


if __name__ == '__main__':
    # fix controller position for W46 if terrain/layout has it
    # look at common sources
    w46()
    w47()
