#!/usr/bin/env python3
import sys, json
from pathlib import Path
sys.path.insert(0, "/workspace/screeps/tools")
import q as qmod
OUT = Path("/workspace/screeps/state/_patrol_2026-11-20_1923")
qs = [
    ("opskeys", "({t:Game.time,keys:Object.keys(Memory.ops||{})})"),
    ("remraw", "({t:Game.time,rem:Memory.ops&&Memory.ops.rem})"),
    ("w8ops", "(()=>{const o=Memory.ops||{};const pick=k=>({[k]:o[k]}); const ks=Object.keys(o).filter(k=>/w8|seal|soft|bank|keep|arm|latch|threat|hold/i.test(k)); const out={t:Game.time}; for(const k of ks) out[k]=o[k]; return out;})()"),
    ("resv", "(()=>{const r={}; for(const n of ['W45N8','W45N7','W47N7']){const rm=Game.rooms[n]; const c=rm&&rm.controller; r[n]={vis:!!rm,res:c&&c.reservation&&c.reservation.ticksToEnd,own:c&&c.reservation&&c.reservation.username,host:rm?rm.find(FIND_HOSTILE_CREEPS).length:null,core:rm?rm.find(FIND_HOSTILE_STRUCTURES).filter(s=>s.structureType==STRUCTURE_INVADER_CORE).length:null};} return {t:Game.time,r};})()"),
]
for name, expr in qs:
    print("QUERY", name, "len", len(expr), flush=True)
    try:
        r = qmod.q(expr, timeout=35)
        (OUT / ("q_%s.json" % name)).write_text(json.dumps(r, indent=2, default=str) + "\n")
        print("OK", name, json.dumps(r, default=str)[:3500], flush=True)
    except Exception as e:
        print("FAIL", name, type(e).__name__, e, flush=True)
