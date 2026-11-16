#!/usr/bin/env python3
import sys, json
from collections import defaultdict
from zoneinfo import ZoneInfo
sys.path.insert(0, '/workspace/screeps/tools')
import db
HK = ZoneInfo('Asia/Hong_Kong')
LAST_TIP = 84293920
TIP = 84294810
IDEAL = {'W46N8': 26.0, 'W47N8': 30.08}
c = db.connect()

def p(*a):
    print(*a, flush=True)

def ts(t):
    if t is None: return None
    return t.astimezone(HK).strftime('%Y-%m-%d %H:%M:%S')

def agg_creeps(like=None, role=None, room=None, lo=LAST_TIP-400, hi=TIP+200):
    q = '''
    SELECT creep, role, min(tick) first_t, max(tick) last_t,
           min(tick) FILTER (WHERE store>0) first_loaded,
           max(tick) FILTER (WHERE store>0) last_loaded,
           (ARRAY_AGG(room ORDER BY tick))[1] first_rm,
           (ARRAY_AGG(x ORDER BY tick))[1] first_x,
           (ARRAY_AGG(y ORDER BY tick))[1] first_y,
           (ARRAY_AGG(room ORDER BY tick DESC))[1] last_rm,
           (ARRAY_AGG(x ORDER BY tick DESC))[1] last_x,
           (ARRAY_AGG(y ORDER BY tick DESC))[1] last_y,
           (ARRAY_AGG(state ORDER BY tick DESC))[1] last_st,
           count(*) n,
           count(*) FILTER (WHERE room='W45N7') n45n7,
           count(*) FILTER (WHERE room='W47N7') n47n7,
           count(*) FILTER (WHERE room='W47N8') n47n8,
           count(*) FILTER (WHERE room='W46N8') n46n8,
           count(*) FILTER (WHERE room='W45N8') n45n8
    FROM creep_ticks
    WHERE tick BETWEEN %s AND %s
    '''
    args = [lo, hi]
    if like:
        q += ' AND creep LIKE %s'
        args.append(like)
    if role:
        q += ' AND role=%s'
        args.append(role)
    if room:
        q += ' AND room=%s'
        args.append(room)
    q += ' GROUP BY creep, role ORDER BY first_t'
    return c.execute(q, args).fetchall()

p('=== W47 w8upgrader trajectories ===')
for r in agg_creeps(like='w8upgrader%'):
    p(' ', r)

p('=== home upgrader trajectories ===')
for r in agg_creeps(role='upgrader'):
    p(' ', r)

# seated ticks: W47 ctl neighborhood 12-16, 24-29; home typically 29-32, 28-32
p('=== w8upgrader seated/work by tick buckets ===')
rows = c.execute('''
    SELECT creep, tick, room, x, y, store, state
    FROM creep_ticks
    WHERE creep LIKE 'w8upgrader%%' AND tick BETWEEN %s AND %s
    ORDER BY creep, tick
''', (LAST_TIP-50, TIP+50)).fetchall()
by = defaultdict(list)
for r in rows:
    by[r[0]].append(r)
for name, rs in by.items():
    seated = [r for r in rs if r[2]=='W47N8' and r[3] is not None and 12<=r[3]<=16 and 24<=r[3]<=29 and (r[5] or 0)>0]
    loaded = [r for r in rs if (r[5] or 0)>0]
    p(name, 'n', len(rs), 'first', rs[0][1:], 'last', rs[-1][1:],
      'loaded', len(loaded), 'seated_loaded', len(seated))
    if seated:
        p('   first_seated', seated[0][1:], 'last_seated', seated[-1][1:])
    # detect gaps in seated
    if seated:
        gaps=[]
        prev=seated[0][1]
        for r in seated[1:]:
            if r[1] > prev+1:
                gaps.append((prev+1, r[1]-1, r[1]-prev-1))
            prev=r[1]
        p('   seated_span', seated[0][1], seated[-1][1], 'internal_gaps', gaps[:8], 'ngap', len(gaps))

p('=== home upgrader seated ===')
rows = c.execute('''
    SELECT creep, tick, room, x, y, store, state
    FROM creep_ticks
    WHERE role='upgrader' AND tick BETWEEN %s AND %s
    ORDER BY creep, tick
''', (LAST_TIP-50, TIP+50)).fetchall()
by = defaultdict(list)
for r in rows:
    by[r[0]].append(r)
for name, rs in by.items():
    seated = [r for r in rs if r[2]=='W46N8' and r[3] is not None and 28<=r[3]<=33 and 28<=r[4]<=33 and (r[5] or 0)>0]
    p(name, 'n', len(rs), 'first', rs[0][1:], 'last', rs[-1][1:], 'seated_loaded', len(seated))
    if seated:
        p('   first_seated', seated[0][1:], 'last_seated', seated[-1][1:])

p('=== INTERP short windows from room_stats (progress delta / tick span, including freeze gaps) ===')
# Use continuous interpolation: get all samples, plus compute e/t over last N ticks by interpolating start progress
for room, ideal in IDEAL.items():
    samples = c.execute('''
        SELECT tick, ts, progress, storage FROM room_stats
        WHERE room=%s AND tick BETWEEN %s AND %s
        ORDER BY tick
    ''', (room, TIP-2000, TIP)).fetchall()
    # also fetch a bit before
    tip = samples[-1] if samples else None
    p(room, 'samples', len(samples), 'tip', tip[0] if tip else None, 'p', tip[2] if tip else None)
    for window in (20, 30, 70, 100, 140, 200, 300, 500, 800):
        target = TIP - window
        # interpolate progress at target
        before = [s for s in samples if s[0] <= target]
        after = [s for s in samples if s[0] >= target]
        # also query slightly earlier if needed
        if not before:
            before = c.execute('''
                SELECT tick, ts, progress, storage FROM room_stats
                WHERE room=%s AND tick<=%s ORDER BY tick DESC LIMIT 1
            ''', (room, target)).fetchall()
            before = list(reversed(before))
        if not before or not after:
            p(f'  last{window} INCOMPLETE before={bool(before)} after={bool(after)}')
            continue
        a = before[-1]
        b = after[0]
        if b[0]==a[0]:
            p0, s0 = a[2], a[3]
            frac=0
        else:
            frac = (target - a[0]) / (b[0] - a[0])
            p0 = a[2] + frac*(b[2]-a[2])
            s0 = a[3] + frac*((b[3] or 0)-(a[3] or 0))
        dt = TIP - target
        dprog = tip[2] - p0
        rate = dprog/dt if dt else 0
        pct = 100*rate/ideal
        p(f'  INTERP last{window}t  {rate:.2f} e/t {pct:.1f}%  start_tick={target} p0={p0:.1f} stor0={s0:.0f} -> tip p={tip[2]} stor={tip[3]}  brackets {a[0]}..{b[0]} frac={frac:.3f}')

p('=== W47 source A (near 26,11) miner presence & store ===')
rows = c.execute('''
    SELECT creep, min(tick), max(tick),
           count(*) FILTER (WHERE room='W47N8' AND x BETWEEN 24 AND 28 AND y BETWEEN 9 AND 13) on_src,
           count(*) n,
           avg(store) FILTER (WHERE room='W47N8' AND x BETWEEN 24 AND 28 AND y BETWEEN 9 AND 13) avg_store
    FROM creep_ticks
    WHERE role IN ('w8miner','wminer') AND tick BETWEEN %s AND %s
    GROUP BY creep ORDER BY min(tick)
''', (LAST_TIP, TIP+80)).fetchall()
for r in rows:
    p(' miner', r)

# per 100-tick harvest proxy: store increases / presence
p('--- source A on-tile ticks per 100 ---')
rows = c.execute('''
    SELECT (tick/100)*100 bucket,
           count(DISTINCT tick) ticks_with_miner,
           count(DISTINCT creep) miners,
           array_agg(DISTINCT creep)
    FROM creep_ticks
    WHERE role IN ('w8miner','wminer') AND room='W47N8'
      AND x BETWEEN 24 AND 28 AND y BETWEEN 9 AND 13
      AND tick BETWEEN %s AND %s
    GROUP BY 1 ORDER BY 1
''', (LAST_TIP, TIP+80)).fetchall()
for r in rows:
    p(' ', r)

p('=== W47 source B (near 11,43) miner presence per 100 ===')
rows = c.execute('''
    SELECT (tick/100)*100 bucket,
           count(DISTINCT tick) ticks_with_miner,
           count(DISTINCT creep) miners
    FROM creep_ticks
    WHERE role IN ('w8miner','wminer') AND room='W47N8'
      AND x BETWEEN 9 AND 13 AND y BETWEEN 41 AND 45
      AND tick BETWEEN %s AND %s
    GROUP BY 1 ORDER BY 1
''', (LAST_TIP, TIP+80)).fetchall()
for r in rows:
    p(' ', r)

p('=== W45N7 role presence (rminer/reserver/rhauler/defender) ===')
rows = c.execute('''
    SELECT role, creep, min(tick), max(tick), count(*),
           (ARRAY_AGG(room ORDER BY tick))[1] frm,
           (ARRAY_AGG(x ORDER BY tick))[1] fx,
           (ARRAY_AGG(y ORDER BY tick))[1] fy,
           (ARRAY_AGG(room ORDER BY tick DESC))[1] lrm,
           (ARRAY_AGG(x ORDER BY tick DESC))[1] lx,
           (ARRAY_AGG(y ORDER BY tick DESC))[1] ly
    FROM creep_ticks
    WHERE tick BETWEEN %s AND %s
      AND (role IN ('rminer','reserver','rhauler','defender','rdef')
           OR creep LIKE 'rminer%%' OR creep LIKE 'reserver%%' OR creep LIKE 'defender%%')
    GROUP BY role, creep
    ORDER BY role, min(tick)
''', (LAST_TIP-200, TIP+80)).fetchall()
for r in rows:
    p(' ', r)

p('=== ticks with any creep in W45N7 ===')
rows = c.execute('''
    SELECT min(tick), max(tick), count(DISTINCT tick), count(*),
           array_agg(DISTINCT role), array_agg(DISTINCT creep)
    FROM creep_ticks
    WHERE room='W45N7' AND tick BETWEEN %s AND %s
''', (LAST_TIP-200, TIP+80)).fetchall()
for r in rows:
    p(' ', r)

p('--- W45N7 occupancy spans (gaps > 20t) ---')
ticks = [r[0] for r in c.execute(
    'SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s ORDER BY tick',
    ('W45N7', LAST_TIP-200, TIP+80)).fetchall()]
if ticks:
    p(' first', ticks[0], 'last', ticks[-1], 'distinct', len(ticks), 'span', ticks[-1]-ticks[0]+1)
    gaps=[]
    prev=ticks[0]
    for t in ticks[1:]:
        if t>prev+1:
            if t-prev-1>=20:
                gaps.append((prev+1, t-1, t-prev-1))
        prev=t
    p(' gaps>=20', gaps)

p('=== reserve7 presence ===')
for r in agg_creeps(like='reserve7%', lo=LAST_TIP-400, hi=TIP+80):
    p(' ', r)
# any tick with reserve7 in W47N7
rows = c.execute('''
    SELECT creep, min(tick), max(tick), count(*)
    FROM creep_ticks
    WHERE (creep LIKE 'reserve7%%' OR role IN ('reserve','reserve7'))
      AND room='W47N7' AND tick BETWEEN %s AND %s
    GROUP BY creep ORDER BY min(tick)
''', (LAST_TIP-400, TIP+80)).fetchall()
p(' on controller room', rows)
ticks = [r[0] for r in c.execute(
    '''SELECT DISTINCT tick FROM creep_ticks
       WHERE (creep LIKE 'reserve7%%' OR role IN ('reserve','reserve7'))
         AND room='W47N7' AND tick BETWEEN %s AND %s ORDER BY tick''',
    (LAST_TIP-200, TIP+80)).fetchall()]
if ticks:
    gaps=[]
    prev=ticks[0]
    for t in ticks[1:]:
        if t>prev+1 and t-prev-1>=20:
            gaps.append((prev+1, t-1, t-prev-1))
        prev=t
    p(' W47N7 reserve7 first', ticks[0], 'last', ticks[-1], 'distinct', len(ticks), 'gaps>=20', gaps)

p('=== defender trajectory ===')
for r in agg_creeps(like='defender%', lo=LAST_TIP-50, hi=TIP+80):
    p(' ', r)
rows = c.execute('''
    SELECT tick, room, x, y, hits, store, state
    FROM creep_ticks WHERE creep LIKE 'defender%%' AND tick BETWEEN %s AND %s
    ORDER BY tick
''', (LAST_TIP, TIP+80)).fetchall()
if rows:
    # compress: print first, last, and room-change points
    p(' n', len(rows), 'first', rows[0], 'last', rows[-1])
    prev=None
    for r in rows:
        key=(r[1], r[6])
        if key!=prev:
            p('  change', r)
            prev=key

p('=== W45N7-bound rminer84294091 path ===')
rows = c.execute('''
    SELECT tick, room, x, y, store, state
    FROM creep_ticks WHERE creep='rminer84294091' AND tick BETWEEN %s AND %s
    ORDER BY tick
''', (LAST_TIP-50, TIP+80)).fetchall()
if rows:
    p(' n', len(rows), 'first', rows[0], 'last', rows[-1])
    prev=None
    for r in rows:
        key=r[1]
        if key!=prev:
            p('  room', r)
            prev=key
    # last 5
    p('  last5', rows[-5:])

p('=== reserver84294563 path (parked_threat?) ===')
rows = c.execute('''
    SELECT tick, room, x, y, store, state
    FROM creep_ticks WHERE creep='reserver84294563' AND tick BETWEEN %s AND %s
    ORDER BY tick
''', (LAST_TIP-50, TIP+80)).fetchall()
if rows:
    p(' n', len(rows), 'first', rows[0], 'last', rows[-1])
    prev=None
    for r in rows:
        key=(r[1], r[5])
        if key!=prev:
            p('  change', r)
            prev=key

p('=== previous W45N7 reserver/rminer last seen ===')
for name in ('reserver84293689','rminer84292810','reserver84294237','rminer84294342','reserver84293199'):
    r = c.execute('''
        SELECT min(tick), max(tick),
               (ARRAY_AGG(room ORDER BY tick DESC))[1],
               (ARRAY_AGG(x ORDER BY tick DESC))[1],
               (ARRAY_AGG(y ORDER BY tick DESC))[1],
               count(*)
        FROM creep_ticks WHERE creep=%s AND tick BETWEEN %s AND %s
    ''', (name, LAST_TIP-800, TIP+80)).fetchone()
    p(' ', name, r)

p('=== W47N7 rminers / sites related ===')
for r in agg_creeps(role='w8rminer', lo=LAST_TIP-50, hi=TIP+80):
    p(' ', r)

p('=== construction sites in room_stats (sites>0) since last ===')
for room in ('W46N8','W47N8'):
    rows=c.execute('''
        SELECT tick, ts, sites, storage FROM room_stats
        WHERE room=%s AND tick BETWEEN %s AND %s AND sites>0
        ORDER BY tick
    ''', (room, LAST_TIP-20, TIP+20)).fetchall()
    p(room, 'sites>0 n', len(rows))
    if rows:
        p('  first', rows[0][0], ts(rows[0][1]), 'sites', rows[0][2], 'stor', rows[0][3])
        p('  last', rows[-1][0], ts(rows[-1][1]), 'sites', rows[-1][2], 'stor', rows[-1][3])

p('=== events alert_* last 6h W45/W47 ===')
rows=c.execute('''
    SELECT tick, ts, kind, room, severity, episode, msg, data
    FROM events
    WHERE tick>=84290000 AND (kind LIKE 'alert%%' OR kind LIKE 'threat%%' OR room IN ('W45N7','W47N7','W47N8'))
    ORDER BY tick
''').fetchall()
for r in rows:
    p(' ', r[0], ts(r[1]), r[2], r[3], r[4], r[5], r[6], r[7])

p('=== box_pause this morning ===')
rows=c.execute('''
    SELECT tick, ts, msg, data FROM events
    WHERE kind='box_pause' AND tick>=84290000 ORDER BY tick
''').fetchall()
for r in rows:
    p(' ', r[0], ts(r[1]), r[2], r[3])

p('DONE')
