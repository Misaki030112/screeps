#!/usr/bin/env python3
from __future__ import annotations
import json, os, sys, subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-23_0800"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
HK = ZoneInfo("Asia/Hong_Kong")
os.chdir(ROOT)
sys.path.insert(0, "tools")
import db

# Leftover official-404 holes still worth checking (plus any new ones later).
# Last delivered 3h patrol: ~05:40 _patrol_2026-11-23_0516 USER_LOG finished_at 05:40:08
# (already delivered; do not re-tell that patrol). Prior 02:43 _patrol_2026-11-23_0216
# also already delivered. Do not write a patrol or 12h-review folder, and do not
# restart the listener.
# Quiet 05:30 half-hour _halfhour_2026-11-23_0530 wrapped 05:45:16 official-filled
# 84427901..84428600 (published_bases 84427900..84428500 at game.time=84428656;
# first pass 34/35 200, missing_chunks=1 W45N7@84428300) and JP 84428600
# (all_five_200, just_actual by-room 6/1320/442/315/541). No NEW leftover official
# 404 this 0530 pass beyond what 0516 already told. new_official_404_untold=[],
# still_untold_from_0300=[], new_box_freeze_untold=[], still_untold_freeze_from_0500=[],
# still_untold_freeze_from_0430=[], still_untold_freeze_from_0400=[],
# still_untold_freeze_from_0330=[], still_untold_freeze_from_0300=[],
# new_short_ws_untold=[] after 0530.
# Already-told leftover official 404 W45N7@84428300 and W45N8@84426200 were told
# in the ~05:40 0516 USER_LOG; retry if they still fall in/near this official
# window; do not label them as NEW. Already-told leftovers W45N8@84425500 and
# W45N8@84425800 were told in the 02:43 patrol and mentioned as already-told in
# 0516; retry if in/near window; do not label NEW. Already-told leftovers
# W45N8@84422100 and W45N8@84422400 were told in the 22:37 patrol; retry only
# if they still fall in/near this new official window; do not label them as NEW.
# Older already-told leftovers aged out of prior windows, not labeled NEW.
# Already-told 盒子休眠 05:16:36-05:25:46 and 04:53:04-04:58:42 and 04:20:59-04:35:45
# and 03:52:38-03:58:50 and 03:22:33-03:29:51 and 02:51:37-02:58:39 were told in
# the ~05:40 0516 USER_LOG; do not re-tell. Already-told freezes through
# 02:19:33-02:28:15 (told in the 02:43 patrol) and 01:46:20-02:01:27,
# 01:15:53-01:27:13, 00:51:21-00:57:39, 00:23:50-00:33:45, 23:52:01-23:59:48,
# 22:43:27-23:05:49, 21:45:57-22:04:37 and older.
# Already-told short WS through 19:12:43-19:12:57 and 16:02:42-16:02:55 and
# 12:14:21-12:14:56 and 05:25:19-05:27:20.
# Fold only newer freezes / short WS / leftover 404s than the already-told
# 05:40 0516 patrol set. Do not manually restart a healthy listener.

KNOWN_HOLES = [
    ("W47N8", 84429900),  # NEW leftover official 404 from quiet 0700 JP; retry if in/near window; NOT YET TOLD
    ("W47N7", 84429300),  # still-untold leftover official 404 from quiet 0630 JP (also first-pass 404 in 0700); retry if in/near window; NOT YET TOLD; do not re-label NEW if already recorded
    ("W45N7", 84428300),  # already told in 05:40 0516 patrol; retry if in/near window; do not label NEW
    ("W45N8", 84426200),  # already told in 05:40 0516 patrol; retry if in/near window; do not label NEW
    ("W45N8", 84425500),  # already told in 02:43 patrol; retry if in/near window; do not label NEW
    ("W45N8", 84425800),  # already told in 02:43 patrol; retry if in/near window; do not label NEW
    ("W45N8", 84422100),  # already-told leftover in 22:37 patrol; retry if in/near window
    ("W45N8", 84422400),  # already-told leftover in 22:37 patrol; retry if in/near window
    ("W45N7", 84419000),  # already-told leftover; aged out of 84420301
    ("W45N7", 84419300),  # already-told leftover; aged out of 84420301
    ("W45N8", 84419600),  # already-told leftover; aged out of 84420301
    ("W46N8", 84418900),  # already told in 18:38 patrol; aged out of 19:00 window
    ("W47N8", 84418900),
    ("W45N8", 84418900),
    ("W45N7", 84418900),
    ("W47N7", 84418900),
    ("W47N8", 84400100),
    ("W45N7", 84400300),
    ("W45N7", 84400400),
    ("W45N7", 84403700),
    ("W45N7", 84403800),
    ("W45N8", 84406400),
    ("W46N8", 84406600),
    ("W46N8", 84406700),
    ("W46N8", 84407000),
    ("W45N8", 84407700),
    ("W47N7", 84407900),
    ("W46N8", 84408300),
    ("W47N8", 84408300),
    ("W47N8", 84409800),
    ("W45N7", 84411500),
    ("W47N7", 84412400),
    ("W46N8", 84413700),
    ("W46N8", 84414700),
    ("W45N8", 84415500),
]

# Previously recorded STATS gaps. Already told through the delivered ~05:40
# patrol _patrol_2026-11-23_0516 USER_LOG (finished_at 05:40:08):
# freeze_0516_0525 (05:16:36-05:25:46, STATS 84428401..84428539),
# freeze_0453_0458, freeze_0420_0435, freeze_0352_0358, freeze_0322_0329,
# freeze_0251_0258, plus the earlier already-told set from the ~02:43 patrol
# (freeze_0219_0228 through freeze_2352_2359 and older), and already-told
# short interruption 19:12:43-19:12:57 (shortws_1912 STATS 84419821..84419849)
# and 16:02:42-16:02:55 and 12:14:21-12:14:56 and 05:25:19-05:27:20.
# Quiet 05:30 half-hour wrapped 05:45:16 found no newer leftover official 404
# or box freeze / short WS beyond the 0516 already-told set.
# Fold only newer freezes / short WS than the already-told 05:40 0516 patrol set.
# Do not restart the listener.

KNOWN_STATS_GAPS = [
    ("shortws_2021_stats", 84400171, 84400189),
    ("freeze_2049_stats", 84400561, 84400789),
    ("freeze_2142_stats", 84401311, 84401589),
    ("freeze_2214_stats", 84401751, 84401939),
    ("freeze_2249_stats", 84402241, 84402409),
    ("freeze_2320_stats", 84402681, 84402749),
    ("freeze_2353_stats", 84403151, 84403209),
    ("freeze_0011_stats", 84403391, 84403549),
    ("freeze_0050_stats", 84403921, 84404079),
    ("freeze_0118_stats", 84404311, 84404369),
    ("freeze_0150_stats", 84404761, 84404919),
    ("freeze_0213_stats", 84405081, 84405269),
    ("freeze_0244_stats", 84405501, 84405799),
    ("freeze_0347_stats", 84406431, 84406719),
    ("freeze_0418_stats", 84406881, 84406949),
    ("freeze_0441_stats", 84407211, 84407499),
    ("freeze_0517_stats", 84407741, 84407849),
    ("shortws_0525_stats", 84407871, 84407899),
    ("freeze_0552_stats", 84408271, 84408449),
    ("freeze_0621_stats", 84408691, 84408779),
    ("freeze_0650_stats", 84409111, 84409299),
    ("freeze_0720_stats", 84409551, 84409649),
    ("freeze_0744_stats", 84409901, 84410189),
    ("freeze_0851_stats", 84410881, 84411039),
    ("freeze_0914_stats", 84411221, 84411299),
    ("freeze_0941_stats", 84411621, 84411889),
    ("freeze_1016_stats", 84412131, 84412219),
    ("freeze_1045_stats", 84412541, 84412859),
    ("freeze_1145_stats", 84413411, 84413649),
    ("shortws_1214_stats", 84413821, 84413849),
    ("freeze_1220_stats", 84413921, 84413969),
    ("freeze_1251_stats", 84414371, 84414559),
    ("freeze_1316_stats", 84414731, 84414879),
    ("freeze_1348_stats", 84415191, 84415339),
    ("freeze_1415_stats", 84415571, 84415649),
    ("freeze_1447_stats", 84416041, 84416249),
    ("shortws_1602_stats", 84417111, 84417129),
    ("freeze_1615_stats", 84417291, 84417409),
    ("freeze_1644_stats", 84417731, 84417949),
    ("freeze_1712_stats", 84418131, 84418279),
    ("freeze_1741_stats", 84418531, 84418879),  # already told in 18:38 patrol
    ("shortws_1912_stats", 84419821, 84419849),  # already told in 19:36 patrol
    ("freeze_1943_stats", 84420281, 84420519),  # already told in 20:27 patrol
    ("freeze_2049_2059_stats", 84421221, 84421389),  # already told in 21:27 patrol
    ("freeze_2145_2204_stats", 84422041, 84422319),  # already told in 22:37 patrol
    ("freeze_2243_2305_stats", 84422871, 84423199),  # already told in 23:31 patrol
    ("freeze_2352_2359_stats", 84423801, 84423969),  # already told in 02:43 patrol
    ("freeze_0023_0033_stats", 84424291, 84424449),  # already told in 02:43 patrol
    ("freeze_0051_0057_stats", 84424691, 84424799),  # already told in 02:43 patrol
    ("freeze_0115_0127_stats", 84425041, 84425219),  # already told in 02:43 patrol
    ("freeze_0146_0201_stats", 84425481, 84425709),  # already told in 02:43 patrol
    ("freeze_0219_0228_stats", 84425951, 84426089),  # already told in 02:43 patrol
    ("freeze_0251_0258_stats", 84426401, 84426519),  # already told in 05:40 0516 patrol
    ("freeze_0322_0329_stats", 84426841, 84426959),  # already told in 05:40 0516 patrol
    ("freeze_0352_0358_stats", 84427261, 84427359),  # already told in 05:40 0516 patrol
    ("freeze_0420_0435_stats", 84427641, 84427859),  # already told in 05:40 0516 patrol
    ("freeze_0453_0458_stats", 84428081, 84428169),  # already told in 05:40 0516 patrol
    ("freeze_0516_0525_stats", 84428401, 84428539),  # already told in 05:40 0516 patrol
    ("freeze_0548_0606_stats", 84428841, 84429079),  # still untold from quiet 0600 half-hour; fold into next 3h patrol
    ("freeze_0623_0627_stats", 84429281, 84429349),  # still untold from quiet 0630 half-hour; fold into next 3h patrol
    ("freeze_0700_0706_stats", 84429761, 84429849),  # still untold from quiet 0700 half-hour; fold into next 3h patrol
]





def gaps(ticks):
    if not ticks:
        return []
    ticks = sorted(set(ticks))
    out = []
    expect = ticks[0]
    for t in ticks:
        if t > expect:
            out.append((expect, t - 1, t - expect))
        expect = t + 1
    return out


def main():
    now = datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
    print(f"pre_run {now}")
    live = json.loads((ROOT / "metrics/live.json").read_text())
    stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}
    print(f"live.updated {live.get('updated')} stats.t {stats.get('t')} roomSlot {live.get('roomSlot')} cpu {live.get('cpu')} gameTime {live.get('gameTime')}")

    rot = json.loads((ROOT / "metrics/listener_rot.json").read_text())
    yield_p = ROOT / "metrics/listener_yield_rooms"
    print(f"listener_rot {rot} yield_absent={not yield_p.exists()}")

    out = subprocess.check_output(["ps", "-o", "pid,ppid,lstart,etime,stat,cmd", "-C", "python"], text=True)
    n_listeners = 0
    for line in out.splitlines():
        if "tools/listener.py" in line:
            n_listeners += 1
            print("listener_ps", line.strip())
    print(f"listener_count {n_listeners}")

    with db.connect() as c:
        rows = c.execute(
            "SELECT tick FROM room_stats WHERE tick >= (SELECT max(tick)-2000 FROM room_stats) ORDER BY tick"
        ).fetchall()
        ticks = [r[0] for r in rows]
        print(f"room_stats n {len(ticks)} min {ticks[0] if ticks else None} max {ticks[-1] if ticks else None}")
        gs = gaps(ticks)
        print("room_stats gaps (start,end,len) len>=11:")
        big = []
        for g in gs:
            if g[2] >= 11:
                print(f"  {g}")
                big.append(g)
        print("room_stats all gaps count", len(gs), "len>=11", len(big))
        print("room_stats all gaps (start,end,len):")
        for g in gs:
            print(f"  {g}")

        for table in ("creep_cpu", "path_arrivals", "room_stats"):
            row = c.execute(f"SELECT min(tick), max(tick), count(*) FROM {table}").fetchone()
            print(f"{table} all min={row[0]} max={row[1]} n={row[2]}")
            print(f"  tip {row[1]}")

        tip = ticks[-1] if ticks else 0
        t0 = (tip // 100) * 100 - 1000 + 1
        print(f"creep_ticks per room recent {t0}.. now")
        for room in ROOMS:
            r = c.execute(
                "SELECT min(tick), max(tick), count(*), count(DISTINCT tick) FROM creep_ticks "
                "WHERE room=%s AND tick>=%s",
                (room, t0),
            ).fetchone()
            print(f"  {room} min={r[0]} max={r[1]} rows={r[2]} distinct={r[3]}")

        for room, base in KNOWN_HOLES:
            r = c.execute(
                "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks "
                "WHERE room=%s AND tick BETWEEN %s AND %s",
                (room, base + 1, base + 100),
            ).fetchone()
            print(f"{room}@{base} hole distinct={r[0]} rows={r[3]} range={r[1]}..{r[2]}")

        gap_specs = list(KNOWN_STATS_GAPS)
        known_spans = {(a, b) for _, a, b in KNOWN_STATS_GAPS}
        for a, b, ln in big:
            if (a, b) not in known_spans:
                gap_specs.append((f"new_stats_{a}_{b}", a, b))

        for label, a, b in gap_specs:
            r = c.execute(
                "SELECT min(tick), max(tick), count(DISTINCT tick) FROM room_stats WHERE tick BETWEEN %s AND %s",
                (a, b),
            ).fetchone()
            print(f"room_stats {label} {a}..{b} min={r[0]} max={r[1]} distinct={r[2]}")
            for room in ROOMS:
                d, mn, mx, n = c.execute(
                    "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks "
                    "WHERE room=%s AND tick BETWEEN %s AND %s",
                    (room, a, b),
                ).fetchone()
                span = b - a + 1
                print(f"  {room} fill={int(d or 0)}/{span} rows={n} range={mn}..{mx}")

    pauses = []
    with open(ROOT / "metrics/box_pauses.jsonl") as f:
        for line in f:
            line = line.strip()
            if line:
                pauses.append(json.loads(line))
    print("box_pauses last 8:")
    for p in pauses[-8:]:
        print(f"  {p}")

    outp = (ROOT / "metrics/listener.out").read_text().splitlines()
    today = [ln for ln in outp if (ln.startswith("2026-11-22") or ln.startswith("2026-11-23")) and "restart" in ln]
    print("listener.out recent restarts last 8:")
    for ln in today[-8:]:
        print(f"  {ln}")

    errp = ROOT / "metrics/errors.log"
    if errp.exists():
        lines = errp.read_text().splitlines()
        recent = [ln for ln in lines if ln.startswith("2026-11-22 ") or ln.startswith("2026-11-23 ")]
        print("errors.log since 00:00 last 16:")
        for ln in recent[-16:]:
            print(f"  {ln}")


if __name__ == "__main__":
    main()
