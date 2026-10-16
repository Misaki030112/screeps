// Remote roles: rminer (sits on container, repairs it), rhauler (container -> home via hauler delivery), reserver.
const move = require('../utils/move'), remote = require('../managers/remote'), threat = require('../managers/threat');
// cross-room travel through fixed exits along remote.route (home -> via... -> remote); returns true when in range of target
const OFF = (x, y) => x === 49 ? RIGHT : x === 0 ? LEFT : y === 49 ? BOTTOM : TOP;
// Border step-in. A creep still on an exit tile at the end of a tick is sent back to the other room, so a failed step-in
// = bounce. 2026-10-16: loaded W45N7 rhaulers arriving at W46N8 49,21 stepped straight LEFT onto 48,21 while an outbound
// rhauler stepped 47->48,21 on its cached path; the outbound one won, the loaded one stayed on 49 and bounced to W45N8
// (2-4 ticks/trip). Pick an inward tile (straight first, then diagonals) that is not wall, not occupied and not the next
// cached step (_m) of a nearby creep of ours. pure: inward(x, y, wall(x,y), busy(x,y)) -> direction
function inward(x, y, wall, busy) {
  const [dx, dy] = x === 0 ? [1, 0] : x === 49 ? [-1, 0] : y === 0 ? [0, 1] : [0, -1];
  const C = dx ? [[dx, 0], [dx, -1], [dx, 1]] : [[0, dy], [-1, dy], [1, dy]];
  const D = (a, b) => ({ '0,-1': TOP, '1,-1': TOP_RIGHT, '1,0': RIGHT, '1,1': BOTTOM_RIGHT, '0,1': BOTTOM, '-1,1': BOTTOM_LEFT, '-1,0': LEFT, '-1,-1': TOP_LEFT })[a + ',' + b];
  const ok = C.filter(([a, b]) => { const nx = x + a, ny = y + b; return nx > 0 && nx < 49 && ny > 0 && ny < 49 && !wall(nx, ny); });
  const free = ok.find(([a, b]) => !busy(x + a, y + b));
  const [a, b] = free || ok[0] || C[0]; return D(a, b);
}
function stepIn(c) {
  const T = c.room.getTerrain(), taken = new Set();
  for (const o of c.pos.findInRange(FIND_CREEPS, 3)) { if (o === c) continue; taken.add(o.pos.x * 50 + o.pos.y);
    const m = o.my && o.memory && o.memory._m; if (m && m.p) { const i = m.p.indexOf(String.fromCharCode(o.pos.x * 50 + o.pos.y + 192)), ch = i >= 0 ? m.p.charCodeAt(i + 1) : 0;
      if (ch) taken.add(ch - 192); } }
  return inward(c.pos.x, c.pos.y, (x, y) => T.get(x, y) === TERRAIN_MASK_WALL, (x, y) => taken.has(x * 50 + y));
}
function go(c, room, x, y, range, rr) {
  const rm = rr || c.memory.remote;
  if (c.room.name === room) {
    // just crossed: step off the border first
    if (c.pos.x === 0 || c.pos.x === 49 || c.pos.y === 0 || c.pos.y === 49) { delete c.memory._m; c.move(stepIn(c)); return false; }
    return move.to(c, x, y, range);
  }
  const R = remote.route(rm), i = R.indexOf(c.room.name), j = R.indexOf(room);
  if (i < 0 || j < 0) { c.moveTo(new RoomPosition(x, y, room), { range, reusePath: 20, costCallback: move.foreignSites }); return false; } // off-route (should not happen)
  const nxt = R[i + Math.sign(j - i)], ex = remote.exitTile(rm, c.room.name, nxt);
  if (c.pos.x === ex[0] && c.pos.y === ex[1]) { c.move(OFF(ex[0], ex[1])); return false; }
  move.to(c, ex[0], ex[1], 0); return false;
}
// Paused remote: at home the creep works with the home role that matches its body (reads the threat state only via remote.paused)
// pure rule (tests/remote_fixes.js): urgent <30k; batch <100k when full; free repair <100k while the source regenerates.
// batch was 50k (0247656): same repair ticks (= decay) but only ~1000t of pause buffer; R rarely empties so the free
// branch never topped it up (100k 11:00 -> 50.4k 13:10 10-16). 100k keeps the ~2000t buffer at no extra cost.
const REP = { urgent: 30000, batch: 100000, idle: 100000 };
function repairNow(hits, free, perHarvest, srcEmpty) {
  return hits < REP.urgent || (hits < REP.batch && free < perHarvest) || (srcEmpty && hits < REP.idle);
}
// 10-16 W45N7: the container (21,15) has only 3 free neighbours north (20-22,14) + 22,16 (22,15 is a foreign site, rest wall).
// Waiting rhaulers filled all of them; the replacement rminer orbited outside for ~700t, source untouched at 3000/3000.
// Rule: while our rminer is in the room but NOT yet on the container tile, rhaulers adjacent to the container back off to
// range 3 so the approach tiles are free; they come back once the miner sits on the container.
function yieldToMiner(c, C) {
  const [cx, cy] = C.cont, d = Math.max(Math.abs(c.pos.x - cx), Math.abs(c.pos.y - cy));
  const mine = c.room.find(FIND_MY_CREEPS, { filter: o => o.memory.role === 'rminer' && o.memory.remote === c.memory.remote });
  const minerIn = mine.some(o => o.pos.x === cx && o.pos.y === cy);
  if (mine.length && !minerIn) { if (d <= 2) awayFrom(c, cx, cy); return true; }
  return false;
}
function awayFrom(c, cx, cy) {
  const r = PathFinder.search(c.pos, { pos: new RoomPosition(cx, cy, c.room.name), range: 3 },
    { flee: true, maxRooms: 1, roomCallback: rn => move.foreignSites(rn, new PathFinder.CostMatrix()) });
  if (r.path.length) c.move(c.pos.getDirectionTo(r.path[0]));
}
const HOME = { rhauler: 'hauler', rminer: 'builder' };
function flee(c) {
  const C = remote.CFG[c.memory.remote];
  if (c.room.name === C.home && c.pos.x > 1 && c.pos.x < 48) {
    if (HOME[c.memory.role]) { c.memory.home = C.home; return require('./index')[HOME[c.memory.role]].run(c); }
    const [px, py] = C.park || [33, 26]; require('../utils/trace').why(c, 't'); return move.to(c, px, py, 1); }
  const [px, py] = C.park || [33, 26]; go(c, C.home, px, py, 1);
}
const roles = {
  rminer(c) {
    const C = remote.CFG[c.memory.remote]; if (remote.paused(c.memory.remote, 'rminer')) return flee(c);
    // travel = ticks to reach range 1 of the container (the old miner still sits on it; measuring on the tile itself
    // added the wait: 83654755 adjacent at ~+65, on tile +130 -> lead drifting to the 160 cap, ~50-100t overlap)
    if (c.memory.travel === undefined && c.ticksToLive && c.room.name === c.memory.remote && c.pos.isNearTo(C.cont[0], C.cont[1])) { const t = 1500 - c.ticksToLive; c.memory.travel = t >= 0 && t <= 300 ? t : 110; }
    if (!go(c, c.memory.remote, C.cont[0], C.cont[1], 0)) return;
    const src = c.room.lookForAt(LOOK_SOURCES, C.src[0], C.src[1])[0];
    const k = c.room.lookForAt(LOOK_STRUCTURES, C.cont[0], C.cont[1]).find(s => s.structureType === STRUCTURE_CONTAINER);
    // Unowned-room containers decay 50 hits/t; keep >=100k so it survives a ~1500-tick threat pause with nobody repairing
    // (30k lasted only 600 ticks: container lost during the 2026-10-13 Invader pause). Steady-state cost is the same (= decay).
    // Repair vs harvest (W45N8 review 2026-10-16): repair blocks harvest in the same tick. Urgent <30k: repair first.
    // <100k: batch — harvest until the store is full, then repair. Source empty (regen wait): repair for free up to 100k.
    if (k && c.store[RESOURCE_ENERGY] >= 10 && repairNow(k.hits, c.store.getFreeCapacity(), 2 * c.getActiveBodyparts(WORK), !src || src.energy === 0)) return c.repair(k);
    if (!k) { const s = c.room.lookForAt(LOOK_CONSTRUCTION_SITES, C.cont[0], C.cont[1])[0];
      if (!s) c.room.createConstructionSite(C.cont[0], C.cont[1], STRUCTURE_CONTAINER);
      // harvest and build share a tick: build only when the next harvest would overflow the store (or source empty)
      // -> ~25 built per 3.5 ticks = 7.1/t (was 5/t: building every 10 harvested)
      else if (c.store[RESOURCE_ENERGY] > 0 && (c.store.getFreeCapacity() < 2 * c.getActiveBodyparts(WORK) || !src || src.energy === 0)) return c.build(s); }
    if (src && src.energy > 0) c.harvest(src);
  },
  rhauler(c) {
    const C = remote.CFG[c.memory.remote]; if (remote.paused(c.memory.remote, 'rhauler')) return flee(c);
    if (c.memory.working && !c.memory.full && c.room.name === C.home && c.store[RESOURCE_ENERGY] > 0) return require('./hauler').run(c); // finish a home job after a pause
    c.memory.working = false;
    if (!c.memory.full && c.store.getFreeCapacity() === 0) { c.memory.full = true; c.memory.load = c.store[RESOURCE_ENERGY]; }
    if (c.memory.full && c.store[RESOURCE_ENERGY] === 0) { c.memory.full = false; c.memory.trips = (c.memory.trips || 0) + 1;
      const m = remote.mem(c.memory.remote); m.delivered = (m.delivered || 0) + (c.memory.load || 0); c.memory.load = 0; }
    if (c.memory.full) {
      if (c.memory.dep && c.room.name === C.home && c.pos.x < 48) { c.memory.rt = Game.time - c.memory.dep; delete c.memory.dep; } // measured round trip
      if (c.room.name !== C.home || c.pos.x >= 48) return go(c, C.home, 40, 20, 5);
      c.memory.working = true; require('./hauler').run(c); return;
    }
    if (c.room.name === C.home && c.store[RESOURCE_ENERGY] > 0 && c.store[RESOURCE_ENERGY] < 50) { c.memory.working = true; return require('./hauler').run(c); }
    // remote container gone (Invader / decay; rminer rebuilding it): nothing to collect -> haul at home until it exists (10-13: 2 rhaulers 100% idle)
    const R = Game.rooms[c.memory.remote];
    // multi-hop (W45N7, ~100t walk): leave once our site is >=60% so we arrive about when it completes
    if (R && c.store[RESOURCE_ENERGY] === 0 && !(C.via && (remote.mem(c.memory.remote).siteProg || 0) >= 3000) && !R.lookForAt(LOOK_STRUCTURES, C.cont[0], C.cont[1]).some(s => s.structureType === STRUCTURE_CONTAINER)
      && !R.find(FIND_DROPPED_RESOURCES).some(r => r.amount >= 100)) return flee(c);
    // too old for another round trip (2026-10-16: rhaulers died at the home exit holding 400/296): work at home, recycle when empty
    const S = require('../utils/salvage');
    if (c.room.name === C.home && c.ticksToLive && c.ticksToLive < (c.memory.rt || C.rt || 200) + 40) { c.memory.home = C.home; return require('./hauler').run(c); }
    if (c.room.name === C.home && !c.memory.dep) c.memory.dep = Game.time;
    if (c.room.name === c.memory.remote && c.pos.x > 0 && c.pos.x < 49) { const sv = S.pick(c); if (sv) { if (move.to(c, sv.pos.x, sv.pos.y, 1)) S.take(c, sv); return; } }
    if (!go(c, c.memory.remote, C.cont[0], C.cont[1], 1)) return;
    if (yieldToMiner(c, C)) return;
    const drop = c.pos.findInRange(FIND_DROPPED_RESOURCES, 2).find(r => r.resourceType === RESOURCE_ENERGY && r.amount >= 30);
    if (drop) { if (c.pickup(drop) === ERR_NOT_IN_RANGE) c.moveTo(drop, { costCallback: move.foreignSites }); return; }
    const k = c.room.lookForAt(LOOK_STRUCTURES, C.cont[0], C.cont[1]).find(s => s.structureType === STRUCTURE_CONTAINER);
    if (k && k.store[RESOURCE_ENERGY] >= 50) c.withdraw(k, RESOURCE_ENERGY);
    else if (c.store[RESOURCE_ENERGY] >= c.store.getCapacity() * 0.6 && (!k || k.store[RESOURCE_ENERGY] < 50) && (c.memory.wait = (c.memory.wait || 0) + 1) > 30) { c.memory.full = true; c.memory.load = c.store[RESOURCE_ENERGY]; c.memory.wait = 0; }
  },
  reserver(c) {
    const C = remote.CFG[c.memory.remote]; if (remote.paused(c.memory.remote)) return flee(c);
    if (!go(c, c.memory.remote, C.ctl[0], C.ctl[1], 1)) return;
    const ct = c.room.controller; if (!ct) return;
    if (ct.reservation && ct.reservation.username !== c.owner.username) return; // never attackController
    c.reserveController(ct);
    const S = require('../utils/sign'); if (S.needs(ct, c.owner.username)) c.signController(ct, S.SIGN);
  },
};
// Anti-NPC defender (docs/DEFENDER.md). Spawned on demand; engages owner 'Invader' only (never players); kites melee at range 3,
// closes to 3 on pure ranged; target = utils/focus.pickDef (net damage, healers first, mass attack on 3+ within 2, sticky on dying).
// Retreats home (<60% hp: tower heals it) or when it cannot win (focus.canWin) -> asks the FSM for a 2nd defender (threat.request2)
// and waits at the rally point until the partner is near. After the fight (Memory.defense.remotePatrol, default ON) it patrols
// W45N8 <-> W45N7 until TTL (lingers at the W45N8 south exit = the only way into W45N7); the FSM adopts it for the next THREAT.
// opt.approaching: target closed in since last tick (kite holds at >=4 off swamp); c.memory.kd = last step (direction inertia)
function kite(c, t, flee, approaching) {
  const C = remote.CFG[c.memory.remote], R = remote.route(c.memory.remote), i = R.indexOf(c.room.name);
  const ex = i > 0 ? remote.exitTile(c.memory.remote, c.room.name, R[i - 1]) : null; // our way home from here
  let d = require('../utils/kite').step(c, t, flee, ex, { approaching, last: c.memory.kd });
  if (d && C.avoid && c.room.name === c.memory.remote) { const D = [null, [0, -1], [1, -1], [1, 0], [1, 1], [0, 1], [-1, 1], [-1, 0], [-1, -1]][d];
    if (C.avoid.some(([x, y]) => x === c.pos.x + D[0] && y === c.pos.y + D[1])) d = 0; } // never step on the foreign site
  c.memory.kd = d || undefined; if (d) c.move(d); }
const meleeOf = h => h.body.some(p => p.type === ATTACK && p.hits > 0);
const rangedOf = h => h.body.some(p => p.type === RANGED_ATTACK && p.hits > 0);
const F = require('../utils/focus');
// patrol loop: [remoteKey(route), room, x, y, linger]
const PATROL = [['W45N7', 'W45N8', 24, 43, 40], ['W45N7', 'W45N7', 20, 12, 10], ['W45N7', 'W45N8', 24, 43, 40], ['W45N8', 'W45N8', 10, 8, 10]];
const patrolOn = () => require('../managers/home').on('remotePatrol');
function patrol(c) {
  const home = remote.CFG[c.memory.remote].home;
  // rooms not SAFE (Invaders waited out / players): skip their waypoints; nothing safe -> park at home
  const safe = rn => !remote.CFG[rn] || threat.state(rn).st === threat.S.SAFE;
  const blocked = Object.keys(remote.CFG).some(r => threat.state(r).why === 'player' && threat.state(r).st === threat.S.WAIT);
  const pts = PATROL.filter(([, rn]) => safe(rn) && !(rn === 'W45N7' && !safe('W45N8')));
  if (blocked || !pts.length) { const C = remote.CFG[c.memory.remote], [px, py] = C.park || [46, 21];
    return c.room.name === home ? move.to(c, px, py, 1) : go(c, home, px, py, 1); }
  let i = (c.memory.pi || 0) % pts.length; const [rr, rn, x, y, linger] = pts[i];
  if (c.room.name === rn && c.pos.inRangeTo(x, y, 2)) {
    c.memory.pw = c.memory.pw || Game.time;
    if (Game.time - c.memory.pw >= linger) { c.memory.pi = i + 1; delete c.memory.pw; }
    return;
  }
  delete c.memory.pw; go(c, rn, x, y, 2, rr);
}
const act = (c, t) => c.body.filter(p => p.type === t && p.hits > 0).length;
function threatInfo(c) { return { hits: c.hits, ra: act(c, RANGED_ATTACK), heal: act(c, HEAL) }; }
roles.defender = function (c) {
  // Reads the FSM only (managers/threat.js); never decides about players/escalation itself.
  const rm = c.memory.remote, C = remote.CFG[rm], th = threat.state(rm), K = threat.cfg(rm);
  const inRoom = !!remote.CFG[c.room.name] || (C.via || []).includes(c.room.name);
  const inv = inRoom ? c.room.find(FIND_HOSTILE_CREEPS).filter(h => h.owner.username === 'Invader') : [];
  // heal: hurt -> self; Invader within 4 -> pre-heal (damage lands this tick)
  if (c.hits < c.hitsMax || inv.some(h => c.pos.inRangeTo(h, 4))) c.heal(c);
  const here = c.room.name === rm;
  const mine = th.def === c.name || th.def2 === c.name, edge = c.pos.x === 0 || c.pos.x === 49 || c.pos.y === 0 || c.pos.y === 49;
  const fighting = mine && (th.st === threat.S.DEFEND || th.st === threat.S.THREAT);
  if (c.ticksToLive < 10) threat.noteRecycle(rm, c.name); // natural death (patrol to TTL) is not a combat loss
  // patrol until TTL instead of recycling (FSM adopts us for the next THREAT); the old TTL<80 recycle stays when patrol is off
  if (!fighting && patrolOn() && !c.memory.hurt) {
    c.memory.patrol = true; delete c.memory.lk;
    const t = inv.find(h => c.pos.inRangeTo(h, 3)); if (t) c.rangedAttack(t); // passing Invader: shoot, but don't chase (FSM decides)
    return patrol(c);
  }
  c.memory.patrol = false;
  c.memory.recycle = !patrolOn() && (!fighting || c.ticksToLive < 80); // recomputed each tick: a returning defender can be reused by a new THREAT
  if (c.hits < c.hitsMax * K.hp) c.memory.hurt = true; else if (c.hits >= c.hitsMax * K.hpBack) c.memory.hurt = false;
  if (c.memory.recycle || c.memory.hurt) {
    delete c.memory.lk;
    const t = inv.find(h => c.pos.inRangeTo(h, 3)); if (t) c.rangedAttack(t);
    // a melee Invader within 3 (e.g. camping the exit): get clear first; pathing home now walks into it (2026-10-15 death).
    // Exception: one step from the exit tile -> stepping onto it leaves the room this tick.
    const R = remote.route(rm), ri = R.indexOf(c.room.name), ex = ri > 0 ? remote.exitTile(rm, c.room.name, R[ri - 1]) : null;
    const m = inRoom && !edge && inv.find(h => meleeOf(h) && c.pos.inRangeTo(h, 3));
    if (m && ex && !c.pos.inRangeTo(ex[0], ex[1], 1)) return kite(c, m, true);
    if (c.room.name !== C.home || c.pos.x >= 48) { const sp = Game.spawns[C.spawn || 'Spawn1']; return go(c, C.home, sp ? sp.pos.x : 35, sp ? sp.pos.y : 28, 1); }
    if (c.memory.hurt && !c.memory.recycle) { const [px, py] = C.park || [33, 26]; return move.to(c, px, py, 1); } // tower heals it
    const sp = c.pos.findClosestByRange(FIND_MY_SPAWNS); if (!sp) return;
    if (c.pos.isNearTo(sp)) { threat.noteRecycle(rm, c.name); sp.recycleCreep(c); } else move.to(c, sp.pos.x, sp.pos.y, 1);
    return;
  }
  // can't win alone (heal >= our net / boosted out-trade): ask for a 2nd defender, wait at the rally point until it is near
  const partner = Game.creeps[th.def === c.name ? th.def2 : th.def];
  const rally = C.via ? [C.via[C.via.length - 1], 24, 43] : [C.home].concat(C.park || [46, 21]);
  const t0 = here && inv.length ? F.pickDef(c.pos, threatInfo(c).ra, inv, c.memory.tg) : null;
  if (t0 && !partner && !F.canWin(threatInfo(c), t0.h, inv)) threat.request2(rm);
  if ((threat.state(rm).need2 && !partner) || (partner && !partner.spawning && !(partner.room.name === c.room.name && c.pos.inRangeTo(partner, 6)))) {
    const t = inv.find(h => c.pos.inRangeTo(h, 3)); if (t) c.rangedAttack(t);
    return c.room.name === rally[0] ? move.to(c, rally[1], rally[2], 2) : go(c, rally[0], rally[1], rally[2], 2);
  }
  // on an exit tile with an Invader within 4 (exit campers): fight from here instead of blindly stepping toward the container
  if (!here || (edge && !inv.some(h => c.pos.inRangeTo(h, 4)))) return go(c, rm, C.cont[0], C.cont[1], 2);
  const P = t0, t = P ? P.h : null;
  // after a kill (FSM still DEFEND for clearTicks): hold at the kill spot (tombstone stays covered), don't walk to the container
  if (!t) { if (c.memory.lk) return; return move.to(c, C.cont[0], C.cont[1], 2); }
  c.memory.lk = [t.pos.x, t.pos.y]; c.memory.tg = t.id;
  const r = c.pos.getRangeTo(t), prev = c.memory.kr || 99;
  if (P.mass) c.rangedMassAttack();
  else if (r <= 3) c.rangedAttack(t);
  else { const n = inv.find(h => c.pos.inRangeTo(h, 3)); if (n) c.rangedAttack(n); } // goal out of range: shoot whatever is in range
  const mv = { range: 3, reusePath: 0, maxRooms: 1, plainCost: 2, swampCost: 10, costCallback: move.foreignSites };
  // pure ranged target (no ATTACK): kiting only gives it free shots — close to range 3 and trade (we out-heal/out-damage small ones)
  if (rangedOf(t) && !meleeOf(t)) { c.memory.kr = r; if (r > 3) { delete c.memory._m; c.moveTo(t, mv); } return; }
  // melee target (it chases us): within 8 let it come and hold range 3 (utils/kite); moveTo would walk into swamp -> 5-tick lock -> melee.
  // If it stops coming (busy elsewhere / wall in the way: range 4-8 not shrinking for 10 ticks), approach normally.
  c.memory.kw = r > 3 && r <= 8 && r >= (c.memory.kr || 99) ? (c.memory.kw || 0) + 1 : 0; c.memory.kr = r;
  if (meleeOf(t) && r <= 8 && c.memory.kw <= 10) return kite(c, t, false, r < prev);
  if (r > 3) { delete c.memory._m; c.moveTo(t, mv); }
};
// Vision fallback (no observer): 1 MOVE scout parks in the remote when nobody else gives vision (spawn.js decides when).
roles.rscout = function (c) {
  const C = remote.CFG[c.memory.remote], [x, y] = C.scout || C.cont;
  if (remote.paused(c.memory.remote)) return flee(c);
  go(c, c.memory.remote, x, y, 1);
};
module.exports = { repairNow, inward, rminer: { run: roles.rminer }, rhauler: { run: roles.rhauler }, reserver: { run: roles.reserver }, defender: { run: roles.defender }, rscout: { run: roles.rscout } };
