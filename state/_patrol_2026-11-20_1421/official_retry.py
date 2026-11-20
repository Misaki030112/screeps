#!/usr/bin/env python3
"""Retry in-window official 404 and leftover official 404s; insert if a later GET returns 200."""
from __future__ import annotations
import json, sys, time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api

ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
IN_WINDOW = [("W45N7", 84373700), ("W47N8", 84373800)]
LEFTOVER = [
    ("W45N7", 84373300),
    ("W47N7", 84373200),
    ("W46N8", 84371600),
    ("W45N8", 84368100),
    ("W47N8", 84366200),
    ("W47N7", 84366500),
    ("W45N7", 84365200),
    ("W47N8", 84363900),
    ("W46N8", 84362700),
    ("W47N8", 84361700),
    ("W46N8", 84360600),
    ("W45N7", 84360200),
    ("W47N8", 84359900),
    ("W47N8", 84359500),
    ("W45N7", 84358500),
    ("W47N8", 84358700),
    ("W46N8", 84354300),
    ("W47N7", 84354300),
    ("W47N8", 84352400),
]
TICK_S = 4.188
OUT = "/workspace/screeps/state/_patrol_2026-11-20_1421/official_retries.json"
HK = ZoneInfo("Asia/Hong_Kong")


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
    j = hb.history_get(room, base)
    time.sleep(hb.GAP_S)
    rec = {"room": room, "base": base, "status": 404 if not j else 200, "ticks": 0}
    if not j:
        rec["bytes"] = 0
        return rec, 0, 0
    rec["ticks"] = len(j.get("ticks") or {})
    rec["ts"] = j.get("timestamp")
    state, seeded = fetch_seed(room, base)
    rec["seeded"] = seeded
    rows = []
    tmin = tmax = None
    for tick, objs in hb.merge_chunk(j, state):
        ts = hb.tick_time(now_ts, gt, tick, tick_s)
        rows.extend(hb.creep_rows(tick, room, objs, our, ts, cm))
        tmin = tick if tmin is None else min(tmin, tick)
        tmax = tick if tmax is None else max(tmax, tick)
    inserted, nfix = insert_rows(rows, now_ts, gt, tick_s, tmin, tmax, [room])
    rec["inserted"] = inserted
    rec["ts_realigned"] = nfix
    rec["tmin"] = tmin
    rec["tmax"] = tmax
    rec["nrows"] = len(rows)
    return rec, inserted, nfix


def main():
    kind = sys.argv[1] if len(sys.argv) > 1 else "all"
    if kind == "in_window":
        targets = list(IN_WINDOW)
    elif kind == "leftover":
        targets = list(LEFTOVER)
    else:
        targets = list(IN_WINDOW) + list(LEFTOVER)
    our = hb.uid()
    now_ts = datetime.now(timezone.utc)
    gt = None
    for attempt in range(3):
        try:
            gt = api.req(f"game/time?shard={hb.SHARD}")["time"]
            break
        except Exception as e:
            print(f"game/time attempt {attempt+1} failed: {e!r}", flush=True)
            time.sleep(3 * (attempt + 1))
    if gt is None:
        import json as _j
        from pathlib import Path
        live = _j.loads(Path("/workspace/screeps/metrics/live.json").read_text())
        st = live.get("stats") if isinstance(live.get("stats"), dict) else {}
        gt = live.get("gameTime") or st.get("t")
        print(f"fell back to live game.time={gt}", flush=True)
    with db.connect() as c:
        cm = db.current_commit(c)
    hk = datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
    print(f"{kind} GET start {hk} game.time={gt} tick_s={TICK_S} targets={len(targets)}", flush=True)
    results = []
    recovered, still_404 = [], []
    inserted = ts_realigned = 0
    for room, base in targets:
        with db.connect() as c:
            d, mn, mx, n = db_range(c, room, base)
        print(f"  pre  {room}@{base} distinct={d} rows={n} range={mn}..{mx}", flush=True)
        rec, ins, nfix = retry_one(room, base, our, now_ts, gt, TICK_S, cm)
        rec["kind"] = "in_window" if (room, base) in IN_WINDOW else "leftover"
        rec["pre_distinct"] = d
        rec["pre_rows"] = n
        rec["at"] = datetime.now(HK).strftime("%H:%M:%S")
        rec["game_time"] = gt
        results.append(rec)
        inserted += ins
        ts_realigned += nfix
        tag = f"{room}@{base}"
        if rec["status"] == 200:
            recovered.append(tag)
            print(f"  recovered {tag} ticks={rec.get('ticks')} inserted={ins} ts_realigned={nfix}", flush=True)
        else:
            still_404.append(tag)
            print(f"  still_404 {tag} at {rec['at']} game.time={gt}", flush=True)
        with db.connect() as c:
            d2, mn2, mx2, n2 = db_range(c, room, base)
        rec["post_distinct"] = d2
        rec["post_rows"] = n2
        rec["post_range"] = [mn2, mx2]
    print(f"recovered={recovered} still_404={still_404} inserted={inserted} ts_realigned={ts_realigned}", flush=True)
    try:
        prev = json.loads(open(OUT).read())
        if not isinstance(prev, list):
            prev = [prev]
    except Exception:
        prev = []
    prev.extend(results)
    open(OUT, "w").write(json.dumps(prev, indent=2, default=str) + "\n")
    print("wrote", OUT, "n", len(prev), flush=True)
    print("finished", flush=True)

if __name__ == "__main__":
    main()
