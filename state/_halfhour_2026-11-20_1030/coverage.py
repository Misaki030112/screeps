#!/usr/bin/env python3
"""Coverage and official empty-no-creep ranges for this 40-minute window."""
from __future__ import annotations
import json
from datetime import datetime
from zoneinfo import ZoneInfo
import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db

TMIN, TMAX = 84370701, 84371400
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
DIR = "/workspace/screeps/state/_halfhour_2026-11-20_1030"
# First pass 35 of 35 official GETs 200, missing_chunks=0.
# published_bases 84370700..84371300 at game.time=84371416; reconstructed 84370701..84371400 (700).
# 10:00 half-hour already official-filled through 84370800 / reconstructed through 84370900 (just-published 84370900 written 10:11:26 for all 5, ticks 84370901..84371000).
# CONCURRENT 1h patrol _patrol_2026-11-20_1025 already official-filled 84370501..84371200 and just-published 84371200 at 10:35:10 (game.time=84371383, all 5 HTTP 200, inserted=3027). This first pass already_in_db=23071 / inserted=2758
# (W46N8 1138, W47N8 802, W45N8 364, W45N7 0, W47N7 454); overlap from 10:00 half-hour official fill through 84371000, patrol official fill through 84371200, patrol just-published 84371200 (ticks 84371201..84371300), plus live rotation.
# No in-window official 404. Leftover official 404 W45N8@84368100 and older aged out of this window start 84370701 and were not retried (1h patrol official_retry 10:35 still 404 on all 16).
# NEW box freeze 10:15:38-10:25:57 (611s) STATS gap 84371101..84371259 (159) sits inside this window; listener auto-restart 10:26:00 (pid 1251176 started 10:26:10).
# Prior STATS gap 84370641..84370929 (09:44 freeze) still overlaps this window start 84370701 and was already official-filled (told status left to the concurrent 1h patrol). Prior 84370151..84370319 has aged out of this window start.
IN_WINDOW_404 = set()  # first pass 35/35 official 200, missing_chunks=0
OUT = sys.argv[1] if len(sys.argv) > 1 else f"{DIR}/coverage_final.json"

def chunk_base(tick):
    return ((tick - 1) // 100) * 100

def ranges(ticks, tmin=TMIN, tmax=TMAX):
    missing, start, s = [], None, set(ticks)
    for t in range(tmin, tmax + 1):
        if t not in s:
            if start is None:
                start = t
        elif start is not None:
            missing.append([start, t - 1])
            start = None
    if start is not None:
        missing.append([start, tmax])
    return missing

def split_missing(miss, room):
    empty, hole = [], []
    for a, b in miss:
        cur_kind = None
        seg_start = a
        for tick in range(a, b + 1):
            base = chunk_base(tick)
            kind = "hole" if (room, base) in IN_WINDOW_404 else "empty"
            if cur_kind is None:
                cur_kind = kind
                seg_start = tick
            elif kind != cur_kind:
                (hole if cur_kind == "hole" else empty).append([seg_start, tick - 1])
                cur_kind = kind
                seg_start = tick
        if cur_kind is not None:
            (hole if cur_kind == "hole" else empty).append([seg_start, b])
    return empty, hole

def main():
    coverage = {}
    with db.connect() as c:
        unique = c.execute(
            """SELECT count(*), count(DISTINCT (creep, tick)), count(DISTINCT tick),
                      count(DISTINCT (room, tick))
               FROM creep_ticks WHERE tick BETWEEN %s AND %s AND room = ANY(%s)""",
            (TMIN, TMAX, list(ROOMS)),
        ).fetchone()
        for room in ROOMS:
            ticks = [r[0] for r in c.execute(
                "SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s ORDER BY 1",
                (room, TMIN, TMAX),
            ).fetchall()]
            miss = ranges(ticks)
            empty, hole = split_missing(miss, room)
            coverage[room] = {
                "distinct": len(ticks),
                "missing_n": sum(b - a + 1 for a, b in miss),
                "missing_ranges": miss,
                "official_empty_no_creep": sum(b - a + 1 for a, b in empty),
                "official_empty_no_creep_ranges": empty,
                "official_404_missing": sum(b - a + 1 for a, b in hole),
                "official_404_ranges": hole,
            }
    expected = 5 * 700
    recovered = sum(coverage[r]["distinct"] for r in ROOMS)
    empty_no_creep = sum(coverage[r]["official_empty_no_creep"] for r in ROOMS)
    official_404_missing = sum(coverage[r]["official_404_missing"] for r in ROOMS)
    payload = {
        "coverage": coverage,
        "official_recovered": recovered,
        "expected": expected,
        "empty_no_creep": empty_no_creep,
        "official_404_missing": official_404_missing,
        "unique_after": {
            "rows": unique[0],
            "unique_creep_tick_rows": unique[1],
            "distinct_ticks": unique[2],
            "distinct_room_ticks": unique[3],
        },
        "at": datetime.now(ZoneInfo("Asia/Hong_Kong")).isoformat(),
    }
    Path = __import__("pathlib").Path
    Path(OUT).write_text(json.dumps(payload, indent=2) + chr(10))
    print(f"coverage official_recovered={recovered}/{expected} empty_no_creep={empty_no_creep} official_404={official_404_missing}")
    for room in ROOMS:
        c = coverage[room]
        print(f"  {room} distinct={c['distinct']} missing={c['missing_n']} empty={c['official_empty_no_creep']} 404={c['official_404_missing']}")
    print("wrote", OUT)

if __name__ == "__main__":
    main()
