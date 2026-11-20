#!/usr/bin/env python3
"""Retry in-window official 404s; then try just-published next chunk; report coverage/freezes."""
from __future__ import annotations
import json, sys, time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api

ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
# first-pass 40-min backfill this hour: missing_chunks=0, no NEW official 404s
IN_WINDOW = [
]
# leftover already-told, retry once in case it published
LEFTOVER = [
    ("W47N7", 84378000),  # already told by 18:31 1h patrol; hole 84378001..84378100 overlaps first 10t of hour window start 84378091
    ("W46N8", 84377600),  # already told by 18:31; aged out of hour window start 84378091
]
TICK_S = 4.244  # this hour first-pass official history (40-min 84378201..84378900)
OUTDIR = "/workspace/screeps/state/_patrol_2026-11-20_1923"
HK = ZoneInfo("Asia/Hong_Kong")

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
    rec = {"room": room, "base": base, "status": 404 if not j else 200, "at": datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"), "gt": gt}
    if not j:
        print(f"  404 {room}@{base}", flush=True)
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
        print(f"  empty {room}@{base} ticks={rec['nticks']}", flush=True)
        rec["inserted"] = 0
        return rec
    with db.connect() as c:
        exist = hb.already(c, tmin, tmax, [room])
    new_rows = [r for r in rows if (r[3], r[1]) not in exist]
    if new_rows:
        sql = ("INSERT INTO creep_ticks (ts,tick,room,creep,role,x,y,hits,store,state,commit) "
               "SELECT %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s "
               "WHERE NOT EXISTS (SELECT 1 FROM creep_ticks c WHERE c.creep=%s AND c.tick=%s)")
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
    print(f"  {room}@{base} status=200 ticks={rec['nticks']} range={tmin}..{tmax} inserted={len(new_rows)} realign={nfix}", flush=True)
    return rec

def main():
    now_ts = datetime.now(timezone.utc)
    gt = api.req(f"game/time?shard={hb.SHARD}")["time"]
    print("game.time", gt, "at", datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"), "tick_s", TICK_S, flush=True)
    results = {"gt": gt, "tick_s": TICK_S, "retries": [], "just_published": []}

    print("=== pre db ranges ===", flush=True)
    with db.connect() as c:
        for room, base in IN_WINDOW + LEFTOVER:
            d, mn, mx, n = db_range(c, room, base)
            print(f"  pre {room}@{base} distinct={d} rows={n} min={mn} max={mx}", flush=True)

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

    # just-published: next base after 84376300 is 84376400 once gt is past ~84376500
    jp_base = 84378900
    print(f"=== just-published {jp_base} (gt={gt}) ===", flush=True)
    if gt >= jp_base + 100:
        for room in ROOMS:
            rec = insert_chunk(room, jp_base, now_ts, gt, TICK_S)
            rec["kind"] = "just_published"
            results["just_published"].append(rec)
    else:
        print(f"  skip just-published {jp_base}: game.time={gt} < {jp_base+100}", flush=True)
        results["just_published_skipped"] = {"base": jp_base, "gt": gt}

    print("=== post db ranges ===", flush=True)
    with db.connect() as c:
        post = {}
        for room, base in IN_WINDOW + LEFTOVER + [(r, jp_base) for r in ROOMS]:
            d, mn, mx, n = db_range(c, room, base)
            post[f"{room}@{base}"] = {"distinct": d, "rows": n, "min": mn, "max": mx}
            print(f"  post {room}@{base} distinct={d} rows={n} min={mn} max={mx}", flush=True)
        results["post"] = post

        # hour window and freeze coverage
        LAST_TIP, TIP_GUESS = 84378090, 84378900
        print("=== hour-window coverage LAST_TIP+1..84378900 ===", flush=True)
        cov = {}
        for room in ROOMS:
            row = c.execute(
                "SELECT count(DISTINCT tick), min(tick), max(tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
                (room, LAST_TIP+1, TIP_GUESS),
            ).fetchone()
            cov[room] = {"distinct": row[0], "min": row[1], "max": row[2], "expected": TIP_GUESS-LAST_TIP}
            print(f"  {room} {row[0]}/{TIP_GUESS-LAST_TIP} min={row[1]} max={row[2]}", flush=True)
        results["hour_cov_through_78900"] = cov

        # freeze STATS gaps from room_stats
        print("=== room_stats gaps since 84378000 ===", flush=True)
        gaps = []
        rows = c.execute(
            "SELECT tick, ts FROM room_stats WHERE room='W46N8' AND tick>=84378000 ORDER BY tick"
        ).fetchall()
        for a, b in zip(rows, rows[1:]):
            if b[0] > a[0] + 1:
                gaps.append({"after": a[0], "after_ts": str(a[1]), "next": b[0], "next_ts": str(b[1]), "missing": b[0]-a[0]-1})
                print(f"  STATS gap {a[0]+1}..{b[0]-1} ({b[0]-a[0]-1}t) after {a[1]} before {b[1]}", flush=True)
        results["stats_gaps"] = gaps

        # official fill of known freezes
        freezes = [
            # previous hour already told 15:44-16:03 and 16:17-16:22
        ]
        # also fill any gap ranges
        for g in gaps:
            lo, hi = g["after"]+1, g["next"]-1
            fill = {}
            for room in ROOMS:
                n = c.execute(
                    "SELECT count(DISTINCT tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
                    (room, lo, hi),
                ).fetchone()[0]
                fill[room] = f"{n}/{hi-lo+1}"
            g["official_fill"] = fill
            print(f"  fill {lo}..{hi} {fill}", flush=True)

        for name, lo, hi in freezes:
            fill = {}
            for room in ROOMS:
                n = c.execute(
                    "SELECT count(DISTINCT tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
                    (room, lo, hi),
                ).fetchone()[0]
                fill[room] = f"{n}/{hi-lo+1}"
            print(f"  freeze {name} {lo}..{hi} {fill}", flush=True)
            results[f"freeze_{name}"] = fill

    path = OUTDIR + "/official_retries.json"
    with open(path, "w") as f:
        json.dump(results, f, indent=2, default=str)
        f.write('\n')
    print("wrote", path, flush=True)

if __name__ == "__main__":
    main()
