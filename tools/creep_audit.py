#!/usr/bin/env python3
"""Creep audit on TimescaleDB (SQL in db/audit.sql; see docs/DATA.md).
  .venv/bin/python tools/creep_audit.py              windows 1h/6h/24h -> metrics/creep_audit.json (dashboard cache) + metrics/traffic_<room>.png
  .venv/bin/python tools/creep_audit.py --patrol     exit 0 ok, 1 findings/regressions vs previous window, 2 regression after the last deploy
  --window 6h   heatmap/ranking window (default 24h)
Per creep: stuck episodes (>=10 ticks same tile, no intents, non-stationary role), oscillation (A-B-A-B bounces/4), idle ratio,
CPU/tick, work per CPU ms, repaths/100 ticks, route excess (actual ticks / planned path length), trip time.
Per role: sums/means + trends; regressions vs the previous equal window and before/after the last deploy (equal spans)."""
import os, sys, json, time, math
from datetime import datetime, timedelta, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import db
M = os.path.join(db.ROOT, 'metrics'); SQL = open(os.path.join(db.ROOT, 'db', 'audit.sql')).read()
WIN = {'1h': 1, '6h': 6, '24h': 24}
def creeps(c, a, b):
    cur = c.execute(SQL, {'a': a, 'b': b}); cols = [d.name for d in cur.description]
    return [{k: (float(v) if hasattr(v, 'as_integer_ratio') and not isinstance(v, int) else v) for k, v in zip(cols, r)} for r in cur.fetchall()]
def roles(cs):
    R = {}
    for m in cs:
        r = R.setdefault(m['role'] or '?', {'creeps': 0, 'cpu_t_sum': 0, 'stuck': 0, 'osc': 0, '_': {}})
        r['creeps'] += 1; r['cpu_t_sum'] = round(r['cpu_t_sum'] + (m['cpu_t'] or 0), 3); r['stuck'] += m['stuck']; r['osc'] += m['osc']
        for k in ('idle', 'work_per_cpu', 'excess', 'rp100', 'trip_med'):
            if m[k] is not None: r['_'].setdefault(k, []).append(m[k])
    for r in R.values():
        for k, v in r.pop('_').items(): r[k] = round(sum(v) / len(v), 2)
    return R
def score(m):
    return round((m['cpu_t'] or 0) * 10 + (m['idle'] or 0) * 2 + m['stuck'] + m['osc'] * 0.5 + max(0, (m['excess'] or 1) - 1.3) * 3 + (m['rp100'] or 0) * 0.2, 2)
def regress(cur, prev):
    out = []
    for r, m in cur.items():
        p = prev.get(r)
        if not p: continue
        for k, worse in (('cpu_t_sum', 1.25), ('idle', 1.25), ('excess', 1.2), ('rp100', 1.5), ('trip_med', 1.2)):
            if m.get(k) is not None and p.get(k) and m[k] > p[k] * worse and m[k] - p[k] > 0.05: out.append(f'{r}.{k} {p[k]} -> {m[k]}')
        if m.get('work_per_cpu') and p.get('work_per_cpu') and m['work_per_cpu'] < p['work_per_cpu'] * 0.8: out.append(f"{r}.work_per_cpu {p['work_per_cpu']} -> {m['work_per_cpu']}")
    return out
def heatmap(c, room, a, b, worst):
    from PIL import Image, ImageDraw
    S = 12; f = os.path.join(db.ROOT, 'data', f'terrain_{room}.txt'); T = open(f).read().strip() if os.path.exists(f) else ''
    im = Image.new('RGB', (50 * S, 50 * S + 20), (30, 30, 30)); d = ImageDraw.Draw(im)
    for i, ch in enumerate(T[:2500]):
        x, y = i % 50, i // 50; d.rectangle([x * S, y * S, x * S + S - 1, y * S + S - 1], fill=(0, 0, 0) if ch in '13' else (35, 50, 30) if ch == '2' else (55, 55, 55))
    try:
        H = c.execute('SELECT x, y, sum(n) FROM tile_traffic_10m WHERE room=%s AND bucket >= %s AND bucket < %s GROUP BY x, y', (room, a, b)).fetchall()
    except Exception:
        H = c.execute('SELECT x, y, count(*) FROM creep_ticks WHERE room=%s AND ts >= %s AND ts < %s GROUP BY x, y', (room, a, b)).fetchall()
    mx = max((n for *_, n in H), default=1)
    for x, y, n in H:
        v = math.log1p(n) / math.log1p(mx); d.rectangle([x * S, y * S, x * S + S - 1, y * S + S - 1], fill=(int(60 + 195 * v), int(200 * (1 - v)), 40))
    for col, n in zip([(0, 200, 255), (255, 0, 255), (255, 255, 255)], worst):
        pts = [(x * S + S // 2, y * S + S // 2) for x, y in c.execute('SELECT x, y FROM creep_ticks WHERE room=%s AND creep=%s AND ts >= %s AND ts < %s ORDER BY tick', (room, n, a, b))]
        if len(pts) > 1: d.line(pts, fill=col, width=1)
    d.text((4, 50 * S + 4), f'{room} {a.astimezone():%m-%d %H:%M}..{b.astimezone():%H:%M} UTC+8  max {mx}/tile  lines: {", ".join(worst)}', fill=(255, 255, 255))
    p = os.path.join(M, f'traffic_{room}.png'); im.save(p); return p
def main():
    c = db.connect(); now = datetime.now(timezone.utc)
    res = {'generated': time.strftime('%F %T'), 'windows': {}, 'regressions': {}}
    for w, h in WIN.items():
        a = now - timedelta(hours=h); cs = creeps(c, a, now)
        if not cs: continue
        for m in cs: m['score'] = score(m)
        R = roles(cs); res['windows'][w] = {'from': a.astimezone().strftime('%F %T'), 'roles': R, 'worst': sorted(cs, key=lambda m: -m['score'])[:10]}
        prev = creeps(c, a - timedelta(hours=h), a)
        if prev: res['regressions'][w] = regress(R, roles(prev))
    dep = c.execute('SELECT ts, tick, commit FROM deploys ORDER BY ts DESC LIMIT 1').fetchone()
    if dep:
        dts, t, h = dep; span = min(timedelta(hours=1), now - dts)
        res['deploy'] = {'tick': t, 'commit': h, 'at': dts.astimezone().strftime('%F %T'), 'compare_minutes': int(span.total_seconds() // 60)}
        if span >= timedelta(minutes=10):
            before, after = roles(creeps(c, dts - span, dts)), roles(creeps(c, dts, dts + span))
            res['deploy']['before'], res['deploy']['after'] = before, after
            res['regressions']['deploy'] = regress(after, before)
    W = sys.argv[sys.argv.index('--window') + 1] if '--window' in sys.argv else '24h'
    if W in res['windows']:
        a = now - timedelta(hours=WIN[W]); worst = [m['creep'] for m in res['windows'][W]['worst']]
        res['images'] = []
        for (room,) in c.execute('SELECT DISTINCT room FROM creep_ticks WHERE ts >= %s', (a,)).fetchall():
            here = {r for (r,) in c.execute('SELECT DISTINCT creep FROM creep_ticks WHERE room=%s AND ts >= %s', (room, a)).fetchall()}
            res['images'].append(heatmap(c, room, a, now, [n for n in worst if n in here][:3]))
    json.dump(res, open(os.path.join(M, 'creep_audit.json'), 'w'), indent=1, default=str)
    L = [f"creep audit {res['generated']} (UTC+8)  last deploy {res.get('deploy', {}).get('commit')} @ {res.get('deploy', {}).get('at')}"]
    for w, v in res['windows'].items():
        r = v['roles']; L.append(f"[{w}] creep CPU/t " + ', '.join(f"{k}:{m['cpu_t_sum']}" for k, m in sorted(r.items(), key=lambda kv: -kv[1]['cpu_t_sum'])))
        L.append('   worst: ' + '; '.join(f"{x['creep']}({x['score']}: cpu/t {x['cpu_t']} idle {x['idle']} stuck {x['stuck']} osc {x['osc']} excess {x['excess']} rp/100 {x['rp100']})" for x in v['worst'][:3]))
    # idle attribution (in-game state codes; falls back to retro inference tools/idle_history.py before codes exist)
    try:
        q = c.execute("""SELECT creep, role, sum(ticks) FILTER (WHERE NOT legit)::float / sum(ticks) AS nl, sum(ticks) AS n,
            (array_agg(reason ORDER BY ticks DESC) FILTER (WHERE NOT legit))[1] AS top FROM idle_by_reason
            WHERE bucket >= now() - interval '1 hour' GROUP BY 1, 2""").fetchall()
    except Exception:
        q = []
    if sum(r[3] for r in q) < 500:
        import idle_history as ih
        rows = ih.run((now - timedelta(hours=1)).isoformat(), None); sm = ih.summarize(rows, 'creep')
        q = [(k, k.rstrip('0123456789'), v['nonlegit'] / 100, v['ticks'], next((r for r in v['reasons'] if r not in ih.LEGIT), None)) for k, v in sm.items()]
        src = 'inferred'
    else: src = 'codes'
    idle_flags = sorted([(n, r, round(100 * (x or 0), 1), t) for n, r, x, k, t in q if (x or 0) > 0.10 and k >= 100], key=lambda z: -z[2])
    res['idle'] = {'source': src, 'flags': idle_flags}
    L.append(f"[idle 1h, {src}] non-legit >10%: " + ('; '.join(f'{n}({r}) {p}% top={t}' for n, r, p, t in idle_flags) or 'none'))
    regs = {k: v for k, v in res['regressions'].items() if v}
    for k, v in regs.items(): L.append(f'REGRESSION [{k}]: ' + '; '.join(v))
    if res.get('images'): L.append('images: ' + ', '.join(res['images']))
    print('\n'.join(L))
    flags = sum(x['stuck'] + x['osc'] + ((x['excess'] or 0) > 1.6) for v in res['windows'].values() for x in v['worst'][:5])
    flags += len(idle_flags)
    json.dump(res, open(os.path.join(M, 'creep_audit.json'), 'w'), indent=1, default=str)
    if '--patrol' in sys.argv: sys.exit(2 if regs.get('deploy') else 1 if (regs or flags) else 0)
if __name__ == '__main__': main()
