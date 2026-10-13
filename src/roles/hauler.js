// Hauler (RCL2-6): one FIXED pickup per hauler (its miner container + drops next to it, waits there until full) -> fixed drop-offs:
// spawn/ext via queen route when no queen, controller container, storage, filler container. No room-wide searches.
const plan = require('../utils/plan'), move = require('../utils/move'), rc = require('../utils/roomcache');
const queen = require('./queen');
function pickups(room) {
  const P = plan.get(room.name);
  return P.pos.miners.map(([x, y]) => rc.at(room, x, y, STRUCTURE_CONTAINER)).filter(Boolean)
    .concat(rc.all(room, STRUCTURE_CONTAINER).filter(s => !P.any[plan.key(s.pos.x, s.pos.y)])); // leftover containers (e.g. 31,11)
}
function assignPickup(c, room, P) {
  let a = c.memory.hp;
  if (a && P.pos.miners.some(([x, y]) => x === a[0] && y === a[1])) return a;
  const n = {};
  for (const h of _.filter(Game.creeps, x => x.memory.role === 'hauler' && x.memory.home === room.name && x.memory.hp)) n[h.memory.hp.join()] = (n[h.memory.hp.join()] || 0) + 1;
  const [sx, sy] = P.pos.storageDoor;
  a = _.min(P.pos.miners, ([x, y]) => (n[x + ',' + y] || 0) * 100 - Math.max(Math.abs(x - sx), Math.abs(y - sy))); // fewest owners, then farthest
  c.memory.hp = a; return a;
}
function legacyPickup(c, room, P) {
  let src = c.memory.src && Game.getObjectById(c.memory.src);
  if (!src || (src.store ? src.store[RESOURCE_ENERGY] : src.amount) < 50) {
    const free = c.store.getFreeCapacity();
    const cands = pickups(room).filter(s => s.store[RESOURCE_ENERGY] >= 100);
    for (const [x, y] of P.pos.miners) for (const r of room.lookForAtArea(LOOK_RESOURCES, y - 1, x - 1, y + 1, x + 1, true)) if (r.resource.amount >= 50) cands.push(r.resource);
    src = cands.length ? _.max(cands, o => Math.min(o.store ? o.store[RESOURCE_ENERGY] : o.amount, free) / (c.pos.getRangeTo(o) + 10)) : null;
    c.memory.src = src ? src.id : undefined;
    if (!src) { if (c.store[RESOURCE_ENERGY] > 0) c.memory.working = true; else { const [x, y] = P.pos.controllerDrop; move.to(c, x, y, 3); } return; }
  }
  if (move.to(c, src.pos.x, src.pos.y, 1)) { (src.store ? c.withdraw(src, RESOURCE_ENERGY) : c.pickup(src)); delete c.memory.src; }
}
module.exports = { pickups, run(c) {
  const room = c.room, P = plan.get(room.name);
  if (c.memory.working && c.store[RESOURCE_ENERGY] === 0) { c.memory.working = false; delete c.memory.dst; }
  if (!c.memory.working && c.store.getFreeCapacity() === 0) { c.memory.working = true; delete c.memory.src; }
  if (!c.memory.working) {
    // Fixed pickup: each hauler owns one miner container (memory.hp) and waits next to it until it can fill up.
    // No mid-trip switching between sources (that ping-pong cost ~1 PathFinder search per 10 ticks per hauler).
    const a = assignPickup(c, room, P), cont = a && rc.at(room, a[0], a[1], STRUCTURE_CONTAINER);
    if (!cont) return legacyPickup(c, room, P); // fallback: container missing -> old nearest-energy pick
    if (!move.to(c, a[0], a[1], 1)) return;
    const free = c.store.getFreeCapacity();
    const drop = c.pos.findInRange(FIND_DROPPED_RESOURCES, 1).find(r => r.resourceType === RESOURCE_ENERGY && r.amount >= 25);
    if (drop) { c.pickup(drop); if (drop.amount >= free) c.memory.working = true; return; }
    const take = Math.min(free, cont.store[RESOURCE_ENERGY]);
    const urgent = room.energyAvailable < room.energyCapacityAvailable * 0.5 && c.store[RESOURCE_ENERGY] + take >= 100;
    if (take >= free || (urgent && take >= 50)) { c.withdraw(cont, RESOURCE_ENERGY); if (take < free) c.memory.working = true; return; }
    if (urgent && c.store[RESOURCE_ENERGY] > 0) c.memory.working = true; // leave with what we have
    return; // wait (no intents, no pathing)
  }
  // deliver
  const queens = room.memory.queenAlive && room.memory.queenAlive > Game.time - 3;
  // Keep ~10% spawn headroom so ctl container still gets fed while builders drain extensions
  if (room.energyAvailable < room.energyCapacityAvailable * 0.9 && queen.fillRoute(c)) return;
  let dst = c.memory.dst && Game.getObjectById(c.memory.dst);
  if (!dst || dst.store.getFreeCapacity(RESOURCE_ENERGY) === 0 || (dst.body && Game.time % 5 === 0)) {
    const [cx, cy] = P.pos.controllerContainer;
    const opts = [];
    const tw = rc.all(room, STRUCTURE_TOWER).filter(t => t.store[RESOURCE_ENERGY] < 600);
    if (!queens) opts.push(...tw);
    const cc = rc.at(room, cx, cy, STRUCTURE_CONTAINER); if (cc && cc.store.getFreeCapacity(RESOURCE_ENERGY) >= 100) opts.push(cc);
    const st = room.storage; if (st && st.store.getFreeCapacity() > 10000) opts.push(st);
    const [fx, fy] = P.pos.fillerContainerA; const fc = rc.at(room, fx, fy, STRUCTURE_CONTAINER);
    if (fc && fc.store.getFreeCapacity(RESOURCE_ENERGY) >= 200) opts.push(fc);
    // creeps that need energy: queen first (keeps the fill loop short), then builders
    const needCreep = _.filter(Game.creeps, x => x.room.name === room.name && (x.memory.role === 'queen' || x.memory.role === 'builder') && x.store.getFreeCapacity() >= 50);
    needCreep.sort((a, b) => (a.memory.role === 'queen' ? 0 : 1) - (b.memory.role === 'queen' ? 0 : 1));
    if (needCreep[0] && needCreep[0].memory.role === 'queen') opts.unshift(needCreep[0]); else if (needCreep[0]) opts.push(needCreep[0]);
    dst = opts[0] || null; c.memory.dst = dst ? dst.id : undefined;
    if (!dst) { const [x, y] = P.pos.controllerDrop; if (move.to(c, x, y, 0)) c.drop(RESOURCE_ENERGY); return; }
  }
  // controller container: stand on the drop tile (31,29) — never on upgrader spots
  if (dst.structureType === STRUCTURE_CONTAINER && dst.pos.x === P.pos.controllerContainer[0] && dst.pos.y === P.pos.controllerContainer[1]) {
    if (move.to(c, dst.pos.x, dst.pos.y, 1)) { c.transfer(dst, RESOURCE_ENERGY); delete c.memory.dst; } return; // upgrader tiles are costly in the matrix, so it stops on 31,29 / 30,29 / 29,29
  }
  if (move.to(c, dst.pos.x, dst.pos.y, 1)) { c.transfer(dst, RESOURCE_ENERGY); delete c.memory.dst; }
} };
