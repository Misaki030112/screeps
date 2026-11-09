#!/usr/bin/env python3
"""Energy ledger snapshots + per-category e/t (Memory.ledger, src/utils/ledger.js).
Memory.ledger is cumulative since t0 (2026-11-09: ~190k ticks), so a single read cannot say where the last few hours went.
  python3 tools/ledger.py snap          read Memory.ledger via tools/q.py (console stream; no user/memory quota) and append
                                        {ts, t, ledger} to state/ledger_snaps.jsonl (one line ~1-2 KB)
  python3 tools/ledger.py diff [HOURS]  e/t per room/category between the newest snapshot and the newest one >= HOURS old
                                        (default: the previous snapshot). Categories: up upgrade, b build, rw/rr/rc/ro creep repair
                                        (wall/road/container/other, '@room' = remote), sp:<role> spawn body cost, tw/tr tower repair,
                                        th tower attack/heal, dr dropped, lk link loss. Note: `up` undercounts ~13% (docs/MODEL.md).
  python3 tools/ledger.py snapdiff [HOURS]  snap, then diff.
Read-only in game (one console expression). Added 2026-11-09 12h review: attribute W47 storage drops (defender spawn vs walls)."""
import sys, os, json, time
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SNAPS = os.path.join(ROOT, 'state', 'ledger_snaps.jsonl')
def load():
    try:
        with open(SNAPS) as f: return [json.loads(l) for l in f if l.strip()]
    except OSError: return []
def snap():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from q import q
    m = q('Memory.ledger ? {t0: Memory.ledger.t0, r: Memory.ledger.r} : null')
    v = m.get('v')
    if isinstance(v, str): v = json.loads(v) if v.startswith('{') else None
    if not v: raise SystemExit('ledger.py: no Memory.ledger / bad reply: ' + str(m)[:200])
    rec = {'ts': int(time.time()), 't': m['t'], 'ledger': v}
    with open(SNAPS, 'a') as f: f.write(json.dumps(rec, separators=(',', ':')) + '\n')
    print(f"snap t={m['t']} t0={v['t0']} rooms={','.join(sorted(v['r']))} -> {os.path.relpath(SNAPS, ROOT)}")
    return rec
def diff(hours=None):
    s = load()
    if len(s) < 2: raise SystemExit('ledger.py: need >= 2 snapshots (run `snap` again later)')
    b = s[-1]
    cands = [x for x in s[:-1] if x['ledger']['t0'] == b['ledger']['t0'] and (hours is None or b['ts'] - x['ts'] >= hours * 3600)]
    if not cands: raise SystemExit('ledger.py: no earlier snapshot with the same t0' + (f' >= {hours}h old' if hours else ''))
    a = cands[-1]; dt = b['t'] - a['t']
    if dt <= 0: raise SystemExit('ledger.py: tick delta <= 0')
    print(f"window t{a['t']}->t{b['t']} = {dt} ticks ({(b['ts'] - a['ts']) / 3600:.2f} h wall)")
    for rn in sorted(b['ledger']['r']):
        A, B = a['ledger']['r'].get(rn, {}), b['ledger']['r'][rn]
        rows = sorted(((k, (B[k] - A.get(k, 0)) / dt) for k in B), key=lambda kv: -kv[1])
        rows = [(k, v) for k, v in rows if v > 0.005]
        sp = sum(v for k, v in rows if k.startswith('sp:')); rep = sum(v for k, v in rows if k[:1] == 'r' or k in ('tw', 'tr'))
        wall = sum(v for k, v in rows if k in ('rw', 'tw'))
        print(f"{rn}: spawn {sp:.2f} e/t | repair {rep:.2f} (walls/ramparts {wall:.2f}) | up {B.get('up', 0) and (B['up'] - A.get('up', 0)) / dt:.2f} | build {(B.get('b', 0) - A.get('b', 0)) / dt:.2f}")
        print('   ' + '  '.join(f'{k}={v:.2f}' for k, v in rows))
if __name__ == '__main__':
    a = sys.argv[1:]
    if not a or a[0] not in ('snap', 'diff', 'snapdiff'): raise SystemExit(__doc__.strip())
    h = float(a[1]) if len(a) > 1 else None
    if a[0] in ('snap', 'snapdiff'): snap()
    if a[0] in ('diff', 'snapdiff'): diff(h)
