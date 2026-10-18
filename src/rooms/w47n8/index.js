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
  // 1) miners per source (replace at TTL<60)
  for (let i = 0; i < C.SOURCES.length && !want; i++)
    if (!cs.some(c => c.memory.role === 'w8miner' && (c.memory.si | 0) === i && (c.spawning || c.ticksToLive > 60))) { want = 'w8miner'; mem.si = i; }
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
function layoutRun(room) {
  if (Game.time % 20) return;
  if (room.controller.level >= 2) placeSeal(room); // re-placed if destroyed; nothing in W47N8 code repairs walls
  const rcl = room.controller.level;
  if (!room.find(FIND_MY_SPAWNS).length) return; // pioneers (conquest.js) own the spawn site until it is built
  let placed = 0;
  for (let r = 2; r <= rcl; r++) for (const t in (C.BUILD[r] || {})) for (const [x, y] of C.BUILD[r][t]) {
    if (placed >= 5) return;
    if (room.lookForAt(LOOK_STRUCTURES, x, y).some(s => s.structureType === t)) continue;
    if (room.lookForAt(LOOK_CONSTRUCTION_SITES, x, y).length) continue;
    if (room.createConstructionSite(x, y, t) === OK) placed++;
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
