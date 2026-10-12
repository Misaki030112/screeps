const energy = require('../utils/energy');
const upgrader = require('./upgrader');
const PRIO = { extension: 0, tower: 1, spawn: 2, container: 3, storage: 4, link: 5, road: 6, rampart: 7 };
module.exports = { run(c) {
  if (!energy.toggle(c)) return energy.get(c);
  const sites = c.room.find(FIND_CONSTRUCTION_SITES);
  if (sites.length) {
    sites.sort((a, b) => (PRIO[a.structureType] ?? 9) - (PRIO[b.structureType] ?? 9)
      || (b.progress / b.progressTotal) - (a.progress / a.progressTotal));
    let site = sites[0];
    // Secondary builders start roads once the lead site is well underway, so core roads
    // are not blocked behind the controller container.
    const builders = _.filter(Game.creeps, x => x.memory.role === 'builder' && x.room.name === c.room.name)
      .sort((a, b) => a.name.localeCompare(b.name));
    const idx = builders.findIndex(x => x.name === c.name);
    if (idx > 0) {
      const lead = sites[0];
      const road = sites.find(s => s.structureType === STRUCTURE_ROAD);
      if (road && (PRIO[lead.structureType] ?? 9) <= 3 && lead.progress / lead.progressTotal >= 0.4) site = road;
    }
    if (c.build(site) === ERR_NOT_IN_RANGE) c.moveTo(site);
    return;
  }
  const rep = c.pos.findClosestByPath(FIND_STRUCTURES, { filter: s => s.hits < s.hitsMax * 0.5 && s.structureType !== STRUCTURE_WALL && s.structureType !== STRUCTURE_RAMPART });
  if (rep) { if (c.repair(rep) === ERR_NOT_IN_RANGE) c.moveTo(rep); return; }
  upgrader.run(c);
} };
