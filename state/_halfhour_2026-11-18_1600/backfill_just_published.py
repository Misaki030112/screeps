#!/usr/bin/env python3
"""Fetch just-published official history base 84337300 and retry leftover official 404s still outstanding."""
from __future__ import annotations
import sys, time
from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api

ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
JUST_BASE = 84337300
RETRY_404 = [
    ("W46N8", 84336400),
    ("W47N7", 84334700), ("W47N8", 84334600),
    ("W45N8", 84333500), ("W47N8", 84333300), ("W47N8", 84332600), ("W47N7", 84332600),
    ("W47N8", 84332700), ("W45N8", 84332200), ("W47N7", 84331000), ("W47N7", 84330300),
    ("W45N8", 84328100), ("W45N7", 84328300),
]
TICK_S = 4.69892  # later-mean-robust this run; corrective realign nfix=5066, still_over_45s_vs_later=0

def insert_all(by_room, now_ts, gt, tick_s, rooms):
    all_rows = [row for ticks in by_room.values() for rows in ticks.values() for row in rows]
    if not all_rows:
        print("reconstructed ticks=none creep_rows=0")
        return 0, 0, None, None
    tmin = min(t for ticks in by_room.values() for t in ticks)
    tmax = max(t for ticks in by_room.values() for t in ticks)
    print(f"reconstructed ticks={tmin}..{tmax} creep_rows={len(all_rows)}")
    with db.connect() as c:
        exist = hb.already(c, tmin, tmax, rooms)
    new_rows = [r for r in all_rows if (r[3], r[1]) not in exist]
    skip = len(all_rows) - len(new_rows)
    print(f"already_in_db={skip} would_insert={len(new_rows)}")
    per = []
    for room in rooms:
        ticks = sorted(by_room[room])
        nnew = sum(1 for t, rows in by_room[room].items() for r in rows if (r[3], r[1]) not in exist)
        per.append(f"{room}:{len(ticks)}t/{nnew}new")
    print("per_room", " ".join(per))
    if new_rows:
        sql = ('INSERT INTO creep_ticks (ts,tick,room,creep,role,x,y,hits,store,state,commit) '
               'SELECT %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s '
               'WHERE NOT EXISTS (SELECT 1 FROM creep_ticks c WHERE c.creep=%s AND c.tick=%s)')
        packed = [r + (r[3], r[1]) for r in new_rows]
        with db.connect(autocommit=False) as c:
            with c.cursor() as cur:
                cur.executemany(sql, packed)
            c.commit()
        print(f"inserted={len(new_rows)}")
    else:
        print("nothing to insert")
    nfix = 0
    with db.connect(autocommit=False) as c:
        nfix = hb.realign_ts(c, tmin, tmax, rooms, now_ts, gt, tick_s)
        c.commit()
    print(f"ts_realigned={nfix}")
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
    row = c.execute(
        "SELECT min(tick), max(tick), count(*), count(DISTINCT tick) "
        "FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
        (room, lo, hi),
    ).fetchone()
    return row

def main():
    our = hb.uid()
    now_ts = datetime.now(timezone.utc)
    hk = datetime.now(ZoneInfo("Asia/Hong_Kong")).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
    gt = api.req(f"game/time?shard={hb.SHARD}")["time"]
    print(f"just_published start {hk} game.time={gt} tick_s={TICK_S}")
    with db.connect() as c:
        cm = db.current_commit(c)

    missing = []
    hole_fetched = []
    for room, base in RETRY_404:
        j = hb.history_get(room, base)
        time.sleep(hb.GAP_S)
        if not j:
            print(f"  404 {room}@{base}")
            missing.append((room, base))
            continue
        print(f"  ok  {room}@{j.get('base')} ticks={len(j.get('ticks') or {})} ts={j.get('timestamp')}")
        prev = hb.history_get(room, base - 100)
        time.sleep(hb.GAP_S)
        fetched = []
        if prev:
            fetched.append((room, prev))
        fetched.append((room, j))
        hole_fetched.extend(fetched)

    just_fetched = []
    for room in ROOMS:
        prev = hb.history_get(room, JUST_BASE - 100)
        time.sleep(hb.GAP_S)
        j = hb.history_get(room, JUST_BASE)
        time.sleep(hb.GAP_S)
        if not j:
            print(f"  404 {room}@{JUST_BASE}")
            missing.append((room, JUST_BASE))
            continue
        print(f"  ok  {room}@{j.get('base')} ticks={len(j.get('ticks') or {})} ts={j.get('timestamp')}")
        if prev:
            just_fetched.append((room, prev))
        just_fetched.append((room, j))

    rooms_just = tuple(r for r in ROOMS if any(rr == r for rr, _ in just_fetched))
    by_room = reconstruct(just_fetched, rooms_just, our, now_ts, gt, TICK_S, cm)
    for room in list(by_room):
        by_room[room] = {t: rows for t, rows in by_room[room].items() if JUST_BASE < t <= JUST_BASE + 100}
    print(f"missing={missing}")
    inserted, nfix, tmin, tmax = insert_all(by_room, now_ts, gt, TICK_S, rooms_just)

    if hole_fetched:
        hole_rooms = tuple(sorted({r for r, _ in hole_fetched}))
        hole_by = reconstruct(hole_fetched, hole_rooms, our, now_ts, gt, TICK_S, cm)
        for room, base in RETRY_404:
            if room in hole_by:
                hole_by[room] = {t: rows for t, rows in hole_by[room].items() if base < t <= base + 100}
        print("hole recovered rows follow")
        insert_all(hole_by, now_ts, gt, TICK_S, hole_rooms)

    print("db_after_just_published")
    with db.connect() as c:
        holes = [
            ("leftover W46N8@84336400", "W46N8", 84336401, 84336500),
            ("leftover W47N7@84334700", "W47N7", 84334701, 84334800),
            ("leftover W47N8@84334600", "W47N8", 84334601, 84334700),
            ("leftover W45N8@84333500", "W45N8", 84333501, 84333600),
            ("leftover W47N8@84333300", "W47N8", 84333301, 84333400),
            ("leftover W47N8@84332600", "W47N8", 84332601, 84332700),
            ("leftover W47N7@84332600", "W47N7", 84332601, 84332700),
            ("leftover W47N8@84332700", "W47N8", 84332701, 84332800),
            ("leftover W45N8@84332200", "W45N8", 84332201, 84332300),
            ("leftover W47N7@84331000", "W47N7", 84331001, 84331100),
            ("leftover W47N7@84330300", "W47N7", 84330301, 84330400),
            ("leftover W45N8@84328100", "W45N8", 84328101, 84328200),
            ("leftover W45N7@84328300", "W45N7", 84328301, 84328400),
        ]
        for label, room, lo, hi in holes:
            mn, mx, n, d = db_span(c, room, lo, hi)
            print(f"  {label} {lo}..{hi}: {mn}..{mx} rows={n} distinct={d}/100")
        print(f"  just-published {JUST_BASE} {JUST_BASE+1}..{JUST_BASE+100}:")
        for room in ROOMS:
            mn, mx, n, d = db_span(c, room, JUST_BASE + 1, JUST_BASE + 100)
            print(f"    {room} {mn}..{mx} rows={n} distinct={d}/100")
        print("  this-window official published 84336601..84337300:")
        for room in ROOMS:
            mn, mx, n, d = db_span(c, room, 84336601, 84337300)
            print(f"    {room} {mn}..{mx} rows={n} distinct={d}/700")  # window 84336601..84337300
    print("finished")

if __name__ == "__main__":
    main()
