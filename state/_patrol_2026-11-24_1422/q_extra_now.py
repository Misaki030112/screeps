#!/usr/bin/env python3
import sys, json
from pathlib import Path
sys.path.insert(0, "/workspace/screeps/tools")
import q as qmod
OUT = Path("/workspace/screeps/state/_patrol_2026-11-24_1422")
qs = [
    ("r7", "({t:Game.time,r7:Memory.ops&&Memory.ops.r7})"),
    ("sites", "(()=>{const o={}; for (const id in Game.constructionSites){const s=Game.constructionSites[id]; o[id]={rm:s.pos.roomName,x:s.pos.x,y:s.pos.y,st:s.structureType,p:s.progress,t:s.progressTotal};} return {t:Game.time,n:Object.keys(o).length,o};})()"),
    ("road3744", "(()=>{const rm=Game.rooms.W47N8; if(!rm) return {t:Game.time,vis:false}; const s=rm.lookForAt(LOOK_STRUCTURES,37,44); const c=rm.lookForAt(LOOK_CONSTRUCTION_SITES,37,44); return {t:Game.time,vis:true,s:s.map(x=>({st:x.structureType,hits:x.hits,hitsMax:x.hitsMax})),c:c.map(x=>({st:x.structureType,p:x.progress,t:x.progressTotal}))};})()"),
    ("resnames", "(()=>{const out=[]; for (const n in Game.creeps){const cr=Game.creeps[n]; const r=(cr.memory&&cr.memory.role)||''; if(/reserv|miner|queen|filler|upgrader/i.test(r)||/reserv|miner|queen|filler|upgrader/i.test(n)) out.push({n,r,rm:cr.pos.roomName,x:cr.pos.x,y:cr.pos.y,sp:!!cr.spawning,ttl:cr.ticksToLive||0,hits:cr.hits});} return {t:Game.time,out};})()"),
]
for name, expr in qs:
    print("QUERY", name, "len", len(expr), flush=True)
    try:
        r = qmod.q(expr, timeout=35)
        (OUT / ("q_%s.json" % name)).write_text(json.dumps(r, indent=2, default=str) + "\n")
        print("OK", name, json.dumps(r, default=str)[:4000], flush=True)
    except Exception as e:
        print("FAIL", name, type(e).__name__, e, flush=True)
