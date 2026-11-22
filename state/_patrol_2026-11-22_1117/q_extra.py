#!/usr/bin/env python3
import json, sys
from pathlib import Path
sys.path.insert(0, "/workspace/screeps/tools")
import q as qmod
OUT = Path("/workspace/screeps/state/_patrol_2026-11-22_1117")
qs = [
    ("host", "(()=>{const r={}; for (const n of ['W46N8','W47N8','W45N8','W45N7','W47N7']){ const rm=Game.rooms[n]; if(!rm){r[n]={vis:false}; continue;} const h=rm.find(FIND_HOSTILE_CREEPS).map(c=>({n:c.name,own:c.owner&&c.owner.username,x:c.pos.x,y:c.pos.y,hits:c.hits,ttl:c.ticksToLive,body:c.body.map(p=>p.type[0]).join('')})); const cores=rm.find(FIND_HOSTILE_STRUCTURES).filter(s=>s.structureType==STRUCTURE_INVADER_CORE).map(s=>({id:s.id,x:s.pos.x,y:s.pos.y,hits:s.hits,lv:s.level})); r[n]={vis:true,host:h,cores,hc:h.length,cc:cores.length};} return {t:Game.time,r};})()"),
    ("ups", "(()=>{const o={}; for (const n in Game.creeps){ const c=Game.creeps[n]; const role=(c.memory&&c.memory.role)||''; if(!/upg/i.test(n+role)) continue; o[n]={rm:c.pos.roomName,x:c.pos.x,y:c.pos.y,ttl:c.ticksToLive||0,e:c.store&&c.store.energy,sp:!!c.spawning,body:c.body.map(p=>p.type[0]+(p.boost?(':'+p.boost):'')).join(''),role:role};} return {t:Game.time,o};})()"),
    ("w8th", "(()=>{const o=Memory.ops||{}; return {t:Game.time,w8t:o.w8threat,w8f:o.w8flee,w8i:o.w8inv,thUntil:o.thUntil,softLeft:o.softLeft,seal:o.sealPark,sealWhy:o.sealWhy,w8soft:o.w8soft,w8day:o.w8day&&{storE:o.w8day.storE,keep:o.w8day.upgKeep,upArm:o.w8day.upArm,upLatched:o.w8day.upLatched,threatSoft:o.w8day.threatSoft,softCap2:o.w8day.softCap2,bankWhy:o.w8day.bankWhy,softLeft:o.w8day.softLeft,sealPark:o.w8day.sealPark,why:o.w8day.why,phase:o.w8day.phase,feedOk:o.w8day.feedOk,hubLink:o.w8day.hubLink,upgCeil:o.w8day.upgCeil},r7:o.r7};})()"),
    ("lab2", "(()=>{const o=Memory.ops||{}; return {t:Game.time,labs:o.labs,labReady:o.labReady,koLab:(()=>{const labs=Game.rooms.W46N8&&Game.rooms.W46N8.find(FIND_MY_STRUCTURES).filter(s=>s.structureType==STRUCTURE_LAB); const out={}; for (const l of labs||[]){ out[l.id.slice(-4)]={m:l.mineralType,a:l.store&&(l.store[l.mineralType]||0),e:l.store&&l.store.energy}; } return out;})()};})()"),
]
for name, expr in qs:
    print("QUERY", name, "len", len(expr), flush=True)
    try:
        r = qmod.q(expr, timeout=35)
        (OUT / ("q_%s.json" % name)).write_text(json.dumps(r, indent=2, default=str) + "\n")
        print("OK", name, json.dumps(r, default=str)[:4000], flush=True)
    except Exception as e:
        print("FAIL", name, type(e).__name__, e, flush=True)
