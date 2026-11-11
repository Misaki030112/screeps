// Upgrader on a fixed spot next to the controller container (30,30) / controller link (30,31). Never wanders.
const plan = require('../utils/plan'), move = require('../utils/move'), rc = require('../utils/roomcache');
const sign = require('../utils/sign'); // one-shot detour to sign when sign differs, then back to spot
module.exports = { run(c) {
  if (require('../utils/cmd').yieldCreep(c)) return;
  const room = c.room, P = plan.get(room.name), ctl = room.controller;
  if (ctl && ctl.my && sign.needs(ctl, (ctl.owner || {}).username)
      && !_.some(Game.creeps, x => x !== c && x.memory.signing)) {
    c.memory.signing = 1;
    if (c.pos.isNearTo(ctl)) { c.signController(ctl, sign.SIGN); delete c.memory.signing; }
    else { move.to(c, ctl.pos.x, ctl.pos.y, 1); return; }
  } else if (c.memory.signing) delete c.memory.signing;
  if (!c.memory.spot) {
    const taken = new Set(_.filter(Game.creeps, x => x.memory.role === 'upgrader' && x.memory.spot).map(x => x.memory.spot.join()));
    c.memory.spot = P.pos.upgraders.find(s => !taken.has(s.join())) || P.pos.upgraders[P.pos.upgraders.length - 1];
  }
  // build hold (walls.noUpgrade): spend what it carries, then recycle at the spawn (body energy back) instead of eating feed
  if (require('../managers/walls').noUpgrade(room)) {
    if (c.store[RESOURCE_ENERGY] > 0 && c.pos.inRangeTo(ctl, 3)) { c.upgradeController(ctl); return; }
    const sp = _.filter(Game.spawns, s => s.pos.roomName === room.name)[0];
    if (sp) { if (c.pos.isNearTo(sp)) sp.recycleCreep(c); else move.to(c, sp.pos.x, sp.pos.y, 1); }
    return;
  }
  // Surplus recycle (patrol 2026-11-01 soft-upgrade): when roleTargets.upgrader drops under defLow banking, extras keep
  // drawing the sole A-link feed. Name-order keep the first N; spend carry then recycle.
  // Patrol 2026-11-11 09:26: spawn.retiring() already drops a dying upgrader from the census so a
  // replacement pre-spawns, but this list still counted the dying one (name-order keeps the older
  // name). The newborn (upgrader84196699) was recycled on its first live tick next to the spawn,
  // then another replacement was queued — 50t spawn wasted and a ~20t zero-upgrader hole after the
  // incumbent died. Exclude retiring creeps with the same TTL rule as spawn.js (body*3+30).
  { const want = ((room.memory || {}).roleTargets || {}).upgrader;
    if (want !== undefined) {
      const retiring = (x) => !x.spawning && x.ticksToLive <= ((x.body && x.body.length) || 0) * 3 + 30;
      const ups = _.filter(Game.creeps, x => x.memory.role === 'upgrader' && (x.memory.home || x.room.name) === room.name && !x.spawning && !retiring(x))
        .sort((a, b) => a.name.localeCompare(b.name));
      if (ups.indexOf(c) >= want) {
        if (c.store[RESOURCE_ENERGY] > 0 && ctl && c.pos.inRangeTo(ctl, 3)) { c.upgradeController(ctl); return; }
        const sp = _.filter(Game.spawns, s => s.pos.roomName === room.name)[0];
        if (sp) { if (c.pos.isNearTo(sp)) sp.recycleCreep(c); else move.to(c, sp.pos.x, sp.pos.y, 1); }
        return;
      }
    }
  }
  const [x, y] = c.memory.spot;
  if (!move.to(c, x, y, 0)) {
    if (c.store[RESOURCE_ENERGY] > 0 && c.pos.inRangeTo(room.controller, 3)) c.upgradeController(room.controller);
    return;
  }
  // Remote defender collecting 1300 (threat.holding): stop drawing until spawn starts (th.def set).
  // With or without storage — keep ctl/link energy put so queen/haulers fill spawn/extensions first
  // (10-16 fight: 31t wait; home guards untouched — holding is remote-THREAT only).
  const hold = require('../managers/threat').holding(room.name);
  if (!hold && c.store[RESOURCE_ENERGY] <= c.getActiveBodyparts(WORK)) {
    const [lx, ly] = P.pos.controllerLink, [cx, cy] = P.pos.controllerContainer;
    const l = rc.at(room, lx, ly, STRUCTURE_LINK), k = rc.at(room, cx, cy, STRUCTURE_CONTAINER);
    const s = (l && l.store[RESOURCE_ENERGY] > 0) ? l : (k && k.store[RESOURCE_ENERGY] > 0 ? k : null);
    if (s) c.withdraw(s, RESOURCE_ENERGY);
    else { // energy dropped on the drop tile / on own tile
      const d = room.lookForAtArea(LOOK_RESOURCES, y - 1, x - 1, y + 1, x + 1, true)[0];
      if (d) c.pickup(d.resource);
    }
  }
  if (c.store[RESOURCE_ENERGY] > 0) c.upgradeController(room.controller);
} };
