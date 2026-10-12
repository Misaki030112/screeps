#!/usr/bin/env python3
"""Print a readable colony summary from the latest metrics row (run collect.py first, or pass --live)."""
import json, os, sys, time
ROOT = os.path.dirname(os.path.abspath(__file__))
if '--live' in sys.argv: os.system(f'python3 {ROOT}/collect.py >/dev/null')
rows = open(os.path.join(ROOT, 'metrics', 'metrics.jsonl')).read().splitlines()
r = json.loads(rows[-1]); s = r['stats']
print(f"Collected {time.strftime('%F %H:%M', time.localtime(r['ts']))} (UTC+8)  tick {s.get('time')}  world={r['world']}")
g = s.get('gcl', {}); print(f"GCL {g.get('level')} ({g.get('progress',0):.0f}/{g.get('progressTotal',1):.0f})  CPU {s.get('cpu',0):.2f}  bucket {s.get('bucket')}")
for n, rm in s.get('rooms', {}).items():
    print(f"  {n}: RCL{rm['rcl']} {rm['progress']}/{rm['progressTotal']}  energy {rm['energy']}/{rm['energyCap']}  sites {rm['sites']}  hostiles {rm['hostiles']}  safeModes {rm['safeModeAvailable']}")
print('Creeps:', s.get('creeps'))
errs = s.get('errors', []); print(f"Errors (last {len(errs)}):"); [print('  ', e) for e in errs[-5:]]
