#!/usr/bin/env python3
import sys
from datetime import datetime
sys.path.insert(0, "/workspace/screeps/tools")
import db

ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
c = db.connect()

print("=== later room_stats after TIP 84428620 ===")
for room in ("W46N8", "W47N8"):
    rows = c.execute(
        "SELECT tick, ts, storage, progress, cpu, bucket, hostiles, energy, creeps FROM room_stats WHERE room=%s AND tick>84428620 ORDER BY tick",
        (room,),
    ).fetchall()
    print(room, "n", len(rows))
    # detect columns if n_upgraders missing
    for r in rows:
        print(" ", r)

print("=== room_stats columns ===")
cols = c.execute("SELECT column_name FROM information_schema.columns WHERE table_name='room_stats' ORDER BY ordinal_position").fetchall()
print([r[0] for r in cols])

print("=== STATS gaps W46N8 around 05:16 freeze ===")
rows = c.execute(
    "SELECT tick, ts FROM room_stats WHERE room='W46N8' AND tick BETWEEN 84428300 AND 84428700 ORDER BY tick"
).fetchall()
print("n", len(rows), "first", rows[0] if rows else None, "last", rows[-1] if rows else None)
for a, b in zip(rows, rows[1:]):
    gap = b[0] - a[0]
    if gap >= 20:
        print(f"  STATS gap {a[0]}..{b[0]-1} missing={gap-1} {a[1]} -> {b[1]}")

# If freeze 05:16:36-05:25:46, estimate ticks
print("=== creep_ticks fill candidates for 05:16 freeze ===")
# find last STATS before 05:16:36 and first after 05:25:46
rows = c.execute(
    "SELECT tick, ts FROM room_stats WHERE room='W46N8' AND ts BETWEEN '2026-11-23 05:10:00+08' AND '2026-11-23 05:35:00+08' ORDER BY tick"
).fetchall()
for r in rows:
    print("  STATS", r[0], r[1])

print("=== home under15k samples since LAST_TIP ===")
rows = c.execute(
    "SELECT tick, ts, storage, creeps FROM room_stats WHERE room='W46N8' AND tick>=84426210 AND storage<15000 ORDER BY tick"
).fetchall()
for r in rows:
    print(" ", r)

print("=== W47 storage min/max since last and 3h ===")
for label, lo in (("since_last", 84426210), ("3h", 84428620 - int(3*3600/4.23))):
    rows = c.execute(
        "SELECT tick, ts, storage FROM room_stats WHERE room='W47N8' AND tick>=%s AND storage IS NOT NULL ORDER BY tick",
        (lo,),
    ).fetchall()
    if not rows:
        continue
    imin = min(range(len(rows)), key=lambda i: rows[i][2])
    imax = max(range(len(rows)), key=lambda i: rows[i][2])
    over40 = [r for r in rows if r[2] >= 40000]
    print(label, "n", len(rows), "min", rows[imin], "max", rows[imax], "last", rows[-1], "over40", len(over40), over40[:2])

print("=== rdef / defender / threat-related creeps last 3h ===")
rows = c.execute(
    """SELECT room, creep, role, MIN(tick), MAX(tick), COUNT(*), MIN(hits), MAX(hits), MIN(x), MAX(x), MIN(y), MAX(y)
       FROM creep_ticks
       WHERE tick>=84426210 AND (creep ILIKE '%%rdef%%' OR creep ILIKE '%%def%%' OR role ILIKE '%%def%%' OR role ILIKE '%%guard%%' OR creep ILIKE '%%invader%%' OR creep ILIKE '%%Invader%%')
       GROUP BY room, creep, role ORDER BY MIN(tick)"""
).fetchall()
for r in rows:
    print(" ", r)

print("=== W47N7 creep presence around 84428300 hole ===")
rows = c.execute(
    """SELECT tick, COUNT(*), array_agg(creep ORDER BY creep)
       FROM creep_ticks WHERE room='W47N7' AND tick BETWEEN 84428250 AND 84428450
       GROUP BY tick ORDER BY tick"""
).fetchall()
# compress
prev = None
run = []
def flush():
    if not run:
        return
    a, b = run[0], run[-1]
    print(f"  {a[0]}..{b[0]} n={len(run)} creeps_first={a[1:]} creeps_last={b[1:]}")
for r in rows:
    if prev is None or r[0] != prev[0]+1 or r[1] != prev[1]:
        flush(); run=[r]
    else:
        run.append(r)
    prev = r
flush()
# missing ticks
ticks=set(r[0] for r in rows)
miss=[t for t in range(84428250,84428451) if t not in ticks]
print("missing ticks in 84428250..84428450", len(miss), miss[:20], "..." if len(miss)>20 else "")

print("=== nUp / w8up from room_stats creeps since last (counts) ===")
rows = c.execute(
    "SELECT tick, ts, storage, creeps FROM room_stats WHERE room='W46N8' AND tick>=84426210 ORDER BY tick"
).fetchall()
# print when upgrader or w8upgrader changes
prev = None
for tick, ts, stor, cr in rows:
    cr = cr or {}
    key = (cr.get("upgrader"), cr.get("w8upgrader"), cr.get("defender"), cr.get("w8guard"), cr.get("reserve7"), cr.get("reserver"))
    if key != prev:
        print(" ", tick, ts, "stor", stor, "up", cr.get("upgrader"), "w8up", cr.get("w8upgrader"), "def", cr.get("defender"), "w8g", cr.get("w8guard"), "r7", cr.get("reserve7"), "res", cr.get("reserver"))
        prev = key

print("DONE")
