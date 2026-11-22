#!/usr/bin/env python3
import sys, json
from pathlib import Path
sys.path.insert(0, "/workspace/screeps/tools")
import q as qmod
OUT = Path("/workspace/screeps/state/_patrol_2026-11-23_0216")
qs = [
    ("soft", "(()=>{const o=Memory.ops||{};return {t:Game.time,seal:o.sealPark,why:o.sealWhy||o.why,soft:o.softCap2,bank:o.bankWhy,w8t:o.w8threat,softLeft:o.softLeft,nUp:o.upgFeed&&o.upgFeed.nUp,w8up:o.w8up};})()"),
    ("roles", "(()=>{const c={};for(const n in Game.creeps){const r=(Game.creeps[n].memory&&Game.creeps[n].memory.role)||'?';c[r]=(c[r]||0)+1;}return {t:Game.time,n:Object.keys(Game.creeps).length,c};})()"),
    ("defs", "(()=>{const names=Object.keys(Game.creeps).filter(n=>/def|guard|Invader|core/i.test(n)||((Game.creeps[n].memory||{}).role||'').match(/def|guard/));const out={};for(const n of names){const cr=Game.creeps[n];out[n]={rm:cr.pos.roomName,x:cr.pos.x,y:cr.pos.y,sp:!!cr.spawning,hits:cr.hits,ttl:cr.ticksToLive||0,role:cr.memory&&cr.memory.role,st:cr.memory&&cr.memory.st,core:cr.memory&&cr.memory.core,mis:cr.memory&&cr.memory.mission};}return {t:Game.time,out};})()"),
    ("lab", "(()=>{const s=Game.rooms.W46N8&&Game.rooms.W46N8.storage;const t=Game.rooms.W46N8&&Game.rooms.W46N8.terminal;const store=s&&s.store;const ts=t&&t.store;const pick=st=>{const o={};if(!st)return o;for(const k of Object.keys(st)){if(st[k])o[k]=st[k];}return o;};return {t:Game.time,labs:Memory.ops&&Memory.ops.labs,stor:pick(store),term:pick(ts),sites:Object.keys(Game.constructionSites).length};})()"),
]
for name, expr in qs:
    print("QUERY", name, "len", len(expr), flush=True)
    try:
        r = qmod.q(expr, timeout=35)
        (OUT / ("q_%s.json" % name)).write_text(json.dumps(r, indent=2, default=str) + "\n")
        print("OK", name, json.dumps(r, default=str)[:3000], flush=True)
    except Exception as e:
        print("FAIL", name, type(e).__name__, e, flush=True)
