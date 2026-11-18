#!/usr/bin/env python3
"""Deep traces for 15:22 patrol (creep, store, state, hits)."""
import sys
from collections import defaultdict
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import db

HK = ZoneInfo("Asia/Hong_Kong")
LAST_TIP, TIP = 84336020, 84336830
c = db.connect()

def ts(x):
    return x.astimezone(HK).strftime("%H:%M:%S") if x is not None else None

def p(*a):
    print(*a, flush=True)

def traj(creep, lo=LAST_TIP-400, hi=TIP+40):
    return c.execute(
        "SELECT tick, ts, room, x, y, store, hits, state FROM creep_ticks WHERE creep=%s AND tick BETWEEN %s AND %s ORDER BY tick",
        (creep, lo, hi),
    ).fetchall()

def summarize(name, xs):
    if not xs:
        p(f"  {name} no rows")
        return
    first, last = xs[0], xs[-1]
    p(f"  {name} n={len(xs)} first={first[0]} {ts(first[1])} {first[2]} {first[3]},{first[4]} e={first[5]} hits={first[6]} st={first[7]}")
    p(f"    last={last[0]} {ts(last[1])} {last[2]} {last[3]},{last[4]} e={last[5]} hits={last[6]} st={last[7]}")
    changes = []
    prev = None
    for r in xs:
        key = (r[2], r[3], r[4])
        if key != prev:
            changes.append((r[0], ts(r[1]), r[2], r[3], r[4], r[5], r[7]))
            prev = key
    p(f"    pos_changes={len(changes)} first4={changes[:4]} last5={changes[-5:]}")

SEATS = {(14,26),(14,27),(14,28),(12,25),(13,26),(13,27),(12,26),(15,26),(15,27)}

p("=== W47 upgraders ===")
names = [r[0] for r in c.execute(
    "SELECT DISTINCT creep FROM creep_ticks WHERE role='w8upgrader' AND tick BETWEEN %s AND %s ORDER BY 1",
    (LAST_TIP-400, TIP+40),
).fetchall()]
p("names", names)
for n in names:
    xs = traj(n, LAST_TIP-400, TIP+40)
    summarize(n, xs)
    seats = [r for r in xs if (r[3], r[4]) in SEATS and r[2]=="W47N8"]
    loaded = [r for r in seats if (r[5] or 0) > 0]
    if seats:
        p(f"    first_seat {seats[0][0]} {ts(seats[0][1])} {seats[0][3]},{seats[0][4]} e={seats[0][5]} st={seats[0][7]}")
        p(f"    last_seat  {seats[-1][0]} {ts(seats[-1][1])} {seats[-1][3]},{seats[-1][4]} e={seats[-1][5]} st={seats[-1][7]}")
    if loaded:
        p(f"    first_loaded {loaded[0][0]} {ts(loaded[0][1])} {loaded[0][3]},{loaded[0][4]} e={loaded[0][5]}")
    # spawn at 34,30 then path to seat
    spawn_tiles = [r for r in xs if r[2]=="W47N8" and (r[3], r[4]) in {(34,30),(33,30),(34,31),(33,31)}]
    if spawn_tiles:
        p(f"    first_spawn_tile {spawn_tiles[0][0]} {ts(spawn_tiles[0][1])} {spawn_tiles[0][3]},{spawn_tiles[0][4]}")
    if spawn_tiles and seats:
        hatch = spawn_tiles[0][0]
        seat = seats[0][0]
        p(f"    spawn_tile_to_first_seat {seat-hatch}t")
        # print path every 8 ticks
        path = [r for r in xs if hatch <= r[0] <= seat]
        p("    path:")
        last = None
        for r in path:
            key=(r[2],r[3],r[4])
            if key!=last:
                p(f"      {r[0]} {ts(r[1])} {r[2]} {r[3]},{r[4]} e={r[5]} st={r[7]}")
                last=key
    seated=False
    for r in xs:
        if r[2]=="W47N8" and (r[3], r[4]) in SEATS:
            seated=True
            lastseat=r
        elif seated:
            p(f"    left_seat after {lastseat[0]} {ts(lastseat[1])} {lastseat[3]},{lastseat[4]} -> {r[0]} {ts(r[1])} {r[2]} {r[3]},{r[4]} e={r[5]}")
            seated=False

p("=== w8up count changes this hour ===")
rows=c.execute(
    "SELECT tick, count(DISTINCT creep) FROM creep_ticks WHERE role='w8upgrader' AND tick BETWEEN %s AND %s GROUP BY tick ORDER BY tick",
    (LAST_TIP-50, TIP+20)).fetchall()
prev=None
for t,n in rows:
    if n!=prev:
        p("  w8up", t, n)
        prev=n
if rows: p("  last", rows[-1], "samples", len(rows))

p("=== home upgraders ===")
names = [r[0] for r in c.execute(
    "SELECT DISTINCT creep FROM creep_ticks WHERE role='upgrader' AND tick BETWEEN %s AND %s ORDER BY 1",
    (LAST_TIP-200, TIP+40),
).fetchall()]
p("names", names)
for n in names:
    xs = traj(n, LAST_TIP-200, TIP+40)
    summarize(n, xs)
    ctl=[r for r in xs if 27<=r[3]<=33 and 27<=r[4]<=33 and r[2]=="W46N8"]
    if ctl:
        p(f"    first_ctl {ctl[0][0]} {ts(ctl[0][1])} {ctl[0][3]},{ctl[0][4]} e={ctl[0][5]} st={ctl[0][7]}")
        p(f"    last_ctl  {ctl[-1][0]} {ts(ctl[-1][1])} {ctl[-1][3]},{ctl[-1][4]} e={ctl[-1][5]} st={ctl[-1][7]}")

p("=== reserve7 ===")
names=[r[0] for r in c.execute(
    "SELECT DISTINCT creep FROM creep_ticks WHERE role IN ('reserve7','reserve') AND tick BETWEEN %s AND %s ORDER BY 1",
    (LAST_TIP-500,TIP+40)).fetchall()]
p("reserve names", names)
for n in names:
    summarize(n, traj(n, LAST_TIP-500, TIP+40))

# W47N7 presence of reserve7 vs missing ticks
p("=== reserve7 vs W47N7 coverage ===")
cov=c.execute(
    """
    SELECT tick, bool_or(role='reserve7' OR role='reserve') AS has_r7
    FROM creep_ticks
    WHERE tick BETWEEN %s AND %s AND room='W47N7'
    GROUP BY tick ORDER BY tick
    """,
    (LAST_TIP, TIP),
).fetchall()
has=[t for t,h in cov if h]
no=[t for t,h in cov if not h]
all_t=[t for t,_ in cov]
def ranges(xs):
    if not xs: return []
    out=[]; a=b=xs[0]
    for t in xs[1:]:
        if t==b+1: b=t
        else:
            out.append((a,b,b-a+1)); a=b=t
    out.append((a,b,b-a+1)); return out
p(f"  W47N7 distinct={len(all_t)} with_r7={len(has)} without={len(no)} without_ranges={ranges(no)}")
miss=sorted(set(range(LAST_TIP,TIP+1))-set(all_t))
p(f"  W47N7 missing n={len(miss)} ranges={ranges(miss)}")

p("=== reservers this hour ===")
names=[r[0] for r in c.execute(
    "SELECT DISTINCT creep FROM creep_ticks WHERE role='reserver' AND tick BETWEEN %s AND %s ORDER BY 1",
    (LAST_TIP-100,TIP+40)).fetchall()]
p("reserver names", names)
for n in names:
    summarize(n, traj(n, LAST_TIP-100, TIP+40))

p("=== w8rminers ===")
names=[r[0] for r in c.execute(
    "SELECT DISTINCT creep FROM creep_ticks WHERE role='w8rminer' AND tick BETWEEN %s AND %s ORDER BY 1",
    (LAST_TIP-100,TIP+40)).fetchall()]
p("w8rminer names", names)
for n in names:
    summarize(n, traj(n, LAST_TIP-100, TIP+40))

p("=== defender84335584 this hour ===")
xs=traj("defender84335584", LAST_TIP-20, TIP+40)
summarize("defender84335584", xs)
prev=None
for r in xs:
    if prev is None or r[2]!=prev[2]:
        p(f"    room {r[0]} {ts(r[1])} {r[2]} {r[3]},{r[4]} hits={r[6]} st={r[7]}")
        prev=r

p("=== w8filler / w8miner handoffs ===")
for role in ("w8filler","w8miner"):
    names=[r[0] for r in c.execute(
        "SELECT DISTINCT creep FROM creep_ticks WHERE role=%s AND tick BETWEEN %s AND %s ORDER BY 1",
        (role, LAST_TIP-50, TIP+40)).fetchall()]
    p(f"  {role} names {names}")
    for n in names:
        summarize(n, traj(n, LAST_TIP-50, TIP+40))

p("=== home storage later / latest room_stats ===")
for room in ("W46N8","W47N8"):
    rows=c.execute(
        "SELECT tick, ts, storage, progress, cpu, bucket FROM room_stats WHERE room=%s AND tick>=%s ORDER BY tick",
        (room, TIP-5),
    ).fetchall()
    p(f"  {room} n={len(rows)}")
    for r in rows[-6:]:
        p(f"    {r[0]} {ts(r[1])} stor={r[2]} p={r[3]} cpu={r[4]} bkt={r[5]}")

p("DONE")
