#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path

sys.path.insert(0, "/workspace/screeps/tools")
import db

ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
LAST_TIP = 84409680
KNOWN_404 = [
    ("W46N8", 84408300),
    ("W47N8", 84408300),
    ("W47N7", 84407900),
    ("W45N8", 84407700),
    ("W46N8", 84407000),
    ("W45N8", 84406400),
    ("W46N8", 84406600),
    ("W46N8", 84406700),
    ("W45N7", 84403700),
    ("W45N7", 84403800),
    ("W45N7", 84400300),
    ("W45N7", 84400400),
    ("W47N8", 84400100),
]

def gaps(ticks):
    if not ticks:
        return []
    ticks = sorted(set(ticks))
    out = []
    expect = ticks[0]
    for t in ticks:
        if t > expect:
            out.append((expect, t - 1, t - expect))
        expect = t + 1
    return out

def main():
    with db.connect() as c:
        print("=== room_stats latest ===")
        rows = c.execute("SELECT room, max(tick), max(ts) FROM room_stats GROUP BY room ORDER BY 1").fetchall()
        for r in rows:
            print(" ", r)

        print("=== room_stats since LAST_TIP-200 ===")
        rows = c.execute(
            "SELECT tick, ts, cpu, bucket FROM room_stats WHERE room='W46N8' AND tick>=%s ORDER BY tick",
            (LAST_TIP - 200,),
        ).fetchall()
        ticks = [r[0] for r in rows]
        print(f" n={len(ticks)} min={ticks[0] if ticks else None} max={ticks[-1] if ticks else None}")
        gs = gaps(ticks)
        print(f" gaps n={len(gs)}")
        for g in gs:
            print("  STATS_GAP", g)

        print("=== room_stats around freezes and this hour (sample edges) ===")
        for lo, hi in ((84406400, 84406750), (84406431, 84406719), (84406850, 84406990)):
            rows = c.execute(
                "SELECT tick, ts FROM room_stats WHERE room='W46N8' AND tick>=%s AND tick<=%s ORDER BY tick",
                (lo, hi),
            ).fetchall()
            ts = [r[0] for r in rows]
            print(f"  {lo}..{hi} n={len(ts)} min={ts[0] if ts else None} max={ts[-1] if ts else None} gaps={gaps(ts)[:12]}")

        print("=== creep_ticks coverage LAST_TIP+1..max ===")
        mx = c.execute("SELECT max(tick) FROM creep_ticks").fetchone()[0]
        print(" global max", mx)
        for room in ROOMS:
            ts = [r[0] for r in c.execute(
                "SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick>=%s AND tick<=%s ORDER BY 1",
                (room, LAST_TIP + 1, mx),
            ).fetchall()]
            want = mx - LAST_TIP
            gs = gaps(ts)
            missing = 0
            if ts:
                if ts[0] > LAST_TIP + 1:
                    gs = [(LAST_TIP + 1, ts[0] - 1, ts[0] - LAST_TIP - 1)] + gs
                if ts[-1] < mx:
                    gs = gs + [(ts[-1] + 1, mx, mx - ts[-1])]
                missing = sum(g[2] for g in gs)
            print(f"  {room} distinct={len(ts)} range={ts[0] if ts else None}..{ts[-1] if ts else None} want~{want} missing_ticks={missing} spans={gs[:8]}")

        print("=== freeze window creep_ticks 84406431..84406719 and 84406881..84406949 ===")
        for lo,hi,want in ((84406431,84406719,289),(84406881,84406949,69)):
          print(f"  window {lo}..{hi} want={want}")
          for room in ROOMS:
            n = c.execute(
                "SELECT count(DISTINCT tick) FROM creep_ticks WHERE room=%s AND tick>=%s AND tick<=%s",
                (room, lo, hi),
            ).fetchone()[0]
            print(f"    {room} {n}/{want}")

        print("=== infer 03:40-04:30 freeze STATS holes ===")
        rows = c.execute(
            """
            SELECT tick, ts FROM room_stats
            WHERE room='W46N8' AND ts >= '2026-11-22 03:40:00+08' AND ts <= '2026-11-22 04:30:00+08'
            ORDER BY tick
            """
        ).fetchall()
        print(f" stats samples 03:40-04:30 n={len(rows)}")
        prev = None
        for tick, ts in rows:
            if prev and (tick - prev[0] > 15 or (ts - prev[1]).total_seconds() > 60):
                print(f"  jump {prev[0]} {prev[1]} -> {tick} {ts} dtick={tick-prev[0]} dsec={(ts-prev[1]).total_seconds():.1f}")
            prev = (tick, ts)
        if rows:
            print("  first", rows[0], "last", rows[-1])

        print("=== leftover official-404 chunk presence ===")
        for room, base in KNOWN_404:
            lo, hi = base + 1, base + 100
            n = c.execute(
                "SELECT count(DISTINCT tick) FROM creep_ticks WHERE room=%s AND tick>=%s AND tick<=%s",
                (room, lo, hi),
            ).fetchone()[0]
            mn, mxv = c.execute(
                "SELECT min(tick), max(tick) FROM creep_ticks WHERE room=%s AND tick>=%s AND tick<=%s",
                (room, lo, hi),
            ).fetchone()
            print(f"  {room}@{base} distinct={n}/100 range={mn}..{mxv}")

        print("=== room_stats last 8 raw ===")
        cols = [r[0] for r in c.execute(
            """SELECT column_name FROM information_schema.columns
               WHERE table_name='room_stats' ORDER BY ordinal_position"""
        ).fetchall()]
        print(" COLS", cols)
        for room in ("W46N8", "W47N8"):
            rows = c.execute(
                "SELECT * FROM room_stats WHERE room=%s ORDER BY tick DESC LIMIT 6",
                (room,),
            ).fetchall()
            for r in rows:
                print(" ", room, r)

        print("=== incidents since LAST_TIP ===")
        try:
            rows = c.execute("SELECT * FROM incidents WHERE tick>=%s ORDER BY tick", (LAST_TIP,)).fetchall()
            print(" n", len(rows))
            for r in rows[:20]:
                print(" ", r)
        except Exception as e:
            print(" incidents err", e)

        print("=== listener_rot / live files ===")
        live = json.loads(Path("/workspace/screeps/metrics/live.json").read_text())
        rot = json.loads(Path("/workspace/screeps/metrics/listener_rot.json").read_text())
        print(" live.updated", live.get("updated"), "roomSlot", live.get("roomSlot"), "stats.t", (live.get("stats") or {}).get("t"))
        print(" rot", rot)

if __name__ == "__main__":
    main()
