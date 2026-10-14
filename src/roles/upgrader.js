// Upgrader on a fixed spot next to the controller container (30,30) / controller link (30,31). Never wanders.
const plan = require('../utils/plan'), move = require('../utils/move'), rc = require('../utils/roomcache');
// Desired controller sign (one constant). One upgrader detours 1-2 tiles to sign when it differs, then returns to its spot.
const SIGN = 'Peace grows here, guarded by steel. Cross in war, fall in silence. 和平在此，越界必诛。';
module.exports = { SIGN, run(c) {
  const room = c.room, P = plan.get(room.name), ctl = room.controller;
  if (ctl && ctl.my && (!ctl.sign || ctl.sign.text !== SIGN || ctl.sign.username !== (ctl.owner || {}).username)
      && !_.some(Game.creeps, x => x !== c && x.memory.signing)) {
    c.memory.signing = 1;
    if (c.pos.isNearTo(ctl)) { c.signController(ctl, SIGN); delete c.memory.signing; }
    else { move.to(c, ctl.pos.x, ctl.pos.y, 1); return; }
  } else if (c.memory.signing) delete c.memory.signing;
  if (!c.memory.spot) {
    const taken = new Set(_.filter(Game.creeps, x => x.memory.role === 'upgrader' && x.memory.spot).map(x => x.memory.spot.join()));
    c.memory.spot = P.pos.upgraders.find(s => !taken.has(s.join())) || P.pos.upgraders[P.pos.upgraders.length - 1];
  }
  const [x, y] = c.memory.spot;
  if (!move.to(c, x, y, 0)) {
    if (c.store[RESOURCE_ENERGY] > 0 && c.pos.inRangeTo(room.controller, 3)) c.upgradeController(room.controller);
    return;
  }
  // defender energy readiness without storage: stop drawing so haulers' energy goes to extensions (threat.holding)
  const hold = !room.storage && require('../managers/threat').holding(room.name);
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
