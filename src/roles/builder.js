// Builder: picks a site once (priority order), walks a cached path, builds until done. Energy from fixed sources.
// With no sites it destroy()s (fallback: dismantles) empty unplanned containers (e.g. v1 leftover 31,11), keeps planned containers
// healthy, builds remote swamp-road sites when remote is not paused, then helps upgrade from the drop tile.
const plan = require('../utils/plan'), move = require('../utils/move'), rc = require('../utils/roomcache');
const remote = require('../managers/remote');
const PRIO = { spawn: 0, extension: 1, tower: 2, container: 3, storage: 4, link: 5, rampart: 6, road: 7 };
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
      if (!cands.length && tw) { move.to(c, tw.pos.x, tw.pos.y, 3); return; }
      if (!cands.length) cands = all;
      src = cands.length ? _.max(cands, s => s.store[RESOURCE_ENERGY] / (c.pos.getRangeTo(s) + 15)) : null;
      c.memory.src = src ? src.id : undefined;
      if (!src) return;
    }
    if (move.to(c, src.pos.x, src.pos.y, 1)) { c.withdraw(src, RESOURCE_ENERGY); delete c.memory.src; }
    return;
  }
  let t = c.memory.t && Game.getObjectById(c.memory.t);
  if (t && t.hits !== undefined && t.progress === undefined && t.hits >= t.hitsMax * 0.9) t = null;
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
        const conts = rc.all(home, STRUCTURE_CONTAINER).filter(s => P.any[plan.key(s.pos.x, s.pos.y)] && s.hits < s.hitsMax * 0.5);
        t = conts.length ? _.min(conts, s => s.hits) : null;
      }
    }
    c.memory.t = t ? t.id : undefined;
  }
  if (!t) { const [x, y] = P.pos.controllerDrop; if (move.to(c, x, y, 0)) c.upgradeController((Game.rooms[c.memory.home] || room).controller); return; }
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
