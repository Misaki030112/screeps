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

print("=== 13. miner evac / exit stalls ===", flush=True)
# rminer/wrminer ticks on exit tiles or home exits, last 8 days, with stall runs
cols, rows = q("""
WITH m AS (
  SELECT creep, role, tick, room, x, y, store, ts, state
  FROM creep_ticks
  WHERE role IN ('rminer','wrminer')
    AND ts >= now() - interval '8 days'
    AND (state IS DISTINCT FROM 'spawning')
    AND (
      (room='W46N8' AND (x IN (0,1,48,49) OR y IN (0,1,48,49)))
      OR (room IN ('W45N8','W45N7','W47N8','W47N7') AND (x IN (0,1,48,49) OR y IN (0,1,48,49)))
    )
)
SELECT room, role, x, y,
  count(*) ticks, count(DISTINCT creep) creeps,
  min(tick) t0, max(tick) t1,
  min(ts) AT TIME ZONE 'Asia/Hong_Kong' AS t0_hkt,
  max(ts) AT TIME ZONE 'Asia/Hong_Kong' AS t1_hkt
FROM m
GROUP BY room, role, x, y
HAVING count(*) >= 20
ORDER BY ticks DESC
LIMIT 40
""")
dump("13_miner_exit_tiles.txt", fmt(cols, rows))

# Long stall episodes of rminer on exit-ish tiles
cols, rows = q("""
WITH m AS (
  SELECT creep, role, tick, room, x, y, store, ts,
         lag(tick) OVER p AS pt, lag(room) OVER p AS pr, lag(x) OVER p AS px, lag(y) OVER p AS py
  FROM creep_ticks
  WHERE role IN ('rminer','wrminer')
    AND ts >= now() - interval '8 days'
    AND (state IS DISTINCT FROM 'spawning')
  WINDOW p AS (PARTITION BY creep ORDER BY tick)
),
still AS (
  SELECT * FROM m
  WHERE pt = tick-1 AND room=pr AND x=px AND y=py
    AND (x IN (0,1,2,47,48,49) OR y IN (0,1,2,47,48,49) OR (room='W46N8' AND x<=3))
),
e AS (
  SELECT *, tick - row_number() OVER (PARTITION BY creep, room, x, y ORDER BY tick) AS grp FROM still
),
eps AS (
  SELECT creep, role, room, x, y, min(tick) t0, max(tick) t1, count(*) n,
         min(ts) AT TIME ZONE 'Asia/Hong_Kong' AS t0_hkt, max(store) max_e
  FROM e GROUP BY creep, role, room, x, y, grp
)
SELECT * FROM eps WHERE n >= 20
ORDER BY n DESC
LIMIT 40
""")
dump("13_miner_exit_stalls.txt", fmt(cols, rows))

print("=== 14. W47N7 miner store vs wrhauler presence (full container proxy) ===", flush=True)
# Hourly: wrminer store at stands 18,17 / 31,34, wrhauler count in W47N7, wrhauler waiting codes
cols, rows = q("""
WITH miner AS (
  SELECT date_trunc('hour', ts AT TIME ZONE 'Asia/Hong_Kong') AS hour,
    count(*) FILTER (WHERE (x,y)=(18,17) OR (x,y)=(31,34)) AS stand_ticks,
    count(*) FILTER (WHERE ((x,y)=(18,17) OR (x,y)=(31,34)) AND store>=50) AS stand_store50,
    count(*) FILTER (WHERE ((x,y)=(18,17) OR (x,y)=(31,34)) AND store>=100) AS stand_store100,
    round(avg(store) FILTER (WHERE (x,y)=(18,17) OR (x,y)=(31,34))::numeric,1) AS avg_stand_store,
    max(store) FILTER (WHERE (x,y)=(18,17) OR (x,y)=(31,34)) AS max_stand_store
  FROM creep_ticks
  WHERE role='wrminer' AND room='W47N7' AND ts >= now() - interval '72 hours'
  GROUP BY 1
),
haul AS (
  SELECT date_trunc('hour', ts AT TIME ZONE 'Asia/Hong_Kong') AS hour,
    count(*) FILTER (WHERE room='W47N7') AS ticks_in_remote,
    count(*) FILTER (WHERE room='W47N8') AS ticks_in_home,
    count(DISTINCT creep) FILTER (WHERE room='W47N7') AS haulers_in_remote,
    count(*) FILTER (WHERE room='W47N7' AND store=0) AS empty_in_remote,
    count(*) FILTER (WHERE room='W47N7' AND store>0) AS loaded_in_remote
  FROM creep_ticks
  WHERE role='wrhauler' AND ts >= now() - interval '72 hours'
  GROUP BY 1
),
codes AS (
  SELECT date_trunc('hour', ts AT TIME ZONE 'Asia/Hong_Kong') AS hour,
    sum(length(regexp_replace(coalesce(codes,''), '[^p]', '', 'g'))) AS waiting_pickup,
    sum(length(regexp_replace(coalesce(codes,''), '[^w]', '', 'g'))) AS working,
    sum(length(regexp_replace(coalesce(codes,''), '[^m]', '', 'g'))) AS moving,
    sum(fails) fails
  FROM creep_cpu
  WHERE role IN ('wrhauler','wrminer') AND ts >= now() - interval '72 hours'
  GROUP BY 1
)
SELECT m.hour, m.stand_ticks, m.stand_store50, m.stand_store100, m.avg_stand_store, m.max_stand_store,
  h.ticks_in_remote, h.ticks_in_home, h.haulers_in_remote, h.empty_in_remote, h.loaded_in_remote,
  c.waiting_pickup, c.working, c.moving, c.fails
FROM miner m
LEFT JOIN haul h ON h.hour=m.hour
LEFT JOIN codes c ON c.hour=m.hour
ORDER BY 1
""")
dump("14_w47n7_miner_store_vs_haulers.txt", fmt(cols, rows))

# wrminer fails last 24h - when/where
cols, rows = q("""
SELECT creep, sum(fails) fails, sum(work) work, sum(acts) acts, count(*) windows,
  min(tick) t0, max(tick) t1,
  min(ts) AT TIME ZONE 'Asia/Hong_Kong' AS t0_hkt
FROM creep_cpu
WHERE role='wrminer' AND ts >= now() - interval '24 hours' AND fails>0
GROUP BY creep
ORDER BY fails DESC
""")
dump("14_wrminer_fails_24h.txt", fmt(cols, rows))

print("=== 15. source A miner at 26,11 / link 26,12 ===", flush=True)
cols, rows = q("""
SELECT
  date_trunc('hour', ts AT TIME ZONE 'Asia/Hong_Kong') AS hour,
  count(*) FILTER (WHERE x=26 AND y=11) AS ticks_2611,
  count(*) FILTER (WHERE x=26 AND y=12) AS ticks_2612,
  count(*) FILTER (WHERE room='W47N8') AS ticks_room,
  round(avg(store) FILTER (WHERE x=26 AND y=11)::numeric,1) AS avg_store_stand,
  max(store) FILTER (WHERE x=26 AND y=11) AS max_store_stand,
  count(*) FILTER (WHERE x=26 AND y=11 AND store>=50) AS stand_store50
FROM creep_ticks
WHERE role='wminer' AND room='W47N8' AND ts >= now() - interval '72 hours'
GROUP BY 1
ORDER BY 1
""")
dump("15_sourceA_miner_72h.txt", fmt(cols, rows))

cols, rows = q("""
SELECT creep, sum(fails) fails, sum(work) work, sum(acts) acts, count(*) windows,
  min(tick) t0, max(tick) t1
FROM creep_cpu
WHERE role='wminer' AND ts >= now() - interval '24 hours'
GROUP BY creep
ORDER BY fails DESC
""")
dump("15_wminer_fails_24h.txt", fmt(cols, rows))

print("=== 16. post-yieldHub upgraders who touched 34,32 ===", flush=True)
cols, rows = q("""
SELECT tick, ts AT TIME ZONE 'Asia/Hong_Kong' AS hkt, creep, role, x, y, store, state
FROM creep_ticks
WHERE creep IN ('w8upgrader84330641') AND tick BETWEEN 84330680 AND 84330850
  AND room='W47N8'
ORDER BY tick
""")
dump("16_upg_30641_walk.txt", fmt(cols, rows))

# all post-hub upgraders that touched 34,32 in first 150 ticks
cols, rows = q("""
WITH firsts AS (
  SELECT creep, min(tick) AS born
  FROM creep_ticks
  WHERE room='W47N8' AND role='wupgrader' AND tick >= 84324673
    AND (state IS DISTINCT FROM 'spawning')
  GROUP BY creep
),
walk AS (
  SELECT f.creep, f.born, t.tick, t.x, t.y, t.store
  FROM firsts f
  JOIN creep_ticks t ON t.creep=f.creep AND t.tick BETWEEN f.born AND f.born+150 AND t.room='W47N8'
)
SELECT creep, born, string_agg(x||','||y, '>' ORDER BY tick) AS path
FROM walk
WHERE creep IN (
  SELECT DISTINCT creep FROM walk WHERE x=34 AND y=32
)
GROUP BY creep, born
ORDER BY born
""")
dump("16_posthub_upg_touched_post_paths.txt", fmt(cols, rows))

print("=== 17. wrhauler border bounce recency ===", flush=True)
cols, rows = q("""
WITH w AS (
  SELECT creep, tick, room, x, y, store, ts,
         lag(tick) OVER p AS pt, lag(room) OVER p AS pr, lag(x) OVER p AS px, lag(y) OVER p AS py,
         lag(tick,2) OVER p AS pt2, lag(room,2) OVER p AS pr2, lag(x,2) OVER p AS px2, lag(y,2) OVER p AS py2
  FROM creep_ticks
  WHERE role='wrhauler' AND ts >= now() - interval '8 days'
    AND (state IS DISTINCT FROM 'spawning')
    AND ((room='W47N7' AND y=0) OR (room='W47N8' AND y=49))
  WINDOW p AS (PARTITION BY creep ORDER BY tick)
),
b AS (
  SELECT creep, tick, ts, store, room
  FROM w
  WHERE tick=pt+1 AND pt=pt2+1 AND (room,x,y) IS DISTINCT FROM (pr,px,py)
    AND (pr2,px2,py2)=(room,x,y)
    AND ((room='W47N7' AND pr='W47N8') OR (room='W47N8' AND pr='W47N7'))
),
e AS (
  SELECT *, tick - row_number() OVER (PARTITION BY creep ORDER BY tick) AS grp FROM b
),
eps AS (
  SELECT creep, min(tick) t0, max(tick) t1, count(*) n,
         min(ts) AT TIME ZONE 'Asia/Hong_Kong' AS t0_hkt, max(store) max_e
  FROM e GROUP BY creep, grp
)
SELECT date_trunc('day', t0_hkt) AS day,
  count(*) episodes, count(*) FILTER (WHERE n>=6) n6p, count(*) FILTER (WHERE n>=20) n20p,
  max(n) max_n, sum(n) bounce_ticks
FROM eps
GROUP BY 1
ORDER BY 1
""")
dump("17_wrhauler_border_bounce_by_day.txt", fmt(cols, rows))

print("=== 18. reserve bounce last 24h / W47N7 ===", flush=True)
cols, rows = q("""
WITH w AS (
  SELECT creep, role, tick, x, y, ts,
         lag(tick) OVER p AS pt, lag(x) OVER p AS px, lag(y) OVER p AS py,
         lag(tick,2) OVER p AS pt2, lag(x,2) OVER p AS px2, lag(y,2) OVER p AS py2
  FROM creep_ticks
  WHERE room='W47N7' AND role IN ('reserve','reserver')
    AND ts >= now() - interval '72 hours'
    AND (state IS DISTINCT FROM 'spawning')
  WINDOW p AS (PARTITION BY creep ORDER BY tick)
),
b AS (
  SELECT creep, role, tick, ts,
    CASE WHEN (x,y)<=(px,py) THEN x||','||y||'↔'||px||','||py ELSE px||','||py||'↔'||x||','||y END AS pair
  FROM w
  WHERE tick=pt+1 AND pt=pt2+1 AND x=px2 AND y=py2 AND (x,y) IS DISTINCT FROM (px,py)
)
SELECT role, pair, count(*) bounces, count(DISTINCT creep) creeps, min(tick) t0, max(tick) t1,
  min(ts) AT TIME ZONE 'Asia/Hong_Kong' AS t0_hkt
FROM b
GROUP BY 1,2
HAVING count(*)>=5
ORDER BY bounces DESC
""")
dump("18_reserve_bounce_72h.txt", fmt(cols, rows))

print("done 13-18", flush=True)
