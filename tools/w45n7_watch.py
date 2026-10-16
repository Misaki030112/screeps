#!/usr/bin/env python3
"""W45N7 bootstrap watch: python3 tools/w45n7_watch.py (creep positions, reservation, container site, spawn, errors)."""
import sys, os, json; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts')); import api
t = api.req('game/time?shard=shard3')['time']
m = (api.memory('remote') or {}).get('W45N7', {})
print('tick', t, 'W45N7 mem', json.dumps({k: m.get(k) for k in ('res', 'cont', 'siteProg', 'seen', 'foreign', 'th', 'lastRh', 'armed')}))
mine = {}
for rn in ('W46N8', 'W45N8', 'W45N7'):
    for o in api.req(f'game/room-objects?room={rn}&shard=shard3')['objects']:
        if o['type'] == 'creep' and o.get('user') == '6010ee96cbca26e9512da6f0': mine[o['name']] = (rn, o['x'], o['y'], o.get('ageTime', 0) - t, o.get('store', {}).get('energy', 0))
        if rn == 'W46N8' and o['type'] == 'spawn': print('spawn', o.get('spawning'), 'store', o.get('store'))
        if rn == 'W46N8' and o['type'] == 'storage': print('storage', o.get('store'))
        if rn == 'W46N8' and o['type'] == 'controller': print('ctl', o.get('level'), o.get('progress'))
        if rn == 'W45N7' and o['type'] in ('controller', 'constructionSite', 'container'): print(' W45N7', o['type'], o['x'], o['y'], o.get('reservation'), o.get('progress'), o.get('user'), o.get('hits'))
cr = api.memory('creeps') or {}
for n, c in sorted(cr.items()):
    if c.get('remote') in ('W45N7',) or c.get('role') in ('defender', 'rscout') or c.get('remote') == 'W45N7': print(' ', n, c.get('role'), c.get('remote'), mine.get(n), {k: c.get(k) for k in ('travel', 'full', 'patrol')})
roles = {}
for n, c in cr.items(): roles.setdefault((c.get('role'), c.get('remote')), 0); roles[(c.get('role'), c.get('remote'))] += 1
print('roles', sorted(((str(k)), v) for k, v in roles.items()))
st = api.memory('stats') or {}
print('cpu', st.get('cpu'), 'errors', (st.get('errors') or [])[:3])
