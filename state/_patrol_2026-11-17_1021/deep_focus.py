#!/usr/bin/env python3
import sys
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
sys.path.insert(0, '/workspace/screeps/tools')
import db

HK = ZoneInfo('Asia/Hong_Kong')
LAST, TIP = 84313970, 84314690
ROOMS = ('W46N8','W47N8','W45N8','W45N7','W47N7')

def p(*a):
    print(*a, flush=True)

c = db.connect()

p('=== nUp / storage / upgrader seats HOME ===')
rows = c.execute('''
SELECT tick, ts, storage, (creeps->>'upgrader')::int AS nup, upgrade, p
FROM room_stats WHERE room='W46N8' AND tick BETWEEN %s AND %s
ORDER BY tick
''', (LAST, TIP+80)).fetchall()
# print changes in nup and under15k samples
prev=None
for r in rows:
    tick,ts,stor,nup,upg,prog=r
    flag=''
    if stor is not None and stor<15000: flag+=' UNDER15k'
    if prev is None or prev[3]!=nup or (stor and prev[2] and (stor>=15000)!=(prev[2]>=15000)) or (stor and (stor>=20000)!=(prev[2]>=20000 if prev[2] else False)):
        p(f'  {tick} {ts.astimezone(HK) if ts else None} stor={stor} nUp={nup} upgrade={upg} p={prog}{flag}')
    prev=r
if rows:
    r=rows[-1]
    p(f'  LAST {r[0]} {r[1].astimezone(HK) if r[1] else None} stor={r[2]} nUp={r[3]} upgrade={r[4]} p={r[5]}')
p('home samples', len(rows), 'under15k', sum(1 for r in rows if r[2] is not None and r[2]<15000),
  'min', min((r[2],r[0],r[1]) for r in rows if r[2] is not None),
  'max', max((r[2],r[0],r[1]) for r in rows if r[2] is not None))

p('=== W47 nUp / storage / 40k ===')
rows = c.execute('''
SELECT tick, ts, storage, (creeps->>'w8upgrader')::int AS nup, upgrade, p
FROM room_stats WHERE room='W47N8' AND tick BETWEEN %s AND %s
ORDER BY tick
''', (LAST-2000, TIP+80)).fetchall()  # need 6h for 40k? do since_last + scan >=40k
prev=None
ge40=[]
for r in rows:
    tick,ts,stor,nup,upg,prog=r
    if tick>=LAST:
        flag=''
        if stor and stor>=40000: flag+=' GE40k'
        if prev is None or (prev[0]>=LAST and (prev[3]!=nup or (stor and prev[2] and (stor>=25000)!=(prev[2]>=25000) or (stor>=40000)!=(prev[2]>=40000)))):
            p(f'  {tick} {ts.astimezone(HK) if ts else None} stor={stor} nUp={nup} upgrade={upg} p={prog}{flag}')
        prev=r
# 40k spans in this hour and 6h
for lo,label in ((TIP-int(6*3600/4.4),'6h'), (LAST,'since_last'), (TIP-int(3*3600/4.4),'3h')):
    rr=c.execute('''
      SELECT tick, storage FROM room_stats WHERE room='W47N8' AND tick>=%s AND tick<=%s ORDER BY tick
    ''', (lo, TIP)).fetchall()
    mx=max((r[1] or 0, r[0]) for r in rr) if rr else (None,None)
    # longest >=40000 run (allowing 10t gap? use consecutive samples)
    best=0; cur=0; start=None; bestspan=None
    prevt=None
    for t,s in rr:
        if s is not None and s>=40000:
            if cur==0: start=t
            cur += (t-prevt) if prevt and t-prevt<=20 else 1
            if cur>best:
                best=cur; bestspan=(start,t,t-start if start else 0)
        else:
            cur=0; start=None
        prevt=t
    p(f'  40k {label} max={mx} best_ge40_span={bestspan} best_len={best} n={len(rr)}')

p('=== room_stats gaps since last (freeze map) ===')
for room in ('W46N8','W47N8'):
    ticks=[r[0] for r in c.execute('SELECT tick FROM room_stats WHERE room=%s AND tick BETWEEN %s AND %s ORDER BY 1',(room,LAST-200,TIP+50))]
    s=set(ticks)
    gaps=[]; st=None
    for t in range((ticks[0] if ticks else LAST), (ticks[-1] if ticks else TIP)+1):
        if t not in s:
            if st is None: st=t
        elif st is not None:
            gaps.append((st,t-1,t-st)); st=None
    if st is not None: gaps.append((st,ticks[-1],ticks[-1]-st+1))
    # only report gaps >= 20
    big=[g for g in gaps if g[2]>=20]
    p(room, 'gaps>=20', big)

p('=== official coverage 84313901..84314600 + live fills in 404 holes ===')
for room, hole in (('W47N8',(84314001,84314051)), ('W45N7',(84314501,84314600))):
    d=c.execute('SELECT count(DISTINCT tick), min(tick), max(tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s',
                (room, hole[0], hole[1])).fetchone()
    p(f'  {room} hole {hole} distinct={d[0]} range={d[1]}..{d[2]}')
    # any creeps?
    names=c.execute('SELECT creep, min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s GROUP BY 1',
                    (room, hole[0], hole[1])).fetchall()
    p('    creeps', names[:8])

# last W45N7 creeps around the 404
p('=== W45N7 last official / after ===')
rows=c.execute('''
SELECT tick,ts,creep,x,y,state,store FROM creep_ticks
WHERE room='W45N7' AND tick BETWEEN 84314480 AND 84314690
ORDER BY tick, creep
''').fetchall()
# summarize last 15 unique ticks
seen=set(); show=[]
for r in rows:
    if r[0] not in seen:
        seen.add(r[0])
    show.append(r)
# print first/last few and tick set
ticks=sorted(seen)
p('  ticks present', ticks[:8], '...', ticks[-8:], 'n', len(ticks))
if rows:
    for r in rows[:8]:
        p('  first', r)
    for r in rows[-12:]:
        p('  last', r)

p('=== CPU since_last / 1h / 2h ===')
for lo,label in ((LAST,'since_last'), (TIP-int(3600/4.71),'1h'), (TIP-int(7200/4.71),'2h')):
    r=c.execute('''
      SELECT avg(cpu), max(cpu), min(bucket), max(bucket), count(*), min(tick) FILTER (WHERE cpu=(SELECT max(cpu) FROM room_stats r2 WHERE r2.room='W46N8' AND r2.tick BETWEEN %s AND %s))
      FROM room_stats WHERE room='W46N8' AND tick BETWEEN %s AND %s
    ''', (lo,TIP,lo,TIP)).fetchone()
    mx=c.execute('SELECT tick, ts, cpu, bucket FROM room_stats WHERE room=%s AND tick BETWEEN %s AND %s ORDER BY cpu DESC NULLS LAST LIMIT 1',
                 ('W46N8',lo,TIP)).fetchone()
    p(label, 'avg', r[0], 'max', mx, 'bkt_min', r[2], 'n', r[4])

p('=== home 20k / 3h 6h ===')
for lo,label in ((LAST,'since_last'), (TIP-int(3*3600/4.5),'3h'), (TIP-int(6*3600/4.5),'6h')):
    r=c.execute('SELECT min(storage), max(storage), count(*) FILTER (WHERE storage>=20000), count(*) FROM room_stats WHERE room=%s AND tick>=%s AND tick<=%s',
                ('W46N8',lo,TIP)).fetchone()
    p(label, r)

p('=== role zeros critical ===')
for role in ('miner','rminer','reserver','queen','w8filler','w8miner','w8rminer'):
    rows=c.execute('''
      SELECT tick, (creeps->>%s)::int FROM room_stats
      WHERE room='W46N8' AND tick BETWEEN %s AND %s AND (creeps->>%s) IS NOT NULL
      ORDER BY tick
    ''', (role, LAST, TIP, role)).fetchall()
    zeros=[]
    st=None
    prev=None
    lastv=None
    for t,v in rows:
        lastv=v
        if v==0:
            if st is None: st=t
        elif st is not None:
            zeros.append((st,prev,prev-st+1)); st=None
        prev=t
    if st is not None: zeros.append((st,prev,prev-st+1))
    p(role, 'last', lastv, 'zero_runs', zeros)

p('=== W47 threat / reserved ===')
# from room_stats if columns exist
cols=[r[0] for r in c.execute("SELECT column_name FROM information_schema.columns WHERE table_name='room_stats'")]
p('room_stats cols sample', [x for x in cols if any(k in x.lower() for k in ('host','core','res','threat','safe','why'))])

p('=== hostiles this hour ===')
for room in ROOMS:
    r=c.execute("SELECT count(*) FILTER (WHERE hostiles>0), max(hostiles), min(tick) FILTER (WHERE hostiles>0), max(tick) FILTER (WHERE hostiles>0) FROM room_stats WHERE room=%s AND tick BETWEEN %s AND %s",
                (room, LAST, TIP)).fetchone()
    p(room, 'host', r)
