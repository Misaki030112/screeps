#!/usr/bin/env python3
import sys, json
from pathlib import Path
sys.path.insert(0, "/workspace/screeps/tools")
import q as qmod
OUT = Path("/workspace/screeps/state/_patrol_2026-11-22_2016")
qs = [
    ("end_snap", "({t:Game.time,b:Game.cpu.bucket,c:+Game.cpu.getUsed().toFixed(2),hs:Game.rooms.W46N8&&Game.rooms.W46N8.storage.store.energy,ws:Game.rooms.W47N8&&Game.rooms.W47N8.storage.store.energy,hp:Game.rooms.W46N8&&Game.rooms.W46N8.controller.progress,wp:Game.rooms.W47N8&&Game.rooms.W47N8.controller.progress,ht:Game.rooms.W46N8&&Game.rooms.W46N8.controller.ticksToDowngrade,wt:Game.rooms.W47N8&&Game.rooms.W47N8.controller.ticksToDowngrade,sma:Game.rooms.W46N8&&Game.rooms.W46N8.controller.safeModeAvailable,smaW:Game.rooms.W47N8&&Game.rooms.W47N8.controller.safeModeAvailable})"),
    ("end_ops", "(()=>{const o=Memory.ops||{};const d=o.w8day||{};return {t:Game.time,nUp:o.upgFeed&&o.upgFeed.nUp,why:o.upgFeed&&o.upgFeed.why,storE:o.upgFeed&&o.upgFeed.storE,keep:d.upgKeep,latch:d.upLatched,w8up:d.upgraders,seal:d.sealPark,sealWhy:(o.w8soft&&o.w8soft.why)||d.bankWhy,soft:d.threatSoft,bank:d.bankWhy,w8t:o.w8threat,w8inv:o.w8inv,w8f:o.w8flee};})()"),
    ("end_resv", "(()=>{const r={}; for(const n of ['W45N8','W45N7','W47N7']){const rm=Game.rooms[n]; const c=rm&&rm.controller; r[n]={vis:!!rm,res:c&&c.reservation&&c.reservation.ticksToEnd,host:rm?rm.find(FIND_HOSTILE_CREEPS).length:null,core:rm?rm.find(FIND_HOSTILE_STRUCTURES).filter(s=>s.structureType==STRUCTURE_INVADER_CORE).length:null};} return {t:Game.time,r};})()"),
    ("end_host", "(()=>{const r={}; for (const n of ['W46N8','W47N8','W45N8','W45N7','W47N7']){ const rm=Game.rooms[n]; if(!rm){r[n]={vis:false}; continue;} const h=rm.find(FIND_HOSTILE_CREEPS).map(c=>({n:c.name,own:c.owner&&c.owner.username,x:c.pos.x,y:c.pos.y,hits:c.hits,ttl:c.ticksToLive,body:c.body.map(p=>p.type[0]).join('')})); r[n]={vis:true,hc:h.length,h};} return {t:Game.time,r};})()"),
]
for name, expr in qs:
    print("QUERY", name, "len", len(expr), flush=True)
    try:
        r = qmod.q(expr, timeout=35)
        (OUT / ("q_%s.json" % name)).write_text(json.dumps(r, indent=2, default=str) + "\n")
        print("OK", name, json.dumps(r, default=str)[:4000], flush=True)
    except Exception as e:
        print("FAIL", name, type(e).__name__, e, flush=True)
