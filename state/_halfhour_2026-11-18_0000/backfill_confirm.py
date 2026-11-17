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
# First pass at game.time=84325104; published_bases 84324400..84325000,
# reconstructed 84324401..84325100 (700). inserted=13204, already_in_db=10785,
# ts_realigned_first_pass=0 on first-interval tick_s=4.68156 (printed 4.682).
# 31 of 35 official GETs 200; missing_chunks=4, in-window official 404
# W45N7@84324900, W47N8@84325000, W45N8@84325000, W47N7@84325000.
# W47N8@84324300 is now outside this window (26 live 84324375..84324400 / 74 empty 84324301..84324374).
# W47N8@84323200 remains outside this window (19 live 84323282..84323300 / 81 empty 84323201..84323281).
# W47N8@84322100 is now outside this window (93 live 84322101..84322193 / 7 empty 84322194..84322200).
# W45N7@84321600 is outside this window (2 live 84321601..84321602 / 98 empty 84321603..84321700).
# W47N8@84321300 is outside this window (39 live 84321362..84321400 / 61 empty 84321301..84321361).
# W47N8@84319900 is outside this window (0 live / 100 empty 84319901..84320000).
# W47N8@84319000 is outside this window (48 live 84319001..84319048, 52 empty 84319049..84319100).
# W46N8@84318500 is outside this window (32 live 84318569..84318600, 68 empty 84318501..84318568).
# W45N8@84318000 is outside this window (0 live, 100 empty 84318001..84318100).
# W47N7@84315100 is outside this window (0 live, 100 empty 84315101..84315200).
# W45N8@84314900 is outside this window (0 live, 100 empty 84314901..84315000).
# W45N7@84314500 is outside this window (0 live, 100 empty 84314501..84314600).
# W47N8@84314000 is outside this window (49 live 84314052..84314100, 51 empty 84314001..84314051).
# W46N8@84313200 remains outside this window (4 empty 84313201..84313204, 96 live 84313205..84313300).
# Leftovers from prior runs unchanged:
# W46N8@84310500 (11 live), W47N7@84309000, W45N8@84309100 (25 live), W45N8@84306500,
# W45N7@84305100, W47N8@84304700, W45N7@84303900, W45N8@84302200, W47N8@84300900 (74 live),
# W45N8@84300900 (7 live), W45N8@84300000 (26 live), W47N8@84298000,
# W47N8@84297200 (live-filled), W47N7@84296500, W45N8@84295900, W45N7@84295800.
IN_WINDOW = [
    ("W45N7", 84324900),  # NEW in-window official 404 this first pass; ticks 84324901..84325000
    ("W47N8", 84325000),  # NEW in-window official 404 this first pass; ticks 84325001..84325100
    ("W45N8", 84325000),  # NEW in-window official 404 this first pass; ticks 84325001..84325100
    ("W47N7", 84325000),  # NEW in-window official 404 this first pass; ticks 84325001..84325100
    ("W47N8", 84324300),  # leftover official 404 now outside window; 26 live / 74 empty
    ("W47N8", 84323200),  # leftover official 404 now outside window; 19 live / 81 empty
    ("W47N8", 84322100),  # leftover official 404 now outside window; 93 live / 7 empty
    ("W45N7", 84321600),  # leftover official 404 now outside window; 2 live / 98 empty
    ("W47N8", 84321300),  # leftover official 404 now outside window; 39 live / 61 empty
    ("W47N8", 84319900),  # leftover official 404 now outside window; 0 live / 100 empty
    ("W47N8", 84319000),  # leftover official 404 now outside window; 48 live / 52 empty
    ("W46N8", 84318500),  # leftover official 404 now outside window; 32 live / 68 empty
    ("W45N8", 84318000),  # leftover official 404 now outside window; 0 live / 100 empty
    ("W47N7", 84315100),  # leftover official 404 now outside window; 0 live / 100 empty
    ("W45N8", 84314900),  # leftover official 404 outside window; 0 live / 100 empty
    ("W45N7", 84314500),  # leftover official 404 outside window; 0 live / 100 empty
    ("W47N8", 84314000),  # leftover official 404 from 10:00 window; 49 live, 51 empty
    ("W46N8", 84313200),  # leftover official 404 from 09:00 window; 96 live, 4 empty
    ("W46N8", 84310500),  # leftover official 404, 11 live-filled
    ("W47N7", 84309000),
    ("W45N8", 84309100),
    ("W45N8", 84306500),
    ("W45N7", 84305100),
    ("W47N8", 84304700),
    ("W45N7", 84303900),
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
TICK_S = 4.68156  # overwritten from tick_s_realign.json if present
PASS = sys.argv[1] if len(sys.argv) > 1 else "confirm"
OUT = "/workspace/screeps/state/_halfhour_2026-11-18_0000/backfill_confirm_gets.json"
TICK_S_FILE = "/workspace/screeps/state/_halfhour_2026-11-18_0000/tick_s_realign.json"

def load_tick_s():
    global TICK_S
    try:
        j = json.load(open(TICK_S_FILE))
        if j.get("corrective_applied"):
            TICK_S = float(j["later_mean_w46"])
        elif j.get("still_over_45s_vs_later", 1) == 0 and j.get("later_mean_w46"):
            # First-pass realign may have rolled back; rows already sit on later-mean.
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
    try:
        with db.connect(autocommit=False) as c:
            nfix = hb.realign_ts(c, tmin, tmax, rooms, now_ts, gt, tick_s)
            c.commit()
    except Exception as e:
        print(f"realign after insert failed ({e!r}); leaving newly inserted ts as-is")
        nfix = 0
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
