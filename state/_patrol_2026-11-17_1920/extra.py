#!/usr/bin/env python3
"""W47 40k/500t, upgrader handoff/spawn-pocket, leftover holes, tick_s, box pauses."""
from __future__ import annotations
import json, sys, os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
sys.path.insert(0, '/workspace/screeps/tools')
import db

HK = ZoneInfo('Asia/Hong_Kong')
OUT = Path('/workspace/screeps/state/_patrol_2026-11-17_1920/extra.txt')
LAST_TIP = 84320740
DEPLOY_TICK = 84321282
DEPLOY_SHA = 'c6d43491'
SEATS = {(12, 25), (14, 26), (14, 27), (12, 26), (13, 25), (13, 26), (13, 27), (12, 27), (14, 25)}
# spawn-pocket tiles of interest
POCKET = {(x, y) for x in range(30, 37) for y in range(28, 36)}
BYPASS_SOUTH = {(32, 32), (32, 33), (31, 32), (33, 32), (32, 31)}
NORTH_REPATH = {(32, 29), (32, 28), (33, 29), (31, 29), (33, 28)}
FILLER_POST = (34, 32)

def p(lines, *a):
    s = ' '.join(str(x) for x in a)
    lines.append(s)
    print(s)

def spans_missing(have, lo, hi):
    miss = sorted(set(range(lo, hi + 1)) - set(have))
    out = []
    span = None
    for t in miss:
        if span and t == span[1] + 1:
            span[1] = t
        else:
            if span:
                out.append((span[0], span[1], span[1] - span[0] + 1))
            span = [t, t]
    if span:
        out.append((span[0], span[1], span[1] - span[0] + 1))
    return out

def main():
    lines = []
    c = db.connect()
    tip = c.execute("""
        SELECT a.tick, a.ts FROM room_stats a
        JOIN room_stats b ON a.tick=b.tick AND b.room='W47N8'
        WHERE a.room='W46N8' ORDER BY a.tick DESC LIMIT 1
    """).fetchone()
    TIP, TIP_TS = tip
    p(lines, 'TIP', TIP, TIP_TS, 'LAST_TIP', LAST_TIP, 'DEPLOY', DEPLOY_TICK, DEPLOY_SHA)

    # --- 40k/500t ---
    p(lines, '=== W47 40k/500t ===')
    rows = c.execute("""
        SELECT tick, ts, storage FROM room_stats
        WHERE room='W47N8' AND tick>=%s AND tick<=%s ORDER BY tick
    """, (TIP - int(12 * 3600 / 4.4), TIP)).fetchall()
    best = 0
    cur_start = None
    prev = None
    mx = (0, None, 0)
    spans = []
    ge40 = 0
    for t, ts, s in rows:
        s = s or 0
        if s > mx[2]:
            mx = (t, ts, s)
        if s >= 40000:
            ge40 += 1
            if cur_start is None:
                cur_start = (prev[0] if prev else t, prev[1] if prev else ts, s)
            best = max(best, t - cur_start[0])
        else:
            if cur_start is not None:
                spans.append((cur_start[0], prev[0], prev[0] - cur_start[0], str(cur_start[1]), str(prev[1]), prev[2]))
            cur_start = None
        prev = (t, ts, s)
    if cur_start is not None and prev:
        spans.append((cur_start[0], prev[0], prev[0] - cur_start[0], str(cur_start[1]), str(prev[1]), prev[2]))
    last = rows[-1] if rows else None
    p(lines, f'12h n={len(rows)} max={mx} last={last} samples>=40k={ge40} best_span={best} n_spans={len(spans)}')
    for s in spans:
        p(lines, '  span', s)
    # this hour
    rows_h = [r for r in rows if r[0] >= LAST_TIP]
    if rows_h:
        mn = min(rows_h, key=lambda r: r[2] or 0)
        mxh = max(rows_h, key=lambda r: r[2] or 0)
        p(lines, f'since_last n={len(rows_h)} min={mn} max={mxh} last={rows_h[-1]}')

    # --- home storage this hour ---
    p(lines, '=== home storage since_last / 6h 20k ===')
    for room, floor, latch in (('W46N8', 15000, 20000),):
        rows = c.execute("""
            SELECT tick, ts, storage FROM room_stats
            WHERE room=%s AND tick>=%s AND tick<=%s ORDER BY tick
        """, (room, LAST_TIP, TIP)).fetchall()
        if rows:
            vals = [(r[0], r[1], r[2] or 0) for r in rows]
            under = sum(1 for v in vals if v[2] < floor)
            p(lines, room, 'since_last', 'n', len(vals), 'min', min(vals, key=lambda x: x[2]), 'max', max(vals, key=lambda x: x[2]),
              f'under{floor}={under}/{len(vals)}={100*under/len(vals):.1f}%', 'last', vals[-1])
        rows6 = c.execute("""
            SELECT tick, ts, storage FROM room_stats
            WHERE room=%s AND tick>=%s AND tick<=%s ORDER BY tick
        """, (room, TIP - int(6 * 3600 / 4.4), TIP)).fetchall()
        best = 0
        cur_start = None
        prev = None
        mx = (0, None, 0)
        for t, ts, s in rows6:
            s = s or 0
            if s > mx[2]:
                mx = (t, ts, s)
            if s >= latch:
                if cur_start is None:
                    cur_start = prev[0] if prev else t
                best = max(best, t - cur_start)
            else:
                cur_start = None
            prev = (t, s)
        p(lines, room, '6h max', mx, 'best>=20k span', best)

    # --- W47 upgrader trajectories ---
    p(lines, '=== W47 upgrader trajectories since LAST_TIP-200 ===')
    lo = LAST_TIP - 200
    rows = c.execute("""
        SELECT tick, ts, creep, x, y, store, hits
        FROM creep_ticks
        WHERE room='W47N8' AND tick>=%s AND role IN ('w8upgrader','upgrader')
           OR (room='W47N8' AND tick>=%s AND creep LIKE 'w8upgrader%%')
        ORDER BY creep, tick
    """, (lo, lo)).fetchall()
    # dedupe in case of or
    by = defaultdict(list)
    seen = set()
    for t, ts, name, x, y, store, hits in rows:
        key = (name, t)
        if key in seen:
            continue
        seen.add(key)
        e = None
        if store:
            if isinstance(store, str):
                try:
                    store = json.loads(store)
                except Exception:
                    store = {}
            if isinstance(store, dict):
                e = store.get('energy') or store.get('E')
        by[name].append((t, ts, x, y, e, hits))

    def first_seat(seq):
        for rec in seq:
            if (rec[2], rec[3]) in SEATS:
                return rec
        return None

    def last_seat(seq):
        last = None
        for rec in seq:
            if (rec[2], rec[3]) in SEATS:
                last = rec
        return last

    def path_flags(seq, t0=None, t1=None):
        tiles = []
        for rec in seq:
            if t0 is not None and rec[0] < t0:
                continue
            if t1 is not None and rec[0] > t1:
                continue
            tiles.append((rec[0], rec[2], rec[3]))
        hit_south = [t for t in tiles if (t[1], t[2]) in BYPASS_SOUTH]
        hit_north = [t for t in tiles if (t[1], t[2]) in NORTH_REPATH]
        hit_pocket = [t for t in tiles if (t[1], t[2]) in POCKET]
        hit_post = [t for t in tiles if (t[1], t[2]) == FILLER_POST]
        bounce = 0
        for i in range(1, len(tiles)):
            if (tiles[i][1], tiles[i][2]) == (tiles[i-1][1], tiles[i-1][2]):
                continue
            # oscillation: return to a tile within 3 steps
            for j in range(max(0, i-4), i):
                if (tiles[i][1], tiles[i][2]) == (tiles[j][1], tiles[j][2]) and (tiles[i][1], tiles[i][2]) in POCKET:
                    bounce += 1
                    break
        return {
            'n': len(tiles),
            'south_bypass': len(hit_south),
            'south_first': hit_south[0] if hit_south else None,
            'north_repath': len(hit_north),
            'north_first': hit_north[0] if hit_north else None,
            'pocket': len(hit_pocket),
            'filler_post_34_32': len(hit_post),
            'pocket_bounce_events': bounce,
        }

    for name in sorted(by, key=lambda n: by[n][0][0]):
        seq = by[name]
        fs = first_seat(seq)
        ls = last_seat(seq)
        spawn_t = int(''.join(ch for ch in name if ch.isdigit()) or 0)
        # walk: from first appearance (or leave spawn area) to first seat
        first = seq[0]
        last = seq[-1]
        walk = None
        if fs:
            walk = fs[0] - first[0]
        # last loaded / leave seat of previous? printed per creep
        p(lines, f'-- {name} spawn#={spawn_t} first={first[0]} {first[1]} ({first[2]},{first[3]}) e={first[4]} last={last[0]} {last[1]} ({last[2]},{last[3]}) e={last[4]} n={len(seq)}')
        p(lines, '   first_seat', fs, 'last_seat', ls, 'walk_from_first_to_seat', walk)
        # pre/post deploy path flags during approach
        t_end = fs[0] if fs else last[0]
        flags_all = path_flags(seq, first[0], t_end)
        flags_post = path_flags(seq, max(first[0], DEPLOY_TICK), t_end)
        p(lines, '   path_to_seat', flags_all, 'post_deploy_subset', flags_post)
        # compact approach path (until first seat or last)
        approach = []
        for rec in seq:
            approach.append(f"{rec[0]}:{rec[2]},{rec[3]}")
            if fs and rec[0] == fs[0]:
                break
        # downsample if long
        if len(approach) > 80:
            approach = approach[:20] + ['...'] + approach[-20:]
        p(lines, '   approach', ' '.join(approach))

    # identify handoff events: a seated upgrader disappears and a replacement arrives
    p(lines, '=== handoff events (seat occupancy) ===')
    # per tick which creeps sit on seats
    occ = defaultdict(list)
    all_ticks = set()
    for name, seq in by.items():
        for rec in seq:
            all_ticks.add(rec[0])
            if (rec[2], rec[3]) in SEATS:
                occ[rec[0]].append((name, rec[2], rec[3], rec[4]))
    if all_ticks:
        tmin, tmax = min(all_ticks), max(all_ticks)
        prev_names = None
        for t in range(tmin, tmax + 1):
            names = tuple(sorted(x[0] for x in occ.get(t, [])))
            if names != prev_names:
                p(lines, '  occ', t, 'n', len(names), names, occ.get(t))
                prev_names = names

    # filler at 34,32 around handoffs / deploy
    p(lines, '=== w8filler at/near 34,32 since LAST_TIP ===')
    fills = c.execute("""
        SELECT tick, ts, creep, x, y FROM creep_ticks
        WHERE room='W47N8' AND tick>=%s AND role='w8filler'
          AND x BETWEEN 32 AND 36 AND y BETWEEN 30 AND 35
        ORDER BY tick, creep
    """, (LAST_TIP,)).fetchall()
    # summarize who occupies 34,32
    at_post = [r for r in fills if (r[3], r[4]) == FILLER_POST]
    p(lines, 'rows_near', len(fills), 'at_34_32', len(at_post))
    if at_post:
        p(lines, 'first_post', at_post[0], 'last_post', at_post[-1])
        creeps = sorted({r[2] for r in at_post})
        p(lines, 'fillers_at_post', creeps)

    # --- coverage leftovers in last 2h ---
    p(lines, '=== official coverage holes last 2h (TIP-1600..TIP published) ===')
    lo = TIP - 1600
    for room in ('W46N8', 'W47N8', 'W45N8', 'W45N7', 'W47N7'):
        ticks = [r[0] for r in c.execute(
            'SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s',
            (room, lo, TIP)).fetchall()]
        miss = spans_missing(ticks, lo, TIP)
        p(lines, room, 'distinct', len(ticks), 'want', TIP - lo + 1, 'missing_n', sum(s[2] for s in miss), 'spans', miss[:12])

    # --- box pauses this hour ---
    p(lines, '=== box pauses last 3h ===')
    bp = Path('/workspace/screeps/metrics/box_pauses.jsonl')
    if bp.exists():
        for line in bp.read_text().splitlines()[-20:]:
            try:
                d = json.loads(line)
            except Exception:
                continue
            p(lines, ' pause', d)

    # --- room_stats gaps ---
    p(lines, '=== room_stats gaps W46N8 since last (>=30t) ===')
    rows = c.execute("""
        SELECT tick, ts FROM room_stats WHERE room='W46N8' AND tick>=%s AND tick<=%s ORDER BY tick
    """, (LAST_TIP, TIP)).fetchall()
    for i in range(1, len(rows)):
        dt = rows[i][0] - rows[i-1][0]
        if dt >= 30:
            wall = (rows[i][1] - rows[i-1][1]).total_seconds()
            p(lines, ' gap', rows[i-1][0], rows[i][0], 'dt', dt, 'wall_s', wall, rows[i-1][1], rows[i][1])

    # --- later-mean-robust tick_s from official chunk timestamps stored? use creep_ticks ts vs tick ---
    p(lines, '=== tick_s later-mean-robust (room_stats ts vs tick, last 40m) ===')
    rows = c.execute("""
        SELECT tick, ts FROM room_stats WHERE room='W46N8' AND tick>=%s AND tick<=%s ORDER BY tick
    """, (TIP - 800, TIP)).fetchall()
    # pairwise dt/dTick, drop outliers over 45% from median
    pairs = []
    for i in range(1, len(rows)):
        dtick = rows[i][0] - rows[i-1][0]
        if dtick <= 0:
            continue
        ds = (rows[i][1] - rows[i-1][1]).total_seconds()
        pairs.append(ds / dtick)
    if pairs:
        sp = sorted(pairs)
        med = sp[len(sp)//2]
        kept = [x for x in pairs if abs(x - med) / med <= 0.45]
        mean = sum(kept) / len(kept) if kept else None
        p(lines, f'n_pairs={len(pairs)} median={med:.5f} kept={len(kept)} mean_robust={mean:.5f} over45={len(pairs)-len(kept)} min={min(pairs):.5f} max={max(pairs):.5f}')
    else:
        p(lines, 'no pairs')

    # CPU already in exact2h; also print current bucket/cpu tip
    p(lines, '=== tip room_stats both rooms ===')
    for room in ('W46N8', 'W47N8'):
        row = c.execute("""
            SELECT tick, ts, rcl, progress, storage, energy, energy_cap, cpu, bucket, commit, ctl, ctl_ema, hostiles, sites, creeps
            FROM room_stats WHERE room=%s ORDER BY tick DESC LIMIT 1
        """, (room,)).fetchone()
        p(lines, room, row)

    p(lines, 'DONE')
    OUT.write_text('\n'.join(lines) + '\n')

if __name__ == '__main__':
    main()
