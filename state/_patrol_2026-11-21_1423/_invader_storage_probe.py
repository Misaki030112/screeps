#!/usr/bin/env python3
import sys, json
from collections import defaultdict
sys.path.insert(0, "/workspace/screeps/tools")
import db
c = db.connect()

print("=== incidents since 84394300 ===")
rows = c.execute("SELECT * FROM incidents WHERE tick>=84394300 ORDER BY tick").fetchall()
print("n", len(rows))
for r in rows:
    print(r)

print("=== events non-watch since 84394600 ===")
try:
    cols = c.execute("SELECT * FROM events LIMIT 0")
except Exception:
    pass
# discover columns
try:
    rows = c.execute("SELECT * FROM events WHERE tick>=84394600 AND coalesce(kind, typ, type, '') <> 'watch' ORDER BY tick LIMIT 80").fetchall()
    print("n", len(rows))
    for r in rows:
        print(r)
except Exception as e:
    print("filter failed", e)
    try:
        rows = c.execute("SELECT * FROM events WHERE tick>=84394600 ORDER BY tick LIMIT 5").fetchall()
        print("sample", rows[:2])
    except Exception as e2:
        print("events fail", e2)

print("=== defenders/guards since 84394330 ===")
rows = c.execute("""
SELECT creep, role, min(tick), max(tick), count(*),
       min(hits), max(hits),
       (array_agg(room ORDER BY tick))[1] as first_room,
       (array_agg(x ORDER BY tick))[1], (array_agg(y ORDER BY tick))[1],
       (array_agg(room ORDER BY tick DESC))[1] as last_room,
       (array_agg(x ORDER BY tick DESC))[1], (array_agg(y ORDER BY tick DESC))[1]
FROM creep_ticks
WHERE tick>=84394330 AND (role ILIKE '%def%' OR role ILIKE '%guard%' OR creep ILIKE '%def%' OR creep ILIKE '%guard%' OR creep ILIKE '%rdef%')
GROUP BY creep, role
ORDER BY min(tick)
""").fetchall()
for r in rows:
    print(r)

print("=== all W47N7 creeps 84394700..84395080 ===")
rows = c.execute("""
SELECT creep, role, min(tick), max(tick), count(*), min(hits), max(hits)
FROM creep_ticks
WHERE room='W47N7' AND tick BETWEEN 84394700 AND 84395080
GROUP BY creep, role
ORDER BY min(tick)
""").fetchall()
for r in rows:
    print(r)

print("=== storage W46N8/W47N8 since LAST_TIP 84394330 ===")
for room in ("W46N8", "W47N8"):
    mn, mx, n, n15, n25, n40 = c.execute("""
      SELECT min(storage), max(storage), count(*),
             count(*) FILTER (WHERE storage<15000),
             count(*) FILTER (WHERE storage<25000),
             count(*) FILTER (WHERE storage>=40000)
      FROM room_stats WHERE room=%s AND tick>=84394330
    """, (room,)).fetchone()
    mint = c.execute("SELECT tick, ts, storage FROM room_stats WHERE room=%s AND tick>=84394330 AND storage=%s ORDER BY tick LIMIT 1", (room, mn)).fetchone()
    maxt = c.execute("SELECT tick, ts, storage FROM room_stats WHERE room=%s AND tick>=84394330 AND storage=%s ORDER BY tick LIMIT 1", (room, mx)).fetchone()
    print(room, "min", mn, "at", mint, "max", mx, "at", maxt, "n", n, "under15k", n15, "under25k", n25, "ge40k", n40)

print("=== last 20 room_stats both ===")
rows = c.execute("""
SELECT a.tick, a.ts, a.storage AS h, b.storage AS w, a.progress AS hp, b.progress AS wp, a.cpu, a.bucket
FROM room_stats a JOIN room_stats b ON a.tick=b.tick AND b.room='W47N8'
WHERE a.room='W46N8' AND a.tick>=84395100
ORDER BY a.tick
""").fetchall()
for r in rows:
    print(r)

print("=== W46N8 crossings under 15k since LAST_TIP ===")
rows = c.execute("""
SELECT tick, ts, storage FROM room_stats
WHERE room='W46N8' AND tick>=84394300
ORDER BY tick
""").fetchall()
prev = None
for tick, ts, stor in rows:
    if stor is None:
        continue
    if prev is not None:
        if prev >= 15000 and stor < 15000:
            print("CROSS UNDER", tick, ts, stor)
        if prev < 15000 and stor >= 15000:
            print("CROSS OVER", tick, ts, stor)
    prev = stor
if rows:
    print("first", rows[0], "last", rows[-1])
