#!/usr/bin/env python3
import sys
from collections import defaultdict
sys.path.insert(0, "/workspace/screeps/tools")
import db
c = db.connect()

print("=== 01:18 freeze official fill STATS 84404311..84404369 (59t) ===")
for room in ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7"):
    n = c.execute(
        "SELECT count(DISTINCT tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN 84404311 AND 84404369",
        (room,),
    ).fetchone()[0]
    print(room, f"{n}/59")

print()
print("=== W45N7@84404300 coverage ===")
for room in ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7"):
    row = c.execute(
        "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN 84404301 AND 84404400",
        (room,),
    ).fetchone()
    print(room, row)

print()
print("=== defender84403448 path (compressed) ===")
rows = c.execute(
    """
  SELECT tick, room, x, y, hits, store, state
  FROM creep_ticks
  WHERE creep='defender84403448'
  ORDER BY tick
"""
).fetchall()
print("rows", len(rows))
if rows:
    print("first", rows[0], "last", rows[-1])
    prev = None
    for r in rows:
        key = (r[1], r[2], r[3], r[6])
        if prev != key:
            print(r)
            prev = key
    # around kill window
    print("--- 84403800..84403860 ---")
    for r in rows:
        if 84403800 <= r[0] <= 84403860:
            print(r)
    print("--- last 15 ---")
    for r in rows[-15:]:
        print(r)

print()
print("=== later room_stats after TIP 84404430 ===")
for room in ("W46N8", "W47N8"):
    for r in c.execute(
        """
      SELECT tick, ts, progress, storage, cpu, bucket
      FROM room_stats WHERE room=%s AND tick>=84404430 ORDER BY tick
    """,
        (room,),
    ):
        print(room, r)

print()
print("=== listener / freshness now ===")
for table in ("room_stats", "creep_ticks"):
    print(table, c.execute(f"SELECT max(tick), now()-max(ts) FROM {table}").fetchone())
