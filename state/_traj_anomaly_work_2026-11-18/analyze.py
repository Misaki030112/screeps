#!/usr/bin/env python3
"""Trajectory anomaly catalog analysis. Analysis only; no game writes."""
import os, sys, json
from collections import defaultdict
from datetime import datetime, timezone, timedelta
sys.path.insert(0, "/workspace/screeps/tools")
import db

OUT = "/workspace/screeps/state/_traj_anomaly_work_2026-11-18"
HKT = timezone(timedelta(hours=8))
# Key deploys
YIELD_POST = 84321282   # c6d43491 PR 61
YIELD_HUB  = 84324673   # 8daf0494 occupied-hub bypass
HAULER16   = 84302295   # 3cf63791 16C8M home hauler

def dump(name, text):
    path = os.path.join(OUT, name)
    with open(path, "w") as f:
        f.write(text if text.endswith("\n") else text + "\n")
    print(f"wrote {path} ({len(text)} chars)", flush=True)

def q(sql):
    c = db.connect()
    cur = c.execute(sql)
    cols = [d.name for d in cur.description] if cur.description else []
    rows = cur.fetchall()
    return cols, rows

def fmt(cols, rows, limit=None):
    if not cols:
        return "(no columns)\n"
    lines = ["\t".join(cols)]
    for i, r in enumerate(rows):
        if limit is not None and i >= limit:
            lines.append(f"... {len(rows)-limit} more rows")
            break
        lines.append("\t".join("" if v is None else str(v) for v in r))
    return "\n".join(lines) + "\n"

print("=== 1. coverage + gaps ===", flush=True)
cols, rows = q("""
WITH rooms AS (SELECT unnest(ARRAY['W46N8','W47N8','W45N8','W45N7','W47N7']) AS room)
SELECT r.room,
  (SELECT count(*) FROM creep_ticks t WHERE t.room=r.room) AS tick_rows,
  (SELECT min(tick) FROM creep_ticks t WHERE t.room=r.room) AS min_tick,
  (SELECT max(tick) FROM creep_ticks t WHERE t.room=r.room) AS max_tick,
  (SELECT min(ts) AT TIME ZONE 'Asia/Hong_Kong' FROM creep_ticks t WHERE t.room=r.room) AS min_hkt,
  (SELECT max(ts) AT TIME ZONE 'Asia/Hong_Kong' FROM creep_ticks t WHERE t.room=r.room) AS max_hkt,
  (SELECT count(DISTINCT tick) FROM creep_ticks t WHERE t.room=r.room) AS distinct_ticks,
  (SELECT count(DISTINCT creep) FROM creep_ticks t WHERE t.room=r.room) AS creeps
FROM rooms r ORDER BY r.room
""")
dump("01_coverage_rooms.txt", fmt(cols, rows))

# Hourly coverage last 72h
cols, rows = q("""
SELECT room,
  date_trunc('hour', ts AT TIME ZONE 'Asia/Hong_Kong') AS hour_hkt,
  count(*) AS rows,
  count(DISTINCT tick) AS ticks,
  min(tick) AS t0, max(tick) AS t1
FROM creep_ticks
WHERE ts >= now() - interval '72 hours'
  AND room IN ('W46N8','W47N8','W45N8','W45N7','W47N7')
GROUP BY 1,2
ORDER BY 2,1
""")
dump("01_coverage_72h_hourly.txt", fmt(cols, rows))

# room_stats vs creep_ticks last 72h (freeze gaps)
cols, rows = q("""
SELECT
  'creep_ticks' AS src, count(*) rows, count(DISTINCT tick) ticks,
  min(tick) t0, max(tick) t1,
  min(ts) AT TIME ZONE 'Asia/Hong_Kong' min_hkt,
  max(ts) AT TIME ZONE 'Asia/Hong_Kong' max_hkt
FROM creep_ticks WHERE ts >= now() - interval '72 hours'
UNION ALL
SELECT 'room_stats', count(*), count(DISTINCT tick), min(tick), max(tick),
  min(ts) AT TIME ZONE 'Asia/Hong_Kong', max(ts) AT TIME ZONE 'Asia/Hong_Kong'
FROM room_stats WHERE ts >= now() - interval '72 hours'
UNION ALL
SELECT 'creep_cpu', count(*), count(DISTINCT tick), min(tick), max(tick),
  min(ts) AT TIME ZONE 'Asia/Hong_Kong', max(ts) AT TIME ZONE 'Asia/Hong_Kong'
FROM creep_cpu WHERE ts >= now() - interval '72 hours'
UNION ALL
SELECT 'path_arrivals', count(*), count(DISTINCT tick), min(tick), max(tick),
  min(ts) AT TIME ZONE 'Asia/Hong_Kong', max(ts) AT TIME ZONE 'Asia/Hong_Kong'
FROM path_arrivals WHERE ts >= now() - interval '72 hours'
""")
dump("01_coverage_72h_tables.txt", fmt(cols, rows))

# room_stats gaps last 72h (box freezes): gaps of > 30 ticks between consecutive samples per room
cols, rows = q("""
WITH s AS (
  SELECT room, tick, ts,
         lag(tick) OVER (PARTITION BY room ORDER BY tick) AS pt,
         lag(ts) OVER (PARTITION BY room ORDER BY tick) AS pts
  FROM room_stats
  WHERE ts >= now() - interval '72 hours'
    AND room IN ('W46N8','W47N8')
)
SELECT room, pt AS gap_from_tick, tick AS gap_to_tick, (tick-pt-1) AS missing_ticks,
  pts AT TIME ZONE 'Asia/Hong_Kong' AS from_hkt,
  ts AT TIME ZONE 'Asia/Hong_Kong' AS to_hkt
FROM s
WHERE pt IS NOT NULL AND tick-pt > 40
ORDER BY pt
""")
dump("01_roomstats_gaps_72h.txt", fmt(cols, rows))

print("=== 2. bounce pairs 72h ===", flush=True)
cols, rows = q("""
WITH w AS (
  SELECT creep, role, tick, room, x, y, store,
         lag(tick) OVER p AS pt, lag(room) OVER p AS pr, lag(x) OVER p AS px, lag(y) OVER p AS py,
         lag(tick,2) OVER p AS pt2, lag(room,2) OVER p AS pr2, lag(x,2) OVER p AS px2, lag(y,2) OVER p AS py2
  FROM creep_ticks
  WHERE ts >= now() - interval '72 hours'
    AND (state IS DISTINCT FROM 'spawning')
  WINDOW p AS (PARTITION BY creep ORDER BY tick)
),
b AS (
  SELECT creep, role, tick, room, x, y, px, py, store,
    CASE WHEN (x,y) <= (px,py)
      THEN x::text||','||y::text||'↔'||px::text||','||py::text
      ELSE px::text||','||py::text||'↔'||x::text||','||y::text
    END AS pair
  FROM w
  WHERE tick = pt + 1 AND pt = pt2 + 1
    AND room = pr AND room = pr2
    AND x = px2 AND y = py2
    AND (x,y) IS DISTINCT FROM (px,py)
)
SELECT room, role, pair, count(*) AS bounces, count(DISTINCT creep) AS creeps,
       min(tick) AS t0, max(tick) AS t1
FROM b
GROUP BY room, role, pair
HAVING count(*) >= 8
ORDER BY bounces DESC
LIMIT 120
""")
dump("02_bounce_pairs_72h.txt", fmt(cols, rows))

print("=== 2b. bounce pairs since Nov 10 (dense) top ===", flush=True)
cols, rows = q("""
WITH w AS (
  SELECT creep, role, tick, room, x, y,
         lag(tick) OVER p AS pt, lag(room) OVER p AS pr, lag(x) OVER p AS px, lag(y) OVER p AS py,
         lag(tick,2) OVER p AS pt2, lag(room,2) OVER p AS pr2, lag(x,2) OVER p AS px2, lag(y,2) OVER p AS py2
  FROM creep_ticks
  WHERE tick >= 84177901  -- W47N7 start / dense coverage ~ Nov 10
    AND (state IS DISTINCT FROM 'spawning')
  WINDOW p AS (PARTITION BY creep ORDER BY tick)
),
b AS (
  SELECT creep, role, tick, room,
    CASE WHEN (x,y) <= (px,py)
      THEN x::text||','||y::text||'↔'||px::text||','||py::text
      ELSE px::text||','||py::text||'↔'||x::text||','||y::text
    END AS pair
  FROM w
  WHERE tick = pt + 1 AND pt = pt2 + 1
    AND room = pr AND room = pr2
    AND x = px2 AND y = py2
    AND (x,y) IS DISTINCT FROM (px,py)
)
SELECT room, role, pair, count(*) AS bounces, count(DISTINCT creep) AS creeps,
       min(tick) AS t0, max(tick) AS t1
FROM b
GROUP BY room, role, pair
HAVING count(*) >= 30
ORDER BY bounces DESC
LIMIT 150
""")
dump("02_bounce_pairs_since_nov10.txt", fmt(cols, rows))

print("done phase 1-2", flush=True)
