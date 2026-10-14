// Writes Memory.stats each tick; keeps last 20 errors.
const plan = require('../utils/plan'), rc = require('../utils/roomcache');
function ctlEnergy(r) {
  const P = plan.get(r.name); if (!P || !P.pos.controllerContainer) return null;
  const k = rc.at(r, P.pos.controllerContainer[0], P.pos.controllerContainer[1], STRUCTURE_CONTAINER);
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
  s.errors = (s.errors || []).concat(errors).slice(-20);
  if (errors.length) s.lastErrorTick = Game.time;
  s.alerts = (s.alerts || []).concat(alerts).slice(-30);
  if (alerts.length) s.lastAlertTick = Game.time;
  s.cpu = Game.cpu.getUsed();
} };
