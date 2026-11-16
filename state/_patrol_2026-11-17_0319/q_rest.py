#!/usr/bin/env python3
import sys, json
from pathlib import Path
sys.path.insert(0,'/workspace/screeps/tools')
import q as qmod
OUT = Path('/workspace/screeps/state/_patrol_2026-11-17_0319')
ns={}
exec((OUT/'_q_exprs.py').read_text(), ns)
Q=dict(ns['QUERIES'])

# shorter replacements that previously overflowed ~1000
W47N7 = "(()=>{const r=Game.rooms.W47N7;if(!r)return{t:Game.time,vis:false};const res=r.controller&&r.controller.reservation;return{t:Game.time,vis:true,res:res&&res.ticksToEnd,cores:r.find(FIND_HOSTILE_STRUCTURES,{filter:s=>s.structureType==STRUCTURE_INVADER_CORE}).length,host:r.find(FIND_HOSTILE_CREEPS).length,src:r.find(FIND_SOURCES).map(s=>({x:s.pos.x,y:s.pos.y,e:s.energy,c:s.energyCapacity})),cont:r.find(FIND_STRUCTURES,{filter:s=>s.structureType==STRUCTURE_CONTAINER}).map(s=>({x:s.pos.x,y:s.pos.y,e:s.store.energy,hits:s.hits})),mine:r.find(FIND_MY_CREEPS).map(c=>({n:c.name,r:c.memory&&c.memory.role,x:c.pos.x,y:c.pos.y,ttl:c.ticksToLive,e:c.store&&c.store.energy||0}))};})()"
W47SRC = "(()=>{const R=Game.rooms.W47N8;if(!R)return{t:Game.time,vis:false};return{t:Game.time,vis:true,src:R.find(FIND_SOURCES).map(s=>({x:s.pos.x,y:s.pos.y,e:s.energy,c:s.energyCapacity})),links:R.find(FIND_MY_STRUCTURES,{filter:s=>s.structureType==STRUCTURE_LINK}).map(s=>({x:s.pos.x,y:s.pos.y,e:s.store.energy,cd:s.cooldown})),cont:R.find(FIND_STRUCTURES,{filter:s=>s.structureType==STRUCTURE_CONTAINER}).map(s=>({x:s.pos.x,y:s.pos.y,e:s.store.energy,hits:s.hits})),stor:R.storage&&R.storage.store.energy};})()"
W45N8 = "(()=>{const r=Game.rooms.W45N8;if(!r)return{t:Game.time,vis:false};const res=r.controller&&r.controller.reservation;return{t:Game.time,vis:true,res:res&&{u:res.username,tte:res.ticksToEnd},cores:r.find(FIND_HOSTILE_STRUCTURES,{filter:s=>s.structureType==STRUCTURE_INVADER_CORE}).length,host:r.find(FIND_HOSTILE_CREEPS).length,src:r.find(FIND_SOURCES).map(s=>({x:s.pos.x,y:s.pos.y,e:s.energy,c:s.energyCapacity})),mine:r.find(FIND_MY_CREEPS).map(c=>({n:c.name,r:c.memory&&c.memory.role,x:c.pos.x,y:c.pos.y,ttl:c.ticksToLive,e:c.store&&c.store.energy||0}))};})()"
LABSMEM = "(()=>{const o=Memory.ops||{};return{t:Game.time,labs:o.labs||null,labRun:o.labRun||null,labReady:o.labReady||null};})()"
LABSDET = "(()=>{const R=Game.rooms.W46N8;if(!R)return{t:Game.time,vis:false};const labs=R.find(FIND_MY_STRUCTURES,{filter:s=>s.structureType==STRUCTURE_LAB}).map(s=>({x:s.pos.x,y:s.pos.y,cd:s.cooldown,st:s.store}));return{t:Game.time,vis:true,labs};})()"
SPAWNS = "(()=>{return{t:Game.time,spawns:Object.values(Game.spawns).map(s=>({rn:s.room.name,n:s.name,sp:s.spawning?{n:s.spawning.name,rem:s.spawning.remainingTime}:null,e:s.store.energy}))};})()"
HAULERS = "(()=>{const o=[];for(const c of Object.values(Game.creeps)){const r=c.memory&&c.memory.role||'';if(r!=='hauler'&&r!=='queen'&&r!=='w8filler'&&r.indexOf('hauler')<0)continue;o.push({n:c.name,r,rm:c.pos.roomName,x:c.pos.x,y:c.pos.y,ttl:c.ticksToLive||0,e:c.store&&c.store.energy||0,sp:!!c.spawning});}return{t:Game.time,o};})()"
UPS = "(()=>{const o=[];for(const c of Object.values(Game.creeps)){const r=c.memory&&c.memory.role||'';if(r!=='upgrader'&&r!=='w8upgrader'&&r!=='miner'&&r!=='w8miner'&&r!=='w8filler'&&r!=='queen')continue;o.push({n:c.name,r,rm:c.pos.roomName,x:c.pos.x,y:c.pos.y,ttl:c.ticksToLive||0,e:c.store&&c.store.energy||0,sp:!!c.spawning,st:c.memory&&c.memory.st});}return{t:Game.time,o};})()"
BOOST = "(()=>{const o=Memory.ops||{};return{t:Game.time,boost:o.boost||o.boostSkip||null,labs:o.labs||null,w8min:o.w8min||null,kite:o.kite||null};})()"

wanted = {
    'roles': Q['roles'],
    'sites': Q['sites'],
    'labsN': Q['labsN'],
    'lab2': Q['lab2'],
    'min2': Q['min2'],
    'err': Q['err'],
    'resv': Q['resv'],
    'w47src': W47SRC,
    'w47n7': W47N7,
    'w45n8': W45N8,
    'labsMem': LABSMEM,
    'labsDetail': LABSDET,
    'spawns': SPAWNS,
    'haulers': HAULERS,
    'ups': UPS,
    'boost': BOOST,
}
for n,e in wanted.items():
    print(f'LEN {n} {len(e)}', flush=True)
    if len(e) > 980:
        print(f'WARNING {n} may overflow', flush=True)

log=[]
def run(name, expr):
    print(f'=== {name} ===', flush=True)
    try:
        res=qmod.q(expr, timeout=35)
    except TypeError:
        res=qmod.q(expr)
    except Exception as e:
        res={'error':repr(e)}
    (OUT/f'q_{name}.json').write_text(json.dumps(res, indent=2, default=str)[:200000])
    s=json.dumps(res, separators=(',',':'), default=str)
    print(s[:6000], flush=True)
    log.append((name,s))
    return res

for name in ('roles','w47src','w47n7','w45n8','labsMem','lab2','min2','labsN','labsDetail','sites','spawns','err','resv','haulers','ups','boost'):
    run(name, wanted[name])
(OUT/'q_run_rest.txt').write_text('\n'.join(f'=== {n} ===\n{s}' for n,s in log)+'\n')
print('DONE')
