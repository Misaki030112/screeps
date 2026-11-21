#!/usr/bin/env python3
"""Freeze STATS gaps, official creep_ticks fill, threats, nUp, roles around this hour."""
import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
HK = ZoneInfo("Asia/Hong_Kong")

c = db.connect()
OFFICIAL = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
LAST_TIP, TIP = 84401970, 84402790

def p(*a):
    print(*a)

p("=== room_stats freshness ===")
for room in ("W46N8", "W47N8"):
    row = c.execute("SELECT max(tick), max(ts), now()-max(ts) FROM room_stats WHERE room=%s", (room,)).fetchone()
    p(room, row)

p("=== creep_ticks freshness ===")
for room in OFFICIAL:
    row = c.execute("SELECT max(tick), max(ts), now()-max(ts), count(*) FROM creep_ticks WHERE room=%s AND tick>=%s", (room, LAST_TIP)).fetchone()
    p(room, row)

p("=== room_stats gaps since last tip (>=30t) ===")
for room in ("W46N8", "W47N8"):
    ticks = [r[0] for r in c.execute("SELECT tick FROM room_stats WHERE room=%s AND tick>=%s ORDER BY tick", (room, LAST_TIP))]
    p(room, "n", len(ticks), "min", ticks[0] if ticks else None, "max", ticks[-1] if ticks else None)
    holes = []
    for a,b in zip(ticks, ticks[1:]):
        if b-a > 30:
            holes.append((a, b, b-a))
    p("  holes>30", holes)

p("=== map wall-clock freezes to room_stats ticks ===")
freezes = [
    ("22:49:18-22:59:56", "2026-11-21 22:49:18", "2026-11-21 22:59:56", 634),
    ("23:20:38-23:24:23", "2026-11-21 23:20:38", "2026-11-21 23:24:23", 224),
]
for name, fr, to, sec in freezes:
    p(f"--- freeze {name} ({sec}s) ---")
    for room in ("W46N8", "W47N8"):
        a = c.execute("SELECT tick, ts FROM room_stats WHERE room=%s AND ts <= %s ORDER BY ts DESC LIMIT 1", (room, fr)).fetchone()
        b = c.execute("SELECT tick, ts FROM room_stats WHERE room=%s AND ts >= %s ORDER BY ts ASC LIMIT 1", (room, to)).fetchone()
        p(f"  {room} last_before", a, "first_after", b)
        if a and b:
            missing = c.execute("""
                SELECT count(*) FROM generate_series(%s+1, %s-1) s
                LEFT JOIN room_stats rs ON rs.room=%s AND rs.tick=s
                WHERE rs.tick IS NULL
            """, (a[0], b[0], room)).fetchone()
            present = c.execute("""
                SELECT min(tick), max(tick), count(*) FROM room_stats
                WHERE room=%s AND tick > %s AND tick < %s
            """, (room, a[0], b[0])).fetchone()
            p(f"    span {a[0]+1}..{b[0]-1} missing_stats={missing[0]} present={present}")

p("=== official creep_ticks fill for freeze ranges ===")
ranges = [
    ("f2249_STATS_84402241_84402409", 84402241, 84402409),
    ("f2320_STATS_84402681_84402749", 84402681, 84402749),
    ("f2320_official_through_84402700", 84402681, 84402700),
    ("f2320_unpublished_tail_84402701_84402749", 84402701, 84402749),
]
for name, lo, hi in ranges:
    p(f"--- {name} {lo}..{hi} want={hi-lo+1} ---")
    for room in OFFICIAL:
        n = c.execute("SELECT count(DISTINCT tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s", (room, lo, hi)).fetchone()[0]
        mn, mx = c.execute("SELECT min(tick), max(tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s", (room, lo, hi)).fetchone()
        p(f"  {room} distinct={n}/{hi-lo+1} range={mn}..{mx}")

p("=== hostiles / incidents since last tip ===")
for room in ("W46N8", "W47N8"):
    row = c.execute("SELECT count(*) FROM room_stats WHERE room=%s AND tick>=%s AND hostiles>0", (room, LAST_TIP)).fetchone()
    p(room, "hostiles_samples", row)
try:
    rows = c.execute("SELECT tick, room, kind, detail FROM incidents WHERE tick>=%s ORDER BY tick", (LAST_TIP,)).fetchall()
    p("incidents", rows[:50], "n", len(rows))
except Exception as e:
    p("incidents err", type(e).__name__, e)

p("=== guard / rdef in creep_ticks this hour ===")
rows = c.execute("""
    SELECT creep, role, min(tick), max(tick), min(hits), max(hits), count(DISTINCT tick)
    FROM creep_ticks
    WHERE tick BETWEEN %s AND %s AND (creep LIKE 'w8guard%%' OR creep LIKE 'rdef%%' OR role IN ('w8guard','rdef','w8defender'))
    GROUP BY creep, role ORDER BY min(tick)
""", (LAST_TIP, TIP+200)).fetchall()
for r in rows:
    p(" ", r)

p("=== home storage under 15k since last ===")
rows = c.execute("SELECT tick, ts, storage FROM room_stats WHERE room='W46N8' AND tick>=%s AND storage<15000 ORDER BY tick", (LAST_TIP,)).fetchall()
p(rows)

p("DONE")
