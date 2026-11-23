#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

sys.path.insert(0, "/workspace/screeps/tools")
import db

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-23_1800"
HK = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84438401, 84439100
JP_BASE = 84439100
HOLES = [("W47N7", 84438700), ("W45N8", 84437100), ("W47N7", 84436400)]
FREEZES = {
    "freeze_1450_1502": (84436431, 84436619),
    "freeze_1521_1531": (84436871, 84437029),
    "freeze_1549_1556": (84437281, 84437379),
    "freeze_1614_1629": (84437621, 84437849),
    "freeze_1652_1706": (84438151, 84438369),
    "freeze_1723_1727": (84438601, 84438669),
}


def rng(c, room, a, b):
    d, mn, mx, n = c.execute(
        "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) "
        "FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
        (room, a, b),
    ).fetchone()
    return {"distinct": int(d or 0), "rows": int(n or 0), "min": mn, "max": mx}


def main():
    snap = {"at": datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")}
    with db.connect() as c:
        for table in ("creep_cpu", "path_arrivals", "room_stats"):
            row = c.execute(f"SELECT min(tick), max(tick), count(*) FROM {table}").fetchone()
            snap[table] = {"min": row[0], "max": row[1], "n": row[2]}
        window_db = {}
        for room in ROOMS:
            window_db[room] = rng(c, room, TMIN, TMAX)
            window_db[room]["span"] = TMAX - TMIN + 1
        snap["window_db"] = window_db
        jp_post = {}
        for room in ROOMS:
            jp_post[room] = rng(c, room, JP_BASE + 1, JP_BASE + 100)
        snap["jp_post"] = jp_post
        holes = {}
        for room, base in HOLES:
            h = rng(c, room, base + 1, base + 100)
            h["hole_ticks"] = 100 - h["distinct"]
            holes[f"{room}@{base}"] = h
        snap["holes"] = holes
        freeze_fill = {}
        for label, (a, b) in FREEZES.items():
            span = b - a + 1
            rooms = {}
            for room in ROOMS:
                r = rng(c, room, a, b)
                r["fill"] = r["distinct"]
                r["span"] = span
                rooms[room] = r
            freeze_fill[label] = {"span": span, "rooms": rooms}
        snap["freeze_fill"] = freeze_fill
        stats_gaps = {}
        for label, (a, b) in FREEZES.items():
            r = c.execute(
                "SELECT min(tick), max(tick), count(DISTINCT tick) "
                "FROM room_stats WHERE tick BETWEEN %s AND %s",
                (a, b),
            ).fetchone()
            stats_gaps[label] = {
                "min": r[0], "max": r[1],
                "distinct": int(r[2] or 0), "span": b - a + 1,
            }
        snap["stats_gaps"] = stats_gaps

    out = subprocess.check_output(
        ["ps", "-o", "pid,ppid,lstart,etime,stat,cmd", "-C", "python"], text=True
    )
    listeners = [ln.strip() for ln in out.splitlines() if "tools/listener.py" in ln]
    snap["listener"] = listeners
    snap["listener_rot"] = json.loads((ROOT / "metrics/listener_rot.json").read_text())
    snap["yield_absent"] = not (ROOT / "metrics/listener_yield_rooms").exists()
    live = json.loads((ROOT / "metrics/live.json").read_text())
    st = live.get("stats") if isinstance(live.get("stats"), dict) else {}
    snap["live"] = {
        "updated": live.get("updated"),
        "t": st.get("t"),
        "gameTime": live.get("gameTime"),
        "roomSlot": live.get("roomSlot"),
    }

    pauses = []
    with open(ROOT / "metrics/box_pauses.jsonl") as f:
        for line in f:
            line = line.strip()
            if line:
                pauses.append(json.loads(line))
    snap["box_pauses_last"] = pauses[-5:]

    outp = (ROOT / "metrics/listener.out").read_text().splitlines()
    today = [ln for ln in outp if ln.startswith("2026-11-23") and "restart" in ln]
    snap["listener_restarts_last"] = today[-6:]
    errp = ROOT / "metrics/errors.log"
    if errp.exists():
        rec = [ln for ln in errp.read_text().splitlines() if ln.startswith("2026-11-23 ")]
        snap["errors_last"] = rec[-8:]

    (DIR / "wrapup_snap.json").write_text(json.dumps(snap, indent=2, default=str) + "\n")
    print(json.dumps(snap, indent=2, default=str))


if __name__ == "__main__":
    main()
