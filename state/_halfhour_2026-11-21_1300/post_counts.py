#!/usr/bin/env python3
"""Snapshot just-published post counts, freeze-gap fill, and listener tips."""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-21_1300")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
JUST_BASE = 84393900
T0, T1 = JUST_BASE + 1, JUST_BASE + 100
WIN_TMIN, WIN_TMAX = 84393201, 84393900
GAPS = [
    ("gap_1248_1257", 84393831, 84393969),  # NEW this run, not yet told (box freeze 12:48:14-12:57:17, 534s); 139t; last_stats 84393830 at 12:48:02, next 84393970 at 12:57:57; listener auto-restart 12:57:20, python 1876378 started 12:57:29; official window start 84393201 covers 84393831..84393900 (chunk 84393800); tail 84393901..84393969 needs just-published 84393900.
    ("gap_1230_1235", 84393581, 84393659),  # not yet told (recorded by 12:30 half-hour backfill; box freeze 12:30:42-12:35:35, 283s); 79t; official-filled all five 79/79 at 12:30 run; still in official window start 84393201. Fold into next 1h patrol together with 12:48 freeze; do not treat as already told.
    ("gap_1218", 84393391, 84393419),  # already-told by the 12:26 1h patrol (short listener WS ping/pong 12:18:13, restart 12:18:17; not a box freeze); 29t; official 84393400 confirm-filled; W45N7 may have empty-no-creep after evac; still in official window start 84393201
    ("gap_1210", 84393291, 84393319),  # already-told by the 12:26 1h patrol (short listener WS ping/pong 12:10:56, restart 12:10:59; not a box freeze); 29t; official-filled all five 29/29; still in official window start 84393201
    ("gap_1149_1157", 84393001, 84393129),  # already-told by the 12:26 1h patrol (box freeze 11:49:12-11:57:31, 494s); 129t; official-filled all five 129/129; ages out of window start 84393201
    ("gap_1119_1120", 84392571, 84392609),  # already-told by the 11:28 1h patrol (box freeze 11:19:06-11:20:43, 88s); leftover official 404 W45N8@84392600 already told by 12:26 patrol; ages out of window start 84393201
    ("gap_1111_1113", 84392471, 84392499),  # already-told by the 12:26 1h patrol (short listener WS ping/pong 11:12:51-11:12:54, not a box freeze); official-filled all five 29/29; ages out of window start 84393201
]
HK = ZoneInfo("Asia/Hong_Kong")

jp_path = DIR / f"just_published_{JUST_BASE}.json"
pre_path = DIR / "just_published_pre_counts.json"
if jp_path.exists():
    jp = json.loads(jp_path.read_text())
    script_by = {g["room"]: int(g.get("inserted") or 0) for g in (jp.get("gets") or [])}
    skipped = False
else:
    jp = {"skipped": True, "base": JUST_BASE, "gets": []}
    script_by = {r: 0 for r in ROOMS}
    skipped = True

if pre_path.exists():
    pre = json.loads(pre_path.read_text())
else:
    pre = {r: {"distinct": 0, "rows": 0, "min": None, "max": None} for r in ROOMS}

with db.connect() as c:
    post = {}
    actual = {}
    for room in ROOMS:
        d, mn, mx, n = c.execute(
            "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, T0, T1),
        ).fetchone()
        post[room] = {"distinct": int(d or 0), "rows": int(n or 0), "min": mn, "max": mx}
        actual[room] = int(n or 0) - int((pre.get(room) or {}).get("rows") or 0)
    (DIR / "just_published_post_counts.json").write_text(json.dumps(post, indent=2) + "\n")

    gaps = {}
    for label, a, b in GAPS:
        gaps[label] = {}
        span = b - a + 1
        for room in ROOMS:
            d, mn, mx, n = c.execute(
                "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
                (room, a, b),
            ).fetchone()
            miss = c.execute(
                "select array_agg(t order by t) from (select generate_series(%s,%s) t except select distinct tick from creep_ticks where room=%s and tick between %s and %s) x",
                (a, b, room, a, b),
            ).fetchone()[0] or []
            gaps[label][room] = {
                "fill": f"{int(d or 0)}/{span}",
                "distinct": int(d or 0),
                "rows": int(n or 0),
                "min": mn,
                "max": mx,
                "missing_n": len(miss),
                "missing_range": f"{miss[0]}..{miss[-1]}" if miss else None,
            }

    holes = {}
    for room, base in [("W46N8", 84390400), ("W45N7", 84388500), ("W47N8", 84385300), ("W45N7", 84383500), ("W45N7", 84383900), ("W45N7", 84382700), ("W46N8", 84382900), ("W45N8", 84382600), ("W45N8", 84386600), ("W46N8", 84386400), ("W47N8", 84385900)]:
        t0, t1 = base + 1, base + 100
        d, mn, mx, n = c.execute(
            "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, t0, t1),
        ).fetchone()
        holes[f"{room}@{base}"] = {"distinct": int(d or 0), "rows": int(n or 0), "min": mn, "max": mx}

    tips = {}
    for table in ("room_stats", "creep_cpu", "path_arrivals"):
        tips[table] = c.execute(f"select max(tick) from {table}").fetchone()[0]
    live_by_room = {}
    tip = tips["room_stats"]
    for room in ROOMS:
        d, mn, mx, n = c.execute(
            "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick>=%s",
            (room, tip - 40),
        ).fetchone()
        live_by_room[room] = {"distinct": int(d or 0), "rows": int(n or 0), "min": mn, "max": mx}

    win = {}
    for room in ROOMS:
        d, mn, mx, n = c.execute(
            "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, WIN_TMIN, WIN_TMAX),
        ).fetchone()
        win[room] = {"distinct": int(d or 0), "rows": int(n or 0), "min": mn, "max": mx}

print("skipped_just_published", skipped)
print("post", json.dumps(post, indent=2))
print("actual_by_room", actual, "sum", sum(actual.values()))
print("script_by", script_by, "sum", sum(script_by.values()))
for label, a, b in GAPS:
    print(f"gap {label} {a}..{b}")
    for room, g in gaps[label].items():
        print(f"  {room} {g['fill']} rows={g['rows']} range={g['min']}..{g['max']} missing_n={g['missing_n']} missing_range={g['missing_range']}")
print("holes", holes)
print("tips", tips)
print("live near tip", live_by_room)
print("first_pass_window", win)

payload = {
    "at": datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"),
    "just_published_skipped": skipped,
    "post": post,
    "pre": pre,
    "actual_by_room": actual,
    "actual_sum": sum(actual.values()),
    "script_by_room": script_by,
    "script_sum": sum(script_by.values()),
    "gaps": gaps,
    "holes": holes,
    "tips": tips,
    "live_by_room": live_by_room,
    "first_pass_window": win,
}
(DIR / "just_published_post_summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
print("wrote post_counts and summary")
