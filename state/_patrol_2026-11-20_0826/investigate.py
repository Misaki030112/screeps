#!/usr/bin/env python3
"""Investigate W47 R1 harvest gap, reserve7 dropout, storage dip, 40k/20k lock, later stats."""
import sys, json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
sys.path.insert(0, '/workspace/screeps/tools')
import db

SH = ZoneInfo('Asia/Shanghai')
TIP = 84369590
LAST = 84368630

def p(*a):
    print(*a, flush=True)

c = db.connect()

p('=== later room_stats after TIP ===')
for room in ('W46N8','W47N8'):
    rows = c.execute('''
        SELECT tick, ts, progress, storage, energy, cpu, bucket, commit, creeps, hostiles
        FROM room_stats WHERE room=%s AND tick > %s ORDER BY tick
    ''', (room, TIP)).fetchall()
    p(room, 'later_n', len(rows))
    if rows:
        for r in rows[-5:]:
            p(' ', r[0], r[1], 'p', r[2], 'stor', r[3], 'ea', r[4], 'cpu', r[5], 'bkt', r[6], 'cmt', r[7], 'host', r[9])
            p('    creeps', r[8])

p('=== latest both ===')
for room in ('W46N8','W47N8'):
    r = c.execute('''
        SELECT tick, ts, progress, storage, cpu, bucket, commit
        FROM room_stats WHERE room=%s ORDER BY tick DESC LIMIT 1
    ''', (room,)).fetchone()
    p(room, r)

p('=== 40k/500t W47 and 20k/300t home last 8h ===')
for room, thresh, need in (('W47N8', 40000, 500), ('W46N8', 20000, 300)):
    rows = c.execute('''
        SELECT tick, ts, storage FROM room_stats
        WHERE room=%s AND tick >= %s ORDER BY tick
    ''', (room, TIP-int(8*3600/4.0))).fetchall()
    best = 0
    run = 0
    run_start = None
    above_any = [r for r in rows if r[2] and r[2] >= thresh]
    p(room, 'samples', len(rows), f'>={thresh}', len(above_any), 'max_stor', max((r[2] or 0) for r in rows) if rows else None)
    prev = None
    for tick, ts, stor in rows:
        if stor and stor >= thresh:
            if run_start is None:
                run_start = tick
            run = tick - run_start
            if run > best:
                best = run
        else:
            run_start = None
            run = 0
        prev = tick
    p('  best consecutive tick-span at/above', thresh, '=', best, 'need', need, 'locked' if best>=need else 'NOT locked')

p('=== home storage under 15k samples since last ===')
rows = c.execute('''
    SELECT tick, ts, storage, creeps FROM room_stats
    WHERE room='W46N8' AND tick BETWEEN %s AND %s AND storage < 15000
    ORDER BY tick
''', (LAST, TIP+500)).fetchall()
for r in rows:
    creeps=r[3] if isinstance(r[3], dict) else {}
    p(' under15k', r[0], r[1], r[2], 'nUp', creeps.get('upgrader'), 'w8up', creeps.get('w8upgrader'))

p('=== reserve7 / reserver / w8rminer counts since last (every sample) ===')
for room in ('W47N8','W46N8'):
    rows = c.execute('''
        SELECT tick, ts, storage, creeps FROM room_stats
        WHERE room=%s AND tick BETWEEN %s AND %s ORDER BY tick
    ''', (room, LAST, TIP+500)).fetchall()
    prev = None
    p(f'-- {room} role counts changes --')
    for tick, ts, stor, creeps in rows:
        if not isinstance(creeps, dict):
            continue
        key = (creeps.get('reserve7'), creeps.get('reserver'), creeps.get('w8rminer'), creeps.get('rminer'), creeps.get('w8upgrader'), creeps.get('upgrader'))
        if key != prev:
            p(f'  {tick} {ts} stor={stor} reserve7={key[0]} reserver={key[1]} w8rminer={key[2]} rminer={key[3]} w8up={key[4]} nUp={key[5]}')
            prev = key

p('=== W47N7 w8rminer trajectories (names, pos, last ticks) last 2h ===')
rows = c.execute('''
    SELECT name, min(tick), max(tick), count(*),
           min(x), max(x), min(y), max(y)
    FROM creep_ticks
    WHERE room='W47N7' AND tick BETWEEN %s AND %s
      AND (name LIKE 'w8rminer%%' OR name LIKE '%%rminer%%' OR role IN ('wrminer','w8rminer','rminer'))
    GROUP BY name
    ORDER BY min(tick)
''', (TIP-2000, TIP+200)).fetchall()
p('W47N7 miner-like', rows)

# columns of creep_ticks
cols = c.execute('''
    SELECT column_name FROM information_schema.columns
    WHERE table_name='creep_ticks' ORDER BY ordinal_position
''').fetchall()
p('creep_ticks cols', [r[0] for r in cols])

p('=== W47N7 occupancy by tile last 1h (top) ===')
rows = c.execute('''
    SELECT x, y, count(*) n, count(DISTINCT name),
           array_agg(DISTINCT name)
    FROM creep_ticks
    WHERE room='W47N7' AND tick BETWEEN %s AND %s
    GROUP BY x,y
    ORDER BY n DESC
    LIMIT 15
''', (TIP-900, TIP)).fetchall()
for r in rows:
    p(' tile', r)

p('=== W47N7 source-adjacent presence (18,17 and 31,34 containers / typical source tiles) ===')
for xy in [(18,17),(17,17),(18,16),(18,18),(19,17),(31,34),(30,34),(31,33),(31,35),(32,34)]:
    r = c.execute('''
        SELECT count(DISTINCT tick), count(DISTINCT name), min(tick), max(tick)
        FROM creep_ticks
        WHERE room='W47N7' AND tick BETWEEN %s AND %s AND x=%s AND y=%s
          AND (name LIKE 'w8rminer%%' OR role IN ('wrminer','w8rminer'))
    ''', (LAST, TIP, xy[0], xy[1])).fetchone()
    p('  miner at', xy, r)

p('=== which creeps sat near 18,17 vs 31,34 in last hour ===')
for cx,cy in [(18,17),(31,34)]:
    rows = c.execute('''
        SELECT name, role, count(DISTINCT tick), min(tick), max(tick),
               min(x), max(x), min(y), max(y)
        FROM creep_ticks
        WHERE room='W47N7' AND tick BETWEEN %s AND %s
          AND abs(x-%s)<=1 AND abs(y-%s)<=1
        GROUP BY name, role
        ORDER BY count(DISTINCT tick) DESC
    ''', (LAST, TIP, cx, cy)).fetchall()
    p(f' near {cx},{cy}', rows)

p('=== reserve7 / reserve / reserver in W47N7 or named reserve7 last 2h ===')
rows = c.execute('''
    SELECT name, role, room, min(tick), max(tick), count(*),
           (array_agg(x ORDER BY tick DESC))[1] lx,
           (array_agg(y ORDER BY tick DESC))[1] ly
    FROM creep_ticks
    WHERE tick BETWEEN %s AND %s
      AND (name LIKE 'reserve%%' OR role IN ('reserve','reserve7','reserver'))
    GROUP BY name, role, room
    ORDER BY min(tick)
''', (LAST-500, TIP+200)).fetchall()
for r in rows:
    p(' ', r)

p('=== harvest intent or energy around W47N7 sources if columns exist ===')
# try common columns
p('DONE')
