#!/usr/bin/env python3
import json, os, sys
sys.path.insert(0, "/workspace/screeps/tools")
import q as qmod
os.chdir("/workspace/screeps")
outdir = "/tmp/patrol_1113_1419"
os.makedirs(outdir, exist_ok=True)
QUERIES = [
("hublink", """(()=>{const R=Game.rooms.W47N8;if(!R)return{t:Game.time,vis:false};const look=(x,y)=>R.lookAt(x,y).map(o=>({t:o.type,st:o.structure&&o.structure.structureType,hits:o.structure&&o.structure.hits,hitsMax:o.structure&&o.structure.hitsMax,e:o.structure&&o.structure.store&&o.structure.store.energy,p:o.constructionSite&&o.constructionSite.progress,tP:o.constructionSite&&o.constructionSite.progressTotal,id:(o.structure&&o.structure.id)||(o.constructionSite&&o.constructionSite.id)}));const links=R.find(FIND_MY_STRUCTURES,{filter:s=>s.structureType===STRUCTURE_LINK}).map(s=>({x:s.pos.x,y:s.pos.y,e:s.store.energy||0,hits:s.hits,id:s.id,cd:s.cooldown}));const linkSites=R.find(FIND_MY_CONSTRUCTION_SITES,{filter:s=>s.structureType===STRUCTURE_LINK}).map(s=>({x:s.pos.x,y:s.pos.y,p:s.progress,tP:s.progressTotal,id:s.id}));return{t:Game.time,at3334:look(33,34),at3233:look(32,33),at3533:look(35,33),at3333:look(33,33),links,linkSites}})()"""),
("labsroads", """(()=>{const rooms=['W46N8','W47N8'];const out={};for(const rn of rooms){const R=Game.rooms[rn];if(!R){out[rn]={vis:false};continue;}const labs=R.find(FIND_MY_STRUCTURES,{filter:s=>s.structureType===STRUCTURE_LAB}).map(s=>({x:s.pos.x,y:s.pos.y,hits:s.hits}));const fac=R.find(FIND_MY_STRUCTURES,{filter:s=>s.structureType===STRUCTURE_FACTORY}).map(s=>({x:s.pos.x,y:s.pos.y,hits:s.hits}));const sites=R.find(FIND_MY_CONSTRUCTION_SITES).map(s=>({t:s.structureType,x:s.pos.x,y:s.pos.y,p:s.progress,tP:s.progressTotal}));const byT={};for(const s of sites){byT[s.t]=(byT[s.t]||0)+1;}const labSites=sites.filter(s=>s.t==='lab');const roadSites=sites.filter(s=>s.t==='road');const otherSites=sites.filter(s=>s.t!=='lab'&&s.t!=='road');const ramps=R.find(FIND_MY_STRUCTURES,{filter:s=>s.structureType===STRUCTURE_RAMPART&&((s.pos.x===35&&s.pos.y===30)||(s.pos.x===27&&s.pos.y===38)||(s.pos.x===27&&s.pos.y===39))}).map(s=>({x:s.pos.x,y:s.pos.y,hits:s.hits}));out[rn]={vis:true,nSites:sites.length,byT,labs,fac,labSites,roadSites,otherSites,ramps};}return{t:Game.time,rooms:out}})()"""),
("guard", """(()=>{const names=['w8guard84238816','w8defender84238817'];const out={};for(const n of names){const c=Game.creeps[n];if(!c){out[n]={alive:false,mem:(Memory.creeps&&Memory.creeps[n])||null};continue;}out[n]={alive:true,rm:c.pos.roomName,x:c.pos.x,y:c.pos.y,ttl:c.ticksToLive||0,hits:c.hits,hitsMax:c.hitsMax,fat:c.fatigue,st:c.memory&&c.memory.st,idle:c.memory&&c.memory.idle,post:c.memory&&c.memory.post,tgt:c.memory&&c.memory.tgt,move:c.memory&&c.memory._move,say:c.saying};}const host={};for(const rn of ['W47N8','W47N7','W46N8']){const R=Game.rooms[rn];host[rn]=R?R.find(FIND_HOSTILE_CREEPS).map(c=>({n:c.name,x:c.pos.x,y:c.pos.y,owner:c.owner&&c.owner.username,hits:c.hits,ttl:c.ticksToLive})):null;}return{t:Game.time,out,host,w8threat:Memory.ops&&Memory.ops.w8threat}})()"""),
("r7", """(()=>{const rs=[];for(const c of Object.values(Game.creeps)){const r=c.memory&&c.memory.role;if(r==='reserver'||r==='reserve7')rs.push({n:c.name,r,rm:c.pos.roomName,x:c.pos.x,y:c.pos.y,ttl:c.ticksToLive||0,sp:!!c.spawning,st:c.memory&&c.memory.st});}const endTimes={},vis={};for(const n of ['W45N8','W45N7','W47N7']){const room=Game.rooms[n];const c=room&&room.controller;vis[n]=!!room;endTimes[n]=c&&c.reservation?{user:c.reservation.username,left:c.reservation.ticksToEnd,end:Game.time+c.reservation.ticksToEnd}:null;}return{t:Game.time,rs,vis,endTimes,r7:(Memory.ops&&Memory.ops.r7)||null}})()"""),
]
allres = {}
for name, expr in QUERIES:
    print(f"=== Q {name} (len={len(expr)}) ===", flush=True)
    try:
        res = qmod.q(expr, timeout=30)
        path = f"{outdir}/q_{name}.json"
        with open(path, "w") as f:
            json.dump(res, f, indent=2, default=str)
        print(json.dumps(res, default=str, separators=(',', ':'))[:6000], flush=True)
        allres[name]=res
    except SystemExit as e:
        print(f"FAIL {name}: {e}", flush=True)
    except Exception as e:
        print(f"ERR {name}: {type(e).__name__} {e}", flush=True)
with open(f"{outdir}/q2_all.json","w") as f:
    json.dump(allres, f, indent=2, default=str)
print("=== Q2 DONE ===", flush=True)
