#!/usr/bin/env python3
"""Coverage and official empty-no-creep ranges for this 40-minute window."""
from __future__ import annotations
import json
from datetime import datetime
from zoneinfo import ZoneInfo
import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db

TMIN, TMAX = 84454001, 84454700
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
DIR = "/workspace/screeps/state/_halfhour_2026-11-24_1230"
# First pass --minutes 40. First pass 35/35 official GETs 200, missing_chunks=0.
# published_bases 84441000..84441600 at game.time=84441737; reconstructed
# 84441001..84441700 (700). Quiet 2030 official-filled 84440601..84441300
# / JP 84441300. No first-pass in-window 404 this 2100 pass.
# Already-told leftover official 404 W47N7@84440900 (from quiet 2030 /
# told in 20:44 2028 patrol) aged out of window start 84441001 by 1 tick;
# retried as near-window on confirm/retry2/late/postjp; do not relabel NEW.
# Already-told leftovers W45N8@84439200 / W45N8@84439300 / W45N8@84439500
# (from quiet 1830) and W47N7@84438700 (from quiet 1730 JP) also aged out;
# retry as near-window; do not relabel NEW.
# Already-told leftovers W45N8@84437100, W47N7@84436400 and older aged out
# of 84441001; not retried.
# First pass inserted=9432 already_in_db=16526 ts_realigned=12; tick_s printed 4.199.
# Do not restart the listener. Do not write a patrol folder.
IN_WINDOW_404 = {
    ("W46N8", 84454300),  # first-pass in-window official 404 this 1230 pass; still 404 through confirm/retry2/late
    ("W47N7", 84454200),  # leftover official 404 from quiet 1200 JP (NOT YET TOLD); still 404 at 1230 first pass and confirm/retry2/late
    ("W46N8", 84454100),  # leftover official 404 from quiet 1200 first pass (NOT YET TOLD); still 404 at 1230 first pass and confirm/retry2/late
}
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
    expected = 5 * (TMAX - TMIN + 1)
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

