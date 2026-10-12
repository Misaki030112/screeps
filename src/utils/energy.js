module.exports = {
  toggle(c) {
    if (c.memory.working && c.store[RESOURCE_ENERGY] === 0) c.memory.working = false;
    if (!c.memory.working && c.store.getFreeCapacity() === 0) c.memory.working = true;
    return c.memory.working;
  },
  get(c) {
    const drop = c.pos.findClosestByPath(FIND_DROPPED_RESOURCES, { filter: r => r.resourceType === RESOURCE_ENERGY && r.amount > 50 });
    if (drop) { if (c.pickup(drop) === ERR_NOT_IN_RANGE) c.moveTo(drop); return; }
    const cont = c.pos.findClosestByPath(FIND_STRUCTURES, { filter: s => (s.structureType === STRUCTURE_CONTAINER || s.structureType === STRUCTURE_STORAGE) && s.store[RESOURCE_ENERGY] > 100 });
    if (cont) { if (c.withdraw(cont, RESOURCE_ENERGY) === ERR_NOT_IN_RANGE) c.moveTo(cont); return; }
    const src = c.pos.findClosestByPath(FIND_SOURCES_ACTIVE) || c.room.find(FIND_SOURCES)[0];
    if (src && c.harvest(src) === ERR_NOT_IN_RANGE) c.moveTo(src, { visualizePathStyle: {} });
  },
};
