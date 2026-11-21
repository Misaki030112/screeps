#!/usr/bin/env python3
"""Defender/core timeline, freeze creep_ticks fill, later stats, reservation."""
from __future__ import annotations
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import db

HK = ZoneInfo("Asia/Hong_Kong")

def p(*a):
    print(*a, flush=True)

def ranges(ticks):
    if not ticks:
        return []
    ticks=sorted(ticks)
    out=[]; s=e=ticks[0]
    for t in ticks[1:]:
        if t==e+1:
            e=t
        else:
            out.append((s,e,e-s+1)); s=e=t
    out.append((s,e,e-s+1))
    return out

def main():
    c=db.connect()
    names=["defender84395887","w8defender84395962","w8guard84395961","rdef84394792"]
    p("=== defender traces ===")
    for name in names:
        rows=c.execute("""
            SELECT tick, ts, room, x, y, hits, store, state, role
            FROM creep_ticks WHERE creep=%s AND tick BETWEEN 84395800 AND 84397000
            ORDER BY tick
        """, (name,)).fetchall()
        p(f"-- {name} n={len(rows)}")
        if not rows:
            continue
        p(f"  first {rows[0]}")
        p(f"  last  {rows[-1]}")
        prev=None
        for r in rows:
            chg = (prev is None or prev[2]!=r[2] or prev[5]!=r[5] or (prev[7]!=r[7] and (prev[7] in ('spawning','spawn') or r[7] in ('spawning','spawn') or prev[7]!=r[7])))
            # room change, hits change, state change
            if prev is None or prev[2]!=r[2] or (prev[5]!=r[5] and r[5] is not None) or prev[7]!=r[7]:
                p(f"    chg {r}")
            prev=r
        # samples every 40
        last=None
        for r in rows:
            if last is None or r[0]-last>=50:
                p(f"    samp {r}"); last=r[0]
        p(f"    ends {rows[-1]}")
        # present ranges
        p(f"    ranges {ranges([r[0] for r in rows])}")
        # hits min/max
        hs=[r[5] for r in rows if r[5] is not None]
        if hs:
            p(f"    hits min={min(hs)} max={max(hs)}")

    p("=== W45N7 occupancy 84395880..84396500 ===")
    rows=c.execute("""
        SELECT tick, creep, role, x, y, hits, state
        FROM creep_ticks WHERE room='W45N7' AND tick BETWEEN 84395880 AND 84396500
        ORDER BY tick, creep
    """).fetchall()
    by={}
    for r in rows:
        by.setdefault(r[1], []).append(r)
    p(f"  rows={len(rows)} names={list(by)}")
    for n,rs in by.items():
        p(f"  {n} role={rs[0][2]} n={len(rs)} first={rs[0]} last={rs[-1]}")
        # room entry hits changes
        prev=None
        for r in rs:
            if prev is None or prev[5]!=r[5] or prev[6]!=r[6]:
                p(f"    chg {r}")
            prev=r

    p("=== first civilians back in W45N7 after 84396271 ===")
    rows=c.execute("""
        SELECT tick, ts, creep, role, x, y, hits, state
        FROM creep_ticks WHERE room='W45N7' AND tick>=84396271
        ORDER BY tick, creep LIMIT 60
    """).fetchall()
    seen=set()
    for r in rows:
        if r[2] not in seen or True:
            if r[2] not in seen:
                p(f"  first {r}")
                seen.add(r[2])
    p(f"  first tick present {rows[0] if rows else None}")

    p("=== last civilians leaving W45N7 before/during core ===")
    rows=c.execute("""
        SELECT tick, ts, creep, role, x, y
        FROM creep_ticks WHERE room='W45N7' AND tick BETWEEN 84395800 AND 84396340
        ORDER BY tick
    """).fetchall()
    if rows:
        p(f"  last before clear window: {rows[-1]}")
        # last tick per creep
        last={}
        first={}
        for r in rows:
            if r[2] not in first: first[r[2]]=r
            last[r[2]]=r
        for n in last:
            p(f"  {n} first {first[n]} last {last[n]}")

    p("=== freeze 16:16 creep_ticks 84396751..84396799 ===")
    for room in ("W46N8","W47N8","W45N8","W45N7","W47N7"):
        row=c.execute("""
            SELECT count(DISTINCT tick), min(tick), max(tick), count(*)
            FROM creep_ticks WHERE room=%s AND tick BETWEEN 84396751 AND 84396799
        """, (room,)).fetchone()
        present={r[0] for r in c.execute("SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN 84396751 AND 84396799",(room,))}
        miss=[t for t in range(84396751,84396800) if t not in present]
        p(f"  {room} {row[0]}/49 min={row[1]} max={row[2]} rows={row[3]} missing={len(miss)} {ranges(miss)[:8]}")

    p("=== WS ping/pong 16:22 creep_ticks 84396821..84396839 ===")
    for room in ("W46N8","W47N8","W45N8","W45N7","W47N7"):
        row=c.execute("""
            SELECT count(DISTINCT tick), min(tick), max(tick), count(*)
            FROM creep_ticks WHERE room=%s AND tick BETWEEN 84396821 AND 84396839
        """, (room,)).fetchone()
        present={r[0] for r in c.execute("SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN 84396821 AND 84396839",(room,))}
        miss=[t for t in range(84396821,84396840) if t not in present]
        p(f"  {room} {row[0]}/19 min={row[1]} max={row[2]} rows={row[3]} missing={len(miss)} {ranges(miss)}")

    p("=== unpublished/live tail 84396801.. now ===")
    mx=c.execute("SELECT max(tick) FROM room_stats WHERE room='W46N8'").fetchone()[0]
    p("  max room_stats", mx)
    mx2=c.execute("SELECT max(tick) FROM creep_ticks").fetchone()[0]
    p("  max creep_ticks", mx2)
    for room in ("W46N8","W47N8","W45N8","W45N7","W47N7"):
        row=c.execute("""
            SELECT count(DISTINCT tick), min(tick), max(tick)
            FROM creep_ticks WHERE room=%s AND tick>=84396801
        """, (room,)).fetchone()
        p(f"  {room} distinct={row}")

    p("=== later room_stats after 84396870 ===")
    for room in ("W46N8","W47N8"):
        rows=c.execute("""
            SELECT tick, ts, storage, progress, cpu, bucket, creeps
            FROM room_stats WHERE room=%s AND tick>=84396870 ORDER BY tick
        """, (room,)).fetchall()
        p(f"  {room} n={len(rows)}")
        for r in rows:
            p(f"    {r[0]} {r[1]} stor={r[2]} p={r[3]} cpu={r[4]} bkt={r[5]}")

    p("=== home storage samples since 84395990 (every sample) ===")
    rows=c.execute("""
        SELECT tick, ts, storage FROM room_stats
        WHERE room='W46N8' AND tick>=84395990 ORDER BY tick
    """).fetchall()
    for r in rows:
        p(f"  {r[0]} {r[1]} stor={r[2]}")
    stor=[r[2] for r in rows if r[2] is not None]
    p(f"  min={min(stor)} at {[r for r in rows if r[2]==min(stor)][0]} max={max(stor)} at {[r for r in rows if r[2]==max(stor)][-1]}")
    # under continuously?
    under=all(s<15000 for s in stor)
    p(f"  all_under_15k_since_last_tip={under}")

    p("=== W47 storage samples since 84395990 ===")
    rows=c.execute("""
        SELECT tick, ts, storage FROM room_stats
        WHERE room='W47N8' AND tick>=84395990 ORDER BY tick
    """).fetchall()
    stor=[r[2] for r in rows if r[2] is not None]
    p(f"  n={len(rows)} min={min(stor)} at {[r for r in rows if r[2]==min(stor)][0]} max={max(stor)} at {[r for r in rows if r[2]==max(stor)][0]} last={rows[-1]}")
    # 40k touches
    over=[r for r in rows if r[2] and r[2]>=40000]
    p(f"  >=40k samples {len(over)} {over[:5]}")

    p("=== nUp/w8up from creeps json since last ===")
    rows=c.execute("""
        SELECT tick, ts, storage, creeps
        FROM room_stats WHERE room='W46N8' AND tick>=84395990 ORDER BY tick
    """).fetchall()
    prev=None
    for r in rows:
        cr=r[3] or {}
        nup=cr.get('upgrader',0)
        w8=cr.get('w8upgrader',0)
        key=(nup,w8)
        if key!=prev:
            p(f"  {r[0]} {r[1]} stor={r[2]} nUp={nup} w8up={w8} creeps={cr}")
            prev=key
    p(f"  last {rows[-1][0]} nUp={(rows[-1][3] or {}).get('upgrader')} w8up={(rows[-1][3] or {}).get('w8upgrader')}")

    p("=== CPU 1h details ===")
    rows=c.execute("""
        SELECT tick, ts, cpu, bucket FROM room_stats
        WHERE room='W46N8' AND ts >= now() - interval '65 minutes'
        ORDER BY cpu DESC LIMIT 8
    """).fetchall()
    p("  top", rows)
    agg=c.execute("""
        SELECT min(cpu), max(cpu), avg(cpu), min(bucket), max(bucket), count(*)
        FROM room_stats WHERE room='W46N8' AND ts >= now() - interval '1 hour'
    """).fetchone()
    p("  wall1h", agg)

    p("=== listener python start times (best effort via /proc) skipped ===")
    p("DONE")

if __name__=='__main__':
    main()
