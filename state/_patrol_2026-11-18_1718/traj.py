#!/usr/bin/env python3
import json, sys
sys.path.insert(0, "/workspace/screeps/tools")
import db
c = db.connect()
LAST = 84337700

def p(*a):
    print(*a, flush=True)

names = [
    "rdef84337911",
    "w8upgrader84336415",
    "w8upgrader84336935",
    "w8upgrader84337872",
    "w8rminer84337097",
    "w8rminer84337323",
    "reserve784337630",
    "reserver84337655",
    "reserver84337880",
    "upgrader84336617",
    "upgrader84337350",
    "w8filler84336747",
    "w8filler84337078",
    "w8filler84338206",
]

for name in names:
    rows = c.execute(
        "SELECT tick, ts, room, x, y, role, hits, store, state FROM creep_ticks WHERE creep=%s AND tick>=%s ORDER BY tick",
        (name, LAST - 200),
    ).fetchall()
    if not rows:
        n = c.execute("SELECT count(*) FROM creep_ticks WHERE creep=%s", (name,)).fetchone()[0]
        p(name, "no rows near LAST, total", n)
        continue
    p("----", name, "n", len(rows), "first", rows[0][:8], "last", rows[-1][:8])
    prev = None
    changes = []
    for r in rows:
        key = (r[2], r[3], r[4])
        if prev is None or key != prev:
            changes.append(r)
            prev = key
    p("  n_pos", len(changes))
    show = changes if len(changes) <= 30 else (changes[:12] + [None] + changes[-12:])
    for r in show:
        if r is None:
            p("  ...")
        else:
            p("  ", r[0], r[1], r[2], f"{r[3]},{r[4]}", "hits", r[6], "store", r[7], "state", r[8])

# first/last for upgrader 37872 including spawn (maybe before LAST)
for name in ("w8upgrader84337872", "w8upgrader84336415", "rdef84337911", "upgrader84336617"):
    r0 = c.execute("SELECT min(tick), max(tick) FROM creep_ticks WHERE creep=%s", (name,)).fetchone()
    p("span", name, r0)
    if r0[0]:
        firsts = c.execute("SELECT tick, ts, room, x, y, hits, store, state FROM creep_ticks WHERE creep=%s ORDER BY tick LIMIT 5", (name,)).fetchall()
        lasts = c.execute("SELECT tick, ts, room, x, y, hits, store, state FROM creep_ticks WHERE creep=%s ORDER BY tick DESC LIMIT 5", (name,)).fetchall()
        p("  firsts", firsts)
        p("  lasts", list(reversed(lasts)))
        # first time at upgrade seats
        seats = c.execute(
            "SELECT tick, ts, x, y, store FROM creep_ticks WHERE creep=%s AND room='W47N8' AND ((x,y) in ((12,25),(14,26),(14,27),(13,29),(14,28))) ORDER BY tick LIMIT 8",
            (name,),
        ).fetchall()
        p("  first seats", seats)

# W47N7 creeps around the fight, every 10t from 84337880 to 84338200
p("======= W47N7 occupants sample =======")
for t0 in list(range(84337880, 84338201, 20)) + [84338175, 84338164, 84338061, 84338099]:
    rows = c.execute(
        "SELECT creep, role, x, y, hits, store FROM creep_ticks WHERE room='W47N7' AND tick=%s ORDER BY creep",
        (t0,),
    ).fetchall()
    p(t0, [(r[0], r[1], r[2], r[3], r[4]) for r in rows])
