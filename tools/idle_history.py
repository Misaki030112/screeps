#!/usr/bin/env python3
"""Retroactive idle attribution from history (no in-game codes needed).
Unit = 5-tick creep_cpu window (acts = successful intents) joined with creep_ticks positions/store of the same 5 ticks.
  working: acts>0 | moving: position changed | spawning | idle:<reason> inferred from role + tile + store + room energy.
  .venv/bin/python tools/idle_history.py [--from ISO] [--to ISO] [--split-deploys] [--json out]"""
import sys, os, json, bisect, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import db
L = json.load(open(os.path.join(db.ROOT, 'data', 'layout_W46N8_v2.json')))['positions']
MINERS, DROP, UPG = L['miners'], tuple(L['controllerDrop']), [tuple(p) for p in L['upgraders']]
PARK, RCONT = (46, 21), (13, 11)
LEGIT = {'source_empty', 'spawning', 'renewing'}
near = lambda a, b, r=1: abs(a[0]-b[0]) <= r and abs(a[1]-b[1]) <= r
def reason(role, room, xy, store, cap_full, room_full):
    if room == 'W46N8' and role in ('rminer', 'rhauler', 'reserver', 'defender') and near(xy, PARK, 3): return 'parked_threat'
    if role in ('miner', 'rminer', 'mminer'): return 'source_empty'
    if role == 'hauler':
        if any(near(xy, m) for m in MINERS): return 'waiting_pickup'
        if near(xy, DROP, 1): return 'waiting_fill_target_full'
        return 'queue_blocked'
    if role == 'rhauler':
        if room == 'W45N8' and near(xy, RCONT, 2): return 'waiting_pickup'
        return 'queue_blocked'
    if role == 'upgrader': return 'waiting_feed' if store == 0 else 'queue_blocked'
    if role == 'builder': return 'no_task' if store else 'waiting_pickup'
    if role == 'queen': return 'waiting_fill_target_full' if room_full else 'waiting_pickup'
    return 'queue_blocked'
def run(a=None, b=None):
    c = db.connect(); w = "WHERE ts >= coalesce(%s::timestamptz,'-infinity') AND ts < coalesce(%s::timestamptz,'infinity')"
    T = collections.defaultdict(list)
    for tick, n, room, x, y, st, state in c.execute(f"SELECT DISTINCT ON (creep,tick) tick,creep,room,x,y,store,state FROM creep_ticks {w} ORDER BY creep,tick", (a, b)):
        T[n].append((tick, room, x, y, st, state))
    RS = c.execute(f"SELECT tick, energy>=energy_cap FROM room_stats {w} AND room='W46N8' ORDER BY tick", (a, b)).fetchall(); rt = [r[0] for r in RS]
    D = c.execute("SELECT tick, commit FROM deploys ORDER BY tick").fetchall(); dt = [d[0] for d in D]
    rows = []
    for tick, n, role, cpu, acts, work, ts in c.execute(f"SELECT DISTINCT ON (creep,tick) tick,creep,role,cpu_ms,acts,work,ts FROM creep_cpu {w} ORDER BY creep,tick", (a, b)):
        s = T.get(n);
        if not s: continue
        ks = [r[0] for r in s]; i0, i1 = bisect.bisect_left(ks, tick-5), bisect.bisect_right(ks, tick)
        win = s[max(0, i0-1):i1]
        if not win or tick - win[-1][0] > 30: continue
        last = win[-1]; moved = len({(r[1], r[2], r[3]) for r in win}) > 1
        j = bisect.bisect_right(rt, tick) - 1; full = RS[j][1] if j >= 0 else False
        if last[5] == 'spawning': st = 'spawning'
        elif acts: st = 'working'
        elif moved: st = 'moving'
        else: st = reason(role, last[1], (last[2], last[3]), last[4], None, full)
        k = bisect.bisect_right(dt, tick) - 1
        rows.append(dict(tick=tick, ts=ts, creep=n, role=role, st=st, cpu=cpu or 0, acts=acts, work=work, room=last[1], dep=D[k][1] if k >= 0 else 'pre'))
    return rows
def summarize(rows, key='role'):
    S = collections.defaultdict(lambda: collections.Counter()); C = collections.defaultdict(float)
    for r in rows: S[r[key]][r['st']] += 5; C[(r[key], r['st'])] += r['cpu']
    out = {}
    for k, cnt in S.items():
        tot = sum(cnt.values()); idle = {s: v for s, v in cnt.items() if s not in ('working', 'moving')}
        out[k] = dict(ticks=tot, work=round(100*cnt['working']/tot, 1), move=round(100*cnt['moving']/tot, 1),
            nonlegit=round(100*sum(v for s, v in idle.items() if s not in LEGIT)/tot, 1),
            reasons={s: round(100*v/tot, 1) for s, v in sorted(idle.items(), key=lambda kv: -kv[1])},
            idle_cpu_ms=round(sum(C[(k, s)] for s in idle if s not in LEGIT), 1))
    return out
if __name__ == '__main__':
    g = lambda f: sys.argv[sys.argv.index(f)+1] if f in sys.argv else None
    rows = run(g('--from'), g('--to'))
    print(f'windows={len(rows)} ticks {min(r["tick"] for r in rows)}..{max(r["tick"] for r in rows)}  {min(r["ts"] for r in rows):%m-%d %H:%M}..{max(r["ts"] for r in rows):%H:%M} UTC+8')
    res = {'role': summarize(rows)}
    for k, v in sorted(res['role'].items()): print(k, v)
    if '--split-deploys' in sys.argv:
        res['deploy'] = {}
        for d in dict.fromkeys(r['dep'] for r in sorted(rows, key=lambda r: r['tick'])):
            sub = [r for r in rows if r['dep'] == d]; res['deploy'][d] = summarize(sub)
            print('==', d, len(sub), {k: (v['nonlegit'], v['ticks']) for k, v in res['deploy'][d].items()})
    if g('--json'): json.dump(res, open(g('--json'), 'w'), indent=1, default=str)
