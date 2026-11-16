#!/usr/bin/env python3
"""Coverage and official empty-no-creep ranges for this 40-minute window."""
from __future__ import annotations
import json
from datetime import datetime
from zoneinfo import ZoneInfo
import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db

TMIN, TMAX = 84307101, 84307800
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
DIR = "/workspace/screeps/state/_halfhour_2026-11-17_0130"
# First-pass official 404 inside this reconstructed window: none
# (35 of 35 official GETs 200). Leftovers such as W45N8@84306500
# are just outside TMIN and retried as leftovers.
IN_WINDOW_404 = set()
OUT = sys.argv[1] if len(sys.argv) > 1 else f"{DIR}/coverage_final.json"

def chunk_base(tick):
    return ((tick - 1) // 100) * 100

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

def split_missing(miss, room):
    miss_404, miss_empty = [], []
    n404 = nempty = 0
    for a, b in miss:
        cur_404 = cur_empty = None
        for t in range(a, b + 1):
            is_404 = (room, chunk_base(t)) in IN_WINDOW_404
            if is_404:
                n404 += 1
                if cur_404 is None:
                    if cur_empty is not None:
                        miss_empty.append(cur_empty); cur_empty = None
                    cur_404 = [t, t]
                else:
                    cur_404[1] = t
            else:
                nempty += 1
                if cur_empty is None:
                    if cur_404 is not None:
                        miss_404.append(cur_404); cur_404 = None
                    cur_empty = [t, t]
                else:
                    cur_empty[1] = t
        if cur_404 is not None:
            miss_404.append(cur_404)
        if cur_empty is not None:
            miss_empty.append(cur_empty)
    return n404, miss_404, nempty, miss_empty

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
            n404, miss_404, nempty, miss_empty = split_missing(miss, room)
            coverage[room] = {
                "distinct": len(ticks),
                "rows": n[0] or 0,
                "range": [n[1], n[2]] if n[1] is not None else None,
                "missing_n": sum((b - a + 1) for a, b in miss),
                "missing_ranges": miss,
                "official_empty_no_creep": nempty,
                "official_empty_no_creep_ranges": miss_empty,
                "official_404_missing": n404,
                "official_404_missing_ranges": miss_404,
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
        # Any live-filled ticks inside official-404 hole(s)
        live_filled_404 = {}
        for room, base in sorted(IN_WINDOW_404):
            a, b = base + 1, base + 100
            row = c.execute(
                """SELECT count(DISTINCT tick), min(tick), max(tick), count(*)
                   FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s""",
                (room, a, b),
            ).fetchone()
            live_filled_404[f"{room}@{base}"] = {
                "distinct": row[0] or 0, "min": row[1], "max": row[2], "rows": row[3] or 0,
                "hole": [a, b],
            }
    expected = 5 * (TMAX - TMIN + 1)
    official_with_creeps = sum(coverage[r]["distinct"] for r in ROOMS)
    empty_no_creep = sum(coverage[r]["official_empty_no_creep"] for r in ROOMS)
    official_404_missing = sum(coverage[r]["official_404_missing"] for r in ROOMS)
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
        "official_404_missing": official_404_missing,
        "official_recovered": official_with_creeps + empty_no_creep,
        "expected": expected,
        "in_window_official_404": sorted(f"{r}@{b}" for r, b in IN_WINDOW_404),
        "in_window_official_404_n_bases": len(IN_WINDOW_404),
        "live_filled_404": live_filled_404,
        "db_tips": tips,
        "live_after": live_after,
        "at": datetime.now(ZoneInfo("Asia/Hong_Kong")).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"),
    }
    with open(OUT, "w") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
    print(f"window {TMIN}..{TMAX} ({TMAX-TMIN+1})")
    for room in ROOMS:
        c = coverage[room]
        print(
            f"{room} distinct={c['distinct']} rows={c['rows']} range={c['range']} "
            f"missing_n={c['missing_n']} {c['missing_ranges']} "
            f"empty_no_creep={c['official_empty_no_creep']} {c['official_empty_no_creep_ranges']} "
            f"official_404={c['official_404_missing']} {c['official_404_missing_ranges']}"
        )
    print("unique_after", payload["unique_after"])
    print(
        f"official_with_creeps={official_with_creeps} empty_no_creep={empty_no_creep} "
        f"official_404_missing={official_404_missing} official_recovered={payload['official_recovered']} "
        f"expected={expected} in_window_404={payload['in_window_official_404']}"
    )
    print("live_filled_404", live_filled_404)
    print("db_tips", tips)
    print("live_after", live_after)
    print("wrote", OUT)

if __name__ == "__main__":
    main()
