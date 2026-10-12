const energy = require('../utils/energy');
const upgrader = require('./upgrader');
const PRIO = { extension: 0, tower: 1, spawn: 2, container: 3, storage: 4, link: 5, road: 6, rampart: 7 };
module.exports = { run(c) {
  if (!energy.toggle(c)) return energy.get(c);
  // Critical container upkeep: containers decay (5k hits / 500 ticks) and would collapse while
  // builders are busy with sites. The newest builder repairs a non-redundant container below 40%
  // until it reaches 80% (hysteresis kept in memory.repairId).
  const crew = _.filter(Game.creeps, x => x.memory.role === 'builder' && x.room.name === c.room.name)
    .sort((a, b) => a.name.localeCompare(b.name));
  let fix = c.memory.repairId && Game.getObjectById(c.memory.repairId);
  if (fix && fix.hits >= fix.hitsMax * 0.8) fix = null;
  if (!fix && crew.length && crew[crew.length - 1].name === c.name) {
    const conts = c.room.find(FIND_STRUCTURES, { filter: s => s.structureType === STRUCTURE_CONTAINER });
    fix = _.min(conts.filter(s => s.hits < s.hitsMax * 0.4
      && !conts.some(o => o.id !== s.id && o.hits > s.hits && o.pos.isNearTo(s))), s => s.hits);
    if (!fix || fix === Infinity) fix = null;
  }
  c.memory.repairId = fix ? fix.id : undefined;
  if (fix) { if (c.repair(fix) === ERR_NOT_IN_RANGE) c.moveTo(fix, { range: 3, reusePath: 10 }); return; }
  const sites = c.room.find(FIND_CONSTRUCTION_SITES);
  if (sites.length) {
    sites.sort((a, b) => (PRIO[a.structureType] ?? 9) - (PRIO[b.structureType] ?? 9)
      || (b.progress / b.progressTotal) - (a.progress / a.progressTotal));
    let site = sites[0];
    // Secondary builders start roads once the lead site is well underway, so core roads
    // are not blocked behind the controller container.
    const idx = crew.findIndex(x => x.name === c.name);
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
