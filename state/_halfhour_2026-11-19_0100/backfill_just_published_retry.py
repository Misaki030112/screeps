#!/usr/bin/env python3
"""Retry leftover just-published 404s and in-window official 404 W47N8@84343800."""
from __future__ import annotations
import sys, time
from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api

# Import helpers from the sibling just-published script
import importlib.util
p = "/workspace/screeps/state/_halfhour_2026-11-19_0100/backfill_just_published.py"
spec = importlib.util.spec_from_file_location("jp", p)
jp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jp)

JUST_BASE = 84344200
TARGETS = []  # filled after first just-published attempt if any rooms still 404
HOLES = [("W47N8", 84343800)]
TICK_S = 4.68990
WAIT_UNTIL_GT = JUST_BASE + 170

def main():
    jp.wait_for_publish(target=WAIT_UNTIL_GT, timeout_s=300, poll_s=15)
    our = hb.uid()
    now_ts = datetime.now(timezone.utc)
    hk = datetime.now(ZoneInfo("Asia/Hong_Kong")).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
    gt = api.req(f"game/time?shard={hb.SHARD}")["time"]
    print(f"just_published retry start {hk} game.time={gt} tick_s={TICK_S}", flush=True)
    with db.connect() as c:
        cm = db.current_commit(c)
    missing = []
    fetched = []
    hole_fetched = []
    for room, base in HOLES + TARGETS:
        j = jp.history_get_retry(room, base)
        time.sleep(hb.GAP_S)
        if not j:
            print(f"  404 {room}@{base}", flush=True)
            missing.append((room, base))
            continue
        print(f"  ok  {room}@{j.get('base')} ticks={len(j.get('ticks') or {})} ts={j.get('timestamp')}", flush=True)
        prev = jp.history_get_retry(room, base - 100)
        time.sleep(hb.GAP_S)
        chunk = []
        if prev:
            chunk.append((room, prev))
        chunk.append((room, j))
        if (room, base) in HOLES:
            hole_fetched.extend(chunk)
        else:
            fetched.extend(chunk)
    inserted = 0
    if fetched:
        rooms = tuple(sorted({r for r, _ in fetched}))
        by_room = jp.reconstruct(fetched, rooms, our, now_ts, gt, TICK_S, cm)
        for room in list(by_room):
            by_room[room] = {t: rows for t, rows in by_room[room].items() if JUST_BASE < t <= JUST_BASE + 100}
        n, nfix, tmin, tmax = jp.insert_all(by_room, now_ts, gt, TICK_S, rooms)
        inserted += n
        print(f"just W47N8@{JUST_BASE} inserted={n} ts_realigned={nfix}", flush=True)
    if hole_fetched:
        rooms = tuple(sorted({r for r, _ in hole_fetched}))
        by_room = jp.reconstruct(hole_fetched, rooms, our, now_ts, gt, TICK_S, cm)
        for room, base in HOLES:
            if room in by_room:
                by_room[room] = {t: rows for t, rows in by_room[room].items() if base < t <= base + 100}
        n, nfix, tmin, tmax = jp.insert_all(by_room, now_ts, gt, TICK_S, rooms)
        inserted += n
        print(f"hole inserted={n} ts_realigned={nfix}", flush=True)
    print(f"missing={missing} inserted_total={inserted}", flush=True)
    print("db_after_retry", flush=True)
    with db.connect() as c:
        for room, base in HOLES + TARGETS:
            mn, mx, n, d = jp.db_span(c, room, base + 1, base + 100)
            print(f"  {room}@{base} {base+1}..{base+100}: {mn}..{mx} rows={n} distinct={d}/100", flush=True)
    print("finished", flush=True)

if __name__ == "__main__":
    main()
