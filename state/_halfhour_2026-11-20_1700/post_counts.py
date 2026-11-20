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

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-20_1700")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
JUST_BASE = 84376800
T0, T1 = JUST_BASE + 1, JUST_BASE + 100
GAP0, GAP1 = 84376701, 84376869
HK = ZoneInfo("Asia/Hong_Kong")

pre = json.loads((DIR / "just_published_pre_counts.json").read_text())
out = {}
with db.connect() as c:
    post = {}
    actual = {}
    script_by = {"W46N8": 965, "W47N8": 1069, "W45N8": 518, "W45N7": 0, "W47N7": 501}
    for room in ROOMS:
        d, mn, mx, n = c.execute(
            "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, T0, T1),
        ).fetchone()
        post[room] = {"distinct": int(d or 0), "rows": int(n or 0), "min": mn, "max": mx}
        actual[room] = int(n or 0) - int((pre.get(room) or {}).get("rows") or 0)
    (DIR / "just_published_post_counts.json").write_text(json.dumps(post, indent=2) + "\n")

    gap = {}
    for room in ROOMS:
        d, mn, mx, n = c.execute(
            "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, GAP0, GAP1),
        ).fetchone()
        miss = c.execute(
            "select array_agg(t order by t) from (select generate_series(%s,%s) t except select distinct tick from creep_ticks where room=%s and tick between %s and %s) x",
            (GAP0, GAP1, room, GAP0, GAP1),
        ).fetchone()[0] or []
        gap[room] = {"distinct": int(d or 0), "rows": int(n or 0), "min": mn, "max": mx, "missing_n": len(miss), "missing": miss}

    # prior already-told freeze fill still in/near window
    prior = {}
    for label, a, b in [
        ("freeze_1544", 84375811, 84376109),
        ("freeze_1617", 84376291, 84376369),
    ]:
        prior[label] = {}
        for room in ROOMS:
            d, n = c.execute(
                "SELECT count(DISTINCT tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
                (room, a, b),
            ).fetchone()
            prior[label][room] = f"{int(d or 0)}/{b-a+1}"

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

print("post", json.dumps(post, indent=2))
print("actual_by_room", actual, "sum", sum(actual.values()))
print("script_by", script_by, "sum", sum(script_by.values()))
print("gap 84376701..84376869")
for room, g in gap.items():
    print(f"  {room} distinct={g['distinct']}/169 rows={g['rows']} range={g['min']}..{g['max']} missing_n={g['missing_n']}")
    if g["missing"] and len(g["missing"]) <= 80:
        print("    missing", g["missing"][:5], "...", g["missing"][-5:] if len(g["missing"])>5 else "")
    elif g["missing"]:
        print("    missing first/last", g["missing"][0], g["missing"][-1], "n", len(g["missing"]))
print("prior fills", prior)
print("tips", tips)
print("live near tip", live_by_room)

payload = {
    "at": datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"),
    "post": post,
    "pre": pre,
    "actual_by_room": actual,
    "actual_sum": sum(actual.values()),
    "script_by_room": script_by,
    "script_sum": sum(script_by.values()),
    "gap": {r: {k: v for k, v in g.items() if k != "missing"} | {"missing_range": f"{g['missing'][0]}..{g['missing'][-1]}" if g["missing"] else None} for r, g in gap.items()},
    "prior": prior,
    "tips": tips,
    "live_by_room": live_by_room,
}
(DIR / "just_published_post_summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
print("wrote post_counts and summary")
