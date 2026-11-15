#!/usr/bin/env python3
import sys
from collections import defaultdict
from zoneinfo import ZoneInfo
from datetime import timezone
sys.path.insert(0, '/workspace/screeps/tools')
import db

HK = ZoneInfo('Asia/Hong_Kong')
c = db.connect()
LAST, TIP = 84289800, 84290720
IDEAL = {'W46N8': 26.0, 'W47N8': 30.08}
out=[]
def p(*a):
    s=' '.join(str(x) for x in a)
    out.append(s); print(s)

def hkt(t):
    if t is None: return None
    if t.tzinfo is None: t=t.replace(tzinfo=timezone.utc)
    return t.astimezone(HK).strftime('%H:%M:%S')

p('=== later room_stats after TIP ===')
for room in ('W46N8','W47N8'):
    rows=c.execute("""
    SELECT tick, ts, progress, storage, energy, cpu, creeps, hostiles, ctl
    FROM room_stats WHERE room=%s AND tick>=%s ORDER BY tick
    """, (room, TIP)).fetchall()
    p(room,'later_n',len(rows))
    for r in rows[-12:]:
        cr=r[6] or {}
        p(f'  {r[0]} {hkt(r[1])} p={r[2]} stor={r[3]} ea={r[4]} cpu={r[5]} host={r[7]} ctl={r[8]} nUp={cr.get("upgrader")} w8u={cr.get("w8upgrader")} bld={cr.get("w8builder")} res={cr.get("reserver")} r7={cr.get("reserve7")} def={cr.get("defender")}')

def progress_windows(room, tip):
    p(f'\n=== {room} progress samples since LAST and short-window reconstruct ===')
    rows=c.execute("""
    SELECT tick, ts, progress, storage,
           creeps->>'upgrader' AS u, creeps->>'w8upgrader' AS wu,
           creeps->>'w8builder' AS b, creeps->>'builder' AS hb
    FROM room_stats WHERE room=%s AND tick>=%s AND tick<=%s ORDER BY tick
    """, (room, LAST-200, tip+200)).fetchall()
    prev=None
    rates=[]
    for r in rows:
        tick,ts,prog,stor,u,wu,b,hb=r
        if prev:
            dt=tick-prev[0]; dp=prog-prev[2]; rate=dp/dt if dt else 0
            rates.append((tick,ts,dt,dp,rate,stor,u,wu,b))
            if dt>=30 or rate<=12 or rate>=24 or tick>=tip-50:
                p(f'  {tick} {hkt(ts)} dt={dt} +{dp} {rate:.2f} e/t stor={stor} up={u} w8u={wu} bld={b}')
        prev=r
    # Compute short windows using nearest sample at or before tip-N
    tiprow=None
    for r in rows:
        if r[0]<=tip:
            tiprow=r
    if not tiprow:
        p('  NO TIP ROW'); return
    p(f'  tiprow {tiprow[0]} {hkt(tiprow[1])} p={tiprow[2]} stor={tiprow[3]}')
    for win in (20,30,70,100,140,200,300,400,500):
        target=tiprow[0]-win
        before=[r for r in rows if r[0]<=target]
        after=[r for r in rows if r[0]>=target]
        if not before or not after:
            p(f'  last{win}t: no bracket around {target}')
            continue
        a=before[-1]; b=after[0]
        if a[0]==b[0]:
            ip, itick=a[2], a[0]
        else:
            frac=(target-a[0])/(b[0]-a[0])
            ip=a[2]+frac*(b[2]-a[2])
            itick=target
        dt=tiprow[0]-itick
        dp=tiprow[2]-ip
        et=dp/dt if dt else 0
        # also raw nearest-sample (no interp)
        raw_dt=tiprow[0]-a[0]; raw_dp=tiprow[2]-a[2]; raw_et=raw_dp/raw_dt if raw_dt else 0
        ideal=IDEAL[room]
        p(f'  last{win}t INTERP target={target} a={a[0]}@{hkt(a[1])} p={a[2]} b={b[0]} p={b[2]} dt={dt:.1f} +{dp:.1f} {et:.2f} e/t ={100*et/ideal:.1f}%  raw_from_a {raw_et:.2f} span={raw_dt}')

progress_windows('W46N8', TIP)
progress_windows('W47N8', TIP)

p('\n=== W47 3h stor >=30k/>=40k ===')
rows=c.execute("""
SELECT tick, ts, storage FROM room_stats
WHERE room='W47N8' AND tick>=%s AND tick<=%s ORDER BY tick
""", (TIP-int(3*3600/4.2), TIP)).fetchall()
stor=[(t,ts,s or 0) for t,ts,s in rows]
mx=max(stor, key=lambda x:x[2]) if stor else None
n30=sum(1 for x in stor if x[2]>=30000); n40=sum(1 for x in stor if x[2]>=40000)
p('n',len(stor),'max',mx[0],hkt(mx[1]),mx[2],'>=30k samples',n30,'>=40k',n40)
# also hour path
p('hour stor samples:')
for t,ts,s in stor:
    if t>=LAST:
        p(f'  {t} {hkt(ts)} {s}')

def longest(th):
    best=0; start=None; bestspan=None; prev=None
    for t,ts,s in stor:
        if s>=th:
            if start is None: start=(t,ts)
            span=t-start[0]
            if span>best:
                best=span; bestspan=(start[0],t,hkt(start[1]),hkt(ts),best,s)
        else:
            start=None
        prev=(t,ts,s)
    return bestspan
p('longest>=30k', longest(30000), 'longest>=40k', longest(40000))

# 25k crosses this hour
p('\n=== W47 25k/30k crosses since LAST-200 ===')
prev=None
for t,ts,s in stor:
    if t<LAST-200: continue
    if prev:
        for th,name in ((25000,'25k'),(30000,'30k'),(40000,'40k')):
            if prev[2]<th<=s:
                p(f'  over{name} {t} {hkt(ts)} {prev[2]}->{s}')
            if prev[2]>=th>s:
                p(f'  under{name} {t} {hkt(ts)} {prev[2]}->{s}')
    prev=(t,ts,s)

p('\n=== W47 upgraders first_loaded / last ===')
rows=c.execute("""
SELECT creep, min(tick), max(tick),
       min(tick) FILTER (WHERE store>0 AND room='W47N8' AND state IS DISTINCT FROM 'spawning') first_loaded,
       max(tick) FILTER (WHERE store>0 AND room='W47N8') last_loaded,
       (array_agg(x||','||y||'@'||room||':'||coalesce(state,'') ORDER BY tick))[1] first_pos,
       (array_agg(x||','||y||'@'||room||':'||coalesce(state,'') ORDER BY tick DESC))[1] last_pos,
       count(*) FILTER (WHERE state='spawning') nsp,
       min(tick) FILTER (WHERE state IS DISTINCT FROM 'spawning') first_alive
FROM creep_ticks
WHERE creep LIKE 'w8upgrader%%' AND tick BETWEEN %s AND %s
GROUP BY creep ORDER BY min(tick)
""", (LAST-500, TIP+200)).fetchall()
for r in rows: p(' ', r)

# detailed tile changes for each upgrader in window
p('\n=== W47 upgrader tile/store changes in window ===')
creeps=[r[0] for r in rows]
for name in creeps:
    rows=c.execute("""
    SELECT tick, room, x, y, store, state
    FROM creep_ticks WHERE creep=%s AND tick BETWEEN %s AND %s
    ORDER BY tick
    """, (name, LAST-200, TIP+50)).fetchall()
    if not rows: continue
    prev=None; ch=[]
    near_ctl=0; loaded=0
    for r in rows:
        tick,room,x,y,store,state=r
        pos=(room,x,y,state, 1 if (store or 0)>0 else 0)
        if pos!=prev:
            ch.append((tick,room,x,y,store,state))
            prev=pos
        if room=='W47N8' and 10<=x<=16 and 23<=y<=30 and (store or 0)>0 and state!='spawning':
            near_ctl+=1
        if (store or 0)>0: loaded+=1
    p(f'  {name} samples={len(rows)} changes={len(ch)} near_ctl_loaded={near_ctl} loaded={loaded} first={rows[0]} last={rows[-1]}')
    # print changes if not too many, else first/last and any not-near-ctl
    show=ch if len(ch)<=40 else ch[:12]+[('...','')]+ch[-12:]
    for t in show:
        p('   ', t)

p('\n=== builders near W47 controller ===')
rows=c.execute("""
SELECT creep, tick, x, y, store, state
FROM creep_ticks
WHERE room='W47N8' AND creep LIKE 'w8builder%%'
  AND tick BETWEEN %s AND %s
  AND x BETWEEN 10 AND 16 AND y BETWEEN 23 AND 30
ORDER BY tick
""", (LAST, TIP+50)).fetchall()
# compress to ranges per creep/tile
cur=None; ranges=[]
for r in rows:
    key=(r[0],r[2],r[3])
    if cur and cur[0]==key and r[1]==cur[2]+1:
        cur=(cur[0],cur[1],r[1],r[4],r[5])
    else:
        if cur: ranges.append(cur)
        cur=(key, r[1], r[1], r[4], r[5])
if cur: ranges.append(cur)
p('near-ctl builder ranges', len(ranges), 'raw', len(rows))
for r in ranges[:40]:
    p(' ', r[0], r[1], '->', r[2], 'len', r[2]-r[1]+1, 'store', r[3], r[4])

p('\n=== home upgraders ===')
rows=c.execute("""
SELECT creep, min(tick), max(tick),
       min(tick) FILTER (WHERE store>0 AND room='W46N8' AND state IS DISTINCT FROM 'spawning') first_loaded,
       max(tick) FILTER (WHERE store>0 AND room='W46N8') last_loaded,
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
       count(*) FILTER (WHERE room='W46N8') nh,
       count(*) FILTER (WHERE state='spawning') nsp
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
    # tile occupants over time (gaps)
    ticks=[r[0] for r in c.execute("""
    SELECT DISTINCT tick FROM creep_ticks
    WHERE room='W47N8' AND x=%s AND y=%s AND creep LIKE 'w8miner%%' AND tick BETWEEN %s AND %s ORDER BY tick
    """, (tile[0], tile[1], LAST, TIP)).fetchall()]
    gaps=[]
    if ticks:
        if ticks[0]>LAST: gaps.append((LAST,ticks[0]-1,ticks[0]-LAST))
        prev=ticks[0]
        for t in ticks[1:]:
            if t>prev+1: gaps.append((prev+1,t-1,t-1-prev))
            prev=t
        if ticks[-1]<TIP: gaps.append((ticks[-1]+1,TIP,TIP-ticks[-1]))
    p(f'    gaps>5', [g for g in gaps if g[2]>5][:15])

p('\n=== incidents since LAST-100 ===')
rows=c.execute("""
SELECT ts, tick, remote, inc, ev, from_state, state, why, inv, inv_ttl, def, dur, data
FROM incidents WHERE tick>=%s ORDER BY tick
""", (LAST-100,)).fetchall()
p('n',len(rows))
for r in rows:
    p(' ', r[1], hkt(r[0]), r[2], 'inc', r[3], 'ev', r[4], r[5], '->', r[6], 'why', r[7], 'def', r[10], 'dur', r[11], 'inv', r[8], r[9])

p('\n=== rdef / defender trajectories ===')
rows=c.execute("""
SELECT creep, role, min(tick), max(tick),
       (array_agg(room||':'||x||','||y||':'||coalesce(state,'')||':h'||hits ORDER BY tick))[1] fp,
       (array_agg(room||':'||x||','||y||':'||coalesce(state,'')||':h'||hits ORDER BY tick DESC))[1] lp,
       count(*) FILTER (WHERE state='spawning') nsp,
       min(hits), max(hits),
       count(*) FILTER (WHERE room='W47N7') n7,
       count(*) FILTER (WHERE room='W47N8') n8
FROM creep_ticks
WHERE (creep LIKE 'rdef%%' OR creep LIKE 'w8defender%%' OR creep LIKE 'w8guard%%' OR role IN ('defender','rdef','w8defender','w8guard'))
  AND tick BETWEEN %s AND %s
GROUP BY creep, role ORDER BY min(tick)
""", (LAST-200, TIP+200)).fetchall()
for r in rows: p(' ', r)

# tile changes for rdef84290307
p('\n=== rdef84290307 tile changes ===')
rows=c.execute("""
SELECT tick, room, x, y, hits, store, state
FROM creep_ticks WHERE creep='rdef84290307' AND tick BETWEEN %s AND %s
ORDER BY tick
""", (LAST, TIP+80)).fetchall()
prev=None; ch=[]
for r in rows:
    pos=(r[1],r[2],r[3],r[6],r[4])
    if pos!=prev:
        ch.append(r); prev=pos
p('samples',len(rows),'changes',len(ch))
for t in ch:
    p(' ', t[0], hkt(None) if False else t[0], t[1], f'{t[2]},{t[3]}', 'hits', t[4], 'st', t[6])

# any hostile creeps in W47N7?
p('\n=== any non-owned creeps in remotes this hour (from events or our creeps hits) ===')
# events
erows=c.execute("""
SELECT ts, tick, kind, room, severity, msg, left(data::text,200)
FROM events WHERE tick>=%s AND tick<=%s
  AND (kind ILIKE '%%invad%%' OR kind ILIKE '%%host%%' OR kind ILIKE '%%core%%' OR kind ILIKE '%%threat%%' OR severity IN ('warn','error','alert'))
ORDER BY tick
""", (LAST, TIP+50)).fetchall()
p('events n',len(erows))
for r in erows[:40]:
    p(' ', r[1], hkt(r[0]), r[2], r[3], r[4], r[5], r[6])

p('\n=== W47N7 creeps this hour (roles around core time) ===')
rows=c.execute("""
SELECT tick, creep, role, x, y, hits, store, state
FROM creep_ticks
WHERE room='W47N7' AND tick BETWEEN 84290290 AND 84290690
  AND (creep LIKE 'rdef%%' OR creep LIKE 'invader%%' OR role IN ('defender','rdef') OR hits IS NOT NULL AND hits<4000 AND creep LIKE 'rdef%%')
ORDER BY tick
""").fetchall()
# just rdef in that room + unique creep names
names=c.execute("""
SELECT creep, role, min(tick), max(tick), min(hits), max(hits), count(*)
FROM creep_ticks
WHERE room='W47N7' AND tick BETWEEN 84290280 AND 84290720
GROUP BY creep, role ORDER BY min(tick)
""").fetchall()
p('unique creeps in W47N7 around incident:')
for r in names: p(' ', r)

p('\n=== home storage samples since LAST ===')
rows=c.execute("""
SELECT tick, ts, storage FROM room_stats
WHERE room='W46N8' AND tick>=%s AND tick<=%s ORDER BY tick
""", (LAST, TIP+80)).fetchall()
for t,ts,s in rows:
    p(f'  {t} {hkt(ts)} {s}')

p('\n=== inferred upgrade work from creep_ticks (W47, loaded near ctl) ===')
# per 10-tick bucket count loaded upgraders + builders near ctl
rows=c.execute("""
SELECT tick,
       count(*) FILTER (WHERE creep LIKE 'w8upgrader%%' AND store>0 AND x BETWEEN 10 AND 16 AND y BETWEEN 23 AND 30) ups,
       count(*) FILTER (WHERE creep LIKE 'w8builder%%' AND store>0 AND x BETWEEN 10 AND 16 AND y BETWEEN 23 AND 30) blds
FROM creep_ticks
WHERE room='W47N8' AND tick BETWEEN %s AND %s
GROUP BY tick ORDER BY tick
""", (LAST, TIP)).fetchall()
# summarize buckets
if rows:
    # fill missing ticks as None
    by={t:(u,b) for t,u,b in rows}
    def avg(lo,hi):
        xs=[by[t] for t in range(lo,hi+1) if t in by]
        if not xs: return None,0
        # 10 e/t per upgrader, builders maybe 5-6 work? unknown; report counts
        mu=sum(u for u,b in xs)/len(xs)
        mb=sum(b for u,b in xs)/len(xs)
        return (mu,mb,len(xs),hi-lo+1)
    for lo,hi,label in [
        (TIP-20,TIP,'last20'),(TIP-30,TIP,'last30'),(TIP-100,TIP,'last100'),
        (TIP-200,TIP,'last200'),(TIP-300,TIP,'last300'),(LAST,TIP,'hour'),
        (84290350,84290680,'freeze3'),(84290020,84290260,'freeze2'),
        (84290201,84290256,'official_hole'),
    ]:
        a=avg(lo,hi)
        p(f'  {label} {lo}-{hi} avg_ups={a[0] if a[0] is not None else None} avg_bld={a[1] if a[0] is not None else None} samples={a[2] if a[0] is not None else 0}/{a[3] if a[0] is not None else hi-lo+1}')
    # transitions of (ups,blds)
    prev=None; ch=[]
    for t,u,b in rows:
        key=(u,b)
        if key!=prev:
            ch.append((t,u,b)); prev=key
    p('  (ups,blds) changes', len(ch))
    for t in ch:
        p('   ', t[0], 'ups',t[1],'bld',t[2])

p('\n=== listener slot / deploy.lock / git status snippets via files later ===')
p('DONE')
open('/workspace/screeps/state/_patrol_2026-11-16_0325/deep2.txt','w').write('\n'.join(out)+'\n')
