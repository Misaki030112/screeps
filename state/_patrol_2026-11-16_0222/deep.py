#!/usr/bin/env python3
"""Deep traces: reservers, reserve7, W47 source A, upgraders, rdef, threat, later stats."""
import os, sys, json
from collections import defaultdict
from datetime import datetime
sys.path.insert(0, '/workspace/screeps/tools')
import db

LAST, TIP = 84288140, 84288890
HK = 'Asia/Hong_Kong'
out = []
def p(*a):
    s = ' '.join(str(x) for x in a)
    out.append(s)
    print(s)

c = db.connect()

def role_of(n):
    return ''.join(ch for ch in (n or '') if ch.isalpha()) or None

p('=== later room_stats after script TIP ===')
for room in ('W46N8','W47N8'):
    rows = c.execute('''
        SELECT tick, ts, progress, storage, energy, cpu, bucket, creeps, hostiles, sites, ctl
        FROM room_stats WHERE room=%s AND tick>=%s ORDER BY tick
    ''', (room, TIP)).fetchall()
    p(room, 'n', len(rows))
    for r in rows[-6:]:
        p(' ', r[0], r[1], 'p', r[2], 'stor', r[3], 'ea', r[4], 'cpu', r[5], 'host', r[8], 'ctl', r[10], 'creeps', r[7])

p('=== reserver / reserve7 trajectories since last ===')
rows = c.execute('''
    SELECT tick, ts, room, creep, x, y, energy, hits, spawning
    FROM creep_ticks
    WHERE tick BETWEEN %s AND %s
      AND (creep LIKE 'reserver%%' OR creep LIKE 'reserve7%%' OR creep LIKE 'reserve%%')
    ORDER BY creep, tick
''', (LAST-200, TIP+200)).fetchall()
by = defaultdict(list)
for r in rows:
    by[r[3]].append(r)
for name in sorted(by, key=lambda n: (role_of(n), n)):
    xs = by[name]
    first, last = xs[0], xs[-1]
    # first loaded / seated at controller-ish
    rooms = []
    prev_rm = None
    for t,ts,rm,cr,x,y,e,h,sp in xs:
        if rm != prev_rm:
            rooms.append((t, str(ts), rm, x, y))
            prev_rm = rm
    p(f'{name} n={len(xs)} first={first[0]} {first[1]} {first[2]} {first[4]},{first[5]} e={first[6]} sp={first[8]}')
    p(f'  last={last[0]} {last[1]} {last[2]} {last[4]},{last[5]} e={last[6]} hits={last[7]} sp={last[8]}')
    p(f'  room_changes {rooms}')
    # last 5
    p('  last5', [(r[0], r[2], r[4], r[5], r[6], r[8]) for r in xs[-5:]])

p('=== any reserver after 84288800 (live listener) ===')
rows = c.execute('''
    SELECT tick, ts, room, creep, x, y, energy, spawning
    FROM creep_ticks
    WHERE tick>=84288800 AND (creep LIKE 'reserver%%' OR creep LIKE 'reserve7%%')
    ORDER BY tick
''').fetchall()
p('n', len(rows))
for r in rows[:30]:
    p(' ', r)
if len(rows)>30:
    p(' ...', len(rows)-30, 'more; last=', rows[-1])

p('=== W47 miners (source A 26,11 / source B 11,43) since last ===')
rows = c.execute('''
    SELECT tick, ts, room, creep, x, y, energy, hits, spawning
    FROM creep_ticks
    WHERE tick BETWEEN %s AND %s
      AND creep LIKE 'w8miner%%'
    ORDER BY creep, tick
''', (LAST-50, TIP+50)).fetchall()
by = defaultdict(list)
for r in rows:
    by[r[3]].append(r)
for name, xs in by.items():
    first, last = xs[0], xs[-1]
    # position histogram
    pos = defaultdict(int)
    for t,ts,rm,cr,x,y,e,h,sp in xs:
        pos[(rm,x,y)] += 1
    top = sorted(pos.items(), key=lambda kv:-kv[1])[:6]
    p(f'{name} n={len(xs)} first={first[0]} {first[2]} {first[4]},{first[5]} last={last[0]} {last[2]} {last[4]},{last[5]} e={last[6]}')
    p('  top pos', top)
    # energy over time at A (26,11) — sample every ~50
    atA = [r for r in xs if r[2]=='W47N8' and r[4]==26 and r[5]==11]
    if atA:
        p(f'  at 26,11 n={len(atA)} first={atA[0][0]} last={atA[-1][0]} e_first={atA[0][6]} e_last={atA[-1][6]}')

p('=== W47 source containers / dropped near 26,11 and 11,43 if in room_objects? skip ===')

p('=== w8upgrader trajectories ===')
rows = c.execute('''
    SELECT tick, ts, room, creep, x, y, energy, spawning
    FROM creep_ticks
    WHERE tick BETWEEN %s AND %s AND creep LIKE 'w8upgrader%%'
    ORDER BY creep, tick
''', (LAST-100, TIP+100)).fetchall()
by = defaultdict(list)
for r in rows:
    by[r[3]].append(r)
for name, xs in by.items():
    first, last = xs[0], xs[-1]
    pos = defaultdict(int)
    first_loaded = next((r for r in xs if (r[6] or 0)>0 and not r[7]), None)
    p(f'{name} n={len(xs)} first={first[0]} {first[2]} {first[4]},{first[5]} e={first[6]} sp={first[7]} last={last[0]} {last[2]} {last[4]},{last[5]} e={last[6]}')
    if first_loaded:
        p(f'  first_loaded {first_loaded[0]} {first_loaded[2]} {first_loaded[4]},{first_loaded[5]} e={first_loaded[6]}')
    # time away from stands 14,27 / 12,25 / 14,26 / 15,26
    stands = {(14,27),(12,25),(14,26),(15,26),(13,26),(13,27),(12,26)}
    away = [r for r in xs if (r[4],r[5]) not in stands]
    p(f'  away_from_stands n={len(away)} last_away={away[-1][:6] if away else None}')

p('=== home upgrader trajectories ===')
rows = c.execute('''
    SELECT tick, ts, room, creep, x, y, energy, spawning
    FROM creep_ticks
    WHERE tick BETWEEN %s AND %s AND creep LIKE 'upgrader%%' AND creep NOT LIKE 'w8%%'
    ORDER BY creep, tick
''', (LAST-200, TIP+100)).fetchall()
by = defaultdict(list)
for r in rows:
    by[r[3]].append(r)
for name, xs in by.items():
    first, last = xs[0], xs[-1]
    first_loaded = next((r for r in xs if (r[6] or 0)>0 and not r[7]), None)
    p(f'{name} n={len(xs)} first={first[0]} {first[1]} {first[2]} {first[4]},{first[5]} e={first[6]} sp={first[7]}')
    p(f'  last={last[0]} {last[1]} {last[2]} {last[4]},{last[5]} e={last[6]}')
    if first_loaded:
        p(f'  first_loaded {first_loaded[0]} {first_loaded[1]} {first_loaded[2]} {first_loaded[4]},{first_loaded[5]} e={first_loaded[6]} delay_from_first={first_loaded[0]-first[0]}')

p('=== defender / rdef / guard trajectories ===')
rows = c.execute('''
    SELECT tick, ts, room, creep, x, y, hits, spawning
    FROM creep_ticks
    WHERE tick BETWEEN %s AND %s
      AND (creep LIKE 'defender%%' OR creep LIKE 'rdef%%' OR creep LIKE 'w8defender%%' OR creep LIKE 'w8guard%%')
    ORDER BY creep, tick
''', (LAST-800, TIP+100)).fetchall()
by = defaultdict(list)
for r in rows:
    by[r[3]].append(r)
for name, xs in by.items():
    first, last = xs[0], xs[-1]
    rooms = []
    prev = None
    for r in xs:
        key = (r[2], r[4], r[5]) if False else r[2]
        if key != prev:
            rooms.append((r[0], str(r[1]), r[2], r[4], r[5], r[6], r[7]))
            prev = key
    p(f'{name} n={len(xs)} first={first[0]} {first[2]} {first[4]},{first[5]} hits={first[6]} last={last[0]} {last[2]} {last[4]},{last[5]} hits={last[6]}')
    p(f'  room_seq {rooms[:12]}{"..." if len(rooms)>12 else ""}')

p('=== incidents tables / threat ===')
for table in ('incidents','threat_events','alerts','console_events'):
    try:
        n = c.execute(f"SELECT count(*) FROM {table} WHERE tick>=%s", (LAST-2000,)).fetchone()
        p('table', table, 'exists n since LAST-2000', n)
        rows = c.execute(f'SELECT * FROM {table} WHERE tick>=%s ORDER BY tick DESC LIMIT 15', (LAST-2000,)).fetchall()
        for r in rows:
            p(' ', table, r)
    except Exception as e:
        p('table', table, type(e).__name__, e)
        c.rollback()

# list tables like inc/threat
tabs = c.execute("""
    SELECT table_name FROM information_schema.tables
    WHERE table_schema='public' AND (table_name ILIKE '%incid%' OR table_name ILIKE '%threat%' OR table_name ILIKE '%alert%' OR table_name ILIKE '%invad%')
""").fetchall()
p('related tables', tabs)

p('=== w8builder ===')
rows = c.execute('''
    SELECT tick, ts, room, creep, x, y, energy, spawning
    FROM creep_ticks
    WHERE tick BETWEEN %s AND %s AND creep LIKE 'w8builder%%'
    ORDER BY creep, tick
''', (LAST-50, TIP+50)).fetchall()
by = defaultdict(list)
for r in rows:
    by[r[3]].append(r)
for name, xs in by.items():
    first, last = xs[0], xs[-1]
    p(f'{name} n={len(xs)} first={first[0]} {first[2]} {first[4]},{first[5]} last={last[0]} {last[2]} {last[4]},{last[5]} e={last[6]} sp={last[7]}')

p('=== Memory-ish from room_stats hostiles all rooms since last-2000 ===')
rows = c.execute('''
    SELECT room, tick, ts, hostiles FROM room_stats
    WHERE tick>=%s AND hostiles>0 ORDER BY tick
''', (LAST-2000,)).fetchall()
p('hostiles n', len(rows))
for r in rows[:20]:
    p(' ', r)

# coverage hole W47N8 84287500 still empty?
n = c.execute("SELECT count(DISTINCT tick) FROM creep_ticks WHERE room='W47N8' AND tick BETWEEN 84287501 AND 84287600").fetchone()[0]
p('W47N8@84287500 distinct', n)

# live listener freshness now
p('=== freshness now ===')
for table in ('room_stats','creep_ticks','creep_cpu'):
    p(table, c.execute(f'SELECT max(tick), max(ts), now()-max(ts) FROM {table}').fetchone())

open('/workspace/screeps/state/_patrol_2026-11-16_0117/deep.txt','w').write('\n'.join(out)+'\n')
p('WROTE deep.txt')
