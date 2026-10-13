// Builder: picks a site once (priority order), walks a cached path, builds until done. Energy from fixed sources.
// With no sites it keeps planned containers healthy, then helps upgrade from the drop tile.
const plan = require('../utils/plan'), move = require('../utils/move'), rc = require('../utils/roomcache');
const PRIO = { spawn: 0, extension: 1, tower: 2, container: 3, storage: 4, link: 5, rampart: 6, road: 7 };
module.exports = { run(c) {
  const room = c.room, P = plan.get(room.name);
  if (c.memory.working && c.store[RESOURCE_ENERGY] === 0) { c.memory.working = false; }
  if (!c.memory.working && c.store.getFreeCapacity() === 0) { c.memory.working = true; delete c.memory.src; }
  if (!c.memory.working) {
    let src = c.memory.src && Game.getObjectById(c.memory.src);
    if (!src || src.store[RESOURCE_ENERGY] < 50) {
      const [fx, fy] = P.pos.fillerContainerA, [cx, cy] = P.pos.controllerContainer;
      const all = [room.storage].concat(require('./hauler').pickups(room), [rc.at(room, fx, fy, STRUCTURE_CONTAINER), rc.at(room, cx, cy, STRUCTURE_CONTAINER)])
        .filter(s => s && s.store[RESOURCE_ENERGY] >= 100);
      const tw = c.memory.t && Game.getObjectById(c.memory.t);
      let cands = all.filter(s => c.pos.getRangeTo(s) <= 12);
      // far from energy but has a job: wait at the work site, haulers bring energy to builders
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
    const sites = rc.sites(room);
    if (sites.length) t = _.min(sites, s => (PRIO[s.structureType] ?? 9) * 100 + c.pos.getRangeTo(s));
    else {
      const conts = rc.all(room, STRUCTURE_CONTAINER).filter(s => P.any[plan.key(s.pos.x, s.pos.y)] && s.hits < s.hitsMax * 0.5);
      t = conts.length ? _.min(conts, s => s.hits) : null;
    }
    c.memory.t = t ? t.id : undefined;
  }
  if (!t) { const [x, y] = P.pos.controllerDrop; if (move.to(c, x, y, 0)) c.upgradeController(room.controller); return; }
  if (move.to(c, t.pos.x, t.pos.y, 3)) {
    const r = t.progress !== undefined ? c.build(t) : c.repair(t);
    if (r !== OK && r !== ERR_NOT_ENOUGH_RESOURCES) delete c.memory.t;
    if (r === OK && t.progress !== undefined && t.progressTotal - t.progress <= c.getActiveBodyparts(WORK) * 5) { rc.invalidate(room.name); require('../utils/move').invalidate(room.name); }
  }
} };
