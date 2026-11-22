#!/usr/bin/env python3
"""Patrol exact2h / short-window / storage / CPU / gaps analysis."""
import os, sys, json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, '/workspace/screeps/tools')
import db

HK = ZoneInfo('Asia/Hong_Kong')
SH = ZoneInfo('Asia/Shanghai')  # same offset, prior logs used this in some places
IDEAL = {'W46N8': 26.0, 'W47N8': 30.08}
LAST_TIP = 84410480  # previous 1h patrol analysis tip (08:23:24 later live/room_stats 84410550 08:28:14)
ROOMS = ['W46N8', 'W47N8']
OFFICIAL = ('W46N8', 'W47N8', 'W45N8', 'W45N7', 'W47N7')
# last 40m backfill window
BF_LO, BF_HI = 84410601, 84411300  # first-pass official window this hour, missing_chunks=1 W47N7@84411200

def connect():
    return db.connect()

def main():
    c = connect()
    out = []
    def p(*a):
        s = ' '.join(str(x) for x in a)
        out.append(s)
        print(s)

    p('=== freshness ===')
    for table in ('room_stats', 'creep_ticks', 'creep_cpu'):
        row = c.execute(f'SELECT max(tick), max(ts), now()-max(ts) FROM {table}').fetchone()
        p(table, row)

    p('--- creep_ticks per room last 40min window-ish ---')
    for r in c.execute('''
        SELECT room, max(tick), now()-max(ts), count(*)
        FROM creep_ticks
        WHERE tick >= %s
        GROUP BY room ORDER BY room
    ''', (BF_LO,)):
        p('creep_ticks', r)

    p('=== latest room_stats ===')
    tips = {}
    for room in ROOMS:
        row = c.execute('''
            SELECT tick, ts, rcl, progress, storage, energy, energy_cap, cpu, bucket, commit, ctl, ctl_ema, hostiles, sites, creeps
            FROM room_stats WHERE room=%s ORDER BY tick DESC LIMIT 1
        ''', (room,)).fetchone()
        tips[room] = row
        tick, ts, rcl, prog, stor, ea, ecap, cpu, bkt, cmt, ctl, ema, host, sites, creeps = row
        p(room, tick, ts, 'rcl', rcl, 'p', prog, 'stor', stor, 'ea', ea, ecap, 'cpu', cpu, 'bkt', bkt, 'cmt', cmt, 'ctl', ctl, 'ema', ema, 'host', host, 'sites', sites)
        p('  creeps', creeps)

    # Use common tip: min of the two latest ticks if close, else each room's own
    tip_tick = min(tips['W46N8'][0], tips['W47N8'][0])
    # Prefer a tick that exists in both, else use W46N8 tip
    both = c.execute('''
        SELECT a.tick, a.ts FROM room_stats a
        JOIN room_stats b ON a.tick=b.tick AND b.room='W47N8'
        WHERE a.room='W46N8' AND a.tick <= %s
        ORDER BY a.tick DESC LIMIT 1
    ''', (tip_tick,)).fetchone()
    TIP = both[0] if both else tips['W46N8'][0]
    TIP_TS = both[1] if both else tips['W46N8'][1]
    p('TIP', TIP, TIP_TS)

    def samples(room, lo, hi):
        return c.execute('''
            SELECT tick, ts, progress, storage, energy, cpu, bucket, creeps, hostiles, sites, commit, ctl, ctl_ema
            FROM room_stats WHERE room=%s AND tick BETWEEN %s AND %s
            ORDER BY tick
        ''', (room, lo, hi)).fetchall()

    def interp_at(room, tip_tick, tip_ts, tip_p, tip_stor, wall_s, ideal):
        """Wall-clock exact window ending at tip_ts, interpolate start progress."""
        target_ts = tip_ts - timedelta(seconds=wall_s)
        # find brackets around target_ts
        rows = c.execute('''
            SELECT tick, ts, progress, storage FROM room_stats
            WHERE room=%s AND ts BETWEEN %s AND %s
            ORDER BY ts
        ''', (room, target_ts - timedelta(minutes=15), target_ts + timedelta(minutes=15))).fetchall()
        before = [r for r in rows if r[1] <= target_ts]
        after = [r for r in rows if r[1] >= target_ts]
        if not before or not after:
            # widen
            rows = c.execute('''
                SELECT tick, ts, progress, storage FROM room_stats
                WHERE room=%s AND ts BETWEEN %s AND %s
                ORDER BY ts
            ''', (room, target_ts - timedelta(hours=1), target_ts + timedelta(hours=1))).fetchall()
            before = [r for r in rows if r[1] <= target_ts]
            after = [r for r in rows if r[1] >= target_ts]
        if not before or not after:
            return None
        a = before[-1]; b = after[0]
        if a[1] == b[1]:
            frac = 0.0
            itick, ip, istor = a[0], a[2], a[3]
        else:
            frac = (target_ts - a[1]).total_seconds() / (b[1] - a[1]).total_seconds()
            itick = a[0] + frac * (b[0] - a[0])
            ip = a[2] + frac * (b[2] - a[2])
            istor = (a[3] or 0) + frac * ((b[3] or 0) - (a[3] or 0))
        dt = tip_tick - itick
        dprog = tip_p - ip
        et = dprog / dt if dt else 0
        shard_st = wall_s / dt if dt else 0
        pct = 100 * et / ideal if ideal else 0
        return dict(itick=itick, its=target_ts, ip=ip, istor=istor, tip=tip_tick, tip_p=tip_p,
                    dt=dt, dprog=dprog, et=et, pct=pct, wall_s=wall_s, shard_st=shard_st,
                    a=a, b=b, frac=frac)

    p('=== exact rates (interp) ===')
    for room in ROOMS:
        row = c.execute('''
            SELECT tick, ts, rcl, progress, storage, energy, energy_cap, cpu, bucket, commit, ctl, ctl_ema
            FROM room_stats WHERE room=%s AND tick=%s
        ''', (room, TIP)).fetchone()
        if not row:
            # nearest <= TIP
            row = c.execute('''
                SELECT tick, ts, rcl, progress, storage, energy, energy_cap, cpu, bucket, commit, ctl, ctl_ema
                FROM room_stats WHERE room=%s AND tick<=%s ORDER BY tick DESC LIMIT 1
            ''', (room, TIP)).fetchone()
        tick, ts, rcl, prog, stor, ea, ecap, cpu, bkt, cmt, ctl, ema = row
        pct_rcl = 100.0 * prog / 10935000 if rcl == 7 else None
        p(f'NOW {room} RCL{rcl} {pct_rcl:.2f}% p={prog} stor={stor} ea={ea}/{ecap} cpu={cpu} bucket={bkt} commit={cmt} ts={ts} ctl={ctl} ema={ema}')
        for label, wall_s in (('exact2h', 7200), ('1h', 3600)):
            r = interp_at(room, tick, ts, prog, stor, wall_s, IDEAL[room])
            if not r:
                p(f'  {room} {label} INTERP FAILED')
                continue
            p(f'  {room} {label} INTERP tick={r["itick"]:.2f} ts={r["its"]} p={r["ip"]:.1f} stor={r["istor"]:.1f} -> {r["tip"]} p={r["tip_p"]} dt={r["dt"]:.2f} dprog={r["dprog"]:.1f} {r["et"]:.2f}/{IDEAL[room]}={r["pct"]:.1f}% wall_s={r["wall_s"]} shard_s/t={r["shard_st"]:.3f}')
            p(f'    brackets a={r["a"]} b={r["b"]} frac={r["frac"]}')

    p('=== short windows ===')
    for room in ROOMS:
        ideal = IDEAL[room]
        rows = c.execute('''
            SELECT tick, ts, progress, storage FROM room_stats
            WHERE room=%s AND tick<=%s ORDER BY tick DESC LIMIT 200
        ''', (room, TIP)).fetchall()
        rows = list(reversed(rows))
        if not rows:
            continue
        tip = rows[-1]
        for span in (20, 30, 70, 100, 140, 200, 300, 500, 800, 1500):
            cands = [r for r in rows if tip[0] - r[0] >= span]
            if not cands:
                start = rows[0]
            else:
                # closest to exactly `span` ticks back (the last one that is >= span away? previous used first sample within last N)
                # Previous: last20t means samples in the last 20 ticks from tip, start = first sample with tick >= tip-span
                start_cands = [r for r in rows if r[0] >= tip[0] - span]
                start = start_cands[0] if start_cands else rows[0]
            dt = tip[0] - start[0]
            if dt <= 0:
                continue
            et = (tip[2] - start[2]) / dt
            pct = 100 * et / ideal
            n = sum(1 for r in rows if start[0] <= r[0] <= tip[0])
            p(f'{room} last{span}t (n={n} span={dt}) {et:.2f} e/t {pct:.1f}% stor {start[3]}->{tip[3]} ticks {start[0]}->{tip[0]} ts {start[1]}->{tip[1]}')

    p('=== storage extremes since last patrol (and last 3h) ===')
    for room in ROOMS:
        for label, lo in (('since_last', LAST_TIP), ('3h', TIP - int(3*3600/4.4))):
            rows = c.execute('''
                SELECT tick, ts, storage, creeps FROM room_stats
                WHERE room=%s AND tick>=%s AND tick<=%s ORDER BY tick
            ''', (room, lo, TIP)).fetchall()
            if not rows:
                p(f'{room} {label} no rows')
                continue
            n = len(rows)
            stor = [(r[0], r[1], r[2] or 0) for r in rows]
            mn = min(stor, key=lambda x: x[2])
            mx = max(stor, key=lambda x: x[2])
            under = sum(1 for *_, s in stor if s < 15000)
            over20 = sum(1 for *_, s in stor if s >= 20000)
            over25 = sum(1 for *_, s in stor if s >= 25000)
            p(f'{room} {label} n={n} min={mn} max={mx} under15k={under}/{n}={100*under/n:.1f}% over20k={over20} over25k={over25}')
            # crosses
            crosses = []
            thresh = [('over15k', 15000, True), ('over16k', 16000, True), ('under16k', 16000, False), ('under15k', 15000, False)]
            prev_s = stor[0][2]
            for i in range(1, len(stor)):
                s = stor[i][2]
                for name, th, going_up in thresh:
                    if going_up and prev_s < th <= s:
                        crosses.append((name, stor[i][0], str(stor[i][1]), s, prev_s))
                    if not going_up and prev_s >= th > s:
                        crosses.append((name, stor[i][0], str(stor[i][1]), s, prev_s))
                prev_s = s
            p(f'  crosses {crosses}')
            # nUp / w8up changes
            def nup(creeps):
                if not creeps: return 0, 0
                if isinstance(creeps, str):
                    creeps = json.loads(creeps)
                return int(creeps.get('upgrader') or 0), int(creeps.get('w8upgrader') or 0)
            changes = []
            prev_u = None
            for tick, ts, st, cr in rows:
                u, w = nup(cr)
                if prev_u is None or (u, w) != prev_u:
                    # also ctl if we want - skip, fetch from row? we didn't select ctl in this query
                    changes.append((tick, str(ts), st, u, w))
                    prev_u = (u, w)
            p(f'  nUp/w8up changes {changes}')

    p('=== room_stats gaps W46N8 since last patrol (>=30t) ===')
    rows = c.execute('''
        SELECT tick, ts FROM room_stats WHERE room='W46N8' AND tick>=%s AND tick<=%s ORDER BY tick
    ''', (LAST_TIP, TIP)).fetchall()
    gaps = []
    for i in range(1, len(rows)):
        dt = rows[i][0] - rows[i-1][0]
        if dt >= 30:
            wall = (rows[i][1] - rows[i-1][1]).total_seconds()
            gaps.append((rows[i-1][0], rows[i][0], dt, rows[i-1][1], rows[i][1], wall))
    p('gaps', gaps)

    p('=== CPU ===')
    def cpu_win(lo, hi, label):
        rows = c.execute('''
            SELECT tick, ts, cpu, bucket, storage FROM room_stats
            WHERE room='W46N8' AND tick>=%s AND tick<=%s AND cpu IS NOT NULL
            ORDER BY tick
        ''', (lo, hi)).fetchall()
        if not rows:
            p(label, 'no rows'); return
        cpus = [r[2] for r in rows]
        bkts = [r[3] for r in rows if r[3] is not None]
        n = len(cpus)
        mn, mx = min(cpus), max(cpus)
        avg = sum(cpus)/n
        srt = sorted(cpus)
        p95 = srt[int(0.95*(n-1))] if n>1 else srt[0]
        bmin = min(bkts) if bkts else None
        # top 3 max
        max_at = sorted(rows, key=lambda r: -r[2])[:3]
        max_at = [(r[0], r[1], r[2], r[4]) for r in max_at]
        p(label, (mn, mx, avg, p95, bmin, n, rows[0][0], rows[-1][0]), 'max_at', max_at)

    # 1h/2h wall clock from tip ts
    tip_ts = c.execute("SELECT ts FROM room_stats WHERE room='W46N8' AND tick=%s", (TIP,)).fetchone()[0]
    for label, secs in (('1h', 3600), ('2h', 7200)):
        lo_tick_approx = TIP - int(secs / 4.2) - 200
        # use ts filter
        lo = c.execute('''
            SELECT min(tick) FROM room_stats WHERE room='W46N8' AND ts>=%s AND tick<=%s
        ''', (tip_ts - timedelta(seconds=secs), TIP)).fetchone()[0]
        cpu_win(lo or (TIP-900), TIP, label)
    cpu_win(LAST_TIP, TIP, 'since_last')

    p('=== hostiles since last ===')
    h = c.execute('''
        SELECT room, tick, ts, hostiles, creeps
        FROM room_stats
        WHERE tick>=%s AND tick<=%s AND hostiles>0
        ORDER BY tick
    ''', (LAST_TIP, TIP)).fetchall()
    p('count', len(h))
    for row in h[:30]:
        p('  hostile', row)

    p('=== 20k/300t home spans last 3h ===')
    rows = c.execute('''
        SELECT tick, storage FROM room_stats
        WHERE room='W46N8' AND tick>=%s AND tick<=%s ORDER BY tick
    ''', (TIP - int(3*3600/4.4), TIP)).fetchall()
    best = 0
    cur_start = None
    prev = None
    mx = 0
    for t, s in rows:
        s = s or 0
        mx = max(mx, s)
        if s >= 20000:
            if cur_start is None:
                cur_start = t if prev is None else prev[0]
            best = max(best, t - cur_start)
        else:
            cur_start = None
        prev = (t, s)
    p(f'samples>=20000: check span in ticks not samples; best consecutive samples tick-span={best}')
    p(f'3h max stor={mx} best>=20k tick-span={best}')

    p(f'=== official coverage {BF_LO}..{BF_HI} ===')
    for room in OFFICIAL:
        ticks = [r[0] for r in c.execute(
            'SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s ORDER BY tick',
            (room, BF_LO, BF_HI)).fetchall()]
        missing = []
        if ticks:
            # spans of missing
            want = set(range(BF_LO, BF_HI+1))
            have = set(ticks)
            miss = sorted(want - have)
            span = None
            for t in miss:
                if span and t == span[1]+1:
                    span[1] = t
                else:
                    if span: missing.append(tuple(span)+(span[1]-span[0]+1,))
                    span = [t, t]
            if span: missing.append(tuple(span)+(span[1]-span[0]+1,))
        p(room, 'distinct', len(ticks), 'missing', (BF_HI-BF_LO+1)-len(ticks), 'spans', missing[:8], ('...' if len(missing)>8 else ''))

    p('=== later live room_stats after TIP (if any) ===')
    for room in ROOMS:
        rows = c.execute('''
            SELECT tick, ts, progress, storage, energy, cpu, bucket, creeps, hostiles, sites
            FROM room_stats WHERE room=%s AND tick>%s ORDER BY tick
        ''', (room, TIP)).fetchall()
        p(room, 'later_n', len(rows))
        if rows:
            for r in (rows[0], rows[-1]):
                p(' ', r[0], r[1], 'p', r[2], 'stor', r[3], 'ea', r[4], 'cpu', r[5], 'bkt', r[6], 'host', r[8], 'sites', r[9], 'creeps', r[7])
            # storage after tip
            stors = [(r[0], r[1], r[3] or 0) for r in rows]
            p('  later stor min', min(stors, key=lambda x:x[2]), 'max', max(stors, key=lambda x:x[2]), 'last', stors[-1])

    p('=== nUp timeseries since last (every sample) W46N8 ===')
    rows = c.execute('''
        SELECT tick, ts, storage, creeps FROM room_stats
        WHERE room='W46N8' AND tick>=%s ORDER BY tick
    ''', (LAST_TIP,)).fetchall()
    def nup(cr):
        if not cr: return 0
        if isinstance(cr, str): cr=json.loads(cr)
        return int(cr.get('upgrader') or 0)
    # compact: print when nUp changes and a few anchors
    prev = None
    for tick, ts, st, cr in rows:
        u = nup(cr)
        if prev is None or u != prev[0]:
            p(f'  nUp={u} from {tick} {ts} stor={st}')
            prev = (u, tick)
    if rows:
        p(f'  last nUp={nup(rows[-1][3])} tick={rows[-1][0]} {rows[-1][1]} stor={rows[-1][2]}')

    p('=== W47 progress / storage / sites / creeps since last ===')
    rows = c.execute('''
        SELECT tick, ts, progress, storage, sites, creeps, hostiles
        FROM room_stats WHERE room='W47N8' AND tick>=%s ORDER BY tick
    ''', (LAST_TIP,)).fetchall()
    if rows:
        progs = set(r[2] for r in rows)
        p('unique progress values', sorted(progs)[:10], 'nunique', len(progs), 'first', rows[0][2], 'last', rows[-1][2])
        stors = [(r[0], r[1], r[3] or 0) for r in rows]
        p('stor min', min(stors, key=lambda x:x[2]), 'max', max(stors, key=lambda x:x[2]), 'last', stors[-1])
        # w8defender / w8builder / w8rhauler / w8upgrader presence
        def cnt(cr, role):
            if not cr: return 0
            if isinstance(cr, str): cr=json.loads(cr)
            return int(cr.get(role) or 0)
        for role in ('w8defender', 'w8builder', 'w8rhauler', 'w8upgrader', 'w8miner', 'w8filler', 'w8rminer', 'reserve7', 'upgrader'):
            xs = [(r[0], r[1], cnt(r[5], role)) for r in rows]
            nonzero = [x for x in xs if x[2]>0]
            zero_runs = []
            run = None
            for t, ts, n in xs:
                if n == 0:
                    if run is None: run = [t, t, ts, ts]
                    else:
                        run[1] = t; run[3] = ts
                else:
                    if run:
                        zero_runs.append((run[0], run[1], run[1]-run[0], str(run[2]), str(run[3])))
                        run = None
            if run:
                zero_runs.append((run[0], run[1], run[1]-run[0], str(run[2]), str(run[3])))
            p(f'  {role}: last={xs[-1][2]} first_nonzero={nonzero[0] if nonzero else None} last_nonzero={nonzero[-1] if nonzero else None} zero_runs={zero_runs[:6]}')

    # also home role presence
    p('=== home critical roles since last ===')
    rows = c.execute('''
        SELECT tick, ts, creeps FROM room_stats
        WHERE room='W46N8' AND tick>=%s ORDER BY tick
    ''', (LAST_TIP,)).fetchall()
    def cnt(cr, role):
        if not cr: return 0
        if isinstance(cr, str): cr=json.loads(cr)
        return int(cr.get(role) or 0)
    for role in ('miner', 'queen', 'hauler', 'rminer', 'rhauler', 'reserver', 'upgrader', 'builder'):
        xs = [(r[0], r[1], cnt(r[2], role)) for r in rows]
        nonzero = [x for x in xs if x[2]>0]
        zero_runs = []
        run = None
        for t, ts, n in xs:
            if n == 0:
                if run is None: run = [t, t, ts, ts]
                else:
                    run[1] = t; run[3] = ts
            else:
                if run:
                    zero_runs.append((run[0], run[1], run[1]-run[0], str(run[2]), str(run[3])))
                    run = None
        if run:
            zero_runs.append((run[0], run[1], run[1]-run[0], str(run[2]), str(run[3])))
        p(f'  {role}: last={xs[-1][2] if xs else None} zero_runs={zero_runs[:8]}')


    p('=== leftover official holes (known 404s + hour window) ===')
    leftovers = [
        (84366201, 84366300, 'W47N8@84366200'),
        (84366501, 84366600, 'W47N7@84366500'),
        (84365201, 84365300, 'W45N7@84365200'),
        (84363901, 84364000, 'W47N8@84363900'),
        (84362701, 84362800, 'W46N8@84362700'),
        (84354301, 84354400, 'W46N8@84354300'),
        (84354301, 84354400, 'W47N7@84354300'),
        (84352401, 84352500, 'W47N8@84352400'),
        (84358501, 84358600, 'W45N7@84358500'),
        (84358701, 84358800, 'W47N8@84358700'),
        (84359501, 84359600, 'W47N8@84359500'),
        (84359901, 84360000, 'W47N8@84359900'),
        (84360201, 84360300, 'W45N7@84360200'),
        (84360601, 84360700, 'W46N8@84360600'),
        (84361701, 84361800, 'W47N8@84361700'),
        (84368101, 84368200, 'W45N8@84368100'),
        (84383501, 84383600, 'W45N7@84383500'),
        (84383901, 84384000, 'W45N7@84383900'),
        (84382601, 84382700, 'W45N8@84382600'),
        (84382701, 84382800, 'W45N7@84382700'),
        (84382901, 84383000, 'W46N8@84382900'),
        (84385301, 84385400, 'W47N8@84385300'),
        (84385901, 84386000, 'W47N8@84385900'),
        (84386401, 84386500, 'W46N8@84386400'),
        (84403701, 84403800, 'W45N7@84403700'),
        (84403801, 84403900, 'W45N7@84403800'),
        (84400301, 84400400, 'W45N7@84400300'),
        (84400401, 84400500, 'W45N7@84400400'),
        (84400101, 84400200, 'W47N8@84400100'),
        (84406401, 84406500, 'W45N8@84406400'),
        (84406601, 84406700, 'W46N8@84406600'),
        (84406701, 84406800, 'W46N8@84406700'),
        (84407001, 84407100, 'W46N8@84407000'),
        (84407701, 84407800, 'W45N8@84407700'),
    ]
    for lo, hi, label in leftovers:
        for room in OFFICIAL:
            n = c.execute('SELECT count(DISTINCT tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s', (room, lo, hi)).fetchone()[0]
            if n != (hi-lo+1) or room in label:
                p(' ', label, room, 'distinct=%s/100' % n)

    p('=== hour-window creep_ticks coverage LAST_TIP+1..TIP ===')
    for room in OFFICIAL:
        ticks = [r[0] for r in c.execute(
            'SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s ORDER BY tick',
            (room, LAST_TIP+1, TIP)).fetchall()]
        missing = []
        if ticks:
            want = set(range(LAST_TIP+1, TIP+1))
            miss = sorted(want - set(ticks))
            span = None
            for tk in miss:
                if span and tk == span[1]+1:
                    span[1] = tk
                else:
                    if span:
                        missing.append(tuple(span)+(span[1]-span[0]+1,))
                    span = [tk, tk]
            if span:
                missing.append(tuple(span)+(span[1]-span[0]+1,))
        else:
            missing = [(LAST_TIP+1, TIP, TIP-LAST_TIP)]
        p(room, 'hour distinct', len(ticks), 'want', TIP-LAST_TIP, 'missing_spans', missing[:10], ('...' if len(missing)>10 else ''))

    p('=== incidents since last ===')
    try:
        rows = c.execute('SELECT * FROM incidents WHERE tick>=%s ORDER BY tick', (LAST_TIP,)).fetchall()
        cols = [d[0] for d in c.description] if c.description else []
        p('incidents cols', cols, 'n', len(rows))
        for r in rows[:20]:
            p(' ', r)
    except Exception as e:
        p('incidents query err', type(e).__name__, e)
        c.rollback()

    p('DONE TIP', TIP)
    open('/workspace/screeps/state/_patrol_2026-11-22_0918/exact2h_copy.txt','w').write('\n'.join(out)+'\n')
    open('/workspace/screeps/state/_patrol_exact2h.txt','w').write('\n'.join(out)+'\n')

if __name__ == '__main__':
    main()
