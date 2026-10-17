// Queen (RCL2-4): fills spawn/extensions/tower by walking a FIXED list of stops (filler tiles of stamp A + hub tile);
// at each stop it transfers to the fixed neighbour structures that need energy. Energy from filler container A /
// storage / source containers. From RCL5 stationary fillers + manager take over.
const plan = require('../utils/plan'), move = require('../utils/move'), rc = require('../utils/roomcache');
const N8 = [[-1, -1], [0, -1], [1, -1], [-1, 0], [1, 0], [-1, 1], [0, 1], [1, 1]];
const FILL = new Set([STRUCTURE_SPAWN, STRUCTURE_EXTENSION, STRUCTURE_TOWER]);
const H = {}; // heap: room -> {t, stops:[{x,y,ids}]}
function stops(room) {
  let h = H[room.name];
  if (!h || Game.time - h.t > 50) {
    const P = plan.get(room.name);
    const tiles = P.pos.fillers.slice(0, 4).concat([P.pos.manager]);
    const st = [], covered = new Set(), at = rc.get(room).at;
    const walkable = (x, y) => { const e = at[x * 50 + y]; return !e || Object.keys(e).every(t => t === 'road' || t === 'container' || t === 'rampart'); };
    for (const [x, y] of tiles) {
      if (!walkable(x, y)) continue;
      const ids = [];
      for (const [dx, dy] of N8) { const e = at[(x + dx) * 50 + y + dy]; if (e) for (const t in e) if (FILL.has(t)) { ids.push(e[t]); covered.add(e[t]); } }
      if (ids.length) st.push({ x, y, ids, r: 0 });
    }
    // anything not reachable from a stop (e.g. old v1 extensions until removed): visit directly
    for (const t of FILL) for (const s of rc.all(room, t)) if (!covered.has(s.id)) st.push({ x: s.pos.x, y: s.pos.y, ids: [s.id], r: 1 });
    h = H[room.name] = { t: Game.time, st };
  }
  return h.st;
}
function needy(id) { const s = Game.getObjectById(id); return s && s.store.getFreeCapacity(RESOURCE_ENERGY) > (s.structureType === STRUCTURE_TOWER ? 100 : 0) ? s : null; } // towers topped to ≥900
function fillRoute(c) {
  const st = stops(c.room);
  // current stop: transfer to one needy neighbour per tick
  let cur = c.memory.stop !== undefined ? st[c.memory.stop] : null;
  if (cur && c.pos.inRangeTo(cur.x, cur.y, cur.r)) {
    const t = cur.ids.map(needy).find(Boolean);
    if (t) { c.transfer(t, RESOURCE_ENERGY); return true; }
    cur = null;
  }
  if (!cur || !cur.ids.some(needy)) {
    let best = -1, bd = 1e9;
    const war = require('../managers/home').active(c.room), tw = s => war && s.ids.some(id => { const o = Game.getObjectById(id); return o && o.structureType === STRUCTURE_TOWER && o.store.getFreeCapacity(RESOURCE_ENERGY) > 100; });
    st.forEach((s, i) => { if (s.ids.some(needy)) { const d = c.pos.getRangeTo(s.x, s.y) - (tw(s) ? 100 : 0); if (d < bd) { bd = d; best = i; } } });
    if (best < 0) { delete c.memory.stop; return false; }
    c.memory.stop = best; cur = st[best];
  }
  if (move.to(c, cur.x, cur.y, cur.r)) { const t = cur.ids.map(needy).find(Boolean); if (t) c.transfer(t, RESOURCE_ENERGY); }
  return true;
}
// Room full (52% of queen time historically): ferry surplus -> controller / hub link while ctl feed is low.
// Source: storage SURPLUS above the defender reserve, else filler container A above 400 for the next refill.
// Without the storage leg source B + remote energy never reached the controller (10-14 06:58: upgrade 9.7/t, storage
// spent on spawns, upgraders waiting_feed ~50%); with no floor it drained storage to ~100 (05:50), hence the floor.
// Require floor+carry (e7c3966) left a dead band: storage 1300..1699 with ctl empty and upgraders waiting_feed while the
// queen parked target_full (patrol 10-14 13:35: storage 1473-1673, ctl 0 for ~40t stretches, upgrade avg ~18 vs 24 when fed).
// Ferry any surplus above the floor (partial withdraw); never dip below the floor.
// RCL5 bug (patrol 10-15 06:53): max(reserve, energyCapacityAvailable) became 1800 once cap hit 1800, so storage
// sitting at 1300..1600 never ferried — hub link stayed empty, link plan A idle, upgraders waiting_feed while spawn
// was full for 100+ ticks. Floor is the defender reserve when armed; spawn cap only as the unarmed fallback
// (standby already runs only when spawn/tower are full, so spawn refill does not need a floor).
function storageFloor(room) {
  const r = require('../managers/threat').reserve(room.name);
  return (r || room.energyCapacityAvailable) + require('../managers/walls').reserved(room); // wall fund is not ferry energy
}
// RCL5+ link plan A: with hub + controller links built, the ferry target is the hub link (2 tiles from storage) instead of
// walking to the controller container; links.js forwards hub -> controller link.
function standby(c, room, P) {
  const H = require('./hauler'), Lk = require('../managers/links');
  if (require('../managers/walls').noUpgrade(room)) return false; // build hold: no storage -> controller ferry
  const hub = Lk.ctlLinkLow(room) && Lk.roles(room).hub;
  const toHub = hub && hub.store.getFreeCapacity(RESOURCE_ENERGY) > 0;
  if (!toHub && !H.ctlLow(room, P)) return false;
  const [cx, cy] = P.pos.controllerContainer, [fx, fy] = P.pos.fillerContainerA;
  if (c.store[RESOURCE_ENERGY] > 0) {
    if (toHub) { if (move.to(c, hub.pos.x, hub.pos.y, 1)) c.transfer(hub, RESOURCE_ENERGY); return true; }
    const k = rc.at(room, cx, cy, STRUCTURE_CONTAINER); if (H.handoff(c)) return true; if (move.to(c, cx, cy, 1)) c.transfer(k, RESOURCE_ENERGY); return true; }
  const cap = c.store.getCapacity(), st = room.storage, a = rc.at(room, fx, fy, STRUCTURE_CONTAINER);
  const floor = storageFloor(room);
  const surplus = st ? st.store[RESOURCE_ENERGY] - floor : 0;
  const src = surplus > 0 ? st : a && a.store[RESOURCE_ENERGY] >= 400 + cap ? a : null;
  if (!src) return false;
  if (move.to(c, src.pos.x, src.pos.y, 1)) c.withdraw(src, RESOURCE_ENERGY, src === st ? Math.min(cap, surplus) : undefined); return true;
}
module.exports = { fillRoute, storageFloor, run(c) {
  const room = c.room, P = plan.get(room.name);
  room.memory.queenAlive = Game.time;
  if (c.memory.working && c.store[RESOURCE_ENERGY] === 0) c.memory.working = false;
  if (!c.memory.working && c.store.getFreeCapacity() === 0) c.memory.working = true;
  if (!c.memory.working && require('../utils/salvage').retire(c, 25)) return; // 2026-10-16: queen died holding 200
  const full = room.energyAvailable >= room.energyCapacityAvailable && !rc.all(room, STRUCTURE_TOWER).some(t => t.store[RESOURCE_ENERGY] < 900);
  if (c.memory.working || (full && c.store[RESOURCE_ENERGY] > 0)) {
    if (!full) { if (fillRoute(c)) return; }
    // ctl ferry via standby (storage only above storageFloor, else fc)
    if (full && standby(c, room, P)) return;
    if (c.store.getFreeCapacity() === 0 || full) {
      // dump leftover carry back to storage before parking (was sitting target_full with 360–400e)
      if (full && room.storage && c.store[RESOURCE_ENERGY] > 0) {
        if (move.to(c, room.storage.pos.x, room.storage.pos.y, 1)) c.transfer(room.storage, RESOURCE_ENERGY);
        return;
      }
      const [x, y] = P.pos.fillers[0]; move.to(c, x, y, 0); require('../utils/trace').why(c, 'f'); return;
    }
    c.memory.working = false;
  }
  // Spawn/tower full: no refill for the fill route; standby ferries surplus (storage above floor / fc) to ctl when ctlLow.
  if (full) {
    if (standby(c, room, P)) return;
    const [x, y] = P.pos.fillers[0]; move.to(c, x, y, 0); require('../utils/trace').why(c, 'f'); return;
  }
  // refill: storage > filler container A > source container (fixed list) — only when spawn/tower need energy
  let src = c.memory.src && Game.getObjectById(c.memory.src);
  if (!src || src.store[RESOURCE_ENERGY] < 50) {
    const [fx, fy] = P.pos.fillerContainerA;
    const near = require('./hauler').pickups(room).filter(s => s.store[RESOURCE_ENERGY] >= 50).sort((a, b) => c.pos.getRangeTo(a) - c.pos.getRangeTo(b));
    const cands = [room.storage, rc.at(room, fx, fy, STRUCTURE_CONTAINER)].filter(s => s && s.store[RESOURCE_ENERGY] >= 50).concat(near);
    src = cands[0] || null; c.memory.src = src ? src.id : undefined;
    if (!src) { if (c.store[RESOURCE_ENERGY] > 0) c.memory.working = true; else require('../utils/trace').why(c, 'u'); return; } // starved (was mislabelled target_full)
  }
  if (move.to(c, src.pos.x, src.pos.y, 1)) { c.withdraw(src, RESOURCE_ENERGY); delete c.memory.src; c.memory.working = true; }
} };
