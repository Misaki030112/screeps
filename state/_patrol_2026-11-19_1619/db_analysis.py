#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from collections import defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path

sys.path.insert(0, '/workspace/screeps/tools')
import db

OUT = Path('/workspace/screeps/state/_patrol_2026-11-19_1619')
HK = ZoneInfo('Asia/Hong_Kong')
LAST_TIP = 84355124
TIP = 84355783
ROOMS = ('W46N8','W47N8','W45N8','W45N7','W47N7')

def main():
    c = db.connect()
    out=[]
    def p(*a):
        s=' '.join(str(x) for x in a)
        out.append(s); print(s)

    # freshness
    p('=== freshness ===')
    now=datetime.now(HK)
    for table, tickcol in (('creep_ticks','tick'),('room_stats','tick')):
        for room in ROOMS:
            row=c.execute(f"SELECT max({tickcol}), max(ts) FROM {table} WHERE room=%s", (room,)).fetchone()
            p(f'  {table} {room} max_tick={row[0]} max_ts={row[1]}')
    row=c.execute("SELECT max(tick), max(ts), count(*) FROM room_stats").fetchone()
    p('  room_stats global', row)

    # hour coverage LAST_TIP+1 .. TIP
    p('=== hour coverage LAST_TIP+1..TIP', LAST_TIP+1, TIP, 'span', TIP-LAST_TIP, '===')
    span = TIP - LAST_TIP
    expect = span  # ticks LAST_TIP+1..TIP inclusive = TIP-LAST_TIP
    for room in ROOMS:
        rows=c.execute("""
            SELECT min(tick), max(tick), count(DISTINCT tick)
            FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s
        """, (room, LAST_TIP+1, TIP)).fetchone()
        mn,mx,n=rows
        missing=expect-(n or 0)
        p(f'  {room} {n}/{expect} min={mn} max={mx} missing={missing}')
        # gaps >= 5
        ticks=[r[0] for r in c.execute("SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s ORDER BY 1",(room,LAST_TIP+1,TIP))]
        gaps=[]
        prev=LAST_TIP
        for t in ticks+[TIP+1]:
            if t-prev>1:
                gaps.append((prev+1, t-1, t-prev-1))
            prev=t
        # only report gaps >=5 or first few
        big=[g for g in gaps if g[2]>=5]
        p(f'    gaps>=5 n={len(big)} {big[:12]}{"..." if len(big)>12 else ""} small_gaps={len(gaps)-len(big)}')

    # leftover known 404 ranges
    p('=== leftover official 404 windows (may be outside hour) ===')
    for room, lo, hi in (('W46N8',84354301,84354351),('W47N7',84354301,84354400),('W47N8',84352400,84352499)):
        n=c.execute("SELECT count(DISTINCT tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",(room,lo,hi)).fetchone()[0]
        p(f'  {room} {lo}..{hi} distinct={n} expect={hi-lo+1}')

    # W45N7 40min backfill short tail
    p('=== W45N7 84355001..84355700 coverage ===')
    ticks=[r[0] for r in c.execute("SELECT DISTINCT tick FROM creep_ticks WHERE room='W45N7' AND tick BETWEEN 84355001 AND 84355700 ORDER BY 1")]
    p(f'  distinct={len(ticks)} min={ticks[0] if ticks else None} max={ticks[-1] if ticks else None}')
    if ticks:
        missing=[]
        s=set(ticks)
        for t in range(84355001,84355701):
            if t not in s: missing.append(t)
        p(f'  missing n={len(missing)} first_last={missing[:8], missing[-8:] if missing else None}')

    # roles presence this hour
    p('=== role presence LAST_TIP+1..TIP ===')
    want=['miner','rminer','reserver','queen','w8filler','w8miner','w8rminer','reserve7','defender','upgrader','w8upgrader','rhauler','hauler']
    rows=c.execute("""
        SELECT tick, role, count(DISTINCT creep)
        FROM creep_ticks
        WHERE tick BETWEEN %s AND %s AND role = ANY(%s)
        GROUP BY 1,2
    """, (LAST_TIP+1, TIP, want)).fetchall()
    by=defaultdict(dict)
    for t,role,n in rows:
        by[role][t]=n
    for role in want:
        d=by[role]
        ticks_present=sorted(d)
        zeros=[]
        # ticks in hour with 0
        all_ticks=set(range(LAST_TIP+1, TIP+1))
        absent=sorted(all_ticks - set(ticks_present))
        # collapse absent spans
        spans=[]
        if absent:
            a=b=absent[0]
            for t in absent[1:]:
                if t==b+1: b=t
                else:
                    spans.append((a,b,b-a+1)); a=b=t
            spans.append((a,b,b-a+1))
        big=[s for s in spans if s[2]>=20]
        mx=max(d.values()) if d else 0
        mn=min(d.values()) if d else 0
        p(f'  {role}: ticks_present={len(ticks_present)}/{expect} n min/max={mn}/{mx} absent_spans>=20 {big[:8]} absent_total={len(absent)}')

    # upgrader trajectories
    p('=== home upgraders ===')
    rows=c.execute("""
        SELECT creep, min(tick), max(tick), min(x), max(x), min(y), max(y)
        FROM creep_ticks
        WHERE role='upgrader' AND tick BETWEEN %s AND %s
        GROUP BY 1 ORDER BY 2
    """, (LAST_TIP-200, TIP+50)).fetchall()
    for r in rows:
        # last and first pos
        first=c.execute("SELECT tick,room,x,y,store FROM creep_ticks WHERE creep=%s AND tick BETWEEN %s AND %s ORDER BY tick LIMIT 1",(r[0], LAST_TIP-200, TIP+50)).fetchone()
        last=c.execute("SELECT tick,room,x,y,store FROM creep_ticks WHERE creep=%s AND tick BETWEEN %s AND %s ORDER BY tick DESC LIMIT 1",(r[0], LAST_TIP-200, TIP+50)).fetchone()
        # seated ticks near controller (29-31, 29-31)
        seated=c.execute("""
            SELECT min(tick), max(tick), count(*) FROM creep_ticks
            WHERE creep=%s AND tick BETWEEN %s AND %s AND room='W46N8' AND x BETWEEN 28 AND 32 AND y BETWEEN 28 AND 32
        """, (r[0], LAST_TIP-200, TIP+50)).fetchone()
        p(f'  {r[0]} life {r[1]}..{r[2]} first={first} last={last} seated={seated}')

    p('=== W47 upgraders ===')
    rows=c.execute("""
        SELECT creep, min(tick), max(tick)
        FROM creep_ticks
        WHERE role='w8upgrader' AND tick BETWEEN %s AND %s
        GROUP BY 1 ORDER BY 2
    """, (LAST_TIP-200, TIP+50)).fetchall()
    for r in rows:
        first=c.execute("SELECT tick,room,x,y,store FROM creep_ticks WHERE creep=%s AND tick BETWEEN %s AND %s ORDER BY tick LIMIT 1",(r[0], LAST_TIP-200, TIP+50)).fetchone()
        last=c.execute("SELECT tick,room,x,y,store FROM creep_ticks WHERE creep=%s AND tick BETWEEN %s AND %s ORDER BY tick DESC LIMIT 1",(r[0], LAST_TIP-200, TIP+50)).fetchone()
        seated=c.execute("""
            SELECT min(tick), max(tick), count(*),
                   array_agg(DISTINCT (x||','||y)) FROM creep_ticks
            WHERE creep=%s AND tick BETWEEN %s AND %s AND room='W47N8'
              AND ((x=12 AND y=25) OR (x=14 AND y IN (26,27,28)))
        """, (r[0], LAST_TIP-200, TIP+50)).fetchone()
        p(f'  {r[0]} life {r[1]}..{r[2]} first={first} last={last} seated={seated}')

    # nUp counts per tick near tip and during hour
    p('=== nUp counts ===')
    for role,label in (('upgrader','home'),('w8upgrader','W47')):
        rows=c.execute("""
            SELECT tick, count(DISTINCT creep) FROM creep_ticks
            WHERE role=%s AND tick BETWEEN %s AND %s
            GROUP BY 1 ORDER BY 1
        """, (role, LAST_TIP+1, TIP)).fetchall()
        hist=defaultdict(int)
        for t,n in rows: hist[n]+=1
        # spans of each n
        spans=defaultdict(list)
        if rows:
            a,n0=rows[0][0], rows[0][1]
            prevt,prevn=rows[0]
            for t,n in rows[1:]:
                if n!=prevn or t!=prevt+1:
                    spans[prevn].append((a,prevt,prevt-a+1))
                    a=t
                prevt,prevn=t,n
            spans[prevn].append((a,prevt,prevt-a+1))
        p(f'  {label} hist_n={dict(hist)} long_spans={ {k:[s for s in v if s[2]>=15][:6] for k,v in spans.items()} }')

    # reservers
    p('=== reservers / reserve7 ===')
    for role in ('reserver','reserve7','reserve'):
        rows=c.execute("""
            SELECT creep, room, min(tick), max(tick), min(x), max(x), min(y), max(y)
            FROM creep_ticks WHERE role=%s AND tick BETWEEN %s AND %s
            GROUP BY 1,2 ORDER BY 3
        """, (role, LAST_TIP-400, TIP+50)).fetchall()
        p(f'  {role} n={len(rows)}')
        for r in rows:
            last=c.execute("SELECT tick,room,x,y FROM creep_ticks WHERE creep=%s AND tick BETWEEN %s AND %s ORDER BY tick DESC LIMIT 1",(r[0], LAST_TIP-400, TIP+50)).fetchone()
            p(f'    {r} last={last}')

    # defender / W45N7 hostiles
    p('=== defender84355620 path ===')
    rows=c.execute("""
        SELECT tick, room, x, y FROM creep_ticks
        WHERE creep='defender84355620' ORDER BY tick
    """).fetchall()
    p(f'  n={len(rows)} first={rows[0] if rows else None} last={rows[-1] if rows else None}')
    if rows:
        # room changes
        prev=None
        for t,rm,x,y in rows:
            if rm!=prev:
                p(f'    enter {rm} at {t} {x},{y}')
                prev=rm
        p(f'    last {rows[-1]}')

    # any foreign creeps in remotes this hour? (we only store our creeps typically)
    p('=== miners seated ===')
    for role in ('miner','w8miner','rminer','w8rminer'):
        rows=c.execute("""
            SELECT creep, min(tick), max(tick),
                   (array_agg(room || ':' || x || ',' || y ORDER BY tick DESC))[1] AS lastpos
            FROM creep_ticks WHERE role=%s AND tick BETWEEN %s AND %s
            GROUP BY 1 ORDER BY 2
        """, (role, LAST_TIP-50, TIP)).fetchall()
        for r in rows:
            p(f'  {role} {r}')

    # room_stats freshness / CPU
    p('=== room_stats CPU W46N8 since LAST_TIP ===')
    rows=c.execute("""
        SELECT tick, ts, cpu, bucket, storage, progress, creeps
        FROM room_stats WHERE room='W46N8' AND tick BETWEEN %s AND %s
        ORDER BY tick
    """, (LAST_TIP, TIP+80)).fetchall()
    p(f'  n={len(rows)} min_tick={rows[0][0] if rows else None} max_tick={rows[-1][0] if rows else None}')
    if rows:
        cpus=[r[2] for r in rows if r[2] is not None]
        bkts=[r[3] for r in rows if r[3] is not None]
        imax=max(range(len(rows)), key=lambda i: rows[i][2] or -1)
        p(f'  cpu n={len(cpus)} min={min(cpus):.2f} max={max(cpus):.2f}@{rows[imax][0]} mean={sum(cpus)/len(cpus):.2f} bkt min={min(bkts) if bkts else None} max={max(bkts) if bkts else None}')
        # gaps
        ut=sorted({r[0] for r in rows})
        gaps=[]
        for i in range(1,len(ut)):
            if ut[i]-ut[i-1]>30:
                gaps.append((ut[i-1]+1, ut[i]-1, ut[i]-ut[i-1]-1))
        p('  gaps>=30', gaps)
        # storage min/max
        stors=[(r[0],r[4]) for r in rows if r[4] is not None]
        if stors:
            tmn=min(stors,key=lambda x:x[1]); tmx=max(stors,key=lambda x:x[1])
            under=sum(1 for _,s in stors if s<15000)
            p(f'  stor min={tmn} max={tmx} under15k={under}/{len(stors)} last={stors[-1]}')

    p('=== room_stats W47N8 storage since LAST_TIP ===')
    rows=c.execute("""
        SELECT tick, ts, storage, progress FROM room_stats
        WHERE room='W47N8' AND tick BETWEEN %s AND %s AND storage IS NOT NULL
        ORDER BY tick
    """, (LAST_TIP, TIP+80)).fetchall()
    if rows:
        stors=[(r[0],r[2]) for r in rows]
        tmn=min(stors,key=lambda x:x[1]); tmx=max(stors,key=lambda x:x[1])
        p(f'  n={len(rows)} min={tmn} max={tmx} last={stors[-1]}')
        # 40k check in 12h/24h later in exact_now

    # 12h/24h W47 max from room_stats
    p('=== W47 12h/24h stor from room_stats ===')
    for label, lo in (('12h', TIP-int(12*3600/4.8)), ('24h', TIP-int(24*3600/4.8))):
        row=c.execute("""
            SELECT min(storage), max(storage),
                   (array_agg(tick ORDER BY storage DESC))[1] as tmx,
                   count(*) FILTER (WHERE storage>=40000),
                   count(*)
            FROM room_stats WHERE room='W47N8' AND tick BETWEEN %s AND %s AND storage IS NOT NULL
        """, (lo, TIP)).fetchone()
        p(f'  {label} lo={lo} {row}')

    p('=== home 12h/24h stor from room_stats ===')
    for label, lo in (('12h', TIP-int(12*3600/4.8)), ('24h', TIP-int(24*3600/4.8))):
        row=c.execute("""
            SELECT min(storage), max(storage),
                   (array_agg(tick ORDER BY storage DESC))[1] as tmx,
                   count(*) FILTER (WHERE storage>=20000),
                   count(*) FILTER (WHERE storage<15000),
                   count(*)
            FROM room_stats WHERE room='W46N8' AND tick BETWEEN %s AND %s AND storage IS NOT NULL
        """, (lo, TIP)).fetchone()
        p(f'  {label} lo={lo} {row}')

    # W45N7 creeps around invader time
    p('=== W45N7 creeps around 84355600..TIP ===')
    rows=c.execute("""
        SELECT tick, creep, role, x, y FROM creep_ticks
        WHERE room='W45N7' AND tick BETWEEN 84355580 AND %s
        ORDER BY tick, creep
    """, (TIP,)).fetchall()
    # summarize unique creeps and last/first
    creeps=defaultdict(list)
    for t,cr,role,x,y in rows:
        creeps[cr].append((t,role,x,y))
    p(f'  rows={len(rows)} creeps={len(creeps)}')
    for cr,pts in creeps.items():
        p(f'    {cr} {pts[0][1]} n={len(pts)} {pts[0][0]} {pts[0][2]},{pts[0][3]} .. {pts[-1][0]} {pts[-1][2]},{pts[-1][3]}')

    # DB writer recency vs now
    p('=== listener ingest recency ===')
    row=c.execute("SELECT max(tick), max(ts) FROM creep_ticks").fetchone()
    p('  creep_ticks max', row, 'now', now)
    row=c.execute("SELECT max(tick), max(ts) FROM room_stats").fetchone()
    p('  room_stats max', row)

    (OUT/'db_analysis.txt').write_text('\n'.join(out)+'\n')
    p('WROTE', OUT/'db_analysis.txt')

if __name__=='__main__':
    main()
