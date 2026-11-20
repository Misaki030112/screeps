#!/usr/bin/env python3
import sys, json
from pathlib import Path
sys.path.insert(0, "/workspace/screeps/tools")
import q as qmod
OUT = Path("/workspace/screeps/state/_patrol_2026-11-20_1220")
Qs = [
    ("remops", """(()=>{const rem=(Memory.ops&&Memory.ops.rem)||{};
const pick=n=>{const x=rem[n]||{}; return {st:x.st||x.state,why:x.why,inc:x.inc,core:x.core,inv:x.inv,def:x.def,since:x.since,threat:x.threat,pos:x.pos,hits:x.hits};};
return {t:Game.time, W45N8:pick('W45N8'), W45N7:pick('W45N7'), W47N7:pick('W47N7'), w8t:Memory.ops&&Memory.ops.w8threat, w8inv:Memory.ops&&Memory.ops.w8inv};})()"""),
    ("bodies", """(()=>{const names=['defender84372817','rdef84372551','w8guard84372832','defender84371269'];
const out={};
for(const n of names){
  const cr=Game.creeps[n];
  if(!cr){out[n]=null; continue;}
  const body={}; for(const p of cr.body){body[p.type]=(body[p.type]||0)+1;}
  out[n]={rm:cr.pos.roomName,x:cr.pos.x,y:cr.pos.y,sp:!!cr.spawning,hits:cr.hits,hM:cr.hitsMax,ttl:cr.ticksToLive||0,body,e:cr.store&&cr.store.energy||0,st:cr.memory&&cr.memory.st,mis:cr.memory&&cr.memory.mission,core:cr.memory&&cr.memory.core,noBoost:cr.memory&&cr.memory.noBoost,role:cr.memory&&cr.memory.role};
}
const H=Game.rooms.W46N8,W=Game.rooms.W47N8;
return {t:Game.time,out,sma:H&&H.controller.safeModeAvailable,smaW:W&&W.controller.safeModeAvailable,sites:Object.keys(Game.constructionSites).length,
hs:H&&H.storage&&H.storage.store.energy, ws:W&&W.storage&&W.storage.store.energy,
nUp:_.filter(Game.creeps,c=>c.memory.role==='upgrader'&&!c.spawning).length,
w8up:_.filter(Game.creeps,c=>c.memory.role==='w8upgrader'&&!c.spawning).length};})()"""),
]
for name, expr in Qs:
    print("QUERY", name, "len", len(expr), flush=True)
    try:
        r = qmod.q(expr, timeout=35)
        (OUT / f"q_{name}.json").write_text(json.dumps(r, indent=2, default=str) + "\n")
        print("OK", name, json.dumps(r, default=str)[:2000], flush=True)
    except Exception as e:
        print("FAIL", name, type(e).__name__, e, flush=True)
print("FOLLOWUP_DONE")
