// Writes Memory.stats each tick; keeps last 20 errors.
module.exports = { run(errors, alerts = []) {
  const s = Memory.stats || (Memory.stats = {});
  const rooms = {};
  for (const n in Game.rooms) {
    const r = Game.rooms[n]; if (!r.controller || !r.controller.my) continue;
    rooms[n] = { rcl: r.controller.level, progress: r.controller.progress, progressTotal: r.controller.progressTotal,
      energy: r.energyAvailable, energyCap: r.energyCapacityAvailable,
      sites: r.find(FIND_MY_CONSTRUCTION_SITES).length, hostiles: r.find(FIND_HOSTILE_CREEPS).length,
      safeMode: r.controller.safeMode || 0, safeModeAvailable: r.controller.safeModeAvailable };
  }
  s.time = Game.time;
  s.gcl = { level: Game.gcl.level, progress: Game.gcl.progress, progressTotal: Game.gcl.progressTotal };
  s.rooms = rooms;
  s.creeps = _.countBy(Game.creeps, c => c.memory.role);
  s.bucket = Game.cpu.bucket;
  s.errors = (s.errors || []).concat(errors).slice(-20);
  if (errors.length) s.lastErrorTick = Game.time;
  s.alerts = (s.alerts || []).concat(alerts).slice(-30);
  if (alerts.length) s.lastAlertTick = Game.time;
  s.cpu = Game.cpu.getUsed();
} };
