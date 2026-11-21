#!/usr/bin/env python3
"""Retry in-window official 404s; then try just-published next chunk; report coverage."""
from __future__ import annotations
import json, sys, time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api

ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
IN_WINDOW = [
    ("W45N7", 84397400),  # leftover from 17:00 backfill; first-pass this hour still 404
    ("W47N8", 84397600),  # first-pass 404 (W46N8/W45N7 at 84397600 were 200)
    ("W45N8", 84397600),
    ("W47N7", 84397600),
]
LEFTOVER = [
    ("W47N7", 84395600),
    ("W47N8", 84395100),
    ("W46N8", 84394300),
    ("W45N8", 84392600),
    ("W46N8", 84390400),
    ("W46N8", 84390800),
    ("W47N7", 84390900),
    ("W45N7", 84388500),
    ("W45N8", 84386600),
]
# official interval W46N8@84397000..84397600: (1795253057610-1795250506874)/600/1000
TICK_S = 4.251
OUTDIR = "/workspace/screeps/state/_patrol_2026-11-21_1722"
HK = ZoneInfo("Asia/Hong_Kong")
JP_BASE = 84397700  # next chunk after published_bases 84397000..84397600


def db_range(c, room, base):
    t0, t1 = base + 1, base + 100
    row = c.execute(
        "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
        (room, t0, t1),
    ).fetchone()
    return row[0] or 0, row[1], row[2], row[3] or 0


def insert_chunk(room, base, now_ts, gt, tick_s):
    j = hb.history_get(room, base)
    time.sleep(hb.GAP_S)
    rec = {
        "room": room,
        "base": base,
        "status": 404 if not j else 200,
        "at": datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"),
        "gt": gt,
    }
    if not j:
        print("  404 %s@%s" % (room, base), flush=True)
        rec["inserted"] = 0
        return rec
    rec["nticks"] = len(j.get("ticks") or {})
    rec["ts"] = j.get("timestamp")
    state = {}
    prev = hb.history_get(room, base - 100)
    time.sleep(hb.GAP_S)
    if prev:
        for _tick, objs in hb.merge_chunk(prev, state):
            pass
        rec["seeded"] = True
    else:
        rec["seeded"] = False
    our = hb.uid()
    with db.connect() as c:
        cm = db.current_commit(c)
    rows = []
    tmin = tmax = None
    for tick, objs in hb.merge_chunk(j, state):
        ts = hb.tick_time(now_ts, gt, tick, tick_s)
        rows.extend(hb.creep_rows(tick, room, objs, our, ts, cm))
        tmin = tick if tmin is None else min(tmin, tick)
        tmax = tick if tmax is None else max(tmax, tick)
    rec["tmin"] = tmin
    rec["tmax"] = tmax
    rec["nrows"] = len(rows)
    if not rows:
        print("  empty %s@%s ticks=%s" % (room, base, rec["nticks"]), flush=True)
        rec["inserted"] = 0
        return rec
    with db.connect() as c:
        exist = hb.already(c, tmin, tmax, [room])
    new_rows = [r for r in rows if (r[3], r[1]) not in exist]
    if new_rows:
        sql = (
            "INSERT INTO creep_ticks (ts,tick,room,creep,role,x,y,hits,store,state,commit) "
            "SELECT %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s "
            "WHERE NOT EXISTS (SELECT 1 FROM creep_ticks c WHERE c.creep=%s AND c.tick=%s)"
        )
        packed = [r + (r[3], r[1]) for r in new_rows]
        with db.connect(autocommit=False) as c:
            with c.cursor() as cur:
                cur.executemany(sql, packed)
            c.commit()
    nfix = 0
    with db.connect(autocommit=False) as c:
        nfix = hb.realign_ts(c, tmin, tmax, [room], now_ts, gt, tick_s)
        c.commit()
    rec["inserted"] = len(new_rows)
    rec["ts_realigned"] = nfix
    print(
        "  %s@%s status=200 ticks=%s range=%s..%s inserted=%s realign=%s"
        % (room, base, rec["nticks"], tmin, tmax, len(new_rows), nfix),
        flush=True,
    )
    return rec


def main():
    now_ts = datetime.now(timezone.utc)
    gt = api.req("game/time?shard=%s" % hb.SHARD)["time"]
    print("game.time", gt, "at", datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"), "tick_s", TICK_S, flush=True)
    results = {"gt": gt, "tick_s": TICK_S, "retries": [], "just_published": []}

    print("=== pre db ranges ===", flush=True)
    with db.connect() as c:
        for room, base in IN_WINDOW + LEFTOVER:
            d, mn, mx, n = db_range(c, room, base)
            print("  pre %s@%s distinct=%s rows=%s min=%s max=%s" % (room, base, d, n, mn, mx), flush=True)

    print("=== retry IN_WINDOW ===", flush=True)
    for room, base in IN_WINDOW:
        rec = insert_chunk(room, base, now_ts, gt, TICK_S)
        rec["kind"] = "in_window"
        results["retries"].append(rec)

    print("=== retry LEFTOVER already-told ===", flush=True)
    for room, base in LEFTOVER:
        rec = insert_chunk(room, base, now_ts, gt, TICK_S)
        rec["kind"] = "leftover"
        results["retries"].append(rec)

    print("=== just-published %s (gt=%s) ===" % (JP_BASE, gt), flush=True)
    deadline = time.time() + 90
    while gt < JP_BASE + 100 and time.time() < deadline:
        print("  wait gt=%s < %s" % (gt, JP_BASE + 100), flush=True)
        time.sleep(15)
        gt = api.req("game/time?shard=%s" % hb.SHARD)["time"]
        results["gt"] = gt
    if gt >= JP_BASE + 100:
        for room in ROOMS:
            rec = insert_chunk(room, base=JP_BASE, now_ts=now_ts, gt=gt, tick_s=TICK_S)
            rec["kind"] = "just_published"
            results["just_published"].append(rec)
            if rec["status"] == 404:
                time.sleep(8)
                rec2 = insert_chunk(room, JP_BASE, now_ts, gt, TICK_S)
                rec2["kind"] = "just_published_retry"
                results["just_published"].append(rec2)
    else:
        print("  skip just-published %s: game.time=%s < %s" % (JP_BASE, gt, JP_BASE + 100), flush=True)
        results["just_published_skipped"] = {"base": JP_BASE, "gt": gt}

    print("=== post db ranges ===", flush=True)
    with db.connect() as c:
        post = {}
        keys = IN_WINDOW + LEFTOVER + [(r, JP_BASE) for r in ROOMS]
        # unique
        seen = set()
        uniq = []
        for item in keys:
            if item not in seen:
                seen.add(item)
                uniq.append(item)
        for room, base in uniq:
            d, mn, mx, n = db_range(c, room, base)
            post["%s@%s" % (room, base)] = {"distinct": d, "rows": n, "min": mn, "max": mx}
            print("  post %s@%s distinct=%s rows=%s min=%s max=%s" % (room, base, d, n, mn, mx), flush=True)
        results["post"] = post

        LAST_TIP, TIP_GUESS = 84396870, 84397700
        print("=== hour-window coverage LAST_TIP+1..TIP ===", flush=True)
        cov = {}
        for room in ROOMS:
            row = c.execute(
                "SELECT count(DISTINCT tick), min(tick), max(tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
                (room, LAST_TIP + 1, TIP_GUESS),
            ).fetchone()
            cov[room] = {"distinct": row[0], "min": row[1], "max": row[2], "expected": TIP_GUESS - LAST_TIP}
            print("  %s %s/%s min=%s max=%s" % (room, row[0], TIP_GUESS - LAST_TIP, row[1], row[2]), flush=True)
        results["hour_cov_through_tip_guess"] = cov

        print("=== room_stats gaps since 84396800 ===", flush=True)
        gaps = []
        rows = c.execute(
            "SELECT tick, ts FROM room_stats WHERE room='W46N8' AND tick>=84396800 ORDER BY tick"
        ).fetchall()
        for a, b in zip(rows, rows[1:]):
            if b[0] > a[0] + 1:
                gaps.append({"after": a[0], "after_ts": str(a[1]), "next": b[0], "next_ts": str(b[1]), "missing": b[0] - a[0] - 1})
                print("  STATS gap %s..%s (%st) after %s before %s" % (a[0] + 1, b[0] - 1, b[0] - a[0] - 1, a[1], b[1]), flush=True)
        results["stats_gaps"] = gaps
        for g in gaps:
            lo, hi = g["after"] + 1, g["next"] - 1
            fill = {}
            for room in ROOMS:
                n = c.execute(
                    "SELECT count(DISTINCT tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
                    (room, lo, hi),
                ).fetchone()[0]
                fill[room] = "%s/%s" % (n, hi - lo + 1)
            g["official_fill"] = fill
            print("  fill %s..%s %s" % (lo, hi, fill), flush=True)

        freezes = [
            ("told_1616", 84396751, 84396799),
            ("new_1648", 84397201, 84397439),
        ]
        for name, lo, hi in freezes:
            fill = {}
            for room in ROOMS:
                n = c.execute(
                    "SELECT count(DISTINCT tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
                    (room, lo, hi),
                ).fetchone()[0]
                fill[room] = "%s/%s" % (n, hi - lo + 1)
            print("  freeze %s %s..%s %s" % (name, lo, hi, fill), flush=True)
            results["freeze_%s" % name] = fill

    path = OUTDIR + "/official_retries.json"
    with open(path, "w") as f:
        json.dump(results, f, indent=2, default=str)
        f.write("\n")
    print("wrote", path, flush=True)


if __name__ == "__main__":
    main()
