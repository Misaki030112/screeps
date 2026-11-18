#!/usr/bin/env python3
"""Fetch just-published official history base 84345300 once game.time is safely past 84345400."""
from __future__ import annotations
import sys, time
from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api

ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
JUST_BASE = 84345300
RETRY_404 = [("W45N8", 84344700)]  # first-pass official 404; confirm/retry2 will note times; neighbors @84344600/@84344800 both 200
TICK_S = 4.78116  # first-interval (printed 4.781); later-mean-robust 4.75167 already inside 45s gate, no corrective; prev in-use 4.76498 also over45=0

LIVE = "/workspace/screeps/metrics/live.json"
WAIT_UNTIL_GT = JUST_BASE + 140  # last window first try at +102 was still 404; recovered at +141

def wait_for_publish(target=WAIT_UNTIL_GT, timeout_s=600, poll_s=15):
    """Wait on listener live.json (no extra game/time API) until the next base can be public."""
    import json, time, os
    t0 = time.time()
    last = None
    while time.time() - t0 < timeout_s:
        try:
            d = json.load(open(LIVE))
            st = d.get("stats") if isinstance(d.get("stats"), dict) else {}
            # Prefer stats.t: live.json gameTime can lag the already-published threshold.
            gt = st.get("t") or d.get("gameTime")
            last = gt
            if gt and int(gt) >= target:
                print(f"live game.time={gt} >= {target} after {time.time()-t0:.0f}s; proceeding", flush=True)
                return int(gt)
        except Exception as e:
            print(f"  live.json read failed: {e!r}", flush=True)
        time.sleep(poll_s)
    print(f"wait timeout after {timeout_s}s last_live_gt={last}; will try anyway", flush=True)
    return last

def history_get_retry(room, base, attempts=3):

    last = None
    for i in range(attempts):
        try:
            return hb.history_get(room, base)
        except Exception as e:
            last = e
            print(f"  transient {room}@{base} attempt {i+1}: {e!r}", flush=True)
            time.sleep(5 * (i + 1))
    raise last

def insert_all(by_room, now_ts, gt, tick_s, rooms):
    all_rows = [row for ticks in by_room.values() for rows in ticks.values() for row in rows]
    if not all_rows:
        print("reconstructed ticks=none creep_rows=0", flush=True)
        return 0, 0, None, None
    tmin = min(t for ticks in by_room.values() for t in ticks)
    tmax = max(t for ticks in by_room.values() for t in ticks)
    print(f"reconstructed ticks={tmin}..{tmax} creep_rows={len(all_rows)}", flush=True)
    with db.connect() as c:
        exist = hb.already(c, tmin, tmax, rooms)
    new_rows = [r for r in all_rows if (r[3], r[1]) not in exist]
    skip = len(all_rows) - len(new_rows)
    print(f"already_in_db={skip} would_insert={len(new_rows)}", flush=True)
    per = []
    for room in rooms:
        ticks = sorted(by_room.get(room) or {})
        nnew = sum(1 for t, rows in (by_room.get(room) or {}).items() for r in rows if (r[3], r[1]) not in exist)
        per.append(f"{room}:{len(ticks)}t/{nnew}new")
    print("per_room", " ".join(per), flush=True)
    if new_rows:
        sql = ('INSERT INTO creep_ticks (ts,tick,room,creep,role,x,y,hits,store,state,commit) '
               'SELECT %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s '
               'WHERE NOT EXISTS (SELECT 1 FROM creep_ticks c WHERE c.creep=%s AND c.tick=%s)')
        packed = [r + (r[3], r[1]) for r in new_rows]
        with db.connect(autocommit=False) as c:
            with c.cursor() as cur:
                cur.executemany(sql, packed)
            c.commit()
        print(f"inserted={len(new_rows)}", flush=True)
    else:
        print("nothing to insert", flush=True)
    nfix = 0
    with db.connect(autocommit=False) as c:
        nfix = hb.realign_ts(c, tmin, tmax, rooms, now_ts, gt, tick_s)
        c.commit()
    print(f"ts_realigned={nfix}", flush=True)
    return len(new_rows), nfix, tmin, tmax

def reconstruct(fetched, rooms, our, now_ts, gt, tick_s, cm):
    grouped = defaultdict(list)
    for room, j in fetched:
        grouped[room].append(j)
    by_room = {r: {} for r in rooms}
    for room in rooms:
        state = {}
        for j in sorted(grouped[room], key=lambda x: int(x.get("base") or 0)):
            for tick, objs in hb.merge_chunk(j, state):
                ts = hb.tick_time(now_ts, gt, tick, tick_s)
                rows = hb.creep_rows(tick, room, objs, our, ts, cm)
                by_room[room].setdefault(tick, []).extend(rows)
    return by_room

def db_span(c, room, lo, hi):
    return c.execute(
        "SELECT min(tick), max(tick), count(*), count(DISTINCT tick) "
        "FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
        (room, lo, hi),
    ).fetchone()

    return missing, inserted

def main():
    our = hb.uid()
    attempt = 0
    first_missing = None
    while True:
        attempt += 1
        target = WAIT_UNTIL_GT if attempt == 1 else JUST_BASE + 160
        wait_for_publish(target=target, timeout_s=600, poll_s=15)
        now_ts = datetime.now(timezone.utc)
        hk = datetime.now(ZoneInfo("Asia/Hong_Kong")).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
        gt = api.req(f"game/time?shard={hb.SHARD}")["time"]
        print(f"just_published start attempt={attempt} {hk} game.time={gt} tick_s={TICK_S}", flush=True)
        with db.connect() as c:
            cm = db.current_commit(c)

        missing = []
        hole_fetched = []
        for room, base in RETRY_404:
            j = history_get_retry(room, base)
            time.sleep(hb.GAP_S)
            if not j:
                print(f"  404 {room}@{base}", flush=True)
                missing.append((room, base))
                continue
            print(f"  ok  {room}@{j.get('base')} ticks={len(j.get('ticks') or {})} ts={j.get('timestamp')}", flush=True)
            prev = history_get_retry(room, base - 100)
            time.sleep(hb.GAP_S)
            fetched = []
            if prev:
                fetched.append((room, prev))
            fetched.append((room, j))
            hole_fetched.extend(fetched)

        just_fetched = []
        for room in ROOMS:
            prev = history_get_retry(room, JUST_BASE - 100)
            time.sleep(hb.GAP_S)
            j = history_get_retry(room, JUST_BASE)
            time.sleep(hb.GAP_S)
            if not j:
                print(f"  404 {room}@{JUST_BASE}", flush=True)
                missing.append((room, JUST_BASE))
                continue
            print(f"  ok  {room}@{j.get('base')} ticks={len(j.get('ticks') or {})} ts={j.get('timestamp')}", flush=True)
            if prev:
                just_fetched.append((room, prev))
            just_fetched.append((room, j))

        just_missing = [m for m in missing if m[1] == JUST_BASE]
        if just_fetched:
            rooms_just = tuple(r for r in ROOMS if any(rr == r for rr, _ in just_fetched))
            by_room = reconstruct(just_fetched, rooms_just, our, now_ts, gt, TICK_S, cm)
            for room in list(by_room):
                by_room[room] = {t: rows for t, rows in by_room[room].items() if JUST_BASE < t <= JUST_BASE + 100}
            print(f"missing={missing}", flush=True)
            inserted, nfix, tmin, tmax = insert_all(by_room, now_ts, gt, TICK_S, rooms_just)
        else:
            print(f"missing={missing}", flush=True)
            print("just-published all official 404 this attempt", flush=True)
            inserted = 0
            if attempt == 1:
                first_missing = missing
                print("will wait a bit more and retry once", flush=True)
                continue

        if hole_fetched:
            hole_rooms = tuple(sorted({r for r, _ in hole_fetched}))
            hole_by = reconstruct(hole_fetched, hole_rooms, our, now_ts, gt, TICK_S, cm)
            for room, base in RETRY_404:
                if room in hole_by:
                    hole_by[room] = {t: rows for t, rows in hole_by[room].items() if base < t <= base + 100}
            print("hole recovered rows follow", flush=True)
            insert_all(hole_by, now_ts, gt, TICK_S, hole_rooms)

        print("db_after_just_published", flush=True)
        with db.connect() as c:
            print("  leftover in-window official 404s (retried again here):", flush=True)
            for room, base in RETRY_404:
                mn, mx, n, d = db_span(c, room, base + 1, base + 100)
                print(f"    {room}@{base} {base+1}..{base+100}: {mn}..{mx} rows={n} distinct={d}/100", flush=True)
            print(f"  just-published {JUST_BASE} {JUST_BASE+1}..{JUST_BASE+100}:", flush=True)
            for room in ROOMS:
                mn, mx, n, d = db_span(c, room, JUST_BASE + 1, JUST_BASE + 100)
                print(f"    {room} {mn}..{mx} rows={n} distinct={d}/100", flush=True)
            print("  this-window official published 84344601..84345300:", flush=True)
            for room in ROOMS:
                mn, mx, n, d = db_span(c, room, 84344601, 84345300)
                print(f"    {room} {mn}..{mx} rows={n} distinct={d}/700", flush=True)
        print("finished", flush=True)
        return

if __name__ == "__main__":
    main()
