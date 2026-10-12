// Hauler: source containers / dropped energy -> spawn & extensions -> towers -> controller container.
module.exports = { run(c) {
  if (c.memory.working && c.store[RESOURCE_ENERGY] === 0) c.memory.working = false;
  if (!c.memory.working && c.store.getFreeCapacity() === 0) c.memory.working = true;
  const ctl = c.room.controller;
  if (!c.memory.working) {
    const drop = c.pos.findClosestByRange(FIND_DROPPED_RESOURCES, { filter: r => r.resourceType === RESOURCE_ENERGY && r.amount >= 50 });
    const conts = c.room.find(FIND_STRUCTURES, { filter: s => s.structureType === STRUCTURE_CONTAINER && s.store[RESOURCE_ENERGY] >= 50 && !s.pos.inRangeTo(ctl, 3) });
    const best = _.max(conts, s => s.store[RESOURCE_ENERGY]);
    if (drop && (!conts.length || drop.amount > 200 || c.pos.getRangeTo(drop) < 5)) { if (c.pickup(drop) === ERR_NOT_IN_RANGE) c.moveTo(drop, { reusePath: 10 }); return; }
    if (conts.length) { if (c.withdraw(best, RESOURCE_ENERGY) === ERR_NOT_IN_RANGE) c.moveTo(best, { reusePath: 10 }); return; }
    if (c.store[RESOURCE_ENERGY] > 0) c.memory.working = true; else return;
  }
  const t = c.pos.findClosestByPath(FIND_MY_STRUCTURES, { filter: s =>
    (s.structureType === STRUCTURE_SPAWN || s.structureType === STRUCTURE_EXTENSION || s.structureType === STRUCTURE_TOWER) && s.store.getFreeCapacity(RESOURCE_ENERGY) > 0 });
  if (t) { if (c.transfer(t, RESOURCE_ENERGY) === ERR_NOT_IN_RANGE) c.moveTo(t, { reusePath: 10 }); return; }
  const cc = ctl.pos.findInRange(FIND_STRUCTURES, 3, { filter: s => s.structureType === STRUCTURE_CONTAINER && s.store.getFreeCapacity(RESOURCE_ENERGY) > 0 })[0];
  if (cc) { if (c.transfer(cc, RESOURCE_ENERGY) === ERR_NOT_IN_RANGE) c.moveTo(cc, { reusePath: 10 }); return; }
  // nothing to fill: hand energy to upgraders by dropping near the controller
  if (c.pos.inRangeTo(ctl, 2)) c.drop(RESOURCE_ENERGY); else c.moveTo(ctl, { range: 2, reusePath: 10 });
} };
