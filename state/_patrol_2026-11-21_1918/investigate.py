#!/usr/bin/env python3
import sys
from collections import defaultdict
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import db

HK = ZoneInfo("Asia/Hong_Kong")
LAST = 84398530
END = 84399320
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")

def fmt(ts):
    if ts is None:
        return "-"
    return ts.astimezone(HK).strftime("%Y-%m-%d %H:%M:%S")

def spans(ticks, lo, hi):
    s = set(ticks)
    missing = []
    a = prev = None
    for t in range(lo, hi + 1):
        if t not in s:
            if a is None:
                a = t
            prev = t
        else:
            if a is not None:
                missing.append((a, prev, prev - a + 1))
                a = None
    if a is not None:
        missing.append((a, prev, prev - a + 1))
    return missing

c = db.connect()

print("=== incidents since last tip ===")
rows = c.execute(
    "SELECT ts, tick, remote, inc, ev, from_state, state, why, inv, inv_ttl, def, dur FROM incidents WHERE tick>=%s ORDER BY tick",
    (LAST,),
).fetchall()
print("n", len(rows))
for r in rows:
    print(" ", fmt(r[0]), *r[1:])

print("\n=== events interesting since last ===")
rows = c.execute(
    "SELECT ts, tick, kind, room, severity, episode, left(msg,180) FROM events WHERE tick>=%s ORDER BY tick",
    (LAST,),
).fetchall()
print("n", len(rows))
kinds = defaultdict(int)
for r in rows:
    kinds[r[2]] += 1
print("kinds", dict(kinds))
for r in rows:
    blob = " ".join(str(x) for x in r)
    if any(s in blob.lower() for s in ("threat", "core", "invader", "defend", "stuck", "error", "alert", "killed", "cleared")):
        print(" ", fmt(r[0]), r[1], r[2], r[3], r[4], r[5], r[6])

print("\n=== defender84398431 trajectory summary ===")
rows = c.execute(
    "SELECT tick, ts, room, x, y, hits, store, state, role FROM creep_ticks WHERE creep=%s AND tick>=%s ORDER BY tick",
    ("defender84398431", LAST - 200),
).fetchall()
print("n", len(rows))
if rows:
    print("first", rows[0][0], fmt(rows[0][1]), rows[0][2], rows[0][3], rows[0][4], "hits", rows[0][5], "state", rows[0][7])
    print("last", rows[-1][0], fmt(rows[-1][1]), rows[-1][2], rows[-1][3], rows[-1][4], "hits", rows[-1][5], "state", rows[-1][7])
    prev = None
    hits_min = min(r[5] or 0 for r in rows)
    hits_max = max(r[5] or 0 for r in rows)
    print("hits min/max", hits_min, hits_max)
    for r in rows:
        sig = (r[2], r[7], r[5])
        if sig != prev and (prev is None or sig[0] != prev[0] or sig[1] != prev[1] or (r[5] or 0) != (prev[2] or 0)):
            # print room/state changes and first hit change
            if prev is None or sig[0] != prev[0] or sig[1] != prev[1]:
                print("  ", r[0], fmt(r[1]), r[2], r[3], r[4], "hits", r[5], "state", r[7])
                prev = sig
    # last 3
    print("  tail:")
    for r in rows[-5:]:
        print("  ", r[0], fmt(r[1]), r[2], r[3], r[4], "hits", r[5], "state", r[7])

print("\n=== any other def/guard creeps since last-200 ===")
rows = c.execute(
    """
    SELECT creep, role, min(tick), max(tick), count(*), min(hits), max(hits),
           array_agg(distinct room)
    FROM creep_ticks
    WHERE tick>=%s AND (role LIKE %s OR role LIKE %s OR creep LIKE %s OR creep LIKE %s)
    GROUP BY creep, role ORDER BY min(tick)
    """,
    (LAST - 200, "%def%", "%guard%", "%def%", "%guard%"),
).fetchall()
for r in rows:
    print(" ", r)

print("\n=== official coverage 84398601..84399300 ===")
for room in ROOMS:
    ticks = [t[0] for t in c.execute(
        "SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s ORDER BY 1",
        (room, 84398601, 84399300),
    ).fetchall()]
    miss = spans(ticks, 84398601, 84399300)
    print(room, "distinct", len(ticks), "missing", 700 - len(ticks), "spans", miss[:15], ("..." if len(miss) > 15 else ""))

print("\n=== STATS gaps W46N8 since last-400 (dtick>15) ===")
rows = c.execute(
    "SELECT tick, ts FROM room_stats WHERE room='W46N8' AND tick>=%s ORDER BY tick",
    (LAST - 400,),
).fetchall()
print("n", len(rows), "min", rows[0][0] if rows else None, "max", rows[-1][0] if rows else None, "last_ts", fmt(rows[-1][1]) if rows else None)
for a, b in zip(rows, rows[1:]):
    dt = b[0] - a[0]
    if dt > 15:
        wall = (b[1] - a[1]).total_seconds() if a[1] and b[1] else None
        print(f"  STATS gap {a[0]}@{fmt(a[1])} -> {b[0]}@{fmt(b[1])} dtick={dt} wall={int(wall) if wall else None}s missing {a[0]+1}..{b[0]-1} ({dt-1}t)")

print("\n=== storage extremes since last ===")
for room in ("W46N8", "W47N8"):
    rows = c.execute(
        "SELECT tick, ts, storage, progress, creeps FROM room_stats WHERE room=%s AND tick>=%s ORDER BY tick",
        (room, LAST),
    ).fetchall()
    stor = [(r[0], r[1], r[2] or 0) for r in rows]
    if not stor:
        print(room, "no rows")
        continue
    mn = min(stor, key=lambda x: x[2])
    mx = max(stor, key=lambda x: x[2])
    print(room, "n", len(stor), "first", stor[0][0], stor[0][2], "last", stor[-1][0], stor[-1][2],
          "min", mn[0], fmt(mn[1]), mn[2], "max", mx[0], fmt(mx[1]), mx[2])
    if room == "W46N8":
        under = sum(1 for *_, s in stor if s < 15000)
        print("  under15k", under, "/", len(stor), "=", round(100 * under / len(stor), 1), "%")
        # crosses
        prev = stor[0][2]
        for tick, ts, s in stor[1:]:
            ev = None
            if prev >= 15000 and s < 15000:
                ev = "under15k"
            elif prev < 15000 and s >= 15000:
                ev = "over15k"
            elif prev >= 16000 and s < 16000:
                ev = "under16k"
            elif prev < 16000 and s >= 16000:
                ev = "over16k"
            if ev:
                print("   ", ev, tick, fmt(ts), s, "prev", prev)
            prev = s
    if room == "W47N8":
        print("  over25k", sum(1 for *_, s in stor if s >= 25000), "/", len(stor),
              "over40k", sum(1 for *_, s in stor if s >= 40000),
              "under25k", sum(1 for *_, s in stor if s < 25000))

print("\n=== nUp / def / reserver changes ===")
for room in ("W46N8", "W47N8"):
    rows = c.execute(
        "SELECT tick, ts, storage, creeps FROM room_stats WHERE room=%s AND tick>=%s ORDER BY tick",
        (room, LAST),
    ).fetchall()
    prev = None
    for tick, ts, stor, creeps in rows:
        cr = creeps or {}
        if not isinstance(cr, dict):
            continue
        nup = cr.get("upgrader", 0) if room == "W46N8" else cr.get("w8upgrader", 0)
        ndef = sum(v or 0 for k, v in cr.items() if "def" in k.lower() or "guard" in k.lower())
        nres = cr.get("reserver", 0) + cr.get("reserve7", 0)
        sig = (nup, ndef, nres)
        if sig != prev:
            interesting = {k: v for k, v in cr.items() if v and k in (
                "upgrader","w8upgrader","defender","w8defender","w8guard","reserver","reserve7","rminer","w8rminer","miner","w8miner","queen","w8filler"
            )}
            print(f"  {room} {tick} {fmt(ts)} stor={stor} nUp={nup} def={ndef} res={nres} {interesting}")
            prev = sig

print("\n=== W45N7 / W47N7 occupancy role changes ===")
for room in ("W45N7", "W47N7", "W45N8"):
    rows = c.execute(
        """
        SELECT tick, count(*), min(ts), array_agg(DISTINCT role ORDER BY role)
        FROM creep_ticks
        WHERE room=%s AND tick>=%s AND tick<=%s
        GROUP BY tick ORDER BY tick
        """,
        (room, LAST, END),
    ).fetchall()
    print(room, "ticks_present", len(rows), "range", (rows[0][0], rows[-1][0]) if rows else None)
    prev = None
    for r in rows:
        sig = (r[1], tuple(r[3] or []))
        if sig != prev:
            print("  ", r[0], fmt(r[2]), "n", r[1], "roles", r[3])
            prev = sig

print("\n=== W47N7 miners/haulers last hour presence ===")
rows = c.execute(
    """
    SELECT creep, role, min(tick), max(tick), count(*)
    FROM creep_ticks
    WHERE room='W47N7' AND tick>=%s
    GROUP BY creep, role ORDER BY min(tick)
    """,
    (LAST,),
).fetchall()
for r in rows:
    print(" ", r)

print("\n=== freshness ===")
for table in ("room_stats", "creep_ticks", "creep_cpu"):
    row = c.execute("SELECT max(tick), max(ts), now()-max(ts) FROM " + table).fetchone()
    print(table, row[0], fmt(row[1]), row[2])

print("\n=== 12h/24h W47 storage max (40k lock) ===")
for hours, lo_hint in ((3, LAST - int(3*3600/4.2)), (12, LAST - int(12*3600/4.2)), (24, LAST - int(24*3600/4.2))):
    row = c.execute(
        "SELECT tick, ts, storage FROM room_stats WHERE room='W47N8' AND tick>=%s ORDER BY storage DESC NULLS LAST LIMIT 1",
        (lo_hint,),
    ).fetchone()
    n40 = c.execute(
        "SELECT count(*) FROM room_stats WHERE room='W47N8' AND tick>=%s AND storage>=40000",
        (lo_hint,),
    ).fetchone()[0]
    print(f"  {hours}h max", row[0] if row else None, fmt(row[1]) if row else None, row[2] if row else None, "n>=40k", n40)

row = c.execute(
    "SELECT tick, ts, storage FROM room_stats WHERE room='W46N8' AND tick>=%s ORDER BY storage DESC NULLS LAST LIMIT 1",
    (LAST - int(3*3600/4.2),),
).fetchone()
print("home 3h max", row[0], fmt(row[1]), row[2])
