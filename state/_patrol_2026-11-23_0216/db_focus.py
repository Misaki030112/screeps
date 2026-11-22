#!/usr/bin/env python3
import sys
sys.path.insert(0, '/workspace/screeps/tools')
import db

ROOMS = ('W46N8','W47N8','W45N8','W45N7','W47N7')
# NEW freeze this hour (not yet told)
FREEZE_LO, FREEZE_HI = 84422871, 84423199
# already-told freeze still overlapping older window
OLD_FREEZE_LO, OLD_FREEZE_HI = 84422041, 84422319
LAST_TIP = 84422700
AGED_404 = [
    ('W45N8', 84422101, 84422200, 'W45N8@84422100'),
    ('W45N8', 84422401, 84422500, 'W45N8@84422400'),
]

def spans(ticks, lo, hi):
    s=set(ticks); miss=[]; start=None
    for t in range(lo, hi+1):
        if t not in s:
            if start is None: start=t
        elif start is not None:
            miss.append((start, t-1, t-start)); start=None
    if start is not None: miss.append((start, hi, hi-start+1))
    return miss

c = db.connect()
print('=== official fill NEW freeze STATS %d..%d (%d t) ===' % (FREEZE_LO, FREEZE_HI, FREEZE_HI-FREEZE_LO+1))
for room in ROOMS:
    d,mn,mx,n=c.execute('SELECT COUNT(DISTINCT tick), MIN(tick), MAX(tick), COUNT(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s', (room, FREEZE_LO, FREEZE_HI)).fetchone()
    want=FREEZE_HI-FREEZE_LO+1
    miss=spans([r[0] for r in c.execute('SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s', (room, FREEZE_LO, FREEZE_HI))], FREEZE_LO, FREEZE_HI)
    print('  %s fill=%s/%s rows=%s range=%s..%s missing=%s' % (room, d, want, n, mn, mx, miss[:8]))
print('room_stats in NEW freeze:')
for room in ('W46N8','W47N8'):
    rs=c.execute('SELECT MIN(tick), MAX(tick), COUNT(*) FROM room_stats WHERE room=%s AND tick BETWEEN %s AND %s', (room, FREEZE_LO, FREEZE_HI)).fetchone()
    print('  %s room_stats' % room, rs)

print('=== already-told freeze 21:45 fill (do not re-tell) ===')
for room in ROOMS:
    d,mn,mx,n=c.execute('SELECT COUNT(DISTINCT tick), MIN(tick), MAX(tick), COUNT(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s', (room, OLD_FREEZE_LO, OLD_FREEZE_HI)).fetchone()
    want=OLD_FREEZE_HI-OLD_FREEZE_LO+1
    print('  %s fill=%s/%s rows=%s range=%s..%s' % (room, d, want, n, mn, mx))

print('=== aged leftover 404 holes (already told) ===')
for room, lo, hi, label in AGED_404:
    d,mn,mx,n=c.execute('SELECT COUNT(DISTINCT tick), MIN(tick), MAX(tick), COUNT(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s', (room, lo, hi)).fetchone()
    print('  %s distinct=%s rows=%s range=%s..%s want=%s missing=%s' % (label, d, n, mn, mx, hi-lo+1, (hi-lo+1)-(d or 0)))

print('=== W45N7 official-empty 84422802..84422823 ===')
lo,hi=84422802,84422823
for room in ROOMS:
    d,n=c.execute('SELECT COUNT(DISTINCT tick), COUNT(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s', (room, lo, hi)).fetchone()
    print('  %s distinct=%s rows=%s want=%s' % (room, d, n, hi-lo+1))

print('=== storage / progress last hour (since LAST_TIP) ===')
for room in ('W46N8','W47N8'):
    print('--', room, '--')
    rows=c.execute('SELECT tick, ts, storage, progress, cpu, bucket, hostiles, energy, creeps FROM room_stats WHERE room=%s AND tick>=%s ORDER BY tick', (room, LAST_TIP)).fetchall()
    print('  n', len(rows), 'min_t', rows[0][0] if rows else None, 'max_t', rows[-1][0] if rows else None)
    if not rows: continue
    stor=[r[2] for r in rows if r[2] is not None]
    if stor:
        imin=min(range(len(rows)), key=lambda i: rows[i][2] if rows[i][2] is not None else 10**9)
        imax=max(range(len(rows)), key=lambda i: rows[i][2] if rows[i][2] is not None else -1)
        print('  stor min', rows[imin][2], 'tick', rows[imin][0], 'ts', rows[imin][1])
        print('  stor max', rows[imax][2], 'tick', rows[imax][0], 'ts', rows[imax][1])
        print('  stor first', rows[0][2], 'tick', rows[0][0], 'last', rows[-1][2], 'tick', rows[-1][0])
        under=[r for r in rows if r[2] is not None and r[2]<15000]
        print('  under15k n', len(under), 'first', under[0][:3] if under else None, 'last', under[-1][:3] if under else None)
        over40=[r for r in rows if r[2] is not None and r[2]>=40000]
        print('  over40k n', len(over40), 'first', over40[0][:3] if over40 else None)
    for r in rows:
        if r[0] % 50 == 0 or r is rows[-1] or r is rows[0]:
            print('  ', r[0], r[1], 'stor', r[2], 'prog', r[3], 'cpu', r[4], 'bkt', r[5], 'host', r[6], 'e', r[7], 'cr', r[8])

print('=== CPU since LAST_TIP and last 2h ===')
for label, lo in (('since_last', LAST_TIP), ('2h_approx', LAST_TIP-900)):
    rows=c.execute("SELECT tick, ts, cpu, bucket FROM room_stats WHERE room='W46N8' AND tick>=%s AND cpu IS NOT NULL ORDER BY tick", (lo,)).fetchall()
    if not rows: continue
    cpus=[r[2] for r in rows]
    mx=max(cpus); im=cpus.index(mx)
    bks=[r[3] for r in rows if r[3] is not None]
    print('  %s n=%s mean=%.2f max=%.2f at %s %s min_bucket=%s last_cpu=%.2f last_bkt=%s t=%s..%s' % (
        label, len(rows), sum(cpus)/len(cpus), mx, rows[im][0], rows[im][1], min(bks) if bks else None,
        cpus[-1], rows[-1][3], rows[0][0], rows[-1][0]))

print('=== room_stats gaps since LAST_TIP (len>=11) ===')
ticks=[r[0] for r in c.execute("SELECT tick FROM room_stats WHERE room='W46N8' AND tick>=%s ORDER BY 1", (LAST_TIP,))]
print('  n', len(ticks), 'range', ticks[0] if ticks else None, ticks[-1] if ticks else None)
print('  long gaps', [s for s in spans(ticks, ticks[0], ticks[-1]) if s[2]>=11] if ticks else None)

print('=== defenders since 84422400 ===')
rows=c.execute("""SELECT name, room, MIN(tick), MAX(tick), COUNT(*), MIN(hits), MAX(hits) FROM creep_ticks WHERE name LIKE 'rdef%' AND tick>=84422400 GROUP BY 1,2 ORDER BY 1,2""").fetchall()
for r in rows: print(' ', r)

print('=== incidents since LAST_TIP ===')
try:
    rows=c.execute('SELECT * FROM incidents WHERE tick>=%s ORDER BY tick', (LAST_TIP,)).fetchall()
    print('  n', len(rows))
    for r in rows[:40]:
        print(' ', r)
except Exception as e:
    print('  incidents err', type(e).__name__, e)

print('=== console/events errors since LAST_TIP if table exists ===')
for table in ('events','console_events','alerts'):
    try:
        cols=c.execute("SELECT column_name FROM information_schema.columns WHERE table_name=%s", (table,)).fetchall()
        if not cols:
            continue
        print('  table', table, 'cols', [x[0] for x in cols][:20])
    except Exception as e:
        print('  ', table, e)

print('DONE')
