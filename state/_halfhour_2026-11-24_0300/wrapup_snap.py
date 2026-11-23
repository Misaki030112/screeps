#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

sys.path.insert(0, "/workspace/screeps/tools")
import db

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-24_0300"
HK = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84446001, 84446700
JP_BASE = 84446700
HOLES = [("W47N7", 84446600), ("W46N8", 84445500), ("W45N7", 84444900), ("W47N8", 84445100), ("W46N8", 84444500), ("W46N8", 84444200), ("W47N8", 84443800), ("W47N7", 84443300), ("W45N7", 84441900), ("W47N7", 84440900), ("W45N8", 84439200), ("W45N8", 84439300), ("W45N8", 84439500), ("W47N7", 84438700), ("W45N8", 84437100), ("W47N7", 84436400)]
FREEZES = {
    "freeze_1450_1502": (84436431, 84436619),
    "freeze_1521_1531": (84436871, 84437029),
    "freeze_1549_1556": (84437281, 84437379),
    "freeze_1614_1629": (84437621, 84437849),
    "freeze_1652_1706": (84438151, 84438369),
    "freeze_1723_1727": (84438601, 84438669),
    "freeze_1816_1835": (84439341, 84439619),  # already told in 20:44 2028 patrol; 盒子休眠 18:16:12-18:35:22; STATS 279t
    "freeze_1852_1858": (84439851, 84439959),  # already told in 20:44 2028 patrol; 盒子休眠 18:52:46-18:58:58; STATS 109t
    "freeze_1921_1934": (84440261, 84440459),  # already told in 20:44 2028 patrol; 盒子休眠 19:21:55-19:34:51; STATS 199t
    "shortws_2001": (84440811, 84440839),  # already told in 20:44 2028 patrol; 监听短中断 20:01:56; STATS 29t
    "freeze_2014_2028": (84441001, 84441209),  # already told in 20:44 2028 patrol; 盒子休眠 20:14:37-20:28:31; STATS 209t; official-filled all five 209/209
    "freeze_2056_2101": (84441591, 84441679),  # already told in 23:33 2321 patrol; 盒子休眠 20:56:44-21:01:46; STATS 89t; official-filled all five 89/89; do not relabel NEW
    "freeze_2121_2128": (84441901, 84442049),  # already told in 23:33 2321 patrol; 盒子休眠 21:21:51-21:28:39; STATS 149t; official-filled W46N8/W47N8/W45N8/W47N7 149/149, W45N7 49/149 due to leftover official 404 W45N7@84441900; do not relabel NEW
    "freeze_2143_2201": (84442251, 84442509),  # already told in 23:33 2321 patrol; 盒子休眠 21:43:28-22:01:34; STATS 259t; official-filled all five 259/259 after 2200 first pass plus JP 84442500; do not relabel NEW
    "freeze_2223_2235": (84442741, 84442989),  # already told in 23:33 2321 patrol; 盒子休眠 22:23:02-22:35:40; STATS 249t; official-filled all five 249/249 after 2230 first pass, which included published 84442700..84442900; do not relabel NEW
    "freeze_2259_2305": (84443221, 84443419),  # already told in 23:33 2321 patrol; 盒子休眠 22:59:15-23:05:47; STATS 199t; official-filled W46N8/W47N8/W45N8/W45N7 199/199 after 2300 first pass plus JP 84443400; W47N7 99/199 missing 84443301..84443400 due to leftover official 404 W47N7@84443300; do not relabel NEW
    "shortws_0034": (84444571, 84444659),  # NOT YET TOLD from quiet 0030; errors.log 00:34:41 no STATS for 328s (since ~00:29:13); no box_pauses row and no "box frozen" line; listener auto-restarted 00:34:41, python 3364202 started 00:34:51; STATS gap 89t 84444571..84444659; official-filled W47N8/W45N8/W45N7/W47N7 89/89, W46N8 59/89 missing 84444571..84444600 due to leftover official 404 W46N8@84444500; do not relabel NEW
    "shortws_0102": (84444961, 84445069),  # NOT YET TOLD from quiet 0100; errors.log 01:02:38 no STATS for 348s (since ~00:56:50) then 01:04:10 ws ping/pong timed out; no box_pauses row and no "box frozen" line; listener auto-restarted 01:02:38 and 01:04:14, python 3379693 started 01:04:24, parent 4035476; STATS gap 109t 84444961..84445069; official-filled W46N8/W47N8/W45N8/W47N7 109/109; W45N7 69/109 missing 84444961..84445000 due to leftover official 404 W45N7@84444900; do not relabel NEW
    "freeze_0203_0221": (84445891, 84446159),  # NOT YET TOLD from quiet 0230; 盒子休眠 02:03:03-02:21:36 (1108s, STATS 269t); box_pauses row present; errors.log box frozen line; listener auto-restarted 02:21:39, python 3411463 started 02:21:48, parent 4035476; official-filled all five 269/269 already at 0230 pre_run; do not relabel NEW
    "shortws_0257": (84446631, 84446659),  # NEW this 0300 pass; 监听短中断 02:57:18 (errors.log ws error ping/pong timed out; no box_pauses row and no box-frozen line); listener auto-restarted 02:57:21, python 3431965 started 02:57:31, parent 4035476; STATS gap 29t 84446631..84446659; NOT YET TOLD
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
