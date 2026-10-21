// Writes Memory.stats each tick; keeps last 20 errors.
const plan = require('../utils/plan'), rc = require('../utils/roomcache');
function ctlEnergy(r) {
  // W47N8 has no home-style plan: its ctl container comes from rooms/w47n8/config (strategy 10-21 11:4x, room_stats.ctl was NULL)
  const W = require('../rooms/w47n8/config'), P = r.name === W.ROOM ? null : plan.get(r.name);
  const xy = r.name === W.ROOM ? W.CTL_CONT : P && P.pos.controllerContainer; if (!xy) return null;
  const k = rc.at(r, xy[0], xy[1], STRUCTURE_CONTAINER);
  return k ? k.store[RESOURCE_ENERGY] : null;
}
module.exports = { run(errors, alerts = []) {
  // room details every 5 ticks; cheap fields every tick
  const s = Memory.stats || (Memory.stats = {});
  const rooms = s.rooms || {};
  if (Game.time % 5 === 0 || !s.rooms) for (const n in Game.rooms) {
    const r = Game.rooms[n]; if (!r.controller || !r.controller.my) continue;
    rooms[n] = { rcl: r.controller.level, progress: r.controller.progress, progressTotal: r.controller.progressTotal,
      energy: r.energyAvailable, energyCap: r.energyCapacityAvailable,
      sites: r.find(FIND_MY_CONSTRUCTION_SITES).length, hostiles: r.find(FIND_HOSTILE_CREEPS).length,
      safeMode: r.controller.safeMode || 0, safeModeAvailable: r.controller.safeModeAvailable,
      // spawn gates read these (3rd upgrader: storage >= ferry floor + 1000 and ctlEma >= 700; queen ferry): log them so a
      // gate opening can be explained from room_stats (patrol 10-14 12:27: 3rd 12W at 83633347 could not be explained)
      storage: r.storage ? r.storage.store[RESOURCE_ENERGY] : null, ctl: ctlEnergy(r), ctlEma: r.memory.ctlEma };
  }
  s.time = Game.time;
  s.gcl = { level: Game.gcl.level, progress: Game.gcl.progress, progressTotal: Game.gcl.progressTotal };
  s.rooms = rooms;
  for (const n in rooms) if (Game.rooms[n]) { rooms[n].energy = Game.rooms[n].energyAvailable; rooms[n].progress = Game.rooms[n].controller.progress; }
  s.creeps = _.countBy(Game.creeps, c => c.memory.role);
  s.bucket = Game.cpu.bucket;
  s.errors = (s.errors || []).concat(errors).slice(-10); // CPU 13:10: smaller Memory parse
  if (errors.length) s.lastErrorTick = Game.time;
  s.alerts = (s.alerts || []).concat(alerts).slice(-12);
  if (alerts.length) s.lastAlertTick = Game.time;
  s.cpu = Game.cpu.getUsed();
  // EMA(1/50) per section; mem = CPU before the loop body (Memory parse + global), set by main.js
  const err = require('../utils/errors'), P = err.prof, E = s.prof || (s.prof = {});
  P.total = s.cpu; P.pre = (err.pre || [0])[0]; P.mem = (err.pre || [0, 0])[1];
  for (const k in P) E[k] = Math.round(((E[k] === undefined ? P[k] : E[k] * 0.98 + P[k] * 0.02)) * 1000) / 1000;
  err.prof = {};
  // remote threat snapshot (strategy 2026-10-20 00:0x): st/why/until per CFG remote for q.py / Grafana
  try {
    const threat = require('./threat'), remote = require('./remote'), rem = s.remote || (s.remote = {});
    for (const r of Object.keys(remote.CFG)) {
      const th = threat.state(r);
      rem[r] = { st: th.st, why: th.why || null, until: th.until || null };
    }
  } catch (e) { /* threat/remote may be mid-reload */ }
} };
