#!/usr/bin/env python3
"""Retry in-window and leftover official-history 404s."""
from __future__ import annotations
import json, sys, time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api

ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84310001, 84310700
TICK_S = 4.66027  # first-interval; tick_s_check may correct after this retry
IN_WINDOW = [
    ("W46N8", 84310500),  # first-pass 404; other 4 rooms 200
]
LEFTOVERS = [
    ("W47N7", 84309000),  # hole 84309001..84309100; still 404 after 05:00 confirm/retry2
    ("W45N8", 84309100),  # 25 live-filled 84309174..84309198; 75 empty; still 404
    ("W45N8", 84306500),
    ("W45N7", 84305100),
    ("W47N8", 84304700),
    ("W45N7", 84303900),
    ("W45N8", 84302200),
    ("W47N8", 84300900),
    ("W45N8", 84300900),
    ("W45N8", 84300000),
    ("W47N8", 84298000),
    ("W47N8", 84297200),  # already live-filled 100 distinct
    ("W47N7", 84296500),
    ("W45N8", 84295900),
    ("W45N7", 84295800),
    ("W46N8", 84292000),
]
CHUNKS = IN_WINDOW + LEFTOVERS

def db_range(c, room, base):
    t0, t1 = base + 1, base + 100
    row = c.execute(
        "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
        (room, t0, t1),
    ).fetchone()
    return row[0] or 0, row[1], row[2], row[3] or 0

def holes(ticks, t0, t1):
    s = set(ticks)
    missing, start = [], None
    for t in range(t0, t1+1):
        if t not in s:
            if start is None: start = t
        elif start is not None:
            missing.append((start, t-1, t-start)); start = None
    if start is not None:
        missing.append((start, t1, t1-start+1))
    return missing

def main():
    now_hk = datetime.now(ZoneInfo("Asia/Hong_Kong")).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
    gt = api.req("game/time?shard=shard3")["time"]
    now_ts = datetime.now(timezone.utc)
    our = hb.uid()
    with db.connect() as _c:
        cm = db.current_commit(_c)
    print(f"retry start {now_hk} game.time={gt} tick_s={TICK_S}")
    recovered, still = [], []
    inserted_total, nfix_total = 0, 0
    for room, base in CHUNKS:
        with db.connect() as c:
            d, mn, mx, n = db_range(c, room, base)
        print(f"  pre  {room}@{base} distinct={d} rows={n} range={mn}..{mx}", flush=True)
        j = hb.history_get(room, base)
        time.sleep(hb.GAP_S)
        if not j:
            print(f"  still_404 {room}@{base}", flush=True)
            still.append(f"{room}@{base}")
            continue
        prev = hb.history_get(room, base - 100)
        time.sleep(hb.GAP_S)
        state = {}
        if prev:
            for _tick, objs in hb.merge_chunk(prev, state):
                pass
        rows = []
        tmin = tmax = None
        for tick, objs in hb.merge_chunk(j, state):
            ts = hb.tick_time(now_ts, gt, tick, TICK_S)
            rows.extend(hb.creep_rows(tick, room, objs, our, ts, cm))
            tmin = tick if tmin is None else min(tmin, tick)
            tmax = tick if tmax is None else max(tmax, tick)
        with db.connect() as c:
            exist = hb.already(c, tmin, tmax, (room,))
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
            nfix = hb.realign_ts(c, tmin, tmax, (room,), now_ts, gt, TICK_S)
            c.commit()
        inserted_total += len(new_rows)
        nfix_total += nfix
        recovered.append(f"{room}@{base}")
        print(f"  recovered {room}@{base} hist_ticks={len(j.get('ticks') or {})} inserted={len(new_rows)} nfix={nfix}", flush=True)
    print(f"recovered={recovered} still_404={still} inserted={inserted_total} ts_realigned={nfix_total}")
    print(f"--- coverage {TMIN}..{TMAX} ---")
    with db.connect() as c:
        for room in ROOMS:
            rows = c.execute("SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s ORDER BY 1",
                             (room, TMIN, TMAX)).fetchall()
            ticks = [r[0] for r in rows]
            n = c.execute("SELECT count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
                          (room, TMIN, TMAX)).fetchone()[0]
            rng = (min(ticks), max(ticks)) if ticks else (None, None)
            miss = holes(ticks, TMIN, TMAX)
            print(f"{room} distinct {len(ticks)} range {rng[0]} {rng[1]} rows {n} holes {miss[:8]}{'...' if len(miss)>8 else ''}")
    print("done")

if __name__ == "__main__":
    main()
