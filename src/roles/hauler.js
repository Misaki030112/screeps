// Hauler: source containers / dropped energy -> spawn & extensions -> towers -> controller container.
module.exports = { run(c) {
  if (c.memory.working && c.store[RESOURCE_ENERGY] === 0) c.memory.working = false;
  if (!c.memory.working && c.store.getFreeCapacity() === 0) c.memory.working = true;
  const ctl = c.room.controller;
  if (!c.memory.working) {
    // Sticky pickup target scored by energy per tick of travel; stops ping-ponging between small miner overflow
    // drops and far containers. Re-scored only when the target is gone/drained or after a pickup.
    const amt = o => (o.amount !== undefined ? o.amount : o.store[RESOURCE_ENERGY]);
    let src = c.memory.src && Game.getObjectById(c.memory.src);
    if (!src || amt(src) < 50) {
      const free = c.store.getFreeCapacity();
      const cands = c.room.find(FIND_DROPPED_RESOURCES, { filter: r => r.resourceType === RESOURCE_ENERGY && r.amount >= 50 })
        .concat(c.room.find(FIND_STRUCTURES, { filter: s => s.structureType === STRUCTURE_CONTAINER && s.store[RESOURCE_ENERGY] >= 50 && !s.pos.inRangeTo(ctl, 3) }));
      src = cands.length ? _.max(cands, o => Math.min(amt(o), free) * (o.amount !== undefined ? 1.2 : 1) / (c.pos.getRangeTo(o) + 10)) : null;
      if (src) c.memory.src = src.id; else delete c.memory.src;
    }
    if (src) {
      const r = src.amount !== undefined ? c.pickup(src) : c.withdraw(src, RESOURCE_ENERGY);
      if (r === ERR_NOT_IN_RANGE) c.moveTo(src, { reusePath: 10 }); else delete c.memory.src;
      return;
    }
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
