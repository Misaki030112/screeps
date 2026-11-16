#!/usr/bin/env python3
import sys
from collections import defaultdict
from zoneinfo import ZoneInfo
sys.path.insert(0, '/workspace/screeps/tools')
import db
HK = ZoneInfo('Asia/Hong_Kong')
LAST_TIP = 84308610  # previous 1h patrol analysis TIP (~02:29)
IDEAL = {'W46N8': 26.0, 'W47N8': 30.08}
c = db.connect()
TIP = c.execute("SELECT max(tick) FROM room_stats WHERE room='W46N8'").fetchone()[0]
print('DEEP LAST_TIP', LAST_TIP, 'TIP', TIP, flush=True)

def p(*a):
    print(*a, flush=True)

def ts(t):
    if t is None: return None
    return t.astimezone(HK).strftime('%Y-%m-%d %H:%M:%S')

def path(name, lo, hi, every=0):
    rows = c.execute('''
    SELECT tick, ts, room, x, y, store, state, hits
    FROM creep_ticks WHERE creep=%s AND tick BETWEEN %s AND %s
    ORDER BY tick
    ''', (name, lo, hi)).fetchall()
    if not rows:
        p(f'  {name}: no rows {lo}..{hi}')
        return rows
    first, last = rows[0], rows[-1]
    loaded = [r for r in rows if (r[5] or 0) > 0]
    p(f'  {name}: n={len(rows)} first={first[0]} {ts(first[1])} {first[2]} {first[3]},{first[4]} store={first[5]} st={first[6]} hits={first[7]}')
    p(f'         last={last[0]} {ts(last[1])} {last[2]} {last[3]},{last[4]} store={last[5]} st={last[6]} hits={last[7]}')
    if loaded:
        p(f'         first_loaded={loaded[0][0]} {loaded[0][2]} {loaded[0][3]},{loaded[0][4]} last_loaded={loaded[-1][0]} {loaded[-1][2]} {loaded[-1][3]},{loaded[-1][4]}')
    prev = None
    changes = 0
    seats = defaultdict(int)
    printed = 0
    for i,r in enumerate(rows):
        key = (r[2], r[3], r[4], (r[5] or 0) > 0, r[6])
        seats[(r[2], r[3], r[4])] += 1
        if prev is None or key != prev[0]:
            if every or printed < 16 or i == len(rows)-1:
                p(f'         @{r[0]} {ts(r[1])} {r[2]} {r[3]},{r[4]} e={r[5]} st={r[6]} hits={r[7]}')
                printed += 1
            changes += 1
            prev = (key, r)
    top = sorted(seats.items(), key=lambda kv: -kv[1])[:5]
    p(f'         top_tiles={top} changes={changes}')
    return rows

p('=== W47 upgraders around this hour ===')
ups = c.execute('''
SELECT creep, min(tick), max(tick),
       min(tick) FILTER (WHERE store>0) fl,
       max(tick) FILTER (WHERE store>0) ll,
       (ARRAY_AGG(room ORDER BY tick DESC))[1] lrm,
       (ARRAY_AGG(x ORDER BY tick DESC))[1] lx,
       (ARRAY_AGG(y ORDER BY tick DESC))[1] ly,
       count(*) n
FROM creep_ticks
WHERE role IN ('wupgrader','w8upgrader') AND tick BETWEEN %s AND %s
GROUP BY creep ORDER BY min(tick)
''', (LAST_TIP-400, TIP+80)).fetchall()
for r in ups:
    p('UP', r)
    path(r[0], max(r[1]-20, LAST_TIP-400), min(r[2]+20, TIP+80))

p('=== home upgraders around this hour ===')
hups = c.execute('''
SELECT creep, min(tick), max(tick),
       min(tick) FILTER (WHERE store>0) fl,
       max(tick) FILTER (WHERE store>0) ll,
       (ARRAY_AGG(x ORDER BY tick DESC))[1] lx,
       (ARRAY_AGG(y ORDER BY tick DESC))[1] ly,
       count(*)
FROM creep_ticks
WHERE role='upgrader' AND room='W46N8' AND tick BETWEEN %s AND %s
GROUP BY creep ORDER BY min(tick)
''', (LAST_TIP-400, TIP+80)).fetchall()
for r in hups:
    p('HUP', r)
    path(r[0], max(r[1]-20, LAST_TIP-400), min(r[2]+20, TIP+80))

p('=== defender / W45N7 core traces ===')
defs = c.execute('''
SELECT creep, role, min(tick), max(tick),
       (ARRAY_AGG(room ORDER BY tick))[1],
       (ARRAY_AGG(room ORDER BY tick DESC))[1],
       (ARRAY_AGG(x ORDER BY tick DESC))[1],
       (ARRAY_AGG(y ORDER BY tick DESC))[1],
       count(*) FILTER (WHERE room='W45N7') n7,
       count(*) n
FROM creep_ticks
WHERE (role IN ('defender','rdef','w8defender','w8guard') OR creep LIKE 'defender%%')
  AND tick BETWEEN %s AND %s
GROUP BY creep, role ORDER BY min(tick)
''', (LAST_TIP-200, TIP+80)).fetchall()
for r in defs:
    p('DEF', r)
    path(r[0], r[2], r[3])

p('=== W45N7 presence this hour (any of ours) ===')
rows = c.execute('''
SELECT tick, count(*), string_agg(DISTINCT creep, ',') names
FROM creep_ticks
WHERE room='W45N7' AND tick BETWEEN %s AND %s
GROUP BY tick ORDER BY tick
''', (LAST_TIP-50, TIP+20)).fetchall()
if rows:
    p('W45N7 present ticks', len(rows), 'first', rows[0][0] if rows else None, 'last', rows[-1][0] if rows else None)
# find gaps
if rows:
    ticks = [r[0] for r in rows]
    gaps=[]
    span=None
    want=set(range(ticks[0], ticks[-1]+1))
    miss=sorted(want-set(ticks))
    span=None
    for tk in miss:
        if span and tk==span[1]+1: span[1]=tk
        else:
            if span: gaps.append(tuple(span)+(span[1]-span[0]+1,))
            span=[tk,tk]
    if span: gaps.append(tuple(span)+(span[1]-span[0]+1,))
    p('W45N7 internal gaps', gaps)

p('=== incidents / alerts / box_pause ===')
try:
    for r in c.execute('''
    SELECT * FROM incidents
    WHERE tick>=%s
    ORDER BY tick
    ''', (LAST_TIP-200,)).fetchall():
        p('INC', r)
except Exception as e:
    p('incidents err', type(e), e)

# try other event tables
for tbl in ('events','alerts','console_events','box_events'):
    try:
        n=c.execute(f"SELECT count(*) FROM {tbl} WHERE tick>=%s", (LAST_TIP-200,)).fetchone()[0]
        p('table', tbl, 'n', n)
    except Exception as e:
        p('no', tbl, type(e).__name__)

# look at information_schema for event-like
tabs=c.execute("""
SELECT table_name FROM information_schema.tables
WHERE table_schema='public' AND (table_name ILIKE '%event%' OR table_name ILIKE '%alert%'
   OR table_name ILIKE '%incident%' OR table_name ILIKE '%pause%' OR table_name ILIKE '%threat%')
ORDER BY 1
""").fetchall()
p('event-like tables', tabs)

p('=== reserve7 / W47N7 reservers ===')
for r in c.execute('''
SELECT creep, role, min(tick), max(tick),
       (ARRAY_AGG(room ORDER BY tick DESC))[1],
       (ARRAY_AGG(x ORDER BY tick DESC))[1],
       (ARRAY_AGG(y ORDER BY tick DESC))[1],
       count(*)
FROM creep_ticks
WHERE (role IN ('reserve7','reserve') OR creep LIKE 'reserve%%')
  AND tick BETWEEN %s AND %s
GROUP BY creep, role ORDER BY min(tick)
''', (LAST_TIP-400, TIP+80)).fetchall():
    p('RES', r)
    path(r[0], r[2], r[3])

p('=== INTERP short windows from progress (room_stats + freeze-aware) ===')
# Use all room_stats samples; for a target lookback in ticks, interpolate progress at tip-N if needed,
# but also report progress delta over last N *published* samples and over wall-clock.
for room, ideal in IDEAL.items():
    rows=c.execute('''
    SELECT tick, ts, progress, storage FROM room_stats
    WHERE room=%s AND tick BETWEEN %s AND %s ORDER BY tick
    ''', (room, TIP-2000, TIP)).fetchall()
    tip=rows[-1]
    p(f'{room} tip {tip[0]} {ts(tip[1])} p={tip[2]} stor={tip[3]} n={len(rows)}')
    for window in (20, 40, 70, 100, 140, 200, 300, 500, 800, 1000):
        target = tip[0] - window
        # find brackets
        a=b=None
        for i,r in enumerate(rows):
            if r[0] <= target:
                a=r
            if r[0] >= target and b is None:
                b=r
        if a and b and a[0]!=b[0]:
            frac=(target-a[0])/(b[0]-a[0])
            p0=a[2]+frac*(b[2]-a[2])
            dt=tip[0]-target
            rate=(tip[2]-p0)/dt
            p(f'  INTERP last{window} target={target} p0={p0:.1f} dt={dt} rate={rate:.2f} {100*rate/ideal:.1f}% a={a[0]} b={b[0]}')
        elif a and (not b or a[0]==b[0]):
            # use a if close
            dt=tip[0]-a[0]
            if dt>0:
                rate=(tip[2]-a[2])/dt
                p(f'  NEAREST last{window} a={a[0]} dt={dt} rate={rate:.2f} {100*rate/ideal:.1f}%')
            else:
                p(f'  last{window} no span')
        else:
            p(f'  last{window} no bracket')

p('=== room_stats nUp/ctl/host/sites since last (compact) ===')
for room in ('W46N8','W47N8'):
    rows=c.execute('''
    SELECT tick, ts, storage, ctl, hostiles, sites, creeps, energy
    FROM room_stats WHERE room=%s AND tick BETWEEN %s AND %s ORDER BY tick
    ''', (room, LAST_TIP, TIP)).fetchall()
    p(f'--- {room} n={len(rows)} ---')
    prev=None
    for r in rows:
        creeps=r[6] if isinstance(r[6], dict) else {}
        nup = creeps.get('upgrader') if room=='W46N8' else creeps.get('w8upgrader')
        key=(nup, r[4], r[5], r[2]//500)  # nUp, host, sites, stor band
        if prev is None or key!=prev:
            p(f'  {r[0]} {ts(r[1])} stor={r[2]} ctl={r[3]} host={r[4]} sites={r[5]} nUp={nup} e={r[7]} creeps={creeps}')
            prev=key
    if rows:
        r=rows[-1]
        creeps=r[6] if isinstance(r[6], dict) else {}
        p(f'  TIP {r[0]} {ts(r[1])} stor={r[2]} ctl={r[3]} host={r[4]} sites={r[5]} creeps={creeps}')

p('=== box_pause / listener gaps from room_stats ts ===')
rows=c.execute('''
SELECT tick, ts FROM room_stats WHERE room='W46N8' AND tick BETWEEN %s AND %s ORDER BY tick
''', (LAST_TIP-200, TIP)).fetchall()
prev=None
for r in rows:
    if prev:
        dtick=r[0]-prev[0]
        dsec=(r[1]-prev[1]).total_seconds()
        if dtick>=30 or dsec>=90:
            p(f'  GAP ticks {prev[0]}->{r[0]} (+{dtick}) wall {ts(prev[1])}->{ts(r[1])} ({dsec:.1f}s) s/t={dsec/dtick:.3f}')
    prev=r

p('=== W47 40k latch check last 6h ===')
row=c.execute('''
SELECT count(*) FILTER (WHERE storage>=40000),
       max(storage),
       min(storage),
       count(*)
FROM room_stats WHERE room='W47N8' AND tick>=%s
''', (TIP-int(6*3600/4.0),)).fetchone()
p('6h >=40k / max / min / n', row)
# longest >=30k merged
rows=c.execute('''
SELECT tick, storage FROM room_stats WHERE room='W47N8' AND tick>=%s ORDER BY tick
''', (TIP-int(6*3600/4.0),)).fetchall()
best=0; cur=0; prevt=None; start=None
for t,s in rows:
    if s>=30000:
        if prevt is not None and t-prevt<=30:
            cur += t-prevt
        else:
            cur=0
            start=t
        best=max(best,cur)
    else:
        cur=0
    prevt=t
p('longest merged >=30k approx tick-span', best, 'n', len(rows))

p('=== listener rot / commit live.json peek (no secrets) ===')
import json
from pathlib import Path
rot=json.loads(Path('/workspace/screeps/metrics/listener_rot.json').read_text())
p('rot', rot)
live=json.loads(Path('/workspace/screeps/metrics/live.json').read_text())
# keys only + safe fields
p('live keys', sorted(live.keys()))
for k in ('gameTime','shard','commit','rooms','uid'):
    if k in live: p('live', k, live[k] if k!='uid' else '(set)' if live[k] else None)

p('DONE')
