#!/usr/bin/env python3
import sys
sys.path.insert(0, '/workspace/screeps/tools')
import db

ROOMS = ('W46N8','W47N8','W45N8','W45N7','W47N7')
FREEZE_LO, FREEZE_HI = 84422041, 84422319
LAST_TIP, NOW_LO = 84421700, 84421901

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
print('=== official fill freeze STATS %d..%d (%d t) ===' % (FREEZE_LO, FREEZE_HI, FREEZE_HI-FREEZE_LO+1))
for room in ROOMS:
    rows=c.execute('SELECT COUNT(DISTINCT tick), MIN(tick), MAX(tick), COUNT(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s', (room, FREEZE_LO, FREEZE_HI)).fetchone()
    d,mn,mx,n=rows
    want=FREEZE_HI-FREEZE_LO+1
    print('  %s fill=%s/%s rows=%s range=%s..%s' % (room, d, want, n, mn, mx))
print('room_stats in freeze:')
rs=c.execute("SELECT MIN(tick), MAX(tick), COUNT(*) FROM room_stats WHERE room='W46N8' AND tick BETWEEN %s AND %s", (FREEZE_LO, FREEZE_HI)).fetchone()
print('  W46N8 room_stats', rs)

print('=== W45N8 404 holes listener vs official ===')
for lo,hi,label in [(84422101,84422200,'W45N8@84422100'), (84422401,84422500,'W45N8@84422400')]:
    for room in ('W45N8',):
        rows=c.execute('SELECT COUNT(DISTINCT tick), MIN(tick), MAX(tick), COUNT(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s', (room, lo, hi)).fetchone()
        print('  %s %s distinct=%s rows=%s range=%s..%s want=100 missing=%s' % (label, room, rows[0], rows[3], rows[1], rows[2], 100-(rows[0] or 0)))
        ticks=[r[0] for r in c.execute('SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s ORDER BY 1', (room, lo, hi))]
        print('    spans missing', spans(ticks, lo, hi)[:8], 'present_n', len(ticks))

print('=== storage / progress / nUp last hour (room_stats deciles) ===')
for room in ('W46N8','W47N8'):
    print('--', room, '--')
    rows=c.execute('SELECT tick, ts, storage, progress, cpu, bucket, hostiles, energy, creeps FROM room_stats WHERE room=%s AND tick>=%s ORDER BY tick' % ('%s','%s'), (room, LAST_TIP)).fetchall() if False else c.execute('SELECT tick, ts, storage, progress, cpu, bucket, hostiles, energy, creeps FROM room_stats WHERE room=%s AND tick>=%s ORDER BY tick', (room, LAST_TIP)).fetchall()
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
        print('  under15k n', len(under), 'ticks', [(r[0], r[2], str(r[1])) for r in under[:12]], ('...' if len(under)>12 else ''))
    # print every ~10th plus last few
    for r in rows:
        if r[0] % 50 == 0 or r is rows[-1] or r is rows[0]:
            print('  ', r[0], r[1], 'stor', r[2], 'prog', r[3], 'cpu', r[4], 'bkt', r[5], 'host', r[6], 'e', r[7], 'cr', r[8])

print('=== CPU 1h from room_stats W46N8 since LAST_TIP ===')
rows=c.execute("SELECT tick, ts, cpu, bucket FROM room_stats WHERE room='W46N8' AND tick>=%s AND cpu IS NOT NULL ORDER BY tick", (LAST_TIP,)).fetchall()
if rows:
    cpus=[r[2] for r in rows]
    print('  n', len(rows), 'mean', sum(cpus)/len(cpus), 'max', max(cpus), 'at', rows[cpus.index(max(cpus))][0], rows[cpus.index(max(cpus))][1], 'min_bucket', min(r[3] for r in rows if r[3] is not None))

print('=== room_stats gaps since LAST_TIP (len>=11) ===')
ticks=[r[0] for r in c.execute("SELECT tick FROM room_stats WHERE room='W46N8' AND tick>=%s ORDER BY 1", (LAST_TIP,))]
print('  n', len(ticks), 'range', ticks[0] if ticks else None, ticks[-1] if ticks else None)
print('  long gaps', [s for s in spans(ticks, ticks[0], ticks[-1]) if s[2]>=11] if ticks else None)

print('=== defenders in creep_ticks around incident ===')
rows=c.execute("""SELECT name, room, MIN(tick), MAX(tick), COUNT(*), MIN(hits), MAX(hits) FROM creep_ticks WHERE name LIKE 'rdef%' AND tick>=84422400 GROUP BY 1,2 ORDER BY 1,2""").fetchall()
for r in rows: print(' ', r)

print('DONE')
