#!/usr/bin/env python3
import sys, time
from collections import defaultdict
sys.path.insert(0, "/workspace/screeps/tools")
import db, history_backfill as hb

c = db.connect()

def p(*a):
    print(*a, flush=True)

p("=== W47N7 names 84372400-84372950 ===")
rows = c.execute(
    """
SELECT creep, role, min(tick), max(tick), count(*), min(hits), max(hits), min(x), max(x), min(y), max(y)
FROM creep_ticks
WHERE room='W47N7' AND tick BETWEEN 84372400 AND 84372950
GROUP BY creep, role
ORDER BY min(tick), creep
"""
).fetchall()
for r in rows:
    p(r)

p("=== rdef84372551 path compact ===")
rows = c.execute(
    """
SELECT tick, room, x, y, hits, store, state, role
FROM creep_ticks WHERE creep='rdef84372551' ORDER BY tick
"""
).fetchall()
p("rows", len(rows))
if rows:
    p("first", rows[0], "last", rows[-1])
    prev = None
    for r in rows:
        key = (r[1], r[2], r[3], r[4], r[6])
        if key != prev:
            p(" ", r)
            prev = key

p("=== defender84371269 last changes after 84372100 ===")
rows = c.execute(
    """
SELECT tick, room, x, y, hits, state FROM creep_ticks
WHERE creep='defender84371269' AND tick>=84372100 ORDER BY tick
"""
).fetchall()
p("n", len(rows))
if rows:
    p("first", rows[0], "last", rows[-1])
    prev = None
    changes = []
    for r in rows:
        key = (r[1], r[2], r[3], r[4], r[5])
        if key != prev:
            changes.append(r)
            prev = key
    for r in changes[-30:]:
        p(" ", r)

p("=== spawn ticks for rdef / defender / w8guard this hour ===")
for name in ("rdef84372551", "defender84372817", "w8guard84372832", "defender84371269", "w8upgrader84371527", "w8upgrader84372299"):
    rows = c.execute(
        """
        SELECT min(tick), max(tick), min(room), count(*), min(hits), max(hits)
        FROM creep_ticks WHERE creep=%s
        """,
        (name,),
    ).fetchone()
    p(name, rows)
    rooms = c.execute(
        """
        SELECT room, min(tick), max(tick), count(*) FROM creep_ticks
        WHERE creep=%s GROUP BY room ORDER BY min(tick)
        """,
        (name,),
    ).fetchall()
    p("  rooms", rooms)

our = hb.uid()
p("our uid", our)

p("=== official W47N7 hostiles ===")
for base in (84372400, 84372500, 84372600, 84372700, 84372800):
    time.sleep(hb.GAP_S)
    raw = hb.history_get("W47N7", base)
    p("GET W47N7", base, "200" if raw else "404")
    if not raw:
        continue
    state = {}
    first_inv = last_inv = None
    for tick, objs in hb.merge_chunk(raw, state):
        host = []
        core = []
        for oid, o in objs.items():
            typ = o.get("type") or o.get("structureType")
            user = o.get("user")
            name = o.get("name") or ""
            st = o.get("structureType") or typ
            if st in ("invaderCore", "invadercore") or typ == "invaderCore":
                core.append((tick, oid, o.get("x"), o.get("y"), o.get("hits"), o.get("hitsMax"), o.get("ticksToDeploy")))
            if user and user != our:
                host.append((tick, typ, name, o.get("x"), o.get("y"), o.get("hits"), o.get("hitsMax"), user[:8] if isinstance(user, str) else user))
        if host and first_inv is None:
            first_inv = (tick, host)
        if host:
            last_inv = (tick, host)
            if tick % 25 == 0 or tick in (84372547, 84372548, 84372600, 84372701, 84372739, 84372785, 84372786):
                p("  tickhost", tick, host)
        if core:
            p("  core", core[:3])
    p("  first_host", first_inv)
    p("  last_host", last_inv)

p("=== official W45N7 core around 84372700-84372800 ===")
for base in (84372700, 84372800):
    time.sleep(hb.GAP_S)
    raw = hb.history_get("W45N7", base)
    p("GET W45N7", base, "200" if raw else "404")
    if not raw:
        continue
    state = {}
    first = last = None
    our_span = []
    for tick, objs in hb.merge_chunk(raw, state):
        cores = []
        hosts = []
        ours = []
        for oid, o in objs.items():
            typ = o.get("type") or o.get("structureType")
            user = o.get("user")
            name = o.get("name") or ""
            st = o.get("structureType") or typ
            rec = (tick, typ, st, name, o.get("x"), o.get("y"), o.get("hits"), o.get("hitsMax"), o.get("ticksToDeploy"), o.get("level"), user)
            if st in ("invaderCore", "invadercore") or typ == "invaderCore" or (isinstance(st, str) and "core" in st.lower()):
                cores.append(rec)
            if user and user != our:
                hosts.append(rec)
            if user == our and typ in ("creep", None) and name:
                ours.append((tick, name, typ, o.get("x"), o.get("y"), o.get("hits")))
        if cores or hosts:
            last = (tick, cores, hosts)
            if first is None:
                first = (tick, cores, hosts)
            if tick <= 84372825 or tick % 25 == 0 or tick in (84372816, 84372817, 84372837, 84372890, 84372896, 84372900):
                p("  t", tick, "cores", cores, "hosts", hosts)
        if ours:
            our_span.append((tick, ours))
    p("  first", first)
    p("  last", last)
    p("  our creep ticks in chunk", len(our_span))
    if our_span:
        p("   first ours", our_span[0])
        p("   last ours", our_span[-1])

p("=== storage series ===")
for room in ("W46N8", "W47N8"):
    rows = c.execute(
        """
        SELECT tick, ts, storage, progress, cpu, bucket, energy, hostiles
        FROM room_stats WHERE room=%s AND tick>=84372100 ORDER BY tick
        """,
        (room,),
    ).fetchall()
    p(room, "n", len(rows), "first", rows[0] if rows else None, "last", rows[-1] if rows else None)
    if not rows:
        continue
    stor = [r[2] for r in rows if r[2] is not None]
    p("  min", min(stor), "at", [r for r in rows if r[2] == min(stor)][0][0], "max", max(stor), "at", [r for r in rows if r[2] == max(stor)][0][0], "last", stor[-1])
    prev = None
    for i, r in enumerate(rows):
        if prev is None or abs((r[2] or 0) - (prev or 0)) >= 800 or i % 15 == 0 or r[7]:
            p(" ", r)
        prev = r[2]
    p("  under15k", sum(1 for s in stor if s < 15000), "/", len(stor))
    p("  n>=40k", sum(1 for s in stor if s >= 40000), "n>=25k", sum(1 for s in stor if s >= 25000))

p("=== W47 40k windows ===")
for hours, lo_note in ((6, "6h"), (8, "8h"), (12, "12h"), (24, "24h")):
    lo = 84372970 - int(hours * 3600 / 4.18)
    row = c.execute(
        """
        SELECT min(storage), max(storage), count(*) FILTER (WHERE storage>=40000),
               count(*) FILTER (WHERE storage>=25000)
        FROM room_stats WHERE room='W47N8' AND tick>=%s
        """,
        (lo,),
    ).fetchone()
    mx = c.execute(
        """
        SELECT tick, ts, storage FROM room_stats
        WHERE room='W47N8' AND tick>=%s AND storage IS NOT NULL
        ORDER BY storage DESC, tick DESC LIMIT 1
        """,
        (lo,),
    ).fetchone()
    p(lo_note, "lo_tick", lo, "minmax_n40_n25", row, "maxrow", mx)

p("=== CPU since last tip ===")
rows = c.execute(
    """
SELECT tick, ts, cpu, bucket FROM room_stats
WHERE room='W46N8' AND tick>=84372110 AND cpu IS NOT NULL
ORDER BY tick
"""
).fetchall()
cpus = [r[2] for r in rows]
bkts = [r[3] for r in rows if r[3] is not None]
if cpus:
    xs = sorted(cpus)
    p("n", len(cpus), "min", min(cpus), "max", max(cpus), "avg", round(sum(cpus)/len(cpus), 2),
      "p95", xs[int(0.95 * (len(xs) - 1))], "bkt min", min(bkts) if bkts else None, "bkt last", bkts[-1] if bkts else None)
    p("top cpu", sorted(rows, key=lambda r: -r[2])[:8])

p("=== nUp / w8up from creep_ticks (not spawning) ===")
for role, label in (("upgrader", "home_up"), ("w8upgrader", "w8_up")):
    rows = c.execute(
        """
        SELECT (tick/10)*10 AS t10, count(DISTINCT creep)
        FROM creep_ticks
        WHERE role=%s AND tick BETWEEN 84372110 AND 84372980
        GROUP BY 1 ORDER BY 1
        """,
        (role,),
    ).fetchall()
    prev = None
    run_start = run_val = None
    def flush(end):
        if run_start is not None:
            p(label, run_start, "-", end, "n=", run_val)
    for t, n in rows:
        if run_val is None:
            run_start, run_val = t, n
        elif n != run_val:
            flush(prev)
            run_start, run_val = t, n
        prev = t
    flush(prev)

p("DONE_TRACES")
