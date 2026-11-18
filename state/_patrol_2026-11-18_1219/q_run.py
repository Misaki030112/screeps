#!/usr/bin/env python3
import sys, json
from pathlib import Path
sys.path.insert(0,'/workspace/screeps/tools')
import q as qmod
OUT = Path('/workspace/screeps/state/_patrol_2026-11-18_1219')
queries = []
queries.append(('live', """(()=>{
  const t=Game.time,b=Game.cpu.bucket,c=+Game.cpu.getUsed().toFixed(2);
  const H=Game.rooms.W46N8,W=Game.rooms.W47N8;
  const up=[], fill=[], hub=[], crit=[];
  const want=['miner','rminer','reserver','queen','w8filler','w8miner','w8rminer','reserve7','reserve','upgrader','w8upgrader','rdef','w8guard','w8defender'];
  for(const cr of Object.values(Game.creeps)){
    const r=cr.memory&&cr.memory.role||'?';
    const o={n:cr.name,r,rm:cr.pos.roomName,x:cr.pos.x,y:cr.pos.y,ttl:cr.ticksToLive||0,e:cr.store&&cr.store.energy||0,sp:!!cr.spawning,st:cr.memory&&cr.memory.st};
    if(r==='w8upgrader'||r==='upgrader') up.push(o);
    if(r==='w8filler') fill.push(o);
    if(want.indexOf(r)>=0) crit.push(o);
    if(cr.pos.roomName==='W47N8' && cr.pos.x>=32&&cr.pos.x<=35&&cr.pos.y>=30&&cr.pos.y<=34) hub.push(o);
  }
  const hs=H&&H.storage, ws=W&&W.storage, hc=H&&H.controller, wc=W&&W.controller;
  let hubC=null, tiles={};
  if(W){
    const look=W.lookAt(33,33);
    hubC=look.filter(x=>x.structure&&x.structure.structureType==='container').map(x=>({e:x.structure.store.energy,hits:x.structure.hits}))[0]||null;
    tiles['33,33']={c:look.filter(x=>x.creep).map(x=>x.creep.name),e:hubC&&hubC.e};
    for(const [x,y] of [[34,32],[34,33],[33,34],[34,30],[32,32],[33,31]]){
      const L=W.lookAt(x,y);
      tiles[x+','+y]={c:L.filter(z=>z.creep).map(z=>z.creep.name), s:L.filter(z=>z.structure).map(z=>z.structure.structureType)};
    }
  }
  const cmt=(Memory.stats&&Memory.stats.commit)||Memory.commit||null;
  const d=(Memory.ops&&Memory.ops.w8day)||{};
  const uf=Memory.ops&&Memory.ops.upgFeed;
  const ops=Memory.ops||{};
  return {t,b,c,visW:!!W,visH:!!H,cmt,hs:hs&&hs.store.energy,ws:ws&&ws.store.energy,
    hp:hc&&hc.progress,wp:wc&&wc.progress,sma:hc&&hc.safeModeAvailable,ttd:hc&&hc.ticksToDowngrade,
    smaW:wc&&wc.safeModeAvailable,ttdW:wc&&wc.ticksToDowngrade,ea:H&&H.energyAvailable,eaw:W&&W.energyAvailable,
    nErr:Memory.stats&&Memory.stats.lastErrorTick&&Memory.stats.nErr,le:Memory.stats&&Memory.stats.lastErrorTick,
    lastA:Memory.stats&&Memory.stats.lastAlertTick, alerts:Memory.stats&&Memory.stats.alerts,
    up,fill,hub,tiles,hubC,
    keep:d.upgKeep,upgCeil:d.upgCeil,bWhy:d.bankWhy,sC2:d.softCap2,thS:d.threatSoft,upL:d.upLatched,
    sealPark:d.sealPark,sealMinE:d.sealMinE,feedOk:d.feedOk,phase:d.phase,why:d.why,upArm:d.upArm,
    storE:d.storE,siteRem:d.siteRem,hubLink:d.hubLink,hubReady:d.hubReady,softLeft:d.softLeft,leanBank:d.leanBank,
    uf, w8threat:ops.w8threat,w8inv:ops.w8inv,w8flee:ops.w8flee,labs:ops.labs||ops.labReady};
})()"""))
queries.append(('rem', """(()=>{
  const names=['W45N8','W45N7','W47N7'];
  const out={};
  for(const n of names){
    const x=(Memory.ops&&Memory.ops.rem&&Memory.ops.rem[n])||{};
    const room=Game.rooms[n];
    const ctrl=room&&room.controller;
    const cores=room?room.find(FIND_HOSTILE_STRUCTURES,{filter:s=>s.structureType===STRUCTURE_INVADER_CORE}):[];
    out[n]={vis:!!room,res:ctrl&&ctrl.reservation?ctrl.reservation.ticksToEnd:(x.res||(x.th&&x.th.res)||null),
      cores:cores.length,host:room?room.find(FIND_HOSTILE_CREEPS).length:null,st:x.st||(x.th&&x.th.st)||null,
      mem:x};
  }
  const c=Memory.cmd||null;
  const L=(Memory.ops&&(Memory.ops.labReady||Memory.ops.labs||Memory.ops.lab))||{};
  const r7=Memory.ops&&Memory.ops.r7;
  const defs=[], resv=[], miners=[];
  for(const cr of Object.values(Game.creeps)){
    const r=cr.memory&&cr.memory.role||'';
    if(r==='defender'||r==='w8defender'||r==='w8guard'||r==='rdef'||r==='guard')
      defs.push({n:cr.name,r,rm:cr.pos.roomName,x:cr.pos.x,y:cr.pos.y,ttl:cr.ticksToLive||0,sp:!!cr.spawning,hits:cr.hits,hM:cr.hitsMax});
    if(r==='reserver'||r==='reserve7'||r==='reserve')
      resv.push({n:cr.name,r,rm:cr.pos.roomName,x:cr.pos.x,y:cr.pos.y,ttl:cr.ticksToLive||0,sp:!!cr.spawning,st:cr.memory&&cr.memory.st});
    if(r==='miner'||r==='rminer'||r==='w8miner'||r==='w8rminer'||r==='queen'||r==='w8filler')
      miners.push({n:cr.name,r,rm:cr.pos.roomName,x:cr.pos.x,y:cr.pos.y,ttl:cr.ticksToLive||0,sp:!!cr.spawning});
  }
  const ns=Game.constructionSites?Object.keys(Game.constructionSites).length:0;
  return {t:Game.time,rem:out,cmd:{on:c&&c.on,at:c&&c.at,by:c&&c.by,c:c&&c.c,s:c&&c.s,v:c&&c.v},
    lab:L, r7,defs,resv,miners,ns};
})()"""))
queries.append(('min', """(()=>{
  const p=s=>s&&{E:s.store.energy||0,O:s.store[RESOURCE_OXYGEN]||0,K:s.store[RESOURCE_KEANIUM]||0,KO:s.store[RESOURCE_KEANIUM_OXIDE]||0};
  const H=Game.rooms.W46N8,W=Game.rooms.W47N8;
  let koLab=0, labs=[];
  if(H){for(const s of H.find(FIND_MY_STRUCTURES,{filter:s=>s.structureType===STRUCTURE_LAB})){koLab+=s.store[RESOURCE_KEANIUM_OXIDE]||0;labs.push({x:s.pos.x,y:s.pos.y,min:s.mineralType,amt:s.store[s.mineralType]||0,e:s.store.energy||0});}}
  const spawns=Object.values(Game.spawns).map(s=>({rn:s.room.name,n:s.name,sp:s.spawning?{n:s.spawning.name,rem:s.spawning.remainingTime}:null,e:s.store.energy}));
  return {t:Game.time,hs:p(H&&H.storage),ht:p(H&&H.terminal),ws:p(W&&W.storage),wt:p(W&&W.terminal),koLab,labs,spawns,gcl:Game.gcl};
})()"""))
for name, expr in queries:
    print('QUERY', name, 'len', len(expr), flush=True)
    try:
        r = qmod.q(expr, timeout=35)
        (OUT/f'q_{name}.json').write_text(json.dumps(r, indent=2)+'\n')
        print('OK', name, 't', (r.get('t') if isinstance(r, dict) else None) or (isinstance(r, dict) and (r.get('v') or {}).get('t')), flush=True)
    except Exception as e:
        print('FAIL', name, type(e).__name__, e, flush=True)
        (OUT/f'q_{name}.err').write_text(repr(e)+'\n')
print('ALL_DONE')
