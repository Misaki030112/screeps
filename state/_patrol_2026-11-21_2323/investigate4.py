#!/usr/bin/env python3
import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db
c = db.connect()

print("=== W47N7 / W47N8 north (y<=12) creeps around 84401600-84401680 ===")
rows = c.execute("""
    SELECT tick, room, creep, role, x, y, hits, state
    FROM creep_ticks
    WHERE tick BETWEEN 84401600 AND 84401680
      AND room IN ('W47N7','W47N8')
      AND (room='W47N7' OR y<=12 OR creep ILIKE '%invader%' OR creep ILIKE '%guard%' OR role IN ('w8rminer','w8rhauler','reserve7','defender','w8guard'))
    ORDER BY tick, room, creep
""").fetchall()
# too many? summarize presence by tick for W47N7 civilians and any odd names
from collections import defaultdict
by = defaultdict(list)
odd=[]
for r in rows:
    tick, room, creep, role, x, y, hits, state = r
    if 'invader' in (creep or '').lower() or (role or '') not in (
        'w8rminer','w8rhauler','reserve7','reserver','defender','w8guard','w8miner','w8hauler',
        'w8upgrader','w8filler','w8builder','w8defender','miner','queen','hauler','upgrader',
        'rhauler','rminer','reserve'):
        odd.append(r)
    if room=='W47N7' or (room=='W47N8' and (y or 99)<=12):
        if tick % 10 == 0 or tick in (84401622,84401623,84401624,84401627,84401628):
            by[tick].append((room, creep, role, x, y, state))

print("odd names", len(odd))
for r in odd[:30]:
    print("ODD", r)

print("=== snapshot ticks ===")
for t in sorted(by):
    print("T", t)
    for item in by[t]:
        print(" ", item)

print("=== later room_stats after 84401970 ===")
for room in ("W46N8","W47N8"):
    rows = c.execute("""
        SELECT tick, ts, storage, progress, cpu, bucket
        FROM room_stats WHERE room=%s AND tick>=84401970 ORDER BY tick
    """, (room,)).fetchall()
    for r in rows:
        print(room, r)
