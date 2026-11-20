#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db

ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
T0, T1 = 84372601, 84372700
DIR = Path("/workspace/screeps/state/_halfhour_2026-11-20_1200")
pre = json.loads((DIR / "just_published_pre_counts.json").read_text())
pr = pre["rooms"] if "rooms" in pre else pre
just = json.loads((DIR / "just_published_84372600.json").read_text())
script_inserted = just.get("inserted")
out = {
    "at": datetime.now(ZoneInfo("Asia/Hong_Kong")).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"),
    "t0": T0,
    "t1": T1,
    "rooms": {},
    "deltas": {},
    "script_inserted": script_inserted,
}
with db.connect() as c:
    total_delta = 0
    print("just-published 84372600 ticks 84372601..84372700:")
    for room in ROOMS:
        r = c.execute(
            "SELECT count(*), count(DISTINCT tick), min(tick), max(tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, T0, T1),
        ).fetchone()
        out["rooms"][room] = {"rows": r[0], "distinct": r[1], "min": r[2], "max": r[3]}
        prow = pr[room]["rows"]
        delta = r[0] - prow
        out["deltas"][room] = delta
        total_delta += delta
        print(f"  {room} rows={r[0]} (pre {prow}, delta {delta}) distinct={r[1]} range={r[2]}..{r[3]}")
    out["actual_inserted"] = total_delta
    print(f"actual db inserted={total_delta} script={script_inserted}")

    gaps = [
        ("NEW freeze 11:48 84372431..84372599", 84372431, 84372599, 169),
        ("NEW short 12:01 84372611..84372639", 84372611, 84372639, 29),
        ("prior 11:36 84372251..84372269", 84372251, 84372269, 19),
        ("prior 11:18 84371991..84372019", 84371991, 84372019, 29),
        ("prior 11:11 overlap 84371901..84371919 (full 84371891..84371919 aged-in part)", 84371901, 84371919, 19),
    ]
    out["gaps"] = {}
    for label, a, b, span in gaps:
        print(f"{label}:")
        gap = {}
        for room in ROOMS:
            r = c.execute(
                "SELECT count(*), count(DISTINCT tick), min(tick), max(tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
                (room, a, b),
            ).fetchone()
            miss_n = span - (r[1] or 0)
            gap[room] = {"rows": r[0], "distinct": r[1], "min": r[2], "max": r[3], "missing": miss_n}
            print(f"  {room} rows={r[0]} distinct={r[1]}/{span} range={r[2]}..{r[3]} missing={miss_n}")
        out["gaps"][f"{a}_{b}"] = gap

    rot = json.loads(Path("/workspace/screeps/metrics/listener_rot.json").read_text())
    live = json.loads(Path("/workspace/screeps/metrics/live.json").read_text())
    print("rot", rot)
    print("live slot", live.get("roomSlot"), "stats.t", (live.get("stats") or {}).get("t"), "updated", live.get("updated"))
    print("cpu tip", c.execute("SELECT max(tick) FROM creep_cpu").fetchone()[0])
    print("path tip", c.execute("SELECT max(tick) FROM path_arrivals").fetchone()[0])
    print("stats tip", c.execute("SELECT max(tick) FROM room_stats").fetchone()[0])

(DIR / "just_published_post_counts.json").write_text(json.dumps(out, indent=2) + chr(10))
print("wrote post counts")
