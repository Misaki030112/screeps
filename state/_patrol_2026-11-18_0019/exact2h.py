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
LAST_TIP = 84324560  # previous 1h patrol analysis TIP (~23:25)
ROOMS = ['W46N8', 'W47N8']
OFFICIAL = ('W46N8', 'W47N8', 'W45N8', 'W45N7', 'W47N7')
# last 40m backfill window
BF_LO, BF_HI = 84324601, 84325300

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
            WHERE room=%s AND tick<=%s ORDER BY tick DESC LIMIT 80
        ''', (room, TIP)).fetchall()
        rows = list(reversed(rows))
        if not rows:
            continue
        tip = rows[-1]
        for span in (20, 30, 70, 100, 140, 200, 300, 500, 800):
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
        for label, lo in (('since_last', LAST_TIP), ('3h', TIP - int(3*3600/4.4)), ('6h', TIP - int(6*3600/4.4))):
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
        (84242901, 84243000, 'W45N8@84242900'),
        (84243101, 84243200, 'W47N8@84243100'),
        (84243701, 84243800, 'W47N8@84243700'),
        (84246301, 84246400, 'W45N7@84246300'),
        (84246301, 84246400, 'W47N7@84246300'),
        (84246501, 84246600, 'W46N8@84246500'),
        (84246701, 84246800, 'W47N7@84246700'),
        (84246801, 84246900, 'W45N7@84246800'),
        (84248301, 84248400, 'W45N8@84248300'),
        (84249601, 84249700, 'W47N8@84249600'),
        (84250801, 84250900, 'W45N7@84250800'),
        (84250901, 84251000, 'W45N8@84250900'),
        (84251701, 84251800, 'W45N7@84251700'),
        (84251801, 84251900, 'W45N7@84251800'),
        (84252001, 84252100, 'W46N8@84252000'),
        (84252401, 84252500, 'W46N8@84252400'),
        (84253101, 84253200, 'W46N8@84253100'),
        (84253601, 84253700, 'W47N7@84253600'),
        (84253801, 84253900, 'W45N8@84253800'),
        (84254901, 84255000, 'W47N8@84254900'),
        (84254901, 84255000, 'W45N8@84254900'),
        (84254901, 84255000, 'W47N7@84254900'),
        (84257901, 84258000, 'W45N7@84257900'),
        (84258601, 84258700, 'W45N8@84258600'),
        (84259201, 84259300, 'W45N7@84259200'),
        (84260301, 84260400, 'W46N8@84260300'),
        (84261901, 84262000, 'W47N8@84261900'),
        (84262501, 84262600, 'W46N8@84262500'),
        (84263601, 84263700, 'W46N8@84263600'),
        (84264101, 84264200, 'W45N8@84264100'),
        (84265701, 84265800, 'W45N8@84265700'),
        (84266101, 84266200, 'W45N7@84266100'),
        (84266801, 84266900, 'W47N8@84266800'),
        (84269201, 84269300, 'W46N8@84269200'),
        (84269701, 84269800, 'W47N7@84269700'),
        (84285501, 84285600, 'W45N7@84285500'),
        (84287501, 84287600, 'W47N8@84287500'),
        (84289201, 84289300, 'W47N7@84289200'),
        (84289301, 84289400, 'W45N7@84289300'),
        (84290201, 84290300, 'W47N8@84290200'),
        (84292001, 84292100, 'W46N8@84292000'),
        (84295801, 84295900, 'W45N7@84295800'),
        (84295901, 84296000, 'W45N8@84295900'),
        (84296501, 84296600, 'W47N7@84296500'),
        (84297201, 84297300, 'W47N8@84297200'),
        (84298001, 84298100, 'W47N8@84298000'),
        (84300001, 84300100, 'W45N8@84300000'),
        (84300901, 84301000, 'W47N8@84300900'),
        (84300901, 84301000, 'W45N8@84300900'),
        (84302201, 84302300, 'W45N8@84302200'),
        (84303901, 84304000, 'W45N7@84303900'),
        (84304701, 84304800, 'W47N8@84304700'),
        (84305101, 84305200, 'W45N7@84305100'),
        (84306501, 84306600, 'W45N8@84306500'),

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
    open('/workspace/screeps/state/_patrol_2026-11-17_2223/exact2h.txt','w').write('\n'.join(out)+'\n')

if __name__ == '__main__':
    main()
