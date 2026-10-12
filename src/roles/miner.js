// Static miner: parks on the best container next to its source and harvests forever.
module.exports = { run(c) {
  const src = Game.getObjectById(c.memory.sourceId); if (!src) return;
  // Prefer the healthiest adjacent container (ours) over leftover low-HP ones from prior owners.
  const conts = src.pos.findInRange(FIND_STRUCTURES, 1, { filter: s => s.structureType === STRUCTURE_CONTAINER });
  let spot = c.memory.spot;
  if (conts.length) {
    const best = _.max(conts, s => s.hits);
    spot = c.memory.spot = [best.pos.x, best.pos.y];
  } else if (!spot) {
    const site = src.pos.findInRange(FIND_CONSTRUCTION_SITES, 1, { filter: s => s.structureType === STRUCTURE_CONTAINER })[0];
    if (site) spot = c.memory.spot = [site.pos.x, site.pos.y];
  }
  if (spot && (c.pos.x !== spot[0] || c.pos.y !== spot[1])) { c.moveTo(spot[0], spot[1], { reusePath: 20 }); if (!c.pos.isNearTo(src)) return; }
  else if (!spot && !c.pos.isNearTo(src)) { c.moveTo(src, { reusePath: 20 }); return; }
  // ticks spawn->work spot, used for pre-spawning (miners spawned before this code get the default)
  if (c.memory.travel === undefined && c.ticksToLive) { const t = 1500 - c.ticksToLive; c.memory.travel = t >= 0 && t <= 400 ? t : 100; }
  c.harvest(src);
} };
