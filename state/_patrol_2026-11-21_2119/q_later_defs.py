#!/usr/bin/env python3
import json, sys
from pathlib import Path
sys.path.insert(0, "/workspace/screeps/tools")
import q as qmod
OUT = Path("/workspace/screeps/state/_patrol_2026-11-21_2119")
qs = [
    ("later_roles", "(()=>{const c={};for(const n in Game.creeps){const r=(Game.creeps[n].memory&&Game.creeps[n].memory.role)||'?';c[r]=(c[r]||0)+1;}return {t:Game.time,n:Object.keys(Game.creeps).length,c};})()"),
    ("later_defs2", "(()=>{const out={};for(const n in Game.creeps){const cr=Game.creeps[n];const role=(cr.memory&&cr.memory.role)||'';if(!/def|guard/i.test(n+role))continue;out[n]={rm:cr.pos.roomName,x:cr.pos.x,y:cr.pos.y,sp:!!cr.spawning,hits:cr.hits,ttl:cr.ticksToLive||0,role:role,body:cr.body.map(p=>p.type[0]).join('')};}return {t:Game.time,out};})()"),
    ("later_spawns", "(()=>{const spawns={};for(const n of Object.keys(Game.spawns)){const s=Game.spawns[n];spawns[n]={rm:s.pos.roomName,sp:s.spawning&&{name:s.spawning.name,need:s.spawning.needTime,rem:s.spawning.remainingTime}};}return {t:Game.time,spawns};})()"),
    ("later_w47creeps", "(()=>{const o=[];for(const n in Game.creeps){const c=Game.creeps[n];if(c.pos.roomName==='W47N7'||(c.memory&&c.memory.role||'').indexOf('w8r')===0)o.push({n,role:c.memory&&c.memory.role,rm:c.pos.roomName,x:c.pos.x,y:c.pos.y,sp:!!c.spawning,hits:c.hits,ttl:c.ticksToLive||0,st:c.memory&&c.memory.st});}return {t:Game.time,o};})()"),
]
for name, expr in qs:
    print("QUERY", name, "len", len(expr), flush=True)
    try:
        r = qmod.q(expr, timeout=35)
        (OUT / ("q_%s.json" % name)).write_text(json.dumps(r, indent=2, default=str) + "\n")
        print("OK", name, json.dumps(r, default=str)[:5000], flush=True)
    except Exception as e:
        print("FAIL", name, type(e).__name__, e, flush=True)
print("DEFS_DONE", flush=True)
