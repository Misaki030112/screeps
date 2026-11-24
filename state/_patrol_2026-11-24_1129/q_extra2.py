#!/usr/bin/env python3
import sys, json
from pathlib import Path
sys.path.insert(0, "/workspace/screeps/tools")
import q as qmod
OUT = Path("/workspace/screeps/state/_patrol_2026-11-24_1129")
qs = [
    ("r7", "(Memory.ops&&Memory.ops.r7)"),
    ("rem2", "(()=>{const o=Memory.ops||{}; return {t:Game.time, rem:o.rem, rem2:o.remotes, rstates:o.rstates, threat:o.threat};})()"),
    ("misc", "(()=>{const o=Memory.ops||{}; return {t:Game.time, fm:o.fm, mineralCap:o.mineralCap, labReady:o.labReady, auditSnap:o.auditSnap&&Object.keys(o.auditSnap)};})()"),
]
for name, expr in qs:
    print("QUERY", name, "len", len(expr), flush=True)
    try:
        r = qmod.q(expr, timeout=35)
        (OUT / ("q_%s.json" % name)).write_text(json.dumps(r, indent=2, default=str) + "\n")
        print("OK", name, json.dumps(r, default=str)[:3000], flush=True)
    except Exception as e:
        print("FAIL", name, type(e).__name__, e, flush=True)
