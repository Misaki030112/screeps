#!/usr/bin/env python3
"""This-hour deep traces: park-when-full, handoffs, remotes, threat, coverage."""
import sys, json
from collections import defaultdict, Counter
sys.path.insert(0, '/workspace/screeps/tools')
import db

LAST_TIP = 84333710
DEPLOY = 84334122  # 289a7f06 park-when-full
c = db.connect()

def p(*a):
    print(*a)

p('=== freshness ===')
for table in ('room_stats','creep_ticks','creep_cpu'):
    p(table, c.execute(f'SELECT min(tick), max(tick), max(ts), now()-max(ts), count(*) FROM {table}').fetchone())

p('=== creep_ticks coverage since LAST_TIP ===')
for r in c.execute('''
  SELECT room, min(tick), max(tick), count(*), count(distinct tick)
  FROM creep_ticks WHERE tick > %s
  GROUP BY room ORDER BY room
''', (LAST_TIP,)):
    p('cov', r)

# holes in official 5 rooms between LAST_TIP+1 and 84334400
p('=== holes LAST_TIP+1..84334400 (official 100t chunks with 0 rows) ===')
for room in ('W46N8','W47N8','W45N8','W45N7','W47N7'):
    rows = c.execute('SELECT distinct tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s',
                     (room, LAST_TIP+1, 84334400)).fetchall()
    have = {t[0] for t in rows}
    missing = [t for t in range(LAST_TIP+1, 84334401) if t not in have]
    # compress
    spans=[]
    for t in missing:
        if spans and t==spans[-1][1]+1: spans[-1][1]=t
        else: spans.append([t,t])
    p(room, 'have', len(have), 'missing', len(missing), 'spans', spans[:20], ('...' if len(spans)>20 else ''))

p('=== room_stats tip + later ===')
for room in ('W46N8','W47N8'):
    p(room, 'tip+', c.execute('''
      SELECT tick, ts, progress, storage, cpu, bucket, commit, hostiles, sites, creeps
      FROM room_stats WHERE room=%s AND tick>=%s ORDER BY tick
    ''', (room, LAST_TIP-20)).fetchall()[-8:])

p('=== W47 upgrader identities since LAST_TIP-200 ===')
for r in c.execute('''
  SELECT creep, min(tick), max(tick), min(x), max(x), min(y), max(y),
         count(*), count(*) FILTER (WHERE energy>0) AS loaded,
         (array_agg(x||','||y ORDER BY tick))[1] AS first_xy,
         (array_agg(x||','||y ORDER BY tick DESC))[1] AS last_xy,
         (array_agg(room ORDER BY tick))[1] AS first_rm,
         (array_agg(room ORDER BY tick DESC))[1] AS last_rm
  FROM creep_ticks
  WHERE (role='w8upgrader' OR creep LIKE 'w8upgrader%') AND tick>=%s
  GROUP BY creep ORDER BY min(tick)
''', (LAST_TIP-200,)):
    p('w8up', r)

# detailed seat/leave for each current-hour upgrader
p('=== W47 upgrader seat/leave (loaded at controller tiles) ===')
for name, in c.execute('''
  SELECT distinct creep FROM creep_ticks
  WHERE (role='w8upgrader' OR creep LIKE 'w8upgrader%') AND tick>=%s
  ORDER BY creep
''', (LAST_TIP-200,)):
    rows = c.execute('''
      SELECT tick, room, x, y, energy, spawning, say
      FROM creep_ticks WHERE creep=%s AND tick>=%s ORDER BY tick
    ''', (name, LAST_TIP-200)).fetchall()
    if not rows:
        continue
    first, last = rows[0], rows[-1]
    loaded = [r for r in rows if (r[4] or 0)>0]
    # controller-adjacent seats typically 12,25 14,26 14,27 12,26 etc
    seats = [r for r in loaded if r[1]=='W47N8' and r[2] in (12,13,14,15) and r[3] in (24,25,26,27,28)]
    p(name, 'n', len(rows), 'first', first[:6], 'last', last[:6],
      'first_loaded', (loaded[0][:6] if loaded else None),
      'last_loaded', (loaded[-1][:6] if loaded else None),
      'first_seat', (seats[0][:6] if seats else None),
      'n_seat', len(seats))
    # print walk from spawn/hatch to first seat if any
    if seats:
        t0 = rows[0][0]
        tseat = seats[0][0]
        walk = [r for r in rows if r[0] <= tseat][:80]
        # compact path
        path=[]
        for r in walk:
            xy=(r[1],r[2],r[3],r[4])
            if not path or path[-1][0]!=xy:
                path.append((xy, r[0], 1))
            else:
                path[-1] = (xy, path[-1][1], path[-1][2]+1)
        p('  path_to_seat', path)

p('=== HOME upgrader identities since LAST_TIP-200 ===')
for r in c.execute('''
  SELECT creep, min(tick), max(tick),
         (array_agg(x||','||y ORDER BY tick))[1] AS first_xy,
         (array_agg(x||','||y ORDER BY tick DESC))[1] AS last_xy,
         count(*), count(*) FILTER (WHERE energy>0) AS loaded
  FROM creep_ticks
  WHERE role='upgrader' AND tick>=%s
  GROUP BY creep ORDER BY min(tick)
''', (LAST_TIP-200,)):
    p('up', r)

p('=== nUp / w8up from room_stats creeps json since LAST_TIP-50 ===')
# creeps column may be json/text
sample = c.execute("SELECT creeps FROM room_stats WHERE room='W46N8' AND tick>=%s LIMIT 1", (LAST_TIP,)).fetchone()
p('creeps sample type', type(sample[0]).__name__, str(sample[0])[:300] if sample else None)

p('=== w8filler identities and park/ABA after deploy ===')
for r in c.execute('''
  SELECT creep, min(tick), max(tick),
         (array_agg(x||','||y ORDER BY tick))[1],
         (array_agg(x||','||y ORDER BY tick DESC))[1],
         count(*), count(*) FILTER (WHERE energy>0 AND energy>= (CASE WHEN 1=1 THEN 0 ELSE 0 END))
  FROM creep_ticks
  WHERE (role='w8filler' OR creep LIKE 'w8filler%') AND tick>=%s
  GROUP BY creep ORDER BY min(tick)
''', (LAST_TIP-400,)):
    p('wf', r)

# post-deploy per-tick filler motion (positions, energy, say)
p('=== w8filler POST-DEPLOY', DEPLOY, 'position dwell ===')
for name, in c.execute('''
  SELECT distinct creep FROM creep_ticks
  WHERE (role='w8filler' OR creep LIKE 'w8filler%') AND tick>=%s
  ORDER BY creep
''', (DEPLOY,)):
    rows = c.execute('''
      SELECT tick, x, y, energy, spawning, say
      FROM creep_ticks WHERE creep=%s AND room='W47N8' AND tick>=%s ORDER BY tick
    ''', (name, DEPLOY)).fetchall()
    if not rows:
        p(name, 'no W47N8 rows after deploy')
        continue
    dwell=Counter(); moves=0; prev=None
    full_stand=0; bounce=0
    path=[]
    for t,x,y,e,sp,say in rows:
        dwell[(x,y)] += 1
        if prev and (prev[0],prev[1])!=(x,y):
            moves += 1
            # ABA bounce
        if prev and prev[2] and prev[2]>=50 and (prev[0],prev[1])!=(x,y):
            bounce += 1
        if e and e>=50 and prev and (prev[0],prev[1])==(x,y):
            full_stand += 1
        xy=(x,y,e)
        if not path or path[-1][0]!=(x,y,e):
            path.append(((x,y,e), t, 1, say))
        else:
            path[-1] = (path[-1][0], path[-1][1], path[-1][2]+1, say)
        prev=(x,y,e)
    p(name, 'n', len(rows), 'ticks', rows[0][0], '..', rows[-1][0],
      'moves', moves, 'full_stand', full_stand, 'moves_while_fullish', bounce,
      'dwell_top', dwell.most_common(8))
    p('  last', rows[-1], 'path_changes', len(path))
    # print compact path if not huge
    if len(path)<=40:
        p('  path', path)
    else:
        p('  path_head', path[:12])
        p('  path_tail', path[-12:])

p('=== w8guard / w8defender this hour ===')
for role in ('w8guard','w8defender','wdefender','wguard','rdef','defender'):
    for r in c.execute('''
      SELECT creep, role, min(tick), max(tick),
             (array_agg(room||':'||x||','||y ORDER BY tick))[1],
             (array_agg(room||':'||x||','||y ORDER BY tick DESC))[1],
             count(*)
      FROM creep_ticks
      WHERE (role=%s OR creep LIKE %s) AND tick>=%s
      GROUP BY creep, role ORDER BY min(tick)
    ''', (role, role+'%', LAST_TIP-300,)):
        p(role, r)

p('=== remotes reservation / hostiles from room_stats if present ===')
# inspect room_stats columns
cols = [x[0] for x in c.execute("SELECT column_name FROM information_schema.columns WHERE table_name='room_stats' ORDER BY ordinal_position")]
p('room_stats cols', cols)

p('=== hostile/sites/storage/host since LAST_TIP for remotes and owned ===')
for room in ('W46N8','W47N8','W45N8','W45N7','W47N7'):
    rows = c.execute('''
      SELECT min(tick), max(tick), min(storage), max(storage), max(hostiles), max(sites), count(*)
      FROM room_stats WHERE room=%s AND tick>=%s
    ''', (room, LAST_TIP-10)).fetchone()
    p('rs', room, rows)
    # any hostiles>0
    hs = c.execute('''
      SELECT tick, ts, hostiles, sites, storage FROM room_stats
      WHERE room=%s AND tick>=%s AND (hostiles>0 OR sites>0)
      ORDER BY tick
    ''', (room, LAST_TIP-400)).fetchall()
    if hs:
        p('  host/sites samples', hs[:15], 'n', len(hs))

p('=== reserver / reserve7 identities since LAST_TIP-400 ===')
for rolepat, like in (('reserver','reserver%'), ('reserve7','reserve7%'), ('reserve','reserve%')):
    for r in c.execute('''
      SELECT creep, role, min(tick), max(tick),
             (array_agg(room||':'||x||','||y ORDER BY tick))[1],
             (array_agg(room||':'||x||','||y ORDER BY tick DESC))[1],
             count(*)
      FROM creep_ticks
      WHERE (role=%s OR creep LIKE %s) AND tick>=%s
      GROUP BY creep, role ORDER BY min(tick)
    ''', (rolepat, like, LAST_TIP-400,)):
        p(rolepat, r)

p('=== critical role presence gaps since LAST_TIP (owned+remote) ===')
# for each wanted role, ticks where count==0 in any of the rooms
wanted = ['miner','rminer','reserver','queen','w8filler','w8miner','w8rminer']
# use 10-tick buckets of distinct creeps
for role in wanted:
    rows = c.execute('''
      SELECT tick, count(distinct creep) FROM creep_ticks
      WHERE role=%s AND tick BETWEEN %s AND %s
      GROUP BY tick ORDER BY tick
    ''', (role, LAST_TIP, 84334400)).fetchall()
    if not rows:
        p(role, 'NO ROWS in window')
        continue
    have = {t:n for t,n in rows}
    zeros=[]
    for t in range(LAST_TIP, 84334401):
        n=have.get(t,0)
        if n==0:
            if zeros and t==zeros[-1][1]+1: zeros[-1][1]=t
            else: zeros.append([t,t])
    p(role, 'ticks_present', len(rows), 'zero_spans', zeros[:10], 'nspans', len(zeros),
      'max_zero', max((b-a+1 for a,b in zeros), default=0))

p('=== W47 / home storage series this hour (every ~50t shown via min/max windows) ===')
for room in ('W46N8','W47N8'):
    rows=c.execute('''
      SELECT tick, ts, storage, progress, cpu, bucket, commit
      FROM room_stats WHERE room=%s AND tick>=%s ORDER BY tick
    ''', (room, LAST_TIP)).fetchall()
    p(room, 'n', len(rows))
    if rows:
        p('  first', rows[0])
        p('  last', rows[-1])
        stor=[r[2] for r in rows if r[2] is not None]
        if stor:
            imin=min(range(len(rows)), key=lambda i: rows[i][2] if rows[i][2] is not None else 10**18)
            imax=max(range(len(rows)), key=lambda i: rows[i][2] if rows[i][2] is not None else -1)
            p('  min', rows[imin], 'max', rows[imax])
        # print every 10th
        for r in rows[::10]:
            p('  ', r[0], str(r[1])[11:19], 'stor', r[2], 'p', r[3], 'cpu', r[4], 'cmt', r[6])

p('=== commits seen this hour ===')
for r in c.execute('''
  SELECT commit, min(tick), max(tick), count(*)
  FROM room_stats WHERE tick>=%s AND commit is not null
  GROUP BY commit ORDER BY min(tick)
''', (LAST_TIP-200,)):
    p('cmt', r)

p('=== box freezes: room_stats gaps this hour ===')
rows=c.execute('''
  SELECT tick, ts FROM room_stats WHERE room='W46N8' AND tick>=%s ORDER BY tick
''', (LAST_TIP-200,)).fetchall()
prev=None
gaps=[]
for t,ts in rows:
    if prev:
        dt=t-prev[0]
        if dt>15:  # >~1.5 samples if 10t cadence
            gaps.append((prev[0], t, dt, prev[1], ts, (ts-prev[1]).total_seconds() if ts and prev[1] else None))
    prev=(t,ts)
p('gaps n', len(gaps))
for g in gaps:
    p('  gap', g)

p('=== miners / w8miners seats ===')
for role in ('miner','w8miner','w8rminer','rminer','w8mminer'):
    for r in c.execute('''
      SELECT creep, role, min(tick), max(tick),
             (array_agg(room||':'||x||','||y ORDER BY tick DESC))[1],
             count(*)
      FROM creep_ticks WHERE role=%s AND tick>=%s
      GROUP BY creep, role ORDER BY min(tick)
    ''', (role, LAST_TIP,)):
        p(role, r)

p('done')
