const energy = require('../utils/energy');
const upgrader = require('./upgrader');
const PRIO = { extension: 0, tower: 1, spawn: 2, container: 3, storage: 4, link: 5, road: 6, rampart: 7 };
module.exports = { run(c) {
  if (!energy.toggle(c)) return energy.get(c);
  // Critical container upkeep: containers decay (5k hits / 500 ticks). Only the newest
  // builder may repair, and only while hits are critical — polish waits until sites clear.
  const crew = _.filter(Game.creeps, x => x.memory.role === 'builder' && x.room.name === c.room.name)
    .sort((a, b) => a.name.localeCompare(b.name));
  const fixer = crew.length ? crew[crew.length - 1] : null;
  const isFixer = fixer && fixer.name === c.name;
  if (!isFixer) c.memory.repairId = undefined;
  const urgentSites = c.room.find(FIND_MY_CONSTRUCTION_SITES, {
    filter: s => (PRIO[s.structureType] ?? 9) <= 3,
  }).length;
  const startBelow = urgentSites ? 0.25 : 0.4;
  const stopAt = urgentSites ? 0.45 : 0.8;
  let fix = isFixer && c.memory.repairId && Game.getObjectById(c.memory.repairId);
  if (fix && fix.hits >= fix.hitsMax * stopAt) fix = null;
  if (!fix && isFixer) {
    const conts = c.room.find(FIND_STRUCTURES, { filter: s => s.structureType === STRUCTURE_CONTAINER });
    fix = _.min(conts.filter(s => s.hits < s.hitsMax * startBelow
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
    // Secondary builders start roads once the lead site is well underway — but finish the
    // lead when it is nearly done so a controller container is not starved by road peels.
    const idx = crew.findIndex(x => x.name === c.name);
    const leadRatio = sites[0].progress / sites[0].progressTotal;
    if (idx > 0 && leadRatio < 0.85) {
      const lead = sites[0];
      const road = sites.find(s => s.structureType === STRUCTURE_ROAD);
      if (road && (PRIO[lead.structureType] ?? 9) <= 3 && leadRatio >= 0.4) site = road;
    }
    if (c.build(site) === ERR_NOT_IN_RANGE) c.moveTo(site);
    return;
  }
  const rep = c.pos.findClosestByPath(FIND_STRUCTURES, { filter: s => s.hits < s.hitsMax * 0.5 && s.structureType !== STRUCTURE_WALL && s.structureType !== STRUCTURE_RAMPART });
  if (rep) { if (c.repair(rep) === ERR_NOT_IN_RANGE) c.moveTo(rep); return; }
  upgrader.run(c);
} };
