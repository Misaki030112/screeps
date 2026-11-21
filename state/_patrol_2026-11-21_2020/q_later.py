#!/usr/bin/env python3
import json, sys
from pathlib import Path
sys.path.insert(0, "/workspace/screeps/tools")
import q as qmod
OUT = Path("/workspace/screeps/state/_patrol_2026-11-21_2020")
qs = [
    ("later_snap", "({t:Game.time,b:Game.cpu.bucket,c:+Game.cpu.getUsed().toFixed(2),hs:Game.rooms.W46N8&&Game.rooms.W46N8.storage.store.energy,ws:Game.rooms.W47N8&&Game.rooms.W47N8.storage.store.energy,hp:Game.rooms.W46N8&&Game.rooms.W46N8.controller.progress,wp:Game.rooms.W47N8&&Game.rooms.W47N8.controller.progress,htl:Game.rooms.W46N8&&Game.rooms.W46N8.controller.progressTotal,wtl:Game.rooms.W47N8&&Game.rooms.W47N8.controller.progressTotal,ht:Game.rooms.W46N8&&Game.rooms.W46N8.controller.ticksToDowngrade,wt:Game.rooms.W47N8&&Game.rooms.W47N8.controller.ticksToDowngrade,sma:Game.rooms.W46N8&&Game.rooms.W46N8.controller.safeModeAvailable,smaW:Game.rooms.W47N8&&Game.rooms.W47N8.controller.safeModeAvailable})"),
    ("later_threat", "(()=>{const o=Memory.ops||{};const rem=o.rem||{};const p=n=>{const x=rem[n]||{};return x;}; return {t:Game.time,w8t:o.w8threat,w8f:o.w8flee,w8i:o.w8inv,w8up:o.w8up,seal:o.w8sealPark,w8soft:o.w8soft,w8day:{storE:o.w8day&&o.w8day.storE,keep:o.w8day&&o.w8day.upgKeep,upLatched:o.w8day&&o.w8day.upLatched,threatSoft:o.w8day&&o.w8day.threatSoft,sealPark:o.w8day&&o.w8day.sealPark,bankWhy:o.w8day&&o.w8day.bankWhy,upArm:o.w8day&&o.w8day.upArm,why:o.w8day&&o.w8day.why,upgraders:o.w8day&&o.w8day.upgraders},uf:o.upgFeed,rem};})()"),
    ("later_host", "(()=>{const r={}; for (const n of ['W46N8','W47N8','W45N8','W45N7','W47N7']){ const rm=Game.rooms[n]; if(!rm){r[n]={vis:false}; continue;} const h=rm.find(FIND_HOSTILE_CREEPS).map(c=>({n:c.name,own:c.owner&&c.owner.username,x:c.pos.x,y:c.pos.y,hits:c.hits,hM:c.hitsMax,ttl:c.ticksToLive,body:c.body.map(p=>p.type[0]).join('')})); const cores=rm.find(FIND_HOSTILE_STRUCTURES).filter(s=>s.structureType==STRUCTURE_INVADER_CORE).map(s=>({id:s.id,x:s.pos.x,y:s.pos.y,hits:s.hits,lv:s.level})); r[n]={vis:true,host:h,cores,hc:h.length,cc:cores.length,res:rm.controller&&rm.controller.reservation&&rm.controller.reservation.ticksToEnd};} return {t:Game.time,r};})()"),
    ("later_defs", "(()=>{const names=Object.keys(Game.creeps).filter(n=>/def|guard/i.test(n)||((Game.creeps[n].memory||{}).role||'').match(/def|guard/));const out={};for(const n of names){const cr=Game.creeps[n];out[n]={rm:cr.pos.roomName,x:cr.pos.x,y:cr.pos.y,sp:!!cr.spawning,hits:cr.hits,hM:cr.hitsMax,ttl:cr.ticksToLive||0,role:cr.memory&&cr.memory.role,st:cr.memory&&cr.memory.st,core:cr.memory&&cr.memory.core,mis:cr.memory&&cr.memory.mission,body:cr.body.map(p=>p.type[0]).join(''),spw:cr.spawning};} const roles={}; for(const n in Game.creeps){const r=(Game.creeps[n].memory&&Game.creeps[n].memory.role)||'?';roles[r]=(roles[r]||0)+1;} const spawns={}; for(const n of ['W46N8','W47N8']){const rm=Game.rooms[n]; if(!rm) continue; for(const s of rm.find(FIND_MY_SPAWNS)){ spawns[s.name]={rm:n,sp:s.spawning&&{name:s.spawning.name,need:s.spawning.needTime,rem:s.spawning.remainingTime}}; }} return {t:Game.time,out,roles,n:Object.keys(Game.creeps).length,spawns};})()"),
    ("later_lab2", "(()=>{const o=Memory.ops||{}; return {t:Game.time,labs:o.labs,koLab:(()=>{const labs=Game.rooms.W46N8&&Game.rooms.W46N8.find(FIND_MY_STRUCTURES).filter(s=>s.structureType==STRUCTURE_LAB); const out={}; for (const l of labs||[]){ out[l.id.slice(-4)]={m:l.mineralType,a:l.store&&(l.store[l.mineralType]||0),e:l.store&&l.store.energy}; } return out;})()};})()"),
]
for name, expr in qs:
    print("QUERY", name, "len", len(expr), flush=True)
    try:
        r = qmod.q(expr, timeout=35)
        (OUT / ("q_%s.json" % name)).write_text(json.dumps(r, indent=2, default=str) + "\n")
        print("OK", name, json.dumps(r, default=str)[:5000], flush=True)
    except Exception as e:
        print("FAIL", name, type(e).__name__, e, flush=True)
print("LATER_DONE", flush=True)
