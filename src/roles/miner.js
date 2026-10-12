// Static miner: parks on the container next to its source (or adjacent tile) and harvests forever.
module.exports = { run(c) {
  const src = Game.getObjectById(c.memory.sourceId); if (!src) return;
  let spot = c.memory.spot;
  if (!spot) {
    const cont = src.pos.findInRange(FIND_STRUCTURES, 1, { filter: s => s.structureType === STRUCTURE_CONTAINER })[0]
      || src.pos.findInRange(FIND_CONSTRUCTION_SITES, 1, { filter: s => s.structureType === STRUCTURE_CONTAINER })[0];
    if (cont) spot = c.memory.spot = [cont.pos.x, cont.pos.y];
  }
  if (spot && (c.pos.x !== spot[0] || c.pos.y !== spot[1])) { c.moveTo(spot[0], spot[1], { reusePath: 20 }); if (!c.pos.isNearTo(src)) return; }
  else if (!spot && !c.pos.isNearTo(src)) { c.moveTo(src, { reusePath: 20 }); return; }
  // ticks spawn->work spot, used for pre-spawning (miners spawned before this code get the default)
  if (c.memory.travel === undefined && c.ticksToLive) { const t = 1500 - c.ticksToLive; c.memory.travel = t >= 0 && t <= 400 ? t : 100; }
  c.harvest(src);
} };
