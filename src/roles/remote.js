// Remote roles: rminer (sits on container, repairs it), rhauler (container -> home via hauler delivery), reserver.
const move = require('../utils/move'), remote = require('../managers/remote'), threat = require('../managers/threat');
// cross-room travel through fixed exits; returns true when in range of target
function go(c, room, x, y, range) {
  const C = remote.CFG[c.memory.remote];
  if (c.room.name === room) {
    // just crossed: step off the border first
    if (c.pos.x === 0 || c.pos.x === 49 || c.pos.y === 0 || c.pos.y === 49) { delete c.memory._m; c.move(c.pos.x === 0 ? RIGHT : c.pos.x === 49 ? LEFT : c.pos.y === 0 ? BOTTOM : TOP); return false; }
    return move.to(c, x, y, range);
  }
  const [ex, ey] = c.room.name === C.home ? C.exitHome : C.exitRemote;
  if (c.pos.x === ex && c.pos.y === ey) { c.move(ex === 49 ? RIGHT : LEFT); return false; }
  move.to(c, ex, ey, 0); return false;
}
// Paused remote: at home the creep works with the home role that matches its body (reads the threat state only via remote.paused)
// pure rule (tests/remote_fixes.js): urgent <30k; batch <50k when full; free repair <100k while the source regenerates
const REP = { urgent: 30000, batch: 50000, idle: 100000 };
function repairNow(hits, free, perHarvest, srcEmpty) {
  return hits < REP.urgent || (hits < REP.batch && free < perHarvest) || (srcEmpty && hits < REP.idle);
}
const HOME = { rhauler: 'hauler', rminer: 'builder' };
function flee(c) {
  const C = remote.CFG[c.memory.remote];
  if (c.room.name === C.home && c.pos.x > 1 && c.pos.x < 48) {
    if (HOME[c.memory.role]) { c.memory.home = C.home; return require('./index')[HOME[c.memory.role]].run(c); }
    const [px, py] = C.park || [33, 26]; require('../utils/trace').why(c, 't'); return move.to(c, px, py, 1); }
  const [px, py] = C.park || [33, 26]; go(c, C.home, px, py, 1);
}
const roles = {
  rminer(c) {
    const C = remote.CFG[c.memory.remote]; if (remote.paused(c.memory.remote, 'rminer')) return flee(c);
    // travel = ticks to reach range 1 of the container (the old miner still sits on it; measuring on the tile itself
    // added the wait: 83654755 adjacent at ~+65, on tile +130 -> lead drifting to the 160 cap, ~50-100t overlap)
    if (c.memory.travel === undefined && c.ticksToLive && c.room.name === c.memory.remote && c.pos.isNearTo(C.cont[0], C.cont[1])) { const t = 1500 - c.ticksToLive; c.memory.travel = t >= 0 && t <= 300 ? t : 110; }
    if (!go(c, c.memory.remote, C.cont[0], C.cont[1], 0)) return;
    const src = c.room.lookForAt(LOOK_SOURCES, C.src[0], C.src[1])[0];
    const k = c.room.lookForAt(LOOK_STRUCTURES, C.cont[0], C.cont[1]).find(s => s.structureType === STRUCTURE_CONTAINER);
    // Unowned-room containers decay 50 hits/t; keep >=100k so it survives a ~1500-tick threat pause with nobody repairing
    // (30k lasted only 600 ticks: container lost during the 2026-10-13 Invader pause). Steady-state cost is the same (= decay).
    // Repair vs harvest (W45N8 review 2026-10-16): repair blocks harvest in the same tick. Urgent <30k: repair first.
    // <50k: batch — harvest until the store is full, then repair. Source empty (regen wait): repair for free up to 100k.
    if (k && c.store[RESOURCE_ENERGY] >= 10 && repairNow(k.hits, c.store.getFreeCapacity(), 2 * c.getActiveBodyparts(WORK), !src || src.energy === 0)) return c.repair(k);
    if (!k) { const s = c.room.lookForAt(LOOK_CONSTRUCTION_SITES, C.cont[0], C.cont[1])[0];
      if (!s) c.room.createConstructionSite(C.cont[0], C.cont[1], STRUCTURE_CONTAINER);
      // harvest and build share a tick: build only when the next harvest would overflow the store (or source empty)
      // -> ~25 built per 3.5 ticks = 7.1/t (was 5/t: building every 10 harvested)
      else if (c.store[RESOURCE_ENERGY] > 0 && (c.store.getFreeCapacity() < 2 * c.getActiveBodyparts(WORK) || !src || src.energy === 0)) return c.build(s); }
    if (src && src.energy > 0) c.harvest(src);
  },
  rhauler(c) {
    const C = remote.CFG[c.memory.remote]; if (remote.paused(c.memory.remote, 'rhauler')) return flee(c);
    if (c.memory.working && !c.memory.full && c.room.name === C.home && c.store[RESOURCE_ENERGY] > 0) return require('./hauler').run(c); // finish a home job after a pause
    c.memory.working = false;
    if (!c.memory.full && c.store.getFreeCapacity() === 0) { c.memory.full = true; c.memory.load = c.store[RESOURCE_ENERGY]; }
    if (c.memory.full && c.store[RESOURCE_ENERGY] === 0) { c.memory.full = false; c.memory.trips = (c.memory.trips || 0) + 1;
      const m = remote.mem(c.memory.remote); m.delivered = (m.delivered || 0) + (c.memory.load || 0); c.memory.load = 0; }
    if (c.memory.full) {
      if (c.memory.dep && c.room.name === C.home && c.pos.x < 48) { c.memory.rt = Game.time - c.memory.dep; delete c.memory.dep; } // measured round trip
      if (c.room.name !== C.home || c.pos.x >= 48) return go(c, C.home, 40, 20, 5);
      c.memory.working = true; require('./hauler').run(c); return;
    }
    if (c.room.name === C.home && c.store[RESOURCE_ENERGY] > 0 && c.store[RESOURCE_ENERGY] < 50) { c.memory.working = true; return require('./hauler').run(c); }
    // remote container gone (Invader / decay; rminer rebuilding it): nothing to collect -> haul at home until it exists (10-13: 2 rhaulers 100% idle)
    const R = Game.rooms[c.memory.remote];
    if (R && c.store[RESOURCE_ENERGY] === 0 && !R.lookForAt(LOOK_STRUCTURES, C.cont[0], C.cont[1]).some(s => s.structureType === STRUCTURE_CONTAINER)
      && !R.find(FIND_DROPPED_RESOURCES).some(r => r.amount >= 100)) return flee(c);
    // too old for another round trip (2026-10-16: rhaulers died at the home exit holding 400/296): work at home, recycle when empty
    const S = require('../utils/salvage');
    if (c.room.name === C.home && c.ticksToLive && c.ticksToLive < (c.memory.rt || 200) + 40) { c.memory.home = C.home; return require('./hauler').run(c); }
    if (c.room.name === C.home && !c.memory.dep) c.memory.dep = Game.time;
    if (c.room.name === c.memory.remote && c.pos.x > 0 && c.pos.x < 49) { const sv = S.pick(c); if (sv) { if (move.to(c, sv.pos.x, sv.pos.y, 1)) S.take(c, sv); return; } }
    if (!go(c, c.memory.remote, C.cont[0], C.cont[1], 1)) return;
    const drop = c.pos.findInRange(FIND_DROPPED_RESOURCES, 2).find(r => r.resourceType === RESOURCE_ENERGY && r.amount >= 30);
    if (drop) { if (c.pickup(drop) === ERR_NOT_IN_RANGE) c.moveTo(drop); return; }
    const k = c.room.lookForAt(LOOK_STRUCTURES, C.cont[0], C.cont[1]).find(s => s.structureType === STRUCTURE_CONTAINER);
    if (k && k.store[RESOURCE_ENERGY] >= 50) c.withdraw(k, RESOURCE_ENERGY);
    else if (c.store[RESOURCE_ENERGY] >= c.store.getCapacity() * 0.6 && (!k || k.store[RESOURCE_ENERGY] < 50) && (c.memory.wait = (c.memory.wait || 0) + 1) > 30) { c.memory.full = true; c.memory.load = c.store[RESOURCE_ENERGY]; c.memory.wait = 0; }
  },
  reserver(c) {
    const C = remote.CFG[c.memory.remote]; if (remote.paused(c.memory.remote)) return flee(c);
    if (!go(c, c.memory.remote, C.ctl[0], C.ctl[1], 1)) return;
    const ct = c.room.controller; if (!ct) return;
    if (ct.reservation && ct.reservation.username !== c.owner.username) return; // never attackController
    c.reserveController(ct);
    const S = require('../utils/sign'); if (S.needs(ct, c.owner.username)) c.signController(ct, S.SIGN);
  },
};
// Anti-NPC defender (docs/DEFENDER.md). Spawned on demand only; engages owner 'Invader' only; kites melee at range 3;
// retreats home (<60% hp: tower heals it) or when a player combat creep / an Invader healer shows up; recycles when done.
// melee NPC: kite with utils/kite (terrain-aware escape room, prefers range 3)
// opt.approaching: target closed in since last tick (kite holds at >=4 off swamp); c.memory.kd = last step (direction inertia)
function kite(c, t, flee, approaching) { const d = require('../utils/kite').step(c, t, flee, remote.CFG[c.memory.remote].exitRemote, { approaching, last: c.memory.kd });
  c.memory.kd = d || undefined; if (d) c.move(d); }
const meleeOf = h => h.body.some(p => p.type === ATTACK && p.hits > 0);
const rangedOf = h => h.body.some(p => p.type === RANGED_ATTACK && p.hits > 0);
roles.defender = function (c) {
  // Reads the FSM only (managers/threat.js); never decides about players/escalation itself.
  const rm = c.memory.remote, C = remote.CFG[rm], th = threat.state(rm), K = threat.cfg(rm);
  if (c.hits < c.hitsMax) c.heal(c);
  const here = c.room.name === rm;
  const inv = here ? c.room.find(FIND_HOSTILE_CREEPS).filter(h => h.owner.username === 'Invader') : [];
  const mine = th.def === c.name, edge = c.pos.x === 0 || c.pos.x === 49 || c.pos.y === 0 || c.pos.y === 49;
  c.memory.recycle = !mine || (th.st !== threat.S.DEFEND && th.st !== threat.S.THREAT) || c.ticksToLive < 80; // recomputed each tick: a returning defender can be reused by a new THREAT
  if (c.hits < c.hitsMax * K.hp) c.memory.hurt = true; else if (c.hits >= c.hitsMax * K.hpBack) c.memory.hurt = false;
  if (c.memory.recycle || c.memory.hurt) {
    delete c.memory.lk;
    const t = inv.find(h => c.pos.inRangeTo(h, 3)); if (t) c.rangedAttack(t);
    // a melee Invader within 3 (e.g. camping the exit): get clear first; pathing home now walks into it (2026-10-15 death).
    // Exception: one step from the exit tile -> stepping onto it leaves the room this tick.
    const m = here && !edge && inv.find(h => meleeOf(h) && c.pos.inRangeTo(h, 3));
    if (m && !c.pos.inRangeTo(C.exitRemote[0], C.exitRemote[1], 1)) return kite(c, m, true);
    if (c.room.name !== C.home || c.pos.x >= 48) { const sp = Game.spawns[C.spawn || 'Spawn1']; return go(c, C.home, sp ? sp.pos.x : 35, sp ? sp.pos.y : 28, 1); }
    if (c.memory.hurt && !c.memory.recycle) { const [px, py] = C.park || [33, 26]; return move.to(c, px, py, 1); } // tower heals it
    const sp = c.pos.findClosestByRange(FIND_MY_SPAWNS); if (!sp) return;
    if (c.pos.isNearTo(sp)) { threat.noteRecycle(rm, c.name); sp.recycleCreep(c); } else move.to(c, sp.pos.x, sp.pos.y, 1);
    return;
  }
  // on an exit tile with an Invader within 4 (exit campers): fight from here instead of blindly stepping toward the container
  if (!here || (edge && !inv.some(h => c.pos.inRangeTo(h, 4)))) return go(c, rm, C.cont[0], C.cont[1], 2);
  const t = c.pos.findClosestByRange(inv);
  // after a kill (FSM still DEFEND for clearTicks): hold at the kill spot (tombstone stays covered), don't walk to the container
  if (!t) { if (c.memory.lk) return; return move.to(c, C.cont[0], C.cont[1], 2); }
  c.memory.lk = [t.pos.x, t.pos.y];
  const r = c.pos.getRangeTo(t), prev = c.memory.kr || 99;
  if (r <= 3) c.rangedAttack(t);
  // pure ranged target (no ATTACK): kiting only gives it free shots — close to range 3 and trade (we out-heal/out-damage small ones)
  if (rangedOf(t) && !meleeOf(t)) { c.memory.kr = r; if (r > 3) { delete c.memory._m; c.moveTo(t, { range: 3, reusePath: 0, maxRooms: 1, plainCost: 2, swampCost: 10 }); } return; }
  // melee target (it chases us): within 8 let it come and hold range 3 (utils/kite); moveTo would walk into swamp -> 5-tick lock -> melee.
  // If it stops coming (busy elsewhere / wall in the way: range 4-8 not shrinking for 10 ticks), approach normally.
  c.memory.kw = r > 3 && r <= 8 && r >= (c.memory.kr || 99) ? (c.memory.kw || 0) + 1 : 0; c.memory.kr = r;
  if (meleeOf(t) && r <= 8 && c.memory.kw <= 10) return kite(c, t, false, r < prev);
  if (r > 3) { delete c.memory._m; c.moveTo(t, { range: 3, reusePath: 0, maxRooms: 1, plainCost: 2, swampCost: 10 }); }
};
module.exports = { repairNow, rminer: { run: roles.rminer }, rhauler: { run: roles.rhauler }, reserver: { run: roles.reserver }, defender: { run: roles.defender } };
