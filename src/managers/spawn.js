// Spawn manager v2: per-RCL role table (docs/LAYOUT_V2.md). Counts come from Game.creeps (no room searches).
// Bodies are sized from energyCapacity; if the room has not been full for 300 ticks, sizes fall back to what is available.
const plan = require('../utils/plan'), rc = require('../utils/roomcache');
const rep = (n, p) => Array(Math.max(0, n)).fill(p);
// Birth side. The extension stamp around the spawn is closed except through its fill container, and the default order
// (TOP first) put new creeps on filler tile 36,27 inside it: they walked out through the queen ring, and
// upgrader83620552 (10W1C1M) needed 274 ticks from spawn to 31,30 (10-13 22:27). Born outside the stamp first;
// queen/fillers inside (any stamp tile counts as inside). All 8 directions stay in the list, so a blocked side falls back to the engine default.
const DXY = { 1: [0, -1], 2: [1, -1], 3: [1, 0], 4: [1, 1], 5: [0, 1], 6: [-1, 1], 7: [-1, 0], 8: [-1, -1] };
function birthDirs(spawn, role) {
  const P = plan.get(spawn.room.name); if (!P) return undefined;
  const inside = new Set([].concat(...Object.values(P.raw.stamps).map(st => Object.keys(st.tiles))).map(k => { const [x, y] = k.split(',').map(Number); return plan.key(x, y); }));
  const isIn = d => inside.has(plan.key(spawn.pos.x + DXY[d][0], spawn.pos.y + DXY[d][1]));
  const want = role === 'queen' || role === 'filler', all = [1, 2, 3, 4, 5, 6, 7, 8];
  return all.filter(d => isIn(d) === want).concat(all.filter(d => isIn(d) !== want));
}
const B = {
  // anti-Invader: 5 RANGED_ATTACK + 6 MOVE + 1 HEAL = 1300 (RCL4 full cap); 50 dmg/t at range 3, 12 hp/t self-heal
  defender: e => e >= 1300 ? [].concat(rep(5, RANGED_ATTACK), rep(6, MOVE), [HEAL]) : [].concat(rep(3, RANGED_ATTACK), rep(4, MOVE)),
  harvester: e => { const n = Math.max(1, Math.min(5, Math.floor(e / 200))); return [].concat(rep(n, WORK), rep(n, CARRY), rep(n, MOVE)); },
  miner: (e, carry) => { const c = carry ? 1 : 0; const w = Math.max(2, Math.min(5, Math.floor((e - 50 - c * 50) / 100)));
    const m = Math.max(1, Math.min(3, Math.floor((e - w * 100 - c * 50) / 50))); return [].concat(rep(w, WORK), rep(c, CARRY), rep(m, MOVE)); },
  hauler: e => { const n = Math.max(2, Math.min(8, Math.floor(e / 100))); return [].concat(rep(n, CARRY), rep(n, MOVE)); },
  // home hauler with storage: the A->ctl route is fully paved, so 2 CARRY : 1 MOVE still moves 1 tile/tick loaded
  roadHauler: e => { const n = Math.max(1, Math.min(8, Math.floor(e / 150))); return [].concat(rep(2 * n, CARRY), rep(n, MOVE)); },
  queen: e => { const n = Math.max(2, Math.min(6, Math.floor(e / 150))); return [].concat(rep(2 * n, CARRY), rep(n, MOVE)); },
  // Upgraders walk once (spawn -> ctl spot, ~6 tiles) then sit, so 1 MOVE is enough. RCL4: 2x10W = 20 WORK was the binding
  // limit (1h upgrade ~19/t, ctl container 1000+ unused, storage parked at the ferry floor so the 3rd-upgrader gate never opened;
  // patrol 10-14 10:55). Cap 12 -> 12W1C1M = 1300 = RCL4 full cap, 2x12 = 24 WORK ~ model ideal 23.5.
  upgrader: (e, rcl) => { const w = Math.max(1, Math.min(rcl >= 8 ? 15 : 12, Math.floor((e - 100) / 100))); return [].concat(rep(w, WORK), [CARRY, MOVE]); },
  builder: e => { const n = Math.max(1, Math.min(5, Math.floor(e / 200))); return [].concat(rep(n, WORK), rep(n, CARRY), rep(n, MOVE)); },
  filler: e => [CARRY, CARRY, CARRY, MOVE],
  manager: e => [].concat(rep(Math.min(16, Math.floor((e - 50) / 50)), CARRY), [MOVE]),
};
function targets(room, count, backlog, ctlEnergy, sites) {
  const rcl = room.controller.level, P = plan.get(room.name);
  const st = !!room.storage, links = rc.all(room, STRUCTURE_LINK).length;
  const T = {};
  // With storage, miner B dumps adjacent (38,32→37,31) so only source A needs a hauler: 1×14C7M road hauler (see body note below).
  // Pre-storage keep 2 so both containers drain. Backlog can still add one extra.
  T.hauler = rcl >= 7 && links >= 4 ? 0 : (rcl >= 6 && links >= 3 ? 1 : (st ? Math.min(2, 1 + Math.floor(backlog / 1500)) : Math.min(4, 2 + Math.floor(backlog / 1500))));
  const fillersOn = rcl >= 5 && links >= 2;
  T.queen = fillersOn ? 0 : 1;
  T.filler = fillersOn ? 4 : 0;
  T.manager = st && rcl >= 5 ? 1 : 0;
  // Supply-follows-demand on the smoothed ctl container level (ctlEnergy = ~300-tick EMA): an empty container means upgraders
  // outnumber the feed. A snapshot rule (3 + level/700) spawned 4x7 WORK for ~11/t feed -> upgraders idle 55% waiting_feed (10-13 17:30).
  // With storage, the 3rd+ upgrader needs real surplus: storage SURPLUS above the queen's ferry floor (max(defender reserve, cap)).
  // Below that the queen still ferries storage->ctl, so a full ctl container is only a transient (e.g. a container A backlog drain).
  // Gate at the bare reserve (1300) spawned a 3rd 10W at ~08:00 10-14 while the ferry had not even started (floor+carry 1700):
  // waiting_feed 0-18% (2 upgraders, 07:30-07:59) -> 45-47% (3 upgraders, 08:00-08:14). (patrol 10-14 04:53 had the same: storage ~100.)
  const SURPLUS = 1000;
  const extra = Math.floor(ctlEnergy / 700);
  const allowExtra = !st || room.storage.store[RESOURCE_ENERGY] >= require('../roles/queen').storageFloor(room) + SURPLUS;
  T.upgrader = rcl >= 8 ? 1 : Math.min(P.pos.upgraders.length, (sites ? 1 : 2) + (allowExtra ? extra : 0));
  // RCL4 extension push: 2 builders need ~40 e/t but net income ~22 -> spawn/ctl starve, builders no_task ~28%,
  // haulers wait on empty pickups (patrol 10-13 18:40). One fed builder finishes sites faster than two hungry ones.
  // Second builder only after cap>=1300 (20 ext, CLAIM2-ready) when the room can afford the extra demand.
  // With storage + sites=0 a lone builder cannot withdraw below threat.reserve, walks to source A / upgrades as a
  // hungry 5W, and keeps storage off the 1300 defender cushion (patrol 10-14 02:54 → 03:54, storage 1040→50→~100).
  T.builder = sites ? (sites > 3 && room.energyCapacityAvailable >= 1300 ? 2 : 1) : (st ? 0 : (rcl <= 4 ? 1 : 0));
  return T;
}
// Pure rule for remote hauler early-replace (exported for unit tests).
function rhaulerNeed(liveCount, allCount, target) {
  target = target === undefined ? 2 : target;
  return liveCount < target && allCount < target + 1;
}
// Remote mining (managers/remote.js): after home miners/queen/haulers, before fillers/upgraders/builders.
// CLAIM1 nets 0 reservation ticks; a low buffer never recovers unless two CLAIM1 overlap (+1/t) or we reach CLAIM2 at RCL4.
function remoteSpawn(room, E, go, rcl) {
  const remote = require('./remote');
  for (const r in remote.CFG) {
    if (remote.CFG[r].home !== room.name) continue;
    if (remote.paused(r)) continue; // defender is spawned from the top of run() (threat.wantDefender)
    const m = remote.mem(r);
    const res = (m.res && m.res.ticksToEnd) || 0;
    const wantRes = (res > 0 && res < 800) ? 2 : 1; // overlap rebuilds buffer while CLAIM1-only
    const resLead = 150; // travel ~40 + spawn + margin (was 80; late spawn left ticksToEnd≈13)
    const live = role => _.filter(Game.creeps, c => c.memory.remote === r && c.memory.role === role && (c.spawning || c.ticksToLive > (role === 'reserver' ? resLead : 120))).length;
    const nRes = _.filter(Game.creeps, c => c.memory.remote === r && c.memory.role === 'reserver' && (c.spawning || (c.ticksToLive || 1500) > 30)).length;
    // Reserver before haulers when buffer is thin so the 650 cost is not spent on a 3rd rhauler
    if (nRes < wantRes && res < 4000 && E >= 650) return go('reserver', E >= 1300 ? [CLAIM, CLAIM, MOVE, MOVE] : [CLAIM, MOVE], { remote: r });
    // RCL4 target is 2×8C8M. Early-replace at TTL≤120: both rhaulers born ~50t apart age out together and
    // would spawn 2 replacements on top of 2 dying → 4 creeps / ~1600e wipe (patrol 10-14 09:51: energy 1300→4).
    // Cap total (dying+new) at target+1 so only one overlap is in flight.
    const allRh = _.filter(Game.creeps, c => c.memory.remote === r && c.memory.role === 'rhauler').length;
    if (rhaulerNeed(live('rhauler'), allRh)) return go('rhauler', B.hauler(Math.min(E, 800)), { remote: r });
    if (live('rminer') < 1) { const w = Math.min(5, Math.floor((Math.min(E, 700) - 200) / 100)); return go('rminer', [].concat(rep(w, WORK), [CARRY], rep(3, MOVE)), { remote: r }); }
    // A 3rd was opportunistic on cont>1200 but left waiting_pickup idle while the container sat near empty
    // (patrol 10-14 03:55: 3 rhaulers, cont ~20e). Keep energy for home upgraders / storage reserve instead.
  }
}
module.exports = { targets, rhaulerNeed, B, run(spawn) {
  if (spawn.spawning) return;
  const room = spawn.room, cap = room.energyCapacityAvailable, avail = room.energyAvailable, rcl = room.controller.level;
  if (avail >= cap) room.memory.lastFull = Game.time;
  const starving = Game.time - (room.memory.lastFull || Game.time) > 300;
  const E = starving ? Math.max(300, avail) : cap;
  const mine = _.filter(Game.creeps, c => c.memory.home === room.name || (!c.memory.home && c.room.name === room.name));
  const count = _.countBy(mine, c => c.memory.role);
  const P = plan.get(room.name);
  const go = (role, body, mem = {}) => {
    const cost = _.sum(body, p => BODYPART_COST[p]);
    if (avail < cost) return ERR_NOT_ENOUGH_ENERGY;
    return spawn.spawnCreep(body, role + Game.time, { memory: Object.assign({ role, home: room.name }, mem), directions: birthDirs(spawn, role) });
  };
  // 1) emergency: nothing can refill the spawn
  if (!(count.hauler || 0) && !(count.queen || 0) && !(count.harvester || 0) && !(count.filler || 0))
    return go(count.miner ? 'hauler' : 'harvester', count.miner ? B.hauler(Math.max(200, avail)) : B.harvester(Math.max(200, avail)));
  // 1b) defender: top of the queue; while collecting energy for it only miners/queen may still spawn (non-critical paused)
  const threat = require('./threat'), want = threat.wantDefender(room.name);
  if (want && rcl >= 4) {
    if (avail >= 1300) { const name = 'defender' + Game.time, rv = spawn.spawnCreep(B.defender(1300), name, { memory: { role: 'defender', home: room.name, remote: want, born: Game.time }, directions: birthDirs(spawn, 'defender') });
      if (rv === OK) threat.noteSpawn(want, name); return rv; }
  }
  const hold = !!want;
  // 2) miners (pre-spawned for travel time)
  // miner83614486 (10-13) arrived 115 ticks early and idled next to its predecessor: unmeasured travel defaulted to 100 (real ~30)
  const lead = c => Math.min(c.memory.travel || 40, 80) + c.body.length * 3;
  if (!room.memory.sources) room.memory.sources = room.find(FIND_SOURCES).map(s => s.id);
  for (const s of room.memory.sources.map(id => Game.getObjectById(id)).filter(Boolean)) {
    if (!mine.some(c => c.memory.role === 'miner' && c.memory.sourceId === s.id && (c.ticksToLive || 1500) > lead(c))) {
      const carry = rcl >= 4;
      return go('miner', B.miner(Math.min(E, carry ? 800 : 650), carry), { sourceId: s.id });
    }
  }
  if (hold) { if (!(count.queen || 0) && !(count.filler || 0)) return go('queen', B.queen(Math.max(300, avail))); return ERR_BUSY; }
  const hp = require('../roles/hauler');
  const backlog = _.sum(hp.pickups(room), s => s.store[RESOURCE_ENERGY]);
  const [cx, cy] = P.pos.controllerContainer; const cc = rc.at(room, cx, cy, STRUCTURE_CONTAINER);
  const m = room.memory, ce = cc ? cc.store[RESOURCE_ENERGY] : 0;
  m.ctlEma = m.ctlEma === undefined ? ce : m.ctlEma + (ce - m.ctlEma) * Math.min(1, (Game.time - (m.ctlEmaT || Game.time)) / 300);
  m.ctlEma = Math.round(m.ctlEma); m.ctlEmaT = Game.time;
  const T = targets(room, count, backlog, m.ctlEma, rc.sites(room).length);
  room.memory.roleTargets = T;
  for (const role of ['queen', 'hauler', 'REMOTE', 'filler', 'manager', 'upgrader', 'builder']) {
    if (role === 'REMOTE') {
      // Critical reservation: still spawn even when home is starving (CLAIM1 buffer ~13 ticks is fragile)
      let criticalRes = false;
      const remote = require('./remote');
      for (const rr in remote.CFG) { if (remote.CFG[rr].home !== room.name) continue; const mm = remote.mem(rr); const rv = (mm.res && mm.res.ticksToEnd) || 0; if (rv > 0 && rv < 100) criticalRes = true; }
      if (!starving || criticalRes) { const r = remoteSpawn(room, E, go, rcl); if (r !== undefined) return r; } continue;
    }
    if ((count[role] || 0) >= T[role]) continue;
    const mem = {};
    if (role === 'filler') { const used = new Set(mine.filter(c => c.memory.role === 'filler').map(c => c.memory.spot.join())); mem.spot = P.pos.fillers.slice(0, 4).find(s => !used.has(s.join())); }
    // Home hauler: 8C8M pre-storage. With storage it hauls source A -> ctl container (27 tiles, measured cycle ~57-66t, not the
    // model's A->hub rt 28): 10/t x 66 = 660 carry -> one 14C7M road hauler (700, 1050e). 2x6C6M (600 carry) let
    // container A pile up to 1771/2000 (patrol 10-14 07:05) while upgraders sat waiting_feed ~50%.
    const e = role === 'queen' && !(count.hauler) ? Math.max(300, avail) : Math.min(E, role === 'hauler' ? (room.storage ? 1050 : 800) : role === 'queen' ? 600 : 3000);
    return go(role, role === 'hauler' && room.storage ? B.roadHauler(e) : B[role](e, rcl), mem);
  }
} };
