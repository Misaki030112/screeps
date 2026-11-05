// Links (RCL5+). Plan A (plan.LINK_PLAN): hub 37,29 + controller 30,31 at RCL5, source A 30,11 at RCL6.
// Senders (source links, hub) push to the controller link when it is below CTL_LOW and they hold >= SEND.
// The hub link is filled by the queen from storage surplus above the defender floor (queen.standby).
// With STATIONARY_FILL on, filler links (stamp centres) are also served before the hub.
const plan = require('../utils/plan'), rc = require('../utils/roomcache'), cmd = require('../utils/cmd');
const CTL_LOW = 400, SEND = 400;
const at = (links, p) => p && links.find(l => l.pos.x === p[0] && l.pos.y === p[1]);
function roles(room) {
  const links = rc.all(room, STRUCTURE_LINK), L = plan.LINK_PLAN || {};
  const hub = at(links, L.hub), ctl = at(links, L.ctl);
  let fillers = [];
  if (plan.STATIONARY_FILL) { const st = plan.get(room.name).raw.stamps;
    fillers = ['A', 'B', 'C'].map(n => { const k = st[n] && Object.keys(st[n].tiles).find(k => st[n].tiles[k] === 'L'); return k && at(links, k.split(',').map(Number)); }).filter(Boolean); }
  return { links, hub, ctl, fillers, sources: links.filter(l => l !== hub && l !== ctl && !fillers.includes(l)) };
}
const e = l => l.store[RESOURCE_ENERGY];
function ctlLinkLow(room) { const { hub, ctl } = roles(room); return !!(hub && ctl && e(ctl) < CTL_LOW); }
function target(R, room) { const noUp = room && require('./walls').noUpgrade(room);
  return (!noUp && R.ctl && e(R.ctl) < CTL_LOW && R.ctl) || R.fillers.filter(l => e(l) < 400).sort((a, b) => e(a) - e(b))[0] || null; }
module.exports = { CTL_LOW, SEND, roles, ctlLinkLow, run(room) {
  if (Game.time % 3) return;
  const R = roles(room); if (R.links.length < 2) return;
  for (const s of R.sources) { if ((cmd.armed() && cmd.consumeLink(s)) || s.cooldown || e(s) < SEND) continue; const t = target(R, room) || R.hub; if (t && t !== s) s.transferEnergy(t); }
  if (R.hub && !(cmd.armed() && cmd.consumeLink(R.hub)) && !R.hub.cooldown && e(R.hub) >= SEND) { const t = target(R, room); if (t) R.hub.transferEnergy(t); }
} };
