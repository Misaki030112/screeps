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

def p(*a):
    print(*a)

p("=== room_stats freshness ===")
for room in ("W46N8", "W47N8"):
    row = c.execute("SELECT max(tick), max(ts), now()-max(ts) FROM room_stats WHERE room=%s", (room,)).fetchone()
    p(room, row)

p("=== creep_ticks freshness ===")
for room in OFFICIAL:
    row = c.execute("SELECT max(tick), max(ts), now()-max(ts), count(*) FROM creep_ticks WHERE room=%s AND tick>=84401080", (room,)).fetchone()
    p(room, row)

p("=== room_stats gaps since 84401080 (decile / any hole >5) ===")
for room in ("W46N8", "W47N8"):
    ticks = [r[0] for r in c.execute("SELECT tick FROM room_stats WHERE room=%s AND tick>=84401000 ORDER BY tick", (room,))]
    p(room, "n", len(ticks), "min", ticks[0] if ticks else None, "max", ticks[-1] if ticks else None)
    holes = []
    for a,b in zip(ticks, ticks[1:]):
        if b-a > 5:
            holes.append((a, b, b-a, ))
    p("  holes>5", holes[:30], "count", len(holes))

p("=== map wall-clock freezes to room_stats ticks ===")
# Approximate using room_stats.ts
freezes = [
    ("21:42:29-22:01:09", "2026-11-21 21:42:29", "2026-11-21 22:01:09", 1115),
    ("22:14:12-22:26:30", "2026-11-21 22:14:12", "2026-11-21 22:26:30", 737),
]
for name, fr, to, sec in freezes:
    p(f"--- freeze {name} ({sec}s) ---")
    for room in ("W46N8", "W47N8"):
        # last sample at or before freeze start, first after freeze end
        a = c.execute("""
            SELECT tick, ts FROM room_stats
            WHERE room=%s AND ts <= %s
            ORDER BY ts DESC LIMIT 1
        """, (room, fr)).fetchone()
        b = c.execute("""
            SELECT tick, ts FROM room_stats
            WHERE room=%s AND ts >= %s
            ORDER BY ts ASC LIMIT 1
        """, (room, to)).fetchone()
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

p("=== official creep_ticks fill for candidate freeze tick ranges ===")
# We'll refine after seeing the gaps. Probe a few ranges around expected ticks.
# 21:42 freeze was already reported as 84401311..84401589
# 22:14 freeze: from live 84401950 at 22:27:52, 737s earlier ~176 ticks -> ~84401774..84401950
ranges = [
    ("known_2142", 84401311, 84401589),
    ("probe_2214_wide", 84401650, 84401950),
]
for name, lo, hi in ranges:
    p(f"--- {name} {lo}..{hi} want={hi-lo+1} ---")
    for room in OFFICIAL:
        n = c.execute("SELECT count(DISTINCT tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s", (room, lo, hi)).fetchone()[0]
        mn, mx = c.execute("SELECT min(tick), max(tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s", (room, lo, hi)).fetchone()
        p(f"  {room} {n}/{hi-lo+1} min={mn} max={mx}")

p("=== incidents since 84401080 ===")
try:
    rows = c.execute("SELECT * FROM incidents WHERE tick>=84401080 ORDER BY tick").fetchall()
    cols = [d[0] for d in c.execute("SELECT * FROM incidents LIMIT 0").description] if False else None
except Exception as e:
    p("incidents err", e)
    rows = []
# get colnames
try:
    cur = c.execute("SELECT * FROM incidents LIMIT 0")
    p("incidents cols", [d[0] for d in cur.description])
except Exception as e:
    p("cols err", e)
rows = c.execute("SELECT * FROM incidents WHERE tick>=84400000 ORDER BY tick DESC LIMIT 15").fetchall()
for r in rows:
    p("INC", r)

p("=== threat / rem events in console_events or alerts if any ===")
for table in ("events", "alerts", "console_events", "threat_incidents", "remote_threat"):
    try:
        n = c.execute(f"SELECT count(*) FROM {table}").fetchone()
        p("table", table, n)
    except Exception as e:
        p("no table", table, type(e).__name__)

p("=== room_stats hostiles since 84401080 ===")
rows = c.execute("""
    SELECT room, tick, ts, hostiles, storage, energy, creeps
    FROM room_stats
    WHERE tick>=84401080 AND hostiles>0
    ORDER BY tick
""").fetchall()
p("hostiles rows", len(rows))
for r in rows[:40]:
    p("H", r)

p("=== storage / nUp-related room_stats extrema since last tip ===")
for room in ("W46N8", "W47N8"):
    rmin = c.execute("SELECT tick, ts, storage, progress FROM room_stats WHERE room=%s AND tick>=84401080 ORDER BY storage ASC LIMIT 3", (room,)).fetchall()
    rmax = c.execute("SELECT tick, ts, storage, progress FROM room_stats WHERE room=%s AND tick>=84401080 ORDER BY storage DESC LIMIT 3", (room,)).fetchall()
    p(room, "minstor", rmin)
    p(room, "maxstor", rmax)
    under = c.execute("SELECT count(*), min(storage) FROM room_stats WHERE room=%s AND tick>=84401080 AND storage<15000", (room,)).fetchone()
    p(room, "under15k", under)

p("=== w8 / Memory ops snapshots if stored ===")
for table in ("ops_snaps", "memory_ops", "ledger_snaps", "mem_stats"):
    try:
        n = c.execute(f"SELECT count(*) FROM {table}").fetchone()
        p("table", table, n)
    except Exception as e:
        p("no table", table, type(e).__name__)
