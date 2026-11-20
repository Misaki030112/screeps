#!/usr/bin/env python3
import sys, json
from pathlib import Path
sys.path.insert(0, "/workspace/screeps/tools")
import q as qmod
OUT = Path("/workspace/screeps/state/_patrol_2026-11-20_1220")

qs = [
    ("later", "({t:Game.time,b:Game.cpu.bucket,c:+Game.cpu.getUsed().toFixed(2),hs:Game.rooms.W46N8&&Game.rooms.W46N8.storage.store.energy,ws:Game.rooms.W47N8&&Game.rooms.W47N8.storage.store.energy,hp:Game.rooms.W46N8&&Game.rooms.W46N8.controller.progress,wp:Game.rooms.W47N8&&Game.rooms.W47N8.controller.progress,sma:Game.rooms.W46N8&&Game.rooms.W46N8.controller.safeModeAvailable,smaW:Game.rooms.W47N8&&Game.rooms.W47N8.controller.safeModeAvailable})"),
    ("dpos", "(()=>{const c=Game.creeps['defender84372817']; const r=Game.creeps['rdef84372551']; const g=Game.creeps['w8guard84372832']; const body=c=>{if(!c)return null; const b={}; for(const p of c.body)b[p.type]=(b[p.type]||0)+1; return b;}; return {t:Game.time,d:c&&{rm:c.pos.roomName,x:c.pos.x,y:c.pos.y,sp:!!c.spawning,hits:c.hits,ttl:c.ticksToLive||0,b:body(c),core:c.memory.core},r:r&&{rm:r.pos.roomName,x:r.pos.x,y:r.pos.y,hits:r.hits,ttl:r.ticksToLive||0,b:body(r)},g:g&&{rm:g.pos.roomName,x:g.pos.x,y:g.pos.y,sp:!!g.spawning,hits:g.hits,ttl:g.ticksToLive||0,b:body(g)}};})()"),
    ("uf2", "(Memory.ops&&Memory.ops.upgFeed)"),
]
for name, expr in qs:
    print("QUERY", name, "len", len(expr), flush=True)
    try:
        r = qmod.q(expr, timeout=35)
        (OUT / f"q_{name}.json").write_text(json.dumps(r, indent=2, default=str) + "\n")
        print("OK", json.dumps(r, default=str)[:1500], flush=True)
    except Exception as e:
        print("FAIL", name, type(e).__name__, e, flush=True)
