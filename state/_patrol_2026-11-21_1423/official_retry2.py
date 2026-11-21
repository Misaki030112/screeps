#!/usr/bin/env python3
"""Retry leftover official 404 W46N8@84394300 and aged leftovers; pull just-published 84395100."""
from __future__ import annotations
import json, sys, time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api

ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
IN_WINDOW = [
    ("W46N8", 84394300),  # already told; hole 84394380..84394400 may still 404
]
LEFTOVER = [
    ("W45N8", 84392600),
    ("W46N8", 84390400),
    ("W46N8", 84390800),
    ("W47N7", 84390900),
    ("W45N7", 84388500),
    ("W45N8", 84386600),
    ("W46N8", 84386400),
    ("W47N8", 84385900),
    ("W47N8", 84385300),
    ("W45N7", 84383500),
    ("W45N7", 84383900),
    ("W45N8", 84382600),
    ("W45N7", 84382700),
    ("W46N8", 84382900),
]
TICK_S = 4.239
OUTDIR = "/workspace/screeps/state/_patrol_2026-11-21_1423"
HK = ZoneInfo("Asia/Hong_Kong")
JP_BASE = 84395100

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
    with db.connect() as c:
        print("=== pre db ranges ===", flush=True)
        for room, base in IN_WINDOW + LEFTOVER:
            d, mn, mx, n = db_range(c, room, base)
            print(f"  pre {room}@{base} distinct={d} rows={n} min={mn} max={mx}", flush=True)
    print("=== retry IN_WINDOW / leftover hole ===", flush=True)
    for room, base in IN_WINDOW:
        rec = insert_chunk(room, base, now_ts, gt, TICK_S)
        rec["kind"] = "in_window"
        results["retries"].append(rec)
    print("=== retry LEFTOVER already-told ===", flush=True)
    for room, base in LEFTOVER:
        rec = insert_chunk(room, base, now_ts, gt, TICK_S)
        rec["kind"] = "leftover"
        results["retries"].append(rec)
    print(f"=== just-published {JP_BASE} (gt={gt}) ===", flush=True)
    if gt >= JP_BASE + 100:
        for room in ROOMS:
            rec = insert_chunk(room, JP_BASE, now_ts, gt, TICK_S)
            rec["kind"] = "just_published"
            results["just_published"].append(rec)
    else:
        print(f"  skip just-published {JP_BASE}: game.time={gt} < {JP_BASE+100}", flush=True)
        results["just_published_skipped"] = {"base": JP_BASE, "gt": gt}
    with db.connect() as c:
        print("=== post db ranges ===", flush=True)
        post = {}
        for room, base in IN_WINDOW + LEFTOVER + [(r, JP_BASE) for r in ROOMS]:
            d, mn, mx, n = db_range(c, room, base)
            post[f"{room}@{base}"] = {"distinct": d, "rows": n, "min": mn, "max": mx}
            print(f"  post {room}@{base} distinct={d} rows={n} min={mn} max={mx}", flush=True)
        results["post"] = post
        LAST_TIP, TIP = 84394330, None
        tip = c.execute("SELECT min(tick) FROM (SELECT max(tick) AS tick FROM room_stats WHERE room IN ('W46N8','W47N8') GROUP BY room) s").fetchone()[0]
        # common tip
        both = c.execute("""
            SELECT a.tick FROM room_stats a JOIN room_stats b ON a.tick=b.tick AND b.room='W47N8'
            WHERE a.room='W46N8' ORDER BY a.tick DESC LIMIT 1
        """).fetchone()
        TIP = both[0] if both else tip
        print("=== hour-window coverage LAST_TIP+1..TIP ===", TIP, flush=True)
        for room in ROOMS:
            row = c.execute(
                "SELECT count(DISTINCT tick), min(tick), max(tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
                (room, LAST_TIP+1, TIP),
            ).fetchone()
            print(f"  {room} {row[0]}/{TIP-LAST_TIP} min={row[1]} max={row[2]}", flush=True)
        print("=== room_stats gaps since 84394300 ===", flush=True)
        rows = c.execute("SELECT tick, ts FROM room_stats WHERE room='W46N8' AND tick>=84394300 ORDER BY tick").fetchall()
        for a, b in zip(rows, rows[1:]):
            if b[0] > a[0] + 15:  # ignore regular 10-tick sampling
                lo, hi = a[0]+1, b[0]-1
                fill = {}
                for room in ROOMS:
                    n = c.execute(
                        "SELECT count(DISTINCT tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
                        (room, lo, hi),
                    ).fetchone()[0]
                    fill[room] = f"{n}/{hi-lo+1}"
                print(f"  STATS gap {lo}..{hi} ({hi-lo+1}t) after {a[1]} before {b[1]} fill {fill}", flush=True)
    path = OUTDIR + "/official_retries.json"
    with open(path, "w") as f:
        json.dump(results, f, indent=2, default=str)
        f.write("\n")
    print("wrote", path, flush=True)

if __name__ == "__main__":
    main()
