// Links (RCL5+): source link -> controller link (if < 400) -> filler links -> hub link.
// Hub link -> filler links when they run low (manager keeps the hub link topped up via room.memory.linkWant).
const plan = require('../utils/plan'), rc = require('../utils/roomcache');
module.exports = { run(room) {
  if (Game.time % 3) return;
  const links = rc.all(room, STRUCTURE_LINK); if (links.length < 2) return;
  const P = plan.get(room.name), at = (p) => p && links.find(l => l.pos.x === p[0] && l.pos.y === p[1]);
  const st = P.raw.stamps, center = n => { if (!st[n]) return null; const k = Object.keys(st[n].tiles).find(k => st[n].tiles[k] === 'L'); return k.split(',').map(Number); };
  const hub = links.find(l => l.pos.x === P.pos.manager[0] + 1 && l.pos.y === P.pos.manager[1] - 1) || links.find(l => l.pos.inRangeTo(P.pos.manager[0], P.pos.manager[1], 1));
  const ctl = at(P.pos.controllerLink);
  const fillers = ['A', 'B', 'C'].map(n => at(center(n))).filter(Boolean);
  const sources = links.filter(l => l !== hub && l !== ctl && !fillers.includes(l));
  const lowFill = fillers.filter(l => l.store[RESOURCE_ENERGY] < 400).sort((a, b) => a.store[RESOURCE_ENERGY] - b.store[RESOURCE_ENERGY]);
  for (const s of sources) {
    if (s.cooldown || s.store[RESOURCE_ENERGY] < 400) continue;
    const t = (ctl && ctl.store[RESOURCE_ENERGY] < 400 && ctl) || lowFill[0] || hub;
    if (t) s.transferEnergy(t);
  }
  room.memory.linkWant = lowFill.length || (ctl && ctl.store[RESOURCE_ENERGY] < 200) ? 1 : 0;
  if (hub && !hub.cooldown && hub.store[RESOURCE_ENERGY] >= 200) { const t = lowFill[0] || (ctl && ctl.store[RESOURCE_ENERGY] < 200 && ctl); if (t) hub.transferEnergy(t); }
} };
