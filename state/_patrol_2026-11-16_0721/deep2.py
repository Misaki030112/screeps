#!/usr/bin/env python3
import sys
from zoneinfo import ZoneInfo
sys.path.insert(0, '/workspace/screeps/tools')
import db
HK = ZoneInfo('Asia/Hong_Kong')
LAST_TIP = 84293270
TIP = 84293920
c = db.connect()
def p(*a):
    print(*a, flush=True)
def ts(t):
    if t is None: return None
    return t.astimezone(HK).strftime('%Y-%m-%d %H:%M:%S')

p('=== W47 w8upgrader trajectories since LAST_TIP-200 ===')
rows = c.execute('''
    SELECT creep, min(tick) first_t, max(tick) last_t,
           min(tick) FILTER (WHERE store>0) first_loaded,
           max(tick) FILTER (WHERE store>0) last_loaded,
           (ARRAY_AGG(x ORDER BY tick) FILTER (WHERE store>0))[1] fx,
           (ARRAY_AGG(y ORDER BY tick) FILTER (WHERE store>0))[1] fy,
           (ARRAY_AGG(x ORDER BY tick DESC) FILTER (WHERE store>0))[1] lx,
           (ARRAY_AGG(y ORDER BY tick DESC) FILTER (WHERE store>0))[1] ly,
           (ARRAY_AGG(x ORDER BY tick))[1] first_x,
           (ARRAY_AGG(y ORDER BY tick))[1] first_y,
           (ARRAY_AGG(room ORDER BY tick))[1] first_rm,
           (ARRAY_AGG(x ORDER BY tick DESC))[1] last_x,
           (ARRAY_AGG(y ORDER BY tick DESC))[1] last_y,
           (ARRAY_AGG(room ORDER BY tick DESC))[1] last_rm,
           (ARRAY_AGG(state ORDER BY tick))[1] first_st,
           (ARRAY_AGG(state ORDER BY tick DESC))[1] last_st,
           count(*) n
    FROM creep_ticks
    WHERE creep LIKE 'w8upgrader%%' AND tick BETWEEN %s AND %s
    GROUP BY creep ORDER BY first_t
''', (LAST_TIP-400, TIP+200)).fetchall()
for r in rows:
    p(' ', r)

p('=== home upgrader trajectories ===')
rows = c.execute('''
    SELECT creep, min(tick) first_t, max(tick) last_t,
           min(tick) FILTER (WHERE store>0) first_loaded,
           max(tick) FILTER (WHERE store>0) last_loaded,
           (ARRAY_AGG(x ORDER BY tick) FILTER (WHERE store>0))[1] fx,
           (ARRAY_AGG(y ORDER BY tick) FILTER (WHERE store>0))[1] fy,
           (ARRAY_AGG(x ORDER BY tick DESC) FILTER (WHERE store>0))[1] lx,
           (ARRAY_AGG(y ORDER BY tick DESC) FILTER (WHERE store>0))[1] ly,
           (ARRAY_AGG(x ORDER BY tick))[1] first_x,
           (ARRAY_AGG(y ORDER BY tick))[1] first_y,
           (ARRAY_AGG(x ORDER BY tick DESC))[1] last_x,
           (ARRAY_AGG(y ORDER BY tick DESC))[1] last_y,
           (ARRAY_AGG(state ORDER BY tick DESC))[1] last_st,
           count(*) n
    FROM creep_ticks
    WHERE role='upgrader' AND tick BETWEEN %s AND %s
    GROUP BY creep ORDER BY first_t
''', (LAST_TIP-400, TIP+200)).fetchall()
for r in rows:
    p(' ', r)

p('=== w8upgrader detail ===')
for name in ('w8upgrader84291979','w8upgrader84292195','w8upgrader84293418','w8upgrader84293634'):
    rows = c.execute('''
        SELECT tick, room, x, y, store, hits, state
        FROM creep_ticks WHERE creep=%s AND tick BETWEEN %s AND %s
        ORDER BY tick
    ''', (name, LAST_TIP-50, TIP+80)).fetchall()
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
    if loaded and loaded[-1][0] < last[0]:
        after = [r for r in rows if r[0] > loaded[-1][0]]
        p('   after_last_loaded n', len(after), 'first_empty', after[0] if after else None, 'last', after[-1] if after else None)
    # spawn walk: first ticks until first near/loaded
    p('   first8', rows[:8], 'around last8', rows[-8:])

p('=== invader in W47N8 ===')
rows = c.execute('''
    SELECT tick, x, y, hits, store, state, creep, role
    FROM creep_ticks
    WHERE room='W47N8' AND tick BETWEEN %s AND %s
      AND (creep ILIKE 'invader%%' OR role ILIKE '%%invader%%' OR creep ILIKE '%%Invader%%')
    ORDER BY tick
''', (LAST_TIP-200, TIP+80)).fetchall()
p('invader rows', len(rows))
if rows:
    p('  first', rows[0], 'last', rows[-1])
    prev=None
    for r in rows:
        if prev is None or r[3]!=prev[3] or r[1]!=prev[1] or r[2]!=prev[2] or r[0]-prev[0]>15:
            p('  ', r)
        prev=r

# unique invader names last 6h
p('=== unique invader creeps last 6h W47N8 ===')
rows=c.execute('''
    SELECT creep, min(tick), max(tick), min(hits), max(hits),
           (ARRAY_AGG(x ORDER BY tick DESC))[1], (ARRAY_AGG(y ORDER BY tick DESC))[1], count(*)
    FROM creep_ticks
    WHERE room='W47N8' AND tick>=%s AND creep ILIKE 'invader%%'
    GROUP BY creep ORDER BY min(tick)
''', (TIP-8000,)).fetchall()
for r in rows:
    p(' ', r)

p('=== room_stats hostiles W47N8 84293300.. ===')
rows = c.execute('''
    SELECT tick, ts, hostiles, storage FROM room_stats
    WHERE room='W47N8' AND tick BETWEEN 84293300 AND %s ORDER BY tick
''', (TIP+80,)).fetchall()
for r in rows:
    p(' ', r[0], ts(r[1]), 'host', r[2], 'stor', r[3])

p('=== incidents since 84292000 ===')
rows = c.execute('SELECT ts,tick,remote,inc,ev,from_state,state,why,inv,inv_ttl,def,dur FROM incidents WHERE tick>=84292000 ORDER BY tick').fetchall()
p('n', len(rows))
for r in rows:
    p(' ', r[1], ts(r[0]), r[2], 'inc', r[3], r[4], r[5], '->', r[6], 'why', r[7], 'inv', r[8], 'ttl', r[9], 'def', r[10], 'dur', r[11])

p('=== reserver / reserve7 ===')
rows = c.execute('''
    SELECT creep, role, min(tick), max(tick),
           (ARRAY_AGG(room ORDER BY tick))[1] frm,
           (ARRAY_AGG(x ORDER BY tick))[1], (ARRAY_AGG(y ORDER BY tick))[1],
           (ARRAY_AGG(room ORDER BY tick DESC))[1] lrm,
           (ARRAY_AGG(x ORDER BY tick DESC))[1], (ARRAY_AGG(y ORDER BY tick DESC))[1],
           count(*)
    FROM creep_ticks
    WHERE (creep LIKE 'reserver%%' OR creep LIKE 'reserve7%%' OR role IN ('reserver','reserve'))
      AND tick BETWEEN %s AND %s
    GROUP BY creep, role ORDER BY min(tick)
''', (LAST_TIP-400, TIP+80)).fetchall()
for r in rows:
    p(' ', r)

p('=== later room_stats after 84293920 ===')
for room in ('W46N8','W47N8'):
    rows = c.execute('SELECT tick,ts,progress,storage,hostiles,cpu,bucket,creeps FROM room_stats WHERE room=%s AND tick>%s ORDER BY tick', (room, 84293920)).fetchall()
    p(room, 'later_n', len(rows))
    for r in rows:
        p(' ', r[0], ts(r[1]), 'p', r[2], 'stor', r[3], 'host', r[4], 'cpu', r[5], 'bkt', r[6], 'nUp/w8u', (r[7] or {}).get('upgrader'), (r[7] or {}).get('w8upgrader'))

p('=== coverage after retry 84293101..84293900 ===')
for room in ('W46N8','W47N8','W45N8','W45N7','W47N7'):
    n = c.execute('SELECT count(DISTINCT tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN 84293101 AND 84293900', (room,)).fetchone()[0]
    mx = c.execute('SELECT max(tick) FROM creep_ticks WHERE room=%s', (room,)).fetchone()[0]
    p(room, 'distinct', n, '/800', 'max', mx)

p('=== hour window LAST_TIP+1..max ===')
for room in ('W46N8','W47N8','W45N8','W45N7','W47N7'):
    ticks = [r[0] for r in c.execute('SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s ORDER BY tick', (room, LAST_TIP+1, 84294000)).fetchall()]
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
        p(room, 'distinct', len(ticks), 'range', ticks[0], ticks[-1], 'want', ticks[-1]-LAST_TIP, 'missing_spans', spans[:8])
    else:
        p(room, 'none')

p('=== W47 storage 3h lock ===')
rows = c.execute('SELECT tick, ts, storage FROM room_stats WHERE room=%s AND tick>=%s ORDER BY tick', ('W47N8', TIP-int(3*3600/4.22))).fetchall()
mx = max((r[2] or 0, r[0], ts(r[1])) for r in rows)
p('3h max', mx, 'n', len(rows), '>=40k', sum(1 for r in rows if (r[2] or 0)>=40000), '>=30k', sum(1 for r in rows if (r[2] or 0)>=30000))
best=0; cur_s=None; prev=None
for r in rows:
    if (r[2] or 0)>=30000:
        if cur_s is None: cur_s=r[0]
        prev=r
        best=max(best, r[0]-cur_s)
    else:
        cur_s=None; prev=None
p('longest>=30k tick-span', best)

p('=== home 20k 3h ===')
rows = c.execute('SELECT tick,ts,storage FROM room_stats WHERE room=%s AND tick>=%s ORDER BY tick', ('W46N8', TIP-int(3*3600/4.22))).fetchall()
mx = max((r[2] or 0, r[0], ts(r[1])) for r in rows)
p('3h max', mx, '>=20k', sum(1 for r in rows if (r[2] or 0)>=20000))

p('=== w8builder near ctl ===')
rows = c.execute('''
    SELECT creep, tick, x, y, store, state FROM creep_ticks
    WHERE creep LIKE 'w8builder%%' AND room='W47N8' AND tick BETWEEN %s AND %s
      AND x BETWEEN 12 AND 16 AND y BETWEEN 24 AND 28
    ORDER BY tick
''', (LAST_TIP, TIP+80)).fetchall()
p('near ctl rows', len(rows))
if rows:
    p(' first', rows[0], 'last', rows[-1])

p('=== freshness ===')
for table in ('room_stats','creep_ticks','creep_cpu'):
    p(table, c.execute(f'SELECT max(tick), max(ts), now()-max(ts) FROM {table}').fetchone())

# W47 src A miner
p('=== W47 src A miners (26,11) this hour ===')
rows=c.execute('''
    SELECT creep, min(tick), max(tick),
           min(tick) FILTER (WHERE x=26 AND y=11),
           max(tick) FILTER (WHERE x=26 AND y=11),
           count(*) FILTER (WHERE x=26 AND y=11), count(*)
    FROM creep_ticks
    WHERE role='wminer' AND room='W47N8' AND tick BETWEEN %s AND %s
    GROUP BY creep ORDER BY min(tick)
''', (LAST_TIP, TIP)).fetchall()
for r in rows:
    p(' ', r)

p('DONE')
