// W47N8 room module: spawn manager + layout + tower. Runs ONLY for W47N8; home W46N8 code never sees it.
// Never activates safe mode (Misaki does it manually).
const C = require('./config');
const rep = (n, p) => Array(n).fill(p);
const FM = require('./fillmeter');
const FL = require('./fill');
function mine() { return _.filter(Game.creeps, c => c.memory.home === C.ROOM); }
function bodyFor(role, e) {
  // 17:34 (Misaki joint defence): RA+MOVE only, no HEAL (towers heal on our ground; HP rule 60%/90% in defense.defPlan)
  if (role === 'w8defender') return require('./defense').raBody(e, 12);
  if (role === 'w8guard') return require('./defense').meleeBody(e); // 10-20 15:25 melee gate guard
  if (role === 'w8healer') return require('./defense').healBody(e, 12); // 18:04 local healer (joint roster >= 4)
  if (role === 'w8filler') return FL.body(e, Game.rooms[C.ROOM]); // 17:4x 2C:1M, carry ~75% of the hub spawn energy (fill.js)
  if (role === 'w8rminer') { // 20:22: old formula priced 4W1C3M=600 at cap 550, so it never spawned; now the biggest that fits, trimming MOVE first
    // 10-19 21:4x (strategy review, port of home rmBody): 6W. Reserved-room containers decay 5000/100t = 50 hits/t; repair shares the
    // harvest pipeline (repair blocks harvest that tick), so 5W (10/t, no slack) repaired 1 tick in 10 and mined ~9/t; R2 31,34 had
    // 900 left at ttr 32 (t83745419). 6W = 250 harvest + ~25 repair ticks per 300 -> full 10/t, +25t slack for handoffs.
    // MOVE = ceil(W/2): the empty CARRY weighs nothing, so 6W1C3M (800) still walks 1 tile/t on road.
    for (let w = 6; w >= 2; w--) for (let m = Math.ceil(w / 2); m >= Math.ceil((w + 1) / 3); m--)
      if (100 * w + 50 + 50 * m <= e) return rep(w, WORK).concat([CARRY], rep(m, MOVE));
    return [WORK, WORK, CARRY, MOVE];
  }
  // 02:35: W47N7 routes are road almost end to end (18,17->ctl 45 tiles/43 road, 31,34->59/56), so 2C:1M keeps full speed loaded:
  // 10C5M=750 carries 500 vs 8C8M=800 carrying 400 at cap 800
  if (role === 'w8rhauler') { if (e < 450) { const n = Math.max(2, Math.floor(e / 100)); return rep(n, CARRY).concat(rep(n, MOVE)); }
    // 15:55: 1 WORK (replaces 1 CARRY, still 2 heavy:1 MOVE) so loaded rhaulers build/repair the W47N7 road in passing
    const k = Math.min(8, Math.floor((e - 50) / 150)); return rep(2 * k - 1, CARRY).concat([WORK], rep(k, MOVE)); }
  // 17:20: 6W (12/t vs regen 10/t): a 5W miner needs every tick of the 300-tick regen, so walk-in, container repair and replacement gaps
  // were lost for good (local miners 85% working, 1 h). 6W catches up; +0.07 e/t upkeep. +1 CARRY at RCL5 to feed the source link.
  if (role === 'w8miner') { const w = Math.max(2, Math.min(6, Math.floor((e - 50) / 100))), cy = linkAt(C.SOURCES[0].link) && e >= 750 ? 1 : 0;
    return rep(Math.min(w, Math.floor((e - 50 - 50 * cy) / 100)), WORK).concat(rep(cy, CARRY), [MOVE]); }
  // 15:10 model: local routes are paved end to end (A->ctl 25/25 road, B->ctl 16/16, hub legs 1 unpaved tile), so 2C:1M keeps full
  // speed loaded on road: 10C5M = 750 carries the same 500 as 10C10M = 1000 (-0.5 e/t upkeep over 3 haulers). Below 450: 1:1.
  if (role === 'w8hauler') { if (e < 450) { const n = Math.max(2, Math.floor(e / 100)); return rep(n, CARRY).concat(rep(n, MOVE)); }
    const k = Math.min(5, Math.floor(e / 150)); return rep(2 * k, CARRY).concat(rep(k, MOVE)); }
  // 18:58: upgraders sit beside the ctl container 13,26 (1750/2000 full, spawn idle at 550/550): WORK-heavy 4W1C2M instead of 2W2C2M
  if (role === 'w8upgrader' && e >= 550) { const w = Math.min(10, Math.floor((e - 150) / 100)); return rep(w, WORK).concat([CARRY, MOVE, MOVE]); }
  const n = Math.max(1, Math.min(6, Math.floor(e / 200))); return rep(n, WORK).concat(rep(n, CARRY), rep(n, MOVE)); // upgrader/builder
}
// energy lying on the ground or in source containers (ctl container excluded)
const looseE = room => _.sum(room.find(FIND_DROPPED_RESOURCES, { filter: r => r.resourceType === RESOURCE_ENERGY }), r => r.amount)
  + _.sum(room.find(FIND_STRUCTURES, { filter: s => s.structureType === STRUCTURE_CONTAINER && !(s.pos.x === C.CTL_CONT[0] && s.pos.y === C.CTL_CONT[1]) && !(s.pos.x === C.HUB_CONT[0] && s.pos.y === C.HUB_CONT[1]) }), s => s.store[RESOURCE_ENERGY]);
const siteRem = room => _.sum(room.find(FIND_MY_CONSTRUCTION_SITES), s => s.progressTotal - s.progress);
// 14:57 (Misaki): spawn energy from hub-area extensions (nearest the core first) and hub spawns, Spawn2 + its 5 temp extensions last
function energyOrder(room) {
  const [cx, cy] = L.CORE, all = room.find(FIND_MY_STRUCTURES, { filter: s => s.structureType === STRUCTURE_EXTENSION || s.structureType === STRUCTURE_SPAWN });
  const last = s => (s.structureType === STRUCTURE_SPAWN && s.pos.x === C.SPAWN[0] && s.pos.y === C.SPAWN[1]) || (s.structureType === STRUCTURE_EXTENSION && isTemp(s));
  const d = s => Math.max(Math.abs(s.pos.x - cx), Math.abs(s.pos.y - cy));
  return all.filter(s => !last(s)).sort((a, b) => d(a) - d(b)).concat(all.filter(last).sort((a, b) => (a.structureType === STRUCTURE_SPAWN ? 0 : 1) - (b.structureType === STRUCTURE_SPAWN ? 0 : 1)));
}
// 10-19 22:4x patrol: + 60 queue margin. First live replacement at 18,17 was ordered at old TTL 43 (lead 140): Spawn2 was busy with
// 2 hauler-floor spawns (45t each) + a local miner from TTL 140 on, so the source sat unmined ~77 ticks. Overlap costs ~0.5 e/t-tick.
const rmLead8 = (i, c) => Math.min(180, Math.max(40, (Memory.ops && Memory.ops.w8rlead && Memory.ops.w8rlead[i]) || 90)) + 3 * ((c && c.body) || []).length + 20 + 60;
function spawnRun(spawn) {
  FM.tick(spawn); // 17:3x spawn-energy meter (Memory.ops.w8fm)
  if (spawn.spawning) return;
  const room = spawn.room, cs = mine(), n = r => cs.filter(c => c.memory.role === r).length;
  // 17:5x (patrol: 2 upgraders died within 40 ticks, upgrade fell to ~10 e/t): upgraders count only while they outlive a replacement
  // (spawn 3/part + ~60 ticks Spawn2 -> ctl stands), so the next one is queued before the old one dies
  const nUp = () => cs.filter(c => c.memory.role === 'w8upgrader' && (c.spawning || !(c.ticksToLive <= 3 * (c.body || []).length + 60))).length;
  const cap = room.energyCapacityAvailable, avail = room.energyAvailable;
  const sites = room.find(FIND_MY_CONSTRUCTION_SITES).length;
  let want = null, mem = {};
  // 0) defender (Misaki 14:09): only when an armed hostile is inside the sealed base (towerRun sets threat8.inBase); max 2
  const th = room.memory && room.memory.threat8;
  // 14:46 (Misaki): also on an invasion move (armed hostiles entering W47N8, or an armed group at the W47N9 border); max 2, stays in W47N8
  // 17:3x doctrine (docs/DEFENSE_W47N8.md): only when towerRun's assessment says towers alone lose AND towers + 2 defenders win;
  // never feed an unwinnable fight (Memory.ops.w8adv advises safe mode instead). Memory.ops.w8defOld = 1 restores the old trigger.
  // 17:34 joint defence: Memory.ops.w8roster (assessRun -> defense.plan) = local defenders + 1 home defender (src W46N8, spawned by home)
  const ro = Memory.ops && Memory.ops.w8roster, dOld = Memory.ops && Memory.ops.w8defOld, fresh = ro && Game.time - ro.t < 20;
  const local = cs.filter(c => (c.memory.role === 'w8defender' || c.memory.role === 'w8guard') && !c.memory.jd).length;
  const lg = cs.filter(c => c.memory.role === 'w8guard').length;
  const dGo = dOld ? ((th && th.inBase && Game.time - th.t < 5) || TH.invasion()) && local < 2 : !!(fresh && local < Math.min(D.MAXL, ro.w8)); // 17:56: up to 4 local
  // 10-20 07:4x (2room eval): the hub filler died while Spawn2 made 2 local defenders (threat outside the room) and its replacement
  // waited ~70 t behind them. Refill speed is defence reaction speed (Misaki 10-19), so a due filler goes first unless armed hostiles
  // are inside the base (same idea as home 'queen first' before joint defence).
  const inBase = !!(th && th.inBase && Game.time - th.t < 5);
  if (!inBase && FL.want(room, cs)) want = 'w8filler';
  // 10-20 17:0x (Misaki: guard out fast on any threat): armed group at the W47N9 south rows (north_watch w8n9a, fresh) or any armed
  // hostile in W47N8 -> keep 1 w8guard (roster may ask more in-room). Not replaced once the threat is gone.
  const armedIn = room.find(FIND_HOSTILE_CREEPS).some(h => require('./defense').armed(h)), n9t = (Memory.ops || {}).w8n9a || 0;
  const fmv = Memory.ops && Memory.ops.w8move && Memory.ops.w8move.force && ['prep', 'build'].includes(Memory.ops.w8move.phase);
  if (!want && (armedIn || fmv || (n9t > 0 && Game.time - n9t < 60)) && !cs.some(c => c.memory.role === 'w8guard' && (c.spawning || c.ticksToLive > 3 * 50 + 30))) want = 'w8guard';
  if (!want && dGo) { want = !dOld && lg < (ro.w8m | 0) ? 'w8guard' : 'w8defender'; }
  // 18:04: roster >= 4 combat defenders -> one dedicated healer; local only when home can't send it (ro.hl 'w8')
  if (!want && !dOld && fresh && ro.hl === 'w8' && !_.some(Game.creeps, c => c.memory.role === 'w8healer')) want = 'w8healer';
  // 1) miners per source: keep >=5 WORK (10 e/t) on each source. Replace at TTL<60; and since the first w8miners were 2 WORK
  // (cap 300) and would run at 40% for ~1000 ticks, add a bigger one once cap allows (17:25), counting any cqminer still there.
  for (let i = 0; i < C.SOURCES.length && !want; i++) {
    // 20:20: replace at TTL < walk time + spawn time (learned per source by w8miner on arrival). TTL<60 left source 11,44 unmined
    // ~150 ticks (5W1M walks 5-25 ticks/tile; spawn->11,43 took ~170 ticks), regen wasted at 3000/3000.
    const S = C.SOURCES[i], lead = Math.max(60, ((Memory.ops && Memory.ops.w8lead && Memory.ops.w8lead[i]) || 5 * spawn.pos.getRangeTo(S.stand[0], S.stand[1])) + 3 * 6 + 10);
    const live = cs.filter(c => c.memory.role === 'w8miner' && (c.memory.si | 0) === i && (c.spawning || c.ticksToLive > lead));
    const cq = room.find(FIND_MY_CREEPS, { filter: c => c.memory.role === 'cqminer' && c.ticksToLive > 60 && c.pos.inRangeTo(S.src[0], S.src[1], 1) });
    const works = _.sum(live.concat(cq), c => c.getActiveBodyparts(WORK) || _.filter(c.body, p => p.type === WORK).length);
    const add = bodyFor('w8miner', cap).filter(p => p === WORK).length;
    if (!live.length || (works < 5 && live.length < 2 && add > (live[0] ? live[0].getActiveBodyparts(WORK) : 0))) { want = 'w8miner'; mem.si = i; }
  }
  // 2) haulers 2, 3) upgraders 2 (3 when no sites), 4) builders while sites
  // 04:47: base 3 (was 2): with 2 haulers and 0 sites RCL3 fell ~22 -> ~7.5 e/t (t83731005..1169), ctl cont 0-114 while source conts
  // rose to 633/1000; the surplus 3rd only spawned after loose passed 1200, so the ctl ran dry every cycle
  // 17:15: count only haulers that outlive a replacement (15-part body 45t spawn + ~30t walk): the 5-hauler cohort aged out together
  // to 2 (one at TTL 155) before the floor fired; ctl cont 13,26 at 0 with 3 upgraders empty while 11,43 rose to 1450 (t83741650)
  if (!want && cs.filter(c => c.memory.role === 'w8hauler' && (c.spawning || c.ticksToLive > 75)).length < 3) want = 'w8hauler';
  // 17:4x (Misaki: spawn must never wait for energy): hub filler right after miners + the hauler floor, replaced ahead of death (fill.js)
  if (!want && FL.want(room, cs)) want = 'w8filler';
  // 10-20 03:4x (w8patrol): rminer replacements sat behind the 3rd upgrader (after a defender + 2-hauler burst): W47N7 src 18,17 unmined
  // from t83750522 with the other rminer at TTL 123 < lead. Income before sinks: W47N7 rminers come right after the filler.
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
  // 10-19 21:4x: lead = learned walk (Memory.ops.w8rlead, set on first reaching the source) + spawn time + 20 (fixed 100 < R2 ~70 walk +
  // 30 spawn + queue behind upgraders/filler at the single Spawn2; overlap is free: the newcomer mines from a tile beside the stand)
  for (let i = 0; ours7 && i < C.REMOTE.sources.length && !want; i++)
    if (!cs.some(c => c.memory.role === 'w8rminer' && (c.memory.si | 0) === i && (c.spawning || c.ticksToLive > rmLead8(i, c)))) { want = 'w8rminer'; mem.si = i; }
  // 10-20 04:4x: W47N7 reservation from Spawn2 once cap >= 1800 (roles/reserve7.js: ~60 t walk vs ~200 from home; home is the fallback)
  let body7 = null;
  if (!want) { const w7 = require('../../roles/reserve7').wantSpawn(C.ROOM); if (w7) { want = 'reserve7'; body7 = w7.body; mem = w7.mem; } }
  // 14:23 threat mode: seal walls to 50k ahead of upgrading; 1 upgrader keeps the controller safe (2 if downgrade < 10k)
  const thr = TH.on(), wtgt = TH.wallTarget(TH.planTarget((room.controller || {}).level || 0, C.WALL_TARGET[(room.controller || {}).level] || 0));
  // 15:45 hysteresis: core ramparts decay 300/100t, so a strict '< 50k' gate re-entered wall mode (1-2 upgraders, +builders) ~100 ticks
  // after every top-up. Wall mode starts below 90% of target; builders still repair to the full target (wallJob).
  // 17:15: seal walls only (ramparts no longer part of the wall raise)
  const wallsLow = thr && room.find(FIND_STRUCTURES, { filter: s => (s.structureType === STRUCTURE_WALL || (s.structureType === STRUCTURE_RAMPART && isGate(s.pos.x, s.pos.y))) && C.SEAL.some(([x, y]) => s.pos.x === x && s.pos.y === y) && s.hits < Math.min(wtgt, TH.urgentTarget()) * 0.9 }).length > 0; // 06:3x: threat floor only, RCL target from surplus
  // 15:10 model: under the wall raise 1 upgrader (10 WORK of ~30 e/t net) left ~8k idle in containers (ctl/hub 1.5k+1.6k, W47N8 sources
  // 2.3k, W47N7 2.8k) while builders spent ~13 e/t; a 2nd upgrader while >3000 sits in local piles + ctl/hub conts (stock covers the gap)
  const stock8 = () => looseE(room) + _.sum([C.CTL_CONT, C.HUB_CONT], ([x, y]) => _.sum(room.lookForAt(LOOK_STRUCTURES, x, y).filter(s => s.structureType === STRUCTURE_CONTAINER), s => s.store[RESOURCE_ENERGY]));
  // 10-20 14:4x strategy review: moveReady needs a builder with TTL >= 700, but with 0 sites and the north line at the stage-1 cap
  // nothing spawns one, so the move could stall on 'ttl' after the bank fills. Queue one once storage is within 3k of MOVE_E.
  const mv8 = Memory.ops && Memory.ops.w8move;
  if (!want && mv8 && mv8.phase === 'prep' && room.storage && bankE(room) >= MOVE_E - 3000
    && !cs.some(c => c.memory.role === 'w8builder' && (c.spawning || c.ticksToLive >= 700))) want = 'w8builder';
  if (!want && wallsLow && nUp() < (room.controller.ticksToDowngrade < 10000 || stock8() > 3000 ? 2 : 1)) want = 'w8upgrader';
  else if (!want && wallsLow && n('w8builder') < 3) want = 'w8builder';
  else if (!want && !wallsLow && nUp() < (banking(room) ? (room.controller.ticksToDowngrade < 20000 ? 1 : 0) : sites ? 2 : 3)) want = 'w8upgrader'; // 15:5x: 0 upgraders while moving unless downgrade < 20k // 13:39 spawn move: bank for the 15k spawn
  // 14:55 model-driven (tools/model_w8.py -> Memory.ops.w8model): remote fleet sized by CARRY need = sum 10 x (rt x 1.1 + 4) / 50 over
  // both W47N7 sources (~52 at 14:55) instead of loose-pile thresholds (live 88 CARRY: rhaulers 82% moving/12% blocked, +1.8 e/t upkeep).
  // Floor (ahead of builders): 60% of need; full need + a backlog term (+16 CARRY per 2000 loose above 3000) in step 7.
  const wm = (Memory.ops && Memory.ops.w8model) || {}, rNeed = wm.rcarry || 55;
  // 15:55 model: local CARRY need = lcarry (~20, source->ctl) + ~10 for extension refills (spawn upkeep ~10 e/t over ~45t hub trips) = ~30
  // = 3 x 10C5M. The loose-pile surplus rule had grown it to 5-6 haulers (50-60 CARRY): the piles were sink-bound (ctl cont 2000 full,
  // 1-2 upgraders under the wall rule), so extra haulers only cost upkeep. Max 4 (one spare for stock/storage moves).
  const HMAX = Math.max(3, Math.min(4, Math.ceil(((wm.lcarry || 20) + 10) / 10) + 1));
  const rCarry = (ttl) => cs.filter(c => c.memory.role === 'w8rhauler' && (c.spawning || c.ticksToLive > ttl)).reduce((a, c) => a + c.body.filter(p => p.type === CARRY).length, 0);
  if (!want && ours7 && lo7 > 1000 && n('w8rminer') && rCarry(150) < rNeed * (lo7 > 3000 ? 1 : 0.6)) want = 'w8rhauler';
  // 12:00: local loose ~2.9k (source conts 1090/2000) with hub 0 while spawn waited on a 1000-cost 4th builder (have 3). Surplus
  // haulers sit behind builders in the queue (same trap as the rhauler floor): floor up to 5 haulers ahead of the 4th builder
  // while piles > 2500 so energy reaches hub/builders before more WORK.
  if (!want && sites && looseE(room) > 2500 && n('w8hauler') < HMAX) want = 'w8hauler';
  // 04:10: size by remaining build work, not site count: 3 cheap road sites (~900 left) brought a 4th builder while the ctl cont sat at 0,
  // wbuilder idle 0.69 (6h) and 4 upgraders energy-starved
  else if (!want && sites && n('w8builder') < (siteRem(room) >= 3000 ? 4 : siteRem(room) >= 1200 ? 2 : 1)) want = 'w8builder'; // 17:20: 1 for a small backlog (2 road sites ~480 kept 3x 6W builders, 2.4 e/t upkeep) // 17:05: Spawn2 sat idle at 300/300 with 5 ext sites
  // 5) surplus (17:52: 1.8k energy lying on the ground/in source containers, spenders only ~7 WORK of 20 e/t income):
  // +1 hauler above 1200 loose (max 3), +1 upgrader per 600 loose above 600 (max 6)
  if (!want) {
    const loose = looseE(room);
    // 03:20 hub container energy counts toward upgraders once no sites near the hub use it (2000 full + ctl 652, Spawn2 idle 718/800,
    // only 2 upgraders = 12 WORK for ~40 e/t local+W47N7 income; RCL3 ~14.6 e/t)
    const hubC = room.lookForAt(LOOK_STRUCTURES, C.HUB_CONT[0], C.HUB_CONT[1]).find(s => s.structureType === STRUCTURE_CONTAINER);
    const hubIdle = hubC && !room.find(FIND_MY_CONSTRUCTION_SITES, { filter: s => s.structureType !== STRUCTURE_WALL && s.pos.inRangeTo(C.HUB_CONT[0], C.HUB_CONT[1], 5) }).length ? hubC.store[RESOURCE_ENERGY] : 0;
    if (loose > 1200 && n('w8hauler') < Math.min(HMAX, loose > 2000 ? 4 : 3)) want = 'w8hauler'; // 18:20: 4th when >2k piles (far south source)
    // 23:45: 7th above 3.5k while sites exist: with 6 haulers loose still rose 3.2k -> 3.96k in 146 ticks (~5 e/t), 11,43 full 2000 + 126 dropped,
    // Spawn2 idle 600/600, 4 builders mostly queue_blocked, builds fell to ~5.5 e/t
    // 23:20: 6th already above 2.5k while sites exist: loose 3048 -> 2736 by t83726755 (just under 3k, so Spawn2 sat idle 600/600) while 4 builders
    // were queue_blocked ~100/113 samples and 5 upgraders ~75/69-tick windows (creep_motion 0.25h); builds ~7.5 e/t + RCL3 ~6 e/t
    // 23:10: 6th above 3k: loose 2763 -> 3048 in ~95t (11,43 at 1690) while hub builders sat queue_blocked ~70% of ticks and the ctl cont ran down to 137 (RCL3 ~4 e/t)
    // 21:10: 5th above 2.5k: source conts rose 894/820 -> 1194/1320 in 161t while the ctl cont fell 1984 -> 1386 (haul-bound, not WORK-bound)
    // 15:10 model: base by remaining build work (3 road sites = ~700 left held upgraders at 2 = 20 WORK of ~30 e/t net), and storage
    // above 2k counts as stock (rhaulers now overflow there); WORK cap = model upw + 5 per 5k stored (max 40, 4 stands x 10W)
    const stor = room.storage ? room.storage.store[RESOURCE_ENERGY] : 0, bigBuild = siteRem(room) >= 3000;
    const wcap = Math.max(24, Math.min(40, (wm.upw || 0) + 5 * Math.floor(stor / 5000)));
    if (!want && !wallsLow && !banking(room) && nUp() < Math.min(6, (bigBuild ? 2 : 3) + Math.floor(Math.max(0, loose + hubIdle + Math.max(0, stor - 2000) - 600) / 600))
      && _.sum(cs.filter(c => c.memory.role === 'w8upgrader' && (c.spawning || !(c.ticksToLive <= 3 * (c.body || []).length + 60))), c => _.filter(c.body, p => p.type === WORK).length) + bodyFor('w8upgrader', cap).filter(p => p === WORK).length <= wcap + 5) want = 'w8upgrader'; // 15:55: a whole new body must fit (upw 31 made 4x10W = 40 WORK on ~30 e/t net) // 14:55: WORK cap = model net income (upw ~30) instead of fixed 24 // 21:20: 16->24 WORK; income ~20 local + ~13 W47N7 remote, ctl cont 1984/2000 full with 4x4W upgraders (WORK-bound)
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
    // 18:05: need x1.0 (model rcarry already carries the 1.1 congestion factor; x1.1 kept 75 CARRY vs 56 with W47N7 conts empty)
    if (!want && n('w8rhauler') < 8 && rCarry(100) < rNeed + 16 * Math.floor(Math.max(0, lo7 - 3000) / 2000)) want = 'w8rhauler';
  }
  if (!want) { FM.idle(); return; }
  // emergency: nothing alive that refills -> spawn with what we have
  const starving = !n('w8hauler') || !n('w8miner');
  const e = starving ? Math.max(200, avail) : cap;
  const body = body7 || bodyFor(want, e), cost = _.sum(body, p => BODYPART_COST[p]);
  if (avail < cost) { FM.wait(want, cost, avail); return; }
  if (spawn.spawnCreep(body, want + Game.time, { memory: Object.assign({ role: want, home: C.ROOM, born: Game.time, v2: 1 }, mem), energyStructures: energyOrder(room) }) === 0) FM.spent(cost);
}
const isGate = (x, y) => (C.GATE || []).some(([a, b]) => a === x && b === y);
function placeSeal(room) {
  for (const [x, y] of C.SEAL) {
    if (isGate(x, y)) { // rampart gate (13:30): never re-wall; rampart site only once the old wall is gone
      const st = room.lookForAt(LOOK_STRUCTURES, x, y);
      if (!st.some(s => s.structureType === STRUCTURE_WALL || s.structureType === STRUCTURE_RAMPART) && !room.lookForAt(LOOK_CONSTRUCTION_SITES, x, y).length) room.createConstructionSite(x, y, STRUCTURE_RAMPART);
      continue;
    }
    if (room.lookForAt(LOOK_STRUCTURES, x, y).some(s => s.structureType === STRUCTURE_WALL)) continue;
    if (room.lookForAt(LOOK_CONSTRUCTION_SITES, x, y).length) continue;
    room.createConstructionSite(x, y, STRUCTURE_WALL);
  }
}
const L = require('./layout');
const TH = require('./threat'); // v3b (approved 20:11): ORDER per type nearest-core first; STRIPS with filler stand
const PRIO = ['spawn', 'tower', 'extension', 'container', 'storage', 'link', 'terminal', 'extractor', 'lab', 'factory', 'powerSpawn', 'nuker', 'observer', 'road']; // no 'rampart' (17:15, see layoutRun)
const isTemp = s => L.TEMP_EXT.some(([x, y]) => s.pos.x === x && s.pos.y === y);
function swapTemp(room, minE = 50000) {
  const hub = room.lookForAt(LOOK_STRUCTURES, L.ORDER.spawn[0][0], L.ORDER.spawn[0][1]).some(s => s.structureType === STRUCTURE_SPAWN && s.my);
  if (!hub || !room.storage || room.storage.store[RESOURCE_ENERGY] <= minE || room.energyAvailable < room.energyCapacityAvailable) return null;
  if (room.find(FIND_MY_CONSTRUCTION_SITES, { filter: s => s.structureType === STRUCTURE_EXTENSION }).length || room.find(FIND_MY_CONSTRUCTION_SITES).length >= 5) return null;
  const temp = L.TEMP_EXT.map(([x, y]) => room.lookForAt(LOOK_STRUCTURES, x, y).find(s => s.structureType === STRUCTURE_EXTENSION)).find(Boolean);
  if (!temp) return null;
  const tr = room.getTerrain(), slot = L.ORDER.extension.find(([x, y]) => !room.lookForAt(LOOK_STRUCTURES, x, y).some(s => s.structureType === STRUCTURE_EXTENSION));
  if (!slot || (tr.get(slot[0], slot[1]) & 1) || room.lookForAt(LOOK_STRUCTURES, slot[0], slot[1]).some(s => s.structureType !== STRUCTURE_RAMPART)) return null;
  if (temp.destroy() !== OK) return null;
  (Memory.ops = Memory.ops || {}).w8swap = { from: [temp.pos.x, temp.pos.y], to: slot, t: Game.time };
  return slot;
}
// 10-20 13:39 (Misaki order): relocate Spawn2 15,18 -> 34,30 (was 32,32, see layout.js) (RCL5 allows 1 spawn: destroy, then build 15k site), then swap the
// 5 temp extensions by Spawn2 into v3b ORDER slots one at a time. Memory.ops.w8move.phase: prep -> build -> ext -> done.
// prep only fires when it is safe: no hostiles/threat mode, storage >= MOVE_E (whole spawn bill banked), spawn idle and full, both
// miners + 2 haulers TTL >= 500, a builder TTL >= 700 (nobody needs a spawn during the ~300-500 t build). While in prep the room banks
// (upgraders capped at 1). Abort = set phase 'hold' (prep never resumes on its own once held).
// 10-20 15:5x (Misaki: move ASAP): bank 16k -> 9k in storage + hub container. The 15k site is built from the bank plus live income
// (W47N8 + W47N7 ~20-25 e/t keeps flowing through haulers while no spawn exists): ~6k / 22 e/t ~ 280 t extra build time.
const MOVE_E = 9000, N9_QUIET = 150; // ~one north_watch scan (10 min ~ 140 t)
const bankE = room => (room.storage ? room.storage.store[RESOURCE_ENERGY] : 0) + _.sum(room.lookForAt(LOOK_STRUCTURES, C.HUB_CONT[0], C.HUB_CONT[1]).filter(s => s.structureType === STRUCTURE_CONTAINER), s => s.store[RESOURCE_ENERGY]);
function moveReady(room) {
  const sp = room.find(FIND_MY_SPAWNS)[0], cs = mine(), ttl = (r, t) => cs.filter(c => c.memory.role === r && c.ticksToLive >= t).length;
  const why = [];
  if (!sp || sp.pos.x !== C.SPAWN[0] || sp.pos.y !== C.SPAWN[1]) why.push('spawn');
  if (sp && sp.spawning) why.push('spawning');
  // 10-20 14:0x (Misaki ordered the move today): TH.on() never clears while W48N9 holds >=2 armed (north_watch refreshes w8threatN), so
  // gate only on real proximity: hostiles in W47N8, invasion(), or armed creeps in W47N9 (north_watch w8n9a) within N9_QUIET ticks.
  // 10-20 18:1x (Misaki order: move at 19:30 despite the W47N9 border): Memory.ops.w8move.force = 1 skips ONLY the W47N9 (w8n9a) check.
  // Forced moves additionally need: north line >= 100k, both towers >= 700, a builder within 3 of the new slot, a w8guard alive.
  const n9 = (Memory.ops || {}).w8n9a || 0, mv = (Memory.ops || {}).w8move || {}, force = !!mv.force;
  if (room.find(FIND_HOSTILE_CREEPS).length || TH.invasion() || (!force && n9 > 0 && Game.time - n9 < N9_QUIET)) why.push('threat');
  if (force) {
    const [nx, ny] = L.ORDER.spawn[0];
    if (room.find(FIND_STRUCTURES, { filter: s => (s.structureType === STRUCTURE_WALL || s.structureType === STRUCTURE_RAMPART) && C.SEAL.some(([x, y]) => s.pos.x === x && s.pos.y === y) && s.hits < 100000 }).length) why.push('walls');
    if (room.find(FIND_MY_STRUCTURES, { filter: s => s.structureType === STRUCTURE_TOWER && s.store[RESOURCE_ENERGY] < 700 }).length) why.push('towers');
    if (!cs.some(c => c.memory.role === 'w8builder' && !c.spawning && c.pos.inRangeTo(nx, ny, 3) && c.store[RESOURCE_ENERGY] > 0)) why.push('builderpos');
    if (!cs.some(c => c.memory.role === 'w8guard')) why.push('guard');
  }
  if (!room.storage || bankE(room) < MOVE_E) why.push('storage');
  if (room.energyAvailable < room.energyCapacityAvailable) why.push('energy');
  if (ttl('w8miner', 500) < 2 || ttl('w8hauler', 500) < 2 || ttl('w8builder', 700) < 1) why.push('ttl');
  return why;
}
function moveRun(room) {
  const o = (Memory.ops = Memory.ops || {}), m = o.w8move; if (!m || room.controller.level < 5) return;
  const [nx, ny] = L.ORDER.spawn[0], sp = room.find(FIND_MY_SPAWNS);
  // 18:1x: forced move, armed hostile inside W47N8 before the destroy -> hold (Misaki restarts it: phase 'prep')
  if (m.phase === 'prep' && m.force && room.find(FIND_HOSTILE_CREEPS).some(h => D.armed(h))) { m.phase = 'hold'; m.held = Game.time; m.why = ['armed-in-room']; return; }
  if (m.phase === 'prep') { // 15:5x: rampart over the new slot first (1 hit site, builders finish it fast); the spawn site may sit on a rampart
    const ramp = room.lookForAt(LOOK_STRUCTURES, nx, ny).some(s => s.structureType === STRUCTURE_RAMPART);
    if (!ramp && !room.lookForAt(LOOK_CONSTRUCTION_SITES, nx, ny).length) room.createConstructionSite(nx, ny, STRUCTURE_RAMPART);
    m.why = moveReady(room); if (!ramp) m.why.push('rampart'); if (m.why.length) return;
    const old = sp[0]; if (old.destroy() === OK) { m.phase = 'build'; m.t0 = Game.time; } return; }
  if (m.phase === 'build') {
    if (sp.some(s => s.pos.x === nx && s.pos.y === ny)) { m.phase = 'ext'; m.t1 = Game.time; return; }
    if (!sp.length && !room.lookForAt(LOOK_CONSTRUCTION_SITES, nx, ny).some(s => s.structureType === STRUCTURE_SPAWN)) m.site = room.createConstructionSite(nx, ny, STRUCTURE_SPAWN, 'Spawn2');
    return;
  }
  if (m.phase === 'ext') { if (!L.TEMP_EXT.some(([x, y]) => room.lookForAt(LOOK_STRUCTURES, x, y).some(s => s.structureType === STRUCTURE_EXTENSION))) { m.phase = 'done'; m.t2 = Game.time; } else swapTemp(room, 3500); }
}
// 10-20 17:0x (Misaki: storage 20k+ idle): banking only holds MOVE_E + 2k; above that upgraders/builders/repairs run as normal
const BANK_HOLD = MOVE_E + 2000, banking = room => moving() && bankE(room) < BANK_HOLD;
const moving = () => { const m = Memory.ops && Memory.ops.w8move; return !!m && (m.phase === 'prep' || m.phase === 'build'); };
function layoutRun(room) {
  if (Game.time % 20) return;
  if (room.controller.level >= 2) placeSeal(room);
  moveRun(room);
  if (moving() && Memory.ops.w8move.phase === 'build') return;
  if (!room.find(FIND_MY_SPAWNS).length) return;
  const rcl = room.controller.level, ok = Memory.ops && Memory.ops.w8layout === 'approved';
  if (rcl >= 3) { const [hx, hy] = C.HUB_CONT; if (!room.lookForAt(LOOK_STRUCTURES, hx, hy).some(s => s.structureType === STRUCTURE_CONTAINER) && !room.lookForAt(LOOK_CONSTRUCTION_SITES, hx, hy).length) room.createConstructionSite(hx, hy, STRUCTURE_CONTAINER); }
  // 14:57 (Misaki, was RCL8): temp-extension swap from RCL7 once hub spawn 32,32 stands and storage > 50k. One at a time, in TEMP_EXT
  // order, into the next unbuilt v3b ORDER.extension slot. Destroy only when: spawn energy full (spare), no extension site pending
  // (previous swap done), the replacement tile is clear and the site budget has room (this run's PRIO loop / the next places it).
  // Spawn2 is kept.
  if (ok && rcl >= 7) swapTemp(room);
  for (const s of room.find(FIND_MY_CONSTRUCTION_SITES, { filter: s => s.structureType === STRUCTURE_RAMPART && !isGate(s.pos.x, s.pos.y) && !(s.pos.x === L.ORDER.spawn[0][0] && s.pos.y === L.ORDER.spawn[0][1]) })) s.remove(); // 17:15, see below
  let sites = room.find(FIND_MY_CONSTRUCTION_SITES, { filter: s => s.structureType !== STRUCTURE_RAMPART }).length; if (sites >= 6) return;
  // 03:05 west<->hub link road (missing from v3b plan): loaded 10C5M rhaulers sat 7-10 ticks on unroaded swamp 22,34 (fatigue 70)
  // between road 15,33 and strip road 24,35; queued ahead of the plan roads since every hub trip crosses it
  // 09:13 road audit: only the target network (roads.js: v3b spines + shared trunks + busy live roads) is placed
  // 10-20 03:4x strategy review (docs/PLAN_W47N8.md "RCL6 gate"): with RCL6_MINERALS off, terminal (100k), extractor (5k), 3 labs (150k),
  // the extractor trunk and, with HUB_LINK off, the hub link 33,34 (5k) are not placed: no W47N8 code uses any of them (no mineral miner,
  // no lab/terminal logic, linkRun only moves A -> ctl), so they would idle 260k of energy (~8.7k t, ~10 h of upgrade at ~30 e/t).
  const R8 = require('./roads'), minOk = !!C.RCL6_MINERALS;
  const O = ok ? Object.assign({}, L.ORDER, { link: [C.CTL_LINK, C.SOURCES[0].link].concat(C.HUB_LINK ? L.ORDER.link : []), road: (rcl >= 6 && minOk ? R8.ROADS : R8.ROADS.filter(([x, y]) => !R8.MINERAL.some(([a, b]) => a === x && b === y))).concat(require('../../layouts/w8link').W47N8) },
    minOk ? {} : { terminal: [], extractor: [], lab: [] }) : { extension: L.TEMP_EXT, container: L.ORDER.container };
  // 17:15 (Misaki "急着早 rampart 是为了什么" / "看看主房间"): no rampart placement here. The PRIO loop placed every v3b ORDER.rampart
  // tile at RCL4, incl. empty future spawn/terminal/tower slots (32,32 32,33 33,32 33,30 built; 34,31 36,31 36,33 sites), and
  // builders raised them to the 50k seal target. Home only rampart-covers real structures and deferred even those behind storage
  // (6957a9a). Unbuilt rampart sites are dropped (top of layoutRun); built ones hold their current hits via the tower (rampHold, ~0.2 e/t for 7).
  // 17:5x strategy review: tower before everything except spawn, and nothing new is queued while a tower site stands. At RCL5 the
  // old order put 10 extensions (30k, ~2-3 h at W47N8's ~10-15 e/t build) ahead of tower 2 (5k); combat_sim F2/F3 (DEFENSE_W47N8.md)
  // says 2 towers alone beat the full BustJetter squad while 1 tower loses without defenders, so tower 2 is the defence step to rush.
  let towerSite = room.find(FIND_MY_CONSTRUCTION_SITES, { filter: s => s.structureType === STRUCTURE_TOWER }).length > 0;
  for (const t of PRIO) {
    if (t === 'extension' && towerSite) return;
    if (t === 'road' && rcl < 3) continue;
    for (const [x, y] of (O[t] || [])) {
      if (sites >= 6) return;
      if (t === 'road' && sites > 2) return; // roads only when little else is queued
      if (room.lookForAt(LOOK_STRUCTURES, x, y).some(s => s.structureType === t)) continue;
      if (room.lookForAt(LOOK_CONSTRUCTION_SITES, x, y).length) continue;
      const r = room.createConstructionSite(x, y, t);
      if (r === OK) { sites++; if (t === 'tower') towerSite = true; } else if (r === ERR_RCL_NOT_ENOUGH) break; // next type
    }
  }
}
// Drain-aware tower (Misaki 14:09 / 17:3x doctrine, docs/DEFENSE_W47N8.md): BustJetter TOUGH/MOVE tanks + healers sit at W47N8 y0-2,
// north of the seal walls, to burn tower energy. Target choice is ./defense towerPick: claimers anywhere, anything inside the seal
// (y>3), armed creeps hurting us; net damage > 0 only (tower dmg at range - reachable heal); healer > ranged > melee (lowest hp); one focus for
// all towers; non-urgent targets only from towers >= 400 energy; drain-pattern creeps (knocked down and healed back twice, or
// 1000 energy spent) are skipped unless urgent. Never safe mode (assessment only advises, Memory.ops.w8adv).
const PARTS = (c, t) => c.body.reduce((n, p) => n + (p.type === t && p.hits > 0 ? 1 : 0), 0);
const tdmg = r => (r <= 5 ? 600 : r >= 20 ? 150 : 600 - (r - 5) * 30);
// 17:20 (Misaki final rule): no new ramparts; built ones only offset decay. Memory.ops.w8hold[id] = hits first seen (ratchets down never,
// up never: a fresh rampart's hold is what it had). Tower tops up one rampart once it is HOLD_SLACK below its hold (300 hits/100t decay,
// ~0.03 e/t per rampart). Gone ramparts drop out of the map.
const HOLD_SLACK = 1000;
// 10-20 13:39 (Misaki): only NECESSARY ramparts are held: the gate (29,3), ramparts over a key structure (spawn, storage, tower,
// terminal) and the hub spawn slot 32,32 (the relocated spawn lands under it). Empty-slot ramparts (33,32 33,30 34,31 36,31 36,33
// 32,33) and the old Spawn2 rampart once Spawn2 is gone are left to decay.
const KEY = ['spawn', 'storage', 'tower', 'terminal'];
function rampNeeded(room, r) {
  if (!r.pos) return true;
  const { x, y } = r.pos;
  if (isGate(x, y) || (x === L.ORDER.spawn[0][0] && y === L.ORDER.spawn[0][1])) return true;
  return !room.lookForAt || room.lookForAt(LOOK_STRUCTURES, x, y).some(s => KEY.includes(s.structureType));
}
function rampHold(room) {
  const rs = room.find(FIND_MY_STRUCTURES, { filter: s => s.structureType === STRUCTURE_RAMPART }).filter(r => rampNeeded(room, r));
  const o = (Memory.ops = Memory.ops || {}), h = (o.w8hold = o.w8hold || {}), live = {};
  for (const r of rs) live[r.id] = h[r.id] === undefined ? r.hits : h[r.id];
  o.w8hold = live;
  // 13:30 gate ramp-up; 10-20 16:5x patrol: also the spawn-slot rampart (L.ORDER.spawn[0]). It is built at 1 hit and its hold was 1,
  // so it decayed away every ~100 t (seen t83761858-862) and the relocated spawn would have stood uncovered. Same 20k tower floor (~200 e).
  const slot = (x, y) => x === L.ORDER.spawn[0][0] && y === L.ORDER.spawn[0][1];
  const g = rs.find(r => r.pos && (isGate(r.pos.x, r.pos.y) || slot(r.pos.x, r.pos.y)) && r.hits < (C.GATE_TOWER || 0)); if (g) return g;
  return rs.find(r => r.hits < live[r.id] - HOLD_SLACK) || null;
}
// 17:20 RCL5 links (parent-approved plan): source A link 26,12 -> ctl link 13,25 (3% loss) replaces ~25-tile hauling of source A.
function linkAt(p) { const r = Game.rooms[C.ROOM]; return p && r && r.lookForAt(LOOK_STRUCTURES, p[0], p[1]).find(s => s.structureType === STRUCTURE_LINK); }
function linkRun() {
  const a = linkAt(C.SOURCES[0].link), k = linkAt(C.CTL_LINK);
  if (a && k && !a.cooldown && a.store[RESOURCE_ENERGY] >= 400 && k.store.getFreeCapacity(RESOURCE_ENERGY) >= 400) a.transferEnergy(k);
}
const D = require('./defense'), F = require('../../utils/focus');
const SEAL_FIGHT = { x: 27, y: 3 }; // centre of the east seal: where a north squad has to break in
// armed hostiles within reach (RA 3, ATTACK/WORK 1) of our creeps, our structures or the seal walls
function hurtingSet(room, hs) {
  const s = new Set(); hs = hs.filter(D.armed); if (!hs.length) return s; // drain tanks only: skip the structure scan (CPU)
  const ours = room.find(FIND_MY_CREEPS).concat(room.find(FIND_STRUCTURES, { filter: x => x.my || x.structureType === STRUCTURE_WALL }));
  for (const h of hs) { const r = PARTS(h, RANGED_ATTACK) ? 3 : PARTS(h, ATTACK) + PARTS(h, WORK) ? 1 : 0;
    if (r && ours.some(o => Math.max(Math.abs(o.pos.x - h.pos.x), Math.abs(o.pos.y - h.pos.y)) <= r)) s.add(h.id); }
  return s;
}
// every 5 ticks while an armed force is in W47N8 or announced at the W47N9 border: can towers / towers + 2 defenders win?
function assessRun(room, towers, hs) {
  const m = room.memory, o = (Memory.ops = Memory.ops || {});
  const inRoom = hs.filter(h => PARTS(h, ATTACK) + PARTS(h, RANGED_ATTACK) > 0), north = o.w8invN > 0 && Game.time - o.w8invN < 60; // 18:06: threat cleared = no armed hostile in W47N8 and no border signal for 60 t (~4 north_watch scans) -> roster dropped, no spawns/replacements (was 300: kept 5 defenders spawning after withdrawal)
  if (!inRoom.length && !north) { if (m.w8assess) delete m.w8assess; if (o.w8roster) delete o.w8roster; return; }
  if (m.w8assess && Game.time - m.w8assess.t < 10) return; // up to 5x5 sims (<=600 t each): cached 10 ticks
  let force, at;
  if (inRoom.length) { force = hs.filter(h => D.armed(h) || PARTS(h, HEAL)); at = inRoom.reduce((a, h) => (h.pos.y > a.pos.y ? h : a)).pos; }
  else if (Array.isArray(o.w8invNb) && o.w8invNb.length) { force = o.w8invNb.map(D.fromCounts); at = SEAL_FIGHT; }
  else force = [D.fromCounts({ ranged_attack: 8, move: 8 }), D.fromCounts({ ranged_attack: 6, move: 6 })], at = SEAL_FIGHT; // no body data: assume the 17:34 pair
  const inside = inRoom.some(h => h.pos.y > D.SEAL_Y);
  const tr = towers.map(t => Math.max(Math.abs(t.pos.x - at.x), Math.abs(t.pos.y - at.y)));
  // 17:34 joint planner (defense.plan): one place decides the W46N8 + W47N8 roster; home only if home itself is not threatened
  const hr = Game.rooms[HOME], homeOk = !!hr && !require('../../managers/home').active(hr);
  const r = D.plan({ force, towerR: tr, inside, homeOk, homeCap: hr ? hr.energyCapacityAvailable : 0, w8Cap: room.energyCapacityAvailable || 300,
    towerE: Math.min(...towers.map(t => t.store[RESOURCE_ENERGY])), atkBoost: o.w8uh > 0 ? 'UH' : '', meleeUptime: inside ? 1 : 0 }); // 17:58: UH stock north -> boosted melee; melee only reaches us inside the seal
  o.w8roster = { t: Game.time, home: r.home, w8: r.w8, w8m: r.w8m | 0, hl: r.hl || '', why: r.why };
  m.w8assess = { t: Game.time, spawn: r.w8 > 0, why: r.why, at: [at.x, at.y] };
  if (r.advise) o.w8adv = { t: Game.time, advise: r.advise, why: r.why, n: force.length }; // safe mode is Misaki's call (alerts relay it)
}
function towerRun(room) {
  TH.mark(room); TH.mark(Game.rooms[C.REMOTE.room]); linkRun();
  const towers = room.find(FIND_MY_STRUCTURES, { filter: s => s.structureType === STRUCTURE_TOWER });
  if (!towers.length) return;
  const h = room.find(FIND_HOSTILE_CREEPS).filter(x => !x.my);
  assessRun(room, towers, h);
  // 17:48 (Misaki): heal only creeps < 60% (no-HEAL creeps first, lowest %); a heal candidate beats attacking this tick
  const peace = !F.hostileArmed(h); // 18:00 (Misaki): no armed/healing hostile -> heal any damaged creep to full (floor 200 e)
  const hurt = F.healPick(room.find(FIND_MY_CREEPS), peace);
  let p = null;
  if (h.length) {
    const m = room.memory, hurting = hurtingSet(room, h);
    const banned = F.track(m.drain8 || (m.drain8 = {}), h, Game.time, m.threat8 && m.threat8.id, m.threat8 && m.threat8.e);
    p = D.towerPick(towers.map(t => ({ pos: t.pos, energy: t.store[RESOURCE_ENERGY], t })), h, { prev: m.threat8 && m.threat8.id, hurting, banned,
      allies: room.find(FIND_MY_CREEPS).map(c => ({ pos: c.pos, ra: (c.body || []).filter(b => b.type === RANGED_ATTACK && b.hits > 0).length })).filter(a => a.ra) });
  } else if (room.memory.drain8 && Game.time % 100 === 0) F.track(room.memory.drain8, [], Game.time);
  const inBaseThreat = !!p && p.h.pos.y > D.SEAL_Y && D.armed(p.h);
  room.memory.threat8 = p ? { t: Game.time, id: p.h.id, inBase: inBaseThreat, e: p.shooters.length * 10 } : undefined;
  const fire = new Set(p ? p.shooters.map(s => s.t) : []);
  for (const t of towers) {
    if (hurt && (!peace || t.store[RESOURCE_ENERGY] >= 200)) t.heal(hurt);
    else if (fire.has(t)) t.attack(p.h);
    else if (t.store[RESOURCE_ENERGY] > 600) { // 17:20 (Misaki): built ramparts hold their current hits (decay offset only, never raised)
      const r = rampHold(room);
      if (r) t.repair(r);
    }
  }
}
// 17:34 joint defence, home side: W46N8 spawn asks this. One RA+MOVE defender (max that fits home cap, no HEAL) for W47N8 when the
// planner wants it, home has no player combat creeps, and fewer home-sent defenders (memory.jd W46N8; not 'src', which main.js strips from creeps without v2) are alive/spawning.
// Overrides the home storage floor (defence). The creep runs the w8defender role (home: W47N8) and idles by the north wall until its TTL ends (18:04: no recycle).
const HOME = 'W46N8';
function homeWant(room) {
  const ro = Memory.ops && Memory.ops.w8roster;
  if (room.name !== HOME || !ro || !ro.home || Game.time - ro.t > 20) return null;
  if (require('../../managers/home').active(room)) return null;
  const sent = _.filter(Game.creeps, c => c.memory.role === 'w8defender' && c.memory.jd === HOME).length;
  const mem = { home: C.ROOM, jd: HOME, born: Game.time, v2: 1 };
  if (sent < ro.home) return { role: 'w8defender', body: require('./defense').raBody(room.energyCapacityAvailable, 25), mem };
  // 18:04: roster >= 4 -> one dedicated healer from home at max cap (HEAL+MOVE)
  if (ro.hl === 'home' && !_.some(Game.creeps, c => c.memory.role === 'w8healer')) return { role: 'w8healer', body: require('./defense').healBody(room.energyCapacityAvailable, 25), mem };
  return null;
}
// self-sufficient = own spawn + a miner + a hauler alive (conquest.js stops sending cqworkers/cqhaulers)
function selfSufficient() {
  // 10-20 19:5x (Misaki: the spawn move is W47N8-only, no home support): our own planned move (old spawn destroyed by
  // moveRun, phase 'build') is not a lost room -> home must not send cqminers/cqworkers (it sent 2+5 = 9.5k e on 10-20)
  const mv = Memory.ops && Memory.ops.w8move; if (mv && mv.phase === 'build' && mv.t0) return true;
  const r = Game.rooms[C.ROOM]; if (!r || !r.find(FIND_MY_SPAWNS).length) return false;
  return mine().some(c => c.memory.role === 'w8miner'); // Spawn2 + its own miner -> home stops cq pioneers/haulers (guard stays)
}
module.exports = { banking, BANK_HOLD, moveRun, moveReady, rampNeeded, homeWant, linkAt, linkRun, rampHold, swapTemp, energyOrder, ROOM: C.ROOM, spawnRun, layoutRun, towerRun, selfSufficient, bodyFor, rmLead8 };
