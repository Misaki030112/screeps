// Home upgrade-feed observability (strategy 2026-10-31 02:4x).
// Writes Memory.ops.upgFeed — diagnose waiting_feed vs remote pause vs thin surplus.
// No spawn/link behavior change. Overmind UpgradeSite requests link receive below ~200 and
// logistics input when battery <50%; we keep CTL_LOW/SEND=400 + supply-follows-demand
// (no 3rd upgrader without surplus). See docs/MODEL.md "2026-10-31 02:4x".
const plan = require('../utils/plan'), rc = require('../utils/roomcache');
const queen = require('../roles/queen'), links = require('./links');
const remote = require('./remote'), threat = require('./threat');

// Flow nets from tools/flow.py (design); pause-adjusted ideal hint only.
const REMOTE_NET = { W45N8: 6.86, W45N7: 4.54 };

function run(room) {
  if (!room || !room.controller || !room.controller.my) return null;
  const P = plan.get(room.name);
  if (!P || !P.pos || !P.pos.controllerContainer) return null;
  const o = (Memory.ops = Memory.ops || {});
  const [cx, cy] = P.pos.controllerContainer;
  const k = rc.at(room, cx, cy, STRUCTURE_CONTAINER);
  const ctl = k ? (k.store[RESOURCE_ENERGY] || 0) : 0;
  const ctlEma = room.memory.ctlEma || 0;
  const L = links.roles(room);
  const ctlLinkE = L.ctl ? (L.ctl.store[RESOURCE_ENERGY] || 0) : null;
  const hubLinkE = L.hub ? (L.hub.store[RESOURCE_ENERGY] || 0) : null;
  const srcLinkE = L.sources.length ? (L.sources[0].store[RESOURCE_ENERGY] || 0) : null;
  const floor = queen.storageFloor(room);
  const storE = room.storage ? (room.storage.store[RESOURCE_ENERGY] || 0) : 0;
  const surplus = room.storage ? storE - floor : 0;
  const ups = _.filter(Game.creeps, c => c.memory.role === 'upgrader' && (c.memory.home || c.room.name) === room.name && !c.spawning);
  const nUp = ups.length;
  const work = ups.reduce((s, c) => s + c.getActiveBodyparts(WORK), 0);
  // Hungry = empty-ish carry AND neither ctl link nor container has energy (matches waiting_feed).
  const feedEmpty = (ctlLinkE == null || ctlLinkE === 0) && ctl === 0;
  const hungry = ups.filter(c => (c.store[RESOURCE_ENERGY] || 0) <= c.getActiveBodyparts(WORK) && feedEmpty).length;
  const rem = {};
  let pausedNet = 0;
  for (const r of Object.keys(remote.CFG || {})) {
    const th = threat.state(r);
    const st = (th && th.st) || 'SAFE';
    rem[r] = st;
    if (st !== 'SAFE' && REMOTE_NET[r]) pausedNet += REMOTE_NET[r];
  }
  // Ideal ~26 assumes all remotes; pause-adjusted ≈ ideal - pausedNet/(1+upkeep≈0.072)
  const idealAdj = Math.round((26 - pausedNet / 1.072) * 10) / 10;
  let why = 'ok';
  if (pausedNet > 0) why = 'remote_pause';
  else if (hungry > 0 && ctlEma < 400) why = 'ctl_starved';
  else if (surplus < 1000 && ctlEma < 700) why = 'thin_surplus';
  else if (hungry > 0) why = 'waiting_feed';
  const out = {
    t: Game.time, storE, floor, surplus: Math.round(surplus),
    ctl, ctlEma, ctlLinkE, hubLinkE, srcLinkE,
    nUp, work, hungry, pausedNet: Math.round(pausedNet * 100) / 100, idealAdj,
    rem: Object.keys(rem).map(r => r + ':' + rem[r]).join(','),
    why,
  };
  o.upgFeed = out;
  return out;
}

module.exports = { run, REMOTE_NET };
