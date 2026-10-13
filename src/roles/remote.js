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
function flee(c) {
  const C = remote.CFG[c.memory.remote];
  if (c.room.name === C.home && c.pos.x > 1 && c.pos.x < 48) { if (c.store && c.store[RESOURCE_ENERGY] > 0 && c.memory.role === 'rhauler') { c.memory.working = true; return require('./hauler').run(c); } const [px, py] = C.park || [33, 26]; return move.to(c, px, py, 1); }
  const [px, py] = C.park || [33, 26]; go(c, C.home, px, py, 1);
}
const roles = {
  rminer(c) {
    const C = remote.CFG[c.memory.remote]; if (remote.paused(c.memory.remote)) return flee(c);
    if (!go(c, c.memory.remote, C.cont[0], C.cont[1], 0)) return;
    const src = c.room.lookForAt(LOOK_SOURCES, C.src[0], C.src[1])[0];
    const k = c.room.lookForAt(LOOK_STRUCTURES, C.cont[0], C.cont[1]).find(s => s.structureType === STRUCTURE_CONTAINER);
    // Unowned-room containers decay 50 hits/t; keep >=100k so it survives a ~1500-tick threat pause with nobody repairing
    // (30k lasted only 600 ticks: container lost during the 2026-10-13 Invader pause). Steady-state cost is the same (= decay).
    if (k && k.hits < 100000 && c.store[RESOURCE_ENERGY] >= 10) return c.repair(k);
    if (!k) { const s = c.room.lookForAt(LOOK_CONSTRUCTION_SITES, C.cont[0], C.cont[1])[0];
      if (!s) c.room.createConstructionSite(C.cont[0], C.cont[1], STRUCTURE_CONTAINER);
      // harvest and build share a tick: build only when the next harvest would overflow the store (or source empty)
      // -> ~25 built per 3.5 ticks = 7.1/t (was 5/t: building every 10 harvested)
      else if (c.store[RESOURCE_ENERGY] > 0 && (c.store.getFreeCapacity() < 2 * c.getActiveBodyparts(WORK) || !src || src.energy === 0)) return c.build(s); }
    if (src && src.energy > 0) c.harvest(src);
  },
  rhauler(c) {
    const C = remote.CFG[c.memory.remote]; if (remote.paused(c.memory.remote)) return flee(c);
    if (!c.memory.full && c.store.getFreeCapacity() === 0) { c.memory.full = true; c.memory.load = c.store[RESOURCE_ENERGY]; }
    if (c.memory.full && c.store[RESOURCE_ENERGY] === 0) { c.memory.full = false; c.memory.trips = (c.memory.trips || 0) + 1;
      const m = remote.mem(c.memory.remote); m.delivered = (m.delivered || 0) + (c.memory.load || 0); c.memory.load = 0; }
    if (c.memory.full) {
      if (c.room.name !== C.home || c.pos.x >= 48) return go(c, C.home, 40, 20, 5);
      c.memory.working = true; require('./hauler').run(c); return;
    }
    if (c.room.name === C.home && c.store[RESOURCE_ENERGY] > 0 && c.store[RESOURCE_ENERGY] < 50) { c.memory.working = true; return require('./hauler').run(c); }
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
  },
};
// Anti-NPC defender (docs/DEFENDER.md). Spawned on demand only; engages owner 'Invader' only; kites melee at range 3;
// retreats home (<60% hp: tower heals it) or when a player combat creep / an Invader healer shows up; recycles when done.
const OPP = { 1: 5, 2: 6, 3: 7, 4: 8, 5: 1, 6: 2, 7: 3, 8: 4 };
roles.defender = function (c) {
  // Reads the FSM only (managers/threat.js); never decides about players/escalation itself.
  const rm = c.memory.remote, C = remote.CFG[rm], th = threat.state(rm), K = threat.cfg(rm);
  if (c.hits < c.hitsMax) c.heal(c);
  const here = c.room.name === rm;
  const inv = here ? c.room.find(FIND_HOSTILE_CREEPS).filter(h => h.owner.username === 'Invader') : [];
  const mine = th.def === c.name;
  c.memory.recycle = !mine || (th.st !== threat.S.DEFEND && th.st !== threat.S.THREAT) || c.ticksToLive < 80; // recomputed each tick: a returning defender can be reused by a new THREAT
  if (c.hits < c.hitsMax * K.hp) c.memory.hurt = true; else if (c.hits >= c.hitsMax * K.hpBack) c.memory.hurt = false;
  if (c.memory.recycle || c.memory.hurt) {
    const t = inv.find(h => c.pos.inRangeTo(h, 3)); if (t) c.rangedAttack(t);
    if (c.room.name !== C.home || c.pos.x >= 48) { const sp = Game.spawns[C.spawn || 'Spawn1']; return go(c, C.home, sp ? sp.pos.x : 35, sp ? sp.pos.y : 28, 1); }
    if (c.memory.hurt && !c.memory.recycle) { const [px, py] = C.park || [33, 26]; return move.to(c, px, py, 1); } // tower heals it
    const sp = c.pos.findClosestByRange(FIND_MY_SPAWNS); if (!sp) return;
    if (c.pos.isNearTo(sp)) { threat.noteRecycle(rm, c.name); sp.recycleCreep(c); } else move.to(c, sp.pos.x, sp.pos.y, 1);
    return;
  }
  if (!here || c.pos.x === 0 || c.pos.x === 49 || c.pos.y === 0 || c.pos.y === 49) return go(c, rm, C.cont[0], C.cont[1], 2);
  const t = c.pos.findClosestByRange(inv);
  if (!t) return move.to(c, C.cont[0], C.cont[1], 2);
  const r = c.pos.getRangeTo(t);
  if (r <= 3) c.rangedAttack(t);
  const melee = t.body.some(p => p.type === ATTACK && p.hits > 0);
  if (r > 3) { delete c.memory._m; c.moveTo(t, { range: 3, reusePath: 0, maxRooms: 1 }); }
  else if (melee && r <= 2) {
    // kite: best of 8 neighbours by (range from target, not swamp, open space) — never kite into a swamp or a corner
    const T = c.room.getTerrain(); let best = 0, bs = -1e9;
    for (let k = 1; k <= 8; k++) {
      const [dx, dy] = [[0, 0], [0, -1], [1, -1], [1, 0], [1, 1], [0, 1], [-1, 1], [-1, 0], [-1, -1]][k];
      const x = c.pos.x + dx, y = c.pos.y + dy;
      if (x < 1 || x > 48 || y < 1 || y > 48 || T.get(x, y) === TERRAIN_MASK_WALL) continue;
      let open = 0; for (let i = -1; i <= 1; i++) for (let j = -1; j <= 1; j++) if (T.get(x + i, y + j) !== TERRAIN_MASK_WALL) open++;
      const sc = Math.max(Math.abs(x - t.pos.x), Math.abs(y - t.pos.y)) * 10 - (T.get(x, y) === TERRAIN_MASK_SWAMP ? 25 : 0) + open;
      if (sc > bs) { bs = sc; best = k; }
    }
    if (best) c.move(best);
  }
};
module.exports = { rminer: { run: roles.rminer }, rhauler: { run: roles.rhauler }, reserver: { run: roles.reserver }, defender: { run: roles.defender } };
