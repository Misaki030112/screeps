#!/usr/bin/env python3
import sys
from collections import defaultdict
sys.path.insert(0, "/workspace/screeps/tools")
import db

c = db.connect()
def p(*a):
    print(*a, flush=True)

LAST_TIP = 84372970
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")

p("=== freshness ===")
for table in ("room_stats", "creep_ticks", "creep_cpu"):
    row = c.execute(f"SELECT max(tick), max(ts), now()-max(ts) FROM {table}").fetchone()
    p(table, row)

p("=== room_stats tips ===")
for room in ("W46N8", "W47N8"):
    row = c.execute("""
        SELECT tick, ts, rcl, progress, storage, energy, cpu, bucket, hostiles, sites
        FROM room_stats WHERE room=%s ORDER BY tick DESC LIMIT 1
    """, (room,)).fetchone()
    p(room, row)

p("=== storage series home/W47 since last tip, every ~20t sample plus min ===")
for room in ("W46N8", "W47N8"):
    rows = c.execute("""
        SELECT tick, ts, storage, progress, cpu, bucket, hostiles, energy
        FROM room_stats WHERE room=%s AND tick >= %s ORDER BY tick
    """, (room, LAST_TIP)).fetchall()
    p(f"-- {room} n={len(rows)}")
    if not rows:
        continue
    stor = [r[2] for r in rows if r[2] is not None]
    p("  stor first", rows[0][0], rows[0][2], "last", rows[-1][0], rows[-1][2],
      "min", min(stor) if stor else None, "max", max(stor) if stor else None,
      "n_under15k", sum(1 for s in stor if s < 15000), "n", len(stor))
    # print every ~20th and any under 15k edges
    prev_under = None
    for i, r in enumerate(rows):
        under = r[2] is not None and r[2] < 15000
        edge = prev_under is not None and under != prev_under
        if i == 0 or i == len(rows)-1 or i % 6 == 0 or edge or (r[6] and r[6] > 0):
            p(" ", r)
        prev_under = under

p("=== W45N7 names 84372800-84373720 ===")
rows = c.execute("""
SELECT creep, role, min(tick), max(tick), count(*), min(hits), max(hits), min(x), max(x), min(y), max(y)
FROM creep_ticks
WHERE room='W45N7' AND tick BETWEEN 84372800 AND 84373720
GROUP BY creep, role
ORDER BY min(tick), creep
""").fetchall()
for r in rows:
    p(r)

p("=== defender84372817 compact path ===")
rows = c.execute("""
SELECT tick, room, x, y, hits, store, state, role
FROM creep_ticks WHERE creep='defender84372817' ORDER BY tick
""").fetchall()
p("rows", len(rows))
if rows:
    p("first", rows[0], "last", rows[-1])
    prev = None
    for r in rows:
        key = (r[1], r[2], r[3], r[4], r[6])
        if key != prev:
            p(" ", r)
            prev = key

p("=== Invader / core-like names in W45N7 since 84372700 ===")
rows = c.execute("""
SELECT creep, role, min(tick), max(tick), count(*), min(hits), max(hits)
FROM creep_ticks
WHERE room='W45N7' AND tick >= 84372700
  AND (creep ILIKE '%invader%' OR creep ILIKE '%core%' OR role ILIKE '%invader%' OR role ILIKE '%core%')
GROUP BY creep, role
ORDER BY min(tick)
""").fetchall()
for r in rows:
    p(r)
# also any hostile-looking (non-our naming)
rows = c.execute("""
SELECT creep, role, min(tick), max(tick), count(*), min(hits), max(hits)
FROM creep_ticks
WHERE room='W45N7' AND tick >= 84372700
GROUP BY creep, role
ORDER BY min(tick)
""").fetchall()
p("-- all W45N7 creeps since 84372700 --")
for r in rows:
    p(r)

p("=== rdef84372551 last changes after 84372900 ===")
rows = c.execute("""
SELECT tick, room, x, y, hits, state FROM creep_ticks
WHERE creep='rdef84372551' AND tick>=84372900 ORDER BY tick
""").fetchall()
p("n", len(rows))
if rows:
    p("first", rows[0], "last", rows[-1])
    prev = None
    changes = []
    for r in rows:
        key = (r[1], r[2], r[3], r[4], r[5])
        if key != prev:
            changes.append(r)
            prev = key
    for r in changes[-40:]:
        p(" ", r)

p("=== w8guard84372832 last changes ===")
rows = c.execute("""
SELECT tick, room, x, y, hits, state FROM creep_ticks
WHERE creep='w8guard84372832' AND tick>=84372800 ORDER BY tick
""").fetchall()
p("n", len(rows))
if rows:
    p("first", rows[0], "last", rows[-1])
    prev = None
    changes = []
    for r in rows:
        key = (r[1], r[2], r[3], r[4], r[5])
        if key != prev:
            changes.append(r)
            prev = key
    for r in changes[-30:]:
        p(" ", r)

p("=== W47N8 hostiles in room_stats since last tip ===")
rows = c.execute("""
SELECT tick, ts, hostiles, storage, cpu FROM room_stats
WHERE room='W47N8' AND tick>=%s AND hostiles>0 ORDER BY tick
""", (LAST_TIP,)).fetchall()
p("hostile samples", len(rows))
for r in rows[:20]:
    p(" ", r)
if len(rows) > 20:
    p(" ...", len(rows)-20, "more; last", rows[-1])

p("=== role presence since last tip (owned critical) ===")
# miners/queens/w8filler/rminer/reserver in creep_ticks
crit = ('miner','queen','wfiller','w8filler','wminer','rminer','reserver','reserve','reserve7')
rows = c.execute("""
SELECT tick, room, role, count(*) FROM creep_ticks
WHERE tick BETWEEN %s AND %s
  AND role IN ('miner','queen','wfiller','wminer','rminer','reserver','reserve','hauler','upgrader','wupgrader','w8filler')
GROUP BY tick, room, role
""", (LAST_TIP, LAST_TIP+20000)).fetchall()
# too big maybe - do gaps per role
for role, rooms in [
    ('miner', ('W46N8',)),
    ('queen', ('W46N8',)),
    ('wminer', ('W47N8',)),
    ('wfiller', ('W47N8',)),
    ('rminer', ('W45N8','W45N7','W47N7')),
    ('reserver', ('W45N8','W45N7','W47N7')),
    ('reserve', ('W45N8','W45N7','W47N7')),
]:
    for room in rooms:
        q = c.execute("""
            SELECT min(tick), max(tick), count(DISTINCT tick),
                   count(DISTINCT tick) FILTER (WHERE n=0)
            FROM (
              SELECT t.tick, count(c.creep) n
              FROM generate_series(%s, (SELECT max(tick) FROM creep_ticks WHERE room=%s), 1) t(tick)
              LEFT JOIN creep_ticks c ON c.room=%s AND c.tick=t.tick AND c.role=%s
              GROUP BY t.tick
            ) s
        """, (LAST_TIP, room, room, role)).fetchone()
        # this generate_series might be heavy; skip if slow
        p("role", role, room, q)

p("done")
