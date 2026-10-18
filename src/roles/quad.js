// W47N8 2x2 ranged quads (docs/CONQUEST_QUAD.md). INERT unless Memory.ops.cq.armed === true (Misaki's go only).
// Retreat ONLY by Memory.ops.cq.cmd = "retreat" — NO automatic retreat triggers (Misaki 2026-10-18 13:17).
// Commands: cmd hold|go|retreat; quadSpawn true -> first quad; reinforce N -> N extra members (fill short quads first = merge, else new).
// Sources (adapted):
//  Overmind Swarm/Pathing.findSwarmPath: 2x2 clearance matrix (anchor cost = worst of 4 cells), move only when all fatigue 0,
//    regroup before advance, single-file squeeze when no 2x2 path, rotate so healthiest face the enemy.
//  Overmind CombatIntel: tower falloff 600@<=5..150@>=20, maxDamageAtPos (melee r1 + ranged r3 + towers),
//    maxHostileHealingTo (self+adj 12/part + ranged 4/part), RMA 10/4/1 by range vs single 10/part.
//  Overmind CombatTargeting / TooAngel: score = our focused dmg - their max healing; CLAIM(reserver) first, then healers/armed.
//  Overmind Movement.combatMove + wiki kiting: vs ATTACK keep range>=3 (step-back-then-shoot; dumb melee AI never lands),
//    vs ranged/healers close to 3; pick the formation step that minimises predicted damage.
const OFF = [[0,0],[1,0],[0,1],[1,1]];
const RALLY = {room:"W46N8",x:9,y:26}, ROOM = "W47N8", HOME = "W46N8", MIN_Y = 8;
const FORBID = new Set(["W47N9","W48N9","W48N8"]);
// North defence posts: tools/w47n8_access.py — from W47N9/W48N9 the only short entry into W47N8 is the NORTH (cost 50/278).
// South needs a ~430-tile detour via W47N7. Openings x9-24 and x32-38 feed corridors at y2-5.
const POSTS = [{x:26,y:4},{x:8,y:4},{x:12,y:26}];
const BODY = () => [].concat(Array(4).fill(RANGED_ATTACK),Array(9).fill(MOVE),Array(5).fill(HEAL)); // 2300
const M = () => (Memory.ops = Memory.ops || {}, Memory.ops.cq = Memory.ops.cq || {});
const rng = (a,b) => Math.max(Math.abs(a.x-b.x), Math.abs(a.y-b.y));
const act = (c,t) => c.body.filter(p => p.type===t && p.hits>0).length;
const boost = (c,t) => c.body.some(p => p.type===t && p.boost) ? 4 : 1;
const DIRS = [[0,-1],[1,-1],[1,0],[1,1],[0,1],[-1,1],[-1,0],[-1,-1]]; // TOP..TOP_LEFT = 1..8

// ---- combat intel (pure, unit-tested) ----
function towerDmg(r) { return r<=5 ? 600 : r>=20 ? 150 : 600 - 450*(r-5)/15; }
const meleeD = h => act(h,ATTACK)*30*boost(h,ATTACK);
const rangedD = h => act(h,RANGED_ATTACK)*10*boost(h,RANGED_ATTACK);
const healOf = h => act(h,HEAL)*12*boost(h,HEAL);
function dmgAt(p, hostiles, towers) {
  let d = 0;
  for (const h of hostiles) { const r = rng(p,h.pos); if (r<=2) d += meleeD(h); if (r<=4) d += rangedD(h); }
  for (const t of towers||[]) d += towerDmg(rng(p,t.pos));
  return d;
}
function hostileHealTo(h, hostiles) {
  let s = 0;
  for (const o of hostiles) { const r = rng(o.pos,h.pos); if (r<=1) s += healOf(o); else if (r<=3) s += healOf(o)/3; }
  return s;
}
// team: [{pos,ra}]; higher score = better focus
function scoreTarget(h, team, hostiles) {
  const inR = team.filter(m => rng(m.pos,h.pos)<=3).length || 0.5;
  const ours = team.reduce((a,m)=>a+m.ra,0)*10*inR/Math.max(team.length,1);
  const net = ours - hostileHealTo(h, hostiles);
  let s = net*10 - h.hits/100;
  if (act(h,CLAIM)) s += 1e6;
  else if (act(h,HEAL)) s += 3e3;
  if (meleeD(h)+rangedD(h)>0) s += 1e3 + meleeD(h) + rangedD(h)*2;
  if (net<=0) s -= 5e3;
  return s - rng(team[0].pos,h.pos)*50;
}
function useMass(me, hostiles) {
  let mass = 0;
  for (const h of hostiles) { const r = rng(me.pos,h.pos); mass += r<=1?10:r===2?4:r===3?1:0; }
  return mass > 10;
}
function anchorCost(x,y,terrain,extra) {
  let worst = 0;
  for (const [dx,dy] of OFF) {
    const cx=x+dx, cy=y+dy;
    if (cx<1||cy<1||cx>48||cy>48) return 255;
    const e = extra?extra(cx,cy):undefined, t = terrain(cx,cy);
    const c = e!==undefined ? e : t==="wall"?255 : t==="swamp"?10 : 2;
    if (c>=255) return 255; worst = Math.max(worst,c);
  }
  return worst;
}
function formedAnchor(pos) {
  const a = pos[0]; if (!a) return null;
  for (let k=1;k<4;k++){ const p=pos[k]; if(!p||p.roomName!==a.roomName||p.x!==a.x+OFF[k][0]||p.y!==a.y+OFF[k][1]) return null; }
  return {x:a.x,y:a.y,roomName:a.roomName};
}
// combat step for formed quad: score stay+8 dirs. Avoid melee range (<3), keep focus<=3, minimise predicted dmg.
// valid(x,y)->anchor walkable. Returns 0 (stay) or dir 1..8.
function combatStep(anc, hostiles, towers, focus, valid) {
  let best=0, bestS=-1e12;
  for (let d=0; d<=8; d++) {
    const dx = d?DIRS[d-1][0]:0, dy = d?DIRS[d-1][1]:0;
    const ax = anc.x+dx, ay = anc.y+dy;
    if (d && !valid(ax,ay)) continue;
    let dmg=0, minMelee=99, nearFocus=99;
    for (const [ox,oy] of OFF) {
      const p = {x:ax+ox,y:ay+oy};
      dmg += dmgAt(p, hostiles, towers);
      for (const h of hostiles) if (act(h,ATTACK)) minMelee = Math.min(minMelee, rng(p,h.pos));
      if (focus) nearFocus = Math.min(nearFocus, rng(p,focus.pos));
    }
    // maximise min range to melee (want >=3), then minimise dmg, then keep focus in range 3
    let s = Math.min(minMelee, 3) * 1e6 - dmg;
    if (focus) {
      if (nearFocus<=3) s += 5e3;
      else s -= (nearFocus-3)*800;
    }
    if (s > bestS) { bestS=s; best=d; }
  }
  return best;
}
// heal: most-hurt in range 1, else rangedHeal range 3; pre-heal self when hostiles within 5
function healPick(me, team) {
  const hurt = team.filter(m => m.hits < m.hitsMax).sort((a,b)=>a.hits/a.hitsMax - b.hits/b.hitsMax);
  const r1 = hurt.find(m => rng(me.pos,m.pos)<=1); if (r1) return [r1,"heal"];
  const r3 = hurt.find(m => rng(me.pos,m.pos)<=3); if (r3) return [r3,"rangedHeal"];
  return null;
}
// rotate: assign each member a cell so the healthiest occupy the side facing the threat (Overmind rotate)
function rotateAssign(anc, members, threat) {
  // members sorted by hits DESC; cells sorted by distance to threat ASC (front) / DESC (back)
  const cells = OFF.map(([dx,dy],i)=>({i,x:anc.x+dx,y:anc.y+dy,d:threat?rng({x:anc.x+dx,y:anc.y+dy},threat.pos):0}));
  cells.sort((a,b)=>b.d-a.d); // back first (safer) for the hurt ones
  const byHits = members.slice().sort((a,b)=>a.hits-b.hits); // hurt first -> back
  const map = {};
  for (let k=0;k<byHits.length;k++) map[byHits[k].name] = cells[k] ? cells[k].i : k;
  return map; // name -> cell idx
}

// ---- grouping ----
function allQuads() { return _.filter(Game.creeps, c => c.memory.role==="cqquad"); }
function groupByQid(creeps) {
  const g = {}; for (const c of creeps) { const id = c.memory.qid|0; (g[id]=g[id]||[]).push(c); }
  for (const id of Object.keys(g)) g[id].sort((a,b)=>(a.memory.qi|0)-(b.memory.qi|0));
  return g;
}
function ensureIds(creeps) {
  // assign qid/qi: fill incomplete quads (size<4) first, else next free qid
  const g = groupByQid(creeps);
  for (const c of creeps) if (c.memory.qid===undefined || c.memory.qi===undefined) {
    let placed = false;
    for (const id of Object.keys(g).map(Number).sort((a,b)=>a-b)) {
      if (g[id].length>=4) continue;
      const used = new Set(g[id].map(m=>m.memory.qi));
      const qi = [0,1,2,3].find(i=>!used.has(i));
      c.memory.qid = id; c.memory.qi = qi; g[id].push(c); placed = true; break;
    }
    if (!placed) {
      const next = Object.keys(g).length ? Math.max(...Object.keys(g).map(Number))+1 : 0;
      c.memory.qid = next; c.memory.qi = 0; g[next] = [c];
    }
  }
  return groupByQid(creeps);
}

// ---- pathfinding ----
function quadMatrix(rn) {
  const room = Game.rooms[rn], T = Game.map.getRoomTerrain(rn), m = new PathFinder.CostMatrix();
  if (FORBID.has(rn)) { for (let x=0;x<50;x++) for (let y=0;y<50;y++) m.set(x,y,255); return m; }
  const blk={}, road={};
  if (room) for (const s of room.find(FIND_STRUCTURES)) {
    if (s.structureType===STRUCTURE_ROAD) road[s.pos.x*50+s.pos.y]=1;
    else if (s.structureType!==STRUCTURE_CONTAINER && !(s.structureType===STRUCTURE_RAMPART && s.my)) blk[s.pos.x*50+s.pos.y]=1;
  }
  const terr = (x,y)=>{ const v=T.get(x,y); return v&TERRAIN_MASK_WALL?"wall":v&TERRAIN_MASK_SWAMP?"swamp":"plain"; };
  const extra = (x,y)=> blk[x*50+y]?255 : (rn===ROOM && y<MIN_Y && !(y<=6 && (x<=12||(x>=22&&x<=32))))?255 : road[x*50+y]?1 : undefined;
  // allow north corridor (y<=6 at posts) so the defence posts at y=4 are reachable; still block y=0-1 except exits
  for (let x=0;x<50;x++) for (let y=0;y<50;y++) m.set(x,y,anchorCost(x,y,terr,extra));
  return m;
}
function goalFor(cmd, qid, focus) {
  if (cmd==="go") {
    if (focus) return {pos:focus.pos, range:3};
    const post = POSTS[qid % POSTS.length];
    return {pos:new RoomPosition(post.x, post.y, ROOM), range:1};
  }
  return {pos:new RoomPosition(RALLY.x+(qid%2)*3, RALLY.y+Math.floor(qid/2)*3, RALLY.room), range:1};
}

// ---- per-quad decide (once per tick) ----
function decide(qid, team) {
  const P = M(), Qs = P.quads = P.quads || {}, Q = Qs[qid] = Qs[qid] || {};
  if (Q.t === Game.time) return Q; Q.t = Game.time;
  const cmd = P.cmd || "hold", lead = team[0];
  const hostiles = lead.room.find(FIND_HOSTILE_CREEPS).filter(h => h.owner && h.owner.username!=="Source Keeper");
  const towers = lead.room.find(FIND_HOSTILE_STRUCTURES).filter(s => s.structureType===STRUCTURE_TOWER);
  const owner = P.owner || "BustJetter";
  const targets = hostiles.filter(h => h.owner.username===owner || meleeD(h)+rangedD(h)>0);
  const snap = team.map(c=>({pos:c.pos, ra:act(c,RANGED_ATTACK)}));
  let f = null;
  if (cmd==="go" && targets.length) {
    f = _.max(targets, h => scoreTarget(h, snap, hostiles));
    if (f===-Infinity) f = null;
  }
  Q.focus = f ? f.id : undefined;
  if (team.length>=4) Q.assembled = 1;
  // movement
  const goal = goalFor(cmd, qid, f);
  const pos = {}; for (const c of team) pos[c.memory.qi] = c.pos;
  const anc = team.length===4 ? formedAnchor(pos) : null;
  Q.moves = {}; Q.mode = "wait"; Q.rot = null;
  if (team.length<4 && cmd!=="retreat") { Q.mode="assemble"; return Q; }
  if (team.some(c => c.fatigue>0)) { Q.mode="fatigue"; return Q; }

  // in combat range under "go": formation combat step (kite) instead of pathfinder
  if (cmd==="go" && anc && (f || hostiles.some(h=>rng(anc,h.pos)<=5))) {
    const T = Game.map.getRoomTerrain(anc.roomName);
    const terr=(x,y)=>{const v=T.get(x,y);return v&TERRAIN_MASK_WALL?"wall":v&TERRAIN_MASK_SWAMP?"swamp":"plain";};
    const valid = (x,y)=>anchorCost(x,y,terr)<255 && !(anc.roomName===ROOM && y<1);
    const d = combatStep(anc, hostiles, towers, f, valid);
    if (d) for (const c of team) Q.moves[c.name]=d;
    Q.mode = d ? "combat" : "holdFire";
    Q.rot = rotateAssign(anc, team, f || hostiles[0]);
    return Q;
  }

  if (anc) {
    if (anc.roomName===goal.pos.roomName && rng(anc,goal.pos)<=goal.range) { Q.mode="there"; return Q; }
    const r = PathFinder.search(new RoomPosition(anc.x,anc.y,anc.roomName), {pos:goal.pos,range:goal.range},
      {maxRooms:3, maxOps:4000, roomCallback:quadMatrix, plainCost:2, swampCost:10});
    if (!r.incomplete && r.path.length && r.path[0].roomName===anc.roomName) {
      const d = new RoomPosition(anc.x,anc.y,anc.roomName).getDirectionTo(r.path[0]);
      for (const c of team) Q.moves[c.name]=d; Q.mode="advance"; return Q;
    }
    Q.mode="squeeze";
  } else {
    const T = Game.map.getRoomTerrain(lead.pos.roomName);
    const terr=(x,y)=>{const v=T.get(x,y);return v&TERRAIN_MASK_WALL?"wall":v&TERRAIN_MASK_SWAMP?"swamp":"plain";};
    const allHere = team.every(c=>c.pos.roomName===lead.pos.roomName);
    if (allHere && anchorCost(lead.pos.x,lead.pos.y,terr)<255) {
      Q.mode="regroup"; Q.anchor={x:lead.pos.x,y:lead.pos.y,room:lead.pos.roomName}; return Q;
    }
    Q.mode="squeeze";
  }
  Q.goal={x:goal.pos.x,y:goal.pos.y,room:goal.pos.roomName,range:goal.range};
  return Q;
}

function fight(c, team, Q) {
  const hostiles = c.room.find(FIND_HOSTILE_CREEPS).filter(h => h.owner && h.owner.username!=="Source Keeper");
  const focus = Q.focus && Game.getObjectById(Q.focus);
  if (useMass(c, hostiles)) c.rangedMassAttack();
  else if (focus && c.pos.inRangeTo(focus,3)) c.rangedAttack(focus);
  else {
    const inR = hostiles.filter(h=>c.pos.inRangeTo(h,3));
    if (inR.length) {
      const snap = team.map(m=>({pos:m.pos,ra:act(m,RANGED_ATTACK)}));
      c.rangedAttack(_.max(inR, h=>scoreTarget(h,snap,hostiles)));
    }
  }
  // rotate cells: if assigned a different cell and formed, step toward it (heal-facing)
  if (Q.rot && Q.rot[c.name]!==undefined && Q.mode==="holdFire") {
    // stay put for fire; rotation applied during regroup/advance next opportunity
  }
  const h = healPick(c, team);
  if (h) c[h[1]](h[0]);
  else if (hostiles.some(x=>c.pos.inRangeTo(x,5))) c.heal(c);
}

function run(c) {
  const P = M(), creeps = allQuads(), groups = ensureIds(creeps);
  const qid = c.memory.qid|0, team = groups[qid] || [c];
  const Q = decide(qid, team);
  fight(c, team, Q);
  const k = c.memory.qi|0;
  if (Q.mode==="assemble") {
    const [dx,dy]=OFF[k]||[0,0];
    return c.moveTo(new RoomPosition(RALLY.x+dx+(qid%2)*3, RALLY.y+dy+Math.floor(qid/2)*3, RALLY.room), {reusePath:10});
  }
  if (Q.mode==="advance"||Q.mode==="combat") return Q.moves[c.name] ? c.move(Q.moves[c.name]) : undefined;
  if (Q.mode==="regroup" && Q.anchor) {
    // prefer rotated cell if we have a threat assignment
    const cell = (Q.rot && Q.rot[c.name]!==undefined) ? Q.rot[c.name] : k;
    const [dx,dy]=OFF[cell];
    return c.moveTo(new RoomPosition(Q.anchor.x+dx,Q.anchor.y+dy,Q.anchor.room),{reusePath:0});
  }
  if (Q.mode==="squeeze" && Q.goal) {
    const ahead = team.filter(m=>(m.memory.qi|0)<k).pop();
    if (!ahead) return c.moveTo(new RoomPosition(Q.goal.x,Q.goal.y,Q.goal.room),{range:Q.goal.range,reusePath:5,costCallback:matrixLite});
    if (!c.pos.isNearTo(ahead)) return c.moveTo(ahead,{reusePath:0,costCallback:matrixLite});
  }
}
function matrixLite(rn,m) {
  if (FORBID.has(rn)) for (let x=0;x<50;x++) for (let y=0;y<50;y++) m.set(x,y,255);
  if (rn===ROOM) for (let x=0;x<50;x++) for (let y=0;y<MIN_Y;y++) if (!(y<=6&&(x<=12||(x>=22&&x<=32)))) m.set(x,y,255);
  return m;
}

// spawn: armed + (quadSpawn or reinforce>0); fill short quads first; never during retreat
function wantSpawn(room) {
  const P = Memory.ops && Memory.ops.cq; if (!P || P.armed!==true) return null;
  if ((P.cmd||"hold")==="retreat") return null;
  if (!room.storage || room.storage.store[RESOURCE_ENERGY] < (P.floor||8000)) return null;
  const creeps = allQuads(), n = creeps.length;
  const want = (P.quadSpawn?4:0) + (P.reinforce|0);
  // once first 4 out, clear the one-shot flag (reinforce stays as a count of extras wanted)
  if (P.quadSpawn && n>=4 && !P.quadRespawn) P.quadSpawn = false;
  if (n < want) return {role:"cqquad", body:BODY(), mem:{role:"cqquad", home:HOME, born:Game.time}};
  // replacement during go
  if (P.quadRespawn && (P.cmd||"hold")==="go" && n < want) return {role:"cqquad", body:BODY(), mem:{role:"cqquad", home:HOME, born:Game.time}};
  return null;
}

module.exports = {
  run, wantSpawn, anchorCost, formedAnchor, healPick, combatStep, scoreTarget, towerDmg, dmgAt, hostileHealTo, useMass, rotateAssign,
  BODY, OFF, RALLY, POSTS, ROOM, FORBID, MIN_Y,
};
