#!/usr/bin/env python3
import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db

ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
LAST_TIP = 84426210  # previous 3h patrol analysis tip
FREEZES = [
    # not yet told; fold into this 3h USER_LOG
    ("04:53:04-04:58:42", 84428081, 84428169),
    ("04:20:59-04:35:45", 84427641, 84427859),
    ("03:52:38-03:58:50", 84427261, 84427359),
    ("03:22:33-03:29:51", 84426841, 84426959),
    ("02:51:37-02:58:39", 84426401, 84426519),
]
HOLES = [
    ("W45N8", 84425501, 84425600, "W45N8@84425500 already_told"),
    ("W45N8", 84425801, 84425900, "W45N8@84425800 already_told"),
    ("W45N8", 84426201, 84426300, "W45N8@84426200 still_untold"),
    ("W45N7", 84428301, 84428400, "W45N7@84428300 NEW"),
    ("W45N8", 84422101, 84422200, "W45N8@84422100 already_told aged"),
    ("W45N8", 84422401, 84422500, "W45N8@84422400 already_told aged"),
]
WINDOW = (84425101, 84428500)


def spans(ticks, lo, hi):
    s = set(ticks)
    miss = []
    start = None
    for t in range(lo, hi + 1):
        if t not in s:
            if start is None:
                start = t
        elif start is not None:
            miss.append((start, t - 1, t - start))
            start = None
    if start is not None:
        miss.append((start, hi, hi - start + 1))
    return miss


c = db.connect()
print("=== official fill NOT-YET-TOLD freezes ===")
for label, lo, hi in FREEZES:
    want = hi - lo + 1
    print(f"-- {label} STATS {lo}..{hi} ({want}t) --")
    for room in ROOMS:
        d, mn, mx, n = c.execute(
            "SELECT COUNT(DISTINCT tick), MIN(tick), MAX(tick), COUNT(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, lo, hi),
        ).fetchone()
        miss = spans(
            [r[0] for r in c.execute(
                "SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
                (room, lo, hi),
            )],
            lo, hi,
        )
        print(f"  {room} fill={d}/{want} rows={n} range={mn}..{mx} missing={miss[:8]}")

print("=== leftover official 404 holes ===")
for room, lo, hi, label in HOLES:
    d, mn, mx, n = c.execute(
        "SELECT COUNT(DISTINCT tick), MIN(tick), MAX(tick), COUNT(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
        (room, lo, hi),
    ).fetchone()
    print(f"  {label} distinct={d} rows={n} range={mn}..{mx} want={hi-lo+1} missing={(hi-lo+1)-(d or 0)}")

print("=== official window coverage %s..%s ===" % WINDOW)
for room in ROOMS:
    ticks = [r[0] for r in c.execute(
        "SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
        (room, WINDOW[0], WINDOW[1]),
    )]
    d = len(ticks)
    want = WINDOW[1] - WINDOW[0] + 1
    miss = spans(ticks, WINDOW[0], WINDOW[1])
    print(f"  {room} distinct={d}/{want} missing_n={want-d} spans={miss}")

print("=== storage / progress since LAST_TIP", LAST_TIP, "===")
for room in ("W46N8", "W47N8"):
    print("--", room, "--")
    rows = c.execute(
        "SELECT tick, ts, storage, progress, cpu, bucket, hostiles, energy, creeps FROM room_stats WHERE room=%s AND tick>=%s ORDER BY tick",
        (room, LAST_TIP),
    ).fetchall()
    print("  n", len(rows), "min_t", rows[0][0] if rows else None, "max_t", rows[-1][0] if rows else None)
    if not rows:
        continue
    stor = [r for r in rows if r[2] is not None]
    if stor:
        imin = min(range(len(stor)), key=lambda i: stor[i][2])
        imax = max(range(len(stor)), key=lambda i: stor[i][2])
        print("  stor min", stor[imin][2], "tick", stor[imin][0], "ts", stor[imin][1])
        print("  stor max", stor[imax][2], "tick", stor[imax][0], "ts", stor[imax][1])
        print("  stor first", stor[0][2], "tick", stor[0][0], "last", stor[-1][2], "tick", stor[-1][0])
        under = [r for r in stor if r[2] < 15000]
        print("  under15k n", len(under), "first", under[0][:3] if under else None, "last", under[-1][:3] if under else None)
        over40 = [r for r in stor if r[2] >= 40000]
        print("  over40k n", len(over40), "first", over40[0][:3] if over40 else None)
    for r in rows:
        if r[0] % 100 == 0 or r is rows[-1] or r is rows[0]:
            print("  ", r[0], r[1], "stor", r[2], "prog", r[3], "cpu", r[4], "bkt", r[5], "host", r[6], "e", r[7], "cr", r[8])

print("=== CPU since LAST_TIP ===")
rows = c.execute(
    "SELECT tick, ts, cpu, bucket FROM room_stats WHERE room='W46N8' AND tick>=%s AND cpu IS NOT NULL ORDER BY tick",
    (LAST_TIP,),
).fetchall()
if rows:
    cpus = [r[2] for r in rows]
    imax = max(range(len(rows)), key=lambda i: rows[i][2])
    print("  n", len(rows), "min", min(cpus), "max", rows[imax][2], "tick", rows[imax][0], "ts", rows[imax][1], "mean", sum(cpus)/len(cpus))
    print("  bucket min", min(r[3] for r in rows if r[3] is not None), "last", rows[-1][3], "tick", rows[-1][0])

print("=== hostiles in room_stats since LAST_TIP ===")
for room in ROOMS:
    rows = c.execute(
        "SELECT tick, ts, hostiles FROM room_stats WHERE room=%s AND tick>=%s AND hostiles IS NOT NULL AND hostiles>0 ORDER BY tick",
        (room, LAST_TIP),
    ).fetchall()
    print(f"  {room} hostile_ticks={len(rows)}", ("first", rows[0][:3], "last", rows[-1][:3]) if rows else "")

print("=== invader/guard creep names since LAST_TIP (creep_ticks) ===")
rows = c.execute(
    """SELECT room, creep, MIN(tick), MAX(tick), COUNT(*), MIN(hits), MAX(hits)
       FROM creep_ticks
       WHERE tick>=%s AND (creep ILIKE '%%invader%%' OR creep ILIKE '%%guard%%' OR creep ILIKE '%%w8guard%%' OR creep ILIKE '%%rdef%%' OR role IN ('invader','w8guard','defender','rdef','w8inv'))
       GROUP BY room, creep ORDER BY MIN(tick)""",
    (LAST_TIP,),
).fetchall()
for r in rows:
    print(" ", r)

print("DONE")
