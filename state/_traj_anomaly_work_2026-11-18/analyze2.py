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

# Bounce episode lengths for key pairs (consecutive bounce ticks on same pair/creep)
print("=== 3. bounce episode lengths 72h for key pairs ===", flush=True)
cols, rows = q("""
WITH w AS (
  SELECT creep, role, tick, room, x, y,
         lag(tick) OVER p AS pt, lag(room) OVER p AS pr, lag(x) OVER p AS px, lag(y) OVER p AS py,
         lag(tick,2) OVER p AS pt2, lag(x,2) OVER p AS px2, lag(y,2) OVER p AS py2, lag(room,2) OVER p AS pr2
  FROM creep_ticks
  WHERE ts >= now() - interval '72 hours'
    AND (state IS DISTINCT FROM 'spawning')
    AND room IN ('W47N8','W46N8','W45N7','W45N8','W47N7')
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
),
e AS (
  SELECT *, tick - row_number() OVER (PARTITION BY creep, room, pair ORDER BY tick) AS grp
  FROM b
),
eps AS (
  SELECT creep, role, room, pair, min(tick) AS t0, max(tick) AS t1, count(*) AS n
  FROM e
  GROUP BY creep, role, room, pair, grp
)
SELECT room, role, pair,
  count(*) AS episodes,
  count(*) FILTER (WHERE n=1) AS n1,
  count(*) FILTER (WHERE n BETWEEN 2 AND 3) AS n2_3,
  count(*) FILTER (WHERE n BETWEEN 4 AND 9) AS n4_9,
  count(*) FILTER (WHERE n BETWEEN 10 AND 29) AS n10_29,
  count(*) FILTER (WHERE n >= 30) AS n30p,
  max(n) AS max_n,
  sum(n) AS bounce_ticks,
  round(avg(n)::numeric, 2) AS avg_n,
  (ARRAY_AGG(creep||'@'||t0||'x'||n ORDER BY n DESC))[1] AS longest
FROM eps
WHERE pair IN (
  '34,32↔35,31','33,31↔34,32','33,33↔34,32','34,32↔34,33',
  '28,35↔29,35','27,35↔28,35','29,35↔30,35',
  '32,32↔33,31','32,32↔33,33','32,30↔33,31','33,31↔34,31',
  '13,29↔14,30','14,30↔15,31','15,31↔15,32',
  '38,28↔39,27','39,27↔39,28','20,13↔21,14','19,13↔20,14',
  '34,27↔35,26','24,46↔25,45','20,15↔21,15',
  '18,49↔18,48','18,0↔18,1','21,49↔21,48','21,0↔21,1',
  '49,21↔48,21','49,14↔48,14','0,14↔1,14','0,21↔1,21',
  '32,32↔32,31','32,32↔33,32'
)
GROUP BY room, role, pair
ORDER BY bounce_ticks DESC
""")
dump("03_bounce_episodes_keypairs_72h.txt", fmt(cols, rows))

print("=== 4. 32,32↔33,31 before/after yieldHub ===", flush=True)
cols, rows = q(f"""
WITH w AS (
  SELECT creep, role, tick, room, x, y,
         lag(tick) OVER p AS pt, lag(room) OVER p AS pr, lag(x) OVER p AS px, lag(y) OVER p AS py,
         lag(tick,2) OVER p AS pt2, lag(x,2) OVER p AS px2, lag(y,2) OVER p AS py2, lag(room,2) OVER p AS pr2
  FROM creep_ticks
  WHERE room='W47N8'
    AND tick BETWEEN 84321282-8000 AND 84333620
    AND (state IS DISTINCT FROM 'spawning')
  WINDOW p AS (PARTITION BY creep ORDER BY tick)
),
b AS (
  SELECT creep, role, tick,
    CASE WHEN (x,y) <= (px,py)
      THEN x::text||','||y::text||'↔'||px::text||','||py::text
      ELSE px::text||','||py::text||'↔'||x::text||','||y::text
    END AS pair
  FROM w
  WHERE tick = pt + 1 AND pt = pt2 + 1
    AND room = pr AND room = pr2
    AND x = px2 AND y = py2
    AND (x,y) IS DISTINCT FROM (px,py)
    AND (
      (LEAST(x,px)=32 AND LEAST(y,py)=31 AND GREATEST(x,px)=32 AND GREATEST(y,py)=32) -- 32,31↔32,32
      OR (LEAST(x,px)=32 AND GREATEST(x,px)=33 AND (y IN (31,32) OR py IN (31,32)) AND (y+py) IN (62,63,64))
    )
)
SELECT
  CASE
    WHEN tick < {YIELD_POST} THEN 'pre-yieldPost'
    WHEN tick < {YIELD_HUB} THEN 'post-yieldPost pre-yieldHub'
    ELSE 'post-yieldHub'
  END AS era,
  role, pair, count(*) bounces, count(DISTINCT creep) creeps, min(tick) t0, max(tick) t1
FROM b
GROUP BY 1, role, pair
ORDER BY 1, bounces DESC
""")
dump("04_hub_bounce_by_era.txt", fmt(cols, rows))

# More precise: exactly 32,32↔33,31 and 32,32↔33,32 and 32,32↔32,31
print("=== 4b exact cul-de-sac pairs all history since Nov 10 ===", flush=True)
cols, rows = q(f"""
WITH w AS (
  SELECT creep, role, tick, x, y,
         lag(tick) OVER p AS pt, lag(x) OVER p AS px, lag(y) OVER p AS py,
         lag(tick,2) OVER p AS pt2, lag(x,2) OVER p AS px2, lag(y,2) OVER p AS py2
  FROM creep_ticks
  WHERE room='W47N8' AND tick >= 84177901
    AND x BETWEEN 31 AND 34 AND y BETWEEN 30 AND 34
    AND (state IS DISTINCT FROM 'spawning')
  WINDOW p AS (PARTITION BY creep ORDER BY tick)
),
b AS (
  SELECT creep, role, tick,
    CASE WHEN (x,y) <= (px,py)
      THEN x::text||','||y::text||'↔'||px::text||','||py::text
      ELSE px::text||','||py::text||'↔'||x::text||','||y::text
    END AS pair
  FROM w
  WHERE tick = pt + 1 AND pt = pt2 + 1
    AND x = px2 AND y = py2
    AND (x,y) IS DISTINCT FROM (px,py)
)
SELECT
  CASE
    WHEN tick < {YIELD_POST} THEN 'A pre-yieldPost'
    WHEN tick < {YIELD_HUB} THEN 'B post-yieldPost pre-yieldHub'
    ELSE 'C post-yieldHub'
  END AS era,
  role, pair, count(*) bounces, count(DISTINCT creep) creeps, min(tick) t0, max(tick) t1
FROM b
WHERE pair IN ('32,32↔33,31','32,31↔32,32','32,32↔33,32','32,32↔33,33','33,31↔33,32','32,30↔33,31')
GROUP BY 1, role, pair
ORDER BY 1, bounces DESC
""")
dump("04_culdesac_pairs_eras.txt", fmt(cols, rows))

print("done 3-4", flush=True)
