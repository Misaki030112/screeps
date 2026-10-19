// Hauler (RCL2-6): one FIXED pickup per hauler (its miner container + drops next to it, waits there until full) -> fixed drop-offs:
// spawn/ext via queen route when no queen, controller container, storage, filler container. No room-wide searches.
const plan = require('../utils/plan'), move = require('../utils/move'), rc = require('../utils/roomcache');
const queen = require('./queen'), trace = require('../utils/trace'), salvage = require('../utils/salvage');
// controller container below this -> it is the first drop-off and a half-full hauler stops waiting (upgraders were idle 35% while haulers waited/fed elsewhere, idle_history 10-13)
const CTL_LOW = 1000;
function ctlLow(room, P) { const k = rc.at(room, P.pos.controllerContainer[0], P.pos.controllerContainer[1], STRUCTURE_CONTAINER); return k && k.store[RESOURCE_ENERGY] < CTL_LOW; }
// one rule for every carrier next to the controller: hand energy straight to an adjacent upgrader that has room (no queue on the drop tile)
function handoff(c) { const u = c.pos.findInRange(FIND_MY_CREEPS, 1).find(x => x.memory.role === 'upgrader' && x.store.getFreeCapacity() >= 25); return u ? c.transfer(u, RESOURCE_ENERGY) === OK : false; }
function pickups(room) {
  const P = plan.get(room.name);
  return P.pos.miners.map(([x, y]) => rc.at(room, x, y, STRUCTURE_CONTAINER)).filter(Boolean)
    .concat(rc.all(room, STRUCTURE_CONTAINER).filter(s => !P.any[plan.key(s.pos.x, s.pos.y)])); // leftover containers (e.g. 31,11)
}
// Deterministic assignment, recomputed once per tick: haulers sorted by name -> miner containers ordered farthest first,
// round-robin (2 haulers: far+near, 3: far+near+far). Self-balances when a hauler dies; no stored state to drift.
const AS = {};
function assignPickup(c, room, P) {
  let e = AS[room.name];
  if (!e || e.t !== Game.time) {
    const [sx, sy] = P.pos.storageDoor;
    const d = ([x, y]) => Math.max(Math.abs(x - sx), Math.abs(y - sy));
    // Skip miners adjacent to storage (B at 38,32): they transfer straight in; hauling that container is pure wait.
    const st = room.storage;
    const miners = P.pos.miners.filter(([x, y]) => !(st && Math.max(Math.abs(x - st.pos.x), Math.abs(y - st.pos.y)) === 1));
    const order = (miners.length ? miners : P.pos.miners).slice().sort((p, q) => d(q) - d(p));
    const names = _.filter(Game.creeps, x => x.memory.role === 'hauler' && (x.memory.home || x.room.name) === room.name).map(x => x.name).sort();
    e = AS[room.name] = { t: Game.time, m: {} };
    names.forEach((n, i) => { e.m[n] = order[i % order.length]; });
  }
  const a = e.m[c.name] || P.pos.miners[0];
  c.memory.hp = a; return a;
}
// Idle with nothing to pick: wait within 3 of the ctl drop, but on a free plain tile that is not a road and not next to an
// upgrader spot. 10-19 23:13: the idle home hauler parked on 30,29 (2210 of 5100 t) made a new 1-MOVE upgrader detour
// through swamp 30,28 to spot 29,30 (walk-in 100 t vs 10-34 t usual, ctl container full meanwhile).
function idlePark(c, room, P) {
  const [dx, dy] = P.pos.controllerDrop, ups = P.pos.upgraders || [];
  const ok = (x, y) => Math.max(Math.abs(x - dx), Math.abs(y - dy)) <= 3 && !ups.some(([ux, uy]) => Math.max(Math.abs(ux - x), Math.abs(uy - y)) <= 1);
  let pk = c.memory.pk;
  if (!pk || !ok(pk[0], pk[1])) {
    const t = room.getTerrain(), cands = [];
    for (let x = dx - 3; x <= dx + 3; x++) for (let y = dy - 3; y <= dy + 3; y++) {
      if (x < 1 || x > 48 || y < 1 || y > 48 || t.get(x, y) !== 0 || !ok(x, y)) continue;
      if (room.lookForAt(LOOK_STRUCTURES, x, y).length || room.lookForAt(LOOK_CONSTRUCTION_SITES, x, y).length) continue;
      const o = room.lookForAt(LOOK_CREEPS, x, y)[0]; if (o && o !== c) continue;
      cands.push([x, y]);
    }
    pk = cands.length ? _.min(cands, ([x, y]) => c.pos.getRangeTo(x, y)) : null;
    if (!pk) { move.to(c, dx, dy, 3); return; } // no free tile: old behaviour
    c.memory.pk = pk;
  }
  move.to(c, pk[0], pk[1], 0);
}
function legacyPickup(c, room, P) {
  let src = c.memory.src && Game.getObjectById(c.memory.src);
  if (!src || (src.store ? src.store[RESOURCE_ENERGY] : src.amount) < 50) {
    const free = c.store.getFreeCapacity();
    const cands = pickups(room).filter(s => s.store[RESOURCE_ENERGY] >= 100);
    for (const [x, y] of P.pos.miners) for (const r of room.lookForAtArea(LOOK_RESOURCES, y - 1, x - 1, y + 1, x + 1, true)) if (r.resource.amount >= 50) cands.push(r.resource);
    src = cands.length ? _.max(cands, o => Math.min(o.store ? o.store[RESOURCE_ENERGY] : o.amount, free) / (c.pos.getRangeTo(o) + 10)) : null;
    c.memory.src = src ? src.id : undefined;
    if (!src) { if (c.store[RESOURCE_ENERGY] > 0) c.memory.working = true; else idlePark(c, room, P); return; }
  }
  if (move.to(c, src.pos.x, src.pos.y, 1)) { (src.store ? c.withdraw(src, RESOURCE_ENERGY) : c.pickup(src)); delete c.memory.src; }
}
// Mineral run (RCL6 mineral line): an empty home hauler takes the mineral container (>= MIN_RUN or full) to terminal/storage.
// Sticky in memory.mr until delivered. Returns true while busy with it.
const MIN_RUN = 1000;
function mineralRun(c, room, P) {
  const mm = P.pos.mineralMiner; if (!mm || room.name !== c.memory.home) return false;
  const dst = room.terminal || room.storage; if (!dst) return false;
  const held = Object.keys(c.store).find(r => r !== RESOURCE_ENERGY && c.store[r] > 0);
  if (held) { if (move.to(c, dst.pos.x, dst.pos.y, 1)) c.transfer(dst, held); return true; }
  if (c.store[RESOURCE_ENERGY] > 0 || c.memory.working) return false;
  const k = rc.at(room, mm[0], mm[1], STRUCTURE_CONTAINER); if (!k) { delete c.memory.mr; return false; }
  const r = Object.keys(k.store).find(t => t !== RESOURCE_ENERGY && k.store[t] > 0);
  if (!r) { delete c.memory.mr; return false; }
  if (!c.memory.mr && k.store[r] < Math.min(MIN_RUN, c.store.getCapacity()) && k.store.getFreeCapacity() > 200) return false;
  c.memory.mr = 1;
  if (move.to(c, mm[0], mm[1], 1)) { c.withdraw(k, r); delete c.memory.mr; }
  return true;
}
// Build hold (walls.noUpgrade): hub -> controller link is off, so source A's energy (link 30,11) piles up in the hub link and
// the source-A container next to the link stays near empty. The home hauler's fixed pickup becomes the hub link, waited on
// from the manager tile (hub + storage both in range 1), so the queen no longer leaves stamp A to drain it
// (patrol 10-18 12:38: ~25% of queen windows were hub/storage trips over the x=38 corridor; hauler idle 49% at 31,13).
function hubPickup(room) {
  if (!room.storage || !require('../managers/walls').noUpgrade(room)) return null;
  const R = require('../managers/links').roles(room);
  return R.hub && R.sources.length ? R.hub : null;
}
function homeHauler(room) { return Object.values(Game.creeps || {}).some(x => x.memory.role === 'hauler' && (x.memory.home || x.room.name) === room.name); }
module.exports = { pickups, handoff, ctlLow, mineralRun, hubPickup, homeHauler, idlePark, run(c) {
  const room = c.room, P = plan.get(room.name);
  if (mineralRun(c, room, P)) return;
  if (room.name === c.memory.home && salvage.dump(c)) return; // Invader loot (minerals) -> storage first
  if (c.memory.working && c.store[RESOURCE_ENERGY] === 0) { c.memory.working = false; delete c.memory.dst; delete c.memory.fl; }
  if (!c.memory.working && c.store.getFreeCapacity() === 0) c.memory.working = true;
  if (c.memory.working && (c.memory.src || c.memory.wt || c.memory.lp || c.memory.pk)) { delete c.memory.src; delete c.memory.wt; delete c.memory.lp; delete c.memory.pk; }
  // old hauler: no new load it can't deliver (2026-10-16: 2 haulers died holding 700/650 on the ctl road); empty -> recycle
  if (!c.memory.working && salvage.retire(c, 50)) return;
  if (!c.memory.working) {
    // salvage first: drops/tombstones/ruins worth the detour (utils/salvage), one carrier per pile
    const sv = salvage.pick(c);
    if (sv) { delete c.memory.wt; if (move.to(c, sv.pos.x, sv.pos.y, 1)) salvage.take(c, sv); return; }
    // Fixed pickup: each hauler owns one miner container (memory.hp) and waits next to it until it can fill up.
    // No mid-trip switching between sources (that ping-pong cost ~1 PathFinder search per 10 ticks per hauler).
    const a = assignPickup(c, room, P), cont = a && rc.at(room, a[0], a[1], STRUCTURE_CONTAINER);
    const hb = hubPickup(room); // ignores a stale legacy flag (lp): live 12:47 the hauler idled at the ctl drop with lp=1 and nothing >= 100 to pick
    if (hb && !(cont && cont.store[RESOURCE_ENERGY] >= c.store.getCapacity())) { // container only when the link path overflowed
      const [mx, my] = P.pos.manager; delete c.memory.wt; delete c.memory.lp;
      if (!move.to(c, mx, my, 0)) return;
      const have = hb.store[RESOURCE_ENERGY];
      if (have >= Math.min(c.store.getFreeCapacity(), require('../managers/links').SEND)) { c.withdraw(hb, RESOURCE_ENERGY); c.memory.working = true; return; }
      trace.why(c, 'p'); return;
    }
    // fallbacks: container missing, or waited > 60 ticks without filling (miner dead/absent) -> one nearest-energy trip
    if (!cont || c.memory.lp) return legacyPickup(c, room, P);
    if (!move.to(c, a[0], a[1], 1)) return;
    if (!c.memory.wt) c.memory.wt = Game.time;
    if (Game.time - c.memory.wt > 60) { delete c.memory.wt; if (c.store[RESOURCE_ENERGY] > 0) c.memory.working = true; else c.memory.lp = 1; return; }
    const free = c.store.getFreeCapacity();
    const drop = c.pos.findInRange(FIND_DROPPED_RESOURCES, 1).find(r => r.resourceType === RESOURCE_ENERGY && r.amount >= 25);
    if (drop) { c.pickup(drop); if (drop.amount >= free) c.memory.working = true; return; }
    const take = Math.min(free, cont.store[RESOURCE_ENERGY]);
    const urgent = room.energyAvailable < room.energyCapacityAvailable * 0.5 && c.store[RESOURCE_ENERGY] + take >= 100;
    if (take >= free || (urgent && take >= 50)) { c.withdraw(cont, RESOURCE_ENERGY); if (take < free) c.memory.working = true; return; }
    if (urgent && c.store[RESOURCE_ENERGY] > 0) c.memory.working = true; // leave with what we have
    else if (c.store[RESOURCE_ENERGY] >= c.store.getCapacity() / 2 && ctlLow(room, P)) c.memory.working = true; // upgraders starving: go now
    trace.why(c, cont.store[RESOURCE_ENERGY] < 50 ? 'e' : 'p'); // container empty = source-limited (legit)
    return; // wait (no intents, no pathing)
  }
  // deliver
  const queens = room.memory.queenAlive && room.memory.queenAlive > Game.time - 3;
  // Keep ~10% spawn headroom so ctl container still gets fed while builders drain extensions
  // With a live queen haulers stay off the queen stops (contention at 34,25/34,27) and feed filler container A instead;
  // they only walk the fill route themselves when there is no queen or the room is nearly empty (fallback).
  const hold = require('../managers/threat').holding(room.name); // collecting 1300 for a defender: fill extensions first
  const lowE = room.energyAvailable < room.energyCapacityAvailable * (hold ? 1 : queens ? 0.3 : 0.9);
  // One decision per load (patrol 10-17 15:40): spawn waves swing energyAvailable across the 30% line, so a loaded hauler
  // flipped ctl -> fill route -> ctl mid-trip (140t for a ~28t leg, ctl container hit 0). With a queen alive a hauler already
  // heading to a drop-off finishes it; once on the fill route (memory.fl) it stays there until empty or nothing needs energy.
  if (c.memory.fl || (lowE && !(queens && c.memory.dst))) {
    if (queen.fillRoute(c)) { c.memory.fl = 1; return; }
    delete c.memory.fl;
  }
  let dst = c.memory.dst && Game.getObjectById(c.memory.dst);
  // Re-pick when free <100 (matches selection threshold). Sticky filler A above 400 starved ctl
  // while fc still had room — upgraders idled with ctl empty and fc ~500+.
  const [fx, fy] = P.pos.fillerContainerA;
  if (dst && !dst.body && dst.pos.x === fx && dst.pos.y === fy && queens && dst.store[RESOURCE_ENERGY] >= 400) dst = null;
  if (!dst || dst.store.getFreeCapacity(RESOURCE_ENERGY) < 100 || (dst.body && Game.time % 5 === 0)) {
    const [cx, cy] = P.pos.controllerContainer;
    const opts = [];
    const fc = rc.at(room, fx, fy, STRUCTURE_CONTAINER);
    if (queens && fc && fc.store[RESOURCE_ENERGY] < 400 && fc.store.getFreeCapacity(RESOURCE_ENERGY) >= 100) opts.push(fc); // queen's fixed refill
    const tw = rc.all(room, STRUCTURE_TOWER).filter(t => t.store[RESOURCE_ENERGY] < 600);
    if (!queens) opts.push(...tw);
    const noUp = require('../managers/walls').noUpgrade(room) && room.storage; // build hold: feed storage, not the controller
    const cc = !noUp && rc.at(room, cx, cy, STRUCTURE_CONTAINER); if (cc && cc.store.getFreeCapacity(RESOURCE_ENERGY) >= 100) { if (cc.store[RESOURCE_ENERGY] < CTL_LOW) opts.unshift(cc); else opts.push(cc); }
    const st = room.storage; if (st && st.store.getFreeCapacity() > 10000) opts.push(st);
    if (fc && fc.store.getFreeCapacity(RESOURCE_ENERGY) >= 200) opts.push(fc);
    // creeps that need energy: queen first (keeps the fill loop short), then builders. Pre-storage only: with storage both
    // refill there, and chasing moving creeps doubled hauler repaths (rp/100 8.6 -> 21.7, trip 13 -> 22 after 4b8715a).
    const needCreep = st ? [] : _.filter(Game.creeps, x => x.room.name === room.name && (x.memory.role === 'queen' || x.memory.role === 'builder') && x.store.getFreeCapacity() >= 50);
    needCreep.sort((a, b) => (a.memory.role === 'queen' ? 0 : 1) - (b.memory.role === 'queen' ? 0 : 1));
    if (needCreep[0] && needCreep[0].memory.role === 'queen' && !(fc && opts[0] === fc)) opts.unshift(needCreep[0]); else if (needCreep[0]) opts.push(needCreep[0]);
    dst = opts[0] || null; c.memory.dst = dst ? dst.id : undefined;
    if (!dst) { const [x, y] = P.pos.controllerDrop; if (move.to(c, x, y, 0)) c.drop(RESOURCE_ENERGY); return; }
  }
  // controller container: stand on the drop tile (31,29) — never on upgrader spots
  if (dst.structureType === STRUCTURE_CONTAINER && dst.pos.x === P.pos.controllerContainer[0] && dst.pos.y === P.pos.controllerContainer[1]) {
    if (move.to(c, dst.pos.x, dst.pos.y, 1)) { c.transfer(dst, RESOURCE_ENERGY); delete c.memory.dst; } else if (!handoff(c)) trace.why(c, 'q'); return; // upgrader tiles are costly in the matrix, so it stops on 31,29 / 30,29 / 29,29
  }
  if (move.to(c, dst.pos.x, dst.pos.y, 1)) { c.transfer(dst, RESOURCE_ENERGY); delete c.memory.dst; }
} };
