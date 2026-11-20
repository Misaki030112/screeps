#!/usr/bin/env python3
import json, sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import db

ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
T0, T1 = 84372201, 84372300
DIR = Path("/workspace/screeps/state/_halfhour_2026-11-20_1130")
pre = json.loads((DIR / "just_published_pre_counts.json").read_text())
pr = pre["rooms"] if "rooms" in pre else pre
out = {
    "at": datetime.now(ZoneInfo("Asia/Hong_Kong")).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"),
    "t0": T0,
    "t1": T1,
    "rooms": {},
    "deltas": {},
}
with db.connect() as c:
    total_delta = 0
    print("just-published 84372200 ticks 84372201..84372300:")
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
    print(f"actual db inserted={total_delta} script=2570")

    print("NEW STATS gap 84372251..84372269 (19):")
    gap = {}
    for room in ROOMS:
        r = c.execute(
            "SELECT count(*), count(DISTINCT tick), min(tick), max(tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, 84372251, 84372269),
        ).fetchone()
        miss_n = 19 - (r[1] or 0)
        gap[room] = {"rows": r[0], "distinct": r[1], "min": r[2], "max": r[3], "missing": miss_n}
        print(f"  {room} rows={r[0]} distinct={r[1]} range={r[2]}..{r[3]} missing={miss_n}")
    out["gap_84372251_84372269"] = gap

    for label, a, b, span in [
        ("11:11 84371891..84371919", 84371891, 84371919, 29),
        ("11:18 84371991..84372019", 84371991, 84372019, 29),
        ("10:49 84371591..84371729", 84371591, 84371729, 139),
    ]:
        print(f"{label}:")
        for room in ROOMS:
            r = c.execute(
                "SELECT count(DISTINCT tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
                (room, a, b),
            ).fetchone()
            print(f"  {room} {r[0]}/{span}")

    r = c.execute(
        "SELECT count(DISTINCT tick), count(*) FROM creep_ticks WHERE room='W46N8' AND tick BETWEEN 84371601 AND 84371700"
    ).fetchone()
    print("W46N8@84371600 hole still", r)

    rot = json.loads(Path("/workspace/screeps/metrics/listener_rot.json").read_text())
    live = json.loads(Path("/workspace/screeps/metrics/live.json").read_text())
    print("rot", rot)
    print("live slot", live.get("roomSlot"), "stats.t", (live.get("stats") or {}).get("t"), "updated", live.get("updated"))
    print("cpu tip", c.execute("SELECT max(tick) FROM creep_cpu").fetchone()[0])
    print("path tip", c.execute("SELECT max(tick) FROM path_arrivals").fetchone()[0])
    print("stats tip", c.execute("SELECT max(tick) FROM room_stats").fetchone()[0])

(DIR / "just_published_post_counts.json").write_text(json.dumps(out, indent=2) + chr(10))
print("wrote post counts")
