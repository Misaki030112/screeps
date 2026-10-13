#!/usr/bin/env python3
"""Pull Memory.stats (incl. caught errors) from shard3 and store it in TimescaleDB (events kind=collect).
Note: raw console output is only available over the websocket; errors come from Memory.stats.errors."""
import json, time
import os, sys
try: import psycopg  # noqa
except ImportError:
    _py = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.venv', 'bin', 'python')
    if sys.executable == _py: raise
    os.execv(_py, [_py] + sys.argv)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools')); import db
from datetime import datetime, timezone
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts'))
from api import memory, req, ROOT
stats = memory('stats') or {}
row = {'ts': int(time.time()), 'stats': stats, 'world': req('user/world-status').get('status')}
with db.connect() as c:
    c.execute('INSERT INTO events (ts,tick,kind,msg,data) VALUES (now(),%s,%s,%s,%s)', (stats.get('time'), 'collect', row['world'], json.dumps(stats)))
print('collected tick', stats.get('time'), 'errors', len(stats.get('errors', [])))
