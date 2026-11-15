#!/usr/bin/env python3
"""Deep patrol analysis: invader, handoffs, short INTERP, storage, reservers, CPU, hole."""
import sys, json, re
from datetime import datetime, timezone, timedelta
from collections import defaultdict
sys.path.insert(0, "/workspace/screeps/tools")
import db as dbmod

HK = timezone(timedelta(hours=8))
OUT = "/workspace/screeps/state/_patrol_2026-11-16_0518/deep3.txt"
lines = []
def p(s=""):
    print(s, flush=True)
    lines.append(str(s))

conn = dbmod.connect()

def q(sql, *args):
    cur = conn.execute(sql, args) if args else conn.execute(sql)
    cols = [d.name for d in cur.description] if cur.description else []
    rows = cur.fetchall()
    if not cols:
        return rows
    return [dict(zip(cols, r)) for r in rows]

LAST = 84291540  # previous patrol tip ~04:30
LOOK = 84290700

tips = q("SELECT max(tick) t, max(ts) ts FROM room_stats")[0]
TIP = tips["t"]
p(f"=== NOW / tips room_stats={TIP} {tips['ts']} ===")
for r in q("SELECT room, max(tick) t, count(*) FILTER (WHERE tick>=%s) n FROM creep_ticks WHERE tick>=%s GROUP BY 1 ORDER BY 1", LOOK, LOOK):
    p(f"  creep_ticks {r['room']} tip={r['t']} n_since_look={r['n']}")

p("\n=== hostiles all rooms since last-3h ===")
for r in q("""
SELECT tick, ts, room, hostiles, storage, energy, creeps
FROM room_stats
WHERE tick>=%s AND hostiles>0
ORDER BY tick, room
""", LAST-2000):
    p(f"  HOST {r['room']} t={r['tick']} {r['ts']} host={r['hostiles']} stor={r['storage']} ea={r['energy']} creeps={r['creeps']}")

p("\n=== unusual creep names since LAST-200 (not typical role+digits) ===")
rows = q("""
SELECT creep, role, room, min(tick) a, max(tick) b, count(*) n,
       (array_agg(x ORDER BY tick))[1] x0, (array_agg(y ORDER BY tick))[1] y0,
       (array_agg(x ORDER BY tick DESC))[1] x1, (array_agg(y ORDER BY tick DESC))[1] y1,
       (array_agg(hits ORDER BY tick DESC))[1] hits1,
       (array_agg(store ORDER BY tick DESC))[1] store1
FROM creep_ticks
WHERE tick>=%s
  AND creep !~ '^(w8)?(upgrader|miner|hauler|rhauler|rminer|reserver|queen|filler|builder|defender|rdef|guard)'
  AND creep !~ '^reserve7'
  AND creep !~ '^w8(upgrader|miner|hauler|rhauler|rminer|filler|builder|defender|guard|mm miner|mmminer)'
GROUP BY 1,2,3
ORDER BY a
""", LAST-200)
p(f"n_unusual={len(rows)}")
for r in rows:
    p(r)

p("\n=== names containing invader/Invader/core ===")
for r in q("""
SELECT creep, role, room, min(tick) a, max(tick) b, count(*) n,
       (array_agg(x ORDER BY tick))[1] x0, (array_agg(y ORDER BY tick))[1] y0,
       (array_agg(x ORDER BY tick DESC))[1] x1, (array_agg(y ORDER BY tick DESC))[1] y1,
       (array_agg(hits ORDER BY tick DESC))[1] hits1
FROM creep_ticks
WHERE tick>=%s AND (creep ILIKE '%%invader%%' OR creep ILIKE '%%core%%' OR role ILIKE '%%invader%%' OR role ILIKE '%%core%%')
GROUP BY 1,2,3
ORDER BY a
""", LOOK):
    p(r)

p("\n=== events since LAST-200 ===")
for r in q("""
SELECT ts, tick, kind, room, severity, episode, msg, data
FROM events
WHERE tick>=%s
ORDER BY tick, ts
""", LAST-200):
    p(f"  {r['tick']} {r['ts']} {r['room']} {r['kind']}/{r['severity']} ep={r['episode']} {r['msg']} data={r['data']}")

p("\n=== recent incidents (last 20) ===")
for r in q("""
SELECT ts, tick, remote, inc, ev, from_state, state, why, inv, inv_ttl, def, dur, data
FROM incidents
ORDER BY tick DESC, ts DESC
LIMIT 20
"""):
    p(r)

# store type
p("\n=== sample store for an upgrader ===")
for r in q("""
SELECT creep, tick, store, state, hits FROM creep_ticks
WHERE creep LIKE 'w8upgrader%%' AND tick>=%s
ORDER BY tick DESC LIMIT 3
""", LAST):
    p(r)

# helper to parse energy from store
def energy_of(store):
    if store is None:
        return None
    if isinstance(store, dict):
        return store.get('energy') or store.get('E') or 0
    if isinstance(store, (int, float)):
        return int(store)
    if isinstance(store, str):
        try:
            d=json.loads(store)
            return energy_of(d)
        except Exception:
            return None
    return None

p("\n=== W47 upgraders since LAST-400: spawn/first/last loaded seats ===")
ups = q("""
SELECT creep, tick, ts, room, x, y, store, state, hits
FROM creep_ticks
WHERE tick>=%s AND creep LIKE 'w8upgrader%%'
ORDER BY creep, tick
""", LAST-400)
by = defaultdict(list)
for r in ups:
    r['e'] = energy_of(r['store'])
    by[r['creep']].append(r)
SEATS = {(14,27),(14,26),(12,25),(13,26),(15,26),(12,26),(13,25),(15,27),(11,25),(11,24)}
for name, rs in sorted(by.items(), key=lambda kv: kv[1][0]['tick']):
    first=rs[0]; last=rs[-1]
    loaded=[r for r in rs if (r['e'] or 0)>0 and (r['x'],r['y']) in SEATS or ((r['e'] or 0)>0 and r['room']=='W47N8' and abs((r['x'] or 0)-14)+abs((r['y'] or 0)-26)<=4)]
    # first/last at controller-adjacent
    near=[r for r in rs if r['room']=='W47N8' and r['x'] is not None and r['x']<=16 and r['y'] is not None and r['y']<=30 and r['x']>=10 and r['y']>=22]
    first_loaded = next((r for r in rs if (r['e'] or 0)>0 and r in near), None)
    last_loaded = None
    for r in rs:
        if (r['e'] or 0)>0 and r['room']=='W47N8' and r['x'] is not None and r['x']<=16 and r['y'] is not None and r['y']<=30:
            last_loaded=r
    last_near = near[-1] if near else None
    # empty leaving
    left_empty = next((r for r in rs if last_loaded and r['tick']>last_loaded['tick'] and (r['e'] or 0)==0), None)
    p(f"{name} n={len(rs)} {first['tick']}@{first['room']} {first['x'],first['y']} -> {last['tick']}@{last['room']} {last['x'],last['y']} e={last['e']} st={last['state']}")
    if first_loaded:
        p(f"  first_loaded {first_loaded['tick']} {first_loaded['ts']} {first_loaded['x'],first_loaded['y']} e={first_loaded['e']}")
    if last_loaded:
        p(f"  last_loaded  {last_loaded['tick']} {last_loaded['ts']} {last_loaded['x'],last_loaded['y']} e={last_loaded['e']}")
    if left_empty:
        p(f"  left_empty   {left_empty['tick']} {left_empty['x'],left_empty['y']}")
    # position histogram near end
    hist=defaultdict(int)
    for r in rs:
        if r['tick']>=LAST:
            hist[(r['room'],r['x'],r['y'])]+=1
    top=sorted(hist.items(), key=lambda kv:-kv[1])[:6]
    p(f"  since_last pos {top}")

p("\n=== HOME upgraders since LAST-400 ===")
hups = q("""
SELECT creep, tick, ts, room, x, y, store, state
FROM creep_ticks
WHERE tick>=%s AND creep LIKE 'upgrader%%' AND creep NOT LIKE 'w8%%'
ORDER BY creep, tick
""", LAST-400)
byh=defaultdict(list)
for r in hups:
    r['e']=energy_of(r['store'])
    byh[r['creep']].append(r)
for name, rs in sorted(byh.items(), key=lambda kv: kv[1][0]['tick']):
    first,last=rs[0],rs[-1]
    near=[r for r in rs if r['room']=='W46N8' and r['x'] is not None and r['x']>=28 and r['x']<=33 and r['y']>=28 and r['y']<=32]
    first_loaded=next((r for r in near if (r['e'] or 0)>0), None)
    last_loaded=None
    for r in near:
        if (r['e'] or 0)>0:
            last_loaded=r
    p(f"{name} n={len(rs)} {first['tick']}@{first['room']} {first['x'],first['y']} -> {last['tick']}@{last['room']} {last['x'],last['y']} e={last['e']} st={last['state']}")
    if first_loaded:
        p(f"  first_loaded {first_loaded['tick']} {first_loaded['ts']} {first_loaded['x'],first_loaded['y']} e={first_loaded['e']}")
    if last_loaded:
        p(f"  last_loaded  {last_loaded['tick']} {last_loaded['ts']} {last_loaded['x'],last_loaded['y']} e={last_loaded['e']}")

# W47 progress short INTERP across freezes
p("\n=== W47/home short INTERP (fill room_stats gaps linearly) ===")
def series(room):
    return q("""
    SELECT tick, ts, progress, storage, creeps
    FROM room_stats WHERE room=%s AND tick>=%s
    ORDER BY tick
    """, room, LAST-800)

def interp_rate(rows, last_n, tip):
    # use wall-clock and also tick-span last_n ticks from tip, interpolating across gaps
    if not rows:
        return None
    tip_row=rows[-1]
    target=tip_row['tick']-last_n
    # find brackets around target
    before=None; after=None
    for r in rows:
        if r['tick']<=target:
            before=r
        elif after is None:
            after=r
            break
    if before is None:
        return {'note':'no before', 'first':rows[0]['tick'], 'span_raw':tip_row['tick']-rows[0]['tick']}
    if before['tick']==target or after is None:
        p0=before['progress']; t0=before['tick']; stor0=before['storage']
    else:
        frac=(target-before['tick'])/(after['tick']-before['tick'])
        p0=before['progress']+frac*(after['progress']-before['progress'])
        t0=target
        stor0=before['storage']+frac*((after['storage'] or 0)-(before['storage'] or 0))
    dt=tip_row['tick']-t0
    dprog=tip_row['progress']-p0
    et=dprog/dt if dt else None
    return dict(t0=t0, p0=p0, stor0=stor0, tip=tip_row['tick'], p1=tip_row['progress'], stor1=tip_row['storage'], dt=dt, dprog=dprog, et=et,
                raw_span=tip_row['tick']-rows[-min(len(rows),5)]['tick'], n_samples=sum(1 for r in rows if r['tick']>=t0))

IDEAL={'W46N8':26.0,'W47N8':30.08}
for room in ('W46N8','W47N8'):
    rows=series(room)
    p(f"-- {room} samples since LAST-800: {len(rows)} first={rows[0]['tick'] if rows else None} last={rows[-1]['tick'] if rows else None}")
    # raw gaps
    gaps=[]
    for a,b in zip(rows, rows[1:]):
        if b['tick']-a['tick']>15:
            et=(b['progress']-a['progress'])/(b['tick']-a['tick'])
            gaps.append((a['tick'], b['tick'], b['tick']-a['tick'], str(a['ts']), str(b['ts']), round(et,2), a['storage'], b['storage']))
    p(f"  gaps>15t: {gaps}")
    for n in (20,30,100,200,300,500):
        r=interp_rate(rows, n, TIP)
        if not r or r.get('et') is None:
            p(f"  last{n} INTERP {r}")
            continue
        pct=100.0*r['et']/IDEAL[room]
        p(f"  last{n} INTERP {r['et']:.2f} e/t = {pct:.1f}% dt={r['dt']:.0f} t0={r['t0']:.0f} p0={r['p0']:.1f} stor {r['stor0']:.0f}->{r['stor1']} samples>t0={r['n_samples']}")

# storage detail home since last
p("\n=== HOME storage timeseries since last (all samples) ===")
for r in q("""
SELECT tick, ts, storage, energy, progress, creeps
FROM room_stats WHERE room='W46N8' AND tick>=%s ORDER BY tick
""", LAST):
    nUp=(r['creeps'] or {}).get('upgrader') if isinstance(r['creeps'], dict) else None
    p(f"  {r['tick']} {r['ts']} stor={r['storage']} ea={r['energy']} p={r['progress']} nUp={nUp}")

p("\n=== W47 storage / w8up / hostiles since last ===")
for r in q("""
SELECT tick, ts, storage, energy, progress, hostiles, creeps
FROM room_stats WHERE room='W47N8' AND tick>=%s ORDER BY tick
""", LAST):
    c=r['creeps'] or {}
    nUp=c.get('w8upgrader') if isinstance(c, dict) else None
    p(f"  {r['tick']} {r['ts']} stor={r['storage']} host={r['hostiles']} p={r['progress']} nUp={nUp} ea={r['energy']}")

# reservers
p("\n=== reservers / reserve7 trajectories since LAST-200 ===")
for r in q("""
SELECT creep, role, room, min(tick) a, max(tick) b, count(*) n,
       (array_agg(x ORDER BY tick))[1] x0, (array_agg(y ORDER BY tick))[1] y0,
       (array_agg(x ORDER BY tick DESC))[1] x1, (array_agg(y ORDER BY tick DESC))[1] y1,
       (array_agg(store ORDER BY tick DESC))[1] store1
FROM creep_ticks
WHERE tick>=%s AND (role IN ('reserver','reserve7','reserve') OR creep ILIKE 'reserv%%')
GROUP BY 1,2,3
ORDER BY a, creep
""", LAST-200):
    p(r)

# per-tick presence of reservers in each remote
p("\n=== reserver presence gaps by room (creep_ticks) LAST..TIP ===")
for room in ('W45N8','W45N7','W47N7'):
    rows=q("""
    SELECT tick, count(DISTINCT creep) n
    FROM creep_ticks
    WHERE tick>=%s AND tick<=%s AND room=%s
      AND (role IN ('reserver','reserve7','reserve') OR creep ILIKE 'reserv%%')
    GROUP BY tick ORDER BY tick
    """, LAST, TIP, room)
    ticks=set(r['tick'] for r in rows)
    # expected official/live ticks that exist in room
    allticks=[r['tick'] for r in q("SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick>=%s AND tick<=%s ORDER BY 1", room, LAST, TIP)]
    missing_our=[]
    zero_runs=[]
    prev=None
    for t in allticks:
        has = t in ticks
        if not has:
            if prev and prev[1]==t-1:
                prev=(prev[0], t)
            else:
                if prev: zero_runs.append(prev)
                prev=(t,t)
        else:
            if prev:
                zero_runs.append(prev); prev=None
    if prev: zero_runs.append(prev)
    p(f"  {room} ticks_with_reserver={len(rows)} room_ticks={len(allticks)} zero_runs(on existing ticks)={[(a,b,b-a+1) for a,b in zero_runs if b-a+1>=20]}")

# CPU
p("\n=== CPU since last and 1h/2h ===")
for label, lo in (("since_last", LAST), ("1h", TIP-850), ("2h", TIP-1700)):
    r=q("""
    SELECT count(*) n, min(cpu) mn, max(cpu) mx, avg(cpu) av,
           percentile_cont(0.95) WITHIN GROUP (ORDER BY cpu) p95,
           min(bucket) bmin, max(bucket) bmax,
           min(tick) t0, max(tick) t1
    FROM room_stats WHERE room='W46N8' AND tick>=%s AND cpu IS NOT NULL
    """, lo)[0]
    # max tick of max cpu
    mx=q("""
    SELECT tick, ts, cpu, bucket FROM room_stats
    WHERE room='W46N8' AND tick>=%s AND cpu IS NOT NULL
    ORDER BY cpu DESC, tick DESC LIMIT 3
    """, lo)
    p(f"  {label} n={r['n']} min={r['mn']:.2f} max={r['mx']:.2f} avg={r['av']:.2f} p95={r['p95']:.2f} bkt {r['bmin']}..{r['bmax']} ticks {r['t0']}..{r['t1']}")
    p(f"    top {mx}")

# W46N8 hole 84292001-84292100 coverage
p("\n=== W46N8 official hole 84292001-84292100 live coverage ===")
r=q("""
SELECT count(*) n, count(DISTINCT tick) dt, min(tick), max(tick)
FROM creep_ticks WHERE room='W46N8' AND tick BETWEEN 84292001 AND 84292100
""")[0]
p(r)
# any rooms have those ticks?
for r in q("""
SELECT room, count(DISTINCT tick) dt, min(tick), max(tick)
FROM creep_ticks WHERE tick BETWEEN 84292001 AND 84292100
GROUP BY room ORDER BY 1
"""):
    p(f"  {r}")

# miner 91793 path - was it stand wait?
p("\n=== miner84291793 positions ===")
for r in q("""
SELECT tick, ts, room, x, y, store, state
FROM creep_ticks WHERE creep='miner84291793' ORDER BY tick
LIMIT 8
"""):
    p(r)
p("...")
for r in q("""
SELECT tick, ts, room, x, y, store, state
FROM creep_ticks WHERE creep='miner84291793' ORDER BY tick DESC LIMIT 5
"""):
    p(r)
# stand counts
pos=q("""
SELECT x,y,count(*) n, min(tick), max(tick) FROM creep_ticks
WHERE creep='miner84291793' GROUP BY 1,2 ORDER BY n DESC
""")
p(f"  pos hist {pos}")

# defender/guard presence
p("\n=== defender/guard/rdef since LAST-2000 ===")
for r in q("""
SELECT creep, role, room, min(tick) a, max(tick) b, count(*) n,
       (array_agg(x ORDER BY tick DESC))[1] x1, (array_agg(y ORDER BY tick DESC))[1] y1,
       (array_agg(hits ORDER BY tick DESC))[1] hits1
FROM creep_ticks
WHERE tick>=%s AND (role IN ('defender','w8defender','w8guard','rdef','guard') OR creep ILIKE '%%defender%%' OR creep ILIKE '%%guard%%' OR creep ILIKE 'rdef%%')
GROUP BY 1,2,3
ORDER BY a
""", LAST-2000):
    p(r)

# latest live hostiles after tip? room_stats latest W47
p("\n=== latest 8 room_stats both rooms ===")
for r in q("""
SELECT tick, ts, room, storage, hostiles, progress, energy, cpu, bucket, creeps
FROM room_stats WHERE room IN ('W46N8','W47N8')
ORDER BY tick DESC, room LIMIT 16
"""):
    p(f"  {r['room']} {r['tick']} {r['ts']} stor={r['storage']} host={r['hostiles']} p={r['progress']} ea={r['energy']} cpu={r['cpu']} b={r['bucket']} creeps={r['creeps']}")

open(OUT,"w").write("\n".join(lines)+"\n")
p(f"\nWROTE {OUT}")
