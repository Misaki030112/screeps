#!/usr/bin/env python3
"""Confirm leftover official-history 404s; insert if a later GET returns 200."""
from __future__ import annotations
import json, sys, time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api

ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
# In-window first (this 40m window 84276401..84277100), then aged leftovers still 404.
TARGETS = [
    ("W47N8", 84276400),  # in-window official 404 this first pass (neighbors 84276300 and 84276600 both 200)
    ("W47N8", 84276500),  # in-window official 404 this first pass (neighbors 84276300? 84276400 404; 84276600 200)
    ("W45N7", 84275600),  # leftover official 404 (hole 84275601..84275700); aged out of this 40m window
    ("W47N8", 84275800),  # leftover official 404 (hole 84275801..84275900); aged out of this 40m window
    ("W45N8", 84275000),
    ("W47N8", 84274000),
    ("W47N8", 84273500),
    ("W47N8", 84273200),
    ("W47N7", 84272800),
    ("W45N7", 84272400),
    ("W47N7", 84269700),
    ("W46N8", 84269200),
    ("W45N8", 84267400),
    ("W47N8", 84266800),
    ("W45N7", 84266100),
    ("W45N8", 84265700),
    ("W45N8", 84264100),
    ("W46N8", 84263600),
    ("W46N8", 84262500),
    ("W47N8", 84261900),
    ("W46N8", 84260300),
    ("W45N7", 84259200),
    ("W45N8", 84258600),
    ("W45N7", 84257900),
]
TICK_S = 4.221
PASS = sys.argv[1] if len(sys.argv) > 1 else "confirm"
OUT = "/workspace/screeps/state/_halfhour_2026-11-15_1130/backfill_confirm_gets.json"

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
        with db.connect() as c:
            d, mn, mx, n = db_range(c, room, base)
        return {"ok": False, "inserted": 0, "ticks": 0, "nfix": 0, "seeded": False,
                "status": 404, "at": t0, "db_distinct": d, "db_min": mn, "db_max": mx, "db_rows": n}
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
    with db.connect() as c:
        d, mn, mx, n = db_range(c, room, base)
    return {"ok": True, "inserted": inserted, "ticks": n_hist, "recon_ticks": dticks,
            "nfix": nfix, "seeded": seeded, "tmin": tmin, "tmax": tmax, "ts": j.get("timestamp"),
            "status": 200, "at": t0, "db_distinct": d, "db_min": mn, "db_max": mx, "db_rows": n}

def main():
    our = hb.uid()
    now_ts = datetime.now(timezone.utc)
    hk = datetime.now(ZoneInfo("Asia/Hong_Kong")).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
    targets = TARGETS
    if PASS == "retry2":
        # in-window only
        targets = [t for t in TARGETS if t[1] >= 84276400]
    gt = api.req(f"game/time?shard={hb.SHARD}")["time"]
    gets = []
    with db.connect() as c:
        cm = db.current_commit(c)
    print(f"{PASS} GET start {hk} game.time={gt} tick_s={TICK_S} targets={targets}")
    recovered, still_404 = [], []
    inserted = ts_realigned = 0
    for room, base in targets:
        with db.connect() as c:
            d, mn, mx, n = db_range(c, room, base)
        print(f"  pre  {room}@{base} distinct={d} rows={n} range={mn}..{mx}")
        res = retry_one(room, base, our, now_ts, gt, tick_s=TICK_S, cm=cm)
        rec = {"t": res["at"], "room": room, "base": base, "code": res["status"],
               "ticks": res.get("ticks", 0), "ts": res.get("ts"), "game_time": gt, "pass": PASS,
               "ok": res["ok"], "inserted": res["inserted"], "nfix": res.get("nfix", 0),
               "db_distinct": res.get("db_distinct"), "db_min": res.get("db_min"),
               "db_max": res.get("db_max"), "db_rows": res.get("db_rows")}
        gets.append(rec)
        if not res["ok"]:
            print(f"  still_404 {room}@{base} at {res['at']} game.time={gt}")
            still_404.append(f"{room}@{base}")
            continue
        print(f"  recovered_or_ok {room}@{base} ticks={res['ticks']} ts={res['ts']} at {res['at']} inserted={res['inserted']}")
        inserted += res["inserted"]
        ts_realigned += res["nfix"]
        if res["inserted"] > 0:
            recovered.append(f"{room}@{base}")
    print(f"recovered={recovered} still_404={still_404} inserted={inserted} ts_realigned={ts_realigned}")
    payload = {"game_time": gt, "at": hk, "pass": PASS, "gets": gets,
               "recovered": recovered, "still_404": still_404,
               "inserted": inserted, "ts_realigned": ts_realigned}
    existing = {}
    try:
        with open(OUT) as f:
            existing = json.load(f)
    except Exception:
        existing = {}
    if PASS == "retry2":
        existing["retry2"] = payload
        existing["retry2_game_time"] = gt
        existing["retry2_at"] = hk
    else:
        existing.update(payload)
        existing["confirm_game_time"] = gt
        existing["confirm_at"] = hk
    with open(OUT, "w") as f:
        json.dump(existing, f, indent=2)
    print("gets_written", len(gets), OUT)
    print("finished")

if __name__ == "__main__":
    main()
