const energy = require('../utils/energy');
module.exports = { run(c) {
  if (!energy.toggle(c)) return energy.get(c);
  if (c.upgradeController(c.room.controller) === ERR_NOT_IN_RANGE) c.moveTo(c.room.controller);
} };
