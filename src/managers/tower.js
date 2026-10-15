// Towers: attack closest hostile, heal own creeps, repair planned roads/containers (<60%) and ramparts up to target.
// Off-plan leftovers (old v1 roads, 31,11 container) are left to decay. Repair target chosen every 10 ticks.
// Rampart top-up only while storage holds the defender reserve (threat.reserve): tower refills for the 16 RCL4 ramparts
// (~4k energy to 50k) competed with spawn refills and storage fell 1040 -> 200 (10-14 02:45), no 1300 for a defender. Below it only
// ramparts under RAMPART_FLOOR are repaired, so fresh ramparts (1 hit, decay 300/100t) never die.
const plan = require('../utils/plan'), rc = require('../utils/roomcache');
const RAMPART_TARGET = [0, 0, 0, 20000, 50000, 100000, 300000, 1000000, 3000000], RAMPART_FLOOR = 5000;
// Growth throttle: a rampart already above the previous RCL's target is only "growing" -> repair it every 5th tick (<= 2 e/t per
// tower). At RCL5, 2 towers x 10 e/t would pour ~10.6k energy (17 ramparts 50k->100k) into walls while tower/extension sites
// and upgraders need it (docs/RCL5.md). Fresh/damaged ramparts below the previous target still get full speed.
function growthPaused(s, rcl, time) {
  const prev = RAMPART_TARGET[Math.max(0, rcl - 1)];
  return s.structureType === STRUCTURE_RAMPART && prev > 0 && s.hits >= prev && time % 5 !== 0;
}
module.exports = { growthPaused, run(room) {
  const towers = rc.all(room, STRUCTURE_TOWER);
  if (!towers.length) return;
  const hostiles = room.find(FIND_HOSTILE_CREEPS);
  if (hostiles.length) { for (const t of towers) t.attack(t.pos.findClosestByRange(hostiles)); return; }
  const mem = room.memory;
  if (Game.time % 10 === 0) {
    const P = plan.get(room.name), st = room.storage;
    const funded = !st || st.store[RESOURCE_ENERGY] >= require('./threat').reserve(room.name);
    const target = funded ? RAMPART_TARGET[room.controller.level] : Math.min(RAMPART_FLOOR, RAMPART_TARGET[room.controller.level]);
    const hurt = room.find(FIND_MY_CREEPS).find(c => c.hits < c.hitsMax);
    mem.towerHeal = hurt ? hurt.id : undefined;
    const cand = rc.all(room, STRUCTURE_RAMPART).filter(s => s.hits < target && plan.rampartWanted(P, room, s.pos.x, s.pos.y))
      .concat(rc.all(room, STRUCTURE_ROAD).concat(rc.all(room, STRUCTURE_CONTAINER))
        .filter(s => P.any[plan.key(s.pos.x, s.pos.y)] && s.hits < s.hitsMax * 0.6));
    mem.towerRep = cand.length ? _.min(cand, s => s.hits / (s.structureType === STRUCTURE_RAMPART ? target : s.hitsMax)).id : undefined;
  }
  const heal = mem.towerHeal && Game.getObjectById(mem.towerHeal);
  const rep = mem.towerRep && Game.getObjectById(mem.towerRep);
  for (const t of towers) {
    if (heal && heal.hits < heal.hitsMax) t.heal(heal);
    else if (rep && t.store[RESOURCE_ENERGY] > 800 && !growthPaused(rep, room.controller.level, Game.time)) t.repair(rep); // keep ≥800 for combat (novice ends 2026-10-28)
  }
} };
