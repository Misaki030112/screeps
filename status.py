#!/usr/bin/env python3
"""Print a readable colony summary from the latest metrics row (run collect.py first, or pass --live)."""
import json, os, sys, time
ROOT = os.path.dirname(os.path.abspath(__file__))
if '--live' in sys.argv: os.system(f'python3 {ROOT}/collect.py >/dev/null')
if '--map' in sys.argv: os.system(f'{ROOT}/.venv/bin/python {ROOT}/tools/render_live.py')
# prefer websocket stats (every 10 ticks) when newer
rows = open(os.path.join(ROOT, 'metrics', 'metrics.jsonl')).read().splitlines()
r = next(json.loads(x) for x in reversed(rows) if '"world"' in x); s = r['stats']
print(f"Collected {time.strftime('%F %H:%M', time.localtime(r['ts']))} (UTC+8)  tick {s.get('time')}  world={r['world']}")
g = s.get('gcl', {}); print(f"GCL {g.get('level')} ({g.get('progress',0):.0f}/{g.get('progressTotal',1):.0f})  CPU {s.get('cpu',0):.2f}  bucket {s.get('bucket')}")
for n, rm in s.get('rooms', {}).items():
    print(f"  {n}: RCL{rm['rcl']} {rm['progress']}/{rm['progressTotal']}  energy {rm['energy']}/{rm['energyCap']}  sites {rm['sites']}  hostiles {rm['hostiles']}  safeModes {rm['safeModeAvailable']}")
print('Creeps:', s.get('creeps'))
errs = s.get('errors', []); print(f"Errors (last {len(errs)}):"); [print('  ', e) for e in errs[-5:]]
lv = os.path.join(ROOT, 'metrics', 'live.json')
if os.path.exists(lv):
    L = json.load(open(lv)); w = L.get('stats') or {}
    print(f"\n[websocket live, updated {L.get('updated')} UTC+8] tick {w.get('t')} cpu {w.get('cpu')} bucket {w.get('b')} creeps {w.get('creeps')} rooms {w.get('rooms')}")
    if L.get('errors_tail'): print('Recent console errors:'); [print('  ', e) for e in L['errors_tail'][-5:]]
ca = os.path.join(ROOT, 'metrics', 'creep_audit.json')
if os.path.exists(ca):
    A = json.load(open(ca)); print(f"\n[creep audit {A['generated']} UTC+8, deploy {A.get('deploy', {}).get('commit')}]  (tools/creep_audit.py)")
    for w, v in A['windows'].items():
        r = v['roles']; print(f"  {w}: creep CPU/t {round(sum(m['cpu_t_sum'] for m in r.values()), 2)}  stuck {sum(m['stuck'] for m in r.values())}  osc {sum(m['osc'] for m in r.values())}  worst " +
              ', '.join(f"{x['name']}({x['score']})" for x in v['worst'][:3]))
    for k, v in A.get('regressions', {}).items():
        if v: print(f'  REGRESSION [{k}]: ' + '; '.join(v))
