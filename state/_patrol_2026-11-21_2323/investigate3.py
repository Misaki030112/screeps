#!/usr/bin/env python3
import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db
c = db.connect()

print("=== storage just before first freeze ===")
for room in ("W46N8","W47N8"):
    rows = c.execute("""
        SELECT tick, ts, storage, progress, energy
        FROM room_stats WHERE room=%s AND tick BETWEEN 84401280 AND 84401320
        ORDER BY tick
    """, (room,)).fetchall()
    for r in rows:
        print(room, r)

print("=== upgrader lifetimes this hour ===")
rows = c.execute("""
    SELECT creep, min(tick), max(tick), count(*), min(hits), max(hits)
    FROM creep_ticks
    WHERE creep LIKE 'upgrader%' AND tick BETWEEN 84401080 AND 84402010
    GROUP BY creep ORDER BY min(tick)
""").fetchall()
for r in rows:
    print("UPG", r)

print("=== w8upgrader lifetimes ===")
rows = c.execute("""
    SELECT creep, min(tick), max(tick), count(*)
    FROM creep_ticks
    WHERE creep LIKE 'w8upgrader%' AND tick BETWEEN 84401080 AND 84402010
    GROUP BY creep ORDER BY min(tick)
""").fetchall()
for r in rows:
    print("W8UP", r)

print("=== w8guard84401622 trajectory ===")
rows = c.execute("""
    SELECT tick, room, x, y, hits, store, state
    FROM creep_ticks
    WHERE creep='w8guard84401622'
    ORDER BY tick
""").fetchall()
print("n", len(rows))
if rows:
    print("first", rows[0])
    print("last", rows[-1])
    hits=sorted(set(r[4] for r in rows))
    print("hits unique", hits)
    print("rooms", set(r[1] for r in rows))
    prev=None
    for r in rows:
        key=(r[1], r[4], (r[2]//5, r[3]//5))
        if key!=prev and (prev is None or key[0]!=prev[0] or key[1]!=prev[1]):
            print("change", r)
            prev=key
        elif r[0] % 20 == 0:
            print("  ", r)

print("=== rdef84400224 span ===")
print(c.execute("""
    SELECT min(tick), max(tick), count(*), min(hits), max(hits)
    FROM creep_ticks WHERE creep='rdef84400224'
""").fetchone())
print("last", c.execute("""
    SELECT tick, room, x, y, hits FROM creep_ticks
    WHERE creep='rdef84400224' ORDER BY tick DESC LIMIT 5
""").fetchall())

print("=== invader/guard/def names since 84401000 ===")
rows = c.execute("""
    SELECT creep, room, min(tick), max(tick), count(*), min(hits), max(hits)
    FROM creep_ticks
    WHERE tick>=84401000 AND (
        creep ILIKE '%invader%' OR creep ILIKE '%guard%' OR creep ILIKE '%def%'
        OR creep ILIKE '%core%'
    )
    GROUP BY creep, room ORDER BY min(tick)
""").fetchall()
for r in rows:
    print("N", r)
