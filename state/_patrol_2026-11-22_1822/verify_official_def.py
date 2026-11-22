import json, gzip, urllib.request
from io import BytesIO

def fetch(room, base):
    url = f'https://screeps.com/room-history/shard3/{room}/{base}.json'
    req = urllib.request.Request(url, headers={'Accept-Encoding': 'gzip, deflate', 'User-Agent': 'patrol'})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read()
            if raw[:2] == b'\x1f\x8b':
                raw = gzip.decompress(raw)
            return r.status, json.loads(raw.decode())
    except urllib.error.HTTPError as e:
        return e.code, None

def find_def(rec):
    hits = []
    def walk(obj):
        if isinstance(obj, dict):
            name = obj.get('name') or obj.get('n')
            if name == 'defender84418409':
                hits.append({k: obj.get(k) for k in ('x','y','name','n','hits','usr','type')})
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)
    walk(rec)
    return hits

for room, base in [('W46N8', 84418500), ('W45N8', 84418500), ('W47N8', 84418500), ('W45N8', 84418600), ('W45N8', 84418800)]:
    code, data = fetch(room, base)
    print(f'=== {room}@{base} HTTP {code} ===')
    if not data:
        continue
    ticks = data.get('ticks') or data
    if not isinstance(ticks, dict):
        print(' unexpected', type(ticks), str(data)[:200])
        continue
    keys = sorted(int(k) for k in ticks if str(k).isdigit())
    print(' ticks', keys[0] if keys else None, '..', keys[-1] if keys else None, 'n', len(keys))
    found = 0
    want = {84418570,84418578,84418579,84418593,84418594,84418600,84418694,84418695,84418897,84418898,84418899,84418900}
    positions = []
    for t in keys:
        rec = ticks.get(str(t), ticks.get(t))
        hs = find_def(rec) if rec else []
        if hs:
            found += 1
            positions.append((t, hs[0]))
            if t in want or found <= 3:
                print(' ', t, hs[0])
    print('  defender ticks', found, 'first', positions[0] if positions else None, 'last', positions[-1] if positions else None)
    # jumps
    prev = None
    for t, h in positions:
        x, y = h.get('x'), h.get('y')
        if prev is not None:
            dt = t - prev[0]
            dx = abs((x or 0) - (prev[1] or 0))
            dy = abs((y or 0) - (prev[2] or 0))
            step = max(dx, dy)
            if step > dt:
                print('  JUMP', prev, '->', (t, x, y), 'chebyshev', step, 'dt', dt)
        prev = (t, x, y)

