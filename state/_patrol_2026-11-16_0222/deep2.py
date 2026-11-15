#!/usr/bin/env python3
import sys
from collections import defaultdict
from zoneinfo import ZoneInfo
from datetime import timezone
sys.path.insert(0, '/workspace/screeps/tools')
import db

HK = ZoneInfo('Asia/Hong_Kong')
c = db.connect()
LAST, TIP = 84288890, 84289800
out=[]
def p(*a):
    s=' '.join(str(x) for x in a)
    out.append(s); print(s)

def hkt(t):
    if t is None: return None
    if t.tzinfo is None: t=t.replace(tzinfo=timezone.utc)
    return t.astimezone(HK).strftime('%H:%M:%S')

p('=== later room_stats ===')
for room in ('W46N8','W47N8'):
    rows=c.execute("""
    SELECT tick, ts, progress, storage, energy, cpu, creeps, hostiles, ctl
    FROM room_stats WHERE room=%s AND tick>=%s ORDER BY tick
    """, (room, TIP)).fetchall()
    p(room,'n',len(rows))
    for r in rows[-8:]:
        cr=r[6] or {}
        p(f'  {r[0]} {hkt(r[1])} p={r[2]} stor={r[3]} ea={r[4]} cpu={r[5]} host={r[7]} ctl={r[8]} nUp={cr.get("upgrader")} w8u={cr.get("w8upgrader")} res={cr.get("reserver")} r7={cr.get("reserve7")} rmin={cr.get("rminer")}')

p('\n=== W47 progress deltas (flag unusual rates) ===')
rows=c.execute("""
SELECT tick, ts, progress, storage,
       creeps->>'w8upgrader' AS u, creeps->>'w8builder' AS b
FROM room_stats WHERE room='W47N8' AND tick>=%s ORDER BY tick
""", (LAST,)).fetchall()
prev=None
for r in rows:
    tick,ts,prog,stor,u,b=r
    if prev:
        dt=tick-prev[0]; dp=prog-prev[2]; rate=dp/dt if dt else 0
        if dt>=30 or rate<=12 or rate>=24 or tick in (LAST,TIP):
            p(f'  {tick} {hkt(ts)} dt={dt} +{dp} {rate:.2f} e/t stor={stor} up={u} bld={b}')
    prev=r

p('\n=== W47 3h stor >=30k/>=40k ===')
rows=c.execute("""
SELECT tick, ts, storage FROM room_stats
WHERE room='W47N8' AND tick>=%s AND tick<=%s ORDER BY tick
""", (TIP-int(3*3600/4.2), TIP)).fetchall()
stor=[(t,ts,s or 0) for t,ts,s in rows]
mx=max(stor, key=lambda x:x[2]) if stor else None
n30=sum(1 for x in stor if x[2]>=30000); n40=sum(1 for x in stor if x[2]>=40000)
p('n',len(stor),'max',mx[0],hkt(mx[1]),mx[2],'>=30k',n30,'>=40k',n40)
def longest(th):
    best=0; cur=0; start=None; bestspan=None; prev=None
    for t,ts,s in stor:
        if s>=th:
            if cur==0: start=(t,ts)
            cur = (t-prev[0] if prev and prev[2]>=th else 0) if prev else 0
            # tick-span from start
            span=t-start[0]
            if span>best:
                best=span; bestspan=(start[0],t,hkt(start[1]),hkt(ts),best,s)
        else:
            cur=0
        prev=(t,ts,s)
    return bestspan
p('longest>=30k', longest(30000), 'longest>=40k', longest(40000))

p('\n=== W47 upgraders first_loaded / last ===')
rows=c.execute("""
SELECT creep, min(tick), max(tick),
       min(tick) FILTER (WHERE store>0 AND room='W47N8') first_loaded,
       (array_agg(x||','||y||'@'||room||':'||coalesce(state,'') ORDER BY tick))[1] first_pos,
       (array_agg(x||','||y||'@'||room||':'||coalesce(state,'') ORDER BY tick DESC))[1] last_pos,
       count(*) FILTER (WHERE state='spawning') nsp
FROM creep_ticks
WHERE creep LIKE 'w8upgrader%%' AND tick BETWEEN %s AND %s
GROUP BY creep ORDER BY min(tick)
""", (LAST-400, TIP+200)).fetchall()
for r in rows: p(' ', r)

p('\n=== home upgraders ===')
rows=c.execute("""
SELECT creep, min(tick), max(tick),
       min(tick) FILTER (WHERE store>0 AND room='W46N8') first_loaded,
       (array_agg(x||','||y||':'||coalesce(state,'') ORDER BY tick))[1] fp,
       (array_agg(x||','||y||':'||coalesce(state,'') ORDER BY tick DESC))[1] lp,
       count(*) FILTER (WHERE state='spawning') nsp
FROM creep_ticks
WHERE creep LIKE 'upgrader%%' AND creep NOT LIKE 'w8%%' AND tick BETWEEN %s AND %s
GROUP BY creep ORDER BY min(tick)
""", (LAST-400, TIP+200)).fetchall()
for r in rows: p(' ', r)

p('\n=== reservers / reserve7 ===')
rows=c.execute("""
SELECT creep, role, min(tick), max(tick),
       (array_agg(room||':'||x||','||y ORDER BY tick))[1] fp,
       (array_agg(room||':'||x||','||y ORDER BY tick DESC))[1] lp,
       count(*) FILTER (WHERE room='W45N7') n7,
       count(*) FILTER (WHERE room='W45N8') n8,
       count(*) FILTER (WHERE room='W47N7') n47,
       count(*) FILTER (WHERE room='W46N8') nh
FROM creep_ticks
WHERE (creep LIKE 'reserver%%' OR creep LIKE 'reserve7%%' OR role IN ('reserver','reserve7','reserve'))
  AND tick BETWEEN %s AND %s
GROUP BY creep, role ORDER BY min(tick)
""", (LAST-800, TIP+200)).fetchall()
for r in rows: p(' ', r)

def presence_gaps(label, where, lo, hi):
    ticks=[r[0] for r in c.execute(f"""
    SELECT DISTINCT tick FROM creep_ticks
    WHERE {where} AND tick BETWEEN %s AND %s ORDER BY tick
    """, (lo, hi)).fetchall()]
    p(f'\n=== {label} presence ===')
    if not ticks:
        p('NO TICKS in', lo, hi); return
    gaps=[]
    prev=ticks[0]
    for t in ticks[1:]:
        if t>prev+1:
            gaps.append((prev+1,t-1,t-1-prev))
        prev=t
    # also gap at ends vs window
    if ticks[0]>lo:
        gaps.insert(0, (lo, ticks[0]-1, ticks[0]-lo))
    if ticks[-1]<hi:
        gaps.append((ticks[-1]+1, hi, hi-ticks[-1]))
    p('first',ticks[0],'last',ticks[-1],'n',len(ticks),'window',lo,hi,'gaps>5',[g for g in gaps if g[2]>5][:20])

presence_gaps('reserver any room', "(creep LIKE 'reserver%%' OR role='reserver')", LAST-200, TIP+50)
presence_gaps('reserver in W45N8', "room='W45N8' AND (creep LIKE 'reserver%%' OR role='reserver')", LAST-200, TIP+50)
presence_gaps('reserver in W45N7', "room='W45N7' AND (creep LIKE 'reserver%%' OR role='reserver')", LAST-400, TIP+50)
presence_gaps('reserve7 any', "(creep LIKE 'reserve7%%' OR role='reserve7')", LAST-200, TIP+50)

p('\n=== W47 source miners ===')
rows=c.execute("""
SELECT creep, min(tick), max(tick), count(*) n,
       count(*) FILTER (WHERE x=26 AND y=11) onA,
       count(*) FILTER (WHERE x=11 AND y=43) onB,
       count(*) FILTER (WHERE store>0) loaded,
       (array_agg(x||','||y||':'||coalesce(state,'') ORDER BY tick))[1] fp,
       (array_agg(x||','||y||':'||coalesce(state,'') ORDER BY tick DESC))[1] lp
FROM creep_ticks
WHERE room='W47N8' AND creep LIKE 'w8miner%%' AND tick BETWEEN %s AND %s
GROUP BY creep ORDER BY min(tick)
""", (LAST-400, TIP+200)).fetchall()
for r in rows: p(' ', r)
for tile,label in (((26,11),'A 26,11'),((11,43),'B 11,43')):
    n=c.execute("""
    SELECT count(DISTINCT tick), min(tick), max(tick) FROM creep_ticks
    WHERE room='W47N8' AND x=%s AND y=%s AND creep LIKE 'w8miner%%' AND tick BETWEEN %s AND %s
    """, (tile[0], tile[1], LAST, TIP)).fetchone()
    p(f'  distinct ticks w8miner at {label}', n, 'span', TIP-LAST)

# tile changes for A miner 87608
p('\n=== w8miner84287608 tile changes ===')
rows=c.execute("""
SELECT tick, room, x, y, store, state
FROM creep_ticks WHERE creep='w8miner84287608' AND tick BETWEEN %s AND %s
ORDER BY tick
""", (LAST-400, TIP+200)).fetchall()
if rows:
    prev=None; ch=[]
    for r in rows:
        pos=(r[1],r[2],r[3],r[5])
        if pos!=prev:
            ch.append((r[0],)+pos+(r[4],))
            prev=pos
    p('samples',len(rows),'changes',len(ch),'first',rows[0],'last',rows[-1])
    for t in ch[:30]: p('  ',t)
    if len(ch)>30:
        p('  ...')
        for t in ch[-8:]: p('  ',t)

p('\n=== defenders / rdef / guard ===')
rows=c.execute("""
SELECT creep, role, min(tick), max(tick),
       (array_agg(room||':'||x||','||y ORDER BY tick))[1] fp,
       (array_agg(room||':'||x||','||y ORDER BY tick DESC))[1] lp,
       min(hits), max(hits)
FROM creep_ticks
WHERE (creep LIKE 'defender%%' OR creep LIKE 'rdef%%' OR creep LIKE 'w8defender%%' OR creep LIKE 'w8guard%%')
  AND tick BETWEEN %s AND %s
GROUP BY creep, role ORDER BY min(tick)
""", (LAST-800, TIP+200)).fetchall()
for r in rows: p(' ', r)

for name in ('rdef84288188','defender84286880','w8guard84287424','w8defender84287427'):
    rows=c.execute("""
    SELECT tick, room, x, y, store, hits, state
    FROM creep_ticks WHERE creep=%s AND tick BETWEEN %s AND %s
    ORDER BY tick
    """, (name, LAST-800, TIP+200)).fetchall()
    if not rows:
        p(name,'NO ROWS'); continue
    prev=None; ch=[]
    last_room=None
    for r in rows:
        pos=(r[1],r[2],r[3])
        if pos!=prev:
            ch.append((r[0],)+pos+(r[6], r[5]))
            prev=pos
    p(f'{name} samples={len(rows)} tile_changes={len(ch)} first={rows[0]} last={rows[-1]}')
    for t in ch:
        if t[1]!=last_room or t==ch[0] or t==ch[-1]:
            p('  ROOM' if t[1]!=last_room else '  end' if t==ch[-1] else '  ', t)
            last_room=t[1]

p('\n=== w8builders ===')
rows=c.execute("""
SELECT creep, min(tick), max(tick),
       (array_agg(room||':'||x||','||y||':'||coalesce(state,'') ORDER BY tick))[1] fp,
       (array_agg(room||':'||x||','||y||':'||coalesce(state,'') ORDER BY tick DESC))[1] lp
FROM creep_ticks WHERE creep LIKE 'w8builder%%' AND tick BETWEEN %s AND %s
GROUP BY creep ORDER BY min(tick)
""", (LAST-200, TIP+200)).fetchall()
for r in rows: p(' ', r)

p('\n=== home storage since last (all samples) ===')
rows=c.execute("""
SELECT tick, ts, storage, energy, creeps
FROM room_stats WHERE room='W46N8' AND tick>=%s ORDER BY tick
""", (LAST,)).fetchall()
for r in rows:
    cr=r[4] or {}
    p(f'  {r[0]} {hkt(r[1])} stor={r[2]} ea={r[3]} nUp={cr.get("upgrader")} res={cr.get("reserver")} def={cr.get("defender")}')

p('\n=== hostiles since LAST-2000 ===')
rows=c.execute("""
SELECT room, tick, ts, hostiles FROM room_stats
WHERE tick>=%s AND hostiles>0 ORDER BY tick
""", (LAST-2000,)).fetchall()
p('n',len(rows))
for r in rows[:25]:
    p(' ', r[0], r[1], hkt(r[2]), 'host', r[3])

p('\n=== W47N8@84287500 hole still? ===')
n=c.execute("SELECT count(DISTINCT tick) FROM creep_ticks WHERE room='W47N8' AND tick BETWEEN 84287501 AND 84287600").fetchone()[0]
p('distinct',n)


p('\n=== incidents since LAST-200 ===')
try:
    rows=c.execute("""
    SELECT tick, ts, room, kind, state, why, dur, def, extra
    FROM incidents WHERE tick>=%s ORDER BY tick
    """, (LAST-200,)).fetchall()
except Exception as e:
    c.rollback()
    # try discover columns
    cols=c.execute("""
    SELECT column_name FROM information_schema.columns
    WHERE table_name='incidents' ORDER BY ordinal_position
    """).fetchall()
    p('incidents cols', [r[0] for r in cols], 'err', type(e).__name__, e)
    rows=c.execute("SELECT * FROM incidents WHERE tick>=%s ORDER BY tick", (LAST-200,)).fetchall()
p('n', len(rows))
for r in rows[:40]:
    p(' ', r)

p('\n=== W47 upgrader seats 14,26 / 14,27 / 12,25 ===')
for name in c.execute("""
SELECT DISTINCT creep FROM creep_ticks
WHERE creep LIKE 'w8upgrader%%' AND tick BETWEEN %s AND %s
ORDER BY creep
""", (LAST-400, TIP+200)).fetchall():
    name=name[0]
    rows=c.execute("""
    SELECT tick, room, x, y, store, state
    FROM creep_ticks WHERE creep=%s AND tick BETWEEN %s AND %s ORDER BY tick
    """, (name, LAST-400, TIP+200)).fetchall()
    if not rows: continue
    first_near=None; first_loaded=None; last_loaded=None
    for t,rm,x,y,st,state in rows:
        near = rm=='W47N8' and ((x,y) in ((14,26),(14,27),(12,25),(13,26),(13,27),(15,26),(15,27)))
        if near and first_near is None:
            first_near=(t,x,y,st,state)
        if rm=='W47N8' and st and st>0 and first_loaded is None:
            first_loaded=(t,x,y,st,state)
        if rm=='W47N8' and st and st>0:
            last_loaded=(t,x,y,st,state)
    p(name,'n',len(rows),'first',rows[0],'last',rows[-1],'first_near',first_near,'first_loaded',first_loaded,'last_loaded',last_loaded)

p('\n=== home upgrader seats ===')
for name in c.execute("""
SELECT DISTINCT creep FROM creep_ticks
WHERE creep LIKE 'upgrader%%' AND creep NOT LIKE 'w8%%' AND tick BETWEEN %s AND %s
ORDER BY creep
""", (LAST-400, TIP+200)).fetchall():
    name=name[0]
    rows=c.execute("""
    SELECT tick, room, x, y, store, state
    FROM creep_ticks WHERE creep=%s AND tick BETWEEN %s AND %s ORDER BY tick
    """, (name, LAST-400, TIP+200)).fetchall()
    if not rows: continue
    first_loaded=None; last_loaded=None
    for t,rm,x,y,st,state in rows:
        if st and st>0 and first_loaded is None:
            first_loaded=(t,x,y,st,state)
        if st and st>0:
            last_loaded=(t,x,y,st,state)
    p(name,'n',len(rows),'first',rows[0],'last',rows[-1],'first_loaded',first_loaded,'last_loaded',last_loaded)


p('\n=== freshness ===')
for table in ('room_stats','creep_ticks','creep_cpu'):
    p(table, c.execute(f'SELECT max(tick), max(ts), now()-max(ts) FROM {table}').fetchone())

p('DONE')
open('/workspace/screeps/state/_patrol_2026-11-16_0222/deep2.txt','w').write('\n'.join(out)+'\n')
