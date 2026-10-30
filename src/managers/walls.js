// Wall policy v4 phase (docs/DEFENSE_PLAN.md, layout.defense.policy.start; docs/RCL6.md R4). Single source of the wall phase:
//   off   rcl < 6 or no storage
//   bank  rcl >= 6, walls not started: spawn holds ONE upgrader so storage can reach START (storage never exceeded 2.3k
//         under supply-follows-demand, so `storage>=20000` was unreachable as written). ~11 e/t banked -> 20k in ~2k ticks.
//   build latched in room.memory.walls.started once storage >= START with no threat (or early: after novice end a hostile
//         PLAYER combat creep in the home room). Latched so a later dip below START never re-banks.
// Gate/wall sites + the hits-step budget read phase()==='build' (next roadmap step).
const START = 20000, NOVICE_END = Date.UTC(2026, 9, 27, 19, 33); // 2026-10-28 03:33 UTC+8
const COMBAT = ['attack', 'ranged_attack', 'work', 'claim'];
function playerCombat(room) {
  if (typeof FIND_HOSTILE_CREEPS === 'undefined') return false; // node unit tests without Game stubs
  return room.find(FIND_HOSTILE_CREEPS).some(h => h.owner.username !== 'Invader' && h.body.some(p => COMBAT.includes(p.type) && p.hits > 0));
}
// early start switched off: back to the normal schedule; drop unbuilt (<10% progress) planned barrier sites. Built structures untouched.
function unearly(room) {
  delete room.memory.walls; delete room.memory.defAlert;
  const P = plan().get(room.name); let n = 0;
  for (const s of (room.find(FIND_MY_CONSTRUCTION_SITES) || [])) {
    if ((s.structureType === STRUCTURE_RAMPART || s.structureType === STRUCTURE_WALL) && P && planned(P, s.pos.x, s.pos.y, s.structureType) && s.progress < 0.1 * s.progressTotal && s.remove() === OK) n++;
  }
  console.log(`WALLS early start cancelled ${room.name} t=${Game.time} sites removed=${n}`);
}
function phase(room) {
  const H = require('./home');
  if (room.memory.walls && room.memory.walls.why === 'threat' && !H.on('earlyWalls')) unearly(room);
  const m = room.memory.walls;
  if (m && m.started) return 'build';
  // approved early trigger (Misaki 2026-10-16 "先等，来到隔壁再修"): a player combat squad adjacent (defAlert) or inside -> start now, any RCL
  if (H.on('earlyWalls') && (H.alert(room) || H.active(room))) { room.memory.walls = { started: Game.time, why: 'threat', fund: 0, ft: Game.time }; console.log(`WALLS start ${room.name} t=${Game.time} why=threat`); return 'build'; }
  if (room.controller.level < 6 || !room.storage) return 'off';
  const calm = !require('./threat').holding(room.name) && !room.find(FIND_HOSTILE_CREEPS).length;
  const early = Date.now() >= NOVICE_END && playerCombat(room);
  // Misaki 2026-10-17: walls are LOW priority after RCL6 — no banking / barrier sites until the road plan (managers/roads.js,
  // docs/ROADS.md) is done. Emergency starts (earlyWalls threat above, post-novice player attack) still win.
  if (!early && !require('./roads').done()) return 'roads';
  if ((room.storage.store[RESOURCE_ENERGY] >= START && calm) || early) {
    room.memory.walls = { started: Game.time, why: early ? 'player' : 'bank' };
    console.log(`WALLS start ${room.name} t=${Game.time} why=${room.memory.walls.why}`);
    return 'build';
  }
  return 'bank';
}

// ---- v4 barriers (layout.defense; docs/DEFENSE_PLAN.md). Everything below is inert unless phase()==='build'.
// Site order (policy.order): 6 gate ramparts -> with_gate trunk roads (TR, W, S) -> walls_in_build_order -> wall-phase repair spurs.
// At most SITE_CAP barrier-phase sites at once so they never crowd out core RCL sites (layout MAX_SITES 5 is shared).
const SITE_CAP = 2, WALL_CAP = 15; // walls: own cap, outside layout MAX_SITES (1 energy, 1 tick each; never crowd core sites)
function ringClosed(room, P) { const L = lists(P), rc = require('../utils/roomcache');
  return L.gates.every(([x, y]) => rc.at(room, x, y, STRUCTURE_RAMPART)) && L.walls.every(([x, y]) => rc.at(room, x, y, STRUCTURE_WALL)); }
const plan = () => require('../utils/plan');
function defense(P) { return P && P.raw && P.raw.defense; }
const memo = {};
function lists(P) {
  const name = P.raw.room; if (memo[name]) return memo[name];
  const d = defense(P), gates = [], walls = [], roads = [];
  for (const g of ['TR', 'TL', 'BR', 'W', 'S']) for (const t of (d.gates[g] || [])) gates.push(t);
  // trunk tiles under another planned structure are skipped: W trunk 30,30 is the ctl container; layout.js destroys a road there
  // as a conflict, so the wall phase re-placed it every ~5 min (live 00:44-01:04: built + destroyed 3x, 3 ruins, ~900e).
  const other = ([x, y]) => { const w = P.any && P.any[x * 50 + y]; return !!(w && w.type !== 'road'); };
  for (const g in d.trunks) if (d.trunks[g].mode === 'with_gate' || d.trunks[g].wallPhase) for // v5: BR/TL gate trunks (Misaki 02:38 no road to 44,27) after the ring
    (const t of d.trunks[g].new_tiles) if (!other(t)) roads.push(t);
  for (const t of d.walls_in_build_order) walls.push(t);
  for (const g in d.repair) { const r = d.repair[g]; if (/wall phase/.test(r.build_with || '')) for (const t of (r.spur || [])) roads.push(t); }
  const k = (x, y) => x * 50 + y, type = {};
  for (const [x, y] of gates) type[k(x, y)] = 'rampart';
  for (const [x, y] of roads) if (!type[k(x, y)]) type[k(x, y)] = 'road';
  for (const [x, y] of walls) type[k(x, y)] = STRUCTURE_WALL;
  // v5 (Misaki 2026-10-18 02:3x "光有城门没城墙…优先造城墙围起来"): ENCLOSE FIRST. gates -> all 41 walls (1 energy each, built at 1 hit;
  // tools/ring_check.py: flood-fill from exits never reaches the core once all 47 stand, every wall necessary) -> spur roads after the ring.
  const order = gates.map(t => [t, 'rampart']).concat(walls.map(t => [t, STRUCTURE_WALL]), roads.filter(([x, y]) => type[k(x, y)] === 'road').map(t => [t, 'road']));
  return (memo[name] = { gates, walls, order, type });
}
// Is (x,y) a barrier-phase tile of this structure type? (layout.js keeps these sites instead of removing them as off-plan)
function planned(P, x, y, t) { return !!defense(P) && lists(P).type[x * 50 + y] === t; }
// Hits steps per RCL (policy.hits); stepRule: raise ALL barriers to step k before any to k+1.
// v5: low first tiers so the fresh 1-hit ring gets real hits evenly before anything goes deep (10k = 100e per barrier)
const STEPS = { 6: [10000, 30000, 100000, 300000], 7: [10000, 30000, 100000, 300000, 1000000], 8: [10000, 30000, 100000, 300000, 1000000, 3000000] };
function barriers(room, P) {
  const L = lists(P), rc = require('../utils/roomcache'), out = [];
  for (const [x, y] of L.gates) { const s = rc.at(room, x, y, STRUCTURE_RAMPART); if (s) out.push(s); }
  for (const [x, y] of L.walls) { const s = rc.at(room, x, y, STRUCTURE_WALL); if (s) out.push(s); }
  return out;
}
// v5 rampart slack: ramparts decay 300/100t, so a gate topped up to exactly the step sank back under it ~100t later and the band
// pulled every builder across the map to it (live 03:40-03:55: 3 builders 6,28 -> 20,44 -> 26,15 -> 47,17 in lockstep, work 11% of
// ticks). A rampart counts as at-step within SLACK below it and is topped up to step + SLACK (~3300t of decay between top-ups).
const SLACK = 5000;
const eff = s => s.structureType === STRUCTURE_RAMPART ? s.hits + SLACK : s.hits;
function target(room, B) { // current step: the lowest step not yet reached by every built barrier
  const st = STEPS[Math.min(8, room.controller.level)] || [];
  if (!st.length || !B.length) return 0;
  const low = _.min(B.map(eff));
  return st.find(h => low < h) || st[st.length - 1];
}
// Budget (policy.budget): a fund in room.memory.walls.fund. The 20k bank that latched the phase is the opening fund (supply-follows-
// demand keeps storage near the floor afterwards, so a literal "storage<20k -> 0" would freeze the walls at 1 hit); it then accrues
// RATE x NET per tick (NET = model net income ~23 e/t) and builder repairs debit it. queen.storageFloor adds the fund, so the ctl
// ferry / upgrader extras never spend it. Threat (remote holding or hostile player in home): cap lifted, storage reserve still kept.
const NET = 23, FUND_MAX = 50000;
function rate(room) {
  const e = room.storage ? room.storage.store[RESOURCE_ENERGY] : 0;
  if (room.controller.level >= 8 || e >= 150000) return 0.35;
  return e >= 50000 ? 0.20 : 0.10;
}
function fund(room) {
  const m = room.memory.walls; if (!m || !m.started) return 0;
  if (m.fund === undefined) { m.fund = START; m.ft = Game.time; }
  if (Game.time > (m.ft || Game.time)) { m.fund = Math.min(FUND_MAX, m.fund + (Game.time - m.ft) * rate(room) * NET); m.ft = Game.time; }
  return m.fund;
}
// v5 (Misaki 02:2x "storage can go down to ~5k while the ring closes"): during the wall phase the spendable budget is the fund OR
// storage above FLOOR, whichever is larger (upgrading is held, so storage surplus is wall energy).
const FLOOR = 5000;
// Peacetime fund-backed wall step (strategy 17:4x post W47N9 abort): when walls.fund wants the next STEP and there is no
// remote/home player threat, treat the fund as spendable even under reserveE (same 5k tower cushion as siege). Without this,
// supply-follows-demand pins storage at reserveE, budgetE/pickSource freeze, and walls stay stuck at STEP 142101 despite
// fund=50k (live 10-29 after 2523dd6: builder spawned on a blip then starved waiting_feed).
function fundSpend(room) {
  if (!room || !room.storage || !room.name || !room.memory) return false;
  if (typeof FIND_HOSTILE_CREEPS === 'undefined') return false; // node unit tests without Game stubs
  if (siege(room)) return false; // siege path already lifts the gates
  if (threat(room)) return false; // Invader/player pressure: keep banking at reserveE
  if (fund(room) < 3000) return false;
  const P = plan().get(room.name);
  if (!defense(P) || phase(room) !== 'build') return false;
  const B = barriers(room, P), tgt = target(room, B);
  if (!tgt || stepHeld(room, tgt)) return false;
  return B.some(s => eff(s) < tgt);
}
function budgetE(room) {
  const e = room.storage ? room.storage.store[RESOURCE_ENERGY] : 0;
  if (defLow(room) && !fundSpend(room)) return 0;
  const floor = fundSpend(room) ? FLOOR : Math.max(FLOOR, defReserve());
  return Math.max(fund(room), e - floor);
}
// v5 hit floor (Misaki 02:29 "no red 1-hit walls"): while any barrier is below FLOOR_HITS the repair job outranks road sites.
const FLOOR_HITS = 10000;
function belowFloor(room) { const P = plan().get(room.name); if (!defense(P) || phase(room) !== 'build') return false;
  return barriers(room, P).some(s => eff(s) < FLOOR_HITS); }
// Defense energy reserve (10-18 10:41, BustJetter 18 combat creeps massed in W48N9): console switch Memory.defense.reserveE.
// While storage < reserveE: no builders, no upgraders (downgrade safety excepted), builders never draw hub/storage, so all income
// banks into storage for towers. Remove the key (or 0) to lift. defLow(room) = switch on and storage below it.
function defReserve() { return (typeof Memory !== 'undefined' && Memory.defense && Memory.defense.reserveE) || 0; }
function defLow(room) { const d = defReserve(); return !!d && (!room.storage || room.storage.store[RESOURCE_ENERGY] < d); }
function spend(room, e) { const m = room.memory.walls; if (m && m.fund !== undefined) m.fund = Math.max(0, m.fund - e); }
// Siege exemption (strategy review 2026-10-19 20:5x; Misaki doctrine "builders repair attacked walls" + "reserve floors may be
// spent for defense"): with a hostile PLAYER combat creep inside the home room the reserveE gates (no builders under reserve+2k,
// builders take nothing under reserveE) are lifted for ONE builder, which may draw storage down to storeFloor (5k, tower cushion).
// Without this, storage hovering at 15-17k (normal under supply-follows-demand) meant no builder at all during an attack.
function siege(room) { return !!room && typeof FIND_HOSTILE_CREEPS !== 'undefined' && playerCombat(room); }
function threat(room) { return require('./threat').holding(room.name) || playerCombat(room) || require('./home').alert(room); }
// Storage energy the ctl ferry / upgrader extras must leave alone.
function reserved(room) { const m = room.memory && room.memory.walls; return m && m.started && room.storage ? Math.min(fund(room), room.storage.store[RESOURCE_ENERGY]) : 0; }
// Step hold:
// - RCL < 7 (Misaki 2026-10-19 20:51): peacetime max HOLD_STEP 100k; RCL7 opened 300k via fundSpend.
// - RCL ≥ 7 (strategy 08:4x): peacetime max HOLD_STEP_RCL7 300k. Without this, fundSpend auto-opens STEPS 1M
//   (~287k e for 41 walls) the tick 300k lands and keeps home upgrade crushed. Roadmap puts barriers→1M after
//   colony RCL7 / soft ramps / minerals. Overmind analog: barrierHits[7]=1M but fortifyDutyThreshold=500k energy
//   before routine fortify — we hold the step instead (storage still ~15k). Console resume:
//   Memory.defense.pushBarrier = true (or any truthy). Threat/siege still repairs past the hold.
const HOLD_STEP = 100000, HOLD_BELOW_RCL = 7, HOLD_STEP_RCL7 = 300000;
const heldC = {}; // per room per tick: { t, v }
function pushBarrier() {
  return !!(typeof Memory !== 'undefined' && Memory.defense && Memory.defense.pushBarrier);
}
function stepHeld(room, tgt) {
  if (!room || !room.controller) return false;
  if (tgt === undefined) {
    const c = heldC[room.name]; if (typeof Game !== 'undefined' && c && c.t === Game.time) return c.v;
    const P = plan().get(room.name);
    tgt = defense(P) && phase(room) === 'build' ? target(room, barriers(room, P)) : 0;
    const v = stepHeld(room, tgt);
    if (typeof Game !== 'undefined') heldC[room.name] = { t: Game.time, v };
    return v;
  }
  if (threat(room) || pushBarrier()) return false;
  if (room.controller.level < HOLD_BELOW_RCL) return tgt > HOLD_STEP;
  return tgt > HOLD_STEP_RCL7;
}
// Builder repair job: lowest barrier below the step target, capped at +CHUNK so the set rises evenly. null = no work / no budget.
const CHUNK = 10000;
// v5 proximity: among barriers in the lowest band (hits < min + CHUNK, so the set still rises evenly) take the one nearest to the
// builder that no other builder holds (pos/taken optional). The old global-min pick walked builders across the map (NW <-> S <-> E).
function repairJob(room, pos, taken) {
  const P = plan().get(room.name);
  if (!defense(P) || phase(room) !== 'build') return null;
  if (!threat(room) && budgetE(room) < 100) return null;
  const B = barriers(room, P), tgt = target(room, B);
  const low = B.filter(s => eff(s) < tgt); if (!low.length) return null;
  if (stepHeld(room, tgt)) return null;
  const m = _.min(low.map(eff)), band = low.filter(x => eff(x) < m + CHUNK);
  // all of the band held -> next free barrier below the step before doubling up (5 builders on one 1-tick top-up walked in a pack)
  const fr = a => taken ? a.filter(x => !taken.has(x.id)) : a, free = fr(band), pool = free.length ? free : fr(low).length ? fr(low) : band;
  const s = pos && pos.getRangeTo ? _.min(pool, x => (x.pos && x.pos.roomName === pos.roomName ? pos.getRangeTo(x) : 99) * 1e7 + eff(x)) : _.min(pool, eff);
  const top = s.structureType === STRUCTURE_RAMPART ? tgt + SLACK : tgt;
  return { id: s.id, cap: Math.min(top, s.hits + CHUNK) };
}
// Ramparts are built at 1 hit and decay 300 / 100t. While barrier sites keep builders busy (sites outrank repair) repairJob never
// runs, so gates rot: live 00:37-01:09 TL gate 25,16 built + decayed 3x, 47,17 4.2k->3.0k unrepaired. A gate below DECAY_FLOOR
// (~1600t of life) outranks sites; the builder lifts it to DECAY_CAP before going back to sites.
const DECAY_FLOOR = 5000, DECAY_CAP = 10000;
function decaying(room, taken) {
  const P = plan().get(room.name);
  if (!defense(P) || phase(room) !== 'build') return null;
  const low = barriers(room, P).filter(s => s.structureType === STRUCTURE_RAMPART && s.hits < DECAY_FLOOR && !(taken && taken.has(s.id)));
  return low.length ? _.min(low, s => s.hits) : null;
}
// Spawn: one builder while there is repair work and >= one builder-life of fund (5W x 1500t would spend at most 7.5k).
function wantBuilder(room) { const j = repairJob(room); return !!j && (threat(room) || budgetE(room) >= 3000); }
// Sites (called by layout.run with its leftover budget).
function placeSites(room, budget) {
  const P = plan().get(room.name);
  if (!defense(P) || phase(room) !== 'build') return [];
  const rc = require('../utils/roomcache'), L = lists(P), log = [];
  const mine = rc.sites(room).filter(s => planned(P, s.pos.x, s.pos.y, s.structureType));
  let n = Math.min(budget, SITE_CAP - mine.filter(s => s.structureType !== STRUCTURE_WALL).length);
  let nw = WALL_CAP - mine.filter(s => s.structureType === STRUCTURE_WALL).length;
  const closed = ringClosed(room, P);
  // threat start: west gate (6,28) + west wall x=6 first (the side the squad faces), then the normal order
  const west = ([[x]]) => x <= 6 ? 0 : 1, order = room.memory.walls.why === 'threat' ? L.order.slice().sort((a, b) => west(a) - west(b)) : L.order;
  for (const [[x, y], t] of order) {
    if (n <= 0 && nw <= 0) break;
    if (t === 'road' && !closed) break; // spur roads only once the ring is sealed
    if (t === STRUCTURE_WALL ? nw <= 0 : n <= 0) continue;
    if (rc.at(room, x, y, t) || room.lookForAt(LOOK_CONSTRUCTION_SITES, x, y).length) continue;
    const r = room.createConstructionSite(x, y, t);
    if (r === OK) { if (t === STRUCTURE_WALL) nw--; else n--; log.push(`site ${t} ${x},${y}`); }
    else if (!(room.memory.walls.bad || (room.memory.walls.bad = {}))[x * 50 + y]) { room.memory.walls.bad[x * 50 + y] = r; log.push(`FAIL ${t} ${x},${y} r=${r}`); }
  }
  return log;
}
// Misaki 2026-10-17 21:00 "先停止升级，全力基建": while the road plan runs (phase 'roads') spawn NO upgrader and send no
// energy to the controller. Safety: ticksToDowngrade < UP_SAFE -> 1 minimal upgrader again. Memory.roads.upgrade=1 overrides.
const UP_SAFE = 20000;
function noUpgrade(room) {
  const c = room && room.controller;
  if (!c || !c.my || c.level < 6 || c.level >= 8) return false;
  if ((Memory.roads || {}).upgrade) return false;
  if ((c.ticksToDowngrade || 0) < UP_SAFE) return false;
  const ph = phase(room);
  if (ph === 'roads') return true;
  // Misaki 10-18 09:30 mineral line "spend storage on infrastructure fast, keep ~5k": while terminal/lab/extractor sites are open,
  // upgrading is held and the ctl feed goes to builders (downgrade safety above still wins). The ~5k is kept by the builder storage
  // floor (9edf999), not here: releasing the hold at storage <= FLOOR (27ab37b) let the queen ferry storage to the controller down
  // to 2.3k and spawn an upgrader that recycles once storage passes 5k again (live 10:39: 4.3k -> 2.9k, builders starved at the floor).
  if (room.storage && require('../utils/roomcache').sites(room).some(s => s.structureType === 'terminal' || s.structureType === 'lab' || s.structureType === 'extractor')) return true;
  // v5 (Misaki 2026-10-18 02:2x "基建效率最大，升级不是优先"): wall build phase holds upgrading too (ctl container/link feed ->
  // builders) until every barrier stands at >= HOLD_TO hits; then normal upgrading resumes.
  if (ph !== 'build') return false;
  const P = plan().get(room.name); if (!defense(P)) return false;
  const B = barriers(room, P); return !ringClosed(room, P) || !B.length || _.min(B.map(eff)) < HOLD_TO;
}
const HOLD_TO = 100000;
module.exports = { stepHeld, HOLD_STEP, HOLD_STEP_RCL7, siege, fundSpend, defReserve, defLow, SLACK, FLOOR_HITS, belowFloor, FLOOR, budgetE, WALL_CAP, ringClosed, UP_SAFE, DECAY_FLOOR, DECAY_CAP, decaying, noUpgrade, START, NOVICE_END, phase, planned, STEPS, target, barriers, fund, spend, reserved, repairJob, wantBuilder, placeSites, lists };
