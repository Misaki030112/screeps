#!/usr/bin/env python3
"""Print a readable colony summary from the latest metrics row (run collect.py first, or pass --live)."""
import json, time
import os, sys
try: import psycopg  # noqa
except ImportError:
    _py = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.venv', 'bin', 'python')
    if sys.executable == _py: raise
    os.execv(_py, [_py] + sys.argv)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools')); import db
ROOT = os.path.dirname(os.path.abspath(__file__))
if '--live' in sys.argv: os.system(f'{sys.executable} {ROOT}/collect.py >/dev/null')
if '--map' in sys.argv: os.system(f'{ROOT}/.venv/bin/python {ROOT}/tools/render_live.py')
c = db.connect()
r = c.execute("SELECT ts, tick, msg, data FROM events WHERE kind='collect' ORDER BY ts DESC LIMIT 1").fetchone()
if r:
    ts, t, world, s = r
    print(f"Collected {ts.astimezone().strftime('%F %H:%M')} (UTC+8)  tick {s.get('time')}  world={world}")
    g = s.get('gcl', {}); print(f"GCL {g.get('level')} ({g.get('progress',0):.0f}/{g.get('progressTotal',1):.0f})  CPU {s.get('cpu',0):.2f}  bucket {s.get('bucket')}")
    errs = s.get('errors', []); print(f"Errors (last {len(errs)}):"); [print('  ', e) for e in errs[-5:]]
print('Last hour (room_stats_10m / room_stats):')
for row in c.execute("""SELECT room, max(rcl), max(progress)-min(progress), round(avg(cpu)::numeric,2), round(max(cpu)::numeric,2), min(bucket), round(avg(trace_cpu)::numeric,3), max(tick)-min(tick)
                        FROM room_stats WHERE ts > now()-interval '1 hour' GROUP BY room""").fetchall():
    print(f"  {row[0]}: RCL{row[1]} +{row[2]} progress  cpu avg {row[3]} max {row[4]}  bucket min {row[5]}  trace cpu {row[6]}  ({row[7]} ticks)")
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
