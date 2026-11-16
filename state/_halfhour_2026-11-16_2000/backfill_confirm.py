#!/usr/bin/env python3
"""Confirm leftover official-history 404s and in-window 404s; insert if a later GET returns 200."""
from __future__ import annotations
import json, sys, time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api

ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
# First pass missing_chunks=0 at game.time=84303888; published_bases 84303100..84303700,
# reconstructed 84303101..84303800 (700). inserted=9987, already_in_db=18513,
# ts_realigned_first_pass=1441 on first-interval tick_s=4.87164 (printed 4.872);
# later-mean-robust to be filled from tick_s_realign.json after tick_s_check.
# No in-window official 404 this pass. Previous leftover W45N8@84302200
# (hole 84302201..84302300, 0 live) is just outside TMIN and MUST be retried as a leftover.
# Leftovers from prior runs (still 404 at 19:15 confirm/retry2):
# W45N8@84302200 (0 rows), W47N8@84300900 (74 live, holes 84300965..84300983 and 84300994..84301000),
# W45N8@84300900 (7 live 84300994..84301000), W45N8@84300000 (26 live + 74 empty),
# W47N8@84298000 (still empty), W47N8@84297200 (live-filled),
# W47N7@84296500, W45N8@84295900, W45N7@84295800.
IN_WINDOW = [
    ("W45N8", 84302200),
    ("W47N8", 84300900),
    ("W45N8", 84300900),
    ("W45N8", 84300000),
    ("W47N8", 84298000),
    ("W47N8", 84297200),
    ("W47N7", 84296500),
    ("W45N8", 84295900),
    ("W45N7", 84295800),
]
AGED = [
    ("W46N8", 84292000),
    ("W47N8", 84290200),
    ("W47N7", 84289200),
    ("W45N7", 84289300),
    ("W47N8", 84287500),
    ("W45N7", 84285500),
    ("W45N8", 84282500),
    ("W47N8", 84281500),
    ("W45N8", 84281500),
    ("W45N8", 84279700),
    ("W45N8", 84277800),
    ("W47N8", 84276400),
    ("W47N8", 84276500),
    ("W45N7", 84275600),
    ("W47N8", 84275800),
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
    ("W45N8", 84258600),
    ("W45N7", 84259200),
    ("W45N7", 84257900),
]
TICK_S = 4.87164  # first-interval; overwritten from tick_s_realign.json if present
PASS = sys.argv[1] if len(sys.argv) > 1 else "confirm"
OUT = "/workspace/screeps/state/_halfhour_2026-11-16_2000/backfill_confirm_gets.json"
TICK_S_FILE = "/workspace/screeps/state/_halfhour_2026-11-16_2000/tick_s_realign.json"

def load_tick_s():
    global TICK_S
    try:
        j = json.load(open(TICK_S_FILE))
        if j.get("corrective_applied"):
            TICK_S = float(j["later_mean_w46"])
        else:
            TICK_S = float(j.get("tick_s_used_first_pass") or j.get("later_mean_w46") or TICK_S)
    except Exception:
        pass

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
    load_tick_s()
    our = hb.uid()
    now_ts = datetime.now(timezone.utc)
    hk = datetime.now(ZoneInfo("Asia/Hong_Kong")).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
    if PASS == "retry2":
        targets = list(IN_WINDOW)
    else:
        targets = IN_WINDOW + AGED
    if not targets:
        print(f"{PASS} GET skipped, no targets at {hk}")
        payload = {"game_time": None, "at": hk, "pass": PASS, "gets": [],
                   "recovered": [], "still_404": [], "inserted": 0, "ts_realigned": 0, "tick_s": TICK_S,
                   "skipped": True, "reason": "no targets"}
        existing = {}
        try:
            with open(OUT) as f:
                existing = json.load(f)
        except Exception:
            existing = {}
        if PASS == "retry2":
            existing["retry2"] = payload
            existing["retry2_skipped"] = True
        else:
            existing.update(payload)
        with open(OUT, "w") as f:
            json.dump(existing, f, indent=2)
        print("finished")
        return
    gt = None
    for attempt in range(3):
        try:
            gt = api.req(f"game/time?shard={hb.SHARD}")["time"]
            break
        except Exception as e:
            print(f"game/time attempt {attempt+1} failed: {e!r}")
            time.sleep(3 * (attempt + 1))
    if gt is None:
        raise SystemExit("game/time failed after 3 attempts")
    gets = []
    with db.connect() as c:
        cm = db.current_commit(c)
    print(f"{PASS} GET start {hk} game.time={gt} tick_s={TICK_S} targets={len(targets)}")
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
               "inserted": inserted, "ts_realigned": ts_realigned, "tick_s": TICK_S}
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
        existing["retry2_inserted"] = inserted
        existing["retry2_ts_realigned"] = ts_realigned
        existing["retry2_recovered"] = recovered
        existing["retry2_still_404"] = still_404
        existing["retry2_gets"] = gets
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
