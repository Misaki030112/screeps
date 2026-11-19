#!/usr/bin/env python3
"""exact2h / short windows / storage / CPU using official hist + room_stats + live tip."""
from __future__ import annotations
import json, sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path

sys.path.insert(0, '/workspace/screeps/tools')
import db

OUT = Path('/workspace/screeps/state/_patrol_2026-11-19_1022')
HK = ZoneInfo('Asia/Hong_Kong')
IDEAL = {'W46N8': 26.0, 'W47N8': 30.08}
LAST_TIP = 84350670
# live console tip (q_home)
LIVE = {
    'W46N8': {'t': 84351334, 'p': 8284317, 's': 15992},
    'W47N8': {'t': 84351334, 'p': 5037242, 's': 20604},
}
# later min query slightly after
LIVE_LATER = {
    'W46N8': {'t': 84351340, 'p': None, 's': 15722},
    'W47N8': {'t': 84351340, 'p': None, 's': 20604},
}

def main():
    c = db.connect()
    out = []
    def p(*a):
        s = ' '.join(str(x) for x in a)
        out.append(s)
        print(s)

    hist = json.loads((OUT/'hist_progress_storage.json').read_text())
    series = {}
    for room, rows in hist['series'].items():
        series[room] = {int(t): (p_, s_) for t, p_, s_ in rows}

    # room_stats samples
    rss = {}
    for room in IDEAL:
        rows = c.execute('''
            SELECT tick, ts, progress, storage, energy, cpu, bucket, creeps, hostiles, sites, commit
            FROM room_stats WHERE room=%s AND tick >= 84349000 ORDER BY tick
        ''', (room,)).fetchall()
        rss[room] = rows
        p(f'room_stats {room} n={len(rows)} min={rows[0][0] if rows else None} max={rows[-1][0] if rows else None}')

    # tick_s from recent room_stats (same room, neighboring samples)
    def tick_s_recent():
        rows = c.execute('''
            SELECT tick, ts FROM room_stats WHERE room='W46N8' AND tick >= 84351290 ORDER BY tick
        ''').fetchall()
        if len(rows) >= 2:
            dt = (rows[-1][1] - rows[0][1]).total_seconds()
            dtk = rows[-1][0] - rows[0][0]
            if dtk > 0 and dt > 0:
                return dt/dtk, rows[-1][0], rows[-1][1]
        # fallback
        return 4.739, None, None

    tick_s, anc_tick, anc_ts = tick_s_recent()
    p(f'tick_s_recent={tick_s:.5f} anchor tick={anc_tick} ts={anc_ts}')

    # also tick_s over last 2h from any two room_stats far apart if possible, and hist span
    # Use live tip as TIP
    TIP = 84351334
    if anc_tick and anc_ts:
        TIP_TS = anc_ts + timedelta(seconds=(TIP - anc_tick) * tick_s)
    else:
        TIP_TS = datetime.now(HK)
    p('TIP', TIP, TIP_TS.astimezone(HK))

    def ts_of(tick):
        return TIP_TS - timedelta(seconds=(TIP - tick) * tick_s)

    def at(room, tick):
        """progress, storage at tick, preferring hist then room_stats then live."""
        if tick == LIVE[room]['t']:
            return LIVE[room]['p'], LIVE[room]['s']
        h = series[room]
        if tick in h and h[tick][0] is not None:
            return h[tick]
        # nearest hist
        return None

    def brack(room, target_tick):
        h = series[room]
        ticks = sorted(h)
        # also include live
        pts = {t: h[t] for t in ticks if h[t][0] is not None}
        pts[LIVE[room]['t']] = (LIVE[room]['p'], LIVE[room]['s'])
        # room_stats fill
        for row in rss[room]:
            t, ts, prog, stor, *rest = row
            if t not in pts and prog is not None:
                pts[t] = (prog, stor)
        ks = sorted(pts)
        if target_tick in pts:
            return target_tick, pts[target_tick][0], pts[target_tick][1], 0
        lo = None
        hi = None
        for t in ks:
            if t <= target_tick:
                lo = t
            elif t > target_tick and hi is None:
                hi = t
                break
        if lo is None or hi is None:
            return None
        p0,s0 = pts[lo]
        p1,s1 = pts[hi]
        f = (target_tick - lo) / (hi - lo)
        ip = p0 + f * (p1 - p0)
        ist = None if (s0 is None or s1 is None) else s0 + f * (s1 - s0)
        return target_tick, ip, ist, hi-lo

    def exact(room, wall_s, label):
        target_ts = TIP_TS - timedelta(seconds=wall_s)
        # convert to tick
        target_tick = TIP - wall_s / tick_s
        r = brack(room, target_tick)
        if not r:
            p(f'  {room} {label} INTERP FAILED target_tick={target_tick:.2f}')
            return None
        _, ip, ist, span = r
        tip_p = LIVE[room]['p']
        dt = TIP - target_tick
        dprog = tip_p - ip
        et = dprog / dt if dt else None
        pct = 100 * et / IDEAL[room]
        rec = dict(itick=target_tick, ip=ip, istor=ist, tip=TIP, tip_p=tip_p, dt=dt, dprog=dprog, et=et, pct=pct, wall_s=wall_s, shard_st=tick_s, span=span)
        p(f'  {room} {label} INTERP tick={target_tick:.2f} p={ip:.1f} stor={ist} -> {TIP} p={tip_p} dt={dt:.2f} dprog={dprog:.1f} {et:.2f}/{IDEAL[room]}={pct:.1f}% wall_s={wall_s} shard_s/t={tick_s:.3f}')
        return rec

    p('=== exact rates (interp) ===')
    exacts = {}
    for room in IDEAL:
        exacts[room] = {}
        for label, wall_s in (('exact2h', 7200), ('1h', 3600)):
            exacts[room][label] = exact(room, wall_s, label)

    p('=== short windows (hist+live, designed tick spans from TIP) ===')
    shorts = {}
    for room in IDEAL:
        shorts[room] = {}
        pts = {t: series[room][t] for t in series[room] if series[room][t][0] is not None}
        pts[LIVE[room]['t']] = (LIVE[room]['p'], LIVE[room]['s'])
        ks = sorted(pts)
        for span in (20, 30, 70, 100, 140, 200, 300, 500, 800, 1500):
            start = TIP - span
            # find first sample >= start and last = TIP or closest <= TIP
            lo_t = None
            for t in ks:
                if t >= start and lo_t is None:
                    lo_t = t
            hi_t = max(t for t in ks if t <= TIP)
            if lo_t is None or hi_t <= lo_t:
                p(f'  {room} last{span} FAILED')
                continue
            p0 = pts[lo_t][0]
            p1 = LIVE[room]['p'] if hi_t == TIP or hi_t == LIVE[room]['t'] else pts[hi_t][0]
            # use exact start interpolation if we have brack
            b = brack(room, start)
            if b:
                _, ip, _, _ = b
                p0 = ip
                lo_used = start
            else:
                lo_used = lo_t
            dt = TIP - lo_used
            et = (LIVE[room]['p'] - p0) / dt
            pct = 100 * et / IDEAL[room]
            shorts[room][span] = dict(et=et, pct=pct, dt=dt, lo=lo_used, p0=p0)
            p(f'  {room} last{span} lo={lo_used:.1f} p0={p0:.1f} dt={dt:.1f} {et:.2f}/{IDEAL[room]}={pct:.1f}%')

    # storage extremes from hist + live + room_stats
    p('=== storage extremes ===')
    # also load 0922 hist for 12h/24h if needed
    old = {}
    oldp = Path('/workspace/screeps/state/_patrol_2026-11-19_0922/hist_progress_storage.json')
    if oldp.exists():
        oldj = json.loads(oldp.read_text())
        for room, rows in oldj['series'].items():
            old[room] = {int(t): (pp, ss) for t, pp, ss in rows}

    def stor_series(room, lo, hi):
        d = {}
        if room in old:
            for t,(pp,ss) in old[room].items():
                if lo <= t <= hi and ss is not None:
                    d[t] = ss
        for t,(pp,ss) in series[room].items():
            if lo <= t <= hi and ss is not None:
                d[t] = ss
        for row in rss[room]:
            t, ts, prog, stor, *rest = row
            if lo <= t <= hi and stor is not None:
                d[t] = stor
        if lo <= LIVE[room]['t'] <= hi:
            d[LIVE[room]['t']] = LIVE[room]['s']
        if lo <= LIVE_LATER[room]['t'] <= hi and LIVE_LATER[room]['s'] is not None:
            d[LIVE_LATER[room]['t']] = LIVE_LATER[room]['s']
        return d

    def summarize(room, lo, hi, label):
        d = stor_series(room, lo, hi)
        if not d:
            p(f'{room} {label} NO DATA')
            return
        items = sorted(d.items())
        vals = [s for _,s in items]
        mn, mx = min(vals), max(vals)
        tmn = min(items, key=lambda x: x[1])
        tmx = max(items, key=lambda x: x[1])
        n = len(items)
        under15 = sum(1 for s in vals if s < 15000)
        over20 = sum(1 for s in vals if s >= 20000)
        over25 = sum(1 for s in vals if s >= 25000)
        over30 = sum(1 for s in vals if s >= 30000)
        over40 = sum(1 for s in vals if s >= 40000)
        p(f'{room} {label} n={n} min={tmn} max={tmx} under15k={under15}/{n}={100*under15/n:.1f}% over20k={over20} over25k={over25} over30k={over30} over40k={over40}')
        # longest under 15k / over 20k / over 40k runs (contiguous ticks in hist; allow 1-tick gaps)
        def longest(pred):
            best = 0
            best_span = None
            run = 0
            run_start = None
            prev = None
            for t,s in items:
                ok = pred(s)
                if ok and prev is not None and t - prev <= 2:
                    run += t - prev
                elif ok:
                    run = 1
                    run_start = t
                else:
                    if run > best:
                        best = run
                        best_span = (run_start, prev, run)
                    run = 0
                    run_start = None
                prev = t
            if run > best:
                best = run
                best_span = (run_start, prev, run)
            return best, best_span
        for name, pred in [('under15k', lambda s: s<15000), ('ge20k', lambda s: s>=20000), ('ge40k', lambda s: s>=40000), ('ge30k', lambda s: s>=30000)]:
            best, span = longest(pred)
            if best:
                p(f'  {name} best_span={span}')
        return tmn, tmx

    windows = [
        ('since_last', LAST_TIP, TIP),
        ('3h', TIP - int(3*3600/tick_s), TIP),
        ('6h', TIP - int(6*3600/tick_s), TIP),
        ('12h', TIP - int(12*3600/tick_s), TIP),
        ('24h', TIP - int(24*3600/tick_s), TIP),
    ]
    for room in IDEAL:
        for label, lo, hi in windows:
            summarize(room, lo, hi, label)

    # CPU from room_stats (gappy)
    p('=== CPU room_stats ===')
    for label, lo in (('since_last', LAST_TIP), ('2h', TIP-int(7200/tick_s)), ('postwake', 84351290)):
        rows = c.execute('''
            SELECT tick, ts, cpu, bucket FROM room_stats
            WHERE room='W46N8' AND tick BETWEEN %s AND %s AND cpu IS NOT NULL
            ORDER BY tick
        ''', (lo, TIP+50)).fetchall()
        if not rows:
            p(f'CPU {label} no samples')
            continue
        cpus = [r[2] for r in rows]
        bkts = [r[3] for r in rows if r[3] is not None]
        imax = max(range(len(rows)), key=lambda i: rows[i][2])
        p(f'CPU {label} n={len(rows)} min={min(cpus):.2f} max={max(cpus):.2f}@{rows[imax][0]} mean={sum(cpus)/len(cpus):.2f} bkt min={min(bkts) if bkts else None} max={max(bkts) if bkts else None} ticks {rows[0][0]}..{rows[-1][0]}')

    # room_stats gaps since last (>=30t)
    p('=== room_stats gaps W46N8 since last (>=30t) ===')
    ticks = [r[0] for r in c.execute("SELECT tick FROM room_stats WHERE room='W46N8' AND tick BETWEEN %s AND %s ORDER BY 1", (LAST_TIP, TIP+50))]
    ut = sorted(set(ticks))
    gaps=[]
    for i in range(1,len(ut)):
        if ut[i]-ut[i-1]>30:
            gaps.append((ut[i-1]+1, ut[i]-1, ut[i]-ut[i-1]-1))
    p('gaps', gaps)
    if ut:
        p('room_stats coverage', ut[0], ut[-1], 'n', len(ut))

    # home nUp from room_stats creeps json since last
    p('=== nUp from room_stats creeps ===')
    def nrole(creeps, pred):
        if not creeps: return 0
        if isinstance(creeps, str):
            creeps = json.loads(creeps)
        n=0
        # creeps may be dict role->count or list
        if isinstance(creeps, dict):
            # possibly {name: role} or {role: count} or {role: [names]}
            for k,v in creeps.items():
                if pred(k) and isinstance(v,(int,float)):
                    n += int(v)
                elif isinstance(v,str) and pred(v):
                    n += 1
                elif isinstance(v,list):
                    if pred(k):
                        n += len(v)
                    else:
                        n += sum(1 for x in v if pred(str(x)))
        elif isinstance(creeps, list):
            for x in creeps:
                if isinstance(x,str) and pred(x):
                    n += 1
                elif isinstance(x,dict) and pred(str(x.get('role') or x.get('r') or x.get('name') or '')):
                    n += 1
        return n

    # peek one creeps payload
    peek = c.execute("SELECT tick, creeps FROM room_stats WHERE room='W46N8' AND creeps IS NOT NULL ORDER BY tick DESC LIMIT 1").fetchone()
    p('peek creeps type', type(peek[1] if peek else None), str(peek[1])[:400] if peek else None)

    (OUT/'exact_now.txt').write_text('\n'.join(out)+'\n')
    (OUT/'exact_now.json').write_text(json.dumps({
        'TIP': TIP, 'TIP_TS': str(TIP_TS), 'tick_s': tick_s,
        'exacts': {r: {k: (v if v is None else {kk: (vv if not hasattr(vv,'imag') else vv) for kk,vv in v.items()}) for k,v in exacts[r].items()} for r in exacts},
        'shorts': shorts,
    }, default=str, indent=2))
    p('DONE TIP', TIP)

if __name__ == '__main__':
    main()
