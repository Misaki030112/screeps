// Mineral miner (RCL6 mineral line, Misaki 2026-10-18 09:30). Stands on the mineral container (plan positions.mineralMiner,
// 41,24 next to O 40,24) and harvests whenever the extractor is off cooldown; no CARRY, so output falls into the container.
// The home hauler empties the container into terminal/storage (roles/hauler.js mineralRun). Spawned by managers/spawn.js only
// while extractor + container stand, the mineral has amount and the container has room.
const plan = require('../utils/plan'), move = require('../utils/move');
module.exports = { run(c) {
  const P = plan.get(c.memory.home || c.room.name), [x, y] = P.pos.mineralMiner;
  if (!move.to(c, x, y, 0)) return;
  const m = c.memory.min ? Game.getObjectById(c.memory.min) : c.pos.findInRange(FIND_MINERALS, 1)[0];
  if (!m) return; c.memory.min = m.id;
  const ex = m.pos.lookFor(LOOK_STRUCTURES).find(s => s.structureType === STRUCTURE_EXTRACTOR);
  if (ex && !ex.cooldown && m.mineralAmount > 0) c.harvest(m);
} };
