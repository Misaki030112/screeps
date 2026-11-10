// Salvage: dropped energy, tombstones and ruins (docs/SALVAGE.md).
// Live 2026-10-16: nothing picked these up; ~0.8 energy/tick was lost, mostly haulers/rhaulers/queens dying of old age
// with full loads (700/650/400/296/200) plus scout tombstones (45). Miner containers never overflowed.
// pick(c): best pile worth the detour, reserved per tick so two carriers never chase the same pile.
// Rules: piles >= MIN; value after travel (drops decay ceil(a/1000)/tick) must beat WORTH + PER_TILE*range;
// never within DANGER tiles of a hostile creep with ATTACK/RANGED_ATTACK; at most MAX_RANGE away.
// Reachable (patrol 2026-10-30): skip piles on tiles with no walkable neighbour (fully enclosed by
// structures, e.g. ex-filler stop 31,33 after RCL7 stamp). Haulers otherwise oscillate at range 2 forever
// while the pile decays (~1 e/t).
const MIN = 50, WORTH = 50, PER_TILE = 8, MAX_RANGE = 25, MAX_RANGE_LOOT = 49, DANGER = 5;
const N8 = [[-1, -1], [0, -1], [1, -1], [-1, 0], [1, 0], [-1, 1], [0, 1], [1, 1]];
const PASS = { road: 1, container: 1, rampart: 1 };
const R = {}; // heap: tick -> {id: claimed amount}
function claims() {
  if (!R.t || R.t !== Game.time) { R.t = Game.time; R.m = {}; for (const n in Game.creeps) { const x = Game.creeps[n], m = x.memory; if (m && m.salv) R.m[m.salv] = (R.m[m.salv] || 0) + x.store.getFreeCapacity(); } }
  return R.m;
}
// Loot (2026-10-16): Invader tombstones hold boost minerals (invader_W45N8_499: GO10 KO5 ZH5 UH5), not energy.
// Non-energy counts only when the carrier's home has a storage to put it in (dump() brings it there first).
const stor = c => { const r = c && Game.rooms[(c.memory && c.memory.home) || (c.room && c.room.name)]; return r && r.storage && r.storage.my !== false && r.storage.store.getFreeCapacity() > 1000 ? r.storage : null; };
// value in energy-equivalents: a mineral/boost unit counts LOOT_W energy (T1 boosts trade far above energy; 25 units -> 125)
const LOOT_W = 5;
const amt = (o, all) => o.store ? (o.store[RESOURCE_ENERGY] || 0) + (all ? LOOT_W * (_.sum(Object.values(o.store)) - (o.store[RESOURCE_ENERGY] || 0)) : 0)
  : o.resourceType === RESOURCE_ENERGY ? o.amount : all ? LOOT_W * o.amount : 0;
const armed = h => h.body.some(p => (p.type === ATTACK || p.type === RANGED_ATTACK) && p.hits > 0);
// pure scoring, exported for tests: energy we expect to collect, or 0 if not worth it
// Energy-only piles stay inside MAX_RANGE. Mineral/boost loot (Invaders die on room edges)
// is worth a cross-room walk when storage can take it: PER_TILE still drops tiny far piles.
function maxRange(o, all) { return all && amt(o, true) > amt(o, false) ? MAX_RANGE_LOOT : MAX_RANGE; }
function score(o, d, free, claimed, all) {
  let a = amt(o, all) - (claimed || 0);
  if (!o.store) a -= Math.ceil(amt(o, all) / 1000) * d; // dropped piles decay on the way
  const get = Math.min(a, free);
  return a >= MIN && d <= maxRange(o, all) && get >= WORTH + PER_TILE * d ? get : 0;
}
function tileOpen(room, x, y) {
  if (x < 1 || x > 48 || y < 1 || y > 48) return false;
  if (room.getTerrain) {
    const t = room.getTerrain().get(x, y);
    if (t === TERRAIN_MASK_WALL || t === 1) return false;
  }
  if (!room.lookForAt) return true; // unit tests without structure vision: assume open
  const look = typeof LOOK_STRUCTURES !== 'undefined' ? LOOK_STRUCTURES : 'structure';
  return !room.lookForAt(look, x, y).some(s => !PASS[s.structureType]);
}
// Can a creep outside path onto pos (stand on it)? Needs the tile itself open AND at least one open neighbour
// for PathFinder to step in from. Creep already in range 1 is always fine (finish the pickup).
function reachable(room, pos, from) {
  if (from && Math.max(Math.abs(from.x - pos.x), Math.abs(from.y - pos.y)) <= 1) return true;
  if (!room.lookForAt) return true;
  if (!tileOpen(room, pos.x, pos.y)) return false;
  return N8.some(([dx, dy]) => tileOpen(room, pos.x + dx, pos.y + dy));
}
function list(room, all, from) {
  const hostile = room.find(FIND_HOSTILE_CREEPS).filter(armed);
  return room.find(FIND_DROPPED_RESOURCES).concat(room.find(FIND_TOMBSTONES), room.find(FIND_RUINS))
    .filter(o => amt(o, all) >= MIN && reachable(room, o.pos, from) && !hostile.some(h => h.pos.getRangeTo(o.pos) <= DANGER));
}
function pick(c) {
  const free = c.store.getFreeCapacity(); if (free < WORTH) { delete c.memory.salv; return null; }
  const cl = claims(), all = !!stor(c);
  let cur = c.memory.salv && Game.getObjectById(c.memory.salv);
  if (cur && amt(cur, all) > 0 && c.pos.isNearTo(cur)) return cur; // already there: finish it
  // sticky only while still reachable — enclosed piles must be dropped so the hauler resumes real work
  if (cur && reachable(c.room, cur.pos, c.pos) && score(cur, 0, free, Math.max(0, (cl[cur.id] || 0) - free), all) > 0) return cur;
  if (c.memory.salv) { cl[c.memory.salv] = Math.max(0, (cl[c.memory.salv] || 0) - free); delete c.memory.salv; }
  let best = null, bv = 0;
  for (const o of list(c.room, all, c.pos)) { const v = score(o, c.pos.getRangeTo(o), free, cl[o.id], all); if (v > bv) { bv = v; best = o; } }
  if (best) { c.memory.salv = best.id; cl[best.id] = (cl[best.id] || 0) + free; }
  return best;
}
// take from the pile (in range 1); returns true when done with it
// energy first, then (with a storage) the largest other resource; the pile stays claimed until it is empty
function take(c, o) {
  if (!o.store) { delete c.memory.salv; return c.pickup(o); }
  const all = !!stor(c), k = (o.store[RESOURCE_ENERGY] || 0) > 0 ? RESOURCE_ENERGY : all ? _.max(Object.keys(o.store).filter(t => o.store[t] > 0), t => o.store[t]) : null;
  const left = all ? _.sum(Object.values(o.store)) : o.store[RESOURCE_ENERGY] || 0;
  if (!k || k === -Infinity) { delete c.memory.salv; return ERR_NOT_ENOUGH_RESOURCES; }
  if (left - o.store[k] <= 0 || c.store.getFreeCapacity() <= o.store[k]) delete c.memory.salv;
  return c.withdraw(o, k);
}
// carrying loot (non-energy): bring it to the home storage before any energy job; true while busy
function dump(c) {
  const k = Object.keys(c.store).find(t => t !== RESOURCE_ENERGY && c.store[t] > 0); if (!k) return false;
  const s = stor(c); if (!s) { c.drop(k); return false; } // no storage: never block energy work with loot
  if (c.pos.isNearTo(s)) c.transfer(s, k); else require('./move').to(c, s.pos.x, s.pos.y, 1);
  return true;
}
// Old carriers: don't start a load they can't deliver. Empty and close to death -> recycle at the spawn (energy back).
function retire(c, need) {
  if (!c.ticksToLive || c.ticksToLive > need) return false;
  if (c.store.getUsedCapacity() > 0) { c.memory.working = true; return false; } // deliver what we carry, no new pickups
  const sp = _.filter(Game.spawns, s => s.pos.roomName === c.pos.roomName).sort((a, b) => c.pos.getRangeTo(a) - c.pos.getRangeTo(b))[0];
  if (!sp) return false;
  if (c.pos.isNearTo(sp)) sp.recycleCreep(c); else require('./move').to(c, sp.pos.x, sp.pos.y, 1);
  return true;
}
module.exports = { pick, take, dump, retire, score, reachable, MIN, WORTH, PER_TILE, MAX_RANGE, MAX_RANGE_LOOT };
