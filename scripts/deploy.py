#!/usr/bin/env python3
# run with .venv/bin/python (psycopg)
"""Deploy: lock -> node scripts/check.js -> upload dist/ -> record (tick, git commit) in TimescaleDB deploys -> unlock.
  python3 scripts/deploy.py "note"     (commit first so the tag is meaningful; a dirty tree is tagged <hash>+dirty)"""
import os, sys, json, subprocess, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
sys.path.insert(0, 'scripts'); sys.path.insert(0, 'tools'); import api, db
LOCK = 'state/deploy.lock'
own = not os.path.exists(LOCK)
if own: open(LOCK, 'w').write(f'deploy.py {time.strftime("%F %T")}\n')
try:
    subprocess.run(['node', 'scripts/check.js'], check=True)
    mods = {f[:-3]: open('dist/' + f).read() for f in os.listdir('dist')}
    print(api.req('user/code', {'branch': 'default', 'modules': mods}))
    h = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True).stdout.strip()
    if subprocess.run(['git', 'status', '--porcelain', 'src'], capture_output=True, text=True).stdout.strip(): h += '+dirty'
    t = api.req('game/time?shard=shard3')['time']
    with db.connect() as c: c.execute('INSERT INTO deploys VALUES (now(),%s,%s,%s)', (t, h, ' '.join(sys.argv[1:])))
    print('deployed', h, 'tick', t)
finally:
    if own: os.remove(LOCK)
