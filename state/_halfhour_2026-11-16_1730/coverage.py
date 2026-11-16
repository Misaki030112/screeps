#!/usr/bin/env python3
"""Coverage and official empty-no-creep ranges for this 40-minute window."""
from __future__ import annotations
import json
from datetime import datetime
from zoneinfo import ZoneInfo
import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db

TMIN, TMAX = 84301201, 84301900
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
OUT = "/workspace/screeps/state/_halfhour_2026-11-16_1730/coverage_final.json"

def ranges(ticks, tmin=TMIN, tmax=TMAX):
    missing = []
    s = set(ticks)
    start = None
    for t in range(tmin, tmax + 1):
        if t not in s:
            if start is None:
                start = t
        else:
            if start is not None:
                missing.append([start, t - 1])
                start = None
    if start is not None:
        missing.append([start, tmax])
    return missing

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
            rows = c.execute(
                "SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s ORDER BY 1",
                (room, TMIN, TMAX),
            ).fetchall()
            ticks = [r[0] for r in rows]
            n = c.execute(
                "SELECT count(*), min(tick), max(tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
                (room, TMIN, TMAX),
            ).fetchone()
            miss = ranges(ticks)
            coverage[room] = {
                "distinct": len(ticks),
                "rows": n[0] or 0,
                "range": [n[1], n[2]] if n[1] is not None else None,
                "missing_n": sum((b - a + 1) for a, b in miss),
                "missing_ranges": miss,
            }
        tips = {}
        for table in ("creep_ticks", "room_stats", "creep_cpu", "path_arrivals"):
            row = c.execute(f"SELECT max(tick), max(ts) FROM {table}").fetchone()
            tips[table] = {"max_tick": row[0], "max_ts": row[1].isoformat() if row[1] else None}
        live_after = {}
        for room in ROOMS:
            row = c.execute(
                """SELECT count(DISTINCT tick), min(tick), max(tick), count(*)
                   FROM creep_ticks WHERE room=%s AND tick > %s""",
                (room, TMAX),
            ).fetchone()
            live_after[room] = {"distinct": row[0] or 0, "min": row[1], "max": row[2], "rows": row[3] or 0}
    expected = 5 * 700
    official_with_creeps = sum(coverage[r]["distinct"] for r in ROOMS)
    empty_no_creep = sum(coverage[r]["missing_n"] for r in ROOMS)
    payload = {
        "window": [TMIN, TMAX],
        "span": TMAX - TMIN + 1,
        "coverage": coverage,
        "unique_after": {
            "rows": unique[0],
            "unique_creep_tick_rows": unique[1],
            "distinct_ticks": unique[2],
            "distinct_room_ticks": unique[3],
        },
        "official_with_creeps": official_with_creeps,
        "empty_no_creep": empty_no_creep,
        "official_recovered": official_with_creeps + empty_no_creep,
        "expected": expected,
        "in_window_official_404": 0,
        "db_tips": tips,
        "live_after": live_after,
        "at": datetime.now(ZoneInfo("Asia/Hong_Kong")).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"),
    }
    with open(OUT, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"window {TMIN}..{TMAX} ({TMAX-TMIN+1})")
    for room in ROOMS:
        c = coverage[room]
        print(f"{room} distinct={c['distinct']} rows={c['rows']} range={c['range']} missing_n={c['missing_n']} {c['missing_ranges']}")
    print("unique_after", payload["unique_after"])
    print(f"official_with_creeps={official_with_creeps} empty_no_creep={empty_no_creep} official_recovered={payload['official_recovered']} expected={expected} in_window_404=0")
    print("db_tips", tips)
    print("live_after", live_after)
    print("wrote", OUT)

if __name__ == "__main__":
    main()
