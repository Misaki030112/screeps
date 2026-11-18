#!/usr/bin/env python3
import sys, json
from pathlib import Path
sys.path.insert(0,'/workspace/screeps/tools')
import q as qmod
OUT = Path('/workspace/screeps/state/_patrol_2026-11-18_2017')
Qs = [
('later2', """(()=>{const H=Game.rooms.W46N8,W=Game.rooms.W47N8,d=(Memory.ops&&Memory.ops.w8day)||{},uf=Memory.ops&&Memory.ops.upgFeed||{};
const ups=[],fills=[];
for(const cr of Object.values(Game.creeps)){
  const r=cr.memory&&cr.memory.role;
  const o={n:cr.name,r,rm:cr.pos.roomName,x:cr.pos.x,y:cr.pos.y,ttl:cr.ticksToLive||0,e:cr.store&&cr.store.energy||0,sp:!!cr.spawning};
  if(r==='upgrader'||r==='w8upgrader') ups.push(o);
  if(r==='w8filler') fills.push(o);
}
return {t:Game.time,b:Game.cpu.bucket,c:+Game.cpu.getUsed().toFixed(2),
cmt:(Memory.stats&&Memory.stats.commit)||Memory.commit||null,
hs:H&&H.storage&&H.storage.store.energy,ws:W&&W.storage&&W.storage.store.energy,
nUp:uf.n,why:uf.why,work:uf.work,keep:d.upgKeep,bWhy:d.bankWhy,thS:d.threatSoft,sC2:d.softCap2,
sealPark:d.sealPark,storE:d.storE,phase:d.phase,ups,fills};})()"""),
('hub2', """(()=>{const W=Game.rooms.W47N8,tiles={}; if(!W) return {t:Game.time,vis:false};
for(const [x,y] of [[33,33],[34,32],[35,31],[34,33],[33,34],[34,30],[32,32],[33,31],[32,29],[32,35]]){
  const L=W.lookAt(x,y);
  tiles[x+','+y]={c:L.filter(z=>z.creep).map(z=>z.creep.name+'/'+(z.creep.memory&&z.creep.memory.role))};
}
return {t:Game.time,vis:true,tiles};})()"""),
]
for name, expr in Qs:
    print('SIZE', name, len(expr), flush=True)
    try:
        r = qmod.q(expr, timeout=35)
        (OUT/f'q_{name}.json').write_text(json.dumps(r, indent=2)+'\n')
        print('OK', name, json.dumps(r, ensure_ascii=False)[:2000], flush=True)
    except Exception as e:
        print('FAIL', name, type(e).__name__, e, flush=True)
        (OUT/f'q_{name}.err').write_text(repr(e)+'\n')
print('DONE')
