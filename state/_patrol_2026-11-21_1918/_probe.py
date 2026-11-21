#!/usr/bin/env python3
"""Coverage, freezes, STATS gaps, storage, defender/core timeline."""
from __future__ import annotations
import sys, json
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import db

HK = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
# Last 1h patrol tip and later
LAST_TIP = 84396870
# Official first-pass this hour
BF_LO, BF_HI = 84397001, 84397700
# Hour-ish window since last tip
# Known freezes to verify
FREEZES = [
    # already told in 16:32
    ("told_1616", "2026-11-21 16:16:43", "2026-11-21 16:19:24", 84396751, 84396799),
    # not yet told, from 17:00 backfill
    ("new_1648", "2026-11-21 16:48:46", "2026-11-21 17:04:41", 84397201, 84397439),
]
# leftover 404 chunks
LEFTOVER = [
    ("W45N7", 84397400),  # NEW leftover this hour
    ("W47N7", 84395600),
    ("W47N8", 84395100),
    ("W46N8", 84394300),
    ("W45N8", 84392600),
    ("W46N8", 84390400),
    ("W46N8", 84390800),
    ("W47N7", 84390900),
    ("W45N7", 84388500),
    ("W45N8", 84386600),
]

def p(*a):
    print(*a, flush=True)

def main():
    c = db.connect()
    p("=== freshness ===")
    for table in ("room_stats", "creep_ticks", "creep_cpu", "console_events"):
        try:
            row = c.execute(f"SELECT max(tick), max(ts), now()-max(ts) FROM {table}").fetchone()
            p(table, row)
        except Exception as e:
            p(table, "ERR", type(e).__name__, e)
            c.rollback()

    p("=== latest room_stats both rooms ===")
    for room in ("W46N8", "W47N8"):
        row = c.execute("""
            SELECT tick, ts, storage, progress, cpu, bucket, commit, ctl, hostiles, creeps
            FROM room_stats WHERE room=%s ORDER BY tick DESC LIMIT 1
        """, (room,)).fetchone()
        p(room, row)

    # Common tip
    both = c.execute("""
        SELECT a.tick, a.ts, a.storage, b.storage, a.progress, b.progress, a.cpu, a.bucket, a.commit
        FROM room_stats a JOIN room_stats b ON a.tick=b.tick AND b.room='W47N8'
        WHERE a.room='W46N8'
        ORDER BY a.tick DESC LIMIT 1
    """).fetchone()
    p("TIP_BOTH", both)
    TIP = both[0]

    p("=== room_stats coverage since LAST_TIP", LAST_TIP, "to", TIP, "===")
    for room in ("W46N8", "W47N8"):
        row = c.execute("""
            SELECT count(DISTINCT tick), min(tick), max(tick)
            FROM room_stats WHERE room=%s AND tick BETWEEN %s AND %s
        """, (room, LAST_TIP, TIP)).fetchone()
        p("stats", room, row, "span", TIP-LAST_TIP+1, "missing", (TIP-LAST_TIP+1)-(row[0] or 0))

    p("=== STATS gaps >= 3 ticks since LAST_TIP-200 ===")
    rows = c.execute("""
        SELECT tick FROM room_stats WHERE room='W46N8' AND tick >= %s ORDER BY tick
    """, (LAST_TIP-200,)).fetchall()
    ticks = [r[0] for r in rows]
    gaps = []
    for a,b in zip(ticks, ticks[1:]):
        if b-a > 3:
            # get ts of a and b
            ts = c.execute("SELECT tick, ts FROM room_stats WHERE room='W46N8' AND tick IN (%s,%s) ORDER BY tick", (a,b)).fetchall()
            gaps.append((a+1, b-1, b-a-1, ts))
            p(f"  STATS gap {a+1}..{b-1} missing={b-a-1} after {a} before {b} ts={ts}")
    if not gaps:
        p("  none")

    # Fine-grained: also gaps of 2+ for short WS
    p("=== STATS gaps >= 2 ticks after 84395990 (short too) ===")
    nshort=0
    for a,b in zip(ticks, ticks[1:]):
        if b-a >= 3 and a >= LAST_TIP-50:  # missing at least 2
            if b-a-1 >= 2:
                ts = c.execute("SELECT tick, ts FROM room_stats WHERE room='W46N8' AND tick IN (%s,%s) ORDER BY tick", (a,b)).fetchall()
                p(f"  short+ {a+1}..{b-1} missing={b-a-1} ts={ts}")
                nshort+=1
    if nshort==0:
        p("  none missing>=2")

    p("=== official BF window creep_ticks distinct", BF_LO, BF_HI, "===")
    for room in ROOMS:
        row = c.execute("""
            SELECT count(DISTINCT tick), min(tick), max(tick), count(*)
            FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s
        """, (room, BF_LO, BF_HI)).fetchone()
        # missing ticks list compressed
        present = {r[0] for r in c.execute(
            "SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, BF_LO, BF_HI),
        )}
        missing = [t for t in range(BF_LO, BF_HI+1) if t not in present]
        p(f"  {room} {row[0]}/700 min={row[1]} max={row[2]} rows={row[3]} missing={len(missing)}")
        if missing:
            # compress ranges
            ranges=[]
            s=e=missing[0]
            for t in missing[1:]:
                if t==e+1:
                    e=t
                else:
                    ranges.append((s,e,e-s+1))
                    s=e=t
            ranges.append((s,e,e-s+1))
            p(f"    holes: " + ", ".join(f"{a}..{b}({n})" if a!=b else str(a) for a,b,n in ranges[:20]))

    p("=== leftover 404 chunk coverage ===")
    for room, base in LEFTOVER:
        t0,t1=base+1,base+100
        row = c.execute("""
            SELECT count(DISTINCT tick), min(tick), max(tick), count(*)
            FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s
        """, (room, t0, t1)).fetchone()
        present = {r[0] for r in c.execute(
            "SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, t0, t1),
        )}
        missing = [t for t in range(t0,t1+1) if t not in present]
        p(f"  {room}@{base} {row[0]}/100 min={row[1]} max={row[2]} rows={row[3]} hole={len(missing)}")
        if missing and len(missing)<100:
            ranges=[]
            s=e=missing[0]
            for t in missing[1:]:
                if t==e+1:
                    e=t
                else:
                    ranges.append((s,e,e-s+1)); s=e=t
            ranges.append((s,e,e-s+1))
            p(f"    missing ranges: " + ", ".join(f"{a}..{b}({n})" if a!=b else str(a) for a,b,n in ranges))

    # Freeze STATS and official fill
    p("=== freeze verification (STATS + creep_ticks) ===")
    # First discover STATS ranges for new freezes if not given
    # Map wall clock to ticks via room_stats ts
    for name, fr, to, t0, t1 in FREEZES:
        p(f"-- {name} wall {fr} -> {to} hint ticks {t0}..{t1}")
        # find room_stats ticks around the wall times
        # STATS present in range, and the gap itself
        if t0 and t1:
            for room in ("W46N8",):
                row = c.execute("""
                    SELECT count(DISTINCT tick), min(tick), max(tick)
                    FROM room_stats WHERE room=%s AND tick BETWEEN %s AND %s
                """, (room, t0, t1)).fetchone()
                p(f"  STATS {room} {row[0]}/{t1-t0+1} min={row[1]} max={row[2]}")
            for room in ROOMS:
                row = c.execute("""
                    SELECT count(DISTINCT tick), min(tick), max(tick), count(*)
                    FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s
                """, (room, t0, t1)).fetchone()
                p(f"  ticks {room} {row[0]}/{t1-t0+1} min={row[1]} max={row[2]} rows={row[3]}")

    # Discover ticks for 16:16 freeze from room_stats around those times
    p("=== map 16:16-16:19 and 16:22 ping/pong to STATS ===")
    for label, lo, hi in [
        ("around_1616", "2026-11-21 16:14:00+08", "2026-11-21 16:23:00+08"),
        ("around_1547", "2026-11-21 15:45:00+08", "2026-11-21 16:00:00+08"),
        ("around_1622", "2026-11-21 16:20:00+08", "2026-11-21 16:24:00+08"),
    ]:
        rows = c.execute("""
            SELECT tick, ts FROM room_stats
            WHERE room='W46N8' AND ts BETWEEN %s AND %s
            ORDER BY tick
        """, (lo, hi)).fetchall()
        p(f"  {label} n={len(rows)}")
        if rows:
            p(f"    first {rows[0]} last {rows[-1]}")
            # gaps
            for a,b in zip(rows, rows[1:]):
                if b[0]-a[0] > 1:
                    p(f"    gap ticks {a[0]+1}..{b[0]-1} missing={b[0]-a[0]-1} after {a} before {b}")
        # also show last before and first after window via nearest
        before = c.execute("""
            SELECT tick, ts FROM room_stats WHERE room='W46N8' AND ts < %s ORDER BY tick DESC LIMIT 3
        """, (lo,)).fetchall()
        after = c.execute("""
            SELECT tick, ts FROM room_stats WHERE room='W46N8' AND ts > %s ORDER BY tick LIMIT 3
        """, (hi,)).fetchall()
        p(f"    last_before_window {before} first_after {after}")

    # Also find last STATS tick before 16:16:43 and first after 16:19:24
    p("=== tight wall-clock freeze tick bounds ===")
    for label, tswall in [
        ("before_1616", "2026-11-21 16:16:43+08"),
        ("after_1619", "2026-11-21 16:19:24+08"),
        ("before_1547", "2026-11-21 15:47:29+08"),
        ("after_1558", "2026-11-21 15:58:30+08"),
        ("before_1622", "2026-11-21 16:22:02+08"),
        ("after_1622", "2026-11-21 16:22:16+08"),
    ]:
        prev = c.execute("""
            SELECT tick, ts FROM room_stats WHERE room='W46N8' AND ts <= %s ORDER BY tick DESC LIMIT 2
        """, (tswall,)).fetchall()
        nxt = c.execute("""
            SELECT tick, ts FROM room_stats WHERE room='W46N8' AND ts >= %s ORDER BY tick LIMIT 2
        """, (tswall,)).fetchall()
        p(f"  {label} {tswall} prev={prev} next={nxt}")

    p("=== storage path last hour (every 20 ticks + min/max + under-15k spans) ===")
    rows = c.execute("""
        SELECT tick, ts, storage, progress FROM room_stats
        WHERE room='W46N8' AND tick >= %s ORDER BY tick
    """, (LAST_TIP,)).fetchall()
    if rows:
        stor = [r[2] for r in rows if r[2] is not None]
        p(f"  n={len(rows)} first={rows[0]} last={rows[-1]} min={min(stor)} max={max(stor)}")
        # sample every ~20
        last_printed=None
        for r in rows:
            if last_printed is None or r[0]-last_printed>=20 or r is rows[-1]:
                p(f"    {r[0]} {r[1]} stor={r[2]} p={r[3]}")
                last_printed=r[0]
        # under 15k spans
        under=[]
        cur=None
        for r in rows:
            if r[2] is not None and r[2] < 15000:
                if cur is None:
                    cur=[r,r]
                else:
                    cur[1]=r
            else:
                if cur:
                    under.append(cur); cur=None
        if cur: under.append(cur)
        p("  under-15k spans:")
        for a,b in under:
            p(f"    {a[0]}..{b[0]} stor {a[2]}..{b[2]} ts {a[1]}..{b[1]}")
        # 20k/300t: last 300 ticks max, and 3h max
        tip=rows[-1][0]
        row300=c.execute("""
            SELECT max(storage), min(storage) FROM room_stats WHERE room='W46N8' AND tick BETWEEN %s AND %s
        """, (tip-299, tip)).fetchone()
        row3h=c.execute("""
            SELECT max(storage), min(storage), min(tick), max(tick) FROM room_stats
            WHERE room='W46N8' AND tick BETWEEN %s AND %s
        """, (tip-int(3*3600/4.27), tip)).fetchone()
        p(f"  last300 min/max stor={row300}  3h min/max={row3h}")

    p("=== W47 storage path last hour ===")
    rows = c.execute("""
        SELECT tick, ts, storage, progress FROM room_stats
        WHERE room='W47N8' AND tick >= %s ORDER BY tick
    """, (LAST_TIP,)).fetchall()
    if rows:
        stor = [r[2] for r in rows if r[2] is not None]
        p(f"  n={len(rows)} first={rows[0]} last={rows[-1]} min={min(stor)} max={max(stor)}")
        last_printed=None
        for r in rows:
            if last_printed is None or r[0]-last_printed>=40 or r is rows[-1]:
                p(f"    {r[0]} {r[1]} stor={r[2]} p={r[3]}")
                last_printed=r[0]
        tip=rows[-1][0]
        row500=c.execute("""
            SELECT max(storage), min(storage), count(*) FROM room_stats
            WHERE room='W47N8' AND tick BETWEEN %s AND %s AND storage>=40000
        """, (tip-499, tip)).fetchone()
        rowmm=c.execute("""
            SELECT max(storage), min(storage) FROM room_stats WHERE room='W47N8' AND tick BETWEEN %s AND %s
        """, (tip-499, tip)).fetchone()
        p(f"  last500 ticks >=40k count/max/min={row500} last500 min/max={rowmm}")

    p("=== CPU last hour ===")
    row = c.execute("""
        SELECT count(*), avg(cpu), max(cpu), min(bucket), max(bucket)
        FROM room_stats WHERE room='W46N8' AND tick >= %s
    """, (LAST_TIP,)).fetchone()
    p("  since LAST_TIP", row)
    mx = c.execute("""
        SELECT tick, ts, cpu, bucket FROM room_stats
        WHERE room='W46N8' AND tick >= %s ORDER BY cpu DESC LIMIT 5
    """, (LAST_TIP,)).fetchall()
    p("  top cpu", mx)
    # also 1h wall
    row1h = c.execute("""
        SELECT count(*), avg(cpu), max(cpu), min(bucket)
        FROM room_stats WHERE room='W46N8' AND ts >= now() - interval '1 hour'
    """).fetchone()
    p("  wall 1h", row1h)
    mx1h = c.execute("""
        SELECT tick, ts, cpu, bucket FROM room_stats
        WHERE room='W46N8' AND ts >= now() - interval '1 hour'
        ORDER BY cpu DESC LIMIT 3
    """).fetchall()
    p("  wall 1h top cpu", mx1h)

    p("=== defender / core timeline (creep_ticks + names) ===")
    # names of interest
    names = c.execute("""
        SELECT DISTINCT name FROM creep_ticks
        WHERE tick BETWEEN 84395800 AND 84396900
          AND (name ILIKE '%def%' OR name ILIKE '%guard%' OR name ILIKE '%core%'
               OR name ILIKE 'rminer%' OR name ILIKE 'rhauler%' OR name ILIKE 'reserver%')
        ORDER BY name
    """).fetchall()
    p("  names", [n[0] for n in names])

    for name in [
        "defender84395887",
        "w8defender84395962",
        "w8guard84395961",
        "rdef84394792",
    ]:
        rows = c.execute("""
            SELECT tick, room, x, y, hits, hits_max, ttl, spawning, fatigue
            FROM creep_ticks WHERE name=%s AND tick BETWEEN 84395800 AND 84396900
            ORDER BY tick
        """, (name,)).fetchall()
        p(f"-- {name} n={len(rows)}")
        if not rows:
            continue
        p(f"  first {rows[0]}")
        p(f"  last  {rows[-1]}")
        # room changes and hits changes
        prev=None
        for r in rows:
            if prev is None or prev[1]!=r[1] or (prev[4]!=r[4] and r[4] is not None) or (r[7] and not prev[7]) or (prev[7] and not r[7]):
                p(f"    chg {r}")
            prev=r
        # also sample every 50
        last_s=None
        for r in rows:
            if last_s is None or r[0]-last_s>=80:
                p(f"    samp {r}")
                last_s=r[0]
        p(f"    last samp {rows[-1]}")

    # Invader / core objects if stored
    p("=== hostile / invader_core in creep_ticks (type or name) ===")
    # discover columns
    cols = [r[0] for r in c.execute("SELECT column_name FROM information_schema.columns WHERE table_name='creep_ticks' ORDER BY ordinal_position")]
    p("  creep_ticks cols", cols)

    # W45N7 occupancy around core event
    p("=== W45N7 my creeps around 84395886..84396400 ===")
    rows = c.execute("""
        SELECT tick, name, x, y, hits, ttl, role
        FROM creep_ticks
        WHERE room='W45N7' AND tick BETWEEN 84395880 AND 84396400
        ORDER BY tick, name
    """).fetchall()
    # first/last per name, and first tick after gap
    by={}
    ticks_present=set()
    for r in rows:
        by.setdefault(r[1], []).append(r)
        ticks_present.add(r[0])
    p(f"  rows={len(rows)} distinct ticks={len(ticks_present)} names={list(by)}")
    for n,rs in by.items():
        p(f"  {n} first={rs[0]} last={rs[-1]} n={len(rs)}")
        # room entry: already in W45N7
        # hits changes
        prev=None
        for r in rs:
            if prev is None or (prev[4]!=r[4]):
                if prev and r[0]-prev[0]>1:
                    pass
                p(f"    hits/enter {r}")
            prev=r

    # first civilian return after 84396271
    p("=== first W45N7 ticks after clear 84396271 ===")
    rows = c.execute("""
        SELECT tick, name, x, y, hits, ttl, role
        FROM creep_ticks WHERE room='W45N7' AND tick >= 84396271
        ORDER BY tick, name LIMIT 40
    """).fetchall()
    for r in rows[:40]:
        p(" ", r)

    # reservation if stored in room_stats or elsewhere
    p("=== hostiles in owned rooms since LAST_TIP ===")
    for room in ("W46N8","W47N8"):
        row=c.execute("""
            SELECT count(*) FILTER (WHERE hostiles>0), max(hostiles),
                   min(tick) FILTER (WHERE hostiles>0), max(tick) FILTER (WHERE hostiles>0)
            FROM room_stats WHERE room=%s AND tick>=%s
        """, (room, LAST_TIP)).fetchone()
        p(room, row)

    p("=== commit values in room_stats since LAST_TIP ===")
    rows=c.execute("""
        SELECT commit, min(tick), max(tick), count(*)
        FROM room_stats WHERE room='W46N8' AND tick>=%s
        GROUP BY commit ORDER BY min(tick)
    """, (LAST_TIP,)).fetchall()
    p(rows)

    p("=== console incidents after 15:00 if table exists ===")
    try:
        # try common tables
        tables=[r[0] for r in c.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema='public' AND table_name ILIKE '%event%' OR table_name ILIKE '%alert%' OR table_name ILIKE '%incident%' OR table_name ILIKE '%console%'
        """).fetchall()]
        p("  tables", tables)
    except Exception as e:
        p("  err", e)
        c.rollback()

    p("DONE")

if __name__ == "__main__":
    main()
