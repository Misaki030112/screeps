#!/usr/bin/env python3
"""Retry just-published W47N7@84333900 if it was unpublished-tail lag."""
from __future__ import annotations
import sys, time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api

ROOM, BASE = "W47N7", 84333900
TICK_S = 4.66396
ROOMS = (ROOM,)

def main():
    our = hb.uid()
    now_ts = datetime.now(timezone.utc)
    hk = datetime.now(ZoneInfo("Asia/Hong_Kong")).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
    gt = api.req(f"game/time?shard={hb.SHARD}")["time"]
    print(f"retry {ROOM}@{BASE} start {hk} game.time={gt}")
    with db.connect() as c:
        cm = db.current_commit(c)
    prev = hb.history_get(ROOM, BASE - 100)
    time.sleep(hb.GAP_S)
    j = hb.history_get(ROOM, BASE)
    time.sleep(hb.GAP_S)
    if not j:
        print(f"  still_404 {ROOM}@{BASE} at {hk} game.time={gt}")
        return 1
    print(f"  ok  {ROOM}@{j.get('base')} ticks={len(j.get('ticks') or {})} ts={j.get('timestamp')}")
    fetched = []
    if prev:
        fetched.append((ROOM, prev))
    fetched.append((ROOM, j))
    by_room = {ROOM: {}}
    tmin = tmax = None
    state = {}
    for room, chunk in fetched:
        for tick, objs in hb.merge_chunk(chunk, state):
            if not (BASE < tick <= BASE + 100):
                continue
            ts = hb.tick_time(now_ts, gt, tick, TICK_S)
            rows = hb.creep_rows(tick, room, objs, our, ts, cm)
            by_room[ROOM].setdefault(tick, []).extend(rows)
            tmin = tick if tmin is None else min(tmin, tick)
            tmax = tick if tmax is None else max(tmax, tick)
    all_rows = [row for rows in by_room[ROOM].values() for row in rows]
    print(f"reconstructed ticks={tmin}..{tmax} creep_rows={len(all_rows)}")
    with db.connect() as c:
        exist = hb.already(c, tmin, tmax, ROOMS)
    new_rows = [r for r in all_rows if (r[3], r[1]) not in exist]
    print(f"already_in_db={len(all_rows)-len(new_rows)} would_insert={len(new_rows)}")
    if new_rows:
        sql = ('INSERT INTO creep_ticks (ts,tick,room,creep,role,x,y,hits,store,state,commit) '
               'SELECT %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s '
               'WHERE NOT EXISTS (SELECT 1 FROM creep_ticks c WHERE c.creep=%s AND c.tick=%s)')
        packed = [r + (r[3], r[1]) for r in new_rows]
        with db.connect(autocommit=False) as c:
            with c.cursor() as cur:
                cur.executemany(sql, packed)
            nfix = hb.realign_ts(c, tmin, tmax, ROOMS, now_ts, gt, TICK_S)
            c.commit()
        print(f"inserted={len(new_rows)} ts_realigned={nfix}")
    else:
        print("nothing to insert")
    with db.connect() as c:
        row = c.execute(
            "SELECT min(tick), max(tick), count(*), count(DISTINCT tick) "
            "FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (ROOM, BASE+1, BASE+100),
        ).fetchone()
        print(f"db_after {ROOM}@{BASE} {row[0]}..{row[1]} rows={row[2]} distinct={row[3]}/100")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
