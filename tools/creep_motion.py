#!/usr/bin/env python3
"""Per-creep movement/efficiency analysis (complements creep_audit.py; docs/DATA.md "Motion audit").
  .venv/bin/python tools/creep_motion.py [--hours 1] [--json] [--patrol]
Sources: creep_ticks (websocket trail, 0 in-game CPU; W46N8, W45N8, W45N7), creep_cpu (segment 90: codes, cpu, cpu_max, fails), data/terrain_*.txt.
Only consecutive ticks (dt == 1) are compared, so websocket gaps never count as moves or stalls.
Per creep:
  stuck      ticks standing still while the in-game state code says moving-wanted ('m' never, but no move + pending target + no intent)
  bounce     A-B-A moves;  circle  moves onto a tile already visited in the same leg (no store change, last 30 ticks, excl. A-B-A), i.e. loops/detours
  swamp      ticks a moving creep spent standing on a swamp tile (fatigue: no road there)
  empty_mv   share of moves made with an empty store (haulers: ~50% is the floor of a round trip)
  partial    hauler departures from a source room with < 80% of observed capacity (wasted trip capacity)
  idle       non-legit idle ticks by reason (codes);  cpu_t, cpu_max (worst single tick), fails (failed intents excl. not-in-range)
Ranking: estimated ticks lost per hour (stuck + swamp + circle + bounce + non-legit idle + partial-trip shortfall in tick-equivalents).
--patrol exit 0 nothing material (no creep losing >= 60 ticks/h, no cpu_max >= 2 ms, no fails), 1 findings."""
import os, sys, json
from collections import defaultdict, deque
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import db
H = float(sys.argv[sys.argv.index('--hours') + 1]) if '--hours' in sys.argv else 1.0
TERR = {}
def terr(room):
    if room not in TERR:
        f = os.path.join(db.ROOT, 'data', f'terrain_{room}.txt'); TERR[room] = open(f).read().strip() if os.path.exists(f) else ''
    return TERR[room]
def swamp(room, x, y): t = terr(room); return len(t) >= 2500 and t[y * 50 + x] == '2'
SRC_ROOMS = {'W45N8', 'W45N7'}; HOME = 'W46N8'
STATIC = {'miner', 'rminer', 'upgrader', 'manager', 'filler'}
LEGIT = set('wmesr')
REASON = {'p': 'waiting_pickup', 'u': 'waiting_feed', 'f': 'target_full', 'q': 'queue_blocked', 'n': 'no_task', 't': 'parked_threat'}
def main():
    c = db.connect(); iv = f"{H} hours"
    T = defaultdict(list)
    for n, role, tick, room, x, y, e in c.execute(f"SELECT creep, role, tick, room, x, y, store FROM creep_ticks WHERE ts > now() - interval '{iv}' AND state <> 'spawning' ORDER BY creep, tick"):
        T[n].append((tick, room, x, y, e or 0, role))
    C = defaultdict(lambda: {'cpu': 0, 'win': 0, 'mx': 0, 'fails': 0, 'codes': '', 'tgt': {}})
    for n, cpu, mx, f, codes, t0, tg in c.execute(f"SELECT creep, cpu_ms, cpu_max, fails, codes, tick, target FROM creep_cpu WHERE ts > now() - interval '{iv}'"):
        m = C[n]; m['cpu'] += cpu or 0; m['win'] += 1; m['mx'] = max(m['mx'], mx or 0); m['fails'] += f or 0; m['codes'] += codes or ''
        m['tgt'][t0] = tg
    out = []
    for n in set(T) | set(C):
        tr = T.get(n, []); role = (tr[0][5] if tr else None) or ''.join(ch for ch in n if ch.isalpha())
        r = dict(creep=n, role=role, samples=len(tr), moves=0, stuck=0, bounce=0, circle=0, swamp=0, empty_mv=0, partial=0, departs=0, part_short=0.0)
        cap = max((s[4] for s in tr), default=0); hist = deque(maxlen=30); still = 0
        for i in range(1, len(tr)):
            (t0, r0, x0, y0, e0, _), (t1, r1, x1, y1, e1, _) = tr[i - 1], tr[i]
            if t1 - t0 != 1 or e1 != e0: hist.clear(); still = 0  # a leg ends when the store changes (pickup/delivery)
            if t1 - t0 != 1: continue
            if (r0, x0, y0) != (r1, x1, y1):
                r['moves'] += 1; r['empty_mv'] += e0 == 0
                if i >= 2 and tr[i - 2][0] == t0 - 1 and tr[i - 2][1:4] == (r1, x1, y1): r['bounce'] += 1
                elif (r1, x1, y1) in hist: r['circle'] += 1
                hist.append((r0, x0, y0)); still = 0
                if role == 'rhauler' and r0 in SRC_ROOMS and r1 != r0:
                    r['departs'] += 1
                    if cap and e0 < 0.8 * cap: r['partial'] += 1; r['part_short'] += (cap - e0) / cap
            else:
                still += 1
                if role not in STATIC and swamp(r1, x1, y1) and still <= 9: r['swamp'] += 1  # fatigue wait on swamp (<=5 ticks per step with MOVE ratio <1)
        m = C.get(n)
        codes = m['codes'] if m else ''
        nl = defaultdict(int)
        for ch in codes:
            if ch not in LEGIT: nl[REASON.get(ch, 'other')] += 1
        # stuck: consecutive 'still' runs >=3 with codes not working and creep had a target (pending path)
        r['idle'] = dict(nl); r['idle_nl'] = sum(nl.values())
        r['cpu_t'] = round(m['cpu'] / (m['win'] * 5), 3) if m and m['win'] else None; r['cpu_max'] = round(m['mx'], 2) if m else None; r['fails'] = m['fails'] if m else 0
        # stuck = no move for >=3 consecutive sampled ticks while the window's target was set and code was 'q' (blocked) - approximated from codes 'q'
        r['stuck'] = nl.get('queue_blocked', 0)
        trip = 2 * 67 if role == 'rhauler' else 0
        scale = 1 / H
        r['lost_h'] = round(scale * (r['swamp'] + r['circle'] + 2 * r['bounce'] + r['idle_nl'] + r['part_short'] * trip), 1)
        r['empty_mv'] = round(r['empty_mv'] / r['moves'], 2) if r['moves'] else None
        r['part_short'] = round(r['part_short'], 2)
        out.append(r)
    out.sort(key=lambda r: -r['lost_h'])
    if '--json' in sys.argv: print(json.dumps(out, indent=1)); return
    print(f"motion audit last {H}h (UTC+8 now); lost_h = est. creep-ticks lost per hour")
    print(f"{'creep':18}{'role':9}{'smp':>5}{'mv':>5}{'lost/h':>7}{'swamp':>6}{'circ':>5}{'aba':>4}{'idleNL':>7}{'part':>6}{'empty%':>7}{'cpu/t':>7}{'cpuMx':>6}{'fail':>5}  idle reasons")
    for r in out:
        print(f"{r['creep']:18}{r['role']:9}{r['samples']:5}{r['moves']:5}{r['lost_h']:7}{r['swamp']:6}{r['circle']:5}{r['bounce']:4}{r['idle_nl']:7}{str(r['partial'])+'/'+str(r['departs']):>6}{'' if r['empty_mv'] is None else int(100*r['empty_mv']):>7}{r['cpu_t'] or '':>7}{r['cpu_max'] or '':>6}{r['fails']:5}  {r['idle']}")
    bad = [r for r in out if r['lost_h'] >= 60 or (r['cpu_max'] or 0) >= 2 or r['fails']]
    if '--patrol' in sys.argv: sys.exit(1 if bad else 0)
if __name__ == '__main__': main()
