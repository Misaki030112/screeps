#!/usr/bin/env python3
import sys, json
from pathlib import Path
sys.path.insert(0, "/workspace/screeps/tools")
import q as qmod
OUT = Path("/workspace/screeps/state/_patrol_2026-11-20_1316")
qs = [
    ("opskeys", "({t:Game.time,keys:Object.keys(Memory.ops||{}),seal:Memory.ops&&Memory.ops.sealPark,soft:Memory.ops&&Memory.ops.softCap,soft2:Memory.ops&&Memory.ops.softCap2,bank:Memory.ops&&Memory.ops.bankWhy})"),
    ("wminers", "(()=>{const out={};for(const n in Game.creeps){const cr=Game.creeps[n];const role=(cr.memory||{}).role||'';if(role!=='w8miner'&&!n.startsWith('w8miner'))continue;out[n]={rm:cr.pos.roomName,x:cr.pos.x,y:cr.pos.y,ttl:cr.ticksToLive||0,sp:!!cr.spawning,st:cr.memory&&cr.memory.st,src:cr.memory&&cr.memory.src,hits:cr.hits,e:cr.store&&cr.store.energy||0};}return {t:Game.time,out};})()"),
    ("later", "({t:Game.time,b:Game.cpu.bucket,c:+Game.cpu.getUsed().toFixed(2),hs:Game.rooms.W46N8&&Game.rooms.W46N8.storage.store.energy,ws:Game.rooms.W47N8&&Game.rooms.W47N8.storage.store.energy,hp:Game.rooms.W46N8&&Game.rooms.W46N8.controller.progress,wp:Game.rooms.W47N8&&Game.rooms.W47N8.controller.progress,nUp:Memory.ops&&Memory.ops.upgFeed&&Memory.ops.upgFeed.nUp,why:Memory.ops&&Memory.ops.upgFeed&&Memory.ops.upgFeed.why,rem:Memory.ops&&Memory.ops.upgFeed&&Memory.ops.upgFeed.rem})"),
    ("w8ups", "(()=>{const out={};for(const n in Game.creeps){const cr=Game.creeps[n];const role=(cr.memory||{}).role||'';if(role!=='w8upgrader'&&!n.startsWith('w8upgrader'))continue;out[n]={rm:cr.pos.roomName,x:cr.pos.x,y:cr.pos.y,ttl:cr.ticksToLive||0,sp:!!cr.spawning,e:cr.store&&cr.store.energy||0};}return {t:Game.time,out};})()"),
]
for name, expr in qs:
    print("QUERY", name, "len", len(expr), flush=True)
    try:
        r = qmod.q(expr, timeout=35)
        (OUT / ("q_%s.json" % name)).write_text(json.dumps(r, indent=2, default=str) + "\n")
        print("OK", name, json.dumps(r, default=str)[:2000], flush=True)
    except Exception as e:
        print("FAIL", name, type(e).__name__, e, flush=True)
