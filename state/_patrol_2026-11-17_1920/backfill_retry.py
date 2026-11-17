#!/usr/bin/env python3
"""Retry official 404 W47N8@84321300 (and recent leftovers)."""
from __future__ import annotations
import sys, time
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api

HK = ZoneInfo("Asia/Hong_Kong")
TARGETS = [
    ("W47N8", 84321300),  # first-pass 404 this hour
    ("W47N8", 84319900),
    ("W47N8", 84319000),
    ("W46N8", 84318500),
    ("W45N8", 84318000),
]

def ingest_one(room, base, our, now_ts, gt, tick_s, cm, dry=False):
    j = hb.history_get(room, base)
    time.sleep(hb.GAP_S)
    if not j:
        return "404", 0, 0
    state = {}
    by_tick = {}
    for tick, objs in hb.merge_chunk(j, state):
        ts = hb.tick_time(now_ts, gt, tick, tick_s)
        rows = hb.creep_rows(tick, room, objs, our, ts, cm)
        by_tick.setdefault(tick, []).extend(rows)
    all_rows = [r for rows in by_tick.values() for r in rows]
    tmin = min(by_tick) if by_tick else None
    tmax = max(by_tick) if by_tick else None
    with db.connect() as c:
        exist = hb.already(c, tmin, tmax, (room,)) if tmin else set()
    new_rows = [r for r in all_rows if (r[3], r[1]) not in exist]
    inserted = 0
    if new_rows and not dry:
        sql = ('INSERT INTO creep_ticks (ts,tick,room,creep,role,x,y,hits,store,state,commit) '
               'SELECT %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s '
               'WHERE NOT EXISTS (SELECT 1 FROM creep_ticks c WHERE c.creep=%s AND c.tick=%s)')
        packed = [r + (r[3], r[1]) for r in new_rows]
        with db.connect(autocommit=False) as c:
            with c.cursor() as cur:
                cur.executemany(sql, packed)
            c.commit()
        inserted = len(new_rows)
    return "200", len(all_rows), inserted

def main():
    print("retry at", datetime.now(HK).isoformat(timespec="seconds"))
    our = hb.uid()
    now_ts = datetime.now(timezone.utc)
    gt = api.req(f"game/time?shard={hb.SHARD}")["time"]
    tick_s = 4.690  # first-pass this hour
    with db.connect() as c:
        cm = db.current_commit(c)
    print(f"game.time={gt} tick_s={tick_s} commit={cm}")
    for room, base in TARGETS:
        status, nrows, inserted = ingest_one(room, base, our, now_ts, gt, tick_s, cm)
        print(f"  {status} {room}@{base} rows={nrows} inserted={inserted}")
    # coverage after
    with db.connect() as c:
        n = c.execute("SELECT count(DISTINCT tick) FROM creep_ticks WHERE room='W47N8' AND tick BETWEEN 84321301 AND 84321400").fetchone()[0]
        print(f"W47N8@84321300 coverage now {n}/100")
        n2 = c.execute("SELECT count(DISTINCT tick) FROM creep_ticks WHERE room='W47N8' AND tick BETWEEN 84320801 AND 84321500").fetchone()[0]
        print(f"window 84320801..84321500 W47N8 distinct={n2}/700")

if __name__ == "__main__":
    main()
