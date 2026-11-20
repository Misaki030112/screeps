import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db

c = db.connect()
LO, HI = 84386681, 84387530
print("=== W47 miners last hour: presence by name ===")
rows = c.execute("""
  SELECT creep, min(tick), max(tick), count(*),
         min(x), max(x), min(y), max(y), min(role), max(role)
  FROM creep_ticks
  WHERE room='W47N8' AND tick BETWEEN %s AND %s
    AND (role LIKE '%%miner%%' OR creep LIKE '%%miner%%')
    AND creep NOT LIKE '%%rminer%%' AND role NOT LIKE '%%rminer%%'
  GROUP BY creep ORDER BY min(tick)
""", (LO, HI)).fetchall()
for r in rows:
    print(" ", r)

print("\n=== W47 energy-miner adjacency to sources ===")
for lab, sx, sy in [("26,11", 26, 11), ("11,43", 11, 43)]:
    rows = c.execute("""
      SELECT (tick/50)*50 AS b, count(DISTINCT tick), count(*),
             array_agg(DISTINCT creep)
      FROM creep_ticks
      WHERE room='W47N8' AND tick BETWEEN %s AND %s
        AND (role LIKE '%%w8miner%%' OR creep LIKE '%%w8miner%%' OR role='wminer')
        AND abs(x-%s)<=1 AND abs(y-%s)<=1
      GROUP BY 1 ORDER BY 1
    """, (LO, HI, sx, sy)).fetchall()
    print("  source", lab, "buckets", len(rows))
    for r in rows:
        print("   ", r)
    tot = c.execute("""
      SELECT count(DISTINCT tick), count(DISTINCT creep)
      FROM creep_ticks
      WHERE room='W47N8' AND tick BETWEEN %s AND %s
        AND (creep LIKE '%%w8miner%%' OR role IN ('wminer','w8miner'))
        AND abs(x-%s)<=1 AND abs(y-%s)<=1
    """, (LO, HI, sx, sy)).fetchone()
    print("  TOTAL adj", lab, tot)

print("\n=== all w8miner position histogram ===")
rows = c.execute("""
  SELECT x,y,count(DISTINCT tick), count(*), min(tick), max(tick)
  FROM creep_ticks
  WHERE room='W47N8' AND tick BETWEEN %s AND %s
    AND (creep LIKE '%%w8miner%%' OR role IN ('wminer','w8miner'))
  GROUP BY x,y ORDER BY 3 DESC LIMIT 20
""", (LO, HI)).fetchall()
for r in rows:
    print(" ", r)

print("\n=== 2h miners at each source ===")
for lab, sx, sy in [("26,11", 26, 11), ("11,43", 11, 43)]:
    rows = c.execute("""
      SELECT creep, min(tick), max(tick), count(DISTINCT tick)
      FROM creep_ticks
      WHERE room='W47N8' AND tick BETWEEN %s AND %s
        AND (creep LIKE '%%w8miner%%' OR role IN ('wminer','w8miner'))
        AND abs(x-%s)<=1 AND abs(y-%s)<=1
      GROUP BY creep
    """, (84385815, HI, sx, sy)).fetchall()
    print(lab, rows)
