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

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-21_1600")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
JUST_BASE = 84396500
T0, T1 = JUST_BASE + 1, JUST_BASE + 100
WIN_TMIN, WIN_TMAX = 84395801, 84396500
GAPS = [
    ("gap_1547_1558", 84396331, 84396509),  # NEW not-yet-told box freeze 15:47:29-15:58:30 (655s); 179t; official first-pass filled published part 84396331..84396500 four rooms 170/170, W45N7 164/170 evac empty tail 84396331..84396336 (part of 84395930..84396336 official 200 not a 404); tail 84396501..84396509 awaits just-published 84396500; listener auto-restart 15:58:33, python 1948186 started 15:58:42. In official window start 84395801.
    ("gap_1514_1519", 84395871, 84395959),  # already told by the delivered 15:28 1h patrol (box freeze 15:14:38-15:19:30, 292s); 89t; official-filled W46N8/W47N8/W45N8/W47N7 89/89, W45N7 59/89 evac empty tail official 200 not a 404; listener auto-restart 15:19:33, python 1932081 started 15:19:43. Still in official window start 84395801.
    ("gap_1440_1456", 84395401, 84395639),  # already told by the delivered 15:28 1h patrol (box freeze 14:40:53-14:56:54, 952s); 239t; official-filled four rooms 239/239, W47N7 200/239 missing 84395601..84395639 because of leftover official 404 W47N7@84395600 (also already told). Ages out of official window start 84395801.
    ("gap_1415_1423", 84395061, 84395179),  # already told (box freeze 14:15:50-14:23:29, 450s); 119t; official-filled four rooms 119/119, W47N8 40/119 missing 84395101..84395179 because of leftover official 404 W47N8@84395100 (also already told). Ages out of official window start 84395801.
    ("gap_1349_1356", 84394681, 84394809),  # already told (box freeze 13:49:01-13:56:56, 475s); 129t; official-filled all five 129/129; ages out of official window start 84395801.
    ("gap_1309_1321", 84394131, 84394299),  # already told (box freeze 13:09:46-13:21:14, 680s); ages out of official window start 84395801.
    ("gap_1248_1257", 84393831, 84393969),  # already told (box freeze 12:48:14-12:57:17, 534s); ages out of official window start 84395801.
    ("gap_1230_1235", 84393581, 84393659),  # already told (box freeze 12:30:42-12:35:35, 283s); ages out of official window start 84395801.
    ("gap_1218", 84393391, 84393419),  # already told short WS gap 12:18; ages out
    ("gap_1210", 84393291, 84393319),  # already told short WS gap 12:10; ages out
    ("gap_1149_1157", 84393001, 84393129),  # already told (box freeze 11:49:12-11:57:31, 494s); ages out
    ("gap_1119_1120", 84392571, 84392609),  # already told (box freeze 11:19:06-11:20:43); leftover official 404 W45N8@84392600 already told; ages out
    ("gap_1111_1113", 84392471, 84392499),  # already told short WS gap 11:12; ages out
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
    for room, base in [("W47N7", 84395600), ("W47N8", 84395100), ("W46N8", 84394300), ("W45N8", 84392600), ("W46N8", 84390800), ("W47N7", 84390900), ("W46N8", 84390400), ("W45N7", 84388500), ("W45N8", 84386600), ("W47N8", 84385300), ("W45N7", 84383500), ("W45N7", 84383900), ("W45N7", 84382700), ("W46N8", 84382900), ("W45N8", 84382600), ("W46N8", 84386400), ("W47N8", 84385900)]:
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
