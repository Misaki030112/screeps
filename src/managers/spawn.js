// Spawn manager v2: per-RCL role table (docs/LAYOUT_V2.md). Counts come from Game.creeps (no room searches).
// Bodies are sized from energyCapacity; if the room has not been full for 300 ticks, sizes fall back to what is available.
const plan = require('../utils/plan'), rc = require('../utils/roomcache');
const rep = (n, p) => Array(Math.max(0, n)).fill(p);
const B = {
  // anti-Invader: 5 RANGED_ATTACK + 6 MOVE + 1 HEAL = 1300 (RCL4 full cap); 50 dmg/t at range 3, 12 hp/t self-heal
  defender: e => e >= 1300 ? [].concat(rep(5, RANGED_ATTACK), rep(6, MOVE), [HEAL]) : [].concat(rep(3, RANGED_ATTACK), rep(4, MOVE)),
  harvester: e => { const n = Math.max(1, Math.min(5, Math.floor(e / 200))); return [].concat(rep(n, WORK), rep(n, CARRY), rep(n, MOVE)); },
  miner: (e, carry) => { const c = carry ? 1 : 0; const w = Math.max(2, Math.min(5, Math.floor((e - 50 - c * 50) / 100)));
    const m = Math.max(1, Math.min(3, Math.floor((e - w * 100 - c * 50) / 50))); return [].concat(rep(w, WORK), rep(c, CARRY), rep(m, MOVE)); },
  hauler: e => { const n = Math.max(2, Math.min(8, Math.floor(e / 100))); return [].concat(rep(n, CARRY), rep(n, MOVE)); },
  queen: e => { const n = Math.max(2, Math.min(6, Math.floor(e / 150))); return [].concat(rep(2 * n, CARRY), rep(n, MOVE)); },
  upgrader: (e, rcl) => { const w = Math.max(1, Math.min(rcl >= 8 ? 15 : 10, Math.floor((e - 100) / 100))); return [].concat(rep(w, WORK), [CARRY, MOVE]); },
  builder: e => { const n = Math.max(1, Math.min(5, Math.floor(e / 200))); return [].concat(rep(n, WORK), rep(n, CARRY), rep(n, MOVE)); },
  filler: e => [CARRY, CARRY, CARRY, MOVE],
  manager: e => [].concat(rep(Math.min(16, Math.floor((e - 50) / 50)), CARRY), [MOVE]),
};
function targets(room, count, backlog, ctlEnergy, sites) {
  const rcl = room.controller.level, P = plan.get(room.name);
  const st = !!room.storage, links = rc.all(room, STRUCTURE_LINK).length;
  const T = {};
  T.hauler = rcl >= 7 && links >= 4 ? 0 : (rcl >= 6 && links >= 3 ? 1 : Math.min(4, 2 + Math.floor(backlog / 1500)));
  const fillersOn = rcl >= 5 && links >= 2;
  T.queen = fillersOn ? 0 : 1;
  T.filler = fillersOn ? 4 : 0;
  T.manager = st && rcl >= 5 ? 1 : 0;
  T.upgrader = rcl >= 8 ? 1 : Math.min(P.pos.upgraders.length, (sites ? 2 : 3) + Math.floor(ctlEnergy / 700));
  T.builder = sites ? (sites > 3 ? 2 : 1) : (rcl <= 4 ? 1 : 0);
  return T;
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
    if (live('rhauler') < 2) return go('rhauler', B.hauler(Math.min(E, 800)), { remote: r });
    if (live('rminer') < 1) { const w = Math.min(5, Math.floor((Math.min(E, 700) - 200) / 100)); return go('rminer', [].concat(rep(w, WORK), [CARRY], rep(3, MOVE)), { remote: r }); }
    if (live('rhauler') < 3 && m.cont && m.cont.e > 1200) return go('rhauler', B.hauler(Math.min(E, 800)), { remote: r });
  }
}
module.exports = { targets, run(spawn) {
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
    return spawn.spawnCreep(body, role + Game.time, { memory: Object.assign({ role, home: room.name }, mem) });
  };
  // 1) emergency: nothing can refill the spawn
  if (!(count.hauler || 0) && !(count.queen || 0) && !(count.harvester || 0) && !(count.filler || 0))
    return go(count.miner ? 'hauler' : 'harvester', count.miner ? B.hauler(Math.max(200, avail)) : B.harvester(Math.max(200, avail)));
  // 1b) defender: top of the queue; while collecting energy for it only miners/queen may still spawn (non-critical paused)
  const threat = require('./threat'), want = threat.wantDefender(room.name);
  if (want && rcl >= 4) {
    if (avail >= 1300) { const name = 'defender' + Game.time, rv = spawn.spawnCreep(B.defender(1300), name, { memory: { role: 'defender', home: room.name, remote: want, born: Game.time } });
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
  const T = targets(room, count, backlog, cc ? cc.store[RESOURCE_ENERGY] : 0, rc.sites(room).length);
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
    const e = role === 'queen' && !(count.hauler) ? Math.max(300, avail) : Math.min(E, role === 'hauler' ? 800 : role === 'queen' ? 600 : 3000);
    return go(role, B[role](e, rcl), mem);
  }
} };
