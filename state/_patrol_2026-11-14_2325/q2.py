#!/usr/bin/env python3
import json, sys, os
sys.path.insert(0, "/workspace/screeps/tools")
import q as qmod
os.chdir("/workspace/screeps")
outdir = "/workspace/screeps/state/_patrol_2026-11-14_2325"
QUERIES = [
("vis", """(()=>{const ns=['W45N8','W45N7','W47N7'];const out={};for(const n of ns){const r=Game.rooms[n];const c=r&&r.controller;out[n]={vis:!!r,res:c&&c.reservation?c.reservation.ticksToEnd:null,user:c&&c.reservation&&c.reservation.username,cores:r?r.find(FIND_HOSTILE_STRUCTURES,{filter:s=>s.structureType==STRUCTURE_INVADER_CORE}).length:0,host:r?r.find(FIND_HOSTILE_CREEPS).length:null};}return{t:Game.time,out};})()"""),
("opsRem", """(()=>{const o=Memory.ops&&Memory.ops.rem||{};const st=(Memory.stats&&Memory.stats.remote)||{};const names=['W45N8','W45N7','W47N7'];const x={};for(const n of names){const a=o[n]||{};x[n]={st:a.st||(a.th&&a.th.st)||null,needE:!!a.needE,armed:!!a.armed,res:a.res||null};}return{t:Game.time,o:x,stats:st};})()"""),
("resv", """(()=>{const a=[];for(const c of Object.values(Game.creeps)){const r=c.memory&&c.memory.role;if(r==='reserver'||r==='reserve7')a.push({n:c.name,r,rm:c.pos.roomName,x:c.pos.x,y:c.pos.y,ttl:c.ticksToLive||0,sp:!!c.spawning});}return{t:Game.time,n:a.length,a};})()"""),
("min2", """(()=>{const H=Game.rooms.W46N8,W=Game.rooms.W47N8;const p=s=>s&&{E:s.store.energy||0,O:s.store.O||0,K:s.store.K||0};return{t:Game.time,hs:p(H&&H.storage),ht:p(H&&H.terminal),ws:p(W&&W.storage),wt:p(W&&W.terminal)};})()"""),
("nerr", """(()=>{const s=Memory.stats||{},H=Game.rooms.W46N8,uf=Memory.ops&&Memory.ops.upgFeed;return{t:Game.time,le:s.lastErrorTick,nErr:s.nErr||s.nerr,cmt:s.commit||Memory.commit||null,bucket:Game.cpu.bucket,hs:H&&H.storage&&H.storage.store.energy,ws:Game.rooms.W47N8&&Game.rooms.W47N8.storage&&Game.rooms.W47N8.storage.store.energy,nUp:uf&&uf.nUp,why:uf&&uf.why};})()"""),
("lab2", """(()=>{const L=(Memory.ops&&(Memory.ops.labReady||Memory.ops.lab))||{};const m=(Memory.ops&&Memory.ops.w8min)||{};const w9=(Memory.ops&&Memory.ops.w47n9)||{};return{t:Game.time,mode:L.mode,why:L.why,propose:L.propose,actOk:L.actOk,actGaps:L.actGaps,ready:L.ready,homeStor:L.homeStor,w8minWhy:m.why,w8minGaps:m.gaps,flipGaps:m.flipGaps,w9on:w9.on,w9phase:w9.phase,w9rec:w9.recycle,w9note:w9.note};})()"""),
]
allres = {}
for name, expr in QUERIES:
    print(f"=== Q {name} (len={len(expr)}) ===", flush=True)
    try:
        res = qmod.q(expr, timeout=30)
        path = f"{outdir}/q_{name}.json"
        with open(path, "w") as f:
            json.dump(res, f, indent=2, default=str)
        print(json.dumps(res, default=str, separators=(',', ':'))[:4000], flush=True)
        allres[name]=res
    except SystemExit as e:
        print(f"FAIL {name}: {e}", flush=True)
    except Exception as e:
        print(f"ERR {name}: {type(e).__name__} {e}", flush=True)
print("=== Q2 DONE ===", flush=True)
