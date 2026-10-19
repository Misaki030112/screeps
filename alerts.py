#!/usr/bin/env python3
"""Pending (unacknowledged) attack alerts.
  python3 alerts.py                 print pending alerts; exit code 0 = none, 1 = only low, 2 = medium/high pending
  python3 alerts.py --json          same, machine-readable
  python3 alerts.py --ack [ID|all]  acknowledge
  python3 alerts.py --all           include acknowledged"""
import json
import os, sys
try: import psycopg  # noqa
except ImportError:
    _py = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.venv', 'bin', 'python')
    if sys.executable == _py: raise
    os.execv(_py, [_py] + sys.argv)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools')); import db
# 14:23 north watch (W47N8/W47N9/W48N9 via API) feeds alert_state before we read it; best effort, never blocks the alert check
if '--ack' not in sys.argv and '--no-scan' not in sys.argv:
    import subprocess
    try: subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools', 'north_watch.py'), '--quiet'], timeout=90)
    except Exception as ex: print('north_watch failed:', str(ex)[:120])
c = db.connect()
st = {e: {'severity': sev, 'first': f, 'latest': l, 'acked': ak, 'ended': en, 'seen': seen.astimezone().strftime('%F %T')}
      for e, sev, f, l, ak, en, seen in c.execute('SELECT episode, severity, first, latest, acked, ended, seen FROM alert_state').fetchall()}
if '--ack' in sys.argv:
    i = sys.argv.index('--ack'); tgt = sys.argv[i+1] if len(sys.argv) > i+1 else 'all'
    if tgt == 'all': c.execute('UPDATE alert_state SET acked=true')
    else: c.execute('UPDATE alert_state SET acked=true WHERE episode=%s', (tgt,))
    print('acked', tgt); sys.exit(0)
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
