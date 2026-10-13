"""TimescaleDB access (postgres 17 on 127.0.0.1, db/user screeps, password PGPASSWORD in .env).
  .venv/bin/python tools/db.py --init      apply db/schema.sql (idempotent)
  .venv/bin/python tools/db.py "SQL"       run a query and print rows"""
import os, sys, psycopg
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = dict(l.strip().split('=', 1) for l in open(os.path.join(ROOT, '.env')) if '=' in l)
DSN = f"host=127.0.0.1 dbname=screeps user=screeps password={ENV['PGPASSWORD']}"
def connect(autocommit=True): return psycopg.connect(DSN, autocommit=autocommit)
def current_commit(c):
    r = c.execute('SELECT commit FROM deploys ORDER BY ts DESC LIMIT 1').fetchone(); return r[0] if r else None
if __name__ == '__main__':
    c = connect()
    if sys.argv[1:] == ['--init']: c.execute(open(os.path.join(ROOT, 'db', 'schema.sql')).read()); print('schema ok')
    else:
        cur = c.execute(sys.argv[1])
        if cur.description: print('\t'.join(d.name for d in cur.description)); [print('\t'.join(map(str, r))) for r in cur.fetchall()]
