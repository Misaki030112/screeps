#!/usr/bin/env python3
"""Deep traces using actual creep_ticks schema (creep, store, state, hits)."""
import sys
from collections import defaultdict
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import db

HK = ZoneInfo("Asia/Hong_Kong")
LAST_TIP, TIP = 84335330, 84336020
c = db.connect()

def ts(x):
    return x.astimezone(HK).strftime("%H:%M:%S") if x is not None else None

def p(*a):
    print(*a)

def traj(creep, lo=LAST_TIP-300, hi=TIP):
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
    p(f"    pos_changes={len(changes)} first3={changes[:3]} last4={changes[-4:]}")

p("=== W47 upgraders ===")
names = [r[0] for r in c.execute(
    "SELECT DISTINCT creep FROM creep_ticks WHERE role='w8upgrader' AND tick BETWEEN %s AND %s ORDER BY 1",
    (LAST_TIP-300, TIP),
).fetchall()]
p("names", names)
for n in names:
    xs = traj(n, LAST_TIP-300, TIP)
    summarize(n, xs)
    seats = [r for r in xs if (r[3], r[4]) in {(14,26),(14,27),(14,28),(12,25),(13,26),(13,27)} and r[2]=="W47N8"]
    loaded = [r for r in seats if (r[5] or 0) > 0]
    if seats:
        p(f"    first_seat {seats[0][0]} {ts(seats[0][1])} {seats[0][3]},{seats[0][4]} e={seats[0][5]} st={seats[0][7]}")
        p(f"    last_seat  {seats[-1][0]} {ts(seats[-1][1])} {seats[-1][3]},{seats[-1][4]} e={seats[-1][5]} st={seats[-1][7]}")
    if loaded:
        p(f"    first_loaded {loaded[0][0]} {ts(loaded[0][1])} {loaded[0][3]},{loaded[0][4]} e={loaded[0][5]}")
    # leave seat
    seated=False
    for r in xs:
        if r[2]=="W47N8" and (r[3], r[4]) in {(14,26),(14,27),(14,28),(12,25),(13,26),(13,27)}:
            seated=True
            lastseat=r
        elif seated:
            p(f"    left_seat after {lastseat[0]} {ts(lastseat[1])} {lastseat[3]},{lastseat[4]} -> {r[0]} {ts(r[1])} {r[2]} {r[3]},{r[4]} e={r[5]}")
            seated=False

p("=== home upgraders ===")
names = [r[0] for r in c.execute(
    "SELECT DISTINCT creep FROM creep_ticks WHERE role='upgrader' AND tick BETWEEN %s AND %s ORDER BY 1",
    (LAST_TIP-300, TIP),
).fetchall()]
p("names", names)
for n in names:
    xs = traj(n)
    summarize(n, xs)
    ctl=[r for r in xs if 27<=r[3]<=33 and 27<=r[4]<=33 and r[2]=="W46N8"]
    if ctl:
        p(f"    first_ctl {ctl[0][0]} {ts(ctl[0][1])} {ctl[0][3]},{ctl[0][4]} e={ctl[0][5]} st={ctl[0][7]}")
        p(f"    last_ctl  {ctl[-1][0]} {ts(ctl[-1][1])} {ctl[-1][3]},{ctl[-1][4]} e={ctl[-1][5]} st={ctl[-1][7]}")

p("=== W45N7 empty spans and who fled ===")
ticks=[r[0] for r in c.execute(
    "SELECT DISTINCT tick FROM creep_ticks WHERE room='W45N7' AND tick BETWEEN %s AND %s ORDER BY tick",
    (LAST_TIP, 84335900)).fetchall()]
want=set(range(LAST_TIP, 84335901))
miss=sorted(want-set(ticks))
spans=[]
if miss:
    s=[miss[0],miss[0]]
    for t in miss[1:]:
        if t==s[1]+1: s[1]=t
        else:
            spans.append((s[0],s[1],s[1]-s[0]+1)); s=[t,t]
    spans.append((s[0],s[1],s[1]-s[0]+1))
p("distinct",len(ticks),"missing",len(miss),"spans",spans)

p("--- visitors just before/after hole ---")
for lo,hi in ((84335550,84335640),(84335780,84335830)):
    rows=c.execute(
        "SELECT tick, creep, role, x, y, store, hits, state FROM creep_ticks WHERE room='W45N7' AND tick BETWEEN %s AND %s ORDER BY tick, creep",
        (lo,hi)).fetchall()
    by=defaultdict(list)
    for r in rows: by[r[1]].append(r)
    p(f"  {lo}-{hi} unique={list(by)} rows={len(rows)}")
    for n,xs in by.items():
        p(f"    {n} ({xs[0][2]}) first={xs[0][0]} {xs[0][3]},{xs[0][4]} e={xs[0][5]} st={xs[0][7]} last={xs[-1][0]} {xs[-1][3]},{xs[-1][4]} e={xs[-1][5]} st={xs[-1][7]}")

p("=== Invader fight: defender84335584 ===")
xs=traj("defender84335584", 84335580, TIP)
summarize("defender84335584", xs)
# hits changes
prev=None
for r in xs:
    if prev is None or r[6]!=prev[6] or r[2]!=prev[2]:
        p(f"    hits/room {r[0]} {ts(r[1])} {r[2]} {r[3]},{r[4]} hits={r[6]} st={r[7]}")
        prev=r

p("=== reservers this hour ===")
names=[r[0] for r in c.execute(
    "SELECT DISTINCT creep FROM creep_ticks WHERE role='reserver' AND tick BETWEEN %s AND %s ORDER BY 1",
    (LAST_TIP-100,TIP)).fetchall()]
p("reserver names", names)
for n in names:
    summarize(n, traj(n))

p("=== W45N7/W45N8 rminers ===")
names=[r[0] for r in c.execute(
    "SELECT DISTINCT creep FROM creep_ticks WHERE role='rminer' AND tick BETWEEN %s AND %s ORDER BY 1",
    (LAST_TIP-100,TIP)).fetchall()]
p("rminer names", names)
for n in names:
    summarize(n, traj(n))

p("=== reserve7 ===")
names=[r[0] for r in c.execute(
    "SELECT DISTINCT creep FROM creep_ticks WHERE role IN ('reserve7','reserve') AND tick BETWEEN %s AND %s ORDER BY 1",
    (LAST_TIP-400,TIP)).fetchall()]
p("reserve names", names)
for n in names:
    summarize(n, traj(n, LAST_TIP-400, TIP))

p("=== leftover w8guard/w8defender last ===")
for n in ("w8guard84333824","w8defender84333827"):
    xs=c.execute("SELECT tick, ts, room, x, y, hits, state FROM creep_ticks WHERE creep=%s ORDER BY tick", (n,)).fetchall()
    if not xs:
        p(n,"no rows"); continue
    p(f"  {n} n={len(xs)} first={xs[0][0]} {ts(xs[0][1])} last={xs[-1][0]} {ts(xs[-1][1])} {xs[-1][2]} {xs[-1][3]},{xs[-1][4]} hits={xs[-1][5]} st={xs[-1][6]}")

p("=== w8up count around handoff 84335480-84335720 ===")
rows=c.execute(
    "SELECT tick, count(DISTINCT creep) FROM creep_ticks WHERE role='w8upgrader' AND tick BETWEEN %s AND %s GROUP BY tick ORDER BY tick",
    (84335480, 84335720)).fetchall()
prev=None
for t,n in rows:
    if n!=prev:
        p("  w8up", t, n)
        prev=n
if rows: p("  last", rows[-1])

p("=== home nUp creeps around floor recycle ===")
for lo,hi in ((84335370,84335490),(84335620,84335680),(84335870,84335990)):
    rows=c.execute(
        "SELECT tick, creep, x, y, store, state FROM creep_ticks WHERE role='upgrader' AND room='W46N8' AND tick BETWEEN %s AND %s ORDER BY tick, creep",
        (lo,hi)).fetchall()
    by=defaultdict(list)
    for r in rows: by[r[1]].append(r)
    p(f"  {lo}-{hi} { {k:(v[0][0],v[0][2],v[0][3],v[-1][0],v[-1][2],v[-1][3],v[-1][4],v[-1][5]) for k,v in by.items()} }")

p("DONE")
