#!/usr/bin/env python3
"""Remote mining status: python3 tools/remote_status.py"""
import sys, os, json; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts')); import api
m = api.memory('remote') or {}
cr = api.memory('creeps') or {}
print('Memory.remote', json.dumps(m))
for n, c in cr.items():
    if c.get('remote'): print(' ', n, {k: c.get(k) for k in ('role', 'full', 'load', 'trips')})
st = api.memory('stats') or {}
print('cpu', st.get('cpu'), 'errors', (st.get('errors') or [])[:3])
