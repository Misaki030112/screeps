#!/usr/bin/env python3
"""Coverage and official empty-no-creep ranges for this 40-minute window."""
from __future__ import annotations
import json
from datetime import datetime
from zoneinfo import ZoneInfo
import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db

TMIN, TMAX = 84373701, 84374400
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
DIR = "/workspace/screeps/state/_halfhour_2026-11-20_1400"
# First pass 33 of 35 official GETs 200, missing_chunks=2 (W45N7@84373700 and W47N8@84373800 still 404 after confirm 14:09:17 gt=84374453 and retry2 14:12:11 gt=84374494, inserted=0).
# published_bases 84373700..84374300 at game.time=84374425; reconstructed 84373701..84374400 (700).
# 13:30 half-hour already official-filled through 84374000 / just-published 84374000 for all 5 (ticks 84374001..84374100 at 13:47:35 gt=84374141).
# Prior 1h patrol _patrol_2026-11-20_1316 already official-filled through 84373700. This first pass already_in_db=14250 / inserted=10925
# (W46N8 2791, W47N8 3539, W45N8 1949, W45N7 1208, W47N7 1438); overlap from 13:30 official fill through 84374100, patrol official fill through 84373700, plus live rotation.
# In-window official 404: W45N7@84373700 (ticks 84373701..84373789 hole; 11 live ticks 84373790..84373800 present) and W47N8@84373800 (ticks 84373801..84373900). Leftover official 404 W45N7@84373300, W47N7@84373200, W46N8@84371600 and older aged out of this window start 84373701 and were not retried.
# NEW box freeze 13:53:22-14:05:12 (702s) STATS gap 84374221..84374399 (179) sits inside this window; listener auto-restart 14:05:15 (pid 1340444 started 14:05:25). Official published covers through 84374400 (bases 84374200 and 84374300 200 for all 5).
# Prior STATS gap 84373871..84373979 (13:29 freeze) sits inside this window and was already official-filled except leftover 404 W47N8@84373800 hole (told=false, left to next 1h patrol). Earlier freezes/gaps aged out or were already told by the 13:25 patrol.
IN_WINDOW_404 = {("W45N7", 84373700), ("W47N8", 84373800)}  # still 404 after confirm 14:09:17 gt=84374453 and retry2 14:12:11 gt=84374494
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
