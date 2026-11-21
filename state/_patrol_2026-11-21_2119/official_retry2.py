#!/usr/bin/env python3
"""Retry in-window official 404s; insert if a later GET returns 200."""
from __future__ import annotations
import json, sys, time
from datetime import datetime
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api

ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
# First pass at game.time=84400206; published_bases 84399500..84400100,
# reconstructed 84399501..84400200 (700). first pass 30/35 official GETs 200,
# missing_chunks=5: W45N8@84399500 (not yet told, from 19:47), W45N7@84399800
# (not yet told, from 20:00 halfhour), and NEW first-pass W47N8@84400100,
# W45N8@84400100, W47N7@84400100. Aged-out leftovers W45N8@84399300 and
# all-five @84399100 are not retried.
IN_WINDOW = [
    ("W45N7", 84400300),
    ("W45N7", 84400400),
]
TICK_S = 4.314
PASS = sys.argv[1] if len(sys.argv) > 1 else "confirm"
OUTDIR = "/workspace/screeps/state/_patrol_2026-11-21_2119"
HK = ZoneInfo("Asia/Hong_Kong")


def db_range(c, room, base):
    t0, t1 = base + 1, base + 100
    row = c.execute(
        "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
        (room, t0, t1),
    ).fetchone()
    return row[0] or 0, row[1], row[2], row[3] or 0


def insert_chunk(room, base, now_ts, gt, tick_s):
    with db.connect() as c:
        pre = db_range(c, room, base)
    print("  pre  %s@%s distinct=%s rows=%s range=%s..%s" % (room, base, pre[0], pre[3], pre[1], pre[2]), flush=True)
    j = hb.history_get(room, base)
    time.sleep(hb.GAP_S)
    rec = {
        "room": room,
        "base": base,
        "status": 404 if not j else 200,
        "at": datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"),
        "gt": gt,
        "pre": {"distinct": pre[0], "rows": pre[3], "min": pre[1], "max": pre[2]},
    }
    if not j:
        print("  still_404 %s@%s at %s game.time=%s" % (room, base, rec["at"][-14:], gt), flush=True)
        rec["inserted"] = 0
        rec["still_404"] = True
        return rec
    rec["nticks"] = len(j.get("ticks") or {})
    rec["ts"] = j.get("timestamp")
    state = {}
    prev = hb.history_get(room, base - 100)
    time.sleep(hb.GAP_S)
    seeded = False
    if prev:
        for _tick, objs in hb.merge_chunk(prev, state):
            pass
        seeded = True
    rec["seeded"] = seeded
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
    with db.connect() as c:
        post = db_range(c, room, base)
    rec["post"] = {"distinct": post[0], "rows": post[3], "min": post[1], "max": post[2]}
    print(
        "  recovered_or_ok %s@%s ticks=%s inserted=%s realign=%s db=%s/100"
        % (room, base, rec["nticks"], rec["inserted"], nfix, post[0]),
        flush=True,
    )
    return rec


def main():
    now_ts, gt = api.now_and_time()
    print(
        "%s GET start %s game.time=%s tick_s=%s targets=%s"
        % (PASS, datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"), gt, TICK_S, len(IN_WINDOW)),
        flush=True,
    )
    recs = []
    inserted = 0
    still = []
    recovered = []
    for room, base in IN_WINDOW:
        rec = insert_chunk(room, base, now_ts, gt, TICK_S)
        recs.append(rec)
        inserted += int(rec.get("inserted") or 0)
        if rec.get("still_404") or rec.get("status") == 404:
            still.append("%s@%s" % (room, base))
        else:
            recovered.append("%s@%s" % (room, base))
    outp = "%s/official_%s_gets.json" % (OUTDIR, PASS)
    with open(outp, "w") as f:
        json.dump({"pass": PASS, "gt": gt, "tick_s": TICK_S, "recs": recs}, f, indent=2, default=str)
        f.write("\n")
    print(
        "recovered=%s still_404=%s inserted=%s gets_written %s %s"
        % (recovered, still, inserted, len(recs), outp),
        flush=True,
    )
    print("finished", flush=True)


if __name__ == "__main__":
    main()
