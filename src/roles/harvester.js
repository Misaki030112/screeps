const energy = require('../utils/energy');
const upgrader = require('./upgrader');
module.exports = { run(c) {
  if (!energy.toggle(c)) return energy.get(c);
  const t = c.pos.findClosestByPath(FIND_MY_STRUCTURES, { filter: s =>
    [STRUCTURE_SPAWN, STRUCTURE_EXTENSION, STRUCTURE_TOWER].includes(s.structureType) && s.store.getFreeCapacity(RESOURCE_ENERGY) > 0 });
  if (t) { if (c.transfer(t, RESOURCE_ENERGY) === ERR_NOT_IN_RANGE) c.moveTo(t); }
  else upgrader.run(c);
} };
