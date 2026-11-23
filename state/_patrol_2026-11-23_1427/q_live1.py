#!/usr/bin/env python3
import sys, json
from pathlib import Path
sys.path.insert(0, "/workspace/screeps/tools")
import q as qmod
OUT = Path("/workspace/screeps/state/_patrol_2026-11-23_1427")
qs = [
    ("snap", "({t:Game.time,b:Game.cpu.bucket,c:+Game.cpu.getUsed().toFixed(2),hs:Game.rooms.W46N8&&Game.rooms.W46N8.storage.store.energy,ws:Game.rooms.W47N8&&Game.rooms.W47N8.storage.store.energy,hp:Game.rooms.W46N8&&Game.rooms.W46N8.controller.progress,wp:Game.rooms.W47N8&&Game.rooms.W47N8.controller.progress,ht:Game.rooms.W46N8&&Game.rooms.W46N8.controller.ticksToDowngrade,wt:Game.rooms.W47N8&&Game.rooms.W47N8.controller.ticksToDowngrade,sma:Game.rooms.W46N8&&Game.rooms.W46N8.controller.safeModeAvailable,smaW:Game.rooms.W47N8&&Game.rooms.W47N8.controller.safeModeAvailable,gcl:Game.gcl.level,gp:Game.gcl.progress})"),
    ("cmd", "({t:Game.time,cmd:Memory.cmd})"),
    ("ops1", "(()=>{const o=Memory.ops||{};const rem=o.rem||{};const p=n=>{const x=rem[n]||{};return {st:x.st||x.state,why:x.why,inc:x.inc,core:!!x.core,def:x.def,since:x.since}};return {t:Game.time,w8t:o.w8threat,seal:o.sealPark,soft:o.softCap2,bank:o.bankWhy,labs:o.labs,W45N8:p('W45N8'),W45N7:p('W45N7'),W47N7:p('W47N7')};})()"),
    ("uf", "(Memory.ops&&Memory.ops.upgFeed)"),
]
for name, expr in qs:
    print("QUERY", name, "len", len(expr), flush=True)
    try:
        r = qmod.q(expr, timeout=35)
        (OUT / ("q_%s.json" % name)).write_text(json.dumps(r, indent=2, default=str) + "\n")
        print("OK", name, json.dumps(r, default=str)[:2500], flush=True)
    except Exception as e:
        print("FAIL", name, type(e).__name__, e, flush=True)
