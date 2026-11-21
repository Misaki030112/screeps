#!/usr/bin/env python3
import sys, json
from pathlib import Path
sys.path.insert(0, "/workspace/screeps/tools")
import q as qmod
OUT = Path("/workspace/screeps/state/_patrol_2026-11-21_1918")
qs = [
    ("later", "({t:Game.time,b:Game.cpu.bucket,hs:Game.rooms.W46N8&&Game.rooms.W46N8.storage.store.energy,ws:Game.rooms.W47N8&&Game.rooms.W47N8.storage.store.energy,hp:Game.rooms.W46N8&&Game.rooms.W46N8.controller.progress,wp:Game.rooms.W47N8&&Game.rooms.W47N8.controller.progress,nUp:Memory.ops&&Memory.ops.upgFeed&&Memory.ops.upgFeed.nUp,why:Memory.ops&&Memory.ops.upgFeed&&Memory.ops.upgFeed.why,ea:Game.rooms.W46N8&&Game.rooms.W46N8.energyAvailable,eaw:Game.rooms.W47N8&&Game.rooms.W47N8.energyAvailable})"),
    ("later2", "(()=>{const o=Memory.ops||{}; const d=o.w8day||{}; return {t:Game.time,keep:d.upgKeep||d.keep,upLatched:d.upLatched,threatSoft:d.threatSoft,sealPark:d.sealPark,softCap2:d.softCap2,bankWhy:d.bankWhy,storE:d.storE,w8up:d.upgraders,eAvail:d.eAvail,hubReady:d.hubReady};})()"),
]
for name, expr in qs:
    print("QUERY", name, flush=True)
    try:
        r = qmod.q(expr, timeout=35)
        (OUT / ("q_%s.json" % name)).write_text(json.dumps(r, indent=2, default=str) + "\n")
        print("OK", name, json.dumps(r, default=str)[:2000], flush=True)
    except Exception as e:
        print("FAIL", name, type(e).__name__, e, flush=True)
