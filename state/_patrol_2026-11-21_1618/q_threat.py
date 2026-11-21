#!/usr/bin/env python3
import sys, json
from pathlib import Path
sys.path.insert(0, "/workspace/screeps/tools")
import q as qmod
OUT = Path("/workspace/screeps/state/_patrol_2026-11-21_1618")
qs = [
    ("remfull", "(()=>{const o=Memory.ops||{}; return {t:Game.time, rem:o.rem, rem2:o.remote, rem3:o.remotes, uf:o.upgFeed, w8t:o.w8threat, w8f:o.w8flee, w8i:o.w8inv, w8dayKeep:o.w8day&&{keep:o.w8day.upgKeep,ceil:o.w8day.upgCeil,seal:o.w8day.sealPark,why:o.w8day.why,bankWhy:o.w8day.bankWhy,threatSoft:o.w8day.threatSoft,storE:o.w8day.storE}, r7:o.r7};})()"),
    ("creeps_def", "(()=>{const out={}; for (const n in Game.creeps){ const c=Game.creeps[n]; const role=(c.memory&&c.memory.role)||''; if(!/def|guard|reserver|reserve/i.test(n+role)) continue; out[n]={rm:c.pos.roomName,x:c.pos.x,y:c.pos.y,ttl:c.ticksToLive||0,sp:!!c.spawning,hits:c.hits,role:role,mem:c.memory};} return {t:Game.time,out};})()"),
    ("queens", "(()=>{const out={}; for (const n in Game.creeps){ const c=Game.creeps[n]; const role=(c.memory&&c.memory.role)||''; if(!/queen|filler|miner|reserver/i.test(n+role)) continue; out[n]={rm:c.pos.roomName,x:c.pos.x,y:c.pos.y,ttl:c.ticksToLive||0,sp:!!c.spawning,e:c.store&&c.store.energy||0,role:role};} return {t:Game.time,n:Object.keys(out).length,out};})()"),
]
for name, expr in qs:
    print("QUERY", name, "len", len(expr), flush=True)
    try:
        r = qmod.q(expr, timeout=35)
        (OUT / ("q_%s.json" % name)).write_text(json.dumps(r, indent=2, default=str) + "\n")
        print("OK", name, json.dumps(r, default=str)[:4000], flush=True)
    except Exception as e:
        print("FAIL", name, type(e).__name__, e, flush=True)
