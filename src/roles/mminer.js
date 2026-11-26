// Mineral miner (RCL6 mineral line, Misaki 2026-10-18 09:30). Stands on the mineral container (plan positions.mineralMiner,
// 41,24 next to O 40,24) and harvests whenever the extractor is off cooldown; no CARRY, so output falls into the container.
// The home hauler empties the container into terminal/storage (roles/hauler.js mineralRun). Spawned by managers/spawn.js only
// while extractor + container stand, the mineral has amount and the container has room.
const plan = require('../utils/plan'), move = require('../utils/move');
module.exports = { run(c) {
  if (require('../utils/cmd').yieldCreep(c)) return;
  const home = c.memory.home || c.room.name, room = Game.rooms[home] || c.room;
  // Recycle when spawn dropped the target for a real stop (mineralCap / mineral empty / container gone). NOT on the defence-floor
  // pause (walls.defLow): spawn.js zeroes T.mminer on every dip under reserveE, and with storage hovering at 15k that recycled
  // each fresh 12W3M 45-170 ticks after spawn (patrol 2026-11-26 14:3x JST: 11 mminers in ~1.3k ticks, tombstones on the filler
  // tiles by spawn 35,28 never collected, ~1.3k e lost per cycle). The body is already paid; keep mining into the container
  // (hauler.mineralRun already pauses under defLow), and the floor pause only blocks the NEXT spawn.
  const W = require('../managers/walls'), floorPause = !!(W.defLow && W.defLow(room));
  if ((((room.memory || {}).roleTargets || {}).mminer || 0) === 0 && !floorPause) {
    const sp = _.filter(Game.spawns, s => s.pos.roomName === room.name)[0];
    if (sp) { if (c.pos.isNearTo(sp)) sp.recycleCreep(c); else move.to(c, sp.pos.x, sp.pos.y, 1); }
    return;
  }
  const P = plan.get(home), [x, y] = P.pos.mineralMiner;
  if (!move.to(c, x, y, 0)) return;
  const m = c.memory.min ? Game.getObjectById(c.memory.min) : c.pos.findInRange(FIND_MINERALS, 1)[0];
  if (!m) return; c.memory.min = m.id;
  const ex = m.pos.lookFor(LOOK_STRUCTURES).find(s => s.structureType === STRUCTURE_EXTRACTOR);
  if (ex && !ex.cooldown && m.mineralAmount > 0) c.harvest(m);
} };
