#!/usr/bin/env python3
"""Pre-analysis: coverage, freezes, W45N7 core/defender, storage, roles."""
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import db

HK = ZoneInfo("Asia/Hong_Kong")
LAST_TIP = 84380690
BF_LO, BF_HI = 84380801, 84381500
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")

def p(*a):
    print(*a, flush=True)

c = db.connect()

p("=== freshness ===")
for table in ("room_stats", "creep_ticks", "creep_cpu", "events"):
    try:
        row = c.execute(f"SELECT max(tick), max(ts), now()-max(ts) FROM {table}").fetchone()
        p(table, row)
    except Exception as e:
        p(table, "ERR", e)
        c.rollback()

p("=== latest room_stats both rooms ===")
for room in ("W46N8", "W47N8"):
    row = c.execute("""
        SELECT tick, ts, rcl, progress, storage, energy, cpu, bucket, commit, hostiles, sites, creeps
        FROM room_stats WHERE room=%s ORDER BY tick DESC LIMIT 1
    """, (room,)).fetchone()
    p(room, row)

p("=== room_stats gaps since 84379900 (W46N8) ===")
rows = c.execute("SELECT tick, ts, storage, cpu, bucket, hostiles FROM room_stats WHERE room='W46N8' AND tick>=84379900 ORDER BY tick").fetchall()
p("n_samples", len(rows), "first", rows[0] if rows else None, "last", rows[-1] if rows else None)
for a, b in zip(rows, rows[1:]):
    if b[0] > a[0] + 20:
        dt = (b[1] - a[1]).total_seconds() if a[1] and b[1] else None
        p(f"  STATS gap {a[0]+1}..{b[0]-1} ({b[0]-a[0]-1}t) wall={dt}s after {a[1]} stor {a[2]} before {b[1]} stor {b[2]} cpu {b[3]}")

p("=== all STATS gaps >1 tick since 84379900 W46N8 ===")
for a, b in zip(rows, rows[1:]):
    if b[0] > a[0] + 1:
        dt = (b[1] - a[1]).total_seconds() if a[1] and b[1] else None
        p(f"  {a[0]} -> {b[0]} miss={b[0]-a[0]-1}t wall={dt}s stor {a[2]}->{b[2]}")

p("=== home storage series since last tip (every sample) ===")
for r in c.execute("""
    SELECT tick, ts, storage, energy, progress, cpu, bucket, hostiles, sites
    FROM room_stats WHERE room='W46N8' AND tick>=%s ORDER BY tick
""", (LAST_TIP,)):
    p("  home", r)

p("=== W47 storage series since last tip ===")
for r in c.execute("""
    SELECT tick, ts, storage, energy, progress, cpu, bucket, hostiles, sites
    FROM room_stats WHERE room='W47N8' AND tick>=%s ORDER BY tick
""", (LAST_TIP,)):
    p("  w47", r)

p("=== events since LAST_TIP ===")
try:
    cols = [x[0] for x in c.execute("SELECT column_name FROM information_schema.columns WHERE table_name='events' ORDER BY ordinal_position").fetchall()]
    p("event cols", cols)
    rows = c.execute("SELECT * FROM events WHERE tick>=%s ORDER BY tick", (LAST_TIP - 200,)).fetchall()
    p("n", len(rows))
    for r in rows:
        p(str(r)[:500])
except Exception as e:
    p("events ERR", e)
    c.rollback()

p("=== incidents since LAST_TIP-200 ===")
try:
    cols = [x[0] for x in c.execute("SELECT column_name FROM information_schema.columns WHERE table_name='incidents' ORDER BY ordinal_position").fetchall()]
    p("inc cols", cols)
    rows = c.execute("SELECT * FROM incidents WHERE tick>=%s ORDER BY tick", (LAST_TIP - 200,)).fetchall()
    p("n", len(rows))
    for r in rows:
        p(str(r)[:500])
except Exception as e:
    p("incidents ERR", e)
    c.rollback()

p("=== defenders/guards traces since 84377900 ===")
for r in c.execute("""
SELECT creep, role, min(tick), max(tick), count(*),
       (array_agg(room ORDER BY tick))[1] as first_room,
       (array_agg(room ORDER BY tick DESC))[1] as last_room,
       (array_agg(x ORDER BY tick DESC))[1],
       (array_agg(y ORDER BY tick DESC))[1],
       (array_agg(hits ORDER BY tick DESC))[1],
       min(hits), max(hits)
FROM creep_ticks
WHERE tick>=84377900 AND (role ILIKE '%def%' OR role ILIKE '%guard%' OR creep ILIKE '%def%' OR creep ILIKE '%guard%')
GROUP BY creep, role
ORDER BY min(tick)
"""):
    p(r)

p("=== W45N7 creeps by name 84377900..now ===")
for r in c.execute("""
SELECT creep, role, min(tick), max(tick), count(*),
       (array_agg(x ORDER BY tick DESC))[1],
       (array_agg(y ORDER BY tick DESC))[1],
       (array_agg(hits ORDER BY tick DESC))[1]
FROM creep_ticks
WHERE room='W45N7' AND tick>=84377900
GROUP BY creep, role
ORDER BY min(tick)
"""):
    p(r)

p("=== W45N7 distinct tick coverage 84377900..84379000 ===")
rows = c.execute("""
SELECT tick FROM creep_ticks WHERE room='W45N7' AND tick BETWEEN 84377900 AND 84379000
GROUP BY tick ORDER BY tick
""").fetchall()
ticks = [r[0] for r in rows]
p("distinct", len(ticks), "min", ticks[0] if ticks else None, "max", ticks[-1] if ticks else None)
if ticks:
    missing = []
    prev = ticks[0]
    for t in ticks[1:]:
        if t != prev+1:
            missing.append((prev+1, t-1, t-prev-1))
        prev = t
    p("missing_spans", missing)

p("=== official coverage BF 84380801..84381500 ===")
for room in ROOMS:
    ticks = [r[0] for r in c.execute(
        "SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s ORDER BY tick",
        (room, BF_LO, BF_HI)).fetchall()]
    want = set(range(BF_LO, BF_HI+1))
    have = set(ticks)
    miss = sorted(want-have)
    spans = []
    if miss:
        a=b=miss[0]
        for x in miss[1:]:
            if x==b+1:
                b=x
            else:
                spans.append((a,b,b-a+1)); a=b=x
        spans.append((a,b,b-a+1))
    p(room, "distinct", len(ticks), "missing", len(miss), "spans", spans)

p("=== leftover 404 holes ===")
for room, base in [("W47N7", 84380900), ("W47N8", 84380300)]:
    row = c.execute(
        "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
        (room, base+1, base+100),
    ).fetchone()
    p(f"  {room}@{base} distinct={row[0]} rows={row[3]} min={row[1]} max={row[2]}")

p("=== role presence last 200 official ticks of BF ===")
for room in ROOMS:
    p(f"-- {room} --")
    for r in c.execute("""
        SELECT role, count(DISTINCT creep), min(tick), max(tick)
        FROM creep_ticks
        WHERE room=%s AND tick BETWEEN %s AND %s
        GROUP BY role ORDER BY role
    """, (room, BF_HI-200, BF_HI)):
        p(" ", r)

p("DONE")
