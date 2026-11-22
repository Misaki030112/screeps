#!/usr/bin/env python3
import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db
c = db.connect()
print("=== freshness ===")
for table in ("room_stats", "creep_ticks", "creep_cpu", "path_arrivals"):
    try:
        row = c.execute(
            f"SELECT min(tick), max(tick), max(ts), now()-max(ts), count(*) FROM {table}"
        ).fetchone()
        print(table, row)
    except Exception as e:
        print(table, "ERR", e)

print("\n=== W45N7 defender-like rows 84403400..84404400 ===")
rows = c.execute(
    """
  SELECT tick, name, role, x, y, hits, energy, spawning
  FROM creep_ticks
  WHERE room='W45N7' AND tick BETWEEN 84403400 AND 84404400
    AND (name ILIKE '%def%' OR name ILIKE '%guard%' OR COALESCE(role,'') ILIKE '%def%'
         OR COALESCE(role,'') ILIKE '%guard%' OR name='defender84403448')
  ORDER BY tick, name
"""
).fetchall()
print("defender-like rows", len(rows))
from collections import defaultdict
by = defaultdict(list)
for r in rows:
    by[r[1]].append(r)
for n, rs in by.items():
    print(f"  {n} n={len(rs)} first={rs[0]} last={rs[-1]}")

print("\n=== W45N7 distinct ticks by 20-tick bucket 84403401..84404300 ===")
cov = c.execute(
    """
  SELECT (tick/20)*20 AS b, count(DISTINCT tick) AS dt, count(*) AS rows
  FROM creep_ticks
  WHERE room='W45N7' AND tick BETWEEN 84403401 AND 84404300
  GROUP BY 1 ORDER BY 1
"""
).fetchall()
for r in cov:
    print(r)

print("\n=== related tables ===")
for t in c.execute(
    "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename ~ 'incid|threat|hostil|core|pause'"
).fetchall():
    print("table", t[0])
