#!/usr/bin/env python3
"""Coverage and official empty-no-creep ranges for the 40-minute backfill window."""
from __future__ import annotations
import json, sys
from datetime import datetime
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import db

TMIN, TMAX = 84367801, 84368500
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
DIR = "/workspace/screeps/state/_patrol_2026-11-20_0717"
IN_WINDOW_404 = {("W45N8", 84368100)}
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
                "empty_ranges": empty,
                "official_404": sum(b - a + 1 for a, b in hole),
                "hole_ranges": hole,
                "min": ticks[0] if ticks else None,
                "max": ticks[-1] if ticks else None,
            }
    tot = TMAX - TMIN + 1
    rec = sum(coverage[r]["distinct"] for r in ROOMS)
    emp = sum(coverage[r]["official_empty_no_creep"] for r in ROOMS)
    hol = sum(coverage[r]["official_404"] for r in ROOMS)
    print(f"coverage official_recovered={rec}/{tot*len(ROOMS)} empty_no_creep={emp} official_404={hol}")
    for room in ROOMS:
        d = coverage[room]
        print(f"  {room} distinct={d['distinct']} missing={d['missing_n']} empty={d['official_empty_no_creep']} 404={d['official_404']} ranges_empty={d['empty_ranges']} holes={d['hole_ranges']}")
    out = {
        "tmin": TMIN, "tmax": TMAX, "rooms": list(ROOMS),
        "unique_rows": unique[0], "unique_creep_tick": unique[1],
        "unique_ticks": unique[2], "unique_room_tick": unique[3],
        "recovered": rec, "want": tot * len(ROOMS),
        "empty_no_creep": emp, "official_404": hol,
        "coverage": coverage,
        "at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
    }
    open(OUT, "w").write(json.dumps(out, indent=2, default=str) + "\n")
    print("wrote", OUT)

if __name__ == "__main__":
    main()
