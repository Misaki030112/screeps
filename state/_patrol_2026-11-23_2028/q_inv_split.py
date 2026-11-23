#!/usr/bin/env python3
import sys, json
from pathlib import Path
sys.path.insert(0, '/workspace/screeps/tools')
import q as qmod
OUT = Path('/workspace/screeps/state/_patrol_2026-11-23_2028')
qs = [
  ('inv_defs', open(OUT/'q_inv_defs.expr.js').read()),
  ('inv_spawns', open(OUT/'q_inv_spawns.expr.js').read()),
  ('inv_host', open(OUT/'q_inv_host.expr.js').read()),
]
for name, expr in qs:
    print('QUERY', name, 'len', len(expr), flush=True)
    r = qmod.q(expr, timeout=40)
    OUT.joinpath('q_%s.json' % name).write_text(json.dumps(r, indent=2, default=str) + chr(10))
    print(json.dumps(r, default=str, indent=2), flush=True)
