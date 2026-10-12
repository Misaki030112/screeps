// Towers: attack closest hostile, heal own creeps, repair (roads/containers <60%, ramparts up to RAMPART_TARGET[rcl]).
const RAMPART_TARGET = [0, 0, 0, 20000, 50000, 100000, 300000, 1000000, 3000000];
module.exports = { run(room) {
  const towers = room.find(FIND_MY_STRUCTURES, { filter: { structureType: STRUCTURE_TOWER } });
  if (!towers.length) return;
  const hostiles = room.find(FIND_HOSTILE_CREEPS);
  const hurt = room.find(FIND_MY_CREEPS, { filter: c => c.hits < c.hitsMax });
  const target = RAMPART_TARGET[room.controller.level];
  const rep = hostiles.length ? null : room.find(FIND_STRUCTURES, { filter: s =>
    (s.structureType === STRUCTURE_RAMPART && s.my && s.hits < target) ||
    ((s.structureType === STRUCTURE_ROAD || s.structureType === STRUCTURE_CONTAINER) && s.hits < s.hitsMax * 0.6) }).sort((a, b) => a.hits - b.hits)[0];
  for (const t of towers) {
    if (hostiles.length) t.attack(t.pos.findClosestByRange(hostiles));
    else if (hurt.length) t.heal(hurt[0]);
    else if (rep && t.store[RESOURCE_ENERGY] > 500) t.repair(rep);
  }
} };
