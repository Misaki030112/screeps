#!/usr/bin/env python3
"""Creep audit over rolling windows of the continuous telemetry in metrics/ts.sqlite (see tools/tsdb.py).
  .venv/bin/python tools/creep_audit.py              windows 1h/6h/24h, writes metrics/creep_audit.json + metrics/traffic_<room>.png
  .venv/bin/python tools/creep_audit.py --patrol     short text for the patrol; exit 0 ok, 1 findings, 2 regression after a deploy
  --window 6h  (heatmap/ranking window, default 24h)   --prune   apply retention (7d full res, 60d downsampled)
Flags per creep: stuck episodes (>=10 ticks same tile, no intents, non-stationary role), oscillation (A-B-A-B >=4),
idle ratio (5-tick windows with 0 intents), repaths/100 ticks, route excess (actual ticks / planned path length on arrival),
CPU per tick, work per CPU ms. Regressions: each window vs the previous window of equal length, and before/after the last deploy."""
import os, sys, json, re, time, statistics as S
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import tsdb
from collections import defaultdict
ROOT = tsdb.ROOT; M = os.path.join(ROOT, 'metrics')
STATIONARY = {'miner', 'rminer', 'filler', 'manager', 'upgrader'}
role_of = lambda n: (re.match(r'[a-z]+', n or '') or [None])[0] if n else None
WIN = {'1h': 3600, '6h': 6 * 3600, '24h': 24 * 3600}
def tick_bounds(c, t0, t1):
    r = c.execute('SELECT min(tick), max(tick) FROM pos WHERE ts >= ? AND ts < ?', (t0, t1)).fetchone()
    return r if r[0] is not None else None
def analyse(c, a, b):
    """a..b tick range -> per-creep and per-role metrics"""
    P = defaultdict(list)
    for t, room, n, x, y, e in c.execute('SELECT tick, room, name, x, y, e FROM pos WHERE tick BETWEEN ? AND ? ORDER BY name, tick', (a, b)):
        P[n].append((t, room, x, y, e))
    CP = defaultdict(list)
    for t, n, cpu, acts, work, rp, st in c.execute('SELECT tick, name, cpu, acts, work, rp, st FROM cpu WHERE tick BETWEEN ? AND ?', (a, b)):
        CP[n].append((t, cpu, acts, work, rp, st))
    AR = defaultdict(list)
    for t, n, role, tgt, plan, act in c.execute('SELECT tick, name, role, tgt, plan, actual FROM arr WHERE tick BETWEEN ? AND ?', (a, b)):
        AR[n].append((tgt, plan, act))
    out = {}
    for n in set(P) | set(CP):
        role = role_of(n); pts = P.get(n, []); cw = CP.get(n, [])
        idle_w = {t for t, cpu, acts, *_ in cw if acts == 0}
        # stuck episodes / oscillation from per-tick positions
        stuck, run, osc, orun, moves = 0, 1, 0, 0, 0
        for i in range(1, len(pts)):
            same = pts[i][1:4] == pts[i - 1][1:4]
            if not same: moves += 1
            if same and role not in STATIONARY: run += 1
            else:
                if run >= 10 and any(((t + 4) // 5 * 5) in idle_w for t in range(pts[i - run][0], pts[i - 1][0] + 1)): stuck += 1
                run = 1
            if i >= 2 and pts[i][1:4] == pts[i - 2][1:4] and not same: orun += 1
            else:
                if orun >= 4: osc += 1
                orun = 0
        ticks = max(1, (pts[-1][0] - pts[0][0] + 1) if pts else len(cw) * 5)
        cpu_ms = sum(r[1] for r in cw) / 100; work = sum(r[3] for r in cw)
        arr = AR.get(n, []); ex = [act / plan for _, plan, act in arr if plan]
        out[n] = {'role': role, 'ticks': ticks, 'samples': len(pts), 'moves': moves, 'tiles': len({p[1:4] for p in pts}),
                  'stuck': stuck, 'osc': osc, 'idle': round(len(idle_w) / len(cw), 2) if cw else None,
                  'cpu_t': round(cpu_ms / max(1, len(cw) * 5), 3) if cw else None, 'work_per_cpu': round(work / cpu_ms, 1) if cpu_ms else None,
                  'work_t': round(work / max(1, len(cw) * 5), 2) if cw else None,
                  'rp100': round(sum(r[4] for r in cw) * 100 / max(1, len(cw) * 5), 1) if cw else None, 'stuck_ev': sum(r[5] for r in cw),
                  'trips': len(arr), 'excess': round(S.median(ex), 2) if ex else None, 'excess_max': round(max(ex), 2) if ex else None,
                  'trip_med': S.median([x[2] for x in arr]) if arr else None}
    roles = defaultdict(lambda: defaultdict(list))
    for n, m in out.items():
        for k in ('cpu_t', 'idle', 'work_per_cpu', 'excess', 'rp100', 'trip_med'):
            if m[k] is not None: roles[m['role']][k].append(m[k])
        roles[m['role']]['n'].append(1); roles[m['role']]['stuck'].append(m['stuck']); roles[m['role']]['osc'].append(m['osc'])
    R = {r: {'creeps': len(v['n']), 'cpu_t_sum': round(sum(v['cpu_t']), 3), **{k: round(S.mean(v[k]), 2) for k in ('idle', 'work_per_cpu', 'excess', 'rp100', 'trip_med') if v[k]},
             'stuck': sum(v['stuck']), 'osc': sum(v['osc'])} for r, v in roles.items()}
    return out, R
def score(m):
    return round((m['cpu_t'] or 0) * 10 + (m['idle'] or 0) * 2 + m['stuck'] * 1 + m['osc'] * 0.5 + max(0, (m['excess'] or 1) - 1.3) * 3 + (m['rp100'] or 0) * 0.2, 2)
def regress(cur, prev):
    out = []
    for r, m in cur.items():
        p = prev.get(r); 
        if not p: continue
        for k, worse in (('cpu_t_sum', 1.25), ('idle', 1.25), ('excess', 1.2), ('rp100', 1.5), ('trip_med', 1.2)):
            if k in m and k in p and p[k] and m[k] > p[k] * worse and m[k] - p[k] > 0.05: out.append(f'{r}.{k} {p[k]} -> {m[k]}')
        if m.get('work_per_cpu') and p.get('work_per_cpu') and m['work_per_cpu'] < p['work_per_cpu'] * 0.8: out.append(f"{r}.work_per_cpu {p['work_per_cpu']} -> {m['work_per_cpu']}")
    return out
def terrain(room):
    f = os.path.join(ROOT, 'data', f'terrain_{room}.txt'); return open(f).read().strip() if os.path.exists(f) else None
def heatmap(c, room, a, b, worst):
    from PIL import Image, ImageDraw
    S_ = 12; T = terrain(room); im = Image.new('RGB', (50 * S_, 50 * S_ + 20), (30, 30, 30)); d = ImageDraw.Draw(im)
    if T:
        for i, ch in enumerate(T[:2500]):
            x, y = i % 50, i // 50
            d.rectangle([x * S_, y * S_, x * S_ + S_ - 1, y * S_ + S_ - 1], fill=(0, 0, 0) if ch in '13' else (35, 50, 30) if ch == '2' else (55, 55, 55))
    H = {(x, y): k for x, y, k in c.execute('SELECT x, y, count(*) FROM pos WHERE room=? AND tick BETWEEN ? AND ? GROUP BY x, y', (room, a, b))}
    mx = max(H.values()) if H else 1
    import math
    for (x, y), k in H.items():
        v = math.log1p(k) / math.log1p(mx); d.rectangle([x * S_, y * S_, x * S_ + S_ - 1, y * S_ + S_ - 1], fill=(int(60 + 195 * v), int(200 * (1 - v)), 40))
    cols = [(0, 200, 255), (255, 0, 255), (255, 255, 255)]
    for i, n in enumerate(worst[:3]):
        pts = [(x * S_ + S_ // 2, y * S_ + S_ // 2) for x, y in c.execute('SELECT x, y FROM pos WHERE room=? AND name=? AND tick BETWEEN ? AND ? ORDER BY tick', (room, n, a, b))]
        if len(pts) > 1: d.line(pts, fill=cols[i], width=1)
    d.text((4, 50 * S_ + 4), f'{room} ticks {a}-{b}  max {mx}/tile  lines: {", ".join(worst[:3])}', fill=(255, 255, 255))
    p = os.path.join(M, f'traffic_{room}.png'); im.save(p); return p
def main():
    c = tsdb.connect()
    if '--prune' in sys.argv: tsdb.prune(c)
    now = int(time.time()); res = {'generated': time.strftime('%F %T'), 'windows': {}, 'regressions': {}}
    for w, sec in WIN.items():
        cb, pb = tick_bounds(c, now - sec, now + 1), tick_bounds(c, now - 2 * sec, now - sec)
        if not cb: continue
        creeps, roles = analyse(c, *cb)
        res['windows'][w] = {'ticks': cb, 'roles': roles, 'worst': sorted(({'name': n, 'score': score(m), **m} for n, m in creeps.items()), key=lambda x: -x['score'])[:10]}
        if pb: res['regressions'][w] = regress(roles, analyse(c, *pb)[1])
    dep = c.execute('SELECT tick, gitcommit, ts FROM deploys ORDER BY tick DESC LIMIT 1').fetchone()
    if dep:
        t, h, ts = dep; span = min(1200, max(0, (c.execute('SELECT max(tick) FROM pos').fetchone()[0] or t) - t))
        res['deploy'] = {'tick': t, 'commit': h, 'at': time.strftime('%F %T', time.localtime(ts)), 'compare_ticks': span}
        if span >= 100: res['regressions']['deploy'] = regress(analyse(c, t, t + span)[1], analyse(c, t - span, t - 1)[1])
    wk = next((w for w in ('--window',) if w in sys.argv), None); W = sys.argv[sys.argv.index('--window') + 1] if wk else '24h'
    W = W if W in res['windows'] else next(iter(res['windows']), None)
    if W:
        a, b = res['windows'][W]['ticks']; worst = [x['name'] for x in res['windows'][W]['worst']]
        res['images'] = [heatmap(c, r, a, b, [n for n in worst if c.execute('SELECT 1 FROM pos WHERE room=? AND name=? LIMIT 1', (r, n)).fetchone()])
                         for (r,) in c.execute('SELECT DISTINCT room FROM pos WHERE tick BETWEEN ? AND ?', (a, b)).fetchall()]
    json.dump(res, open(os.path.join(M, 'creep_audit.json'), 'w'), indent=1)
    lines = [f"creep audit {res['generated']} (UTC+8)  last deploy {res.get('deploy', {}).get('commit')} @ {res.get('deploy', {}).get('at')}"]
    for w, v in res['windows'].items():
        r = v['roles']; lines.append(f"[{w}] ticks {v['ticks'][0]}-{v['ticks'][1]}  creep CPU/t " + ', '.join(f"{k}:{m['cpu_t_sum']}" for k, m in sorted(r.items(), key=lambda kv: -kv[1]['cpu_t_sum'])))
        lines.append('   worst: ' + '; '.join(f"{x['name']}({x['score']}: cpu/t {x['cpu_t']} idle {x['idle']} stuck {x['stuck']} osc {x['osc']} excess {x['excess']} rp/100 {x['rp100']})" for x in v['worst'][:3]))
    flags = sum(x['stuck'] + x['osc'] + ((x['excess'] or 0) > 1.6) for v in res['windows'].values() for x in v['worst'])
    regs = {k: v for k, v in res['regressions'].items() if v}
    for k, v in regs.items(): lines.append(f'REGRESSION [{k}]: ' + '; '.join(v))
    if res.get('images'): lines.append('images: ' + ', '.join(res['images']))
    print('\n'.join(lines))
    if '--patrol' in sys.argv: sys.exit(2 if regs.get('deploy') else 1 if (regs or flags) else 0)
if __name__ == '__main__': main()
