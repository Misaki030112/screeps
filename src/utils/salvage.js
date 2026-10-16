// Salvage: dropped energy, tombstones and ruins (docs/SALVAGE.md).
// Live 2026-10-16: nothing picked these up; ~0.8 energy/tick was lost, mostly haulers/rhaulers/queens dying of old age
// with full loads (700/650/400/296/200) plus scout tombstones (45). Miner containers never overflowed.
// pick(c): best pile worth the detour, reserved per tick so two carriers never chase the same pile.
// Rules: piles >= MIN; value after travel (drops decay ceil(a/1000)/tick) must beat WORTH + PER_TILE*range;
// never within DANGER tiles of a hostile creep with ATTACK/RANGED_ATTACK; at most MAX_RANGE away.
const MIN = 50, WORTH = 50, PER_TILE = 8, MAX_RANGE = 25, DANGER = 5;
const R = {}; // heap: tick -> {id: claimed amount}
function claims() {
  if (!R.t || R.t !== Game.time) { R.t = Game.time; R.m = {}; for (const n in Game.creeps) { const x = Game.creeps[n], m = x.memory; if (m && m.salv) R.m[m.salv] = (R.m[m.salv] || 0) + x.store.getFreeCapacity(); } }
  return R.m;
}
const amt = o => (o.store ? o.store[RESOURCE_ENERGY] || 0 : o.resourceType === RESOURCE_ENERGY ? o.amount : 0);
const armed = h => h.body.some(p => (p.type === ATTACK || p.type === RANGED_ATTACK) && p.hits > 0);
// pure scoring, exported for tests: energy we expect to collect, or 0 if not worth it
function score(o, d, free, claimed) {
  let a = amt(o) - (claimed || 0);
  if (!o.store) a -= Math.ceil(amt(o) / 1000) * d; // dropped piles decay on the way
  const get = Math.min(a, free);
  return a >= MIN && d <= MAX_RANGE && get >= WORTH + PER_TILE * d ? get : 0;
}
function list(room) {
  const hostile = room.find(FIND_HOSTILE_CREEPS).filter(armed);
  return room.find(FIND_DROPPED_RESOURCES).concat(room.find(FIND_TOMBSTONES), room.find(FIND_RUINS))
    .filter(o => amt(o) >= MIN && !hostile.some(h => h.pos.getRangeTo(o.pos) <= DANGER));
}
function pick(c) {
  const free = c.store.getFreeCapacity(); if (free < WORTH) { delete c.memory.salv; return null; }
  const cl = claims();
  let cur = c.memory.salv && Game.getObjectById(c.memory.salv);
  if (cur && amt(cur) > 0 && c.pos.isNearTo(cur)) return cur; // already there: finish it
  if (cur && score(cur, 0, free, Math.max(0, (cl[cur.id] || 0) - free)) > 0) return cur; // still worth it (minus own claim)
  if (c.memory.salv) { cl[c.memory.salv] = Math.max(0, (cl[c.memory.salv] || 0) - free); delete c.memory.salv; }
  let best = null, bv = 0;
  for (const o of list(c.room)) { const v = score(o, c.pos.getRangeTo(o), free, cl[o.id]); if (v > bv) { bv = v; best = o; } }
  if (best) { c.memory.salv = best.id; cl[best.id] = (cl[best.id] || 0) + free; }
  return best;
}
// take from the pile (in range 1); returns true when done with it
function take(c, o) { const r = o.store ? c.withdraw(o, RESOURCE_ENERGY) : c.pickup(o); delete c.memory.salv; return r; }
// Old carriers: don't start a load they can't deliver. Empty and close to death -> recycle at the spawn (energy back).
function retire(c, need) {
  if (!c.ticksToLive || c.ticksToLive > need) return false;
  if (c.store[RESOURCE_ENERGY] > 0) { c.memory.working = true; return false; } // deliver what we carry, no new pickups
  const sp = _.filter(Game.spawns, s => s.pos.roomName === c.pos.roomName).sort((a, b) => c.pos.getRangeTo(a) - c.pos.getRangeTo(b))[0];
  if (!sp) return false;
  if (c.pos.isNearTo(sp)) sp.recycleCreep(c); else require('./move').to(c, sp.pos.x, sp.pos.y, 1);
  return true;
}
module.exports = { pick, take, retire, score, MIN, WORTH, PER_TILE };
