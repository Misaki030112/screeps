const energy = require('../utils/energy');
module.exports = { run(c) {
  if (!energy.toggle(c)) {
    // Stay near the controller when haulers can deliver; do not trek to source containers.
    if (energy.getNearController(c)) return;
    const hasHauler = _.some(Game.creeps, x => x.memory.role === 'hauler' && x.room.name === c.room.name);
    if (hasHauler) {
      const ctl = c.room.controller;
      if (ctl && !c.pos.inRangeTo(ctl, 3)) c.moveTo(ctl, { range: 3, reusePath: 10 });
      return;
    }
    return energy.get(c);
  }
  if (c.upgradeController(c.room.controller) === ERR_NOT_IN_RANGE) c.moveTo(c.room.controller);
} };
