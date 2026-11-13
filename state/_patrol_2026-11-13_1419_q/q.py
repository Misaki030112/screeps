#!/usr/bin/env python3
import json, sys, os
sys.path.insert(0, "/workspace/screeps/tools")
import q as qmod
os.chdir("/workspace/screeps")
outdir = "/tmp/patrol_1113_1419"
os.makedirs(outdir, exist_ok=True)
QUERIES = [
("home", """(()=>{const H=Game.rooms.W46N8,W=Game.rooms.W47N8,hc=H&&H.controller,wc=W&&W.controller,hs=H&&H.storage,ws=W&&W.storage;return{t:Game.time,b:Game.cpu.bucket,c:+Game.cpu.getUsed().toFixed(2),n:_.size(Game.creeps),hs:hs&&hs.store.energy,ws:ws&&ws.store.energy,hp:hc&&hc.progress,wp:wc&&wc.progress,ea:H&&H.energyAvailable,eaw:W&&W.energyAvailable,sma:hc&&hc.safeModeAvailable,ttd:hc&&hc.ticksToDowngrade,smaW:wc&&wc.safeModeAvailable,ttdW:wc&&wc.ticksToDowngrade,cmt:(Memory.stats&&Memory.stats.commit)||Memory.commit||null,le:Memory.stats&&Memory.stats.lastErrorTick,nErr:Memory.stats&&Memory.stats.nErr}})()"""),
("uf", """(Memory.ops&&Memory.ops.upgFeed)||null"""),
("soft", """(()=>{const d=(Memory.ops&&Memory.ops.w8day)||{};return{t:Game.time,bWhy:d.bankWhy,sL:d.softLeft,sC2:d.softCap2,keep:d.upgKeep,thS:d.threatSoft,storE:d.storE,upL:d.upLatched,lb:d.leanBank,why:d.why,phase:d.phase,eAvail:d.eAvail,eCap:d.eCap,upN:d.upN,feedOk:d.feedOk,upArm:d.upArm,sealPark:d.sealPark,sealMinE:d.sealMinE,siteRem:d.siteRem,ceil:d.upgCeil||d.ceil,softE:d.softE,softBand:d.softBand,builders:d.builders,upgraders:d.upgraders,roadCrit:d.roadCrit,contLow:d.contLow,contMinPct:d.contMinPct}})()"""),
("roles", """(()=>{const roles={};const ups=[];const miners=[];const crit=[];for(const c of Object.values(Game.creeps)){const r=c.memory&&c.memory.role||'?';roles[r]=(roles[r]||0)+1;const rec={n:c.name,r,rm:c.pos.roomName,x:c.pos.x,y:c.pos.y,ttl:c.ticksToLive||0,e:c.store&&c.store.energy||0,w:c.getActiveBodyparts(WORK),sp:!!c.spawning,st:c.memory&&c.memory.st};if(r==='upgrader'||r==='w8upgrader'){const dest=c.memory&&c.memory._move&&c.memory._move.dest;ups.push(Object.assign({},rec,{dest:dest||null}));}if(r==='miner'||r==='w8miner'||r==='rminer'||r==='w8rminer')miners.push(rec);if(r==='queen'||r==='w8filler'||r==='reserver'||r==='reserve7'||r==='builder'||r==='w8builder')crit.push(rec);}return{t:Game.time,roles,ups,miners,crit}})()"""),
("rem", """(()=>{const names=['W45N8','W45N7','W47N7'];const out={};for(const n of names){const x=(Memory.ops&&Memory.ops.rem&&Memory.ops.rem[n])||{};const room=Game.rooms[n];const ctrl=room&&room.controller;const hosts=room?room.find(FIND_HOSTILE_CREEPS).map(c=>({n:c.name,x:c.pos.x,y:c.pos.y,hits:c.hits,ttl:c.ticksToLive,owner:c.owner&&c.owner.username})):null;out[n]={vis:!!room,res:ctrl&&ctrl.reservation?ctrl.reservation.ticksToEnd:null,resUser:ctrl&&ctrl.reservation&&ctrl.reservation.username,cores:room?room.find(FIND_HOSTILE_STRUCTURES,{filter:s=>s.structureType===STRUCTURE_INVADER_CORE}).length:0,host:hosts?hosts.length:null,hosts,st:x.st||null,seen:x.seen};}return{t:Game.time,rem:out,statsRemote:(Memory.stats&&Memory.stats.remote)||null}})()"""),
("cmd", """(()=>{const c=Memory.cmd||null;return{t:Game.time,on:c&&c.on,at:c&&c.at,by:c&&c.by,c:c&&c.c,s:c&&c.s,v:c&&c.v,keys:c&&Object.keys(c)}})()"""),
("lab", """(()=>{const o=Memory.ops||{};const L=o.labReady||o.lab||{};const m=o.w8min||{};const w9=o.w47n9||{};return{t:Game.time,labMode:L.mode||o.labMode||null,why:L.why,propose:L.propose,actOk:L.actOk,actGaps:L.actGaps,ready:L.ready,homeStor:L.homeStor,kTerm:L.kTerm||L.k,oTerm:L.oTerm,o:L.o,k:L.k,w8minWhy:m.why,w8minGaps:m.gaps,flipReady:m.flipReady,flipGaps:m.flipGaps,miners:m.miners,w47n9:{on:w9.on,phase:w9.phase,recycle:w9.recycle,ps:w9.pauseSpawn||w9.ps,note:w9.note,fallback:w9.fallback}})()"""),
("min", """(()=>{const H=Game.rooms.W46N8,W=Game.rooms.W47N8,hs=H&&H.storage,ht=H&&H.terminal,ws=W&&W.storage,wt=W&&W.terminal;return{t:Game.time,hs:hs&&{E:hs.store.energy||0,O:hs.store.O||0,K:hs.store.K||0},ht:ht&&{E:ht.store.energy||0,O:ht.store.O||0,K:ht.store.K||0},ws:ws&&{E:ws.store.energy||0,O:ws.store.O||0,K:ws.store.K||0},wt:wt&&{E:wt.store.energy||0,O:wt.store.O||0,K:wt.store.K||0}})()"""),
("def", """(()=>{const defs={};let n=0;for(const c of Object.values(Game.creeps)){const r=c.memory&&c.memory.role||'';if(r==='defender'||r==='w8defender'||r==='w8guard'||r==='rdef'||r==='guard'||r==='melee'||r==='ranged'){n++;const body={};for(const p of c.body){const typ=p.type;body[typ]=(body[typ]||0)+1}defs[c.name]={rm:c.pos.roomName,x:c.pos.x,y:c.pos.y,ttl:c.ticksToLive||0,hits:c.hits,hitsMax:c.hitsMax,sp:!!c.spawning,body,role:r,st:c.memory&&c.memory.st,cmd:c.memory&&c.memory._cmd,move:c.memory&&c.memory._move}};}return{t:Game.time,n,defs}})()"""),
("sites", """(()=>{const rooms=['W46N8','W47N8'];const out={};for(const rn of rooms){const R=Game.rooms[rn];if(!R){out[rn]={vis:false};continue;}const sites=R.find(FIND_MY_CONSTRUCTION_SITES).map(s=>({id:s.id,t:s.structureType,x:s.pos.x,y:s.pos.y,p:s.progress,tP:s.progressTotal}));out[rn]={vis:true,nSites:sites.length,sites};}return{t:Game.time,rooms:out}})()"""),
("w8extra", """(()=>{const d=(Memory.ops&&Memory.ops.w8day)||{};return{t:Game.time,d}})()"""),
("w8threat", """(()=>{return{t:Game.time,w8threat:Memory.ops&&Memory.ops.w8threat,lab:(Memory.ops&&(Memory.ops.labReady||Memory.ops.lab))||null}})()"""),
("spawns", """(()=>{const out={};for(const s of Object.values(Game.spawns)){out[s.name]={rm:s.pos.roomName,x:s.pos.x,y:s.pos.y,sp:s.spawning&&{name:s.spawning.name,need:s.spawning.needTime,rem:s.spawning.remainingTime},ea:s.room.energyAvailable,ec:s.room.energyCapacityAvailable};}return{t:Game.time,spawns:out}})()"""),
("err", """(()=>{const s=Memory.stats||{};return{t:Game.time,le:s.lastErrorTick,nErr:s.nErr||s.nerr,cmt:s.commit||Memory.commit||null}})()"""),
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
with open(f"{outdir}/q_all.json","w") as f:
    json.dump(allres, f, indent=2, default=str)
print("=== Q DONE ===", flush=True)
