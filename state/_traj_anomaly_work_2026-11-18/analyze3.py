#!/usr/bin/env python3
import os, sys
sys.path.insert(0, "/workspace/screeps/tools")
import db
OUT = "/workspace/screeps/state/_traj_anomaly_work_2026-11-18"
YIELD_POST = 84321282
YIELD_HUB  = 84324673

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

print("=== 5. south-road long bounce episodes ===", flush=True)
cols, rows = q("""
WITH w AS (
  SELECT creep, role, tick, x, y, store, ts,
         lag(tick) OVER p AS pt, lag(x) OVER p AS px, lag(y) OVER p AS py,
         lag(tick,2) OVER p AS pt2, lag(x,2) OVER p AS px2, lag(y,2) OVER p AS py2
  FROM creep_ticks
  WHERE room='W47N8' AND ts >= now() - interval '8 days'
    AND x BETWEEN 26 AND 32 AND y BETWEEN 33 AND 36
    AND (state IS DISTINCT FROM 'spawning')
  WINDOW p AS (PARTITION BY creep ORDER BY tick)
),
b AS (
  SELECT creep, role, tick, ts, store,
    CASE WHEN (x,y) <= (px,py)
      THEN x::text||','||y::text||'↔'||px::text||','||py::text
      ELSE px::text||','||py::text||'↔'||x::text||','||y::text
    END AS pair
  FROM w
  WHERE tick = pt + 1 AND pt = pt2 + 1
    AND x = px2 AND y = py2
    AND (x,y) IS DISTINCT FROM (px,py)
    AND CASE WHEN (x,y) <= (px,py)
      THEN x::text||','||y::text||'↔'||px::text||','||py::text
      ELSE px::text||','||py::text||'↔'||x::text||','||y::text
    END IN ('28,35↔29,35','27,35↔28,35','29,35↔30,35')
),
e AS (
  SELECT *, tick - row_number() OVER (PARTITION BY creep, pair ORDER BY tick) AS grp FROM b
),
eps AS (
  SELECT creep, role, pair, min(tick) t0, max(tick) t1, count(*) n,
         min(ts) AT TIME ZONE 'Asia/Hong_Kong' AS t0_hkt,
         max(store) max_store, min(store) min_store
  FROM e GROUP BY creep, role, pair, grp
)
SELECT * FROM eps WHERE n >= 6
ORDER BY t0
""")
dump("05_southroad_long_episodes.txt", fmt(cols, rows))

print("=== 6. filler bounce vs store/codes last 24h sample ===", flush=True)
# For recent fillers, bounce ticks and concurrent cpu codes + store
cols, rows = q("""
WITH recent AS (
  SELECT creep, role, tick, x, y, store, ts,
         lag(tick) OVER p AS pt, lag(x) OVER p AS px, lag(y) OVER p AS py,
         lag(tick,2) OVER p AS pt2, lag(x,2) OVER p AS px2, lag(y,2) OVER p AS py2
  FROM creep_ticks
  WHERE room='W47N8' AND role='wfiller' AND ts >= now() - interval '6 hours'
    AND (state IS DISTINCT FROM 'spawning')
  WINDOW p AS (PARTITION BY creep ORDER BY tick)
),
b AS (
  SELECT creep, tick, x, y, px, py, store,
    CASE WHEN (x,y) <= (px,py)
      THEN x::text||','||y::text||'↔'||px::text||','||py::text
      ELSE px::text||','||py::text||'↔'||x::text||','||y::text
    END AS pair
  FROM recent
  WHERE tick = pt + 1 AND pt = pt2 + 1 AND x = px2 AND y = py2 AND (x,y) IS DISTINCT FROM (px,py)
)
SELECT pair,
  count(*) bounces,
  round(avg(store)::numeric,1) avg_store,
  min(store) min_store, max(store) max_store,
  count(*) FILTER (WHERE store=0) empty,
  count(*) FILTER (WHERE store>=1000) high
FROM b
GROUP BY pair
ORDER BY bounces DESC
LIMIT 20
""")
dump("06_filler_bounce_store_6h.txt", fmt(cols, rows))

# codes around filler during last 6h
cols, rows = q("""
SELECT
  sum(length(codes)) AS ticks,
  sum(length(regexp_replace(coalesce(codes,''), '[^f]', '', 'g'))) AS target_full,
  sum(length(regexp_replace(coalesce(codes,''), '[^w]', '', 'g'))) AS working,
  sum(length(regexp_replace(coalesce(codes,''), '[^m]', '', 'g'))) AS moving,
  sum(length(regexp_replace(coalesce(codes,''), '[^n]', '', 'g'))) AS no_task,
  sum(length(regexp_replace(coalesce(codes,''), '[^p]', '', 'g'))) AS waiting_pickup,
  sum(length(regexp_replace(coalesce(codes,''), '[^q]', '', 'g'))) AS queue_blocked,
  sum(length(regexp_replace(coalesce(codes,''), '[^e]', '', 'g'))) AS source_empty,
  sum(repaths) repaths, sum(stuck) stuck, sum(fails) fails,
  round(avg(cpu_ms)::numeric,3) avg_cpu, max(cpu_max) cpu_max,
  count(DISTINCT creep) creeps
FROM creep_cpu
WHERE role='wfiller' AND ts >= now() - interval '24 hours'
""")
dump("06_filler_codes_24h.txt", fmt(cols, rows))

print("=== 7. idle codes by role 72h ===", flush=True)
cols, rows = q("""
SELECT role,
  sum(length(codes)) AS ticks,
  sum(length(regexp_replace(coalesce(codes,''), '[^w]', '', 'g'))) AS working,
  sum(length(regexp_replace(coalesce(codes,''), '[^m]', '', 'g'))) AS moving,
  sum(length(regexp_replace(coalesce(codes,''), '[^s]', '', 'g'))) AS spawning,
  sum(length(regexp_replace(coalesce(codes,''), '[^e]', '', 'g'))) AS source_empty,
  sum(length(regexp_replace(coalesce(codes,''), '[^p]', '', 'g'))) AS waiting_pickup,
  sum(length(regexp_replace(coalesce(codes,''), '[^u]', '', 'g'))) AS waiting_feed,
  sum(length(regexp_replace(coalesce(codes,''), '[^f]', '', 'g'))) AS target_full,
  sum(length(regexp_replace(coalesce(codes,''), '[^q]', '', 'g'))) AS queue_blocked,
  sum(length(regexp_replace(coalesce(codes,''), '[^n]', '', 'g'))) AS no_task,
  sum(length(regexp_replace(coalesce(codes,''), '[^t]', '', 'g'))) AS parked_threat,
  sum(length(regexp_replace(coalesce(codes,''), '[^r]', '', 'g'))) AS renewing,
  sum(repaths) repaths, sum(fails) fails, sum(stuck) stuck_ev,
  round((sum(cpu_ms)/nullif(sum(length(codes)),0))::numeric,4) cpu_per_tick
FROM creep_cpu
WHERE ts >= now() - interval '72 hours'
GROUP BY role
ORDER BY ticks DESC
""")
dump("07_idle_codes_by_role_72h.txt", fmt(cols, rows))

print("=== 8. termPark: home hauler at/near terminal 35,31 ===", flush=True)
# Hauler (home) positions near terminal 35,31 or storage 37,31, store changes
cols, rows = q("""
WITH h AS (
  SELECT creep, role, tick, x, y, store, state, ts,
         lag(store) OVER p AS ps, lag(x) OVER p AS px, lag(y) OVER p AS py, lag(tick) OVER p AS pt,
         lead(store) OVER p AS ns, lead(tick) OVER p AS nt, lead(x) OVER p AS nx, lead(y) OVER p AS ny
  FROM creep_ticks
  WHERE room='W46N8' AND role IN ('hauler')
    AND ts >= now() - interval '72 hours'
    AND (state IS DISTINCT FROM 'spawning')
  WINDOW p AS (PARTITION BY creep ORDER BY tick)
)
-- withdraw/transfer events near terminal (35,31) or storage (37,31): store changes while adjacent
SELECT
  CASE
    WHEN (x BETWEEN 34 AND 36 AND y BETWEEN 30 AND 32) THEN 'near_term_35,31'
    WHEN (x BETWEEN 36 AND 38 AND y BETWEEN 30 AND 32) THEN 'near_stor_37,31'
    ELSE 'other'
  END AS zone,
  count(*) FILTER (WHERE store IS DISTINCT FROM ps AND pt=tick-1) AS store_changes,
  count(*) FILTER (WHERE store IS DISTINCT FROM ps AND pt=tick-1 AND store > ps) AS pickups,
  count(*) FILTER (WHERE store IS DISTINCT FROM ps AND pt=tick-1 AND store < ps) AS drops,
  count(*) FILTER (WHERE store IS DISTINCT FROM ps AND pt=tick-1 AND store > ps AND store < 640) AS pickup_lt80pct800,
  count(*) FILTER (WHERE store IS DISTINCT FROM ps AND pt=tick-1 AND store > ps AND store >= 640) AS pickup_ge80pct800,
  round(avg(store) FILTER (WHERE store IS DISTINCT FROM ps AND pt=tick-1 AND store > ps)::numeric,1) AS avg_after_pickup,
  min(store) FILTER (WHERE store IS DISTINCT FROM ps AND pt=tick-1 AND store > ps) AS min_after_pickup,
  max(store) FILTER (WHERE store IS DISTINCT FROM ps AND pt=tick-1 AND store > ps) AS max_after_pickup
FROM h
GROUP BY 1
ORDER BY 1
""")
dump("08_termpark_pickup_sizes_72h.txt", fmt(cols, rows))

# Detailed pickup events near terminal with size
cols, rows = q("""
WITH h AS (
  SELECT creep, tick, x, y, store, ts,
         lag(store) OVER p AS ps, lag(tick) OVER p AS pt, lag(x) OVER p AS px, lag(y) OVER p AS py
  FROM creep_ticks
  WHERE room='W46N8' AND role='hauler'
    AND ts >= now() - interval '72 hours'
    AND (state IS DISTINCT FROM 'spawning')
  WINDOW p AS (PARTITION BY creep ORDER BY tick)
)
SELECT creep, tick, ts AT TIME ZONE 'Asia/Hong_Kong' AS hkt, x, y, px, py, ps AS store_before, store AS store_after, (store-ps) AS delta
FROM h
WHERE pt = tick-1 AND store > ps
  AND x BETWEEN 34 AND 38 AND y BETWEEN 30 AND 32
ORDER BY tick
""")
dump("08_termpark_pickup_events_72h.txt", fmt(cols, rows))

print("done 5-8", flush=True)
