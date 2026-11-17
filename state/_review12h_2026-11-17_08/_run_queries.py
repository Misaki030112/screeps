#!/usr/bin/env python3
import json, sys, os, time
sys.path.insert(0, "/workspace/screeps/tools")
import q as qmod
os.chdir("/workspace/screeps")
outdir = "/workspace/screeps/state/_review12h_2026-11-17_08"
os.makedirs(outdir, exist_ok=True)
run_path = os.path.join(outdir, "run.txt")

# Keep expressions compact: server wrap must stay <= 1000 chars.
QUERIES = [
("home", """(()=>{const H=Game.rooms.W46N8,W=Game.rooms.W47N8,hc=H&&H.controller,wc=W&&W.controller,hs=H&&H.storage,ws=W&&W.storage;return{t:Game.time,b:Game.cpu.bucket,c:+Game.cpu.getUsed().toFixed(2),n:_.size(Game.creeps),hs:hs&&hs.store.energy,ws:ws&&ws.store.energy,hp:hc&&hc.progress,wp:wc&&wc.progress,ea:H&&H.energyAvailable,eaw:W&&W.energyAvailable,sma:hc&&hc.safeModeAvailable,ttd:hc&&hc.ticksToDowngrade,smaW:wc&&wc.safeModeAvailable,ttdW:wc&&wc.ticksToDowngrade,cmt:(Memory.stats&&Memory.stats.commit)||Memory.commit||null,le:Memory.stats&&Memory.stats.lastErrorTick,nErr:Memory.stats&&Memory.stats.nErr}})()"""),
("uf", """(Memory.ops&&Memory.ops.upgFeed)||null"""),
("soft", """(()=>{const d=(Memory.ops&&Memory.ops.w8day)||{};return{t:Game.time,bWhy:d.bankWhy,sL:d.softLeft,sC2:d.softCap2,keep:d.upgKeep,thS:d.threatSoft,storE:d.storE,upL:d.upLatched,lb:d.leanBank,why:d.why,phase:d.phase,eAvail:d.eAvail,eCap:d.eCap,upN:d.upN,feedOk:d.feedOk,upArm:d.upArm,sealPark:d.sealPark,sealMinE:d.sealMinE,siteRem:d.siteRem,hubLink:d.hubLink,hubReady:d.hubReady}})()"""),
("w8extra", """(()=>{const d=(Memory.ops&&Memory.ops.w8day)||{};return{t:Game.time,sealMinE:d.sealMinE,sealPark:d.sealPark,upArm:d.upArm,upLatched:d.upLatched,softE:d.softE,softBand:d.softBand,siteRem:d.siteRem,keep:d.upgKeep,why:d.why,phase:d.phase,bankWhy:d.bankWhy,storE:d.storE,softCap2:d.softCap2,threatSoft:d.threatSoft,leanBank:d.leanBank,feedOk:d.feedOk,softLeft:d.softLeft,contMinPct:d.contMinPct,roadCrit:d.roadCrit,hubLink:d.hubLink,hubLinkE:d.hubLinkE,ctlBat:d.ctlBat,hubReady:d.hubReady,upgCeil:d.upgCeil}})()"""),
("w8day", """(Memory.ops&&Memory.ops.w8day)||null"""),
("roles", """(()=>{const roles={};const crit=[];const want=['miner','rminer','reserver','queen','w8filler','w8miner','w8rminer','reserve7','reserve','upgrader','w8upgrader'];for(const c of Object.values(Game.creeps)){const r=c.memory&&c.memory.role||'?';roles[r]=(roles[r]||0)+1;const dest=c.memory&&c.memory._move&&c.memory._move.dest;if(want.indexOf(r)>=0){crit.push({n:c.name,r,rm:c.pos.roomName,x:c.pos.x,y:c.pos.y,ttl:c.ticksToLive||0,e:c.store&&c.store.energy||0,w:c.getActiveBodyparts(WORK),sp:!!c.spawning,st:c.memory&&c.memory.st,dest:dest||null});}}return{t:Game.time,roles,crit}})()"""),
("rem", """(()=>{const names=['W45N8','W45N7','W47N7'];const out={};for(const n of names){const x=(Memory.ops&&Memory.ops.rem&&Memory.ops.rem[n])||{};const room=Game.rooms[n];const ctrl=room&&room.controller;const cores=room?room.find(FIND_HOSTILE_STRUCTURES,{filter:s=>s.structureType===STRUCTURE_INVADER_CORE}):[];out[n]={vis:!!room,res:ctrl&&ctrl.reservation?ctrl.reservation.ticksToEnd:(x.res|| (x.th&&x.th.res) ||null),cores:cores.length,coreHits:cores.map(s=>({x:s.pos.x,y:s.pos.y,hits:s.hits,hitsMax:s.hitsMax,lv:s.level})),host:room?room.find(FIND_HOSTILE_CREEPS).length:0,st:x.st||(x.th&&x.th.st)||null,needE:!!x.needE,armed:!!x.armed,tte:x.res||null,why:x.why||null};}return{t:Game.time,rem:out}})()"""),
("cmd", """(()=>{const c=Memory.cmd||null;return{t:Game.time,on:c&&c.on,at:c&&c.at,by:c&&c.by,c:c&&c.c,s:c&&c.s,v:c&&c.v,keys:c&&Object.keys(c)}})()"""),
("def", """(()=>{const defs={};let n=0;for(const c of Object.values(Game.creeps)){const r=c.memory&&c.memory.role||'';if(r==='defender'||r==='w8defender'||r==='w8guard'||r==='rdef'||r==='guard'){n++;const body={};for(const p of c.body){const typ=p.type;body[typ]=(body[typ]||0)+1}defs[c.name]={rm:c.pos.roomName,x:c.pos.x,y:c.pos.y,ttl:c.ticksToLive||0,hits:c.hits,hitsMax:c.hitsMax,sp:!!c.spawning,body,role:r,st:c.memory&&c.memory.st}}}return{t:Game.time,n,defs}})()"""),
("sites", """(()=>{const o=[];for(const rn of ['W46N8','W47N8']){const R=Game.rooms[rn];if(!R)continue;for(const s of R.find(FIND_MY_CONSTRUCTION_SITES))o.push([rn,s.structureType,s.pos.x,s.pos.y,s.progress,s.progressTotal]);}return{t:Game.time,sites:o,ns:o.length}})()"""),
("labsN", """(()=>{const c=(rn,t)=>Game.rooms[rn]?Game.rooms[rn].find(FIND_MY_STRUCTURES,{filter:s=>s.structureType===t}).length:null;return{t:Game.time,hLab:c('W46N8',STRUCTURE_LAB),hFac:c('W46N8',STRUCTURE_FACTORY),wLab:c('W47N8',STRUCTURE_LAB),wFac:c('W47N8',STRUCTURE_FACTORY),hTerm:c('W46N8',STRUCTURE_TERMINAL),wTerm:c('W47N8',STRUCTURE_TERMINAL)};})()"""),
("lab2", """(()=>{const L=(Memory.ops&&(Memory.ops.labReady||Memory.ops.lab))||{};const m=(Memory.ops&&Memory.ops.w8min)||{};const w9=(Memory.ops&&Memory.ops.w47n9)||{};return{t:Game.time,mode:L.mode,why:L.why,propose:L.propose,actOk:L.actOk,actGaps:L.actGaps,ready:L.ready,homeStor:L.homeStor,w8minWhy:m.why,w8minGaps:m.gaps,flipGaps:m.flipGaps,w9on:w9.on,w9phase:w9.phase,w9rec:w9.recycle,w9note:w9.note};})()"""),
("min2", """(()=>{const H=Game.rooms.W46N8,W=Game.rooms.W47N8;const p=s=>s&&{E:s.store.energy||0,O:s.store.O||0,K:s.store.K||0};return{t:Game.time,hs:p(H&&H.storage),ht:p(H&&H.terminal),ws:p(W&&W.storage),wt:p(W&&W.terminal)};})()"""),
("resv", """(()=>{const want=['reserver','reserve7','reserve','rdef','w8defender','w8guard','defender'];const o=[];for(const c of Object.values(Game.creeps)){const r=c.memory&&c.memory.role||'';if(want.indexOf(r)<0)continue;o.push({n:c.name,r,rm:c.pos.roomName,x:c.pos.x,y:c.pos.y,ttl:c.ticksToLive||0,sp:!!c.spawning,hits:c.hits,st:c.memory&&c.memory.st});}const r7=Memory.ops&&Memory.ops.r7;return{t:Game.time,r7,creeps:o}})()"""),
("remth", """(()=>{const o=Memory.ops||{},rem={};for(const n of ['W45N8','W45N7','W47N7'])rem[n]=(o.rem&&o.rem[n])||null;return{t:Game.time,rem,r7:o.r7,th:o.w8threat,inv:o.w8inv,stats:(Memory.stats&&Memory.stats.remote)||null};})()"""),
("err", """(()=>{const s=Memory.stats||{};return{t:Game.time,le:s.lastErrorTick,nErr:s.nErr||s.nerr,cmt:s.commit||Memory.commit||null,cpu:Game.cpu.getUsed(),bucket:Game.cpu.bucket}})()"""),
("walls", """(()=>{const o={};for(const rn of['W46N8','W47N8']){const R=Game.rooms[rn];if(!R){o[rn]=null;continue;}let mw=1e15,mr=1e15,nw=0,nr=0,wx,wy,rx,ry;for(const s of R.find(FIND_STRUCTURES)){if(s.structureType===STRUCTURE_WALL){nw++;if(s.hits<mw){mw=s.hits;wx=s.pos.x;wy=s.pos.y}}if(s.structureType===STRUCTURE_RAMPART){nr++;if(s.hits<mr){mr=s.hits;rx=s.pos.x;ry=s.pos.y}}}o[rn]={nw,nr,mw:mw<1e15?mw:null,mr:mr<1e15?mr:null,wx,wy,rx,ry}}return{t:Game.time,o}})()"""),
]

with open(run_path, "w") as rf:
    rf.write(f"start {time.strftime('%Y-%m-%d %H:%M:%S %Z')}\n")
    for name, expr in QUERIES:
        # estimate wrap size like q.py
        tag = "QQ" + "0"*16
        wrapped = f"(function(){{try{{return ({expr});}}catch(e){{return 'ERR '+e.stack}}}})()"
        full = f"'{tag}'+JSON.stringify({{t:Game.time,v:{wrapped}}})"
        rf.write(f"len {name}: expr={len(expr)} wrapped_full={len(full)}\n")
        if len(full) > 1000:
            rf.write(f"WARN {name} may exceed MAX_EXPR\n")

allres = {}
ok = 0
fail = 0
for name, expr in QUERIES:
    header = f"=== Q {name} (len={len(expr)}) ==="
    print(header, flush=True)
    with open(run_path, "a") as rf:
        rf.write(header + "\n")
    try:
        res = qmod.q(expr, timeout=35)
        path = os.path.join(outdir, f"q_{name}.json")
        with open(path, "w") as f:
            json.dump(res, f, indent=2, default=str)
        compact = json.dumps(res, default=str, separators=(',', ':'))
        print(compact[:8000], flush=True)
        with open(run_path, "a") as rf:
            rf.write(compact + "\n")
        allres[name] = res
        ok += 1
    except SystemExit as e:
        msg = f"FAIL {name}: {e}"
        print(msg, flush=True)
        with open(run_path, "a") as rf:
            rf.write(msg + "\n")
        fail += 1
    except Exception as e:
        msg = f"ERR {name}: {type(e).__name__} {e}"
        print(msg, flush=True)
        with open(run_path, "a") as rf:
            rf.write(msg + "\n")
        fail += 1
    time.sleep(0.4)

with open(os.path.join(outdir, "q_all.json"), "w") as f:
    json.dump(allres, f, indent=2, default=str)
footer = f"=== Q DONE ok={ok} fail={fail} at {time.strftime('%Y-%m-%d %H:%M:%S %Z')} ==="
print(footer, flush=True)
with open(run_path, "a") as rf:
    rf.write(footer + "\n")
