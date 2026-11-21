#!/usr/bin/env python3
import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db
from datetime import datetime
from zoneinfo import ZoneInfo

c = db.connect()
OFFICIAL = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")

print("=== official fill NEW freeze STATS 84401751..84401939 (189t) ===")
lo, hi = 84401751, 84401939
want = hi-lo+1
for room in OFFICIAL:
    ticks = [r[0] for r in c.execute("SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s ORDER BY tick", (room, lo, hi))]
    s = set(ticks)
    missing = []
    span = None
    for t in range(lo, hi+1):
        if t not in s:
            if span: span[1] = t
            else: span = [t,t]
        else:
            if span:
                missing.append(tuple(span))
                span = None
    if span: missing.append(tuple(span))
    print(f"  {room} {len(ticks)}/{want} min={ticks[0] if ticks else None} max={ticks[-1] if ticks else None} missing_spans={missing}")

print("=== split official-published 84401751..84401900 vs unpublished tail 84401901..84401939 ===")
for lo,hi in ((84401751,84401900),(84401901,84401939)):
    print(f"--- {lo}..{hi} want={hi-lo+1} ---")
    for room in OFFICIAL:
        n = c.execute("SELECT count(DISTINCT tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s", (room, lo, hi)).fetchone()[0]
        print(f"  {room} {n}/{hi-lo+1}")

print("=== home storage series around under-15k (84401590..84401980) ===")
rows = c.execute("""
    SELECT tick, ts, storage, progress, energy, creeps
    FROM room_stats WHERE room='W46N8' AND tick>=84401500
    ORDER BY tick
""").fetchall()
for r in rows:
    flag = " UNDER" if r[2] is not None and r[2] < 15000 else ""
    print(f"  {r[0]} {r[1]} stor={r[2]} p={r[3]} e={r[4]} creeps={r[5]}{flag}")

print("=== W47 storage series same window ===")
rows = c.execute("""
    SELECT tick, ts, storage, progress, energy, creeps, hostiles
    FROM room_stats WHERE room='W47N8' AND tick>=84401500
    ORDER BY tick
""").fetchall()
for r in rows:
    print(f"  {r[0]} {r[1]} stor={r[2]} p={r[3]} e={r[4]} creeps={r[5]} host={r[6]}")

print("=== events around 84401600..84401700 (w8t=84401627) ===")
# discover events columns
cur = c.execute("SELECT * FROM events LIMIT 0")
cols = [d[0] for d in cur.description]
print("events cols", cols)
rows = c.execute("SELECT * FROM events WHERE tick BETWEEN 84401500 AND 84401800 ORDER BY tick LIMIT 80").fetchall()
print("n in window", c.execute("SELECT count(*) FROM events WHERE tick BETWEEN 84401500 AND 84401800").fetchone()[0])
for r in rows[:80]:
    print("EV", r)

print("=== events types since 84401080 ===")
# guess a type/kind column
for col in cols:
    if col.lower() in ("ev","event","kind","type","name","msg","text","data"):
        try:
            rows = c.execute(f"SELECT {col}, count(*) FROM events WHERE tick>=84401080 GROUP BY 1 ORDER BY 2 DESC LIMIT 30").fetchall()
            print("group", col, rows)
        except Exception as e:
            print("group fail", col, e)

print("=== 3h storage max home/W47 ===")
for room in ("W46N8","W47N8"):
    row = c.execute("SELECT tick, ts, storage FROM room_stats WHERE room=%s AND tick>=84401980-int(3*3600/4.2) ORDER BY storage DESC NULLS LAST LIMIT 5", (room,)).fetchall()
    print(room, "3h max", row)
    # also since last and this hour
    row2 = c.execute("SELECT min(storage), max(storage) FROM room_stats WHERE room=%s AND tick>=84401080", (room,)).fetchone()
    print(room, "since_last min/max", row2)

print("=== room_stats deciles actually missing since 84401080 (step 10) ===")
for room in ("W46N8","W47N8"):
    ticks = set(r[0] for r in c.execute("SELECT tick FROM room_stats WHERE room=%s AND tick>=84401080 AND tick<=84401980", (room,)))
    want = list(range(84401080, 84401980+1, 10))
    miss = [t for t in want if t not in ticks]
    print(room, "want_deciles", len(want), "have", len(ticks), "missing", miss)
