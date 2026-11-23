(()=>{
  const rem=(Memory.ops&&Memory.ops.rem)||{};
  const p=n=>{const x=rem[n]||{}; return {st:x.st||x.state,why:x.why,inc:x.inc,core:!!x.core,def:x.def,since:x.since,evac:x.evac};};
  const names=Object.keys(Game.creeps).filter(n=>/def|guard|rdef/i.test(n)||((Game.creeps[n].memory||{}).role||'').match(/def|guard/));
  const defs={};
  const C={move:50,work:100,attack:80,ranged_attack:150,heal:250,tough:10,claim:600,carry:50};
  for(const n of names){
    const cr=Game.creeps[n];
    let cost=0; const parts={};
    for(const b of cr.body){ cost+=C[b.type]||0; parts[b.type]=(parts[b.type]||0)+1; }
    defs[n]={rm:cr.pos.roomName,x:cr.pos.x,y:cr.pos.y,sp:!!cr.spawning,hits:cr.hits,hitsMax:cr.hitsMax,ttl:cr.ticksToLive||0,role:cr.memory&&cr.memory.role,parts:cr.body.length,partMap:parts,cost,boost:cr.body.some(b=>b.boost)};
  }
  const spawns={};
  for(const n in Game.spawns){
    const s=Game.spawns[n];
    spawns[n]={rm:s.pos.roomName,sp:s.spawning&&{name:s.spawning.name,need:s.spawning.needTime,rem:s.spawning.remainingTime}};
  }
  const inv={};
  for(const n of ['W45N7','W45N8','W47N7','W46N8','W47N8']){
    const rm=Game.rooms[n];
    if(!rm){inv[n]={vis:false}; continue;}
    const h=rm.find(FIND_HOSTILE_CREEPS).map(c=>({n:c.name,x:c.pos.x,y:c.pos.y,hits:c.hits,ttl:c.ticksToLive,body:c.body.map(p=>p.type[0]).join('')}));
    inv[n]={vis:true,hc:h.length,h,res:rm.controller&&rm.controller.reservation&&rm.controller.reservation.ticksToEnd};
  }
  return {t:Game.time,rem:{W45N7:p('W45N7'),W45N8:p('W45N8'),W47N7:p('W47N7')},defs,spawns,inv};
})()