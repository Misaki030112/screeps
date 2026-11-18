#!/usr/bin/env python3
import os, sys
sys.path.insert(0, "/workspace/screeps/tools")
import db
OUT = "/workspace/screeps/state/_traj_anomaly_work_2026-11-18"

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

print("=== 19. evac miner 84324635 context ===", flush=True)
cols, rows = q("""
SELECT tick, ts AT TIME ZONE 'Asia/Hong_Kong' AS hkt, room, x, y, store, state
FROM creep_ticks
WHERE creep='rminer84324635' AND tick BETWEEN 84324600 AND 84325400
ORDER BY tick
LIMIT 30
""")
dump("19_rminer84324635_head.txt", fmt(cols, rows))

cols, rows = q("""
SELECT room, x, y, count(*) n, min(tick) t0, max(tick) t1
FROM creep_ticks
WHERE creep='rminer84324635'
GROUP BY 1,2,3
ORDER BY n DESC
LIMIT 20
""")
dump("19_rminer84324635_tiles.txt", fmt(cols, rows))

cols, rows = q("""
SELECT tick, ts AT TIME ZONE 'Asia/Hong_Kong' AS hkt, remote, ev, state, from_state, why, inv, def, dur
FROM incidents
WHERE ts >= '2026-11-17 20:00:00+08' AND ts <= '2026-11-18 04:00:00+08'
ORDER BY tick
""")
dump("19_incidents_nov17night.txt", fmt(cols, rows))

print("=== 20. south road Nov 18 05:30-05:50 ===", flush=True)
cols, rows = q("""
WITH w AS (
  SELECT creep, role, tick, x, y, store, ts,
         lag(tick) OVER p AS pt, lag(x) OVER p AS px, lag(y) OVER p AS py,
         lag(tick,2) OVER p AS pt2, lag(x,2) OVER p AS px2, lag(y,2) OVER p AS py2
  FROM creep_ticks
  WHERE room='W47N8' AND ts >= '2026-11-18 05:30:00+08' AND ts < '2026-11-18 06:00:00+08'
    AND x BETWEEN 27 AND 30 AND y=35
    AND (state IS DISTINCT FROM 'spawning')
  WINDOW p AS (PARTITION BY creep ORDER BY tick)
)
SELECT creep, role, tick, ts AT TIME ZONE 'Asia/Hong_Kong' AS hkt, x, y, px, py, store
FROM w
WHERE tick=pt+1 AND pt=pt2+1 AND x=px2 AND y=py2 AND (x,y) IS DISTINCT FROM (px,py)
ORDER BY tick
""")
dump("20_southroad_nov18_0540.txt", fmt(cols, rows))

print("=== 21. path_arrivals high excess 72h ===", flush=True)
cols, rows = q("""
SELECT role,
  count(*) trips,
  round(avg(actual::float/nullif(planned,0))::numeric,2) avg_excess,
  round((percentile_cont(0.5) WITHIN GROUP (ORDER BY actual::float/nullif(planned,0)))::numeric,2) p50,
  round((percentile_cont(0.9) WITHIN GROUP (ORDER BY actual::float/nullif(planned,0)))::numeric,2) p90,
  round(max(actual::float/nullif(planned,0))::numeric,2) max_ex,
  (ARRAY_AGG(creep||' '||target||' p'||planned||' a'||actual||' @'||tick ORDER BY actual::float/nullif(planned,0) DESC))[1] AS worst
FROM path_arrivals
WHERE ts >= now() - interval '72 hours' AND planned > 0
GROUP BY role
ORDER BY avg_excess DESC
""")
dump("21_path_arrivals_72h.txt", fmt(cols, rows))

print("=== 22. official-history ghosts: expired wupgrader at 12,25 ===", flush=True)
# creeps whose last ticks sit at upgrade stands after a gap, or same creep after likely death
cols, rows = q("""
WITH u AS (
  SELECT creep, tick, x, y, ts, state,
         lag(tick) OVER p AS pt, lead(tick) OVER p AS nt
  FROM creep_ticks
  WHERE room='W47N8' AND role='wupgrader' AND ts >= now() - interval '72 hours'
    AND x BETWEEN 12 AND 15 AND y BETWEEN 25 AND 28
  WINDOW p AS (PARTITION BY creep ORDER BY tick)
)
SELECT creep, count(*) ticks, min(tick) t0, max(tick) t1,
  max(tick)-min(tick)+1 AS span,
  count(*) FILTER (WHERE nt IS NOT NULL AND nt-tick>1) AS gaps,
  max(nt-tick) FILTER (WHERE nt IS NOT NULL) AS max_gap
FROM u
GROUP BY creep
HAVING max(tick)-min(tick)+1 - count(*) > 50
ORDER BY t1 DESC
LIMIT 20
""")
dump("22_upg_stand_coverage_holes.txt", fmt(cols, rows))

print("=== 23. filler bounce ticks last 24h vs 72h rate ===", flush=True)
cols, rows = q("""
SELECT
  count(*) FILTER (WHERE codes LIKE '%f%') AS windows_with_f,
  sum(length(regexp_replace(coalesce(codes,''), '[^f]', '', 'g'))) AS target_full_ticks,
  sum(length(regexp_replace(coalesce(codes,''), '[^m]', '', 'g'))) AS moving_ticks,
  sum(repaths) repaths,
  sum(stuck) stuck,
  count(DISTINCT creep) creeps,
  min(tick) t0, max(tick) t1
FROM creep_cpu
WHERE role='wfiller' AND ts >= now() - interval '6 hours'
""")
dump("23_filler_codes_6h.txt", fmt(cols, rows))

# queen bounce episode lengths already mostly n1; codes
cols, rows = q("""
SELECT
  sum(length(regexp_replace(coalesce(codes,''), '[^f]', '', 'g'))) AS target_full,
  sum(length(regexp_replace(coalesce(codes,''), '[^m]', '', 'g'))) AS moving,
  sum(length(regexp_replace(coalesce(codes,''), '[^w]', '', 'g'))) AS working,
  sum(repaths) repaths, sum(stuck) stuck,
  count(DISTINCT creep) creeps
FROM creep_cpu
WHERE role='queen' AND ts >= now() - interval '24 hours'
""")
dump("23_queen_codes_24h.txt", fmt(cols, rows))

print("done 19-23", flush=True)
