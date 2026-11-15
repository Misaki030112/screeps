#!/usr/bin/env python3
"""Deep dive: INTERP shorts, upgrader handoffs, invader end, incidents, roles."""
import os, sys, json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
sys.path.insert(0, '/workspace/screeps/tools')
import db

HK = ZoneInfo('Asia/Hong_Kong')
IDEAL = {'W46N8': 26.0, 'W47N8': 30.08}
LAST_TIP = 84293270
TIP = 84293920
c = db.connect()

def p(*a):
    print(*a, flush=True)

def ts(t):
    if t is None: return None
    if getattr(t, 'tzinfo', None) is None:
        return t
    return t.astimezone(HK).strftime('%Y-%m-%d %H:%M:%S')

# ---- INTERP short windows by TICK (not sample span) ----
p('=== INTERP short-by-tick (progress at TIP-N vs TIP) ===')
for room in ('W46N8', 'W47N8'):
    tip = c.execute('SELECT tick,ts,progress,storage FROM room_stats WHERE room=%s AND tick=%s', (room, TIP)).fetchone()
    if not tip:
        tip = c.execute('SELECT tick,ts,progress,storage FROM room_stats WHERE room=%s ORDER BY tick DESC LIMIT 1', (room,)).fetchone()
    tt, tts, tp, ts_ = tip
    p(f'-- {room} TIP {tt} {ts(tts)} p={tp} stor={ts_}')
    for span in (20, 30, 70, 100, 140, 200, 300, 500, 700, 900):
        lo = tt - span
        # brackets around lo
        rows = c.execute('''
            SELECT tick, ts, progress, storage FROM room_stats
            WHERE room=%s AND tick BETWEEN %s AND %s ORDER BY tick
        ''', (room, lo-50, lo+50)).fetchall()
        # also exact if present
        exact = c.execute('SELECT tick,ts,progress,storage FROM room_stats WHERE room=%s AND tick=%s', (room, lo)).fetchone()
        if exact:
            a = b = exact
            frac = 0
            p0, s0, t0 = exact[2], exact[3], exact[0]
        else:
            a = c.execute('SELECT tick,ts,progress,storage FROM room_stats WHERE room=%s AND tick<=%s ORDER BY tick DESC LIMIT 1', (room, lo)).fetchone()
            b = c.execute('SELECT tick,ts,progress,storage FROM room_stats WHERE room=%s AND tick>=%s ORDER BY tick ASC LIMIT 1', (room, lo)).fetchone()
            if not a or not b:
                p(f'  last{span} MISSING brackets a={a} b={b}')
                continue
            if a[0] == b[0]:
                frac = 0
            else:
                frac = (lo - a[0]) / (b[0] - a[0])
            p0 = a[2] + frac * (b[2] - a[2])
            s0 = a[3] + frac * ((b[3] or 0) - (a[3] or 0))
            t0 = lo
        dprog = tp - p0
        rate = dprog / span
        pct = 100 * rate / IDEAL[room]
        p(f'  last{span} INTERP t={t0:.1f} p={p0:.1f} stor={s0:.0f} -> {tt} p={tp} dprog={dprog:.1f} {rate:.2f} e/t = {pct:.1f}%  brackets a={a[0] if a else None}@{ts(a[1]) if a else None} b={b[0] if b else None}@{ts(b[1]) if b else None} frac={frac:.3f}')

# freeze-gap rates (tick-based, using progress at gap ends)
p('=== freeze-gap upgrade rates ===')
gaps = [(84293420, 84293620, '06:42-07:04'), (84293780, 84293870, '07:16-07:22')]
for lo, hi, lab in gaps:
    for room in ('W46N8', 'W47N8'):
        a = c.execute('SELECT tick,ts,progress,storage,hostiles FROM room_stats WHERE room=%s AND tick=%s', (room, lo)).fetchone()
        b = c.execute('SELECT tick,ts,progress,storage,hostiles FROM room_stats WHERE room=%s AND tick=%s', (room, hi)).fetchone()
        if not a or not b:
            p(room, lab, 'missing', a, b)
            continue
        dt = b[0]-a[0]
        rate = (b[2]-a[2])/dt if dt else 0
        p(f'  {room} {lab} {a[0]}->{b[0]} dt={dt} dprog={b[2]-a[2]} {rate:.2f} e/t stor {a[3]}->{b[3]} host {a[4]}->{b[4]} {ts(a[1])} -> {ts(b[1])}')

# ---- W47 / home upgraders in creep_ticks ----
p('=== W47 w8upgrader trajectories since LAST_TIP ===')
rows = c.execute('''
    SELECT name, min(tick) first_t, max(tick) last_t,
           min(tick) FILTER (WHERE energy>0) first_loaded,
           max(tick) FILTER (WHERE energy>0) last_loaded,
           (ARRAY_AGG(x ORDER BY tick) FILTER (WHERE energy>0))[1] fx,
           (ARRAY_AGG(y ORDER BY tick) FILTER (WHERE energy>0))[1] fy,
           (ARRAY_AGG(x ORDER BY tick DESC) FILTER (WHERE energy>0))[1] lx,
           (ARRAY_AGG(y ORDER BY tick DESC) FILTER (WHERE energy>0))[1] ly,
           (ARRAY_AGG(x ORDER BY tick))[1] first_x,
           (ARRAY_AGG(y ORDER BY tick))[1] first_y,
           (ARRAY_AGG(room ORDER BY tick))[1] first_rm,
           (ARRAY_AGG(x ORDER BY tick DESC))[1] last_x,
           (ARRAY_AGG(y ORDER BY tick DESC))[1] last_y,
           (ARRAY_AGG(room ORDER BY tick DESC))[1] last_rm,
           count(*) n
    FROM creep_ticks
    WHERE name LIKE 'w8upgrader%%' AND tick BETWEEN %s AND %s
    GROUP BY name ORDER BY first_t
''', (LAST_TIP-200, TIP+200)).fetchall()
for r in rows:
    p(' ', r)

p('=== home upgrader trajectories since LAST_TIP ===')
rows = c.execute('''
    SELECT name, min(tick) first_t, max(tick) last_t,
           min(tick) FILTER (WHERE energy>0) first_loaded,
           max(tick) FILTER (WHERE energy>0) last_loaded,
           (ARRAY_AGG(x ORDER BY tick) FILTER (WHERE energy>0))[1] fx,
           (ARRAY_AGG(y ORDER BY tick) FILTER (WHERE energy>0))[1] fy,
           (ARRAY_AGG(x ORDER BY tick DESC) FILTER (WHERE energy>0))[1] lx,
           (ARRAY_AGG(y ORDER BY tick DESC) FILTER (WHERE energy>0))[1] ly,
           (ARRAY_AGG(x ORDER BY tick))[1] first_x,
           (ARRAY_AGG(y ORDER BY tick))[1] first_y,
           (ARRAY_AGG(x ORDER BY tick DESC))[1] last_x,
           (ARRAY_AGG(y ORDER BY tick DESC))[1] last_y,
           count(*) n
    FROM creep_ticks
    WHERE name LIKE 'upgrader%%' AND name NOT LIKE 'w8%%' AND tick BETWEEN %s AND %s
    GROUP BY name ORDER BY first_t
''', (LAST_TIP-200, TIP+200)).fetchall()
for r in rows:
    p(' ', r)

# detail near ctl for w8upgraders
p('=== w8upgrader first/last near ctl (x<=16,y between 24-28) ===')
for name in ('w8upgrader84291979','w8upgrader84292195','w8upgrader84293418','w8upgrader84293634'):
    rows = c.execute('''
        SELECT tick, room, x, y, energy, hits
        FROM creep_ticks WHERE name=%s AND tick BETWEEN %s AND %s
        ORDER BY tick
    ''', (name, LAST_TIP-50, TIP+50)).fetchall()
    if not rows:
        p(name, 'NO ROWS')
        continue
    first, last = rows[0], rows[-1]
    loaded = [r for r in rows if (r[4] or 0)>0]
    near = [r for r in rows if r[1]=='W47N8' and r[2] is not None and r[2]<=16 and r[3] is not None and 23<=r[3]<=29]
    p(name, 'n', len(rows), 'first', first, 'last', last)
    if loaded:
        p('   first_loaded', loaded[0], 'last_loaded', loaded[-1], 'loaded_ticks', len(loaded))
    if near:
        p('   first_near', near[0], 'last_near', near[-1])
    # empty after last loaded
    if loaded and loaded[-1][0] < last[0]:
        after = [r for r in rows if r[0] > loaded[-1][0]]
        p('   after_last_loaded n', len(after), 'first_empty', after[0] if after else None, 'last', after[-1] if after else None)

# ---- invader ----
p('=== invader_W47N8_271 / hostiles in W47N8 creep_ticks ===')
rows = c.execute('''
    SELECT tick, x, y, hits, hits_max, ttl, name, owner
    FROM creep_ticks
    WHERE room='W47N8' AND tick BETWEEN %s AND %s
      AND (name ILIKE 'invader%%' OR owner ILIKE 'Invader%%' OR name ILIKE '%%invader%%')
    ORDER BY tick
''', (LAST_TIP-100, TIP+100)).fetchall()
p('invader rows', len(rows))
if rows:
    p('  first', rows[0], 'last', rows[-1])
    # hits over time
    prev = None
    for r in rows:
        if prev is None or r[3]!=prev[3] or r[1]!=prev[1] or r[2]!=prev[2] or r[0]-prev[0]>20:
            p('  ', r)
        prev = r
    p('  last20', *rows[-5:])

p('=== room_stats hostiles W47N8 around death ===')
rows = c.execute('''
    SELECT tick, ts, hostiles, storage, progress FROM room_stats
    WHERE room='W47N8' AND tick BETWEEN 84293300 AND %s ORDER BY tick
''', (TIP,)).fetchall()
for r in rows:
    p(' ', r[0], ts(r[1]), 'host', r[2], 'stor', r[3], 'p', r[4])

# ---- incidents ----
p('=== incidents since LAST_TIP-2000 ===')
try:
    cols = c.execute("""SELECT column_name FROM information_schema.columns WHERE table_name='incidents' ORDER BY ordinal_position""").fetchall()
    p('cols', [x[0] for x in cols])
    rows = c.execute('SELECT * FROM incidents WHERE tick>=%s ORDER BY tick', (LAST_TIP-2000,)).fetchall()
    p('n', len(rows))
    for r in rows:
        p(' ', r)
except Exception as e:
    p('incidents err', type(e), e)

# ---- reservers / reserve7 ----
p('=== reserver / reserve7 trajectories ===')
rows = c.execute('''
    SELECT name, min(tick), max(tick),
           (ARRAY_AGG(room ORDER BY tick))[1],
           (ARRAY_AGG(x ORDER BY tick))[1], (ARRAY_AGG(y ORDER BY tick))[1],
           (ARRAY_AGG(room ORDER BY tick DESC))[1],
           (ARRAY_AGG(x ORDER BY tick DESC))[1], (ARRAY_AGG(y ORDER BY tick DESC))[1],
           min(tick) FILTER (WHERE room IN ('W45N8','W45N7','W47N7') AND ((room='W45N8' AND x BETWEEN 6 AND 8 AND y BETWEEN 36 AND 38) OR (room='W45N7' AND x BETWEEN 5 AND 7 AND y BETWEEN 38 AND 40) OR (room='W47N7' AND x BETWEEN 38 AND 40 AND y BETWEEN 26 AND 28))),
           count(*)
    FROM creep_ticks
    WHERE (name LIKE 'reserver%%' OR name LIKE 'reserve7%%') AND tick BETWEEN %s AND %s
    GROUP BY name ORDER BY min(tick)
''', (LAST_TIP-200, TIP+50)).fetchall()
for r in rows:
    p(' ', r)

# ---- later room_stats after original TIP ----
p('=== later room_stats after 84293920 ===')
for room in ('W46N8','W47N8'):
    rows = c.execute('SELECT tick,ts,progress,storage,hostiles,cpu,bucket,creeps FROM room_stats WHERE room=%s AND tick>%s ORDER BY tick', (room, 84293920)).fetchall()
    p(room, 'later_n', len(rows))
    for r in rows[-8:]:
        p(' ', r[0], ts(r[1]), 'p', r[2], 'stor', r[3], 'host', r[4], 'cpu', r[5], 'bkt', r[6], 'creeps', r[7])

# ---- coverage after retry ----
p('=== coverage 84293101..84293900 after retry ===')
for room in ('W46N8','W47N8','W45N8','W45N7','W47N7'):
    n = c.execute('SELECT count(DISTINCT tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN 84293101 AND 84293900', (room,)).fetchone()[0]
    mx = c.execute('SELECT max(tick) FROM creep_ticks WHERE room=%s', (room,)).fetchone()[0]
    p(room, 'distinct', n, '/800', 'max', mx)

p('=== hour window LAST_TIP+1..latest ===')
for room in ('W46N8','W47N8','W45N8','W45N7','W47N7'):
    ticks = [r[0] for r in c.execute('SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s ORDER BY tick', (room, LAST_TIP+1, 84293950)).fetchall()]
    if ticks:
        want = set(range(LAST_TIP+1, ticks[-1]+1))
        missing = sorted(want - set(ticks))
        spans=[]
        if missing:
            s=e=missing[0]
            for t in missing[1:]:
                if t==e+1: e=t
                else:
                    spans.append((s,e,e-s+1)); s=e=t
            spans.append((s,e,e-s+1))
        p(room, 'distinct', len(ticks), 'range', ticks[0], ticks[-1], 'missing_spans', spans[:8])
    else:
        p(room, 'none')

# longest >=30k / >=40k W47 3h
p('=== W47 storage 3h lock check ===')
rows = c.execute('''
    SELECT tick, ts, storage FROM room_stats
    WHERE room='W47N8' AND tick>=%s ORDER BY tick
''', (TIP - int(3*3600/4.2),)).fetchall()
mx = max((r[2] or 0, r[0], r[1]) for r in rows)
p('3h max', mx)
ge40 = [r for r in rows if (r[2] or 0)>=40000]
ge30 = [r for r in rows if (r[2] or 0)>=30000]
p('>=40k samples', len(ge40), '>=30k samples', len(ge30))
# longest consecutive >=30k tick span
best=0; cur_s=None; prev=None
for r in rows:
    if (r[2] or 0)>=30000:
        if cur_s is None: cur_s=r[0]
        if prev is not None:
            best=max(best, r[0]-cur_s)
        prev=r
    else:
        if cur_s is not None and prev is not None:
            best=max(best, prev[0]-cur_s)
        cur_s=None; prev=None
if cur_s is not None and prev is not None:
    best=max(best, prev[0]-cur_s)
p('longest>=30k tick-span', best)

# home 20k
p('=== home 20k/300t 3h ===')
rows = c.execute('SELECT tick,ts,storage FROM room_stats WHERE room=%s AND tick>=%s ORDER BY tick', ('W46N8', TIP-int(3*3600/4.2))).fetchall()
mx = max((r[2] or 0, r[0], r[1]) for r in rows)
p('3h max', mx, '>=20k', sum(1 for r in rows if (r[2] or 0)>=20000))

# builder at ctl?
p('=== w8builder near ctl this hour ===')
rows = c.execute('''
    SELECT name, tick, x, y, energy FROM creep_ticks
    WHERE name LIKE 'w8builder%%' AND room='W47N8' AND tick BETWEEN %s AND %s
      AND x BETWEEN 12 AND 16 AND y BETWEEN 24 AND 28
    ORDER BY tick
''', (LAST_TIP, TIP+50)).fetchall()
p('near ctl rows', len(rows))
if rows:
    p(' first', rows[0], 'last', rows[-1])

# DB freshness now
p('=== freshness now ===')
for table in ('room_stats','creep_ticks','creep_cpu'):
    p(table, c.execute(f'SELECT max(tick), max(ts), now()-max(ts) FROM {table}').fetchone())

p('DONE')
