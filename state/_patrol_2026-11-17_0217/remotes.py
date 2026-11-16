#!/usr/bin/env python3
import sys
from collections import defaultdict
from zoneinfo import ZoneInfo
sys.path.insert(0, '/workspace/screeps/tools')
import db
HK = ZoneInfo('Asia/Hong_Kong')
c = db.connect()
LAST_TIP = 84307830  # previous 1h patrol analysis TIP (01:25)
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

p('=== W47 upgrader TTL handoffs predicted this hour (06521 then 06585) ===')
for name in ('w8upgrader84306521','w8upgrader84306585'):
    row=c.execute("SELECT min(tick),max(tick),max(tick) FILTER (WHERE store>0) FROM creep_ticks WHERE creep=%s",(name,)).fetchone()
    p(name, 'span', row)
    if row and row[1]:
        path(name, max(row[0] or LAST_TIP-50, LAST_TIP-200), min((row[1] or TIP)+20, TIP+80))

p('=== home upgraders 07067 / 07459 this hour ===')
for name in ('upgrader84307067','upgrader84307459'):
    row=c.execute("SELECT min(tick),max(tick),max(tick) FILTER (WHERE store>0) FROM creep_ticks WHERE creep=%s",(name,)).fetchone()
    p(name, 'span', row)
    if row and row[1]:
        path(name, max(row[0] or LAST_TIP-50, LAST_TIP-50), min((row[1] or TIP)+20, TIP+80))

p('=== reserver84307839 (W45N7 replacement, still in W46N8 at last tip) ===')
path('reserver84307839', LAST_TIP-50, TIP+80)

p('=== W47N7 reserve784307526 (seated ttl~288 at last tip) ===')
row=c.execute("SELECT min(tick),max(tick) FROM creep_ticks WHERE creep=%s",('reserve784307526',)).fetchone()
p('7526 span', row)
path('reserve784307526', LAST_TIP-50, TIP+80)

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

p('=== upgrader presence this hour (any recycle?) ===')
rows=c.execute("""
SELECT creep, min(tick), max(tick),
       (ARRAY_AGG(x ORDER BY tick DESC))[1],
       (ARRAY_AGG(y ORDER BY tick DESC))[1],
       (ARRAY_AGG(store ORDER BY tick DESC))[1],
       (ARRAY_AGG(state ORDER BY tick DESC))[1]
FROM creep_ticks
WHERE role IN ('upgrader','wupgrader','w8upgrader') AND tick BETWEEN %s AND %s
GROUP BY creep ORDER BY min(tick)
""", (LAST_TIP-50, TIP+80)).fetchall()
for r in rows:
    p('upg', r)

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

p('=== W47 upgrader hub-wait tiles this hour (06521/06585 and replacements) ===')
names=[r[0] for r in c.execute("""
SELECT DISTINCT creep FROM creep_ticks
WHERE role IN ('wupgrader','w8upgrader') AND tick BETWEEN %s AND %s
ORDER BY 1
""", (LAST_TIP-50, TIP+80)).fetchall()]
for name in names:
    rows=c.execute("SELECT tick,ts,x,y,state,room FROM creep_ticks WHERE creep=%s AND tick BETWEEN %s AND %s ORDER BY tick",(name, LAST_TIP-50, TIP+80)).fetchall()
    p(f'-- hubwait {name} n={len(rows)} --')
    prev=None; n=0
    for r in rows:
        key=(r[5],r[2],r[3],r[4])
        if prev is None:
            prev=(r,key); n=1
        elif key==prev[1]:
            n+=1
        else:
            a=prev[0]
            if n>=20 or (a[5]=='W47N8' and (a[2],a[3]) not in ((14,26),(14,27),(13,26),(13,27),(15,26),(15,27))):
                p(f'  {name} {a[0]}-{r[0]-1} n={n} {a[5]} {a[2]},{a[3]} st={a[4]} {ts(a[1])}')
            prev=(r,key); n=1
    if prev:
        a=prev[0]
        p(f'  {name} {a[0]}-end n={n} {a[5]} {a[2]},{a[3]} st={a[4]} {ts(a[1])} last={rows[-1][0] if rows else None}')

p('=== freshness now ===')
for table in ('room_stats','creep_ticks','creep_cpu'):
    row=c.execute(f'SELECT max(tick), now()-max(ts) FROM {table}').fetchone()
    p(table, row)

p('DONE')
