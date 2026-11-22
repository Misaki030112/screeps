#!/usr/bin/env python3
import sys, json
from pathlib import Path
sys.path.insert(0, "/workspace/screeps/tools")
import q as qmod
OUT = Path("/workspace/screeps/state/_patrol_2026-11-22_1722")
qs = [
    ("ea", "(()=>{const h=Game.rooms.W46N8;const w=Game.rooms.W47N8;return {t:Game.time,hea:h&&h.energyAvailable,hcap:h&&h.energyCapacityAvailable,hs:h&&h.storage.store.energy,wea:w&&w.energyAvailable,wcap:w&&w.energyCapacityAvailable,ws:w&&w.storage.store.energy};})()"),
    ("th45", "(()=>{const r=Memory.remote&&Memory.remote.W45N7; const keys=Memory.remote&&Object.keys(Memory.remote); return {t:Game.time,keys,W45N7:r,th:r&&r.th,want:Memory.ops&&Memory.ops.wantDef};})()"),
    ("def4", "(()=>{const out={};for(const n in Game.creeps){const cr=Game.creeps[n];const role=(cr.memory&&cr.memory.role)||'';if(!/def|guard/i.test(n+role))continue;out[n]={rm:cr.pos.roomName,x:cr.pos.x,y:cr.pos.y,sp:!!cr.spawning,ttl:cr.ticksToLive||0,role:role};}const spawns={};for(const n in Game.spawns){const s=Game.spawns[n];const sp=s.spawning;spawns[n]={busy:!!sp,name:sp&&sp.name,rem:sp&&sp.remainingTime};}return {t:Game.time,out,spawns,ufRem:Memory.ops&&Memory.ops.upgFeed&&Memory.ops.upgFeed.rem};})()"),
]
for name, expr in qs:
    print("QUERY", name, "len", len(expr), flush=True)
    try:
        r = qmod.q(expr, timeout=40)
        (OUT / ("q_%s.json" % name)).write_text(json.dumps(r, indent=2, default=str) + "\n")
        print("OK", name, json.dumps(r, default=str)[:5000], flush=True)
    except Exception as e:
        print("FAIL", name, type(e).__name__, e, flush=True)
