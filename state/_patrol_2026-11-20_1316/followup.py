#!/usr/bin/env python3
import sys
from collections import Counter, defaultdict
sys.path.insert(0, "/workspace/screeps/tools")
import db

c = db.connect()
def p(*a):
    print(*a, flush=True)

p("=== W47 storage 40k lock / 3h-24h max ===")
for hours in (3, 6, 8, 12, 24):
    lo = 84373750 - int(hours * 3600 / 4.19)
    row = c.execute(
        """
        SELECT max(storage), min(storage), count(*) FILTER (WHERE storage>=40000), count(*)
        FROM room_stats WHERE room='W47N8' AND tick>=%s
        """,
        (lo,),
    ).fetchone()
    mx = c.execute(
        """
        SELECT tick, ts, storage FROM room_stats
        WHERE room='W47N8' AND tick>=%s ORDER BY storage DESC NULLS LAST LIMIT 1
        """,
        (lo,),
    ).fetchone()
    p(" ", hours, "h max", mx, "agg", row)

p("=== w8miners last 800t ===")
rows = c.execute(
    """
SELECT creep, role, room, min(tick), max(tick), count(*), min(x), max(x), min(y), max(y), min(hits), max(hits)
FROM creep_ticks
WHERE creep LIKE 'w8miner%' AND tick>=84372900
GROUP BY creep, role, room
ORDER BY min(tick), creep
"""
).fetchall()
for r in rows:
    p(r)

p("=== w8miner compact states ===")
names = [r[0] for r in rows]
for name in sorted(set(names)):
    rs = c.execute(
        """
        SELECT tick, room, x, y, hits, store, state FROM creep_ticks
        WHERE creep=%s AND tick>=84372900 ORDER BY tick
        """,
        (name,),
    ).fetchall()
    p(name, "n", len(rs))
    if not rs:
        continue
    p(" first", rs[0], "last", rs[-1])
    prev = None
    ch = []
    for r in rs:
        key = (r[1], r[2], r[3], r[6])
        if key != prev:
            ch.append(r)
            prev = key
    p(" changes", len(ch), "states", Counter(r[6] for r in rs))
    for r in ch[:10]:
        p("  ", r)
    if len(ch) > 30:
        p("  ...")
    for r in ch[-15:]:
        p("  ", r)

p("=== defender84372817 room enters ===")
rows = c.execute(
    """
SELECT tick, room, x, y, state FROM creep_ticks
WHERE creep='defender84372817' ORDER BY tick
"""
).fetchall()
p("n", len(rows), "first", rows[0] if rows else None, "last", rows[-1] if rows else None)
prev_room = None
for r in rows:
    if r[1] != prev_room:
        p(" ENTER", r)
        prev_room = r[1]
rows7 = [r for r in rows if r[1] == "W45N7"]
p("W45N7 ticks", len(rows7), "first", rows7[0] if rows7 else None, "last", rows7[-1] if rows7 else None)
if rows7:
    p("W45N7 pos", Counter((r[2], r[3]) for r in rows7))
    p("W45N7 states", Counter(r[4] for r in rows7))
row = c.execute("SELECT max(tick), count(*) FROM creep_ticks WHERE creep='defender84372817'").fetchone()
p("defender max/count", row)
rows = c.execute(
    """
SELECT creep, min(tick), max(tick), count(*) FROM creep_ticks
WHERE creep LIKE 'defender%' AND tick>=84372800 GROUP BY creep
"""
).fetchall()
p("defenders", rows)

p("=== W47N7 rminers this hour ===")
rows = c.execute(
    """
SELECT creep, role, room, min(tick), max(tick), count(*)
FROM creep_ticks
WHERE creep LIKE 'rminer%' AND tick BETWEEN 84372970 AND 84373780
GROUP BY creep, role, room
ORDER BY min(tick)
"""
).fetchall()
for r in rows:
    p(r)
rows = c.execute(
    """
SELECT role, count(DISTINCT creep), min(tick), max(tick), count(DISTINCT tick)
FROM creep_ticks WHERE room='W47N7' AND tick BETWEEN 84372970 AND 84373780
GROUP BY role ORDER BY role
"""
).fetchall()
p("W47N7 roles", rows)

p("=== rminer84372704 where ===")
rows = c.execute(
    """
SELECT room, min(tick), max(tick), count(*), min(x), max(x), min(y), max(y)
FROM creep_ticks WHERE creep='rminer84372704' AND tick>=84372900
GROUP BY room
"""
).fetchall()
p(rows)
rs = c.execute(
    """
SELECT tick, room, x, y, state, store FROM creep_ticks
WHERE creep='rminer84372704' AND tick>=84372900 ORDER BY tick
"""
).fetchall()
p("n", len(rs), "first", rs[0] if rs else None, "last", rs[-1] if rs else None)
prev = None
ch = []
for r in rs:
    key = (r[1], r[2], r[3], r[4])
    if key != prev:
        ch.append(r)
        prev = key
for r in ch[:8] + ch[-12:]:
    p(" ", r)

p("=== w8upgrader names ===")
rows = c.execute(
    """
SELECT creep, min(tick), max(tick), count(*) FROM creep_ticks
WHERE creep LIKE 'w8upgrader%' AND tick>=84372900
GROUP BY creep ORDER BY min(tick)
"""
).fetchall()
for r in rows:
    p(r)

p("=== incidents tables ===")
tabs = c.execute(
    """
SELECT table_name FROM information_schema.tables
WHERE table_schema='public' AND (table_name ILIKE '%incident%' OR table_name ILIKE '%alert%' OR table_name ILIKE '%event%')
ORDER BY 1
"""
).fetchall()
p("tables", tabs)

p("=== rhauler84372786 rooms ===")
rows = c.execute(
    """
SELECT room, min(tick), max(tick), count(*), min(x), max(x), min(y), max(y)
FROM creep_ticks WHERE creep='rhauler84372786' AND tick>=84372900
GROUP BY room
"""
).fetchall()
p(rows)

p("=== listener rot / freeze official fill ===")
# STATS gap 84373281..84373469
for room in ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7"):
    row = c.execute(
        """
        SELECT count(DISTINCT tick), min(tick), max(tick)
        FROM creep_ticks WHERE room=%s AND tick BETWEEN 84373281 AND 84373469
        """,
        (room,),
    ).fetchone()
    p("freeze fill", room, row, "want 189")

p("done")
