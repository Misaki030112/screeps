// W47N8 room module: spawn manager + layout + tower. Runs ONLY for W47N8; home W46N8 code never sees it.
// Never activates safe mode (Misaki does it manually).
const C = require('./config');
const rep = (n, p) => Array(n).fill(p);
function mine() { return _.filter(Game.creeps, c => c.memory.home === C.ROOM); }
function bodyFor(role, e) {
  // 14:46 kite body: RA+MOVE pairs, plus 1 HEAL(+MOVE) once energy allows (>=1100)
  if (role === 'w8defender') { const h = e >= 1100 ? 1 : 0, k = Math.max(1, Math.min(9, Math.floor((e - 300 * h) / 200)));
    return rep(k, RANGED_ATTACK).concat(rep(k + h, MOVE), rep(h, HEAL)); }
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
const siteRem = room => _.sum(room.find(FIND_MY_CONSTRUCTION_SITES), s => s.progressTotal - s.progress);
function spawnRun(spawn) {
  if (spawn.spawning) return;
  const room = spawn.room, cs = mine(), n = r => cs.filter(c => c.memory.role === r).length;
  const cap = room.energyCapacityAvailable, avail = room.energyAvailable;
  const sites = room.find(FIND_MY_CONSTRUCTION_SITES).length;
  let want = null, mem = {};
  // 0) defender (Misaki 14:09): only when an armed hostile is inside the sealed base (towerRun sets threat8.inBase); max 2
  const th = room.memory && room.memory.threat8;
  // 14:46 (Misaki): also on an invasion move (armed hostiles entering W47N8, or an armed group at the W47N9 border); max 2, stays in W47N8
  if (((th && th.inBase && Game.time - th.t < 5) || TH.invasion()) && n('w8defender') < 2) { want = 'w8defender'; }
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
  // 04:47: base 3 (was 2): with 2 haulers and 0 sites RCL3 fell ~22 -> ~7.5 e/t (t83731005..1169), ctl cont 0-114 while source conts
  // rose to 633/1000; the surplus 3rd only spawned after loose passed 1200, so the ctl ran dry every cycle
  if (!want && n('w8hauler') < 3) want = 'w8hauler';
  // 14:23 threat mode: walls/core ramparts to 50k ahead of upgrading; 1 upgrader keeps the controller safe (2 if downgrade < 10k)
  const thr = TH.on(), wtgt = TH.wallTarget(C.WALL_TARGET[(room.controller || {}).level] || 0);
  const wallsLow = thr && room.find(FIND_STRUCTURES, { filter: s => ((s.structureType === STRUCTURE_WALL && C.SEAL.some(([x, y]) => s.pos.x === x && s.pos.y === y)) || (s.structureType === STRUCTURE_RAMPART && s.my)) && s.hits < wtgt }).length > 0;
  if (!want && wallsLow && n('w8upgrader') < (room.controller.ticksToDowngrade < 10000 ? 2 : 1)) want = 'w8upgrader';
  else if (!want && wallsLow && n('w8builder') < 3) want = 'w8builder';
  else if (!want && !wallsLow && n('w8upgrader') < (sites ? 2 : 3)) want = 'w8upgrader';
  // 10:40: rhaulers sat last in the queue, so with 4 builders + 6 sites on the single Spawn2 all 6 (spawned in one burst at RCL3) aged out
  // together: 0 alive t~83735970-6045 while W47N7 conts hit 2000/2000 + ~1.2k dropped. Keep a floor of 2 ahead of builders/surplus.
  const r7m = Memory.ops && Memory.ops.r7, ours7 = r7m && r7m.by === 'Misaki' && (r7m.endTime || 0) > Game.time + 200;
  const R7 = Game.rooms[C.REMOTE.room], lo7 = R7 ? looseE(R7) : 0;
  // 10:57: floor 2 still left W47N7 at 2000/2000 conts + 2936 dropped (lo7 ~6.9k, ~3 e/t decaying) behind 4 builders; 2 sources ~20 e/t need
  // ~3-4 x 700-carry rhaulers (round trip ~100-120t), so floor 4 while lo7 > 3000
  // 11:12: lo7 kept rising 6.9k -> 7.3k (conts 2000/2000 + 3292 dropped) while 3 builders and 2 upgraders sat queue_blocked (energy-starved,
  // local conts 140/530): remote haul is the income bottleneck, so floor 6 above 5k (each 14C7M rhauler ~6 e/t over a ~110t round trip)
  // 14:05: rminer replacement sat in step 7 behind builders/surplus: W47N7 ran on 1 rminer (one source unmined) while Spawn2 made a 4th
  // w8builder t83738940, and the rhauler floor (lo7 ~5.0k -> 6) would have spawned 2 more rhaulers first. A source is ~10 e/t; mine it first.
  for (let i = 0; ours7 && i < C.REMOTE.sources.length && !want; i++)
    if (!cs.some(c => c.memory.role === 'w8rminer' && (c.memory.si | 0) === i && (c.spawning || c.ticksToLive > 100))) { want = 'w8rminer'; mem.si = i; }
  // 14:55 model-driven (tools/model_w8.py -> Memory.ops.w8model): remote fleet sized by CARRY need = sum 10 x (rt x 1.1 + 4) / 50 over
  // both W47N7 sources (~52 at 14:55) instead of loose-pile thresholds (live 88 CARRY: rhaulers 82% moving/12% blocked, +1.8 e/t upkeep).
  // Floor (ahead of builders): 60% of need; full need + a backlog term (+16 CARRY per 2000 loose above 3000) in step 7.
  const wm = (Memory.ops && Memory.ops.w8model) || {}, rNeed = wm.rcarry || 55;
  const rCarry = (ttl) => cs.filter(c => c.memory.role === 'w8rhauler' && (c.spawning || c.ticksToLive > ttl)).reduce((a, c) => a + c.body.filter(p => p.type === CARRY).length, 0);
  if (!want && ours7 && lo7 > 1000 && n('w8rminer') && rCarry(150) < rNeed * (lo7 > 3000 ? 1 : 0.6)) want = 'w8rhauler';
  // 12:00: local loose ~2.9k (source conts 1090/2000) with hub 0 while spawn waited on a 1000-cost 4th builder (have 3). Surplus
  // haulers sit behind builders in the queue (same trap as the rhauler floor): floor up to 5 haulers ahead of the 4th builder
  // while piles > 2500 so energy reaches hub/builders before more WORK.
  if (!want && sites && looseE(room) > 2500 && n('w8hauler') < 5) want = 'w8hauler';
  // 04:10: size by remaining build work, not site count: 3 cheap road sites (~900 left) brought a 4th builder while the ctl cont sat at 0,
  // wbuilder idle 0.69 (6h) and 4 upgraders energy-starved
  else if (!want && sites && n('w8builder') < (siteRem(room) >= 3000 ? 4 : siteRem(room) >= 1200 ? 3 : 2)) want = 'w8builder'; // 17:05: Spawn2 sat idle at 300/300 with 5 ext sites
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
    else if (!wallsLow && n('w8upgrader') < Math.min(6, (sites ? 2 : 3) + Math.floor(Math.max(0, loose + hubIdle - 600) / 600))
      && _.sum(cs.filter(c => c.memory.role === 'w8upgrader'), c => _.filter(c.body, p => p.type === WORK).length) < Math.max(24, Math.min(40, wm.upw || 0))) want = 'w8upgrader'; // 14:55: WORK cap = model net income (upw ~30) instead of fixed 24 // 21:20: 16->24 WORK; income ~20 local + ~13 W47N7 remote, ctl cont 1984/2000 full with 4x4W upgraders (WORK-bound)
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
    const tgt = wtgt;
    if (room.find(FIND_STRUCTURES, { filter: s => s.structureType === STRUCTURE_WALL && s.hits < tgt && C.SEAL.some(([x, y]) => s.pos.x === x && s.pos.y === y) }).length) want = 'w8builder';
  }
  // 7) W47N7 remote (after all local roles): only while home's reserve7 holds the reservation for us
  if (!want && ours7) {
    // 02:16: 3 rhaulers fell behind 2 reserved sources (~20 e/t): W47N7 had 31,34 full 2000 + 5871 dropped, 18,17 at 1138.
    // +1 per 1500 loose above 1500 in W47N7 (max 6), same idea as the local hauler surplus rule
    // looseE already counts drops + containers (CTL/HUB excludes are W47N8 coords, so both W47N7 conts count)
    // 02:35: max 6 -> 8: with 5 alive the pile kept growing (6175 -> 6229 dropped + conts 1978/2000 by t83729299); round trips ~90-120 ticks
    // at 400 carry = ~3.6 e/t each, below the 2 sources' ~20 e/t plus decay
    if (!want && n('w8rhauler') < 8 && rCarry(100) < rNeed * 1.1 + 16 * Math.floor(Math.max(0, lo7 - 3000) / 2000)) want = 'w8rhauler';
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
const L = require('./layout');
const TH = require('./threat'); // v3b (approved 20:11): ORDER per type nearest-core first; STRIPS with filler stand
const PRIO = ['spawn', 'extension', 'tower', 'container', 'storage', 'link', 'terminal', 'extractor', 'lab', 'factory', 'powerSpawn', 'nuker', 'observer', 'road', 'rampart'];
const isTemp = s => L.TEMP_EXT.some(([x, y]) => s.pos.x === x && s.pos.y === y);
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
  // 09:13 road audit: only the target network (roads.js: v3b spines + shared trunks + busy live roads) is placed
  const O = ok ? Object.assign({}, L.ORDER, { road: (rcl >= 6 ? require('./roads').ROADS : require('./roads').ROADS.filter(([x, y]) => !require('./roads').MINERAL.some(([a, b]) => a === x && b === y))).concat(require('../../layouts/w8link').W47N8) }) : { extension: L.TEMP_EXT, container: L.ORDER.container };
  // 14:09 (north threat): ramparts over built spawn/tower/storage go first, ahead of the road budget
  if (ok && rcl >= 4) for (const [x, y] of L.ORDER.rampart) {
    if (sites >= 6) return;
    const st = room.lookForAt(LOOK_STRUCTURES, x, y);
    if (!st.some(s => s.structureType === STRUCTURE_SPAWN || s.structureType === STRUCTURE_TOWER || s.structureType === STRUCTURE_STORAGE)) continue;
    if (st.some(s => s.structureType === STRUCTURE_RAMPART) || room.lookForAt(LOOK_CONSTRUCTION_SITES, x, y).length) continue;
    if (room.createConstructionSite(x, y, STRUCTURE_RAMPART) === OK) sites++;
  }
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
// Drain-aware tower (Misaki 14:09: BustJetter TOUGH/MOVE tanks + healers sit at W47N8 y0-2, north of the seal walls, to burn
// tower energy). Shoot only what matters: CLAIM creeps, anything inside the sealed base (y>=4), creeps able to hurt walls/
// creeps (WORK/ATTACK/RANGED) within 3 of our structures, and only when our damage beats the healing around the target.
// Never safe mode. Keeps 300 energy unless an armed creep is inside the base.
const PARTS = (c, t) => c.body.reduce((n, p) => n + (p.type === t && p.hits > 0 ? 1 : 0), 0);
const tdmg = r => (r <= 5 ? 600 : r >= 20 ? 150 : 600 - (r - 5) * 30);
function towerRun(room) {
  TH.mark(room); TH.mark(Game.rooms[C.REMOTE.room]);
  const towers = room.find(FIND_MY_STRUCTURES, { filter: s => s.structureType === STRUCTURE_TOWER });
  if (!towers.length) return;
  const h = room.find(FIND_HOSTILE_CREEPS);
  const hurt = room.find(FIND_MY_CREEPS, { filter: c => c.hits < c.hitsMax })[0];
  let best = null, bestScore = -1, inBaseThreat = false;
  for (const x of h) {
    const inBase = x.pos.y >= 4, claim = PARTS(x, CLAIM) > 0, armed = PARTS(x, ATTACK) + PARTS(x, RANGED_ATTACK) + PARTS(x, WORK) > 0;
    const nearOurs = armed && x.pos.findInRange(FIND_STRUCTURES, 3, { filter: s => s.my || s.structureType === STRUCTURE_WALL }).length > 0;
    if (!(claim || inBase || nearOurs)) continue;
    const dmg = towers.reduce((a, t) => a + tdmg(t.pos.getRangeTo(x)), 0);
    const heal = x.pos.findInRange(FIND_HOSTILE_CREEPS, 3).reduce((a, y) => a + PARTS(y, HEAL) * (y.pos.getRangeTo(x) <= 1 ? 12 : 4), 0);
    if (dmg <= heal && !inBase && !claim) continue; // out-healed outside the base: holding fire is the drain defence
    if (inBase && armed) inBaseThreat = true;
    const score = (claim ? 1000 : 0) + (inBase ? 500 : 0) + dmg - heal;
    if (score > bestScore) { bestScore = score; best = x; }
  }
  room.memory.threat8 = best ? { t: Game.time, id: best.id, inBase: inBaseThreat } : undefined;
  for (const t of towers) {
    if (best && (t.store[RESOURCE_ENERGY] > 300 || inBaseThreat || PARTS(best, CLAIM))) t.attack(best);
    else if (hurt && t.store[RESOURCE_ENERGY] > 500) t.heal(hurt);
    else if (t.store[RESOURCE_ENERGY] > 600) { // 14:09: keep fresh core ramparts alive (<5k; builders lift them further)
      const r = room.find(FIND_MY_STRUCTURES, { filter: s => s.structureType === STRUCTURE_RAMPART && s.hits < 5000 })[0];
      if (r) t.repair(r);
    }
  }
}
// self-sufficient = own spawn + a miner + a hauler alive (conquest.js stops sending cqworkers/cqhaulers)
function selfSufficient() {
  const r = Game.rooms[C.ROOM]; if (!r || !r.find(FIND_MY_SPAWNS).length) return false;
  return mine().some(c => c.memory.role === 'w8miner'); // Spawn2 + its own miner -> home stops cq pioneers/haulers (guard stays)
}
module.exports = { ROOM: C.ROOM, spawnRun, layoutRun, towerRun, selfSufficient, bodyFor };
