#!/usr/bin/env python3
"""Batch-pull official Screeps room-history into TimescaleDB creep_ticks.

Official HTTP history (GET https://screeps.com/room-history/{shard}/{room}/{base}.json)
stores 100-tick chunks for every room. It does not use a websocket room slot, does
not call GET user/memory, and is public (no token). The in-progress chunk is not
published, so history lags by up to one chunk (~100 ticks, about 6-8 min).

This recovers per-tick positions / hits / energy for our creeps after the box
hibernates — the live listener cannot. It does not recover:
  - room_stats (STATS console line: cpu, bucket, Memory.stats)
  - creep_cpu / path_arrivals (segment 90 already holds only the last 300 ticks)
  - console events / alerts

Usage:
  .venv/bin/python tools/history_backfill.py                 # last ~20 min, colony rooms
  .venv/bin/python tools/history_backfill.py --dry-run
  .venv/bin/python tools/history_backfill.py --minutes 20 --rooms W46N8,W47N8
"""
from __future__ import annotations
import argparse, json, os, sys, time, gzip, urllib.request, urllib.error
from collections import defaultdict
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import db
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))
import api

SHARD = 'shard3'
ROOMS = ('W46N8', 'W47N8', 'W45N8', 'W45N7', 'W47N7')
CHUNK = 100
HISTORY = 'https://screeps.com/room-history/{shard}/{room}/{base}.json'
# Stay well under the global 120 req/min cap (this endpoint is not user/memory).
GAP_S = 0.6
UID_FILE = os.path.join(api.ROOT, 'metrics', 'live.json')
role_of = lambda n: ''.join(ch for ch in (n or '') if ch.isalpha()) or None


def uid():
    try:
        u = json.load(open(UID_FILE)).get('uid')
        if u:
            return u
    except Exception:
        pass
    return api.req('auth/me')['_id']


def history_get(room, base):
    """Return parsed chunk or None if 404 (unpublished / too old). Retry once on 429."""
    url = HISTORY.format(shard=SHARD, room=room, base=base)
    req = urllib.request.Request(url, headers={'User-Agent': 'screeps-ops-history-backfill'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read()
            if r.headers.get('Content-Encoding') == 'gzip' or (raw[:2] == b'\x1f\x8b'):
                try:
                    raw = gzip.decompress(raw)
                except Exception:
                    pass
            return json.loads(raw)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code == 429 and attempt < 2:
                time.sleep(5 * (attempt + 1))
                continue
            raise
    return None


def apply_update(state, upd):
    if not isinstance(upd, dict):
        return
    for oid, o in upd.items():
        if o is None:
            state.pop(oid, None)
        elif not isinstance(o, dict):
            continue
        elif oid in state:
            state[oid].update(o)
        else:
            state[oid] = dict(o)


def merge_chunk(j, state):
    """Apply first-tick full objects + later deltas; yield (listener_tick, objects_by_id).

    Official history tick T is the room *after* that tick's intents (end of T).
    The websocket listener records the same snapshot under gameTime T+1
    (measured 2026-11-10 on W46N8 84177954-84177990: hist[T] == creep_ticks[T+1]
    at 100%). Yield T+1 so backfilled rows join with creep_cpu / live trails.

    A chunk's opening tick is sometimes JSON null (seen on W47N8@84178000). Treat
    that as "no changes" and keep the previous chunk's ending state; resetting
    would drop that listener tick.
    """
    ticks = {}
    for k, v in (j.get('ticks') or {}).items():
        try:
            ticks[int(k)] = v
        except (TypeError, ValueError):
            continue
    for t in sorted(ticks):
        upd = ticks[t]
        if upd is not None:
            apply_update(state, upd)
        yield t + 1, state


def creep_rows(tick, room, objects, our_uid, ts, cm):
    rows = []
    for o in objects.values():
        if o.get('type') != 'creep' or o.get('user') != our_uid:
            continue
        name = o.get('name')
        if not name or o.get('x') is None or o.get('y') is None:
            continue
        e = (o.get('store') or {}).get('energy') or 0
        spawning = o.get('spawning') not in (None, False, 0)
        rows.append((ts, tick, room, name, role_of(name), int(o['x']), int(o['y']),
                     o.get('hits'), e, 'spawning' if spawning else ('loaded' if e else 'empty'), cm))
    return rows


def tick_seconds(chunks):
    """Seconds per tick from two *different* chunk bases (same-base rooms are not a tick interval)."""
    by_base = {}
    for c in chunks:
        if c.get('timestamp') and c.get('base') is not None:
            by_base.setdefault(int(c['base']), []).append(c['timestamp'])
    bases = sorted(by_base)
    if len(bases) >= 2:
        t0, t1 = min(by_base[bases[0]]), min(by_base[bases[1]])
        if t1 > t0:
            return (t1 - t0) / 1000.0 / (bases[1] - bases[0])
    return 3.9


def already(c, t0, t1, rooms):
    return set(c.execute('SELECT creep, tick FROM creep_ticks WHERE tick BETWEEN %s AND %s AND room = ANY(%s)',
                         (t0, t1, list(rooms))).fetchall())


def tick_time(now_ts, gt, tick, tick_s):
    """Wall time of a tick, anchored to live game.time so rows line up with the listener."""
    return now_ts - timedelta(seconds=(gt - tick) * tick_s)


def realign_ts(c, tmin, tmax, rooms, now_ts, gt, tick_s):
    """Move history-derived ts (chunk timestamp is not tick-0 wall time, off by ~8 min)
    onto the live anchor, but leave listener rows whose ts is already close."""
    cur = c.execute(
        """UPDATE creep_ticks
              SET ts = %(now)s + (tick - %(gt)s) * interval '1 second' * %(tick_s)s
            WHERE tick BETWEEN %(t0)s AND %(t1)s AND room = ANY(%(rooms)s)
              AND abs(extract(epoch from (ts - (%(now)s + (tick - %(gt)s) * interval '1 second' * %(tick_s)s)))) > 45""",
        {'now': now_ts, 'gt': gt, 'tick_s': tick_s, 't0': tmin, 't1': tmax, 'rooms': list(rooms)})
    return cur.rowcount


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--minutes', type=float, default=20, help='how far back to pull (published history only)')
    p.add_argument('--rooms', default=','.join(ROOMS))
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--compare', action='store_true', help='print overlap vs existing creep_ticks (always on with --dry-run)')
    args = p.parse_args()
    rooms = tuple(r.strip() for r in args.rooms.split(',') if r.strip())
    our = uid()
    now_ts = datetime.now(timezone.utc)
    gt = api.req(f'game/time?shard={SHARD}')['time']
    # Latest complete chunk starts 100 ticks below floor(now/100); the current base is still being written.
    latest = (gt // CHUNK) * CHUNK - CHUNK
    n_chunks = max(1, int(args.minutes * 60 / 4.0 / CHUNK) + 1)
    bases = [latest - i * CHUNK for i in range(n_chunks)][::-1]
    print(f'game.time={gt} published_bases={bases[0]}..{bases[-1]} rooms={",".join(rooms)} dry={args.dry_run}')

    fetched = []  # (room, chunk_json)
    missing = []
    for base in bases:
        for room in rooms:
            j = history_get(room, base)
            time.sleep(GAP_S)
            if not j:
                missing.append((room, base))
                print(f'  404 {room}@{base}')
                continue
            fetched.append((room, j))
            n = len(j.get('ticks') or {})
            print(f'  ok  {room}@{j.get("base")} ticks={n} ts={j.get("timestamp")}')

    if not fetched:
        print('no chunks fetched'); return 1

    tick_s = tick_seconds([j for _, j in fetched])
    print(f'tick_s={tick_s:.3f}')
    cm = None
    if not args.dry_run:
        with db.connect() as c:
            cm = db.current_commit(c)

    # Reconstruct room-by-room so a null opening tick can keep the previous chunk's state.
    grouped = defaultdict(list)
    for room, j in fetched:
        grouped[room].append(j)
    by_room = {r: {} for r in rooms}
    tmin = tmax = None
    for room in rooms:
        state = {}
        for j in sorted(grouped[room], key=lambda x: int(x.get('base') or 0)):
            for tick, objs in merge_chunk(j, state):
                ts = tick_time(now_ts, gt, tick, tick_s)
                rows = creep_rows(tick, room, objs, our, ts, cm)
                by_room[room].setdefault(tick, []).extend(rows)
                tmin = tick if tmin is None else min(tmin, tick)
                tmax = tick if tmax is None else max(tmax, tick)

    all_rows = [row for ticks in by_room.values() for rows in ticks.values() for row in rows]
    print(f'reconstructed ticks={tmin}..{tmax} ({(tmax - tmin + 1) if tmin is not None else 0}) '
          f'creep_rows={len(all_rows)} missing_chunks={len(missing)}')

    exist = set()
    with db.connect() as c:
        exist = already(c, tmin, tmax, rooms)
    new_rows = [r for r in all_rows if (r[3], r[1]) not in exist]
    skip = len(all_rows) - len(new_rows)
    print(f'already_in_db={skip} would_insert={len(new_rows)}')

    differ = 0
    if args.dry_run or args.compare:
        with db.connect() as c:
            cur = c.execute(
                'SELECT tick, room, creep, x, y, hits, store FROM creep_ticks '
                'WHERE tick BETWEEN %s AND %s AND room = ANY(%s)',
                (tmin, tmax, list(rooms)))
            dbmap = {(r[2], r[0], r[1]): r for r in cur.fetchall()}
        match = 0
        samples = []
        for r in all_rows:
            key = (r[3], r[1], r[2])  # creep, tick, room
            d = dbmap.get(key)
            if not d:
                continue
            ok = (d[3], d[4], d[5], d[6]) == (r[5], r[6], r[7], r[8])
            if ok:
                match += 1
            else:
                differ += 1
                if len(samples) < 8:
                    samples.append((key, ('db', d[3], d[4], d[5], d[6]), ('hist', r[5], r[6], r[7], r[8])))
        print(f'overlap compared={match + differ} match={match} differ={differ}')
        for s in samples:
            print('  DIFF', s)

    per = []
    for room in rooms:
        ticks = sorted(by_room[room])
        nnew = sum(1 for t, rows in by_room[room].items() for r in rows if (r[3], r[1]) not in exist)
        per.append(f'{room}:{len(ticks)}t/{nnew}new')
    print('per_room', ' '.join(per))

    if args.dry_run:
        print('dry-run, not writing')
        return 0 if differ == 0 else 2

    if new_rows:
        sql = ('INSERT INTO creep_ticks (ts,tick,room,creep,role,x,y,hits,store,state,commit) '
               'SELECT %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s '
               'WHERE NOT EXISTS (SELECT 1 FROM creep_ticks c WHERE c.creep=%s AND c.tick=%s)')
        packed = [r + (r[3], r[1]) for r in new_rows]
        with db.connect(autocommit=False) as c:
            with c.cursor() as cur:
                cur.executemany(sql, packed)
            c.commit()
        print(f'inserted={len(new_rows)}')
    else:
        print('nothing to insert')

    with db.connect(autocommit=False) as c:
        nfix = realign_ts(c, tmin, tmax, rooms, now_ts, gt, tick_s)
        c.commit()
        n = c.execute(
            'SELECT room, min(tick), max(tick), count(*), count(DISTINCT tick) '
            'FROM creep_ticks WHERE tick BETWEEN %s AND %s AND room = ANY(%s) '
            'GROUP BY room ORDER BY 1', (tmin, tmax, list(rooms))).fetchall()
    print(f'ts_realigned={nfix}')
    print('db_after')
    for row in n:
        print(' ', row[0], f'ticks={row[1]}..{row[2]} rows={row[3]} distinct={row[4]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
