// Multi-queen zoned refill (Misaki 2026-10-18 13:57-58).
// Two queens, each owns one extension zone (stamp A+manager vs stamp B+C). Fixed stops, nearest energy source.
// Fast: withdraw only the zone deficit (full load when deficit is large), serve nearest needy stop, park FULL at the
// best stop when the room still needs energy (next transfer is instant); dump leftover to storage only when the room
// is already full (justify: parking full beats a storage round-trip during a spawn wave; dumping when full frees
// carry and returns energy to the source for the next wave).
// Failover: if only one queen lives she covers ALL zones.
const plan = require('../utils/plan'), move = require('../utils/move'), rc = require('../utils/roomcache');
const N8 = [[-1,-1],[0,-1],[1,-1],[-1,0],[1,0],[-1,1],[0,1],[1,1]];
const FILL = new Set([STRUCTURE_SPAWN, STRUCTURE_EXTENSION, STRUCTURE_TOWER]);
const H = {}; // room -> {t, zones: stop[][]}

function buildZones(room) {
  let h = H[room.name];
  if (h && Game.time - h.t <= 50) return h.zones;
  const P = plan.get(room.name), at = rc.get(room).at;
  const walkable = (x, y) => { const e = at[x * 50 + y]; return !e || Object.keys(e).every(t => t === 'road' || t === 'container' || t === 'rampart'); };
  // fillers[0..3]=stamp A, [4..7]=B, [8..11]=C; manager with A (spawn side)
  const A = P.pos.fillers.slice(0, 4).concat([P.pos.manager]);
  const B = P.pos.fillers.slice(4); // B+C
  const mk = (tiles) => {
    const st = [], covered = new Set();
    for (const [x, y] of tiles) {
      if (!walkable(x, y)) continue;
      const ids = [];
      for (const [dx, dy] of N8) {
        const e = at[(x + dx) * 50 + y + dy];
        if (e) for (const t in e) if (FILL.has(t)) { ids.push(e[t]); covered.add(e[t]); }
      }
      if (ids.length) st.push({ x, y, ids, r: 0, n: ids.length });
    }
    return { st, covered };
  };
  const z0 = mk(A), z1 = mk(B);
  // orphan fill structures (old v1 etc.): assign by nearer zone centroid
  const c0 = z0.st.length ? [z0.st.reduce((s, p) => s + p.x, 0) / z0.st.length, z0.st.reduce((s, p) => s + p.y, 0) / z0.st.length] : [35, 26];
  const c1 = z1.st.length ? [z1.st.reduce((s, p) => s + p.x, 0) / z1.st.length, z1.st.reduce((s, p) => s + p.y, 0) / z1.st.length] : [32, 34];
  for (const t of FILL) for (const s of rc.all(room, t)) {
    if (z0.covered.has(s.id) || z1.covered.has(s.id)) continue;
    const d0 = Math.max(Math.abs(s.pos.x - c0[0]), Math.abs(s.pos.y - c0[1]));
    const d1 = Math.max(Math.abs(s.pos.x - c1[0]), Math.abs(s.pos.y - c1[1]));
    (d0 <= d1 ? z0.st : z1.st).push({ x: s.pos.x, y: s.pos.y, ids: [s.id], r: 1, n: 1 });
  }
  // prefer stops that reach many extensions (sort desc coverage for park pick)
  z0.st.sort((a, b) => b.n - a.n); z1.st.sort((a, b) => b.n - a.n);
  h = H[room.name] = { t: Game.time, zones: [z0.st, z1.st] };
  return h.zones;
}

function needy(id) {
  const s = Game.getObjectById(id);
  return s && s.store.getFreeCapacity(RESOURCE_ENERGY) > (s.structureType === STRUCTURE_TOWER ? 100 : 0) ? s : null;
}
function stopNeedy(s) { return s.ids.map(needy).find(Boolean); }
function zoneDeficit(stops) {
  let d = 0; const seen = new Set();
  for (const s of stops) for (const id of s.ids) {
    if (seen.has(id)) continue; seen.add(id);
    const o = Game.getObjectById(id); if (!o) continue;
    const free = o.store.getFreeCapacity(RESOURCE_ENERGY);
    if (o.structureType === STRUCTURE_TOWER) { if (free > 100) d += free; }
    else d += free;
  }
  return d;
}
function myStops(c, room) {
  const Z = buildZones(room);
  const queens = _.filter(Game.creeps, x => x.memory.role === 'queen' && x.room.name === room.name && !x.spawning);
  // failover: sole queen covers all
  if (queens.length <= 1) return Z[0].concat(Z[1]);
  // assign zone 0/1 stably by name sort
  if (c.memory.zone !== 0 && c.memory.zone !== 1) {
    const sorted = queens.slice().sort((a, b) => a.name < b.name ? -1 : 1);
    sorted.forEach((q, i) => { q.memory.zone = i % 2; });
  }
  const z = c.memory.zone|0;
  return Z[z] && Z[z].length ? Z[z] : Z[0].concat(Z[1]);
}

// refill loop: transfer at current stop; else walk to nearest needy stop
// 17:5x (Misaki: refill speed = reaction speed): pipelined like W47N8 fill.js. (1) after the transfer that empties a stop's
// last needy structure, start walking to the next needy stop in the same tick (was: one dead tick per stop); (2) while walking,
// transfer to any adjacent needy structure of my zone in passing (was: transfers only on the chosen stop tile).
const FM = require('../rooms/w47n8/fillmeter');
function qx(c, t, done) { const a = Math.min(c.store[RESOURCE_ENERGY], t.store.getFreeCapacity(RESOURCE_ENERGY)); if (c.transfer(t, RESOURCE_ENERGY) === OK) { FM.xfer(c, a); done.add(t.id); return a; } return 0; }
function fillRoute(c) {
  const st = myStops(c, c.room), done = new Set();
  const live = id => !done.has(id) && needy(id), liveStop = s => s.ids.find(live);
  let gave = 0;
  // resolve stop by stored coords (stable across zone rebuild / sort)
  let cur = null;
  if (c.memory.sx !== undefined) {
    const i = st.findIndex(s => s.x === c.memory.sx && s.y === c.memory.sy);
    if (i >= 0) { c.memory.stop = i; cur = st[i]; } else { delete c.memory.stop; delete c.memory.sx; delete c.memory.sy; }
  }
  if (cur && c.pos.inRangeTo(cur.x, cur.y, cur.r)) {
    const t = stopNeedy(cur);
    if (t) {
      gave = qx(c, t, done);
      if (liveStop(cur) || c.store[RESOURCE_ENERGY] - gave <= 0) return true; // more here, or load spent: stay
    }
    cur = null;
  }
  // nearest needy stop (Chebyshev)
  let best = -1, bd = 1e9;
  const war = require('../managers/home').active(c.room);
  st.forEach((s, i) => {
    if (!liveStop(s)) return;
    let d = c.pos.getRangeTo(s.x, s.y);
    if (war && s.ids.some(id => { const o = Game.getObjectById(id); return o && o.structureType === STRUCTURE_TOWER && o.store.getFreeCapacity(RESOURCE_ENERGY) > 100; })) d -= 100;
    if (d < bd) { bd = d; best = i; }
  });
  if (best < 0) { delete c.memory.stop; delete c.memory.sx; delete c.memory.sy; return gave > 0; }
  c.memory.stop = best; cur = st[best]; c.memory.sx = cur.x; c.memory.sy = cur.y;
  if (move.to(c, cur.x, cur.y, cur.r)) { const t = cur.ids.map(id => live(id)).find(Boolean); if (t && !gave) qx(c, t, done); }
  else {
    FM.walk(c);
    if (!gave) { // in passing: any adjacent needy fill structure of my zone (spawn first)
      let pass = null;
      for (const s of st) for (const id of s.ids) { const o = live(id); if (o && c.pos.isNearTo(o) && (!pass || o.structureType === STRUCTURE_SPAWN)) pass = o; }
      if (pass) qx(c, pass, done);
    }
  }
  return true;
}

function storageFloor(room) {
  const r = require('../managers/threat').reserve(room.name);
  return (r || room.energyCapacityAvailable) + require('../managers/walls').reserved(room);
}

function standby(c, room, P) {
  const H = require('./hauler'), Lk = require('../managers/links');
  if (require('../managers/walls').noUpgrade(room)) {
    const hb = Lk.roles(room).hub;
    if (hb && room.storage && c.store[RESOURCE_ENERGY] === 0 && hb.store[RESOURCE_ENERGY] > 400 && !H.homeHauler(room)) {
      if (move.to(c, hb.pos.x, hb.pos.y, 1)) c.withdraw(hb, RESOURCE_ENERGY); return true;
    }
    return false;
  }
  const hub = Lk.ctlLinkLow(room) && Lk.roles(room).hub;
  const toHub = hub && hub.store.getFreeCapacity(RESOURCE_ENERGY) > 0;
  if (!toHub && !H.ctlLow(room, P)) return false;
  const [cx, cy] = P.pos.controllerContainer, [fx, fy] = P.pos.fillerContainerA;
  if (c.store[RESOURCE_ENERGY] > 0) {
    if (toHub) { if (move.to(c, hub.pos.x, hub.pos.y, 1)) c.transfer(hub, RESOURCE_ENERGY); return true; }
    const k = rc.at(room, cx, cy, STRUCTURE_CONTAINER); if (H.handoff(c)) return true; if (move.to(c, cx, cy, 1)) c.transfer(k, RESOURCE_ENERGY); return true;
  }
  const cap = c.store.getCapacity(), st = room.storage, a = rc.at(room, fx, fy, STRUCTURE_CONTAINER);
  const floor = storageFloor(room);
  const surplus = st ? st.store[RESOURCE_ENERGY] - floor : 0;
  const src = surplus > 0 ? st : a && a.store[RESOURCE_ENERGY] >= 400 + cap ? a : null;
  if (!src) return false;
  if (move.to(c, src.pos.x, src.pos.y, 1)) c.withdraw(src, RESOURCE_ENERGY, src === st ? Math.min(cap, surplus) : undefined); return true;
}

// nearest energy source; withdraw only zone deficit (full when deficit >= 60% of carry)
function withdrawForZone(c, room, P, deficit) {
  const cap = c.store.getFreeCapacity();
  if (cap <= 0) return false;
  const need = deficit <= 0 ? 0 : (deficit >= cap * 0.6 ? cap : Math.min(cap, deficit));
  if (need <= 0) return false;
  // fixed planned source per zone: nearest store to the ZONE (not the creep) among storage / terminal / filler containers / hub link
  const src = zoneSource(c, room, P, need);
  if (!src) { require('../utils/trace').why(c, 'u'); return true; }
  if (move.to(c, src.pos.x, src.pos.y, 1)) {
    const amt = Math.min(need, src.store[RESOURCE_ENERGY], cap);
    c.withdraw(src, RESOURCE_ENERGY, amt);
    c.memory.working = true;
  }
  return true;
}

const ZC = [[35, 26], [32, 32]]; // zone centres: stamp A / stamp B+C
function zoneSource(c, room, P, need) {
  const z = c.memory.zone === 1 ? 1 : 0, solo = _.filter(Game.creeps, x => x.memory.role === 'queen' && x.room.name === room.name && !x.spawning).length <= 1;
  const [zx, zy] = solo ? [c.pos.x, c.pos.y] : ZC[z];
  const [fx, fy] = P.pos.fillerContainerA;
  const hub = require('../managers/links').roles(room).hub;
  const list = [room.storage, room.terminal, rc.at(room, fx, fy, STRUCTURE_CONTAINER), rc.at(room, 34, 34, STRUCTURE_CONTAINER), hub]
    .filter(s => s && s.store[RESOURCE_ENERGY] >= Math.min(need, 200));
  list.sort((a, b) => Math.max(Math.abs(a.pos.x - zx), Math.abs(a.pos.y - zy)) - Math.max(Math.abs(b.pos.x - zx), Math.abs(b.pos.y - zy)));
  return list[0] || [room.storage].filter(s => s && s.store[RESOURCE_ENERGY] >= 50)[0];
}
function parkOrDump(c, room, P, st) {
  const full = room.energyAvailable >= room.energyCapacityAvailable
    && !rc.all(room, STRUCTURE_TOWER).some(t => t.store[RESOURCE_ENERGY] < 900);
  if (full) {
    if (standby(c, room, P)) return; // ctl/hub ferry uses the carried energy first
    // room full: dump leftover to storage (don't lock energy in the creep between waves)
    if (room.storage && c.store[RESOURCE_ENERGY] > 0) {
      if (move.to(c, room.storage.pos.x, room.storage.pos.y, 1)) c.transfer(room.storage, RESOURCE_ENERGY);
      return;
    }
    const [x, y] = P.pos.fillers[0]; move.to(c, x, y, 0); require('../utils/trace').why(c, 'f'); return;
  }
  // room still hungry: park FULL at the highest-coverage stop in my zone — next refill tick is a transfer, no walk
  if (c.store[RESOURCE_ENERGY] > 0 && st.length) {
    const best = st[0]; // already sorted by coverage desc
    move.to(c, best.x, best.y, best.r); require('../utils/trace').why(c, 'f'); return;
  }
  if (standby(c, room, P)) return;
  const [x, y] = P.pos.fillers[0]; move.to(c, x, y, 0); require('../utils/trace').why(c, 'f');
}

module.exports = { fillRoute, storageFloor, buildZones, zoneDeficit, myStops, run(c) {
  const room = c.room, P = plan.get(room.name);
  room.memory.queenAlive = Game.time;
  if (c.memory.working && c.store[RESOURCE_ENERGY] === 0) c.memory.working = false;
  if (!c.memory.working && c.store.getFreeCapacity() === 0) c.memory.working = true;
  if (!c.memory.working && require('../utils/salvage').retire(c, 25)) return;

  const st = myStops(c, room);
  const deficit = zoneDeficit(st);
  const full = room.energyAvailable >= room.energyCapacityAvailable
    && !rc.all(room, STRUCTURE_TOWER).some(t => t.store[RESOURCE_ENERGY] < 900);

  // carrying energy: fill first (react immediately when spawn drained)
  if (c.store[RESOURCE_ENERGY] > 0) {
    if (deficit > 0 && fillRoute(c)) return;
    parkOrDump(c, room, P, st); return;
  }

  // empty: if zone needs energy, withdraw the right amount from nearest source
  if (!full && deficit > 0) {
    if (withdrawForZone(c, room, P, deficit)) return;
  }

  // nothing to fill
  if (full) {
    if (standby(c, room, P)) return;
    const [x, y] = P.pos.fillers[0]; move.to(c, x, y, 0); require('../utils/trace').why(c, 'f'); return;
  }
  // hungry room but no deficit in my zone (other queen's job) — idle at best stop ready
  if (st.length) { move.to(c, st[0].x, st[0].y, st[0].r); require('../utils/trace').why(c, 'f'); return; }
  require('../utils/trace').why(c, 'u');
} };
