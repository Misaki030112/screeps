#!/usr/bin/env python3
import sys
from collections import defaultdict
from zoneinfo import ZoneInfo
sys.path.insert(0, '/workspace/screeps/tools')
import db
HK = ZoneInfo('Asia/Hong_Kong')
c = db.connect()
LAST_TIP = 84307170  # previous 1h patrol analysis TIP (00:38)
TIP = c.execute("SELECT max(tick) FROM room_stats WHERE room='W46N8'").fetchone()[0]
print('REMOTES LAST_TIP', LAST_TIP, 'TIP', TIP, flush=True)

def ts(t):
    if t is None: return None
    return t.astimezone(HK).strftime('%Y-%m-%d %H:%M:%S')

def p(*a):
    print(*a, flush=True)

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
    prev=None; changes=0; seats=defaultdict(int); printed=0
    for i,r in enumerate(rows):
        key=(r[2],r[3],r[4],(r[5] or 0)>0,r[6])
        seats[(r[2],r[3],r[4])] += 1
        if prev is None or key!=prev[0]:
            if every or printed<20 or i==len(rows)-1:
                p(f'         @{r[0]} {ts(r[1])} {r[2]} {r[3]},{r[4]} e={r[5]} st={r[6]} hits={r[7]}')
                printed += 1
            changes += 1
            prev=(key,r)
    top=sorted(seats.items(), key=lambda kv: -kv[1])[:5]
    p(f'         top_tiles={top} changes={changes}')
    return rows

p('=== 05146 full end ===')
row=c.execute("SELECT min(tick),max(tick),max(tick) FILTER (WHERE store>0) FROM creep_ticks WHERE creep='w8upgrader84305146'").fetchone()
p('05146 span', row)
path('w8upgrader84305146', 84306500, 84306800)

p('=== 05931 around expected TTL and after official hole ===')
for lo,hi in ((84306400,84306520),(84306601,84306750),(84306900,84307180)):
    n=c.execute("SELECT count(*),min(tick),max(tick) FROM creep_ticks WHERE creep='reserver84305931' AND tick BETWEEN %s AND %s",(lo,hi)).fetchone()
    p(f'05931 {lo}..{hi}', n)
# last 15 rows of 05931 after 84306600
rows=c.execute("SELECT tick,ts,room,x,y,state FROM creep_ticks WHERE creep='reserver84305931' AND tick>=84306600 ORDER BY tick").fetchall()
p('05931 after 84306600 n', len(rows))
if rows:
    p(' first after hole', rows[0][0], ts(rows[0][1]), rows[0][2], rows[0][3], rows[0][4], rows[0][5])
    p(' last', rows[-1][0], ts(rows[-1][1]), rows[-1][2], rows[-1][3], rows[-1][4], rows[-1][5])
# ticks just before hole
rows=c.execute("SELECT tick,ts,room,x,y,state FROM creep_ticks WHERE creep='reserver84305931' AND tick BETWEEN 84306480 AND 84306500 ORDER BY tick").fetchall()
p('05931 pre-hole last samples', [(r[0],ts(r[1]),r[2],r[3],r[4],r[5]) for r in rows[-5:]])

p('=== 07005 arrival vs 05931 ===')
path('reserver84307005', 84307000, 84307180)

p('=== rminers / w8rminers this hour ===')
for role,q in (
    ('rminer', "role='rminer'"),
    ('w8rminer', "role IN ('wrminer','w8rminer')"),
    ('miner', "role='miner' AND room='W46N8'"),
    ('w8miner', "role IN ('wminer','w8miner')"),
):
    rows=c.execute(f'''
    SELECT creep, min(tick), max(tick),
           min(tick) FILTER (WHERE store>0) fl,
           max(tick) FILTER (WHERE store>0) ll,
           (ARRAY_AGG(room ORDER BY tick DESC))[1],
           (ARRAY_AGG(x ORDER BY tick DESC))[1],
           (ARRAY_AGG(y ORDER BY tick DESC))[1],
           count(*)
    FROM creep_ticks
    WHERE {q} AND tick BETWEEN %s AND %s
    GROUP BY creep ORDER BY min(tick)
    ''', (LAST_TIP-200, TIP+80)).fetchall()
    p(f'-- {role} --')
    for r in rows:
        p(role, r)
        # only path if last/first in this hour interesting
        path(r[0], max(r[1], LAST_TIP-50), min(r[2], TIP+80))

p('=== 06331 last states (recycle?) ===')
rows=c.execute("SELECT tick,ts,x,y,store,state,hits FROM creep_ticks WHERE creep='upgrader84306331' AND tick>=84306890 ORDER BY tick").fetchall()
for r in rows:
    p('06331', r[0], ts(r[1]), f'{r[2]},{r[3]}', 'e', r[4], r[5], 'h', r[6])

p('=== events since LAST_TIP ===')
cols=c.execute("SELECT column_name FROM information_schema.columns WHERE table_name='events' ORDER BY ordinal_position").fetchall()
p('events cols', [x[0] for x in cols])
rows=c.execute("SELECT * FROM events WHERE tick>=%s OR ts>=now()-interval '2 hours' ORDER BY 1 DESC LIMIT 40", (LAST_TIP,)).fetchall()
# print safely
for r in rows[:40]:
    p('EV', r)

p('=== hostiles / cores in remotes this hour (creep_ticks hostiles? room_stats) ===')
for room in ('W45N7','W45N8','W47N7','W46N8','W47N8'):
    row=c.execute("SELECT count(*) FILTER (WHERE hostiles>0), max(hostiles), min(tick), max(tick) FROM room_stats WHERE room=%s AND tick BETWEEN %s AND %s", (room, LAST_TIP, TIP)).fetchone()
    p('hostiles room_stats', room, row)

p('=== 06585 hub wait tiles 84306624..84306900 ===')
rows=c.execute("SELECT tick,ts,x,y,state FROM creep_ticks WHERE creep='w8upgrader84306585' AND tick BETWEEN 84306620 AND 84306910 ORDER BY tick").fetchall()
# compress
prev=None; n=0
for r in rows:
    key=(r[2],r[3],r[4])
    if prev is None:
        prev=(r,key); n=1
    elif key==prev[1]:
        n+=1
    else:
        a=prev[0]
        p(f'  {a[0]}-{r[0]-1} n={n} {a[2]},{a[3]} st={a[4]} {ts(a[1])}')
        prev=(r,key); n=1
if prev:
    a=prev[0]
    p(f'  {a[0]}-end n={n} {a[2]},{a[3]} st={a[4]} {ts(a[1])} last={rows[-1][0] if rows else None}')

p('=== freshness now ===')
for table in ('room_stats','creep_ticks','creep_cpu'):
    row=c.execute(f'SELECT max(tick), now()-max(ts) FROM {table}').fetchone()
    p(table, row)

p('DONE')
