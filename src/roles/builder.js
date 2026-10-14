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
    if (remote.paused(r)) continue;
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
    .filter(s => P.any[plan.key(s.pos.x, s.pos.y)] && s.hits < s.hitsMax * 0.8);
}
function hasBuildWork(home, P) {
  if (rc.sites(home).length) return true;
  if (remoteRoadSite()) return true;
  return repairables(home, P).length > 0;
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
module.exports = { run(c) {
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
      trace.why(c, 'n'); return;
    }
    let src = c.memory.src && Game.getObjectById(c.memory.src);
    if (!src || src.store[RESOURCE_ENERGY] < 50) {
      const home = Game.rooms[c.memory.home] || room;
      const Ph = plan.get(home.name) || P;
      // Prefer hub stores (storage / filler A); source containers next. NEVER the controller container —
      // haulers feed ctl for upgraders; builders sipping it kept ctlEma ~150 and pinned us to 1x8W (patrol 10-13 18:40).
      const [fx, fy] = Ph.pos.fillerContainerA;
      const all = [home.storage, rc.at(home, fx, fy, STRUCTURE_CONTAINER)].concat(require('./hauler').pickups(home))
        .filter(s => s && s.store[RESOURCE_ENERGY] >= 50 + (s === home.storage ? require('../managers/threat').reserve(home.name) : 0)); // 50: was 100, left builders no_task while sites existed
      const tw = c.memory.t && Game.getObjectById(c.memory.t);
      let cands = all.filter(s => c.pos.getRangeTo(s) <= 12);
      if (!cands.length && tw) { move.to(c, tw.pos.x, tw.pos.y, 3); trace.why(c, 'u'); return; } // starved, not no_task
      if (!cands.length) cands = all;
      src = cands.length ? _.max(cands, s => s.store[RESOURCE_ENERGY] / (c.pos.getRangeTo(s) + 15)) : null;
      c.memory.src = src ? src.id : undefined;
      if (!src) { trace.why(c, 'u'); return; }
    }
    if (move.to(c, src.pos.x, src.pos.y, 1)) { c.withdraw(src, RESOURCE_ENERGY); delete c.memory.src; }
    return;
  }
  let t = c.memory.t && Game.getObjectById(c.memory.t);
  if (t && t.hits !== undefined && t.progress === undefined && t.hits >= t.hitsMax * 0.9) t = null;
  // Stickiness must not skip a higher-priority site (patrol 10-14 22:40: tower 37,33 at 0 while extensions built).
  if (t && t.progress !== undefined) {
    const home = Game.rooms[c.memory.home] || room;
    if (rc.sites(home).some(s => (PRIO[s.structureType] ?? 9) < (PRIO[t.structureType] ?? 9))) t = null;
  }
  if (!t) {
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
    const C = remote.CFG[rName];
    if (C && c.room.name === C.home) {
      const [ex, ey] = C.exitHome;
      if (c.pos.x === ex && c.pos.y === ey) { c.move(RIGHT); return; }
      move.to(c, ex, ey, 0); return;
    }
    if (C && c.room.name === rName) { /* fall through to build */ }
    else { move.to(c, t.pos.x, t.pos.y, 3); return; }
  }
  if (move.to(c, t.pos.x, t.pos.y, 3)) {
    const r = t.progress !== undefined ? c.build(t) : c.repair(t);
    if (r !== OK && r !== ERR_NOT_ENOUGH_RESOURCES) delete c.memory.t;
    if (r === OK && t.progress !== undefined && t.progressTotal - t.progress <= c.getActiveBodyparts(WORK) * 5) { rc.invalidate(c.room.name); require('../utils/move').invalidate(c.room.name); }
  }
} };
