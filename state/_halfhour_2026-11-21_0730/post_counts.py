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

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-21_0730")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
JUST_BASE = 84389300
T0, T1 = JUST_BASE + 1, JUST_BASE + 100
WIN_TMIN, WIN_TMAX = 84388601, 84389300
GAPS = [
    ("gap_0722_0725", 84389231, 84389299),  # NEW this run, not yet told by a 1h patrol (box freeze 07:22:15-07:25:56, 214s); 69t; last_stats 84389230 at 07:21:52, next 84389300 at 07:26:45; listener auto-restart 07:25:59, python 1733733 started 07:26:09; sits in official window start 84388601..end (chunk 84389200)
    ("gap_0642_0704", 84388671, 84388999),  # first seen by 07:00/07:18 half-hour, not yet told by a 1h patrol (box freeze 06:42:51-07:04:46, 1315s); 329t; last_stats 84388670 at 06:42:15, next 84389000 at 07:05:30; listener auto-restart 07:04:49; still in official window start 84388601 (chunks 84388600..84388900)
    ("gap_0634_0637", 84388561, 84388599),  # first seen by 07:00/07:18 half-hour, not yet told (ping/pong timeout 06:36:25, listener restart 06:36:28); 39t; official-fill missing W45N7 all 39 due to leftover official 404 W45N7@84388500; ages out of window start 84388601
    ("gap_0619_0622", 84388331, 84388399),  # already-told by the 06:33 1h patrol (box freeze 06:19:18-06:22:57, 218s); 69t; official-filled all five 69/69; ages out of window start 84388601
    ("gap_0542_0601", 84387811, 84388109),  # already-told by the 06:33 1h patrol (box freeze 05:42:11-06:01:46, 1169s); 299t; official-filled all five 299/299; ages out of window start 84388601
    ("gap_0442_0503", 84386961, 84387269),  # already-told by the 05:26 1h patrol (box freeze 04:42:19-05:03:11, 1245s); 309t; official-filled all five 309/309; ages out of window start 84388601
    ("gap_0410_0418", 84386511, 84386629),  # already-told by the 04:18/04:29 1h patrol (box freeze 04:10:40-04:18:06, 439s); 119t; official-fill missing W45N8 84386601..84386629; ages out of window start 84388601
    ("gap_0354_0357", 84386281, 84386339),  # already-told by the 04:18/04:29 1h patrol (short freeze 03:54:27-03:57:32, 178s); 59t; official-filled all five 59/59; ages out of window start 84388601
    ("gap_0245_0305", 84385301, 84385599),  # already-told by 03:17 backfill / 03:30 1h patrol (box freeze 02:45:59-03:05:48, ~1189s); 299t; official 404 W47N8@84385300 leaves W47N8 missing 84385301..84385400; ages out of window start 84388601
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
    for room, base in [("W47N8", 84385300), ("W45N7", 84383500), ("W45N7", 84383900), ("W45N7", 84382700), ("W46N8", 84382900), ("W45N8", 84382600), ("W45N8", 84386600), ("W46N8", 84386400), ("W47N8", 84385900)]:
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
