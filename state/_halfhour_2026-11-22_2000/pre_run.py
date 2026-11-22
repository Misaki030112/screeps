#!/usr/bin/env python3
from __future__ import annotations
import json, os, sys, subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-22_2000"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
HK = ZoneInfo("Asia/Hong_Kong")
os.chdir(ROOT)
sys.path.insert(0, "tools")
import db

# Leftover official-404 holes still worth checking (plus any new ones later).
# Last delivered 1h patrol: ~19:36 _patrol_2026-11-22_1924 USER_LOG finished_at 19:36:36
# (do not re-tell that patrol). Do not write a patrol or 12h-review folder, and
# do not restart the listener. 12h review may start around 20:00 (last delivered ~08:33).
# Quiet 19:30/19:37 half-hour _halfhour_2026-11-22_1930 already official-filled through
# 84419900 / just-published 84420000. That run left official 404 W45N7@84419300
# and W45N8@84419600 (already told in the 19:36 patrol; retried still 404).
# Already-told leftover official 404 all five @84418900 and W45N7@84419000 aged out
# of the 19:30 window start 84419301 and were not retried then. Listener 2641627
# started 19:59:43 (parent 4035476) after auto-restart following NEW box freeze
# 19:43:54-19:59:40 (946s). Do not restart the listener.
KNOWN_HOLES = [
    ("W45N7", 84419000),  # already-told leftover; retry if still in/near overlap
    ("W45N7", 84419300),  # NEW leftover from 19:00; retry this overlap
    ("W45N8", 84419600),  # NEW leftover from 19:00; retry this overlap
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

# Previously recorded STATS gaps. Already told through the delivered ~19:36
# patrol _patrol_2026-11-22_1924 USER_LOG (finished_at 19:36:36) through
# freeze_1741 (17:41:00-18:04:50) and freeze_1712 and freeze_1644 and
# freeze_1615 and shortws_1602 and freeze_1447 and freeze_1415 and
# freeze_1348 and freeze_1316 and freeze_1251 and freeze_1220 and
# freeze_1145 and freeze_1045 and freeze_1016 and freeze_0941 and older,
# plus already-told short interruption 19:12:43-19:12:57 (shortws_1912
# STATS 84419821..84419849) and 16:02:42-16:02:55 and 12:14:21-12:14:56.
# NEW not-yet-told this run: freeze_1943 (19:43:54-19:59:40, 946s).
# Leave it to be detected as a new gap and include it. Do not restart the listener.
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
    ("freeze_1943_stats", 84420281, 84420519),  # NEW 19:43:54-19:59:40 946s; detected pre_run
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
    today = [ln for ln in outp if (ln.startswith("2026-11-21") or ln.startswith("2026-11-22")) and "restart" in ln]
    print("listener.out recent restarts last 8:")
    for ln in today[-8:]:
        print(f"  {ln}")

    errp = ROOT / "metrics/errors.log"
    if errp.exists():
        lines = errp.read_text().splitlines()
        recent = [ln for ln in lines if ln.startswith("2026-11-22 ")]
        print("errors.log since 00:00 last 16:")
        for ln in recent[-16:]:
            print(f"  {ln}")


if __name__ == "__main__":
    main()
