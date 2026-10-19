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
const W8 = require('./rooms/w47n8/index'); // separate W47N8 room module
const cpuorder = require('./utils/cpuorder'); // low-bucket creep priority (docs/CPU.md)
module.exports.loop = function () {
  { const t = Game.cpu.getUsed(); void Memory.creeps; err.pre = [t, Game.cpu.getUsed() - t]; } // CPU profile: pre-loop, Memory parse
  trace.wrap();
  const newAlerts = [];
  for (const n in Memory.creeps) if (!Game.creeps[n]) delete Memory.creeps[n];
  for (const n in Game.spawns) { const sp = Game.spawns[n]; if (sp.room.name === W8.ROOM) err.wrap('w8spawn', () => W8.spawnRun(sp)); else err.wrap('spawn ' + n, () => spawnMgr.run(sp)); }
  for (const n in Game.rooms) { const r = Game.rooms[n]; if (r.controller && r.controller.my && n === W8.ROOM) { err.wrap('w8layout', () => W8.layoutRun(r)); err.wrap('w8tower', () => W8.towerRun(r)); continue; } if (r.controller && r.controller.my) { err.wrap('layout ' + n, () => layout.run(r)); err.wrap('tower ' + n, () => tower.run(r)); err.wrap('links ' + n, () => links.run(r)); err.wrap('alerts ' + n, () => newAlerts.push(...(alerts.run(r) || []))); } }
  err.wrap('remote', () => remote.run());
  err.wrap('roads', () => require('./managers/roads').run()); // RCL6 road plan (docs/ROADS.md), no-op below RCL6
  for (const n in Game.rooms) { const r = Game.rooms[n]; if (remote.CFG[n]) err.wrap('alerts ' + n, () => newAlerts.push(...(alerts.run(r) || []))); }
  for (const n of cpuorder.order(Game.creeps, Game.cpu.bucket)) { const c = Game.creeps[n]; if (c.spawning) continue; if (cpuorder.shed(c, Game.cpu.bucket, Game.cpu.getUsed(), Game.cpu.tickLimit)) continue; /* no intents possible; avoids stuck-ladder repaths + false STUCK */ if (!c.memory.role) c.memory.role = 'harvester';
    if (!c.memory.v2) { for (const k of ['spot', '_move', '_m', 'src', 'dst', 't', 'sink', 'stop', 'repairId']) delete c.memory[k]; c.memory.v2 = 1; } if (c.memory.role !== 'guard' && c.memory.role !== 'defender' && c.memory.role !== 'probe' && c.memory.role !== 'cqsquad' && c.memory.role !== 'cqbreaker' && c.memory.role !== 'cqworker' && c.memory.role !== 'cqquad' && c.memory.home !== 'W47N8' && c.memory.role !== 'cqhauler' && c.memory.role !== 'cqatk' && c.memory.role !== 'cqminer' && c.memory.role !== 'reserve7' && c.memory.role !== 'cqrh' && require('./managers/home').flee(c, 4)) continue; const t0 = Game.cpu.getUsed(); err.wrap('creep ' + n, () => (roles[c.memory.role] || roles.harvester).run(c)); trace.cpu(c, Game.cpu.getUsed() - t0); }
  const tt = Game.cpu.getUsed(); err.wrap('trace', () => { trace.tick(); trace.run(); }); Memory.traceCpu = Math.round((Game.cpu.getUsed() - tt) * 1000) / 1000;
  err.wrap('stats', () => stats.run(err.flush(), newAlerts));
  err.wrap('report', () => report.run());
};
