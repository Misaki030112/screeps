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

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-21_0230")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
JUST_BASE = 84385100
T0, T1 = JUST_BASE + 1, JUST_BASE + 100
WIN_TMIN, WIN_TMAX = 84384401, 84385100
GAPS = [
    ("gap_0147_0202", 84384461, 84384689),  # already-told by 02:28/02:30 1h patrol _patrol_2026-11-21_0221 (box freeze 01:47:58-02:02:50, 884s); 229t; fully in window start 84384401
    ("gap_0220_0222", 84384941, 84384959),  # already-told by 02:28/02:30 1h patrol (short listener gap 02:20:54-02:22:17, ~83s); 19t; official-filled 19/19 via patrol just-published 84384900
    ("gap_0110_0124", 84383931, 84384149),  # already-told by 01:33 patrol (box freeze 01:10:46-01:24:59); ages out of window start 84384401; 219t
    ("gap_0050_0057", 84383651, 84383759),  # already-told by 01:33 patrol (box freeze 00:50:52-00:57:30); ages out of window start 84384401; 109t
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
    for room, base in [("W45N7", 84383500), ("W45N7", 84383900), ("W45N7", 84382700), ("W46N8", 84382900), ("W45N8", 84382600)]:
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
