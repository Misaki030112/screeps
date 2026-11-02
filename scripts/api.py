import json, urllib.request, urllib.error, base64, gzip, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = open(os.path.join(ROOT, '.env')).read().split('SCREEPS_TOKEN=')[1].split()[0]
SHARD = 'shard3'
def req(p, body=None):
    # WARNING: POST user/memory with only {"path","shard"} DELETES that Memory path (Screeps API).
    # Always use memory() for reads. For writes use memory_set(path, value). Never api.req('user/memory', {path}).
    if body is not None and p.rstrip('/').endswith('user/memory'):
        keys = set(body) - {'shard'}
        if keys == {'path'} or (keys <= {'path'}):
            raise ValueError('refusing Memory DELETE: POST user/memory with only path. Use memory() to read or memory_set(path, value) to write.')
    r = urllib.request.Request('https://screeps.com/api/' + p, data=json.dumps(body).encode() if body else None,
                               headers={'X-Token': TOKEN, 'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(r, timeout=30))
def memory_set(path, value):
    """POST Memory path = value (object/array/scalar). Never call with value omitted."""
    body = {'path': path, 'value': value, 'shard': SHARD}
    return req('user/memory', body)
# GET user/memory is capped at 1440/day per account and every routine/tool shares it (ran out 10-20 ~19:55, 429 for ~50 min).
# Each call is logged to metrics/api_memory.log (time, remaining, caller, path) so the budget can be audited per consumer.
def _log_mem(path, remaining):
    try:
        import sys, time
        with open(os.path.join(ROOT, 'metrics', 'api_memory.log'), 'a') as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}\t{remaining}\t{os.path.basename(sys.argv[0]) or '-'}\t{path}\n")
    except Exception: pass
def memory(path):
    r = urllib.request.Request(f'https://screeps.com/api/user/memory?path={path}&shard={SHARD}', headers={'X-Token': TOKEN})
    try:
        with urllib.request.urlopen(r, timeout=30) as x: rem = x.headers.get('X-RateLimit-Remaining'); j = json.load(x)
    except urllib.error.HTTPError as e:
        _log_mem(path, f'HTTP{e.code}'); raise
    _log_mem(path, rem)
    d = j['data']
    if isinstance(d, str) and d.startswith('gz:'): d = json.loads(gzip.decompress(base64.b64decode(d[3:])))
    return d
