// W47N8 room module: spawn manager + layout + tower. Runs ONLY for W47N8; home W46N8 code never sees it.
// Never activates safe mode (Misaki does it manually).
const C = require('./config');
const rep = (n, p) => Array(n).fill(p);
function mine() { return _.filter(Game.creeps, c => c.memory.home === C.ROOM); }
function bodyFor(role, e) {
  if (role === 'w8miner') { const w = Math.max(2, Math.min(5, Math.floor((e - 50) / 100))); return rep(w, WORK).concat([MOVE]); }
  if (role === 'w8hauler') { const n = Math.max(2, Math.min(10, Math.floor(e / 100))); return rep(n, CARRY).concat(rep(n, MOVE)); }
  const n = Math.max(1, Math.min(6, Math.floor(e / 200))); return rep(n, WORK).concat(rep(n, CARRY), rep(n, MOVE)); // upgrader/builder
}
function spawnRun(spawn) {
  if (spawn.spawning) return;
  const room = spawn.room, cs = mine(), n = r => cs.filter(c => c.memory.role === r).length;
  const cap = room.energyCapacityAvailable, avail = room.energyAvailable;
  const sites = room.find(FIND_MY_CONSTRUCTION_SITES).length;
  let want = null, mem = {};
  // 1) miners per source: keep >=5 WORK (10 e/t) on each source. Replace at TTL<60; and since the first w8miners were 2 WORK
  // (cap 300) and would run at 40% for ~1000 ticks, add a bigger one once cap allows (17:25), counting any cqminer still there.
  for (let i = 0; i < C.SOURCES.length && !want; i++) {
    const S = C.SOURCES[i], live = cs.filter(c => c.memory.role === 'w8miner' && (c.memory.si | 0) === i && (c.spawning || c.ticksToLive > 60));
    const cq = room.find(FIND_MY_CREEPS, { filter: c => c.memory.role === 'cqminer' && c.ticksToLive > 60 && c.pos.inRangeTo(S.src[0], S.src[1], 1) });
    const works = _.sum(live.concat(cq), c => c.getActiveBodyparts(WORK) || _.filter(c.body, p => p.type === WORK).length);
    const add = bodyFor('w8miner', cap).length - 1;
    if (!live.length || (works < 5 && live.length < 2 && add > (live[0] ? live[0].getActiveBodyparts(WORK) : 0))) { want = 'w8miner'; mem.si = i; }
  }
  // 2) haulers 2, 3) upgraders 2 (3 when no sites), 4) builders while sites
  if (!want && n('w8hauler') < 2) want = 'w8hauler';
  else if (!want && n('w8upgrader') < (sites ? 2 : 3)) want = 'w8upgrader';
  else if (!want && sites && n('w8builder') < (sites >= 3 ? 4 : 2)) want = 'w8builder'; // 17:05: Spawn2 sat idle at 300/300 with 5 ext sites
  if (!want) return;
  // emergency: nothing alive that refills -> spawn with what we have
  const starving = !n('w8hauler') || !n('w8miner');
  const e = starving ? Math.max(200, avail) : cap;
  const body = bodyFor(want, e), cost = _.sum(body, p => BODYPART_COST[p]);
  if (avail < cost) return;
  spawn.spawnCreep(body, want + Game.time, { memory: Object.assign({ role: want, home: C.ROOM, born: Game.time, v2: 1 }, mem) });
}
function placeSeal(room) {
  for (const [x, y] of C.SEAL) {
    if (room.lookForAt(LOOK_STRUCTURES, x, y).some(s => s.structureType === STRUCTURE_WALL)) continue;
    if (room.lookForAt(LOOK_CONSTRUCTION_SITES, x, y).length) continue;
    room.createConstructionSite(x, y, STRUCTURE_WALL);
  }
}
const L = require('./layout'); // generated plan (tools/w47n8_plan.py), cumulative per RCL
const PRIO = ['spawn', 'extension', 'tower', 'container', 'storage', 'link', 'terminal', 'extractor', 'lab', 'factory', 'powerSpawn', 'nuker', 'observer', 'road', 'rampart'];
function layoutRun(room) {
  if (Game.time % 20) return;
  if (room.controller.level >= 2) placeSeal(room); // re-placed if destroyed; nothing in W47N8 code repairs walls
  if (!room.find(FIND_MY_SPAWNS).length) return;
  // Misaki 17:21 rejected the fde2d58 plan: only the RCL2 set (5 extensions near Spawn2 + ctl container) until a new plan is approved
  const rcl = room.controller.level, B = Object.assign({}, L.BUILD[(Memory.ops && Memory.ops.w8layout === 'approved') ? Math.min(8, rcl) : 2] || {});
  if (!(Memory.ops && Memory.ops.w8layout === 'approved')) delete B.road;
  if (rcl >= 4) B.rampart = L.RAMPARTS_RCL4;
  let sites = room.find(FIND_MY_CONSTRUCTION_SITES).length; if (sites >= 6) return;
  for (const t of PRIO) for (const [x, y] of (B[t] || [])) {
    if (sites >= 6) return;
    if (t === 'road' && sites > 2) return; // roads only when little else is queued
    if (room.lookForAt(LOOK_STRUCTURES, x, y).some(s => s.structureType === t)) continue;
    if (room.lookForAt(LOOK_CONSTRUCTION_SITES, x, y).length && t !== 'rampart') continue;
    if (room.createConstructionSite(x, y, t) === OK) sites++;
  }
}
function towerRun(room) {
  const towers = room.find(FIND_MY_STRUCTURES, { filter: s => s.structureType === STRUCTURE_TOWER });
  if (!towers.length) return;
  const h = room.find(FIND_HOSTILE_CREEPS);
  const claimer = h.find(x => x.body.some(p => p.type === CLAIM && p.hits > 0));
  const hurt = room.find(FIND_MY_CREEPS, { filter: c => c.hits < c.hitsMax })[0];
  for (const t of towers) {
    if (claimer || h.length) t.attack(claimer || t.pos.findClosestByRange(h));
    else if (hurt) t.heal(hurt);
  }
}
// self-sufficient = own spawn + a miner + a hauler alive (conquest.js stops sending cqworkers/cqhaulers)
function selfSufficient() {
  const r = Game.rooms[C.ROOM]; if (!r || !r.find(FIND_MY_SPAWNS).length) return false;
  return mine().some(c => c.memory.role === 'w8miner'); // Spawn2 + its own miner -> home stops cq pioneers/haulers (guard stays)
}
module.exports = { ROOM: C.ROOM, spawnRun, layoutRun, towerRun, selfSufficient, bodyFor };
