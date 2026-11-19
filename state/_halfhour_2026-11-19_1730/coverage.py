#!/usr/bin/env python3
"""Coverage and official empty-no-creep ranges for this 40-minute window."""
from __future__ import annotations
import json
from datetime import datetime
from zoneinfo import ZoneInfo
import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db

TMIN, TMAX = 84355901, 84356600
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
DIR = "/workspace/screeps/state/_halfhour_2026-11-19_1730"
# First pass 35 of 35 official GETs 200, missing_chunks=0.
# published_bases 84355900..84356500; reconstructed 84355901..84356600 (700).
# Aged leftovers already outside this window. 17:00 half-hour already official-filled through 84356300 (published_bases 84355600..84356200); just-published 84356300 was not attempted then (gt=84356338 in-progress). Concurrent 17:23 hourly patrol already wrote 84355801..84356500 including 84356300 and 84356400 (gt=84356580, inserted=5713); 84356500 was still in-progress then and is included in this first pass (200 in all 5 rooms, inserted=3546 new).
# New room_stats gap this window: 84356451..84356569 (119, from the 17:15:27-17:23:42 box freeze); official window covers through 84356600 so this gap is fully inside published history. Prior gap 84356051..84356309 (259, 16:43-17:02 freeze) already official-filled last pass (through 84356300) plus patrol/this overlap for the 9-tick tail. Listener auto-restart 17:23:45 after the new freeze; this run did not restart the listener.
IN_WINDOW_404 = set()  # first pass 35/35 official 200, missing_chunks=0; leftover official 404s aged out of this window
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
