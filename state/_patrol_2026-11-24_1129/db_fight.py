import sys
from collections import defaultdict
sys.path.insert(0, "/workspace/screeps/tools")
import db
c = db.connect()

print("=== events non-watch since 84448700 ===")
rows = c.execute("SELECT tick, ts, kind, room, severity, episode, msg FROM events WHERE tick>=84448700 AND kind <> %s ORDER BY tick", ("watch",)).fetchall()
for r in rows:
    print(r)

def summarize(label, rows):
    print(label, "n", len(rows))
    by=defaultdict(list)
    for r in rows:
        by[r[1]].append(r)
    for n,rs in by.items():
        print(" ", n, "n", len(rs), "first", rs[0], "last", rs[-1])

print("=== W45N7 invader/def/rminer 84448740..84449250 ===")
rows = c.execute(
    """
  SELECT tick, creep, role, x, y, hits, state
  FROM creep_ticks
  WHERE room=%s AND tick BETWEEN 84448740 AND 84449250
    AND (creep ILIKE %s OR creep ILIKE %s OR creep ILIKE %s OR COALESCE(role,'') ILIKE %s)
  ORDER BY tick, creep
""",
    ("W45N7", "%invader%", "%def%", "%rminer%", "%def%"),
).fetchall()
summarize("W45N7", rows)

print("=== W47N7 invader/rdef/rminer 84449890..84450150 ===")
rows = c.execute(
    """
  SELECT tick, creep, role, x, y, hits, state
  FROM creep_ticks
  WHERE room=%s AND tick BETWEEN 84449890 AND 84450150
    AND (creep ILIKE %s OR creep ILIKE %s OR creep ILIKE %s OR COALESCE(role,'') ILIKE %s)
  ORDER BY tick, creep
""",
    ("W47N7", "%invader%", "%def%", "%rminer%", "%def%"),
).fetchall()
summarize("W47N7", rows)

print("=== W47N8 invader/rdef 84450070..84450140 ===")
rows = c.execute(
    """
  SELECT tick, creep, role, x, y, hits, state
  FROM creep_ticks
  WHERE room=%s AND tick BETWEEN 84450070 AND 84450140
    AND (creep ILIKE %s OR creep ILIKE %s OR COALESCE(role,'') ILIKE %s)
  ORDER BY tick, creep
""",
    ("W47N8", "%invader%", "%def%", "%def%"),
).fetchall()
summarize("W47N8", rows)

print("=== defender84448870 path ===")
rows = c.execute(
    "SELECT tick, room, x, y, hits, state FROM creep_ticks WHERE creep=%s ORDER BY tick",
    ("defender84448870",),
).fetchall()
print("n", len(rows))
if rows:
    print("first", rows[0], "last", rows[-1])
    rooms=defaultdict(lambda: [None,None,0])
    for t,rm,x,y,h,st in rows:
        o=rooms[rm]
        if o[0] is None: o[0]=(t,x,y,h,st)
        o[1]=(t,x,y,h,st)
        o[2]+=1
    for rm,v in rooms.items():
        print(" room", rm, "n", v[2], "first", v[0], "last", v[1])

print("=== rdef84449916 path ===")
rows = c.execute(
    "SELECT tick, room, x, y, hits, state FROM creep_ticks WHERE creep=%s ORDER BY tick",
    ("rdef84449916",),
).fetchall()
print("n", len(rows))
if rows:
    print("first", rows[0], "last", rows[-1])
    rooms=defaultdict(lambda: [None,None,0])
    for t,rm,x,y,h,st in rows:
        o=rooms[rm]
        if o[0] is None: o[0]=(t,x,y,h,st)
        o[1]=(t,x,y,h,st)
        o[2]+=1
    for rm,v in rooms.items():
        print(" room", rm, "n", v[2], "first", v[0], "last", v[1])
