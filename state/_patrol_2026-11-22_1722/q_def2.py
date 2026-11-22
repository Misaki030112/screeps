#!/usr/bin/env python3
import sys, json
from pathlib import Path
sys.path.insert(0, "/workspace/screeps/tools")
import q as qmod
OUT = Path("/workspace/screeps/state/_patrol_2026-11-22_1722")
qs = [
    ("def2", "(()=>{const out={};for(const n in Game.creeps){const cr=Game.creeps[n];const role=(cr.memory&&cr.memory.role)||'';if(!/def|guard/i.test(n+role))continue;out[n]={rm:cr.pos.roomName,x:cr.pos.x,y:cr.pos.y,sp:!!cr.spawning,hits:cr.hits,ttl:cr.ticksToLive||0,role:role,st:cr.memory&&cr.memory.st};}return {t:Game.time,out};})()"),
    ("spawns2", "(()=>{const spawns={};for(const n in Game.spawns){const s=Game.spawns[n];const sp=s.spawning;spawns[n]={rm:s.pos.roomName,busy:!!sp,name:sp&&sp.name,need:sp&&sp.needTime,rem:sp&&sp.remainingTime};}return {t:Game.time,spawns};})()"),
    ("host2", "(()=>{const r={};for(const n of ['W45N8','W45N7','W47N7']){const rm=Game.rooms[n];if(!rm){r[n]={vis:false};continue;}const h=rm.find(FIND_HOSTILE_CREEPS).map(c=>({n:c.name,own:c.owner&&c.owner.username,x:c.pos.x,y:c.pos.y,hits:c.hits,ttl:c.ticksToLive,body:c.body.map(p=>p.type[0]).join('')}));const cores=rm.find(FIND_HOSTILE_STRUCTURES).filter(s=>s.structureType==STRUCTURE_INVADER_CORE).length;r[n]={vis:true,res:rm.controller&&rm.controller.reservation&&rm.controller.reservation.ticksToEnd,hc:h.length,h,cc:cores};}return {t:Game.time,r};})()"),
    ("rem2", "(()=>{const o=Memory.ops||{};return {t:Game.time,rem:o.rem,ufRem:o.upgFeed&&o.upgFeed.rem,nUp:o.upgFeed&&o.upgFeed.nUp,why:o.upgFeed&&o.upgFeed.why,hs:Game.rooms.W46N8&&Game.rooms.W46N8.storage.store.energy,ws:Game.rooms.W47N8&&Game.rooms.W47N8.storage.store.energy,seal:o.w8soft&&o.w8soft.sealPark,w8t:o.w8threat};})()"),
]
for name, expr in qs:
    print("QUERY", name, "len", len(expr), flush=True)
    try:
        r = qmod.q(expr, timeout=40)
        (OUT / ("q_%s.json" % name)).write_text(json.dumps(r, indent=2, default=str) + "\n")
        print("OK", name, json.dumps(r, default=str)[:5000], flush=True)
    except Exception as e:
        print("FAIL", name, type(e).__name__, e, flush=True)
