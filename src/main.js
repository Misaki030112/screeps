const roles = require('./roles/index');
const spawnMgr = require('./managers/spawn');
const layout = require('./managers/layout');
const tower = require('./managers/tower');
const alerts = require('./managers/alerts');
const links = require('./managers/links');
const report = require('./utils/report');
const stats = require('./managers/stats');
const err = require('./utils/errors');
const remote = require('./managers/remote');
const trace = require('./utils/trace');
module.exports.loop = function () {
  trace.wrap();
  const newAlerts = [];
  for (const n in Memory.creeps) if (!Game.creeps[n]) delete Memory.creeps[n];
  for (const n in Game.spawns) err.wrap('spawn ' + n, () => spawnMgr.run(Game.spawns[n]));
  for (const n in Game.rooms) { const r = Game.rooms[n]; if (r.controller && r.controller.my) { err.wrap('layout ' + n, () => layout.run(r)); err.wrap('tower ' + n, () => tower.run(r)); err.wrap('links ' + n, () => links.run(r)); err.wrap('alerts ' + n, () => newAlerts.push(...(alerts.run(r) || []))); } }
  err.wrap('remote', () => remote.run());
  for (const n in Game.rooms) { const r = Game.rooms[n]; if (remote.CFG[n]) err.wrap('alerts ' + n, () => newAlerts.push(...(alerts.run(r) || []))); }
  for (const n in Game.creeps) { const c = Game.creeps[n]; if (c.spawning) continue; /* no intents possible; avoids stuck-ladder repaths + false STUCK */ if (!c.memory.role) c.memory.role = 'harvester';
    if (!c.memory.v2) { for (const k of ['spot', '_move', '_m', 'src', 'dst', 't', 'sink', 'stop', 'repairId']) delete c.memory[k]; c.memory.v2 = 1; } if (c.memory.role !== 'guard' && c.memory.role !== 'defender' && require('./managers/home').flee(c, 4)) continue; const t0 = Game.cpu.getUsed(); err.wrap('creep ' + n, () => (roles[c.memory.role] || roles.harvester).run(c)); trace.cpu(c, Game.cpu.getUsed() - t0); }
  const tt = Game.cpu.getUsed(); err.wrap('trace', () => { trace.tick(); trace.run(); }); Memory.traceCpu = Math.round((Game.cpu.getUsed() - tt) * 1000) / 1000;
  err.wrap('stats', () => stats.run(err.flush(), newAlerts));
  err.wrap('report', () => report.run());
};
