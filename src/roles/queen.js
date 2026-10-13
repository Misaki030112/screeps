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
    st.forEach((s, i) => { if (s.ids.some(needy)) { const d = c.pos.getRangeTo(s.x, s.y); if (d < bd) { bd = d; best = i; } } });
    if (best < 0) { delete c.memory.stop; return false; }
    c.memory.stop = best; cur = st[best];
  }
  if (move.to(c, cur.x, cur.y, cur.r)) { const t = cur.ids.map(needy).find(Boolean); if (t) c.transfer(t, RESOURCE_ENERGY); }
  return true;
}
// Room full (52% of queen time historically): ferry surplus -> controller container while it is low.
// Source: storage above one full spawn refill (>= defender reserve), else filler container A above 400 for the next refill.
// Without the storage leg source B + remote energy never reached the controller (10-14 06:58: upgrade 9.7/t, storage
// spent on spawns, upgraders waiting_feed ~50%); with no floor it drained storage to ~100 (05:50), hence the floor.
function storageFloor(room) { return Math.max(require('../managers/threat').reserve(room.name), room.energyCapacityAvailable); }
function standby(c, room, P) {
  const H = require('./hauler'); if (!H.ctlLow(room, P)) return false;
  const [cx, cy] = P.pos.controllerContainer, [fx, fy] = P.pos.fillerContainerA;
  if (c.store[RESOURCE_ENERGY] > 0) { const k = rc.at(room, cx, cy, STRUCTURE_CONTAINER); if (H.handoff(c)) return true; if (move.to(c, cx, cy, 1)) c.transfer(k, RESOURCE_ENERGY); return true; }
  const cap = c.store.getCapacity(), st = room.storage, a = rc.at(room, fx, fy, STRUCTURE_CONTAINER);
  const src = st && st.store[RESOURCE_ENERGY] >= storageFloor(room) + cap ? st : a && a.store[RESOURCE_ENERGY] >= 400 + cap ? a : null;
  if (!src) return false;
  if (move.to(c, src.pos.x, src.pos.y, 1)) c.withdraw(src, RESOURCE_ENERGY); return true;
}
module.exports = { fillRoute, run(c) {
  const room = c.room, P = plan.get(room.name);
  room.memory.queenAlive = Game.time;
  if (c.memory.working && c.store[RESOURCE_ENERGY] === 0) c.memory.working = false;
  if (!c.memory.working && c.store.getFreeCapacity() === 0) c.memory.working = true;
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
