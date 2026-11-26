#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

sys.path.insert(0, "/workspace/screeps/tools")
import db

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-24_1230"
HK = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84454001, 84454700
JP_BASE = 84454700
HOLES = [("W46N8", 84454300), ("W47N7", 84454200), ("W46N8", 84454100), ("W47N7", 84452600), ("W47N7", 84451700), ("W46N8", 84450800), ("W46N8", 84450500), ("W46N8", 84448500), ("W45N8", 84448600), ("W47N8", 84448400), ("W47N8", 84447700), ("W45N8", 84447400), ("W47N7", 84446600), ("W46N8", 84445500), ("W45N7", 84444900), ("W47N8", 84445100), ("W46N8", 84444500), ("W46N8", 84444200), ("W47N8", 84443800), ("W47N7", 84443300), ("W45N7", 84441900), ("W47N7", 84440900), ("W45N8", 84439200), ("W45N8", 84439300), ("W45N8", 84439500), ("W47N7", 84438700)]
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
    "shortws_0034": (84444571, 84444659),  # already told in 02:34 0221 patrol; errors.log 00:34:41 no STATS for 328s (since ~00:29:13); no box_pauses row and no "box frozen" line; listener auto-restarted 00:34:41, python 3364202 started 00:34:51; STATS gap 89t 84444571..84444659; official-filled W47N8/W45N8/W45N7/W47N7 89/89, W46N8 59/89 missing 84444571..84444600 due to leftover official 404 W46N8@84444500; do not relabel NEW
    "shortws_0102": (84444961, 84445069),  # already told in 02:34 0221 patrol; errors.log 01:02:38 no STATS for 348s (since ~00:56:50) then 01:04:10 ws ping/pong timed out; no box_pauses row and no "box frozen" line; listener auto-restarted 01:02:38 and 01:04:14, python 3379693 started 01:04:24, parent 4035476; STATS gap 109t 84444961..84445069; official-filled W46N8/W47N8/W45N8/W47N7 109/109; W45N7 69/109 missing 84444961..84445000 due to leftover official 404 W45N7@84444900; do not relabel NEW
    "freeze_0203_0221": (84445891, 84446159),  # already told in 02:34 0221 patrol; 盒子休眠 02:03:03-02:21:36 (1108s, STATS 269t); box_pauses row present; errors.log box frozen line; listener auto-restarted 02:21:39, python 3411463 started 02:21:48, parent 4035476; official-filled all five 269/269 already at 0230 pre_run; do not relabel NEW
    "shortws_0257": (84446631, 84446659),  # already told in ~05:38 0522 USER_LOG; 监听短中断 02:57:18 (errors.log ws error ping/pong timed out; no box_pauses row and no box-frozen line); listener auto-restarted 02:57:21, python 3431965 started 02:57:31, parent 4035476; STATS gap 29t 84446631..84446659; official-filled W46N8/W47N8/W45N8/W45N7 29/29; W47N7 0/29 missing 84446631..84446659 due to leftover official 404 W47N7@84446600; do not relabel NEW
    "freeze_0321_0331": (84446991, 84447129),  # already told in ~05:38 0522 USER_LOG; 盒子休眠 03:21:51-03:31:05 (553s, STATS 139t); box_pauses row present; errors.log box frozen ~553s; listener auto-restarted 03:31:08, python 3445130 started 03:31:17, parent 4035476; official-filled all five 139/139 after 0330 first pass plus JP 84447100; do not relabel NEW
    "freeze_0349_0401": (84447381, 84447549),  # already told in ~05:38 0522 USER_LOG; 盒子休眠 03:49:23-04:01:11 (700s, STATS 169t); box_pauses row present; errors.log box frozen ~700s; listener auto-restarted 04:01:14, python 3455971 started 04:01:24, parent 4035476; official-filled W46N8/W47N8/W45N7/W47N7 169/169, W45N8 69/169 missing 84447401..84447500 due to leftover official 404 W45N8@84447400; do not relabel NEW
    "freeze_0418_0432": (84447781, 84447979),  # already told in ~05:38 0522 USER_LOG; 盒子休眠 04:18:52-04:32:23 (800s, STATS 199t); box_pauses row present; errors.log box frozen ~800s plus ws ping/pong timed out; listener auto-restarted 04:32:26, python 3466868 started 04:32:36, parent 4035476; official-filled W46N8/W45N8/W45N7/W47N7 199/199, W47N8 179/199 missing 84447781..84447800 due to leftover official 404 W47N8@84447700; do not relabel NEW
    "freeze_0451_0501": (84448241, 84448389),  # already told in ~05:38 0522 USER_LOG; 盒子休眠 04:51:47-05:01:57 (602s, STATS 149t); box_pauses row present; errors.log box frozen ~602s; listener auto-restarted 05:02:00, python 3477783 started 05:02:09, parent 4035476; official-filled all five 149/149; do not relabel NEW
    "freeze_0551_0556": (84449071, 84449149),  # already told in ~08:31 0820 USER_LOG; 盒子休眠 05:51:59-05:56:28 (261s, STATS 79t); box_pauses row present; errors.log box frozen ~261s; listener auto-restarted 05:56:31, python 3508501 started 05:56:40, parent 4035476; official-filled W46N8/W47N8/W45N8/W47N7 79/79, W45N7 19/79 with official empty_no_creep on the remaining 60t; do not relabel NEW until next 3h patrol tells it
    "freeze_0616_0634": (84449401, 84449669),  # already told in ~08:31 0820 USER_LOG; 盒子休眠 06:16:01-06:34:24 (1097s, STATS 269t); box_pauses row present; errors.log box frozen ~1097s; listener auto-restarted 06:34:27, python 3519788 started 06:34:37, parent 4035476; official-filled W46N8/W47N8/W45N8/W47N7 269/269, W45N7 132/269 with official empty_no_creep 137t; do not relabel NEW until next 3h patrol tells it
    "freeze_0657_0658": (84449981, 84450009),  # already told in ~08:31 0820 USER_LOG; 盒子休眠 06:57:38-06:58:46 (68s, STATS 29t); box_pauses row present; errors.log box frozen ~68s; listener auto-restarted 06:58:49, python 3533110 started 06:58:59, parent 4035476; do not relabel NEW until next 3h patrol tells it
    "freeze_0716_0736": (84450241, 84450529),  # already told in ~08:31 0820 USER_LOG; 盒子休眠 07:16:30-07:36:22 (1188s, STATS 289t); box_pauses row present; errors.log box frozen ~1188s plus ws ping/pong timed out; listener auto-restarted 07:36:25, python 3544250 started 07:36:34, parent 4035476; NOT YET TOLD
    "freeze_0809_0812": (84450981, 84451029),  # already told in ~08:31 0820 USER_LOG; 盒子休眠 08:09:21-08:12:01 (153s, STATS 49t); box_pauses row present; errors.log box frozen ~153s; listener auto-restarted 08:12:05; official-filled all five 49/49; do not relabel NEW
    "freeze_0815_0821": (84451071, 84451159),  # already told in ~08:31 0820 USER_LOG; 盒子休眠 08:15:47-08:21:02 (307s, STATS 89t); box_pauses row present; errors.log box frozen ~307s; listener auto-restarted 08:21:05, python 3565314 started 08:21:14, parent 4035476; official-filled all five 89/89 in 0830; do not relabel NEW
    "freeze_0854_0905": (84451621, 84451769),  # already told in ~11:46 1129 USER_LOG; 盒子休眠 08:54:41-09:05:01 (615s, official-filled all five 149/149; STATS 84451621..84451769); do not relabel NEW
    "freeze_0923_0930": (84452011, 84452129),  # already told in ~11:46 1129 USER_LOG; 盒子休眠 09:23:04-09:30:46 (462s, official-filled all five 119/119; STATS 84452011..84452129); do not relabel NEW
    "freeze_0948_1000": (84452371, 84452549),  # already told in ~11:46 1129 USER_LOG; 盒子休眠 09:48:37-10:00:27 (703s, official-filled all five 179/179; STATS 84452371..84452549); do not relabel NEW
    "freeze_1018_1028": (84452781, 84452939),  # already told in ~11:46 1129 USER_LOG; 盒子休眠 10:18:29-10:28:45 (610s, official-filled all five 159/159; STATS 84452781..84452939); do not relabel NEW
    "freeze_1047_1100": (84453181, 84453379),  # already told in ~11:46 1129 USER_LOG; 盒子休眠 10:47:01-11:00:07 (785s, official-filled all five 199/199; STATS 84453181..84453379); do not relabel NEW
    "freeze_1123_1129": (84453681, 84453789),  # already told in ~11:46 1129 USER_LOG; 盒子休眠 11:23:06-11:29:38 (385s, official-filled all five 109/109; STATS 84453681..84453789); do not relabel NEW
    "shortws_1158": (84454171, 84454189),  # NOT YET TOLD from quiet 1200; NEW 监听短中断 11:58:28; no box_pauses / no box-frozen; STATS 19t 84454171..84454189; official-filled four rooms 19/19, W46N8 0/19 due to official 404 W46N8@84454100; fold into next 3h patrol
    "freeze_1231_1233": (84454631, 84454679),  # NOT YET TOLD; NEW 盒子休眠 12:31:00-12:33:50 (165s); box_pauses row present; errors.log box frozen ~165s since 12:31:00; listener auto-restarted 12:33:53, python 3686982 started 12:34:02, parent 4035476; STATS 49t 84454631..84454679; official fill to be checked in wrap; fold into next 3h patrol
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
    today = [ln for ln in outp if ln.startswith(("2026-11-23", "2026-11-24")) and "restart" in ln]
    snap["listener_restarts_last"] = today[-6:]
    errp = ROOT / "metrics/errors.log"
    if errp.exists():
        rec = [ln for ln in errp.read_text().splitlines() if ln.startswith(("2026-11-23 ", "2026-11-24 "))]
        snap["errors_last"] = rec[-8:]

    (DIR / "wrapup_snap.json").write_text(json.dumps(snap, indent=2, default=str) + "\n")
    print(json.dumps(snap, indent=2, default=str))


if __name__ == "__main__":
    main()
