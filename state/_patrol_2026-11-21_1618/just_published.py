#!/usr/bin/env python3
from __future__ import annotations
import json, sys, time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api

ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S = 4.271
OUTDIR = "/workspace/screeps/state/_patrol_2026-11-21_1618"
HK = ZoneInfo("Asia/Hong_Kong")
JP_BASE = 84394300

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
    print("  %s@%s status=200 ticks=%s range=%s..%s inserted=%s realign=%s" % (room, base, rec["nticks"], tmin, tmax, len(new_rows), nfix), flush=True)
    return rec

def main():
    now_ts = datetime.now(timezone.utc)
    gt = api.req("game/time?shard=%s" % hb.SHARD)["time"]
    print("game.time", gt, "at", datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"), "tick_s", TICK_S, flush=True)
    results = {"gt": gt, "tick_s": TICK_S, "just_published": []}
    print("=== just-published %s (gt=%s) ===" % (JP_BASE, gt), flush=True)
    deadline = time.time() + 180
    while gt < JP_BASE + 100 and time.time() < deadline:
        print("  wait gt=%s < %s" % (gt, JP_BASE + 100), flush=True)
        time.sleep(15)
        gt = api.req("game/time?shard=%s" % hb.SHARD)["time"]
        results["gt"] = gt
    if gt >= JP_BASE + 100:
        for room in ROOMS:
            rec = insert_chunk(room, JP_BASE, now_ts, gt, TICK_S)
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
    print("=== post ranges ===", flush=True)
    with db.connect() as c:
        for room in ROOMS:
            d, mn, mx, n = db_range(c, room, JP_BASE)
            print("  post %s@%s distinct=%s rows=%s min=%s max=%s" % (room, JP_BASE, d, n, mn, mx), flush=True)
    path = OUTDIR + "/just_published.json"
    with open(path, "w") as f:
        json.dump(results, f, indent=2, default=str)
        f.write(chr(10))
    print("wrote", path, flush=True)

if __name__ == "__main__":
    main()
