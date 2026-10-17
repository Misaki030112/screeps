// Builder: picks a site once (priority order), walks a cached path, builds until done. Energy from fixed sources.
// With no sites it destroy()s (fallback: dismantles) empty unplanned containers (e.g. v1 leftover 31,11), keeps planned containers
// healthy, builds remote swamp-road sites when remote is not paused. Pre-storage: helps upgrade from the drop tile.
// With storage + no build/repair work: dump carry into storage and park (never moonlight at ctl / siphon source A).
// Repair work includes planned roads/containers <80% so paused remote→builder (rminer) stays useful;
// when even that is idle the remapped creep upgrades from fc/source containers (never drains the storage reserve).
const plan = require('../utils/plan'), move = require('../utils/move'), rc = require('../utils/roomcache');
const remote = require('../managers/remote'), trace = require('../utils/trace');
const PRIO = { spawn: 0, tower: 1, extension: 2, container: 3, storage: 4, link: 5, rampart: 6, road: 7 }; // match layout PRIORITY (tower before extension)
function remoteRoadSite() {
  for (const r in remote.CFG) {
    if (remote.paused(r) || remote.CFG[r].via) continue; // multi-hop W45N7: no road (docs/ROADS.md)
    const room = Game.rooms[r]; if (!room) continue;
    const roads = remote.CFG[r].roads || [];
    for (const [x, y] of roads) {
      const s = room.lookForAt(LOOK_CONSTRUCTION_SITES, x, y).find(z => z.structureType === STRUCTURE_ROAD);
      if (s) return s;
    }
    // any road site in the remote room (placed by us)
    const any = room.find(FIND_MY_CONSTRUCTION_SITES).find(s => s.structureType === STRUCTURE_ROAD);
    if (any) return any;
  }
  return null;
}
function junkContainer(room, P) {
  // ownerless leftover containers not in the plan, empty, safe to dismantle
  return rc.all(room, STRUCTURE_CONTAINER).find(s => {
    const want = P.any[plan.key(s.pos.x, s.pos.y)];
    return (!want || want.type !== 'container') && (s.store[RESOURCE_ENERGY] || 0) < 50 && s.hits > 0;
  }) || null;
}
function repairables(home, P) {
  // Planned roads/containers below 80%. At 60% (patrol 10-14 05:52) containers sat ~60.4% and planned roads
  // were all healthy, so paused rminer→builder still hit 87.6% no_task (idle at storage 38,30).
  return rc.all(home, STRUCTURE_ROAD).concat(rc.all(home, STRUCTURE_CONTAINER))
    .filter(s => (P.any[plan.key(s.pos.x, s.pos.y)] || (s.structureType === STRUCTURE_ROAD && require('../managers/roads').isHomeTile(s.pos.x, s.pos.y))) && s.hits < s.hitsMax * 0.8);
}
function hasBuildWork(home, P) {
  if (rc.sites(home).length) return true;
  if (remoteRoadSite()) return true;
  if (require('../managers/roads').repairTarget()) return true;
  return repairables(home, P).length > 0 || !!require('../managers/walls').repairJob(home);
}
function dumpToStorage(c, home) {
  const st = home.storage; if (!st) return false;
  if (c.store[RESOURCE_ENERGY] > 0) { if (move.to(c, st.pos.x, st.pos.y, 1)) c.transfer(st, RESOURCE_ENERGY); return true; }
  return false;
}
// Paused remote→builder (roles/remote HOME map): keep WORK busy when roads are healthy. Never siphon storage
// below the defender reserve — pull from filler A / source containers only (patrol 10-14 pause: storage ~100).
function remoteHelpUpgrade(c, home, P) {
  if (!c.memory.remote || !home.controller) return false;
  if (c.store[RESOURCE_ENERGY] > 0) {
    const [x, y] = P.pos.controllerDrop;
    if (move.to(c, x, y, 0)) c.upgradeController(home.controller);
    return true;
  }
  const [fx, fy] = P.pos.fillerContainerA;
  const cands = [rc.at(home, fx, fy, STRUCTURE_CONTAINER)].concat(require('./hauler').pickups(home))
    .filter(s => s && s.store[RESOURCE_ENERGY] >= 50);
  const src = cands.length ? _.max(cands, s => s.store[RESOURCE_ENERGY] / (c.pos.getRangeTo(s) + 15)) : null;
  if (!src) { trace.why(c, 'u'); return true; }
  if (move.to(c, src.pos.x, src.pos.y, 1)) c.withdraw(src, RESOURCE_ENERGY);
  return true;
}
// Starved builder waits in range of its site but OFF roads: parked on the 37,32/36,32 trunk it blocked the home
// hauler, whose detour through unpaved swamp cost ~50 ticks per source-A trip (patrol 10-15 02:53).
function waitNear(c, t, P) {
  if (!move.to(c, t.pos.x, t.pos.y, 3) || !c.room.lookForAt(LOOK_STRUCTURES, c.pos.x, c.pos.y).length) return;
  const T = c.room.getTerrain();
  for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) {
    const x = c.pos.x + dx, y = c.pos.y + dy;
    if ((!dx && !dy) || x < 1 || y < 1 || x > 48 || y > 48 || T.get(x, y) & TERRAIN_MASK_WALL || P.standing.has(plan.key(x, y))) continue;
    if (Math.max(Math.abs(t.pos.x - x), Math.abs(t.pos.y - y)) > 3) continue;
    if (c.room.lookForAt(LOOK_STRUCTURES, x, y).length || c.room.lookForAt(LOOK_CONSTRUCTION_SITES, x, y).length || c.room.lookForAt(LOOK_CREEPS, x, y).length) continue;
    c.move(c.pos.getDirectionTo(x, y)); return;
  }
}
// Energy pick across the whole home room (patrol 10-17 21:50: builders only looked 12 tiles out, then waitNear'd the
// link site at 30,11 while the ctl container held 1000 idle under the build hold; 3 builders crowded source A and
// starved the home haulers). Hub stores (storage above reserve, ctl container/link in hold, filler A, drops/tombstones)
// rank first; miner containers only when no hub store has energy, and then must keep >=200 for the haulers.
function pickSource(c, home, Ph, ctlSrc, fx, fy) {
  const reserve = require('../managers/threat').reserve(home.name);
  const amt = s => s.store ? s.store[RESOURCE_ENERGY] : s.amount;
  const hub = [home.storage, rc.at(home, fx, fy, STRUCTURE_CONTAINER)].concat(ctlSrc)
    .filter(s => s && s.store[RESOURCE_ENERGY] >= 50 + (s === home.storage ? reserve : 0));
  let loose = [];
  if (typeof FIND_DROPPED_RESOURCES !== 'undefined') {
    loose = home.find(FIND_DROPPED_RESOURCES).filter(r => r.resourceType === RESOURCE_ENERGY && r.amount >= 100)
      .concat(home.find(FIND_TOMBSTONES).filter(t => t.store[RESOURCE_ENERGY] >= 100));
  }
  const score = s => Math.min(amt(s), c.store.getFreeCapacity() || 50) / (c.pos.getRangeTo(s) + 15);
  let cands = hub.concat(loose);
  if (!cands.length) cands = require('./hauler').pickups(home).filter(s => s.store[RESOURCE_ENERGY] >= c.store.getFreeCapacity() + 200);
  return cands.length ? _.max(cands, score) : null;
}
module.exports = { remoteRoadSite, pickSource, run(c) {
  const room = c.room, P = plan.get(c.memory.home || room.name) || plan.get(room.name);
  if (!P) return;
  if (c.memory.working && c.store[RESOURCE_ENERGY] === 0) { c.memory.working = false; }
  if (!c.memory.working && c.store.getFreeCapacity() === 0) { c.memory.working = true; delete c.memory.src; }
  if (!c.memory.working) {
    // dismantle needs no energy; prefer it when we already flagged a junk target
    if (c.memory.dismantle) {
      const j = Game.getObjectById(c.memory.dismantle);
      if (j && j.hits > 0 && j.destroy() !== OK) { if (move.to(c, j.pos.x, j.pos.y, 1)) c.dismantle(j); return; }
      delete c.memory.dismantle;
    }
    // With storage + no sites a leftover builder used to siphon source A / moonlight at ctl and
    // kept storage off the 1300 defender reserve (patrol 10-14 04:53: builder83626083 at 31,29).
    const home0 = Game.rooms[c.memory.home] || room;
    if (home0.storage && !hasBuildWork(home0, plan.get(home0.name) || P)) {
      if (c.memory.remote) { if (remoteHelpUpgrade(c, home0, plan.get(home0.name) || P)) return; }
      if (dumpToStorage(c, home0)) return;
      const junk0 = junkContainer(home0, P);
      if (junk0 && junk0.destroy() === OK) return;
      if (junk0) { c.memory.dismantle = junk0.id; return; }
      // nothing left for 50t (e.g. the one-off remote road builder): recycle at the spawn instead of idling ~1200t (energy back);
      // the 50t grace keeps a home builder alive across short gaps between layout site batches
      if (!c.memory.remote && (c.memory.nt = (c.memory.nt || 0) + 1) > 50 && require('../utils/salvage').retire(c, 1500)) return;
      trace.why(c, 'n'); return;
    }
    delete c.memory.nt;
    // Remote road site (W45N8 2,12 swamp, 0/1500 since RCL5: no home sites -> no builder): refill from that remote's
    // container (often full at 2000 = overflow) instead of a ~50-tile round trip home; keep 400 for the rhaulers.
    const rt = c.memory.t && Game.getObjectById(c.memory.t), RC = rt && rt.pos.roomName === room.name && remote.CFG[room.name];
    if (RC && RC.cont) {
      const k = room.lookForAt(LOOK_STRUCTURES, RC.cont[0], RC.cont[1]).find(s => s.structureType === STRUCTURE_CONTAINER);
      if (k && k.store[RESOURCE_ENERGY] >= c.store.getFreeCapacity() + 400) { if (move.to(c, k.pos.x, k.pos.y, 1)) c.withdraw(k, RESOURCE_ENERGY); return; }
    }
    let src = c.memory.src && Game.getObjectById(c.memory.src);
    if (!src || (src.store ? src.store[RESOURCE_ENERGY] : src.amount) < 50) {
      const home = Game.rooms[c.memory.home] || room;
      const Ph = plan.get(home.name) || P;
      // Hub stores first (pickSource); ctl container only under the build hold — otherwise haulers feed it for upgraders
      // (builders sipping it kept ctlEma ~150 and pinned us to 1x8W, patrol 10-13 18:40).
      const [fx, fy] = Ph.pos.fillerContainerA;
      // build hold (walls.noUpgrade): nobody upgrades, so the ctl container / ctl link leftovers are builder energy
      const noUp = require('../managers/walls').noUpgrade(home), Pc = Ph.pos.controllerContainer, Pl = Ph.pos.controllerLink;
      const ctlSrc = noUp ? [rc.at(home, Pc[0], Pc[1], STRUCTURE_CONTAINER), Pl && rc.at(home, Pl[0], Pl[1], STRUCTURE_LINK)] : [];
      src = pickSource(c, home, Ph, ctlSrc, fx, fy);
      c.memory.src = src ? src.id : undefined;
      if (!src) {
        if (c.store[RESOURCE_ENERGY] > 0) { c.memory.working = true; return; } // build with what we carry
        const tw = c.memory.t && Game.getObjectById(c.memory.t);
        if (tw) waitNear(c, tw, Ph); trace.why(c, 'u'); return; // no energy anywhere: starved, not no_task
      }
    }
    if (move.to(c, src.pos.x, src.pos.y, 1)) { (src.store ? c.withdraw(src, RESOURCE_ENERGY) : c.pickup(src)); delete c.memory.src; }
    return;
  }
  let t = c.memory.t && Game.getObjectById(c.memory.t);
  if (t && t.hits !== undefined && t.progress === undefined && t.hits >= (c.memory.tcap || t.hitsMax * 0.9)) t = null;
  if (t && t.pos.roomName !== (c.memory.home || room.name) && remote.CFG[t.pos.roomName] && remote.paused(t.pos.roomName)) t = null; // remote under threat: leave
  if (t && c.memory.tcap && rc.sites(Game.rooms[c.memory.home] || room).length) t = null; // a new site outranks barrier hits
  // Stickiness must not skip a higher-priority site (patrol 10-14 22:40: tower 37,33 at 0 while extensions built).
  if (t && t.progress !== undefined) {
    const home = Game.rooms[c.memory.home] || room;
    if (rc.sites(home).some(s => (PRIO[s.structureType] ?? 9) < (PRIO[t.structureType] ?? 9))) t = null;
  }
  if (!t) {
    delete c.memory.tcap;
    const home = Game.rooms[c.memory.home] || room;
    const sites = rc.sites(home);
    if (sites.length) t = _.min(sites, s => (PRIO[s.structureType] ?? 9) * 100 + c.pos.getRangeTo(s));
    else {
      const junk = junkContainer(home, P);
      // containers in our own room can be destroyed instantly (ERR_BUSY while hostiles present -> dismantle fallback)
      if (junk && junk.destroy() === OK) return;
      if (junk) { c.memory.dismantle = junk.id; c.memory.working = false; delete c.memory.t; return; }
      const remoteSite = remoteRoadSite();
      if (remoteSite) t = remoteSite;
      else {
        const hurt = repairables(home, P);
        t = hurt.length ? _.min(hurt, s => s.hits / s.hitsMax) : null;
        if (!t) t = require('../managers/roads').repairTarget(); // remote route roads < 50% (docs/ROADS.md)
        const job = !t && require('../managers/walls').repairJob(home); // v4 barrier hits step (lowest first, +10k chunks)
        if (job) { t = Game.getObjectById(job.id); c.memory.tcap = job.cap; }
      }
    }
    c.memory.t = t ? t.id : undefined;
  }
  if (!t) {
    const home = Game.rooms[c.memory.home] || room;
    // Pre-storage only: help upgrade. With storage, dump carry then park — unless this is a paused remote helper.
    if (home.storage) {
      if (c.memory.remote && remoteHelpUpgrade(c, home, P)) return;
      if (dumpToStorage(c, home)) return; trace.why(c, 'n'); return;
    }
    const [x, y] = P.pos.controllerDrop; if (move.to(c, x, y, 0)) c.upgradeController(home.controller); return;
  }
  // cross-room: walk via remote fixed exits when target is in another room
  if (t.pos.roomName !== c.room.name) {
    const rName = t.pos.roomName;
    // walk the remote's fixed exits (W45N7 targets in W45N7: home -> W45N8 -> W45N7); targets in a via room (W45N7 road tiles in
    // W45N8) use the remote that lists that room: W45N8 itself.
    const C = remote.CFG[rName], path = C ? remote.route(rName) : null, i = path ? path.indexOf(c.room.name) : -1;
    if (C && i >= 0 && i < path.length - 1) {
      const [ex, ey] = remote.exitTile(rName, path[i], path[i + 1]);
      if (c.pos.x === ex && c.pos.y === ey) { c.move(ex === 49 ? RIGHT : ex === 0 ? LEFT : ey === 49 ? BOTTOM : TOP); return; }
      move.to(c, ex, ey, 0); return;
    }
    if (!(C && c.room.name === rName)) { move.to(c, t.pos.x, t.pos.y, 3); return; }
  }
  if (move.to(c, t.pos.x, t.pos.y, 3)) {
    const r = t.progress !== undefined ? c.build(t) : c.repair(t);
    if (r === OK && c.memory.tcap) require('../managers/walls').spend(c.room, Math.min(c.store[RESOURCE_ENERGY], c.getActiveBodyparts(WORK)));
    if (r !== OK && r !== ERR_NOT_ENOUGH_RESOURCES) delete c.memory.t;
    if (r === OK && t.progress !== undefined && t.progressTotal - t.progress <= c.getActiveBodyparts(WORK) * 5) { rc.invalidate(c.room.name); require('../utils/move').invalidate(c.room.name); }
  }
} };
