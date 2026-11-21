#!/usr/bin/env python3
import sys
from collections import defaultdict
sys.path.insert(0, "/workspace/screeps/tools")
import db
c = db.connect()

print("=== W45N7 creeps around core 84403400..84404420 ===")
rows = c.execute("""
  SELECT tick, creep, role, x, y, hits, store, state
  FROM creep_ticks
  WHERE room='W45N7' AND tick BETWEEN 84403400 AND 84404420
  ORDER BY tick, creep
""").fetchall()
by = defaultdict(list)
for r in rows:
    by[r[1]].append(r)
print("unique creeps", len(by), "rows", len(rows))
for n, rs in sorted(by.items(), key=lambda kv: kv[1][0][0]):
    print(f"  {n} role={rs[0][2]} n={len(rs)} first={rs[0]} last={rs[-1]}")

print()
print("=== W45N7 tick coverage holes 84403401..84404400 ===")
ticks = [r[0] for r in c.execute(
    "SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s ORDER BY tick",
    ("W45N7", 84403401, 84404400),
).fetchall()]
s = set(ticks)
miss = []
span = None
for tk in range(84403401, 84404401):
    if tk not in s:
        if span and tk == span[1] + 1:
            span[1] = tk
        else:
            if span:
                miss.append((span[0], span[1], span[1] - span[0] + 1))
            span = [tk, tk]
    else:
        if span:
            miss.append((span[0], span[1], span[1] - span[0] + 1))
            span = None
if span:
    miss.append((span[0], span[1], span[1] - span[0] + 1))
print("distinct", len(ticks), "holes", miss)

print()
print("=== room_stats jumps>20 W46N8 since 84402800 ===")
tip = c.execute("SELECT max(tick) FROM room_stats WHERE room='W46N8'").fetchone()[0]
print("tip", tip)
st = [r[0] for r in c.execute(
    "SELECT tick FROM room_stats WHERE room='W46N8' AND tick BETWEEN 84402800 AND %s ORDER BY tick",
    (tip,),
).fetchall()]
prev = None
jumps = []
for t in st:
    if prev is not None and t - prev > 20:
        jumps.append((prev, t, t - prev - 1))
    prev = t
print("room_stats jumps>20", jumps)
print("last 15 room_stats ticks", st[-15:])

print()
print("=== room_stats samples around 01:18 freeze ===")
for r in c.execute("""
  SELECT tick, ts, storage, cpu, bucket FROM room_stats
  WHERE room='W46N8' AND tick BETWEEN 84404200 AND 84404500
  ORDER BY tick
"""):
    print(r)

print()
print("=== 00:50 freeze STATS 84403921..84404079 fill check ===")
for room in ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7"):
    n = c.execute(
        "SELECT count(DISTINCT tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN 84403921 AND 84404079",
        (room,),
    ).fetchone()[0]
    print(room, f"{n}/159")

print()
print("=== W47 storage extrema ===")
for lo, label in (
    (84403680, "since_last"),
    (84403680 - int(3 * 3600 / 4.4), "3h"),
    (84403680 - int(12 * 3600 / 4.4), "12h"),
    (84403680 - int(24 * 3600 / 4.4), "24h"),
):
    mx = c.execute(
        "SELECT max(storage), min(storage) FROM room_stats WHERE room='W47N8' AND tick>=%s",
        (lo,),
    ).fetchone()
    at = c.execute(
        "SELECT tick, ts, storage FROM room_stats WHERE room='W47N8' AND tick>=%s AND storage=%s ORDER BY tick DESC LIMIT 3",
        (lo, mx[0]),
    ).fetchall()
    n40 = c.execute(
        "SELECT count(*) FROM room_stats WHERE room='W47N8' AND tick>=%s AND storage>=40000",
        (lo,),
    ).fetchone()[0]
    print(label, "min/max", mx, "at_max", at, "n>=40k", n40)

print()
print("=== home storage min/max since last ===")
mx = c.execute(
    "SELECT min(storage), max(storage) FROM room_stats WHERE room='W46N8' AND tick>=84403680"
).fetchone()
print("min/max", mx)
unders = c.execute("""
  SELECT tick, ts, storage FROM room_stats
  WHERE room='W46N8' AND tick>=84403680 AND storage<15000
  ORDER BY tick
""").fetchall()
print("under15k samples", len(unders))
for u in unders[:30]:
    print(" ", u)
mins = c.execute("""
  SELECT tick, ts, storage FROM room_stats
  WHERE room='W46N8' AND tick>=84403680 AND storage=%s
  ORDER BY tick LIMIT 5
""", (mx[0],)).fetchall()
print("at_min", mins)

print()
print("=== incidents since 84403400 ===")
try:
    rows = c.execute("SELECT * FROM incidents WHERE tick>=84403400 ORDER BY tick").fetchall()
    cols = [d[0] for d in c.description]
    print("cols", cols, "n", len(rows))
    for r in rows[:40]:
        print(" ", r)
except Exception as e:
    print("incidents err", type(e).__name__, e)
    c.rollback()

print()
print("=== CPU since last ===")
row = c.execute("""
  SELECT avg(cpu), max(cpu), min(bucket)
  FROM room_stats WHERE room='W46N8' AND tick>=84403680
""").fetchone()
print("avg/max/minbucket", row)
atmax = c.execute("""
  SELECT tick, ts, cpu FROM room_stats
  WHERE room='W46N8' AND tick>=84403680
  ORDER BY cpu DESC, tick DESC LIMIT 3
""").fetchall()
print("at_max_cpu", atmax)
