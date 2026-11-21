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

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-21_1030")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
JUST_BASE = 84391900
T0, T1 = JUST_BASE + 1, JUST_BASE + 100
WIN_TMIN, WIN_TMAX = 84391201, 84391900
GAPS = [
    ("gap_1017_1024", 84391711, 84391819),  # already-told by the 10:31 1h patrol (box freeze 10:17:34-10:24:42, 423s); 109t; last_stats 84391710 at 10:17:17, next 84391820 at 10:25:05; listener auto-restart 10:24:45, python 1808991 started 10:24:54; official first-pass this run includes published 84391711..84391800 plus 84391801..84391819 from chunk 84391800 (10:31 patrol had official-filled published 90/90 all five, unpublished tail 84391801..84391819 expected).
    ("gap_0958_1005", 84391431, 84391549),  # already-told by the 10:31 1h patrol (box freeze 09:58:02-10:05:00, 412s); 119t; last_stats 84391430 at 09:57:18, next 84391550 at 10:05:42; listener auto-restart 10:05:03, python 1801941 started 10:05:13; official-fill missing W45N7 84391431..84391537 (90) empty-no-creep during evac, not a 404; still in official window start 84391201.
    ("gap_0915_0923", 84390831, 84390959),  # already-told by the 09:42 1h patrol (box freeze 09:15:27-09:23:48, 492s); 129t; official-fill missing W46N8 70 ticks (W46N8@84390800) and W47N7 59 ticks (W47N7@84390900); ages out of window start 84391201
    ("gap_0852_0856", 84390511, 84390579),  # already-told by the 09:42 1h patrol (box freeze 08:52:35-08:56:43, 248s); 69t; official-filled all five 69/69; ages out of window start 84391201
    ("gap_0818_0823", 84390031, 84390119),  # already-told by the 08:32 1h patrol (box freeze 08:18:49-08:23:57, 299s); 89t; official-filled all five 89/89; ages out of window start 84391201
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
