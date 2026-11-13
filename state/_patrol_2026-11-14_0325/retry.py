#!/usr/bin/env python3
"""Confirm + retry missing official-history chunks for this 40m window."""
from __future__ import annotations
import json, sys, time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api

ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
# in-window hole from first pass, plus its two adjacent published bases
THIS_WINDOW = [("W45N7", 84250800), ("W47N8", 84250900), ("W45N8", 84250900), ("W47N7", 84250900)]
ADJ = [("W45N7", 84250700), ("W45N7", 84250900), ("W47N8", 84250800), ("W45N8", 84250800), ("W47N7", 84250800)]
# leftover official 404s just outside / recent
OUTSIDE = [("W47N8", 84249600), ("W45N8", 84248300)]
TICK_S = 4.425
TMIN, TMAX = 84250301, 84251000

def db_range(c, room, base):
    t0, t1 = base + 1, base + 100
    row = c.execute(
        "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
        (room, t0, t1),
    ).fetchone()
    return row[0] or 0, row[1], row[2], row[3] or 0

def fetch_seed(room, base):
    prev = hb.history_get(room, base - 100)
    time.sleep(hb.GAP_S)
    state = {}
    if prev:
        for _tick, objs in hb.merge_chunk(prev, state):
            pass
        return state, True
    return {}, False

def insert_rows(rows, now_ts, gt, tick_s, tmin, tmax, rooms):
    if not rows:
        return 0, 0
    with db.connect() as c:
        exist = hb.already(c, tmin, tmax, rooms)
    new_rows = [r for r in rows if (r[3], r[1]) not in exist]
    if new_rows:
        sql = ('INSERT INTO creep_ticks (ts,tick,room,creep,role,x,y,hits,store,state,commit) '
               'SELECT %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s '
               'WHERE NOT EXISTS (SELECT 1 FROM creep_ticks c WHERE c.creep=%s AND c.tick=%s)')
        packed = [r + (r[3], r[1]) for r in new_rows]
        with db.connect(autocommit=False) as c:
            with c.cursor() as cur:
                cur.executemany(sql, packed)
            c.commit()
    nfix = 0
    with db.connect(autocommit=False) as c:
        nfix = hb.realign_ts(c, tmin, tmax, rooms, now_ts, gt, tick_s)
        c.commit()
    return len(new_rows), nfix

def retry_one(room, base, our, now_ts, gt, tick_s, cm):
    t0 = datetime.now(ZoneInfo("Asia/Hong_Kong")).strftime("%H:%M:%S")
    j = hb.history_get(room, base)
    time.sleep(hb.GAP_S)
    if not j:
        return {"ok": False, "inserted": 0, "ticks": 0, "nfix": 0, "seeded": False, "status": 404, "at": t0}
    state, seeded = fetch_seed(room, base)
    rows = []
    tmin = tmax = None
    n_hist = len(j.get("ticks") or {})
    for tick, objs in hb.merge_chunk(j, state):
        ts = hb.tick_time(now_ts, gt, tick, tick_s)
        rows.extend(hb.creep_rows(tick, room, objs, our, ts, cm))
        tmin = tick if tmin is None else min(tmin, tick)
        tmax = tick if tmax is None else max(tmax, tick)
    inserted, nfix = insert_rows(rows, now_ts, gt, tick_s, tmin, tmax, (room,))
    dticks = len({r[1] for r in rows})
    return {"ok": True, "inserted": inserted, "ticks": n_hist, "recon_ticks": dticks,
            "nfix": nfix, "seeded": seeded, "tmin": tmin, "tmax": tmax, "ts": j.get("timestamp"),
            "status": 200, "at": t0}

def main():
    our = hb.uid()
    now_ts = datetime.now(timezone.utc)
    hk = datetime.now(ZoneInfo("Asia/Hong_Kong")).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
    gt = api.req(f"game/time?shard={hb.SHARD}")["time"]
    tick_s = TICK_S
    gets = []
    with db.connect() as c:
        cm = db.current_commit(c)
    print(f"confirm GET start {hk} game.time={gt} tick_s={tick_s}")
    recovered, still_404 = [], []
    inserted_retry = ts_realigned_retry = 0

    # confirm hole + insert if recovered
    for room, base in THIS_WINDOW + OUTSIDE:
        with db.connect() as c:
            d, mn, mx, n = db_range(c, room, base)
        print(f"  pre  {room}@{base} distinct={d} rows={n} range={mn}..{mx}")
        res = retry_one(room, base, our, now_ts, gt, tick_s, cm)
        gets.append({"room": room, "base": base, "status": res["status"], "ticks": res.get("ticks", 0), "at": res.get("at")})
        if not res["ok"]:
            print(f"  still_404 {room}@{base} at {res['at']}")
            with db.connect() as c:
                d2, mn2, mx2, n2 = db_range(c, room, base)
            print(f"  post {room}@{base} distinct={d2}/100 rows={n2} range={mn2}..{mx2}")
            still_404.append(f"{room}@{base}")
            continue
        print(f"  recovered {room}@{base} ticks={res['ticks']} ts={res['ts']} at {res['at']}")
        print(f"  inserted={res['inserted']} ts_realigned={res['nfix']} recon={res['recon_ticks']} ticks={res['tmin']}..{res['tmax']}")
        inserted_retry += res["inserted"]
        ts_realigned_retry += res["nfix"]
        with db.connect() as c:
            d2, mn2, mx2, n2 = db_range(c, room, base)
        print(f"  post {room}@{base} distinct={d2}/100 rows={n2} range={mn2}..{mx2}")
        recovered.append(f"{room}@{base}")

    # adjacent / current published-or-unpub confirm only
    for room, base in ADJ:
        t0 = datetime.now(ZoneInfo("Asia/Hong_Kong")).strftime("%H:%M:%S")
        j = hb.history_get(room, base)
        time.sleep(hb.GAP_S)
        n = len((j or {}).get("ticks") or {})
        st = 200 if j else 404
        print(f"  adj  {room}@{base} status={st} ticks={n} at {t0}")
        gets.append({"room": room, "base": base, "status": st, "ticks": n, "at": t0, "kind": "adj"})

    # confirm current in-progress chunk 84250100 unpublished?
    latest_unpub = (gt // 100) * 100
    for room in ROOMS:
        t0 = datetime.now(ZoneInfo("Asia/Hong_Kong")).strftime("%H:%M:%S")
        j = hb.history_get(room, latest_unpub)
        time.sleep(hb.GAP_S)
        n = len((j or {}).get("ticks") or {})
        st = 200 if j else 404
        print(f"  unpub {room}@{latest_unpub} status={st} ticks={n} at {t0}")
        gets.append({"room": room, "base": latest_unpub, "status": st, "ticks": n, "at": t0, "kind": "unpub"})

    print(f"recovered={recovered} still_404={still_404} inserted_retry={inserted_retry} ts_realigned_retry={ts_realigned_retry}")
    with db.connect() as c:
        print("db_after_retry")
        for room in ROOMS:
            row = c.execute(
                "SELECT min(tick), max(tick), count(*), count(DISTINCT tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
                (room, TMIN, TMAX),
            ).fetchone()
            print(f"  {room} ticks={row[0]}..{row[1]} rows={row[2]} distinct={row[3]}")
    out = "/workspace/screeps/state/_patrol_2026-11-14_0325/backfill_retry_gets.json"
    with open(out, "w") as f:
        json.dump(gets, f, indent=2)
    print("gets_written", len(gets), out)
    print("finished")

if __name__ == "__main__":
    main()
