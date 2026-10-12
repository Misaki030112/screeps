#!/usr/bin/env python3
"""Pending (unacknowledged) attack alerts.
  python3 alerts.py                 print pending alerts; exit code 0 = none, 1 = only low, 2 = medium/high pending
  python3 alerts.py --json          same, machine-readable
  python3 alerts.py --ack [ID|all]  acknowledge
  python3 alerts.py --all           include acknowledged"""
import json, os, sys
P = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'metrics', 'alerts_state.json')
st = json.load(open(P)) if os.path.exists(P) else {}
if '--ack' in sys.argv:
    i = sys.argv.index('--ack'); tgt = sys.argv[i+1] if len(sys.argv) > i+1 else 'all'
    for k, v in st.items():
        if tgt in ('all', k): v['acked'] = True
    json.dump(st, open(P + '.tmp', 'w'), indent=1); os.replace(P + '.tmp', P); print('acked', tgt); sys.exit(0)
pend = {k: v for k, v in st.items() if '--all' in sys.argv or not v['acked']}
if '--json' in sys.argv: print(json.dumps(pend))
elif not pend: print('No pending alerts.')
else:
    for k, v in sorted(pend.items(), key=lambda kv: kv[1]['latest']['tick']):
        a = v['latest']; f = v['first']
        print(f"[{v['severity'].upper()}] {k}  owner={a['owner']}  room={a['room']}  ticks {f['tick']}..{a['tick']}  {'ENDED' if v['ended'] else 'ONGOING'}  first seen {v['seen']} UTC+8")
        print(f"    creeps={f.get('creeps', a.get('maxCreeps'))} body={f.get('body') or a.get('body')} totalDamage={a.get('totalDamage')} hitLoss={a.get('structureHitLoss')} damaged={a.get('damaged')}")
rank = max([{'low': 1, 'medium': 2, 'high': 2}.get(v['severity'], 1) for v in pend.values()] or [0])
sys.exit(rank)
