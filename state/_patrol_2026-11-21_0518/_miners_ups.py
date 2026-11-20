import sys, json
sys.path.insert(0, "/workspace/screeps/tools")
import db

c = db.connect()
print("=== home miners last 2h by name ===")
rows = c.execute("""
  SELECT creep, min(tick), max(tick), count(DISTINCT tick),
         min(x), max(x), min(y), max(y), min(role), max(role)
  FROM creep_ticks
  WHERE room='W46N8' AND tick BETWEEN %s AND %s
    AND (creep LIKE 'miner%%' AND creep NOT LIKE '%%rminer%%')
  GROUP BY creep ORDER BY min(tick)
""", (84385815, 84387590)).fetchall()
for r in rows:
    print(" ", r)

print("\n=== at later ticks, who is where ===")
for tick in (84387530, 84387550, 84387570, 84387590):
    rows = c.execute("""
      SELECT tick, creep, role, x, y, hits, store, state
      FROM creep_ticks
      WHERE room='W46N8' AND tick=%s
        AND (creep LIKE 'miner%%' AND creep NOT LIKE '%%rminer%%')
      ORDER BY creep
    """, (tick,)).fetchall()
    print("tick", tick, "n", len(rows))
    for r in rows:
        print(" ", r)

print("\n=== W47 upgraders later ===")
for tick in (84387530, 84387560, 84387590):
    rows = c.execute("""
      SELECT tick, creep, role, x, y, store, state
      FROM creep_ticks
      WHERE room='W47N8' AND tick=%s
        AND (creep LIKE '%%upgrader%%' OR role LIKE '%%upg%%')
      ORDER BY creep
    """, (tick,)).fetchall()
    print("tick", tick, "n", len(rows))
    for r in rows:
        print(" ", r)
