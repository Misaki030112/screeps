// Upgrader on a fixed spot next to the controller container (30,30) / controller link (30,31). Never wanders.
const plan = require('../utils/plan'), move = require('../utils/move'), rc = require('../utils/roomcache');
module.exports = { run(c) {
  const room = c.room, P = plan.get(room.name);
  if (!c.memory.spot) {
    const taken = new Set(_.filter(Game.creeps, x => x.memory.role === 'upgrader' && x.memory.spot).map(x => x.memory.spot.join()));
    c.memory.spot = P.pos.upgraders.find(s => !taken.has(s.join())) || P.pos.upgraders[P.pos.upgraders.length - 1];
  }
  const [x, y] = c.memory.spot;
  if (!move.to(c, x, y, 0)) {
    if (c.store[RESOURCE_ENERGY] > 0 && c.pos.inRangeTo(room.controller, 3)) c.upgradeController(room.controller);
    return;
  }
  // defender energy readiness without storage: stop drawing so haulers' energy goes to extensions (threat.holding)
  const hold = !room.storage && require('../managers/threat').holding(room.name);
  if (!hold && c.store[RESOURCE_ENERGY] <= c.getActiveBodyparts(WORK)) {
    const [lx, ly] = P.pos.controllerLink, [cx, cy] = P.pos.controllerContainer;
    const l = rc.at(room, lx, ly, STRUCTURE_LINK), k = rc.at(room, cx, cy, STRUCTURE_CONTAINER);
    const s = (l && l.store[RESOURCE_ENERGY] > 0) ? l : (k && k.store[RESOURCE_ENERGY] > 0 ? k : null);
    if (s) c.withdraw(s, RESOURCE_ENERGY);
    else { // energy dropped on the drop tile / on own tile
      const d = room.lookForAtArea(LOOK_RESOURCES, y - 1, x - 1, y + 1, x + 1, true)[0];
      if (d) c.pickup(d.resource);
    }
  }
  if (c.store[RESOURCE_ENERGY] > 0) c.upgradeController(room.controller);
} };
