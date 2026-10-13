// Static miner on its fixed plan tile. Delivers: link (if built next to it) > storage (adjacent) > container under it.
const plan = require('../utils/plan'), move = require('../utils/move'), rc = require('../utils/roomcache');
const N8 = [[-1, -1], [0, -1], [1, -1], [-1, 0], [1, 0], [-1, 1], [0, 1], [1, 1]];
module.exports = { run(c) {
  const src = Game.getObjectById(c.memory.sourceId); if (!src) return;
  if (!c.memory.spot) {
    const P = plan.get(c.room.name);
    const spot = P && P.pos.miners.find(([x, y]) => Math.max(Math.abs(x - src.pos.x), Math.abs(y - src.pos.y)) === 1);
    c.memory.spot = spot || [src.pos.x, src.pos.y];
  }
  const [x, y] = c.memory.spot;
  if (!move.to(c, x, y, c.memory.spot[0] === src.pos.x && c.memory.spot[1] === src.pos.y ? 1 : 0)) return;
  if (c.memory.travel === undefined && c.ticksToLive) { const t = 1500 - c.ticksToLive; c.memory.travel = t >= 0 && t <= 400 ? t : 100; }
  if (c.store.getCapacity() > 0 && c.store.getFreeCapacity() < c.getActiveBodyparts(WORK) * 2) {
    if (!c.memory.sink || Game.time % 100 === 0) {
      let sink = null;
      for (const [dx, dy] of N8) { sink = sink || rc.at(c.room, x + dx, y + dy, STRUCTURE_LINK) || rc.at(c.room, x + dx, y + dy, STRUCTURE_STORAGE); }
      c.memory.sink = sink ? sink.id : 0;
    }
    const sink = c.memory.sink && Game.getObjectById(c.memory.sink);
    if (sink && sink.store.getFreeCapacity(RESOURCE_ENERGY) > 0) c.transfer(sink, RESOURCE_ENERGY);
  }
  if (src.energy > 0) c.harvest(src);
} };
