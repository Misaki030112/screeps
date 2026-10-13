// Towers: attack closest hostile, heal own creeps, repair planned roads/containers (<60%) and ramparts up to target.
// Off-plan leftovers (old v1 roads, 31,11 container) are left to decay. Repair target chosen every 10 ticks.
const plan = require('../utils/plan'), rc = require('../utils/roomcache');
const RAMPART_TARGET = [0, 0, 0, 20000, 50000, 100000, 300000, 1000000, 3000000];
module.exports = { run(room) {
  const towers = rc.all(room, STRUCTURE_TOWER);
  if (!towers.length) return;
  const hostiles = room.find(FIND_HOSTILE_CREEPS);
  if (hostiles.length) { for (const t of towers) t.attack(t.pos.findClosestByRange(hostiles)); return; }
  const mem = room.memory;
  if (Game.time % 10 === 0) {
    const P = plan.get(room.name), target = RAMPART_TARGET[room.controller.level];
    const hurt = room.find(FIND_MY_CREEPS).find(c => c.hits < c.hitsMax);
    mem.towerHeal = hurt ? hurt.id : undefined;
    const cand = rc.all(room, STRUCTURE_RAMPART).filter(s => s.hits < target)
      .concat(rc.all(room, STRUCTURE_ROAD).concat(rc.all(room, STRUCTURE_CONTAINER))
        .filter(s => P.any[plan.key(s.pos.x, s.pos.y)] && s.hits < s.hitsMax * 0.6));
    mem.towerRep = cand.length ? _.min(cand, s => s.hits / (s.structureType === STRUCTURE_RAMPART ? target : s.hitsMax)).id : undefined;
  }
  const heal = mem.towerHeal && Game.getObjectById(mem.towerHeal);
  const rep = mem.towerRep && Game.getObjectById(mem.towerRep);
  for (const t of towers) {
    if (heal && heal.hits < heal.hitsMax) t.heal(heal);
    else if (rep && t.store[RESOURCE_ENERGY] > 500) t.repair(rep);
  }
} };
