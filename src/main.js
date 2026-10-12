const roles = require('./roles/index');
const spawnMgr = require('./managers/spawn');
const construction = require('./managers/construction');
const stats = require('./managers/stats');
const err = require('./utils/errors');
module.exports.loop = function () {
  for (const n in Memory.creeps) if (!Game.creeps[n]) delete Memory.creeps[n];
  for (const n in Game.spawns) err.wrap('spawn ' + n, () => spawnMgr.run(Game.spawns[n]));
  for (const n in Game.rooms) { const r = Game.rooms[n]; if (r.controller && r.controller.my) err.wrap('build ' + n, () => construction.run(r)); }
  for (const n in Game.creeps) { const c = Game.creeps[n]; err.wrap('creep ' + n, () => (roles[c.memory.role] || roles.harvester).run(c)); }
  err.wrap('stats', () => stats.run(err.flush()));
};
