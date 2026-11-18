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

print("=== 9. yieldPost walks: who stepped on 34,32 after spawn, pre/post ===", flush=True)
# First 80 ticks after leaving spawn for wupgrader/wminer/wbuilder/whauler — did they step on 34,32?
cols, rows = q(f"""
WITH firsts AS (
  SELECT creep, role, min(tick) AS born
  FROM creep_ticks
  WHERE room='W47N8' AND role IN ('wupgrader','wminer','wbuilder','whauler','wrhauler','wfiller','wguard','wdefender')
    AND tick BETWEEN 84318000 AND 84333620
    AND (state IS DISTINCT FROM 'spawning')
  GROUP BY creep, role
),
walk AS (
  SELECT f.creep, f.role, f.born,
    count(*) FILTER (WHERE t.x=34 AND t.y=32) AS on_post,
    count(*) FILTER (WHERE t.x=32 AND t.y=32) AS on_pocket,
    count(*) FILTER (WHERE t.x=34 AND t.y=33) AS on_3433,
    min(t.tick) FILTER (WHERE t.x=34 AND t.y=32) AS first_post,
    min(t.tick) FILTER (WHERE t.x=32 AND t.y=32) AS first_pocket
  FROM firsts f
  JOIN creep_ticks t ON t.creep=f.creep AND t.tick BETWEEN f.born AND f.born+150
    AND t.room='W47N8'
  GROUP BY f.creep, f.role, f.born
)
SELECT
  CASE WHEN born < {YIELD_POST} THEN 'A pre-yieldPost'
       WHEN born < {YIELD_HUB} THEN 'B post-yieldPost pre-hub'
       ELSE 'C post-yieldHub' END AS era,
  role,
  count(*) creeps,
  count(*) FILTER (WHERE on_post>0) AS touched_post,
  count(*) FILTER (WHERE on_pocket>0) AS touched_pocket,
  sum(on_post) AS post_ticks,
  (ARRAY_AGG(creep||'@'||born||' post='||on_post ORDER BY on_post DESC))[1] AS example
FROM walk
GROUP BY 1, role
ORDER BY 1, role
""")
dump("09_yieldpost_walks.txt", fmt(cols, rows))

print("=== 10. exit-tile bounce / evac jitter ===", flush=True)
cols, rows = q("""
WITH w AS (
  SELECT creep, role, tick, room, x, y, store, ts,
         lag(tick) OVER p AS pt, lag(room) OVER p AS pr, lag(x) OVER p AS px, lag(y) OVER p AS py,
         lag(tick,2) OVER p AS pt2, lag(room,2) OVER p AS pr2, lag(x,2) OVER p AS px2, lag(y,2) OVER p AS py2
  FROM creep_ticks
  WHERE ts >= now() - interval '10 days'
    AND (state IS DISTINCT FROM 'spawning')
    AND (
      (room='W46N8' AND (x IN (0,49) OR y IN (0,49)))
      OR (room='W45N8' AND (x IN (0,49) OR y IN (0,49)))
      OR (room='W45N7' AND (x IN (0,49) OR y IN (0,49)))
      OR (room='W47N8' AND (x IN (0,49) OR y IN (0,49)))
      OR (room='W47N7' AND (x IN (0,49) OR y IN (0,49)))
    )
  WINDOW p AS (PARTITION BY creep ORDER BY tick)
),
b AS (
  SELECT creep, role, tick, room, ts, store,
    CASE WHEN (room,x,y) <= (pr,px,py)
      THEN room||' '||x||','||y||'↔'||pr||' '||px||','||py
      ELSE pr||' '||px||','||py||'↔'||room||' '||x||','||y
    END AS pair
  FROM w
  WHERE tick = pt + 1 AND pt = pt2 + 1
    AND ((x=px2 AND y=py2 AND room=pr2) OR (room=pr2 AND pr=room)) -- bounce including cross-room
    AND (room,x,y) IS DISTINCT FROM (pr,px,py)
),
e AS (
  SELECT *, tick - row_number() OVER (PARTITION BY creep, pair ORDER BY tick) AS grp FROM b
),
eps AS (
  SELECT creep, role, pair, min(tick) t0, max(tick) t1, count(*) n,
         min(ts) AT TIME ZONE 'Asia/Hong_Kong' AS t0_hkt
  FROM e GROUP BY creep, role, pair, grp
)
SELECT role, pair,
  count(*) episodes,
  count(*) FILTER (WHERE n>=6) AS n6p,
  count(*) FILTER (WHERE n>=20) AS n20p,
  max(n) AS max_n,
  sum(n) AS bounce_ticks,
  (ARRAY_AGG(creep||'@'||t0||'x'||n||' '||t0_hkt::text ORDER BY n DESC))[1] AS longest
FROM eps
GROUP BY role, pair
HAVING max(n) >= 6 OR sum(n) >= 20
ORDER BY max_n DESC, bounce_ticks DESC
LIMIT 80
""")
dump("10_exit_bounces.txt", fmt(cols, rows))

print("=== 11. W45N7 rhauler approach bounce episodes (detail) ===", flush=True)
cols, rows = q("""
WITH w AS (
  SELECT creep, role, tick, x, y, store, ts,
         lag(tick) OVER p AS pt, lag(x) OVER p AS px, lag(y) OVER p AS py,
         lag(tick,2) OVER p AS pt2, lag(x,2) OVER p AS px2, lag(y,2) OVER p AS py2
  FROM creep_ticks
  WHERE room='W45N7' AND role='rhauler' AND ts >= now() - interval '8 days'
    AND (state IS DISTINCT FROM 'spawning')
  WINDOW p AS (PARTITION BY creep ORDER BY tick)
),
b AS (
  SELECT creep, tick, ts, store,
    CASE WHEN (x,y) <= (px,py)
      THEN x::text||','||y::text||'↔'||px::text||','||py::text
      ELSE px::text||','||py::text||'↔'||x::text||','||y::text
    END AS pair
  FROM w
  WHERE tick = pt + 1 AND pt = pt2 + 1 AND x=px2 AND y=py2 AND (x,y) IS DISTINCT FROM (px,py)
),
e AS (
  SELECT *, tick - row_number() OVER (PARTITION BY creep, pair ORDER BY tick) AS grp FROM b
),
eps AS (
  SELECT creep, pair, min(tick) t0, max(tick) t1, count(*) n,
         min(ts) AT TIME ZONE 'Asia/Hong_Kong' AS t0_hkt,
         min(store) min_e, max(store) max_e
  FROM e GROUP BY creep, pair, grp
)
SELECT * FROM eps WHERE n >= 8
ORDER BY t0
""")
dump("11_w45n7_rhauler_long_bounces.txt", fmt(cols, rows))

print("=== 12. defenders room occupancy Nov 14 and later ===", flush=True)
cols, rows = q("""
SELECT creep, role,
  min(tick) t0, max(tick) t1,
  min(ts) AT TIME ZONE 'Asia/Hong_Kong' AS t0_hkt,
  max(ts) AT TIME ZONE 'Asia/Hong_Kong' AS t1_hkt,
  count(DISTINCT room) rooms,
  string_agg(DISTINCT room, ',') AS room_list,
  count(*) FILTER (WHERE room='W45N7') AS t_w45n7,
  count(*) FILTER (WHERE room='W45N8') AS t_w45n8,
  count(*) FILTER (WHERE room='W46N8') AS t_w46n8,
  count(*) FILTER (WHERE room='W47N7') AS t_w47n7,
  count(*) FILTER (WHERE room='W47N8') AS t_w47n8,
  count(*) ticks
FROM creep_ticks
WHERE role IN ('defender','rdef','wdefender','wguard')
  AND tick >= 84254940  -- ~Nov 14 12h window start from ROADMAP
GROUP BY creep, role
ORDER BY t0
""")
dump("12_defenders_since_nov14.txt", fmt(cols, rows))

print("done 9-12", flush=True)
