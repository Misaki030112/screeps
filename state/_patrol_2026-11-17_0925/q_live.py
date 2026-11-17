#!/usr/bin/env python3
import sys, json
from pathlib import Path
sys.path.insert(0,'/workspace/screeps/tools')
import q as qmod

OUT = Path('/workspace/screeps/state/_patrol_2026-11-17_0925')

SURVEY = """(()=>{
  const r=Game.rooms.W45N7;
  const cores=r?r.find(FIND_HOSTILE_STRUCTURES,{filter:s=>s.structureType===STRUCTURE_INVADER_CORE}):[];
  const host=r?r.find(FIND_HOSTILE_CREEPS):[];
  const mine=r?r.find(FIND_MY_CREEPS).map(c=>({n:c.name,r:c.memory&&c.memory.role,x:c.pos.x,y:c.pos.y,ttl:c.ticksToLive,hits:c.hits,hM:c.hitsMax})):null;
  const src=r?r.find(FIND_SOURCES).map(s=>({x:s.pos.x,y:s.pos.y,e:s.energy,c:s.energyCapacity})):null;
  const res=r&&r.controller&&r.controller.reservation;
  return {t:Game.time, vis:!!r,
    res:res?{u:res.username,tte:res.ticksToEnd}:null,
    cores:cores.map(s=>({x:s.pos.x,y:s.pos.y,hits:s.hits,hM:s.hitsMax,l:s.level,ttd:s.ticksToDeploy})),
    host:host.map(c=>({n:c.name,o:c.owner&&c.owner.username,x:c.pos.x,y:c.pos.y,hits:c.hits,hM:c.hitsMax,ttl:c.ticksToLive,body:c.body.map(p=>p.type[0]).join('')})),
    mine, src};
})()"""

A = """(()=>{
  const R=Game.rooms.W47N8; if(!R) return {t:Game.time,vis:false};
  const src=R.find(FIND_SOURCES).map(s=>({x:s.pos.x,y:s.pos.y,e:s.energy,c:s.energyCapacity}));
  const links=R.find(FIND_MY_STRUCTURES,{filter:s=>s.structureType===STRUCTURE_LINK}).map(s=>({x:s.pos.x,y:s.pos.y,e:s.store.energy,c:s.store.getCapacity(RESOURCE_ENERGY),cd:s.cooldown}));
  const cont=R.find(FIND_STRUCTURES,{filter:s=>s.structureType===STRUCTURE_CONTAINER}).map(s=>({x:s.pos.x,y:s.pos.y,e:s.store.energy,hits:s.hits}));
  return {t:Game.time,vis:true,src,links,cont,stor:R.storage&&R.storage.store.energy};
})()"""


W47N7S = """(()=>{
  const r=Game.rooms.W47N7;
  const cores=r?r.find(FIND_HOSTILE_STRUCTURES,{filter:s=>s.structureType===STRUCTURE_INVADER_CORE}):[];
  const host=r?r.find(FIND_HOSTILE_CREEPS):[];
  const mine=r?r.find(FIND_MY_CREEPS).map(c=>({n:c.name,r:c.memory&&c.memory.role,x:c.pos.x,y:c.pos.y,ttl:c.ticksToLive,hits:c.hits,hM:c.hitsMax,st:c.memory&&c.memory.st})):null;
  const src=r?r.find(FIND_SOURCES).map(s=>({x:s.pos.x,y:s.pos.y,e:s.energy,c:s.energyCapacity})):null;
  const res=r&&r.controller&&r.controller.reservation;
  return {t:Game.time, vis:!!r,
    res:res?{u:res.username,tte:res.ticksToEnd}:null,
    cores:cores.map(s=>({x:s.pos.x,y:s.pos.y,hits:s.hits,hM:s.hitsMax,l:s.level,ttd:s.ticksToDeploy})),
    host:host.map(c=>({n:c.name,o:c.owner&&c.owner.username,x:c.pos.x,y:c.pos.y,hits:c.hits,hM:c.hitsMax,ttl:c.ticksToLive,body:c.body.map(p=>p.type[0]).join('')})),
    mine, src};
})()"""



LABSMEM = "(()=>{const o=Memory.ops||{};return{t:Game.time,labs:o.labs||null,labRun:o.labRun||null,labReady:o.labReady||null};})()"
SPAWNS = "(()=>{const spawns=Object.values(Game.spawns).map(s=>({rn:s.room.name,n:s.name,sp:s.spawning?{n:s.spawning.name,rem:s.spawning.remainingTime}:null,e:s.store.energy}));return{t:Game.time,spawns};})()"
HAULERS = "(()=>{const want=['hauler','queen','w8filler'];const o=[];for(const c of Object.values(Game.creeps)){const r=c.memory&&c.memory.role||'';if(want.indexOf(r)<0 && r.indexOf('hauler')<0)continue;const body={};for(const p of c.body)body[p.type]=(body[p.type]||0)+1;o.push({n:c.name,r,rm:c.pos.roomName,x:c.pos.x,y:c.pos.y,ttl:c.ticksToLive||0,e:c.store&&c.store.energy||0,sp:!!c.spawning,st:c.memory&&c.memory.st,body,rec:!!(c.memory&&(c.memory.recycle||c.memory.rec))});}return{t:Game.time,o}})()"

ns={}
exec(Path('/workspace/screeps/state/_patrol_2026-11-17_0925/_q_exprs.py').read_text(), ns)
wanted={n:e for n,e in ns['QUERIES'] if n in ('uf','soft','rem','def','remth','roles','home','cmd','err','labsN','lab2','min2','sites','resv','w8extra')}
wanted['w45']=SURVEY
wanted['w47n7']=W47N7S
wanted['w47src']=A
wanted['labsMem']=LABSMEM
wanted['spawns']=SPAWNS
wanted['resv']=ns['QUERIES'] and dict(ns['QUERIES'])['resv']
wanted['haulers']=HAULERS

log=[]
def run(name, expr):
    print(f'=== Q {name} ===', flush=True)
    try:
        res=qmod.q(expr, timeout=35)
    except TypeError:
        res=qmod.q(expr)
    except Exception as e:
        res={'error':repr(e)}
    (OUT/f'q_{name}.json').write_text(json.dumps(res, indent=2, default=str)[:200000])
    s=json.dumps(res, separators=(',',':'), default=str)
    print(s[:5000], flush=True)
    log.append((name,s))
    return res

for name in ('cmd','home','rem','def','remth','uf','soft','w45','w47n7','w47src','roles','sites','labsN','lab2','min2','err','labsMem','spawns','resv','haulers'):
    run(name, wanted[name])

(OUT/'q_run2.txt').write_text('\n'.join(f'=== {n} ===\n{s}' for n,s in log))
print('DONE')
