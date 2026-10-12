const energy = require('../utils/energy');
const upgrader = require('./upgrader');
module.exports = { run(c) {
  if (!energy.toggle(c)) return energy.get(c);
  const site = c.pos.findClosestByPath(FIND_CONSTRUCTION_SITES);
  if (site) { if (c.build(site) === ERR_NOT_IN_RANGE) c.moveTo(site); return; }
  const rep = c.pos.findClosestByPath(FIND_STRUCTURES, { filter: s => s.hits < s.hitsMax * 0.5 && s.structureType !== STRUCTURE_WALL && s.structureType !== STRUCTURE_RAMPART });
  if (rep) { if (c.repair(rep) === ERR_NOT_IN_RANGE) c.moveTo(rep); return; }
  upgrader.run(c);
} };
