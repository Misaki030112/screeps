#!/usr/bin/env python3
import sys, json
from pathlib import Path
sys.path.insert(0, "/workspace/screeps/tools")
import q as qmod
OUT = Path("/workspace/screeps/state/_patrol_2026-11-20_1220")
expr = """(()=>{const n='defender84372817'; const m='rdef84372551'; const g='w8guard84372832';
const f=n=>{const c=Game.creeps[n]; if(!c) return null; const b={}; for(const p of c.body) b[p.type]=(b[p.type]||0)+1;
return {rm:c.pos.roomName,x:c.pos.x,y:c.pos.y,sp:!!c.spawning,hits:c.hits,hM:c.hitsMax,ttl:c.ticksToLive||0,b,core:c.memory&&c.memory.core,st:c.memory&&c.memory.st,mis:c.memory&&c.memory.mission};};
const H=Game.rooms.W46N8,W=Game.rooms.W47N8;
return {t:Game.time,d:f(n),r:f(m),g:f(g),hs:H&&H.storage.store.energy,ws:W&&W.storage.store.energy,
sma:H&&H.controller.safeModeAvailable,ttd:H&&H.controller.ticksToDowngrade,
nUp:_.filter(Game.creeps,c=>c.memory.role==='upgrader'&&!c.spawning).length,
w8up:_.filter(Game.creeps,c=>c.memory.role==='w8upgrader'&&!c.spawning).length,
uf:Memory.ops&&Memory.ops.upgFeed&&Memory.ops.upgFeed.rem,
why:Memory.ops&&Memory.ops.upgFeed&&Memory.ops.upgFeed.why,
nUp2:Memory.ops&&Memory.ops.upgFeed&&Memory.ops.upgFeed.nUp,
work:Memory.ops&&Memory.ops.upgFeed&&Memory.ops.upgFeed.work,
seal:Memory.ops&&Memory.ops.w8day&&Memory.ops.w8day.sealPark,
bWhy:Memory.ops&&Memory.ops.w8day&&Memory.ops.w8day.bankWhy};})()"""
print("len", len(expr), flush=True)
r = qmod.q(expr, timeout=35)
(OUT / "q_bodies2.json").write_text(json.dumps(r, indent=2, default=str) + "\n")
print(json.dumps(r, default=str), flush=True)
