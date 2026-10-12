#!/usr/bin/env python3
"""Pull Memory.stats (incl. caught errors) from shard3 and append to metrics/metrics.jsonl.
Note: raw console output is only available over the websocket; errors come from Memory.stats.errors."""
import json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts'))
from api import memory, req, ROOT
stats = memory('stats') or {}
row = {'ts': int(time.time()), 'stats': stats, 'world': req('user/world-status').get('status')}
os.makedirs(os.path.join(ROOT, 'metrics'), exist_ok=True)
with open(os.path.join(ROOT, 'metrics', 'metrics.jsonl'), 'a') as f: f.write(json.dumps(row) + '\n')
print('collected tick', stats.get('time'), 'errors', len(stats.get('errors', [])))
