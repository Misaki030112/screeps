#!/usr/bin/env python3
# run with .venv/bin/python (psycopg)
"""Deploy: lock -> node scripts/check.js -> upload dist/ -> record (tick, git commit) in TimescaleDB deploys -> unlock.
  python3 scripts/deploy.py "note"     (commit first so the tag is meaningful; a dirty tree is tagged <hash>+dirty)"""
import os, sys, json, subprocess, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
sys.path.insert(0, 'scripts'); sys.path.insert(0, 'tools'); import api, db
LOCK = 'state/deploy.lock'
WAIT, STALE = 300, 900   # wait up to 5 min for another deploy; a lock older than 15 min is considered dead
def acquire():
    t0 = time.time()
    while True:
        try:
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)   # atomic: only one deploy can win
            os.write(fd, f'deploy.py pid={os.getpid()} {time.strftime("%F %T")}\n'.encode()); os.close(fd); return
        except FileExistsError:
            try: age = time.time() - os.path.getmtime(LOCK)
            except FileNotFoundError: continue
            if age > STALE: print(f'removing stale lock ({age:.0f}s)'); os.remove(LOCK); continue
            if time.time() - t0 > WAIT: sys.exit(f'deploy.lock held by: {open(LOCK).read().strip()} -- refusing to deploy')
            print('deploy.lock held, waiting...'); time.sleep(5)
acquire()
try:
    subprocess.run(['node', 'scripts/check.js'], check=True)
    mods = {f[:-3]: open('dist/' + f).read() for f in os.listdir('dist')}
    print(api.req('user/code', {'branch': 'default', 'modules': mods}))
    h = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(['git', 'status', '--porcelain', 'src'], capture_output=True, text=True).stdout.split('\n')
    dirty = [l[3:].strip() for l in dirty if l.strip()]
    note = ' '.join(sys.argv[1:])
    if dirty:   # name the uncommitted files that went live (17:32/17:44 '+dirty' deploys carried other agents' edits untraced)
        h += '+dirty'; note = (note + ' ' if note else '') + '[dirty: ' + ', '.join(dirty) + ']'
        print('WARNING: deploying uncommitted src edits:', ', '.join(dirty))
    t = api.req('game/time?shard=shard3')['time']
    with db.connect() as c: c.execute('INSERT INTO deploys VALUES (now(),%s,%s,%s)', (t, h, note))
    print('deployed', h, 'tick', t)
finally:
    os.remove(LOCK)
