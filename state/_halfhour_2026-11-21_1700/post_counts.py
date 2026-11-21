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

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-21_1700")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
JUST_BASE = 84397400
T0, T1 = JUST_BASE + 1, JUST_BASE + 100
WIN_TMIN, WIN_TMAX = 84396701, 84397400
GAPS = [
    ("gap_1648_1704", 84397201, 84397439),  # NEW box freeze 16:48:46-17:04:41 (954s, box_pauses.jsonl); STATS 239t last 84397200 at 16:48:12 next 84397440 at 17:05:10; listener auto-restart 17:04:44, python 1974391 started 17:04:54. Official first-pass fills 84397201..84397400; tail 84397401..84397439 needs just-published 84397400. Not yet told; fold into next 1h patrol.
    ("gap_1616_1619", 84396751, 84396799),  # already told by the delivered 16:32 1h patrol (box freeze 16:16:43-16:19:24, 161s); 49t; official-filled all five 49/49; listener auto-restart 16:19:27. Still in official window start 84396701.
    ("gap_1622", 84396821, 84396839),  # already told by the delivered 16:32 1h patrol (short WS ping/pong 16:22:02, not a box freeze); 19t; official late-retry filled all five 19/19; listener restart 16:22:05. Still in official window start 84396701.
    ("gap_1547_1558", 84396331, 84396509),  # already told by the delivered 16:32 1h patrol (box freeze 15:47:29-15:58:30, 655s); ages out of official window start 84396701.
    ("gap_1514_1519", 84395871, 84395959),  # already told by the delivered 16:32/15:28 1h patrols (box freeze 15:14:38-15:19:30, 292s); ages out of official window start 84396701.
    ("gap_1440_1456", 84395401, 84395639),  # already told (box freeze 14:40:53-14:56:54, 952s); leftover official 404 W47N7@84395600 already told; ages out of official window start 84396701.
    ("gap_1415_1423", 84395061, 84395179),  # already told (box freeze 14:15:50-14:23:29, 450s); leftover official 404 W47N8@84395100 already told; ages out of official window start 84396701.
    ("gap_1349_1356", 84394681, 84394809),  # already told (box freeze 13:49:01-13:56:56, 475s); ages out
    ("gap_1309_1321", 84394131, 84394299),  # already told (box freeze 13:09:46-13:21:14, 680s); ages out
    ("gap_1248_1257", 84393831, 84393969),  # already told (box freeze 12:48:14-12:57:17, 534s); ages out
    ("gap_1230_1235", 84393581, 84393659),  # already told (box freeze 12:30:42-12:35:35, 283s); ages out
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
