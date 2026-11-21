#!/usr/bin/env python3
"""Late retry just-published 84402700 with SSL retries."""
from __future__ import annotations
import json, sys, time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
sys.path.insert(0, "/workspace/screeps/scripts")
import history_backfill as hb
import db, api

ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
JP_BASE = 84402700
TICK_S = 4.220
OUTDIR = "/workspace/screeps/state/_patrol_2026-11-21_2323"
HK = ZoneInfo("Asia/Hong_Kong")

def db_range(c, room, base):
    t0, t1 = base + 1, base + 100
    row = c.execute(
        "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
        (room, t0, t1),
    ).fetchone()
    return row[0] or 0, row[1], row[2], row[3] or 0

def get_gt():
    for attempt in range(5):
        try:
            return api.req("game/time?shard=%s" % hb.SHARD)["time"]
        except Exception as e:
            print("game/time failed", attempt, e, flush=True)
            time.sleep(3 * (attempt + 1))
    raise SystemExit("game/time failed")

def history_get_retry(room, base, tries=4):
    last = None
    for i in range(tries):
        try:
            j = hb.history_get(room, base)
            time.sleep(hb.GAP_S)
            return j
        except Exception as e:
            last = e
            print("history_get fail", room, base, "try", i, type(e).__name__, e, flush=True)
            time.sleep(4 * (i + 1))
    print("history_get gave up", room, base, last, flush=True)
    return None

def insert_chunk(room, base, now_ts, gt, tick_s):
    with db.connect() as c:
        pre = db_range(c, room, base)
    print("  pre  %s@%s distinct=%s rows=%s range=%s..%s" % (room, base, pre[0], pre[3], pre[1], pre[2]), flush=True)
    j = history_get_retry(room, base)
    rec = {"room": room, "base": base, "status": 404 if not j else 200,
           "at": datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"), "gt": gt,
           "pre": {"distinct": pre[0], "rows": pre[3], "min": pre[1], "max": pre[2]}}
    if not j:
        print("  still_404_or_fail %s@%s" % (room, base), flush=True)
        rec["inserted"] = 0
        rec["still_404"] = True
        return rec
    rec["nticks"] = len(j.get("ticks") or {})
    rec["ts"] = j.get("timestamp")
    state = {}
    prev = history_get_retry(room, base - 100)
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
    rec["tmin"], rec["tmax"], rec["nrows"] = tmin, tmax, len(rows)
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
    with db.connect() as c:
        post = db_range(c, room, base)
    rec["post"] = {"distinct": post[0], "rows": post[3], "min": post[1], "max": post[2]}
    print("  recovered_or_ok %s@%s ticks=%s inserted=%s realign=%s db=%s/100" % (
        room, base, rec["nticks"], rec["inserted"], nfix, post[0]), flush=True)
    return rec

def main():
    gt = get_gt()
    now_ts = datetime.now(timezone.utc)
    print("late_retry GET start %s game.time=%s base=%s" % (
        datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"), gt, JP_BASE), flush=True)
    recs = []
    inserted = 0
    still = []
    recovered = []
    by_script = {}
    for room in ROOMS:
        rec = insert_chunk(room, JP_BASE, now_ts, gt, TICK_S)
        recs.append(rec)
        inserted += int(rec.get("inserted") or 0)
        by_script[room] = rec.get("nrows") or rec.get("inserted") or 0
        if rec.get("still_404") or rec.get("status") == 404:
            still.append("%s@%s" % (room, JP_BASE))
        else:
            recovered.append("%s@%s" % (room, JP_BASE))
    print("late recovered=%s still_404=%s inserted=%s" % (recovered, still, inserted), flush=True)
    payload = {"gt": gt, "tick_s": TICK_S, "jp": recs, "inserted": inserted,
               "still_404_jp": still, "by_script": by_script, "pass": "late"}
    with open(OUTDIR + "/just_published_late.json", "w") as f:
        json.dump(payload, f, indent=2, default=str)
        f.write("\n")
    # also merge into just_published.json as late pass
    print("finished", datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"), flush=True)

if __name__ == "__main__":
    main()
