const TARGET = { harvester: 3, upgrader: 3, builder: 2 };
function body(energy) {
  const parts = []; let e = energy;
  while (e >= 200 && parts.length < 15) { parts.push(WORK, CARRY, MOVE); e -= 200; }
  return parts.length ? parts : [WORK, CARRY, MOVE];
}
module.exports = { TARGET, run(spawn) {
  if (spawn.spawning) return;
  const count = _.countBy(Game.creeps, c => c.memory.role);
  const room = spawn.room;
  for (const role of ['harvester', 'upgrader', 'builder']) {
    if ((count[role] || 0) < TARGET[role]) {
      const emergency = role === 'harvester' && !count.harvester;
      const energy = emergency ? Math.max(200, room.energyAvailable) : room.energyCapacityAvailable;
      if (!emergency && room.energyAvailable < energy) return;
      spawn.spawnCreep(body(energy), role + Game.time, { memory: { role } });
      return;
    }
  }
} };
