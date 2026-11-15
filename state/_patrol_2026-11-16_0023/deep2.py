#!/usr/bin/env python3
import sys, json
sys.path.insert(0, '/workspace/screeps/tools')
import db
from collections import defaultdict
from zoneinfo import ZoneInfo
from datetime import timezone
HK = ZoneInfo('Asia/Hong_Kong')
c = db.connect()
LAST, TIP = 84287220, 84288140

def p(*a): print(*a)

p('=== w8guard / w8defender trajectories ===')
for name in ('w8guard84287424','w8defender84287427'):
    rows=c.execute("""
    SELECT tick, room, x, y, store, hits, state
    FROM creep_ticks WHERE creep=%s AND tick BETWEEN %s AND %s
    ORDER BY tick
    """, (name, LAST, TIP+80)).fetchall()
    if not rows:
        p(name,'NO ROWS'); continue
    tiles=[]
    prev=None
    for r in rows:
        pos=(r[1],r[2],r[3])
        if pos!=prev:
            tiles.append((r[0],)+pos+(r[6],))
            prev=pos
    p(name,'samples',len(rows),'first',rows[0],'last',rows[-1],'tile_changes',len(tiles))
    for t in tiles[:20]:
        p('   ',t)

p('\n=== W47 upgraders first_loaded / last ===')
rows=c.execute("""
SELECT creep, min(tick), max(tick),
       min(tick) FILTER (WHERE store>0 AND room='W47N8') first_loaded,
       (array_agg(x||','||y||'@'||room||':'||state ORDER BY tick))[1] first_pos,
       (array_agg(x||','||y||'@'||room||':'||state ORDER BY tick DESC))[1] last_pos,
       count(*) FILTER (WHERE state='spawning' OR state='spawning') nsp
FROM creep_ticks
WHERE creep LIKE 'w8upgrader%%' AND tick BETWEEN %s AND %s
GROUP BY creep ORDER BY min(tick)
""", (LAST-400, TIP+80)).fetchall()
for r in rows: p(' ', r)

p('\n=== W47 builder last 80 ticks of published + tip ===')
rows=c.execute("""
SELECT tick, creep, x, y, store, state
FROM creep_ticks
WHERE room='W47N8' AND creep LIKE 'w8builder%%'
  AND tick BETWEEN 84288020 AND 84288180
ORDER BY tick, creep
""").fetchall()
by=defaultdict(list)
for r in rows: by[r[1]].append(r)
for n,rs in by.items():
    pos=sorted({(r[2],r[3],r[5]) for r in rs})
    p(n,'n',len(rs),'pos/state',pos,'first',rs[0],'last',rs[-1])

p('\n=== home upgraders ===')
rows=c.execute("""
SELECT creep, min(tick), max(tick),
       min(tick) FILTER (WHERE store>0 AND room='W46N8') first_loaded,
       (array_agg(x||','||y||':'||coalesce(state,'') ORDER BY tick))[1] fp,
       (array_agg(x||','||y||':'||coalesce(state,'') ORDER BY tick DESC))[1] lp
FROM creep_ticks
WHERE creep LIKE 'upgrader%%' AND creep NOT LIKE 'w8%%' AND tick BETWEEN %s AND %s
GROUP BY creep ORDER BY min(tick)
""", (LAST-400, TIP+80)).fetchall()
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
""", (LAST-400, TIP+80)).fetchall()
for r in rows: p(' ', r)

# W45N7 reserver coverage by tick
p('\n=== W45N7 ticks with a reserver present (since last-400) ===')
rows=c.execute("""
SELECT min(tick), max(tick), count(DISTINCT tick)
FROM creep_ticks
WHERE room='W45N7' AND (creep LIKE 'reserver%%' OR role='reserver')
  AND tick BETWEEN %s AND %s
""", (LAST-400, TIP+80)).fetchone()
p('presence', rows)
# gaps
ticks=[r[0] for r in c.execute("""
SELECT DISTINCT tick FROM creep_ticks
WHERE room='W45N7' AND (creep LIKE 'reserver%%' OR role='reserver')
  AND tick BETWEEN %s AND %s ORDER BY tick
""", (LAST-400, TIP+80)).fetchall()]
if ticks:
    gaps=[]
    prev=ticks[0]
    for t in ticks[1:]:
        if t>prev+1:
            gaps.append((prev+1,t-1,t-1-prev))
        prev=t
    p('first',ticks[0],'last',ticks[-1],'n',len(ticks),'gaps>5', [g for g in gaps if g[2]>5][:15])

p('\n=== reserve7 presence gaps ===')
ticks=[r[0] for r in c.execute("""
SELECT DISTINCT tick FROM creep_ticks
WHERE (creep LIKE 'reserve7%%' OR role='reserve7')
  AND tick BETWEEN %s AND %s ORDER BY tick
""", (LAST-200, TIP+80)).fetchall()]
if ticks:
    gaps=[]
    prev=ticks[0]
    for t in ticks[1:]:
        if t>prev+1:
            gaps.append((prev+1,t-1,t-1-prev))
        prev=t
    p('first',ticks[0],'last',ticks[-1],'n',len(ticks),'gaps>5',[g for g in gaps if g[2]>5])
    # first appearance of new
    rows=c.execute("""
    SELECT creep, min(tick), max(tick),
           (array_agg(room||':'||x||','||y ORDER BY tick))[1],
           (array_agg(room||':'||x||','||y ORDER BY tick DESC))[1]
    FROM creep_ticks WHERE creep LIKE 'reserve7%%' AND tick BETWEEN %s AND %s
    GROUP BY creep ORDER BY min(tick)
    """, (LAST-200, TIP+80)).fetchall()
    for r in rows: p('  name', r)

p('\n=== miner84287534 path ===')
rows=c.execute("""
SELECT tick, room, x, y, store, state
FROM creep_ticks WHERE creep='miner84287534' AND tick BETWEEN %s AND %s
ORDER BY tick
""", (LAST-50, TIP+80)).fetchall()
if rows:
    p('samples',len(rows),'first',rows[0],'last',rows[-1])
    prev=None; changes=[]
    for r in rows:
        pos=(r[1],r[2],r[3])
        if pos!=prev:
            changes.append((r[0],)+pos+(r[5],))
            prev=pos
    p('tile_changes',len(changes))
    for t in changes[:25]: p('  ',t)
    if len(changes)>25: 
        p('  ...')
        for t in changes[-8:]: p('  ',t)
    arr=[r for r in rows if r[1]=='W46N8' and r[2]==38 and r[3]==32]
    p('first at 38,32', arr[0] if arr else None, 'born', rows[0][0], 'delay', (arr[0][0]-rows[0][0]) if arr else None)

p('\n=== home miners this hour ===')
rows=c.execute("""
SELECT creep, min(tick), max(tick),
       (array_agg(x||','||y ORDER BY tick))[1] fp,
       (array_agg(x||','||y ORDER BY tick DESC))[1] lp,
       min(tick) FILTER (WHERE x=38 AND y=32) atB,
       min(tick) FILTER (WHERE x=31 AND y=12) atA
FROM creep_ticks
WHERE room='W46N8' AND creep LIKE 'miner%%' AND creep NOT LIKE 'w8%%' AND creep NOT LIKE 'rminer%%'
  AND tick BETWEEN %s AND %s
GROUP BY creep ORDER BY min(tick)
""", (LAST-100, TIP+80)).fetchall()
for r in rows: p(' ', r)

p('\n=== W47 source A miner (26,11) ===')
rows=c.execute("""
SELECT creep, min(tick), max(tick), count(*) n,
       count(*) FILTER (WHERE x=26 AND y=11) onA,
       count(*) FILTER (WHERE x=11 AND y=43) onB,
       count(*) FILTER (WHERE store>0) loaded
FROM creep_ticks
WHERE room='W47N8' AND creep LIKE 'w8miner%%' AND tick BETWEEN %s AND %s
GROUP BY creep ORDER BY min(tick)
""", (LAST, TIP)).fetchall()
for r in rows: p(' ', r)
onA=c.execute("""
SELECT count(DISTINCT tick) FROM creep_ticks
WHERE room='W47N8' AND x=26 AND y=11 AND creep LIKE 'w8miner%%' AND tick BETWEEN %s AND %s
""", (LAST, TIP)).fetchone()
p('distinct ticks w8miner at 26,11', onA, 'span', TIP-LAST)

p('\n=== home storage samples 23:31-00:07 ===')
rows=c.execute("""
SELECT tick, ts, storage, energy, creeps
FROM room_stats WHERE room='W46N8' AND tick BETWEEN 84287350 AND 84287820
ORDER BY tick
""").fetchall()
for r in rows:
    ts=r[1]
    if ts.tzinfo is None: ts=ts.replace(tzinfo=timezone.utc)
    p(f'  {r[0]} {ts.astimezone(HK).strftime("%H:%M:%S")} stor={r[2]} ea={r[3]} up={r[4].get("upgrader") if r[4] else None} def={r[4].get("defender") if r[4] else None} res={r[4].get("reserver") if r[4] else None} rminer={r[4].get("rminer")}')

p('\n=== defender84286880 path (rooms) ===')
rows=c.execute("""
SELECT tick, room, x, y, state
FROM creep_ticks WHERE creep='defender84286880' AND tick BETWEEN %s AND %s
ORDER BY tick
""", (LAST-100, TIP+80)).fetchall()
if rows:
    prev=None; changes=[]
    for r in rows:
        pos=(r[1],r[2],r[3])
        if pos!=prev:
            changes.append((r[0],)+pos+(r[4],))
            prev=pos
    p('samples',len(rows),'tile_changes',len(changes),'first',rows[0],'last',rows[-1])
    # print every 10th change plus room changes
    last_room=None
    for t in changes:
        if t[1]!=last_room or t==changes[0] or t==changes[-1]:
            p('  ROOM' if t[1]!=last_room else '  ', t)
            last_room=t[1]

p('DONE')
