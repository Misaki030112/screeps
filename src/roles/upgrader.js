const energy = require('../utils/energy');
module.exports = { run(c) {
  if (!energy.toggle(c)) {
    // Stay near the controller when haulers are dumping there; only fall back to source containers.
    if (energy.getNearController(c)) return;
    return energy.get(c);
  }
  if (c.upgradeController(c.room.controller) === ERR_NOT_IN_RANGE) c.moveTo(c.room.controller);
} };
