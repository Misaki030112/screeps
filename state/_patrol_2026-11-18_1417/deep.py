#!/usr/bin/env python3
"""Deep traces: upgraders, remotes, W45N7 holes, storage drain, parked_threat, 12h lock."""
import sys, json
from collections import defaultdict
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import db

HK = ZoneInfo("Asia/Hong_Kong")
LAST_TIP = 84335330
TIP = 84336020
c = db.connect()

def p(*a):
    print(*a)

def ts(x):
    if x is None:
        return None
    return x.astimezone(HK).strftime("%H:%M:%S")

p("=== 6h/12h storage W47 and home ===")
for room in ("W46N8", "W47N8"):
    for hours, lo in (("6h", TIP - int(6*3600/4.4)), ("12h", TIP - int(12*3600/4.4)), ("13h", TIP - int(13*3600/4.4))):
        rows = c.execute(
            "SELECT tick, ts, storage FROM room_stats WHERE room=%s AND tick>=%s AND tick<=%s ORDER BY tick",
            (room, lo, TIP),
        ).fetchall()
        if not rows:
            p(room, hours, "no rows")
            continue
        stor = [(r[0], r[1], r[2] or 0) for r in rows]
        mn = min(stor, key=lambda x: x[2])
        mx = max(stor, key=lambda x: x[2])
        n40 = sum(1 for *_, s in stor if s >= 40000)
        n30 = sum(1 for *_, s in stor if s >= 30000)
        # best consecutive >=40k span
        best = 0
        cur = None
        prev = None
        for t, tsv, s in stor:
            if s >= 40000:
                if cur is None:
                    cur = prev[0] if prev else t
                best = max(best, t - cur)
            else:
                cur = None
            prev = (t, s)
        p(f"{room} {hours} n={len(rows)} min={mn[2]}@{mn[0]} {ts(mn[1])} max={mx[2]}@{mx[0]} {ts(mx[1])} n>=30k={n30} n>=40k={n40} best>=40k_span={best}")

p("=== W47 upgrader trajectories since LAST_TIP (and a bit before) ===")
rows = c.execute(
    """
    SELECT tick, ts, name, x, y, energy, ttl, spawning, say, fatigue
    FROM creep_ticks
    WHERE room IN ('W47N8','W47N7') AND name LIKE 'w8upgrader%%'
      AND tick BETWEEN %s AND %s
    ORDER BY name, tick
    """,
    (LAST_TIP - 200, TIP),
).fetchall()
by = defaultdict(list)
for r in rows:
    by[r[2]].append(r)
for name, xs in by.items():
    first, last = xs[0], xs[-1]
    # seat ticks: typical seats 14,26 14,27 12,25 14,28
    seats = [(t, ts_, x, y, e) for t, ts_, n, x, y, e, ttl, sp, say, f in xs if (x, y) in {(14, 26), (14, 27), (14, 28), (12, 25), (13, 26), (13, 27)}]
    loaded = [s for s in seats if (s[4] or 0) > 0]
    left = None
    if seats:
        # first time they leave a seat after being seated
        seated = False
        for t, ts_, n, x, y, e, ttl, sp, say, f in xs:
            if (x, y) in {(14, 26), (14, 27), (14, 28), (12, 25), (13, 26), (13, 27)}:
                seated = True
            elif seated and left is None:
                left = (t, ts_, x, y, e, ttl)
                seated = False
    p(f"  {name} n={len(xs)} first={first[0]} {ts(first[1])} {first[3]},{first[4]} e={first[5]} ttl={first[6]} sp={first[7]}")
    p(f"    last={last[0]} {ts(last[1])} {last[3]},{last[4]} e={last[5]} ttl={last[6]} sp={last[7]}")
    if seats:
        p(f"    first_seat {seats[0][0]} {ts(seats[0][1])} {seats[0][2]},{seats[0][3]} e={seats[0][4]}")
        p(f"    last_seat  {seats[-1][0]} {ts(seats[-1][1])} {seats[-1][2]},{seats[-1][3]} e={seats[-1][4]}")
    if loaded:
        p(f"    first_loaded {loaded[0][0]} {ts(loaded[0][1])} {loaded[0][2]},{loaded[0][3]} e={loaded[0][4]}")
    if left:
        p(f"    left_seat {left}")

p("=== home upgrader trajectories since LAST_TIP-200 ===")
rows = c.execute(
    """
    SELECT tick, ts, name, x, y, energy, ttl, spawning, room
    FROM creep_ticks
    WHERE name LIKE 'upgrader%%' AND name NOT LIKE 'w8%'
      AND tick BETWEEN %s AND %s
    ORDER BY name, tick
    """,
    (LAST_TIP - 200, TIP + 50),
).fetchall()
by = defaultdict(list)
for r in rows:
    by[r[2]].append(r)
# typical home seats around 29-32, 29-31
for name, xs in by.items():
    first, last = xs[0], xs[-1]
    p(f"  {name} n={len(xs)} first={first[0]} {ts(first[1])} {first[8]} {first[3]},{first[4]} e={first[5]} ttl={first[6]} sp={first[7]}")
    p(f"    last={last[0]} {ts(last[1])} {last[8]} {last[3]},{last[4]} e={last[5]} ttl={last[6]} sp={last[7]}")
    # find when energy goes 0 and they leave controller area (x around 28-33, y 28-32)
    in_ctl = [(t, ts_, x, y, e, ttl) for t, ts_, n, x, y, e, ttl, sp, rm in xs if 27 <= x <= 33 and 27 <= y <= 33]
    if in_ctl:
        p(f"    first_ctl {in_ctl[0][0]} {ts(in_ctl[0][1])} {in_ctl[0][2]},{in_ctl[0][3]} e={in_ctl[0][4]} ttl={in_ctl[0][5]}")
        p(f"    last_ctl  {in_ctl[-1][0]} {ts(in_ctl[-1][1])} {in_ctl[-1][2]},{in_ctl[-1][3]} e={in_ctl[-1][4]} ttl={in_ctl[-1][5]}")

p("=== W45N7 occupancy / empty spans LAST_TIP..84335900 ===")
ticks = [r[0] for r in c.execute(
    "SELECT DISTINCT tick FROM creep_ticks WHERE room='W45N7' AND tick BETWEEN %s AND %s ORDER BY tick",
    (LAST_TIP, 84335900),
).fetchall()]
want = set(range(LAST_TIP, 84335901))
miss = sorted(want - set(ticks))
# spans
spans = []
if miss:
    s = [miss[0], miss[0]]
    for t in miss[1:]:
        if t == s[1] + 1:
            s[1] = t
        else:
            spans.append((s[0], s[1], s[1] - s[0] + 1))
            s = [t, t]
    spans.append((s[0], s[1], s[1] - s[0] + 1))
p("distinct", len(ticks), "missing", len(miss), "spans", spans)
# who was in W45N7 just before the big hole
p("--- creeps around the 84335628-84335793 hole ---")
for lo, hi in ((84335580, 84335640), (84335790, 84335830), (84335330, 84335400)):
    rows = c.execute(
        """
        SELECT tick, name, x, y, energy, ttl
        FROM creep_ticks WHERE room='W45N7' AND tick BETWEEN %s AND %s
        ORDER BY tick, name
        """,
        (lo, hi),
    ).fetchall()
    # summarize unique names and first/last
    by = defaultdict(list)
    for r in rows:
        by[r[1]].append(r)
    p(f"  window {lo}-{hi} unique={list(by)} n_rows={len(rows)}")
    for n, xs in by.items():
        p(f"    {n} first={xs[0][0]} {xs[0][2]},{xs[0][3]} e={xs[0][4]} ttl={xs[0][5]} last={xs[-1][0]} {xs[-1][2]},{xs[-1][3]} e={xs[-1][4]} ttl={xs[-1][5]}")

p("=== rminer / reserver / rhauler in W45N7 over the hour ===")
rows = c.execute(
    """
    SELECT tick, ts, name, room, x, y, energy, ttl
    FROM creep_ticks
    WHERE (name LIKE 'rminer%%' OR name LIKE 'reserver%%' OR name LIKE 'rhauler%%')
      AND tick BETWEEN %s AND %s
      AND (room IN ('W45N7','W46N8','W45N8') OR name IN (
        SELECT DISTINCT name FROM creep_ticks WHERE room='W45N7' AND tick BETWEEN %s AND %s
      ))
    ORDER BY name, tick
    """,
    (LAST_TIP - 50, 84335900, LAST_TIP - 50, 84335900),
).fetchall()
# too many rhaulers; filter to those who visited W45N7
visitors = set(r[2] for r in rows if r[3] == "W45N7")
p("W45N7 visitors", sorted(visitors))
by = defaultdict(list)
for r in rows:
    if r[2] in visitors or r[2].startswith("rminer") or (r[2].startswith("reserver") and r[3] in ("W45N7", "W46N8")):
        by[r[2]].append(r)
for name, xs in by.items():
    rooms = []
    prev = None
    for r in xs:
        if prev != (r[3],):
            rooms.append((r[0], ts(r[1]), r[3], r[4], r[5], r[6], r[7]))
            prev = (r[3],)
    first, last = xs[0], xs[-1]
    p(f"  {name} n={len(xs)} first={first[0]} {ts(first[1])} {first[3]} {first[4]},{first[5]} e={first[6]} ttl={first[7]}")
    p(f"    last={last[0]} {ts(last[1])} {last[3]} {last[4]},{last[5]} e={last[6]} ttl={last[7]}")
    if len(rooms) > 1:
        p(f"    room_changes {rooms[:12]}{'...' if len(rooms)>12 else ''}")

p("=== reserver84335219 and other reservers (parked_threat?) ===")
for name_pat in ("reserver%%", "defender%%", "w8guard%%", "w8defender%%"):
    names = [r[0] for r in c.execute(
        "SELECT DISTINCT name FROM creep_ticks WHERE name LIKE %s AND tick BETWEEN %s AND %s",
        (name_pat, LAST_TIP - 100, TIP),
    ).fetchall()]
    p(f"-- {name_pat} names {names}")
    for name in names:
        xs = c.execute(
            """
            SELECT tick, ts, room, x, y, energy, ttl, say
            FROM creep_ticks WHERE name=%s AND tick BETWEEN %s AND %s
            ORDER BY tick
            """,
            (name, LAST_TIP - 200, TIP),
        ).fetchall()
        if not xs:
            continue
        first, last = xs[0], xs[-1]
        p(f"  {name} n={len(xs)} first={first[0]} {ts(first[1])} {first[2]} {first[3]},{first[4]} e={first[5]} ttl={first[6]} say={first[7]}")
        p(f"    last={last[0]} {ts(last[1])} {last[2]} {last[3]},{last[4]} e={last[5]} ttl={last[6]} say={last[7]}")
        # unique rooms and a few waypoints
        path = []
        prev = None
        for r in xs:
            key = (r[2], r[3], r[4])
            if key != prev:
                path.append((r[0], ts(r[1]), r[2], r[3], r[4], r[7]))
                prev = key
        p(f"    pos_changes {len(path)} sample={path[:8]} ... {path[-4:] if len(path)>8 else ''}")

p("=== home R (W45N8) rminer presence ===")
rows = c.execute(
    """
    SELECT tick, ts, name, room, x, y, energy, ttl
    FROM creep_ticks
    WHERE name LIKE 'rminer%%' AND tick BETWEEN %s AND %s
    ORDER BY name, tick
    """,
    (LAST_TIP, 84335900),
).fetchall()
by = defaultdict(list)
for r in rows:
    by[r[2]].append(r)
for name, xs in by.items():
    first, last = xs[0], xs[-1]
    rooms = set(r[3] for r in xs)
    p(f"  {name} n={len(xs)} rooms={rooms} first={first[0]} {ts(first[1])} {first[3]} {first[4]},{first[5]} e={first[6]} ttl={first[7]}")
    p(f"    last={last[0]} {ts(last[1])} {last[3]} {last[4]},{last[5]} e={last[6]} ttl={last[7]}")

p("=== W45N8 / W45N7 harvest proxy: miner energy / standing ===")
# count distinct ticks miners were in each remote
for room in ("W45N8", "W45N7"):
    r = c.execute(
        """
        SELECT count(DISTINCT tick), count(DISTINCT name), min(tick), max(tick)
        FROM creep_ticks
        WHERE room=%s AND name LIKE 'rminer%%' AND tick BETWEEN %s AND %s
        """,
        (room, LAST_TIP, 84335900),
    ).fetchone()
    p(room, "rminer ticks", r)

p("=== reserve7 trajectory ===")
rows = c.execute(
    """
    SELECT tick, ts, name, room, x, y, energy, ttl
    FROM creep_ticks
    WHERE name LIKE 'reserve7%%' AND tick BETWEEN %s AND %s
    ORDER BY name, tick
    """,
    (LAST_TIP - 400, 84335900),
).fetchall()
by = defaultdict(list)
for r in rows:
    by[r[2]].append(r)
p("reserve7 names", list(by))
for name, xs in by.items():
    first, last = xs[0], xs[-1]
    p(f"  {name} n={len(xs)} first={first[0]} {ts(first[1])} {first[3]} {first[4]},{first[5]} ttl={first[7]}")
    p(f"    last={last[0]} {ts(last[1])} {last[3]} {last[4]},{last[5]} ttl={last[7]}")
    # first time in W47N7 and at controller-ish
    in7 = [r for r in xs if r[3] == "W47N7"]
    if in7:
        p(f"    first_W47N7 {in7[0][0]} {ts(in7[0][1])} {in7[0][4]},{in7[0][5]} last {in7[-1][0]} {in7[-1][4]},{in7[-1][5]}")

p("=== leftover guard/defender last ticks ===")
for name in ("w8guard84333824", "w8defender84333827", "defender84335584"):
    xs = c.execute(
        "SELECT tick, ts, room, x, y, ttl FROM creep_ticks WHERE name=%s ORDER BY tick",
        (name,),
    ).fetchall()
    if not xs:
        p(name, "no rows")
        continue
    p(f"  {name} n={len(xs)} first={xs[0][0]} {ts(xs[0][1])} {xs[0][2]} {xs[0][3]},{xs[0][4]} ttl={xs[0][5]}")
    p(f"    last={xs[-1][0]} {ts(xs[-1][1])} {xs[-1][2]} {xs[-1][3]},{xs[-1][4]} ttl={xs[-1][5]}")

p("=== w8upgrader count by tick around 84335500 (handoff?) ===")
rows = c.execute(
    """
    SELECT tick, count(DISTINCT name)
    FROM creep_ticks
    WHERE name LIKE 'w8upgrader%%' AND tick BETWEEN %s AND %s
    GROUP BY tick ORDER BY tick
    """,
    (84335480, 84335720),
).fetchall()
prev = None
for t, n in rows:
    if n != prev:
        p("  w8up count", t, n)
        prev = n
if rows:
    p("  last", rows[-1])

p("DONE")
