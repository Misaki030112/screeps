#!/usr/bin/env python3
import json, sys, os
sys.path.insert(0, "/workspace/screeps/tools")
import q as qmod
os.chdir("/workspace/screeps")
outdir = "/workspace/screeps/state/_patrol_2026-11-15_1625"
os.makedirs(outdir, exist_ok=True)
QUERIES = [
("ping", """Game.time"""),
("home", """(()=>{const H=Game.rooms.W46N8,W=Game.rooms.W47N8,hc=H&&H.controller,wc=W&&W.controller,hs=H&&H.storage,ws=W&&W.storage;return{t:Game.time,b:Game.cpu.bucket,c:+Game.cpu.getUsed().toFixed(2),n:_.size(Game.creeps),hs:hs&&hs.store.energy,ws:ws&&ws.store.energy,hp:hc&&hc.progress,wp:wc&&wc.progress,ea:H&&H.energyAvailable,eaw:W&&W.energyAvailable,sma:hc&&hc.safeModeAvailable,ttd:hc&&hc.ticksToDowngrade,smaW:wc&&wc.safeModeAvailable,ttdW:wc&&wc.ticksToDowngrade,cmt:(Memory.stats&&Memory.stats.commit)||Memory.commit||null,le:Memory.stats&&Memory.stats.lastErrorTick}})()"""),
("uf", """(Memory.ops&&Memory.ops.upgFeed)||null"""),
("soft", """(()=>{const d=(Memory.ops&&Memory.ops.w8day)||{};return{t:Game.time,bWhy:d.bankWhy,sL:d.softLeft,sC2:d.softCap2,keep:d.upgKeep,thS:d.threatSoft,storE:d.storE,upL:d.upLatched,lb:d.leanBank,why:d.why,phase:d.phase,eAvail:d.eAvail,eCap:d.eCap,upN:d.upN,feedOk:d.feedOk,upArm:d.upArm,sealPark:d.sealPark,sealMinE:d.sealMinE,siteRem:d.siteRem,hubLink:d.hubLink,hubReady:d.hubReady}})()"""),
("roles", """(()=>{const roles={};const ups=[];const crit=[];const want=['miner','rminer','reserver','queen','w8filler','w8miner','w8rminer','reserve7','reserve'];for(const c of Object.values(Game.creeps)){const r=c.memory&&c.memory.role||'?';roles[r]=(roles[r]||0)+1;const dest=c.memory&&c.memory._move&&c.memory._move.dest;if(r==='upgrader'||r==='w8upgrader'||want.indexOf(r)>=0){crit.push({n:c.name,r,rm:c.pos.roomName,x:c.pos.x,y:c.pos.y,ttl:c.ticksToLive||0,e:c.store&&c.store.energy||0,w:c.getActiveBodyparts(WORK),sp:!!c.spawning,st:c.memory&&c.memory.st,dest:dest||null});}}return{t:Game.time,roles,crit}})()"""),
("rem", """(()=>{const names=['W45N8','W45N7','W47N7'];const out={};for(const n of names){const x=(Memory.ops&&Memory.ops.rem&&Memory.ops.rem[n])||{};const room=Game.rooms[n];const ctrl=room&&room.controller;const cores=room?room.find(FIND_HOSTILE_STRUCTURES,{filter:s=>s.structureType===STRUCTURE_INVADER_CORE}):[];out[n]={vis:!!room,res:ctrl&&ctrl.reservation?ctrl.reservation.ticksToEnd:(x.res|| (x.th&&x.th.res) ||null),cores:cores.length,coreHits:cores.map(s=>({x:s.pos.x,y:s.pos.y,hits:s.hits,hitsMax:s.hitsMax,lv:s.level})),host:room?room.find(FIND_HOSTILE_CREEPS).length:0,st:x.st||(x.th&&x.th.st)||null,needE:!!x.needE,armed:!!x.armed,tte:x.res||null,why:x.why||null};}return{t:Game.time,rem:out}})()"""),
("cmd", """(()=>{const c=Memory.cmd||null;return{t:Game.time,on:c&&c.on,at:c&&c.at,by:c&&c.by,c:c&&c.c,s:c&&c.s,v:c&&c.v,keys:c&&Object.keys(c)}})()"""),
("min", """(()=>{const H=Game.rooms.W46N8,W=Game.rooms.W47N8,hs=H&&H.storage,ht=H&&H.terminal,ws=W&&W.storage,wt=W&&W.terminal;return{t:Game.time,hs:hs&&{E:hs.store.energy||0,O:hs.store.O||0,K:hs.store.K||0},ht:ht&&{E:ht.store.energy||0,O:ht.store.O||0,K:ht.store.K||0},ws:ws&&{E:ws.store.energy||0,O:ws.store.O||0,K:ws.store.K||0},wt:wt&&{E:wt.store.energy||0,O:wt.store.O||0,K:wt.store.K||0}})()"""),
("def", """(()=>{const defs={};let n=0;for(const c of Object.values(Game.creeps)){const r=c.memory&&c.memory.role||'';if(r==='defender'||r==='w8defender'||r==='w8guard'||r==='rdef'||r==='guard'){n++;const body={};for(const p of c.body){const typ=p.type;body[typ]=(body[typ]||0)+1}defs[c.name]={rm:c.pos.roomName,x:c.pos.x,y:c.pos.y,ttl:c.ticksToLive||0,hits:c.hits,hitsMax:c.hitsMax,sp:!!c.spawning,body,role:r,st:c.memory&&c.memory.st}}}return{t:Game.time,n,defs}})()"""),
("sites", """(()=>{const o=[];for(const rn of ['W46N8','W47N8']){const R=Game.rooms[rn];if(!R)continue;for(const s of R.find(FIND_MY_CONSTRUCTION_SITES))o.push([rn,s.structureType,s.pos.x,s.pos.y,s.progress,s.progressTotal]);}return{t:Game.time,sites:o,ns:o.length}})()"""),
("w8extra", """(()=>{const d=(Memory.ops&&Memory.ops.w8day)||{};return{t:Game.time,sealMinE:d.sealMinE,sealPark:d.sealPark,upArm:d.upArm,upLatched:d.upLatched,softE:d.softE,softBand:d.softBand,siteRem:d.siteRem,keep:d.upgKeep,why:d.why,phase:d.phase,bankWhy:d.bankWhy,storE:d.storE,softCap2:d.softCap2,threatSoft:d.threatSoft,leanBank:d.leanBank,feedOk:d.feedOk,softLeft:d.softLeft,contMinPct:d.contMinPct,roadCrit:d.roadCrit,hubLink:d.hubLink,hubLinkE:d.hubLinkE,ctlBat:d.ctlBat,hubReady:d.hubReady}})()"""),
("resv", """(()=>{const want=['reserver','reserve7','reserve','rdef','w8defender','w8guard','defender'];const o=[];for(const c of Object.values(Game.creeps)){const r=c.memory&&c.memory.role||'';if(want.indexOf(r)<0)continue;o.push({n:c.name,r,rm:c.pos.roomName,x:c.pos.x,y:c.pos.y,ttl:c.ticksToLive||0,sp:!!c.spawning,hits:c.hits,st:c.memory&&c.memory.st});}const r7=Memory.ops&&Memory.ops.r7;return{t:Game.time,r7,creeps:o}})()"""),
("err", """(()=>{const s=Memory.stats||{};return{t:Game.time,le:s.lastErrorTick,nErr:s.nErr||s.nerr,cmt:s.commit||Memory.commit||null,cpu:Game.cpu.getUsed(),bucket:Game.cpu.bucket}})()"""),
]
allres = {}
for name, expr in QUERIES:
    print(f"=== Q {name} ===", flush=True)
    try:
        res = qmod.q(expr, timeout=25)
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
print("=== Q DONE keys="+",".join(allres)+" ===")
