#!/usr/bin/env python3
"""Coverage and official empty-no-creep ranges for this 40-minute window."""
from __future__ import annotations
import json
from datetime import datetime
from zoneinfo import ZoneInfo
import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db

TMIN, TMAX = 84371901, 84372600
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
DIR = "/workspace/screeps/state/_halfhour_2026-11-20_1200"
# First pass 34 of 35 official GETs 200, missing_chunks=1 (W46N8@84371600 404; confirm 11:01:39 gt=84371767 still 404, inserted=0).
# published_bases 84371000..84371600 at game.time=84371748; reconstructed 84371001..84371700 (700).
# 10:30 half-hour already official-filled through 84371300 / reconstructed through 84371400 (just-published 84371400 written 10:46:08 for all 5, ticks 84371401..84371500).
# Prior 1h patrol _patrol_2026-11-20_1025 already official-filled 84370501..84371200 and just-published 84371200 at 10:35:10. This first pass already_in_db=17896 / inserted=5417
# (W46N8 319, W47N8 2500, W45N8 1107, W45N7 705, W47N7 786); overlap from 10:30 half-hour official fill through 84371500, patrol official fill through 84371300, plus live rotation.
# In-window official 404: W46N8@84371600 (ticks 84371601..84371700). Leftover official 404 W45N8@84368100 and older aged out of this window start 84371001 and were not retried.
# NEW box freeze 10:49:41-10:58:24 (516s) STATS gap 84371591..84371729 (139) sits inside/beyond this window; listener auto-restart 10:58:27 (pid 1264845 started 10:58:37). Official published covers through 84371700; tail 84371701..84371729 waits on just-published 84371700.
# Prior STATS gaps 84371101..84371259 (10:15 freeze) and 84370641..84370929 (09:44 freeze; 84370641..84371000 is before this window start) — 84371101..84371259 sits inside this window and was already official-filled (told status left to the 10:25/next 1h patrol).
IN_WINDOW_404 = set()  # first pass 35/35 official GETs 200, missing_chunks=0; just-published base 84372600 is outside first-pass TMAX=84372600
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
