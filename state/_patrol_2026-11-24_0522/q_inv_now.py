#!/usr/bin/env python3
import sys, json
from pathlib import Path
sys.path.insert(0, '/workspace/screeps/tools')
import q as qmod
OUT = Path('/workspace/screeps/state/_patrol_2026-11-24_0522')
expr = open('/workspace/screeps/state/_patrol_2026-11-24_0522/q_inv_now.expr.js').read()
print('QUERY inv_now', flush=True)
r = qmod.q(expr, timeout=40)
OUT.joinpath('q_inv_now.json').write_text(json.dumps(r, indent=2, default=str) + chr(10))
print(json.dumps(r, default=str, indent=2), flush=True)
