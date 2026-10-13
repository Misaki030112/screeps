"""Run every panel query of grafana/dashboards/screeps.json through the Grafana API; prints OK/ERR + row count."""
import json, urllib.request, base64, os
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E = dict(l.strip().split('=', 1) for l in open(os.path.join(R, '.env')) if '=' in l)
d = json.load(open(os.path.join(R, 'grafana/dashboards/screeps.json'))); auth = base64.b64encode(f"admin:{E['GF_ADMIN_PASSWORD']}".encode()).decode()
for p in d['panels']:
    t = p['targets'][0]
    body = {'from': 'now-6h', 'to': 'now', 'queries': [{'refId': 'A', 'datasource': t['datasource'], 'rawSql': t['rawSql'], 'format': t['format'], 'rawQuery': True}]}
    r = urllib.request.Request('http://127.0.0.1:3000/api/ds/query', data=json.dumps(body).encode(), headers={'Content-Type': 'application/json', 'Authorization': 'Basic ' + auth})
    try:
        res = json.load(urllib.request.urlopen(r))['results']['A']; n = sum(len(f['data']['values'][0]) if f['data']['values'] else 0 for f in res.get('frames', []))
        print('OK ' if not res.get('error') else 'ERR', p['title'][:45], n, res.get('error', '')[:150])
    except Exception as e: print('EXC', p['title'][:45], getattr(e, 'read', lambda: b'')()[:200])
