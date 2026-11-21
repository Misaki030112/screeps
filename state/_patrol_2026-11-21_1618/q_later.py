#!/usr/bin/env python3
import sys, json
from pathlib import Path
sys.path.insert(0, "/workspace/screeps/tools")
import q as qmod
OUT = Path("/workspace/screeps/state/_patrol_2026-11-21_1618")
qs = [
    ("later", "({t:Game.time,b:Game.cpu.bucket,c:+Game.cpu.getUsed().toFixed(2),hs:Game.rooms.W46N8&&Game.rooms.W46N8.storage.store.energy,ws:Game.rooms.W47N8&&Game.rooms.W47N8.storage.store.energy,hp:Game.rooms.W46N8&&Game.rooms.W46N8.controller.progress,wp:Game.rooms.W47N8&&Game.rooms.W47N8.controller.progress,nUp:Memory.ops&&Memory.ops.upgFeed&&Memory.ops.upgFeed.nUp,why:Memory.ops&&Memory.ops.upgFeed&&Memory.ops.upgFeed.why,rem:Memory.ops&&Memory.ops.upgFeed&&Memory.ops.upgFeed.rem,keep:Memory.ops&&Memory.ops.w8day&&Memory.ops.w8day.upgKeep,latch:Memory.ops&&Memory.ops.w8day&&Memory.ops.w8day.upLatched,seal:Memory.ops&&Memory.ops.w8day&&Memory.ops.w8day.sealPark,thSoft:Memory.ops&&Memory.ops.w8day&&Memory.ops.w8day.threatSoft,softLeft:Memory.ops&&Memory.ops.w8day&&Memory.ops.w8day.softLeft,w8up:Memory.ops&&Memory.ops.w8day&&Memory.ops.w8day.upgraders})"),
    ("resv2", "(()=>{const r={}; for(const n of ['W45N8','W45N7','W47N7']){const rm=Game.rooms[n]; const c=rm&&rm.controller; r[n]={vis:!!rm,res:c&&c.reservation&&c.reservation.ticksToEnd,own:c&&c.reservation&&c.reservation.username,host:rm?rm.find(FIND_HOSTILE_CREEPS).length:null,core:rm?rm.find(FIND_HOSTILE_STRUCTURES).filter(s=>s.structureType==STRUCTURE_INVADER_CORE).length:null};} return {t:Game.time,r};})()"),
]
for name, expr in qs:
    print("QUERY", name, flush=True)
    try:
        r = qmod.q(expr, timeout=35)
        (OUT / ("q_%s.json" % name)).write_text(json.dumps(r, indent=2, default=str) + "\n")
        print("OK", name, json.dumps(r, default=str)[:2000], flush=True)
    except Exception as e:
        print("FAIL", name, type(e).__name__, e, flush=True)
print("DONE")
