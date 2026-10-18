// W47N8 room module: spawn manager + layout + tower. Runs ONLY for W47N8; home W46N8 code never sees it.
// Never activates safe mode (Misaki does it manually).
const C = require('./config');
const rep = (n, p) => Array(n).fill(p);
function mine() { return _.filter(Game.creeps, c => c.memory.home === C.ROOM); }
function bodyFor(role, e) {
  if (role === 'w8filler') { const n = Math.max(2, Math.min(8, Math.floor(e / 150))); return rep(n, CARRY).concat(rep(Math.ceil(n / 2), MOVE)); }
  if (role === 'w8rminer') { // 20:22: old formula priced 4W1C3M=600 at cap 550, so it never spawned; now the biggest that fits, trimming MOVE first
    for (let w = 5; w >= 2; w--) for (let m = Math.ceil((w + 1) / 2); m >= Math.ceil((w + 1) / 3); m--)
      if (100 * w + 50 + 50 * m <= e) return rep(w, WORK).concat([CARRY], rep(m, MOVE));
    return [WORK, WORK, CARRY, MOVE];
  }
  // 02:35: W47N7 routes are road almost end to end (18,17->ctl 45 tiles/43 road, 31,34->59/56), so 2C:1M keeps full speed loaded:
  // 10C5M=750 carries 500 vs 8C8M=800 carrying 400 at cap 800
  if (role === 'w8rhauler') { if (e < 450) { const n = Math.max(2, Math.floor(e / 100)); return rep(n, CARRY).concat(rep(n, MOVE)); }
    const k = Math.min(8, Math.floor(e / 150)); return rep(2 * k, CARRY).concat(rep(k, MOVE)); }
  if (role === 'w8miner') { const w = Math.max(2, Math.min(5, Math.floor((e - 50) / 100))); return rep(w, WORK).concat([MOVE]); }
  if (role === 'w8hauler') { const n = Math.max(2, Math.min(10, Math.floor(e / 100))); return rep(n, CARRY).concat(rep(n, MOVE)); }
  // 18:58: upgraders sit beside the ctl container 13,26 (1750/2000 full, spawn idle at 550/550): WORK-heavy 4W1C2M instead of 2W2C2M
  if (role === 'w8upgrader' && e >= 550) { const w = Math.min(10, Math.floor((e - 150) / 100)); return rep(w, WORK).concat([CARRY, MOVE, MOVE]); }
  const n = Math.max(1, Math.min(6, Math.floor(e / 200))); return rep(n, WORK).concat(rep(n, CARRY), rep(n, MOVE)); // upgrader/builder
}
// energy lying on the ground or in source containers (ctl container excluded)
const looseE = room => _.sum(room.find(FIND_DROPPED_RESOURCES, { filter: r => r.resourceType === RESOURCE_ENERGY }), r => r.amount)
  + _.sum(room.find(FIND_STRUCTURES, { filter: s => s.structureType === STRUCTURE_CONTAINER && !(s.pos.x === C.CTL_CONT[0] && s.pos.y === C.CTL_CONT[1]) && !(s.pos.x === C.HUB_CONT[0] && s.pos.y === C.HUB_CONT[1]) }), s => s.store[RESOURCE_ENERGY]);
function spawnRun(spawn) {
  if (spawn.spawning) return;
  const room = spawn.room, cs = mine(), n = r => cs.filter(c => c.memory.role === r).length;
  const cap = room.energyCapacityAvailable, avail = room.energyAvailable;
  const sites = room.find(FIND_MY_CONSTRUCTION_SITES).length;
  let want = null, mem = {};
  // 1) miners per source: keep >=5 WORK (10 e/t) on each source. Replace at TTL<60; and since the first w8miners were 2 WORK
  // (cap 300) and would run at 40% for ~1000 ticks, add a bigger one once cap allows (17:25), counting any cqminer still there.
  for (let i = 0; i < C.SOURCES.length && !want; i++) {
    // 20:20: replace at TTL < walk time + spawn time (learned per source by w8miner on arrival). TTL<60 left source 11,44 unmined
    // ~150 ticks (5W1M walks 5-25 ticks/tile; spawn->11,43 took ~170 ticks), regen wasted at 3000/3000.
    const S = C.SOURCES[i], lead = Math.max(60, ((Memory.ops && Memory.ops.w8lead && Memory.ops.w8lead[i]) || 5 * spawn.pos.getRangeTo(S.stand[0], S.stand[1])) + 3 * 6 + 10);
    const live = cs.filter(c => c.memory.role === 'w8miner' && (c.memory.si | 0) === i && (c.spawning || c.ticksToLive > lead));
    const cq = room.find(FIND_MY_CREEPS, { filter: c => c.memory.role === 'cqminer' && c.ticksToLive > 60 && c.pos.inRangeTo(S.src[0], S.src[1], 1) });
    const works = _.sum(live.concat(cq), c => c.getActiveBodyparts(WORK) || _.filter(c.body, p => p.type === WORK).length);
    const add = bodyFor('w8miner', cap).length - 1;
    if (!live.length || (works < 5 && live.length < 2 && add > (live[0] ? live[0].getActiveBodyparts(WORK) : 0))) { want = 'w8miner'; mem.si = i; }
  }
  // 2) haulers 2, 3) upgraders 2 (3 when no sites), 4) builders while sites
  if (!want && n('w8hauler') < 2) want = 'w8hauler';
  else if (!want && n('w8upgrader') < (sites ? 2 : 3)) want = 'w8upgrader';
  else if (!want && sites && n('w8builder') < (sites >= 3 ? 4 : 2)) want = 'w8builder'; // 17:05: Spawn2 sat idle at 300/300 with 5 ext sites
  // 5) surplus (17:52: 1.8k energy lying on the ground/in source containers, spenders only ~7 WORK of 20 e/t income):
  // +1 hauler above 1200 loose (max 3), +1 upgrader per 600 loose above 600 (max 6)
  if (!want) {
    const loose = looseE(room);
    // 03:20 hub container energy counts toward upgraders once no sites near the hub use it (2000 full + ctl 652, Spawn2 idle 718/800,
    // only 2 upgraders = 12 WORK for ~40 e/t local+W47N7 income; RCL3 ~14.6 e/t)
    const hubC = room.lookForAt(LOOK_STRUCTURES, C.HUB_CONT[0], C.HUB_CONT[1]).find(s => s.structureType === STRUCTURE_CONTAINER);
    const hubIdle = hubC && !room.find(FIND_MY_CONSTRUCTION_SITES, { filter: s => s.structureType !== STRUCTURE_WALL && s.pos.inRangeTo(C.HUB_CONT[0], C.HUB_CONT[1], 5) }).length ? hubC.store[RESOURCE_ENERGY] : 0;
    if (loose > 1200 && n('w8hauler') < (sites && loose > 3500 ? 7 : loose > (sites ? 2500 : 3000) ? 6 : loose > 2500 ? 5 : loose > 2000 ? 4 : 3)) want = 'w8hauler'; // 18:20: 4th when >2k piles (far south source)
    // 23:45: 7th above 3.5k while sites exist: with 6 haulers loose still rose 3.2k -> 3.96k in 146 ticks (~5 e/t), 11,43 full 2000 + 126 dropped,
    // Spawn2 idle 600/600, 4 builders mostly queue_blocked, builds fell to ~5.5 e/t
    // 23:20: 6th already above 2.5k while sites exist: loose 3048 -> 2736 by t83726755 (just under 3k, so Spawn2 sat idle 600/600) while 4 builders
    // were queue_blocked ~100/113 samples and 5 upgraders ~75/69-tick windows (creep_motion 0.25h); builds ~7.5 e/t + RCL3 ~6 e/t
    // 23:10: 6th above 3k: loose 2763 -> 3048 in ~95t (11,43 at 1690) while hub builders sat queue_blocked ~70% of ticks and the ctl cont ran down to 137 (RCL3 ~4 e/t)
    // 21:10: 5th above 2.5k: source conts rose 894/820 -> 1194/1320 in 161t while the ctl cont fell 1984 -> 1386 (haul-bound, not WORK-bound)
    else if (n('w8upgrader') < Math.min(6, (sites ? 2 : 3) + Math.floor(Math.max(0, loose + hubIdle - 600) / 600))
      && _.sum(cs.filter(c => c.memory.role === 'w8upgrader'), c => _.filter(c.body, p => p.type === WORK).length) < 24) want = 'w8upgrader'; // 21:20: 16->24 WORK; income ~20 local + ~13 W47N7 remote, ctl cont 1984/2000 full with 4x4W upgraders (WORK-bound)
  }
  // 5b) strip fillers (v3b): one per strip with >=4 built extensions, once the hub storage exists
  if (!want && room.storage && room.storage.store[RESOURCE_ENERGY] > 1000) {
    for (let i = 0; i < L.STRIPS.length && !want; i++) {
      const built = L.STRIPS[i].ext.filter(([x, y]) => room.lookForAt(LOOK_STRUCTURES, x, y).some(s => s.structureType === STRUCTURE_EXTENSION)).length;
      if (built >= 4 && !cs.some(c => c.memory.role === 'w8filler' && c.memory.si === i && (c.spawning || c.ticksToLive > 50))) { want = 'w8filler'; mem.si = i; }
    }
  }
  // 6) wall builder from surplus (19:18): 1 builder while a seal wall is below target and spawn is full
  // 19:31: 2 while >1500 loose energy piles (2.8k at 19:30 with the ctl container full and upgraders at the WORK cap)
  if (!want && room.energyAvailable === cap && n('w8builder') < (looseE(room) > 1500 ? 2 : 1)) {
    const tgt = C.WALL_TARGET[room.controller.level] || 0;
    if (room.find(FIND_STRUCTURES, { filter: s => s.structureType === STRUCTURE_WALL && s.hits < tgt && C.SEAL.some(([x, y]) => s.pos.x === x && s.pos.y === y) }).length) want = 'w8builder';
  }
  // 7) W47N7 remote (after all local roles): only while home's reserve7 holds the reservation for us
  const r7 = Memory.ops && Memory.ops.r7, ours7 = r7 && r7.by === 'Misaki' && (r7.endTime || 0) > Game.time + 200;
  if (!want && ours7) {
    for (let i = 0; i < C.REMOTE.sources.length && !want; i++)
      if (!cs.some(c => c.memory.role === 'w8rminer' && (c.memory.si | 0) === i && (c.spawning || c.ticksToLive > 100))) { want = 'w8rminer'; mem.si = i; }
    // 02:16: 3 rhaulers fell behind 2 reserved sources (~20 e/t): W47N7 had 31,34 full 2000 + 5871 dropped, 18,17 at 1138.
    // +1 per 1500 loose above 1500 in W47N7 (max 6), same idea as the local hauler surplus rule
    // 03:30: count container energy too — full 31,34 (2000) with only ~2k drop looked "fine" (want 3) while south kept overflowing
    const R7 = Game.rooms[C.REMOTE.room];
    const lo7 = R7 ? looseE(R7) + _.sum(R7.find(FIND_STRUCTURES, { filter: s => s.structureType === STRUCTURE_CONTAINER }), s => s.store[E] || 0) : 0;
    // 02:35: max 6 -> 8: with 5 alive the pile kept growing (6175 -> 6229 dropped + conts 1978/2000 by t83729299); round trips ~90-120 ticks
    // at 400 carry = ~3.6 e/t each, below the 2 sources' ~20 e/t plus decay
    if (!want && n('w8rhauler') < Math.min(8, 3 + Math.floor(Math.max(0, lo7 - 1500) / 1500))) want = 'w8rhauler';
  }
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
const L = require('./layout'); // v3b (approved 20:11): ORDER per type nearest-core first; STRIPS with filler stand
const PRIO = ['spawn', 'extension', 'tower', 'container', 'storage', 'link', 'terminal', 'extractor', 'lab', 'factory', 'powerSpawn', 'nuker', 'observer', 'road', 'rampart'];
const isTemp = s => L.TEMP_EXT.some(([x, y]) => s.pos.x === x && s.pos.y === y);
const LINK_ROADS = [[16, 33], [17, 33], [18, 33], [19, 33], [20, 33], [21, 33], [22, 34], [23, 35]];
function layoutRun(room) {
  if (Game.time % 20) return;
  if (room.controller.level >= 2) placeSeal(room);
  if (!room.find(FIND_MY_SPAWNS).length) return;
  const rcl = room.controller.level, ok = Memory.ops && Memory.ops.w8layout === 'approved';
  if (rcl >= 3) { const [hx, hy] = C.HUB_CONT; if (!room.lookForAt(LOOK_STRUCTURES, hx, hy).some(s => s.structureType === STRUCTURE_CONTAINER) && !room.lookForAt(LOOK_CONSTRUCTION_SITES, hx, hy).length) room.createConstructionSite(hx, hy, STRUCTURE_CONTAINER); }
  // RCL8: the 5 temporary RCL2 extensions near Spawn2 give their slots to the last 5 strip extensions
  if (ok && rcl === 8) {
    const ex = room.find(FIND_MY_STRUCTURES, { filter: s => s.structureType === STRUCTURE_EXTENSION });
    const temp = ex.filter(isTemp);
    if (temp.length && ex.length - temp.length >= 55) temp[0].destroy();
  }
  let sites = room.find(FIND_MY_CONSTRUCTION_SITES).length; if (sites >= 6) return;
  // 03:05 west<->hub link road (missing from v3b plan): loaded 10C5M rhaulers sat 7-10 ticks on unroaded swamp 22,34 (fatigue 70)
  // between road 15,33 and strip road 24,35; queued ahead of the plan roads since every hub trip crosses it
  const O = ok ? Object.assign({}, L.ORDER, { road: LINK_ROADS.concat(L.ORDER.road) }) : { extension: L.TEMP_EXT, container: L.ORDER.container };
  for (const t of PRIO) {
    if (t === 'road' && rcl < 3) continue;
    if (t === 'rampart' && rcl < 4) continue;
    for (const [x, y] of (O[t] || [])) {
      if (sites >= 6) return;
      if (t === 'road' && sites > 2) return; // roads only when little else is queued
      if (room.lookForAt(LOOK_STRUCTURES, x, y).some(s => s.structureType === t)) continue;
      if (room.lookForAt(LOOK_CONSTRUCTION_SITES, x, y).length) continue;
      const r = room.createConstructionSite(x, y, t);
      if (r === OK) sites++; else if (r === ERR_RCL_NOT_ENOUGH) break; // next type
    }
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
