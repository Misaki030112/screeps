#!/usr/bin/env python3
import json, sys
from collections import defaultdict
sys.path.insert(0, "/workspace/screeps/tools")
import db
c = db.connect()
LAST = 84337700

def p(*a):
    print(*a, flush=True)

# Events that are not routine W45N8 watch
p("======= events non-watch or not W45N8 =======")
rows = c.execute(
    "SELECT ts, tick, kind, room, severity, episode, msg, data FROM events WHERE tick>=%s ORDER BY tick",
    (LAST,),
).fetchall()
p("total events", len(rows))
kinds = defaultdict(int)
for r in rows:
    kinds[(r[2], r[3])] += 1
p("by kind,room", dict(kinds))
for r in rows:
    if r[2] != "watch" or r[3] not in ("W45N8", "W45N7", "W47N7"):
        p(" ", r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7])

p("======= events kind!=watch (all rooms) =======")
for r in rows:
    if r[2] != "watch":
        p(" ", r[0], r[1], r[2], r[3], r[4], r[5], r[6], str(r[7])[:400])

p("======= incidents since last =======")
cols = [d[0] for d in c.execute("SELECT * FROM incidents LIMIT 0").description]
p("cols", cols)
inc = c.execute("SELECT * FROM incidents WHERE tick>=%s OR latest>=%s OR first>=%s ORDER BY 1", (LAST, LAST, LAST) if "tick" in cols else (LAST,)).fetchall() if False else None
# try flexible
try:
    inc = c.execute("SELECT * FROM incidents ORDER BY 1 DESC LIMIT 8").fetchall()
    for r in inc:
        p(" ", dict(zip(cols, r)))
except Exception as e:
    p("inc err", e)
    c.rollback()

# W47 storage path every sample
p("======= W47 stor path =======")
for r in c.execute("SELECT tick, ts, storage, progress, creeps FROM room_stats WHERE room='W47N8' AND tick>=%s ORDER BY tick", (LAST,)):
    cr = r[4] if not isinstance(r[4], str) else json.loads(r[4])
    p(r[0], r[1], "stor", r[2], "p", r[3], "w8up", cr.get("w8upgrader"), "def", cr.get("defender") or cr.get("w8defender") or 0, "fill", cr.get("w8filler"))

p("======= home stor path =======")
for r in c.execute("SELECT tick, ts, storage, progress, creeps FROM room_stats WHERE room='W46N8' AND tick>=%s ORDER BY tick", (LAST,)):
    cr = r[4] if not isinstance(r[4], str) else json.loads(r[4])
    p(r[0], r[1], "stor", r[2], "p", r[3], "nUp", cr.get("upgrader"))

# defender / rminer / upgrader trajectories
p("======= creep names of interest in creep_ticks =======")
names_like = "%84337911%"
for pat in ("rdef84337911", "defender84337911", "%37911%", "w8upgrader84336415", "w8upgrader84336935", "w8upgrader84337872", "w8rminer84337097", "w8rminer84337323", "reserve784337630", "reserver84337655", "reserver84337880", "upgrader84336617", "upgrader84337350"):
    pass

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
# discover columns
cols = [d[0] for d in c.execute("SELECT * FROM creep_ticks LIMIT 0").description]
p("creep_ticks cols", cols)

for name in names:
    rows = c.execute(
        "SELECT tick, ts, room, x, y, role, hits, store_energy, spawning, intent, idle_reason FROM creep_ticks WHERE name=%s AND tick>=%s ORDER BY tick"
        if set(["intent","idle_reason","store_energy","spawning"]).issubset(cols)
        else "SELECT * FROM creep_ticks WHERE name=%s AND tick>=%s ORDER BY tick LIMIT 1",
        (name, LAST),
    ).fetchall()
    if not rows:
        # try wider
        n = c.execute("SELECT count(*) FROM creep_ticks WHERE name=%s", (name,)).fetchone()[0]
        p(name, "no rows since LAST, total", n)
        continue
    p("----", name, "n", len(rows), "first", rows[0], "last", rows[-1])
    # room/pos changes
    prev = None
    changes = []
    for r in rows:
        key = (r[2], r[3], r[4], r[8] if len(r)>8 else None)
        if prev is None or key != prev:
            changes.append(r)
            prev = key
    # print compressed: first, changes if few, last
    if len(changes) <= 25:
        for r in changes:
            p("  ch", r)
    else:
        for r in changes[:8]:
            p("  ch", r)
        p("  ...", len(changes), "changes")
        for r in changes[-8:]:
            p("  ch", r)

# hostile creeps? maybe not in creep_ticks
p("======= any non-Misaki names in creep_ticks this hour? =======")
# skip if no owner col
if "owner" in cols or "user" in cols:
    oc = "owner" if "owner" in cols else "user"
    p(c.execute(f"SELECT {oc}, count(*) FROM creep_ticks WHERE tick>=%s GROUP BY 1", (LAST,)).fetchall())
else:
    p("no owner col")

# W47N7 our creeps around threat tick 84338164 and defender spawn
p("======= W47N7 our creeps around 84337900-84338300 (sampled) =======")
# discover
for t0 in range(84337900, 84338301, 20):
    rows = c.execute(
        "SELECT tick, name, role, x, y, hits, intent FROM creep_ticks WHERE room='W47N7' AND tick=%s ORDER BY name",
        (t0,),
    ).fetchall()
    if rows:
        p(t0, [(r[1], r[2], r[3], r[4], r[5], r[6] if len(r)>6 else None) for r in rows])

# construction? sites only in room_stats which showed 0 for owned rooms. q_rem said ns=1. maybe a road site in remote.
p("======= events mentioning site/core/invader/hostile/STUCK =======")
ev = c.execute(
    """SELECT ts, tick, kind, room, msg, data FROM events
       WHERE tick>=%s AND (kind ILIKE ANY(ARRAY['%%stuck%%','%%error%%','%%alert%%','%%invader%%','%%core%%','%%hostile%%','%%defend%%','%%site%%'])
            OR coalesce(msg,'') ILIKE ANY(ARRAY['%%stuck%%','%%error%%','%%invader%%','%%core%%','%%hostile%%','%%DEFEND%%'])
            OR data::text ILIKE ANY(ARRAY['%%invader%%','%%Invader%%','%%hostile%%','%%core%%']))
       ORDER BY tick""",
    (LAST,),
).fetchall()
p("n", len(ev))
for r in ev[:40]:
    p(" ", r)
