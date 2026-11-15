#!/usr/bin/env python3
"""Deep traces: W47 upgrade/handoff, hostile, reservers, miner path, src A, storage drain."""
import sys
sys.path.insert(0, '/workspace/screeps/tools')
import db
from zoneinfo import ZoneInfo
from datetime import timezone
HK = ZoneInfo('Asia/Hong_Kong')
c = db.connect()
LAST, TIP = 84287220, 84288140

def hkt(t):
    if t is None: return None
    if t.tzinfo is None: t = t.replace(tzinfo=timezone.utc)
    return t.astimezone(HK).strftime('%H:%M:%S')

def p(*a):
    print(*a)

# W47 controller progress every sample
p('=== W47 progress deltas (room_stats) since last ===')
rows = c.execute("""
SELECT tick, ts, progress, storage, hostiles, sites,
       creeps->>'w8upgrader' AS u, creeps->>'w8builder' AS b,
       creeps->>'w8guard' AS g, creeps->>'w8defender' AS d
FROM room_stats WHERE room='W47N8' AND tick>=%s AND tick<=%s ORDER BY tick
""", (LAST, TIP)).fetchall()
prev=None
for r in rows:
    tick,ts,prog,stor,host,sites,u,b,g,d=r
    if prev:
        dt=tick-prev[0]; dp=prog-prev[2]; rate=dp/dt if dt else 0
        flag=' *' if host or (g!='0' and prev[7] in ('0',None)) or rate>=24 or rate<=12 else ''
        if dt>=30 or host or flag or rate>=24 or rate<=12 or tick in (84287420,84287430,84287440,84287760,84287850,84288100,84288140):
            p(f'  {tick} {hkt(ts)} dt={dt} +{dp} {rate:.2f} e/t stor={stor} host={host} sites={sites} up={u} bld={b} g={g} def={d}{flag}')
    prev=r

p('\n=== W47 3h stor >=30k/>=40k ===')
rows=c.execute("""
SELECT tick, ts, storage FROM room_stats
WHERE room='W47N8' AND tick>=%s AND tick<=%s ORDER BY tick
""", (TIP-int(3*3600/4.2), TIP)).fetchall()
stor=[(t,ts,s) for t,ts,s in rows]
mx=max(stor, key=lambda x:x[2]) if stor else None
n30=sum(1 for x in stor if x[2]>=30000); n40=sum(1 for x in stor if x[2]>=40000)
p('n',len(stor),'max',mx[0],hkt(mx[1]),mx[2],'>=30k',n30,'>=40k',n40)
# longest >=40k and >=30k spans
def longest(th):
    best=0; cur=0; start=None; bestspan=None
    prev=None
    for t,ts,s in stor:
        if s>=th:
            if cur==0: start=(t,ts)
            cur = (cur + (t-prev[0]) if prev and prev[2]>=th else 1)
            if cur>best:
                best=cur; bestspan=(start[0],t,hkt(start[1]),hkt(ts),best,s)
        else:
            cur=0
        prev=(t,ts,s)
    return bestspan
p('longest>=30k', longest(30000), 'longest>=40k', longest(40000))

p('\n=== hostiles all rooms since last ===')
rows=c.execute("""
SELECT room, tick, ts, hostiles, creeps
FROM room_stats WHERE tick>=%s AND tick<=%s AND hostiles>0
ORDER BY tick, room
""", (LAST-200, TIP)).fetchall()
p('n',len(rows))
for r in rows:
    p(' ', r[0], r[1], hkt(r[2]), 'host', r[3], 'creeps', r[4])

# creep_ticks: hostile-looking names around 84287430 in W47N8 / neighbors
p('\n=== creep names near 84287420-84287500 in W47N8/W47N9/W47N7 ===')
# our creeps only in creep_ticks typically; check distinct names
rows=c.execute("""
SELECT tick, name, role, x, y, room, energy, spawning
FROM creep_ticks
WHERE room IN ('W47N8','W47N7','W47N9','W46N8')
  AND tick BETWEEN 84287400 AND 84287520
  AND (name LIKE 'w8guard%' OR name LIKE 'w8defender%' OR name LIKE 'defender%' OR role IN ('w8guard','w8defender','defender','w8invader','invader'))
ORDER BY tick, name
""").fetchall()
# just first/last per name
from collections import defaultdict
by=defaultdict(list)
for r in rows: by[r[1]].append(r)
for n,rs in by.items():
    p(f'  {n} n={len(rs)} first={rs[0]} last={rs[-1]}')

p('\n=== w8guard / w8defender full trajectories (first/last + unique tiles) ===')
for name in ('w8guard84287424','w8defender84287427'):
    rows=c.execute("""
    SELECT tick, room, x, y, energy, hits, spawning, intent
    FROM creep_ticks WHERE name=%s AND tick BETWEEN %s AND %s
    ORDER BY tick
    """, (name, LAST, TIP+50)).fetchall()
    if not rows:
        p(name,'NO ROWS'); continue
    tiles=sorted({(r[1],r[2],r[3]) for r in rows})
    p(name,'samples',len(rows),'first',rows[0],'last',rows[-1],'unique_tiles',len(tiles),tiles[:12])

p('\n=== W47 upgraders first_loaded / last ===')
rows=c.execute("""
SELECT name, min(tick), max(tick),
       min(tick) FILTER (WHERE energy>0 AND room='W47N8') first_loaded,
       max(tick) FILTER (WHERE room='W47N8') last_in,
       (array_agg(x||','||y||'@'||room ORDER BY tick))[1] first_pos,
       (array_agg(x||','||y||'@'||room ORDER BY tick DESC))[1] last_pos
FROM creep_ticks
WHERE (name LIKE 'w8upgrader%' OR (role='w8upgrader'))
  AND tick BETWEEN %s AND %s
GROUP BY name ORDER BY min(tick)
""", (LAST-200, TIP+50)).fetchall()
for r in rows:
    p(' ', r)

p('\n=== W47 builder positions last 80 ticks of tip window ===')
rows=c.execute("""
SELECT tick, name, x, y, energy, intent
FROM creep_ticks
WHERE room='W47N8' AND (name LIKE 'w8builder%' OR role='w8builder')
  AND tick BETWEEN 84288060 AND 84288140
ORDER BY tick, name
""").fetchall()
# summarize unique pos per name and energy pattern
by=defaultdict(list)
for r in rows: by[r[1]].append(r)
for n,rs in by.items():
    pos=sorted({(r[2],r[3]) for r in rs})
    p(n,'n',len(rs),'pos',pos,'first',rs[0],'last',rs[-1])

p('\n=== home upgraders first_loaded ===')
rows=c.execute("""
SELECT name, min(tick), max(tick),
       min(tick) FILTER (WHERE energy>0 AND room='W46N8') first_loaded,
       (array_agg(x||','||y ORDER BY tick))[1] first_pos,
       (array_agg(x||','||y ORDER BY tick DESC))[1] last_pos
FROM creep_ticks
WHERE (name LIKE 'upgrader%' AND name NOT LIKE 'w8%') OR role='upgrader'
  AND tick BETWEEN %s AND %s
GROUP BY name ORDER BY min(tick)
""", (LAST-200, TIP+50)).fetchall()
for r in rows: p(' ', r)

p('\n=== reservers / reserve7 trajectories ===')
rows=c.execute("""
SELECT name, role, min(tick), max(tick),
       (array_agg(room||':'||x||','||y ORDER BY tick))[1] first_pos,
       (array_agg(room||':'||x||','||y ORDER BY tick DESC))[1] last_pos,
       count(*) FILTER (WHERE room='W45N7') n7,
       count(*) FILTER (WHERE room='W45N8') n8,
       count(*) FILTER (WHERE room='W47N7') n47
FROM creep_ticks
WHERE (role IN ('reserver','reserve7','reserve') OR name LIKE 'reserver%' OR name LIKE 'reserve7%')
  AND tick BETWEEN %s AND %s
GROUP BY name, role ORDER BY min(tick)
""", (LAST-300, TIP+50)).fetchall()
for r in rows: p(' ', r)

p('\n=== miner84287534 path ===')
rows=c.execute("""
SELECT tick, room, x, y, energy, spawning, intent
FROM creep_ticks WHERE name='miner84287534' AND tick BETWEEN %s AND %s
ORDER BY tick
""", (LAST, TIP+50)).fetchall()
if rows:
    p('samples',len(rows),'first',rows[0],'last',rows[-1])
    # find long stay vs walk
    prev=None; walks=[]; stay=None
    for r in rows:
        pos=(r[1],r[2],r[3])
        if prev and pos!= (prev[1],prev[2],prev[3]):
            walks.append((prev[0],r[0], (prev[1],prev[2],prev[3]), pos, r[0]-prev[0]))
        prev=r
    p('moves',len(walks),'sample',walks[:15],'... last',walks[-8:] if len(walks)>8 else '')
    # time to arrive 38,32
    arr=[r for r in rows if r[1]=='W46N8' and r[2]==38 and r[3]==32]
    p('first at 38,32', arr[0] if arr else None, 'spawn first', rows[0])

p('\n=== home miners this hour ===')
rows=c.execute("""
SELECT name, min(tick), max(tick),
       (array_agg(x||','||y ORDER BY tick))[1] fp,
       (array_agg(x||','||y ORDER BY tick DESC))[1] lp,
       min(tick) FILTER (WHERE x=38 AND y=32) atB,
       min(tick) FILTER (WHERE x=31 AND y=12) atA
FROM creep_ticks
WHERE room='W46N8' AND (role='miner' OR name LIKE 'miner%') AND name NOT LIKE 'w8%' AND name NOT LIKE 'rminer%'
  AND tick BETWEEN %s AND %s
GROUP BY name ORDER BY min(tick)
""", (LAST-100, TIP+50)).fetchall()
for r in rows: p(' ', r)

p('\n=== W47 source A miner presence (26,11) ===')
rows=c.execute("""
SELECT name, min(tick), max(tick), count(*) n,
       count(*) FILTER (WHERE x=26 AND y=11) onA,
       count(*) FILTER (WHERE energy>0) loaded
FROM creep_ticks
WHERE room='W47N8' AND (role='w8miner' OR name LIKE 'w8miner%')
  AND tick BETWEEN %s AND %s
GROUP BY name ORDER BY min(tick)
""", (LAST, TIP)).fetchall()
for r in rows: p(' ', r)
# ticks with someone at 26,11
onA=c.execute("""
SELECT count(DISTINCT tick) FROM creep_ticks
WHERE room='W47N8' AND x=26 AND y=11 AND tick BETWEEN %s AND %s
  AND (role='w8miner' OR name LIKE 'w8miner%')
""", (LAST, TIP)).fetchone()
span=TIP-LAST
p('distinct ticks with w8miner at 26,11', onA, 'span', span)

p('\n=== home storage drain around 23:38-23:41 (min 12705@84287480) ===')
rows=c.execute("""
SELECT tick, ts, storage, energy, creeps
FROM room_stats WHERE room='W46N8' AND tick BETWEEN 84287350 AND 84287820
ORDER BY tick
""").fetchall()
for r in rows:
    p(f'  {r[0]} {hkt(r[1])} stor={r[2]} ea={r[3]} creeps={r[4]}')

p('\n=== events/console-ish around hostile ===')
# events table?
try:
    rows=c.execute("""
    SELECT * FROM events WHERE tick BETWEEN %s AND %s ORDER BY tick LIMIT 30
    """, (LAST, TIP)).fetchall()
    p('events n', len(rows))
    for r in rows[:20]: p(' ', r)
except Exception as e:
    p('events err', e); c.rollback()

p('\n=== CPU bucket dips ===')
rows=c.execute("""
SELECT min(bucket), max(cpu), avg(cpu), min(cpu)
FROM room_stats WHERE room='W46N8' AND tick BETWEEN %s AND %s
""", (LAST, TIP)).fetchone()
p(rows)

p('DONE')
