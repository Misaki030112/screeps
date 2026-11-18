#!/usr/bin/env python3
import sys, json
from pathlib import Path
sys.path.insert(0,'/workspace/screeps/tools')
import q as qmod
OUT = Path('/workspace/screeps/state/_patrol_2026-11-19_0217')
Qs = [
('ping', "Game.time"),
('home', """(()=>{const H=Game.rooms.W46N8,W=Game.rooms.W47N8,hc=H&&H.controller,wc=W&&W.controller;
return {t:Game.time,b:Game.cpu.bucket,c:+Game.cpu.getUsed().toFixed(2),visH:!!H,visW:!!W,
cmt:(Memory.stats&&Memory.stats.commit)||Memory.commit||null,
hs:H&&H.storage&&H.storage.store.energy,ws:W&&W.storage&&W.storage.store.energy,
hp:hc&&hc.progress,wp:wc&&wc.progress,sma:hc&&hc.safeModeAvailable,ttd:hc&&hc.ticksToDowngrade,
smaW:wc&&wc.safeModeAvailable,ttdW:wc&&wc.ticksToDowngrade,ea:H&&H.energyAvailable,eaw:W&&W.energyAvailable,
le:Memory.stats&&Memory.stats.lastErrorTick,lastA:Memory.stats&&Memory.stats.lastAlertTick};})()"""),
('uf', """(()=>{const d=(Memory.ops&&Memory.ops.w8day)||{},uf=Memory.ops&&Memory.ops.upgFeed;
return {t:Game.time,keep:d.upgKeep,upgCeil:d.upgCeil,bWhy:d.bankWhy,sC2:d.softCap2,thS:d.threatSoft,upL:d.upLatched,
sealPark:d.sealPark,sealMinE:d.sealMinE,feedOk:d.feedOk,phase:d.phase,why:d.why,upArm:d.upArm,storE:d.storE,
siteRem:d.siteRem,hubLink:d.hubLink,hubReady:d.hubReady,softLeft:d.softLeft,leanBank:d.leanBank,uf:uf};})()"""),
('ops', """(()=>{const o=Memory.ops||{},c=Memory.cmd||null,L=o.labReady||o.labs||{};
return {t:Game.time,w8threat:o.w8threat,w8inv:o.w8inv,w8flee:o.w8flee,labs:o.labs,labReady:L,r7:o.r7,
cmd:{on:c&&c.on,at:c&&c.at,by:c&&c.by,c:c&&c.c,s:c&&c.s,v:c&&c.v}};})()"""),
('up', """(()=>{const o=[];
for(const cr of Object.values(Game.creeps)){
  const r=cr.memory&&cr.memory.role;
  if(r==='upgrader'||r==='w8upgrader') o.push({n:cr.name,r,rm:cr.pos.roomName,x:cr.pos.x,y:cr.pos.y,ttl:cr.ticksToLive||0,e:cr.store&&cr.store.energy||0,sp:!!cr.spawning,st:cr.memory&&cr.memory.st});
}
return {t:Game.time,o};})()"""),
('crit', """(()=>{const o=[],want=['miner','rminer','reserver','queen','w8filler','w8miner','w8rminer','reserve7','reserve','rdef','w8guard','w8defender','defender'];
for(const cr of Object.values(Game.creeps)){
  const r=cr.memory&&cr.memory.role||'?';
  if(want.indexOf(r)>=0) o.push({n:cr.name,r,rm:cr.pos.roomName,x:cr.pos.x,y:cr.pos.y,ttl:cr.ticksToLive||0,sp:!!cr.spawning,hits:cr.hits,hM:cr.hitsMax,st:cr.memory&&cr.memory.st});
}
return {t:Game.time,o};})()"""),
]
Qs.append(('rem', """(()=>{const names=['W45N8','W45N7','W47N7'],out={};
for(const n of names){
  const x=(Memory.ops&&Memory.ops.rem&&Memory.ops.rem[n])||{},room=Game.rooms[n],ctrl=room&&room.controller;
  const cores=room?room.find(FIND_HOSTILE_STRUCTURES,{filter:s=>s.structureType===STRUCTURE_INVADER_CORE}):[];
  out[n]={vis:!!room,res:ctrl&&ctrl.reservation?ctrl.reservation.ticksToEnd:null,by:ctrl&&ctrl.reservation&&ctrl.reservation.username,
    cores:cores.length,host:room?room.find(FIND_HOSTILE_CREEPS).length:null};
}
return {t:Game.time,rem:out,ns:Game.constructionSites?Object.keys(Game.constructionSites).length:0};})()"""))
Qs.append(('min', """(()=>{const p=s=>s&&{E:s.store.energy||0,O:s.store[RESOURCE_OXYGEN]||0,K:s.store[RESOURCE_KEANIUM]||0,KO:s.store[RESOURCE_KEANIUM_OXIDE]||0};
const H=Game.rooms.W46N8,W=Game.rooms.W47N8; let koLab=0;
if(H){for(const s of H.find(FIND_MY_STRUCTURES,{filter:s=>s.structureType===STRUCTURE_LAB})) koLab+=s.store[RESOURCE_KEANIUM_OXIDE]||0;}
const spawns=Object.values(Game.spawns).map(s=>({rn:s.room.name,n:s.name,sp:s.spawning?{n:s.spawning.name,rem:s.spawning.remainingTime}:null,e:s.store.energy}));
return {t:Game.time,hs:p(H&&H.storage),ht:p(H&&H.terminal),ws:p(W&&W.storage),wt:p(W&&W.terminal),koLab,spawns,gcl:Game.gcl};})()"""))
Qs.append(('hub', """(()=>{const W=Game.rooms.W47N8,tiles={}; if(!W) return {t:Game.time,vis:false};
for(const [x,y] of [[33,33],[34,32],[34,33],[33,34],[34,30],[32,32],[33,31],[33,30],[12,25],[14,26],[14,27],[14,28]]){
  const L=W.lookAt(x,y);
  tiles[x+','+y]={c:L.filter(z=>z.creep).map(z=>z.creep.name),s:L.filter(z=>z.structure).map(z=>z.structure.structureType+(z.structure.structureType==='container'?':'+z.structure.store.energy:''))};
}
return {t:Game.time,vis:true,tiles};})()"""))
wrap_over = len("'QQ123456789012345'+JSON.stringify({t:Game.time,v:(function(){try{return (X);}catch(e){return 'ERR '+e.stack}})()})") - 1
for name, expr in Qs:
    wrapped_len = wrap_over + len(expr)
    print('SIZE', name, 'expr', len(expr), 'wrapped~', wrapped_len, 'OK' if wrapped_len<=1000 else 'TOO BIG', flush=True)

for name, expr in Qs:
    print('QUERY', name, flush=True)
    try:
        r = qmod.q(expr, timeout=35)
        (OUT/f'q_{name}.json').write_text(json.dumps(r, indent=2)+'\n')
        print('OK', name, 't', r.get('t') if isinstance(r, dict) else None, flush=True)
    except Exception as e:
        print('FAIL', name, type(e).__name__, e, flush=True)
        (OUT/f'q_{name}.err').write_text(repr(e)+'\n')
print('ALL_DONE')
