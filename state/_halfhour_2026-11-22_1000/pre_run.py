#!/usr/bin/env python3
from __future__ import annotations
import json, os, sys, subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-22_1000"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
HK = ZoneInfo("Asia/Hong_Kong")
os.chdir(ROOT)
sys.path.insert(0, "tools")
import db

# Leftover official-404 holes still worth checking (plus any new ones later).
# Already told through the delivered 09:29 _patrol_2026-11-22_0918 USER_LOG
# and the quiet 09:37 _halfhour_2026-11-22_0930 backfill: W47N8@84409800 plus
# previously told W46N8@84408300 / W47N8@84408300 / W47N7@84407900 /
# W45N8@84407700 / W46N8@84407000 and older W45N8@84406400 / W46N8@84406600 /
# W46N8@84406700 / W45N7@84403800 / W45N7@84403700 / W45N7@84400400 /
# W45N7@84400300 / W47N8@84400100. No new leftover official 404s in the 09:37
# backfill (W47N7@84411200 recovered on the 09:18 patrol confirm).
KNOWN_HOLES = [
    ("W47N8", 84400100),
    ("W45N7", 84400300),
    ("W45N7", 84400400),
    ("W45N7", 84403700),
    ("W45N7", 84403800),
    ("W45N8", 84406400),
    ("W46N8", 84406600),
    ("W46N8", 84406700),
    ("W46N8", 84407000),  # already told in 05:22 patrol; still leftover
    ("W45N8", 84407700),  # already told in 05:22 patrol; still leftover
    ("W47N7", 84407900),  # already told in 07:35/06:44 patrols; still leftover
    ("W46N8", 84408300),  # already told in 07:35/06:44 patrols; still leftover
    ("W47N8", 84408300),  # already told in 07:35/06:44 patrols; still leftover
    ("W47N8", 84409800),  # already told in 08:28 patrol; still leftover
]

# Previously recorded STATS gaps: already told through the delivered 09:29
# patrol _patrol_2026-11-22_0918 USER_LOG through freeze_0914 and freeze_0851
# and freeze_0744 / freeze_0720 / freeze_0650 (and older freeze_0621 / 05:52 /
# 05:17 / 04:41 / 04:18 / 03:47 and earlier, plus short interruption
# 05:25:19-05:27:20). Quiet 09:37 backfill found no newer untold freeze.
# Do not write a 12h-review or patrol folder, and do not restart the listener.
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
    ("freeze_0552_stats", 84408271, 84408449),  # already told in 06:44 patrol
    ("freeze_0621_stats", 84408691, 84408779),  # already told in 06:44 patrol
    ("freeze_0650_stats", 84409111, 84409299),  # already told in 07:35 patrol
    ("freeze_0720_stats", 84409551, 84409649),  # already told in 07:35 patrol
    ("freeze_0744_stats", 84409901, 84410189),  # already told in 08:28 patrol
    ("freeze_0851_stats", 84410881, 84411039),  # already told in 09:29 patrol
    ("freeze_0914_stats", 84411221, 84411299),  # already told in 09:29 patrol
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
