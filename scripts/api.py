import json, urllib.request, base64, gzip, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = open(os.path.join(ROOT, '.env')).read().split('SCREEPS_TOKEN=')[1].split()[0]
SHARD = 'shard3'
def req(p, body=None):
    r = urllib.request.Request('https://screeps.com/api/' + p, data=json.dumps(body).encode() if body else None,
                               headers={'X-Token': TOKEN, 'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(r, timeout=30))
def memory(path):
    d = req(f'user/memory?path={path}&shard={SHARD}')['data']
    if isinstance(d, str) and d.startswith('gz:'): d = json.loads(gzip.decompress(base64.b64decode(d[3:])))
    return d
