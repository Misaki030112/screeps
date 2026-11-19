#!/usr/bin/env python3
"""Pull official room-history controller progress, storage energy, and hostiles."""
from __future__ import annotations
import json, sys, time
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, '/workspace/screeps/tools')
import history_backfill as hb

OUT = Path('/workspace/screeps/state/_patrol_2026-11-19_1723')
ROOMS = ('W46N8', 'W47N8', 'W45N8', 'W45N7', 'W47N7')
OWNED = ('W46N8', 'W47N8')
# Cover >2h plus overlap with last patrol hist (from 84349800 is enough for exact2h at tip~84351340;
# pull from 84349600 to be safe, and also reuse 0922 file for earlier overlap if needed)
TMIN_BASE = 84353600  # overlap 13:22 hist; merge older in exact_now  # overlap last patrol hist; merge older files in exact_now  # inclusive official bases
# latest published determined from game time

def find_controller_storage(objects):
    prog = stor = None
    ctrl = None
    storage = None
    for o in objects.values():
        t = o.get('type') or o.get('structureType')
        if t == 'controller':
            ctrl = o
            if o.get('progress') is not None:
                prog = int(o['progress'])
        elif t == 'storage':
            storage = o
            st = o.get('store') or {}
            if 'energy' in st:
                stor = int(st.get('energy') or 0)
    return prog, stor, ctrl, storage

def hostiles(objects, our_uid):
    out = []
    for oid, o in objects.items():
        if o.get('type') != 'creep':
            continue
        user = o.get('user')
        if user and user != our_uid:
            out.append({
                'id': oid, 'name': o.get('name'), 'user': user,
                'x': o.get('x'), 'y': o.get('y'),
                'hits': o.get('hits'), 'hitsMax': o.get('hitsMax'),
                'own': bool(o.get('user') == our_uid),
            })
        elif not user and o.get('name', '').startswith('invader'):
            out.append({
                'id': oid, 'name': o.get('name'), 'user': user,
                'x': o.get('x'), 'y': o.get('y'),
                'hits': o.get('hits'), 'hitsMax': o.get('hitsMax'),
            })
    return out

def our_creeps(objects, our_uid):
    rows = []
    for o in objects.values():
        if o.get('type') == 'creep' and o.get('user') == our_uid:
            rows.append((o.get('name'), o.get('x'), o.get('y'), (o.get('store') or {}).get('energy'), o.get('hits'), o.get('spawning')))
    return rows

def main():
    our = hb.uid()
    print('uid', our, flush=True)
    import api
    gt = api.req('game/time?shard=shard3')['time']
    latest = (gt // 100) * 100 - 100
    bases = list(range(TMIN_BASE, latest + 1, 100))
    print(f'game.time={gt} published_bases={bases[0]}..{bases[-1]} n={len(bases)}', flush=True)

    series = {r: [] for r in OWNED}  # [listener_tick, progress, storage]
    meta = {r: {'n': 0, 'missing_bases': [], 'tmin': None, 'tmax': None} for r in OWNED}
    hostile_events = []  # (listener_tick, room, hostiles)
    w47n7_creep_counts = []
    missing = []

    # carry state across chunks per room
    state = {r: {} for r in ROOMS}
    for base in bases:
        for room in ROOMS:
            j = hb.history_get(room, base)
            time.sleep(0.6)
            if not j:
                missing.append(f'{room}@{base}')
                if room in OWNED:
                    meta[room]['missing_bases'].append(base)
                print(f'  404 {room}@{base}', flush=True)
                # do not reset state; next chunk may still apply
                continue
            n = len(j.get('ticks') or {})
            print(f'  ok  {room}@{j.get("base")} ticks={n}', flush=True)
            for lt, objs in hb.merge_chunk(j, state[room]):
                # lt is listener tick (official T+1)
                if room in OWNED:
                    prog, stor, _, _ = find_controller_storage(objs)
                    if prog is not None or stor is not None:
                        series[room].append([lt, prog, stor])
                hs = hostiles(objs, our)
                if hs:
                    hostile_events.append({'t': lt, 'room': room, 'n': len(hs), 'hs': hs})
                if room == 'W47N7':
                    ours = our_creeps(objs, our)
                    w47n7_creep_counts.append({'t': lt, 'n': len(ours), 'creeps': ours})

    for room in OWNED:
        s = series[room]
        # dedup keep last per tick
        by = {}
        for t, p, st in s:
            by[t] = [t, p, st]
        s = [by[t] for t in sorted(by)]
        series[room] = s
        meta[room]['n'] = len(s)
        if s:
            meta[room]['tmin'] = s[0][0]
            meta[room]['tmax'] = s[-1][0]
            ps = [p for _, p, _ in s if p is not None]
            ss = [st for *_, st in s if st is not None]
            meta[room]['p0'] = ps[0] if ps else None
            meta[room]['p1'] = ps[-1] if ps else None
            meta[room]['smin'] = min(ss) if ss else None
            meta[room]['smax'] = max(ss) if ss else None
            # find argmin/argmax
            if ss:
                meta[room]['smin_t'] = next(t for t,p,st in s if st == meta[room]['smin'])
                meta[room]['smax_t'] = next(t for t,p,st in s if st == meta[room]['smax'])

    # compress hostile events: keep run starts/changes
    compact_h = []
    prev = {}
    for ev in hostile_events:
        key = (ev['room'], tuple(sorted((h['name'] or h['id'], h.get('hits'), h.get('x'), h.get('y')) for h in ev['hs'])))
        last = prev.get(ev['room'])
        if last != key:
            compact_h.append(ev)
            prev[ev['room']] = key
    # always keep last of each room
    last_by = {}
    for ev in hostile_events:
        last_by[ev['room']] = ev
    for ev in last_by.values():
        if ev not in compact_h:
            compact_h.append(ev)
    compact_h.sort(key=lambda e: (e['t'], e['room']))

    # W47N7 empty spans
    if w47n7_creep_counts:
        empty = []
        start = None
        for row in w47n7_creep_counts:
            if row['n'] == 0:
                if start is None:
                    start = row['t']
                end = row['t']
            else:
                if start is not None:
                    empty.append((start, end, end-start+1))
                    start = None
        if start is not None:
            empty.append((start, end, end-start+1))
    else:
        empty = []

    out = {
        'meta': meta,
        'series': series,
        'missing': missing,
        'gt': gt,
        'bases': [bases[0], bases[-1]],
        'uid': our,
    }
    (OUT / 'hist_progress_storage.json').write_text(json.dumps(out))
    (OUT / 'hist_hostiles.json').write_text(json.dumps({
        'compact': compact_h,
        'n_raw': len(hostile_events),
        'w47n7_empty': empty,
        'w47n7_n_samples': len(w47n7_creep_counts),
    }, indent=2))
    print('META', json.dumps(meta, indent=2))
    print('missing', missing)
    print('hostile compact events', len(compact_h), 'raw', len(hostile_events))
    for ev in compact_h:
        names = ','.join(f"{h.get('name')}@{h.get('x')},{h.get('y')} hits={h.get('hits')}" for h in ev['hs'])
        print(f"  HOST {ev['room']} t={ev['t']} n={ev['n']} {names}")
    print('W47N7 empty spans', empty)
    print('DONE')

if __name__ == '__main__':
    main()
