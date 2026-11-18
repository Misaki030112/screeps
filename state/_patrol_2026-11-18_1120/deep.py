#!/usr/bin/env python3
"""Deep dive: W47 upgrader handoff, reserve7 gap, home storage dip, miner excess."""
import sys
from collections import defaultdict
sys.path.insert(0, '/workspace/screeps/tools')
import db

c = db.connect()
p = print

p('=== W47 upgrader identities since 84332800 ===')
rows = c.execute('''
  SELECT creep, min(tick), max(tick), count(*)
  FROM creep_ticks
  WHERE room='W47N8' AND role IN ('w8upgrader','upgrader')
    AND tick >= 84332800
  GROUP BY creep ORDER BY min(tick)
''').fetchall()
for r in rows:
    p(' ', r)

p('=== 33519 first visible / path / seated ===')
rows = c.execute('''
  SELECT tick, room, x, y, store, state
  FROM creep_ticks WHERE creep='w8upgrader84333519' ORDER BY tick
''').fetchall()
p(' n', len(rows))
if rows:
    p(' first', rows[0])
    p(' last', rows[-1])
    path = []
    for r in rows:
        key = (r[1], r[2], r[3], r[5])
        if not path or path[-1][1:] != key:
            path.append(r)
    p(' pos/state changes', len(path))
    for item in path:
        p('  ', item)
    seats = {(14,26),(14,27),(12,25),(13,25),(13,26),(14,25),(12,26),(11,25),(12,24)}
    seated = [r for r in rows if (r[2], r[3]) in seats]
    if seated:
        p(' first seat-ish', seated[0], 'n_seated', len(seated), 'last', seated[-1])

p('=== 32618 recent path ===')
rows = c.execute('''
  SELECT tick, room, x, y, store, state
  FROM creep_ticks WHERE creep='w8upgrader84332618' AND tick>=84333400
  ORDER BY tick
''').fetchall()
p(' n late', len(rows))
if rows:
    path=[]
    for r in rows:
        key=(r[1],r[2],r[3],r[5])
        if not path or path[-1][1:]!=key:
            path.append(r)
    p(' changes', len(path))
    for item in path:
        p('  ', item)
    p(' last', rows[-1])

p('=== 32080 last ticks ===')
rows = c.execute('''
  SELECT tick, room, x, y, store, state
  FROM creep_ticks WHERE creep='w8upgrader84332080' AND tick>=84333300
  ORDER BY tick
''').fetchall()
p(' n late', len(rows))
if rows:
    p(' first late', rows[0], 'last', rows[-1])
    path=[]
    for r in rows:
        key=(r[1],r[2],r[3],r[5])
        if not path or path[-1][1:]!=key:
            path.append(r)
    for item in path:
        p('  ', item)

p('=== W47 progress around handoff 84333450-84333720 ===')
prev_p = None
for r in c.execute('''
  SELECT tick, ts, progress, storage, creeps
  FROM room_stats WHERE room='W47N8' AND tick BETWEEN 84333450 AND 84333720
  ORDER BY tick
''').fetchall():
    creeps = r[4] if isinstance(r[4], dict) else {}
    nup = creeps.get('w8upgrader')
    dp = (r[2]-prev_p) if prev_p is not None else None
    p(f'  {r[0]} {r[1]} p={r[2]} d={dp} stor={r[3]} w8up={nup}')
    prev_p = r[2]

p('=== reserve7 identities since 84332000 ===')
for r in c.execute('''
  SELECT creep, min(tick), max(tick), count(*)
  FROM creep_ticks
  WHERE (role='reserve7' OR creep LIKE 'reserve7%') AND tick>=84332000
  GROUP BY creep ORDER BY min(tick)
''').fetchall():
    p(' ', r)

p('=== reserve7 by room/creep in window ===')
for r in c.execute('''
  SELECT creep, room, min(tick), max(tick), count(*), min(x), max(x), min(y), max(y)
  FROM creep_ticks
  WHERE (role='reserve7' OR creep LIKE 'reserve7%')
    AND tick BETWEEN 84332800 AND 84333720
  GROUP BY creep, room ORDER BY min(tick)
''').fetchall():
    p(' ', r)

rows = c.execute('''
  SELECT tick, creep, room, x, y, state
  FROM creep_ticks
  WHERE (role='reserve7' OR creep LIKE 'reserve7%')
    AND tick BETWEEN 84332800 AND 84333720
  ORDER BY tick
''').fetchall()
by_tick = defaultdict(list)
for r in rows:
    by_tick[r[0]].append(r)
ticks = sorted(by_tick)
if ticks:
    p('creep_ticks reserve7 first', ticks[0], 'last', ticks[-1], 'distinct', len(ticks))
    gaps = []
    prev = ticks[0]-1
    for t in ticks:
        if t != prev+1:
            gaps.append((prev+1, t-1, t-prev-1))
        prev = t
    p(' gaps in creep_ticks', gaps, 'ngap', len(gaps))

p('=== traj reserve7s ===')
for name in ('reserve784332376','reserve784333437','reserve784328092','reserve784323437'):
    rows = c.execute('''
      SELECT tick, room, x, y, state
      FROM creep_ticks WHERE creep=%s ORDER BY tick
    ''', (name,)).fetchall()
    p(name, 'n', len(rows))
    if not rows:
        continue
    p(' first', rows[0], 'last', rows[-1])
    path=[]
    for r in rows:
        if not path or (r[1],r[2],r[3],r[4]) != (path[-1][1],path[-1][2],path[-1][3],path[-1][4]):
            path.append(r)
    p(' pos/state changes', len(path))
    show = path if len(path)<=40 else path[:20]+[('...','','','','')]+path[-12:]
    for item in show:
        p('  ', item)

p('=== HOME storage/nUp 84333580-now ===')
for r in c.execute('''
  SELECT tick, ts, progress, storage, energy, creeps
  FROM room_stats WHERE room='W46N8' AND tick>=84333580
  ORDER BY tick
''').fetchall():
    cr = r[5] if isinstance(r[5], dict) else {}
    p(f'  {r[0]} {r[1]} p={r[2]} stor={r[3]} ea={r[4]} nUp={cr.get("upgrader")} q={cr.get("queen")} h={cr.get("hauler")} rh={cr.get("rhauler")}')

p('=== home upgrader identities since 84332800 ===')
for r in c.execute('''
  SELECT creep, min(tick), max(tick), count(*)
  FROM creep_ticks
  WHERE role='upgrader' AND tick>=84332800
  GROUP BY creep ORDER BY min(tick)
''').fetchall():
    p(' ', r)

p('=== later room_stats after tip ===')
for room in ('W46N8','W47N8'):
    rows = c.execute('''
      SELECT tick, ts, progress, storage, creeps
      FROM room_stats WHERE room=%s AND tick>84333710 ORDER BY tick
    ''', (room,)).fetchall()
    p(room, 'later_n', len(rows))
    for r in rows:
        cr = r[4] if isinstance(r[4], dict) else {}
        p(' ', r[0], r[1], 'p', r[2], 'stor', r[3], 'nUp', cr.get('upgrader'), 'w8up', cr.get('w8upgrader'))

p('=== trailing 12h W47 storage max ===')
row = c.execute('''
  SELECT max(storage), min(storage),
         count(*) FILTER (WHERE storage>=40000),
         count(*) FILTER (WHERE storage>=30000)
  FROM room_stats
  WHERE room='W47N8' AND ts >= now() - interval '12 hours'
''').fetchone()
p(' 12h max/min/>=40k/>=30k', row)
for r in c.execute('''
  SELECT tick, ts, storage FROM room_stats
  WHERE room='W47N8' AND ts >= now() - interval '12 hours'
  ORDER BY storage DESC NULLS LAST LIMIT 3
''').fetchall():
    p(' top', r)

p('=== miner84333185 pos ===')
rows = c.execute('''
  SELECT tick, room, x, y, store, state
  FROM creep_ticks WHERE creep='miner84333185' ORDER BY tick
''').fetchall()
if rows:
    p(' n', len(rows), 'first', rows[0], 'last', rows[-1])
    path=[]
    for r in rows:
        if not path or (r[1],r[2],r[3])!=(path[-1][1],path[-1][2],path[-1][3]):
            path.append(r)
    p(' pos changes', len(path))
    for item in path:
        p('  ', item)

p('DONE')
