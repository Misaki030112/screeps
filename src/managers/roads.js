// RCL6 road plan (docs/ROADS.md, Misaki 2026-10-17 17:40 UTC+8): after RCL6 the order is
//   core   RCL6 core build (10 ext + link 30,11, placed by layout.js) must be finished first
//   home   trunk roads to the wall gates (defense.trunks with_gate: TR, W, S) + home leg of the remote haul routes
//   W45N8  remote haul road in W45N8 (route storage -> container 13,11)
//   (W45N7 road dropped by Misaki 2026-10-17 17:47: W45N7 haulers stay 8C8M)
//   done   -> walls.phase() may start banking / building barriers
// Only active at controller.level >= 6. Sites in batches (BATCH per room, every 50 ticks). Memory.roads.off = true pauses
// placement (walls stay gated). Memory.roads.skip = true un-gates walls immediately (manual override).
const ROUTES = require('../layouts/remote_routes');
const PHASES = ['core', 'home', 'W45N8', 'done']; // W45N7 road dropped (Misaki 2026-10-17 17:47)
const BATCH = 5, HOME = 'W46N8';
const memo = {};
// Tiles per phase: { phase: [[room, x, y], ...] } (deduplicated, earlier phase wins)
function tiles(P) {
  if (memo.t) return memo.t;
  const seen = new Set(), out = { home: [], W45N8: [] };
  const busy = (r, x, y) => { if (r !== HOME || !P || !P.any) return false; const w = P.any[x * 50 + y]; return !!(w && w.type !== 'road' && (w.rcl || 0) <= 6); };
  const add = (ph, r, x, y) => { if (busy(r, x, y)) return; const k = r + ':' + x + ':' + y; if (seen.has(k)) return; seen.add(k); out[ph].push([r, x, y]); };
  const d = P && P.raw && P.raw.defense;
  if (d) for (const g in d.trunks) if (d.trunks[g].mode === 'with_gate') for (const [x, y] of d.trunks[g].new_tiles) add('home', HOME, x, y);
  for (const [rm, x, y] of ROUTES.W45N8) if (rm === HOME) add('home', rm, x, y); // W45N7-only home leg (46-49,18-21) dropped
  for (const [rm, x, y] of ROUTES.W45N8) if (rm !== HOME) add('W45N8', rm, x, y);
  return (memo.t = out);
}
function isHomeTile(x, y) { const P = require('../utils/plan').get(HOME); return tiles(P).home.some(([, a, b]) => a === x && b === y); }
function isRouteTile(r, x, y) { const T = memo.t || tiles(require('../utils/plan').get(HOME)); return [].concat(T.home, T.W45N8).some(([rm, a, b]) => rm === r && a === x && b === y); }
function mem() { return (Memory.roads = Memory.roads || { phase: 'core' }); }
function M() { return typeof Memory === 'undefined' ? undefined : Memory.roads; }
function phase() { const m = M(); return m ? m.phase || 'core' : 'core'; }
// Walls wait for this. Pre-RCL6 it is irrelevant (walls.phase is 'off' anyway).
function done() { const m = M(); return !!(m && (m.skip || m.phase === 'done')); }
function paved(r) { const m = M(); if (!m || PHASES.indexOf(r) < 1) return false; const i = PHASES.indexOf(m.phase); return m.phase === 'done' || (i > PHASES.indexOf(r) && PHASES.indexOf(r) > 0); }
// Pure: status of a tile list. look(r,x,y) -> 'road' | 'site' | 'blocked' | 'open' | null (no vision)
function status(list, look) {
  const s = { total: list.length, road: 0, site: 0, blocked: 0, open: [], unseen: 0 };
  for (const t of list) { const v = look(t[0], t[1], t[2]); if (v === null) s.unseen++; else if (v === 'open') s.open.push(t); else s[v]++; }
  s.complete = s.unseen === 0 && s.open.length === 0 && s.site === 0;
  return s;
}
function look(r, x, y) {
  const room = Game.rooms[r]; if (!room) return null;
  if (room.getTerrain().get(x, y) & TERRAIN_MASK_WALL) return 'blocked';
  const st = room.lookForAt(LOOK_STRUCTURES, x, y);
  if (st.some(s => s.structureType === STRUCTURE_ROAD)) return 'road';
  if (room.lookForAt(LOOK_CONSTRUCTION_SITES, x, y).some(s => s.structureType === STRUCTURE_ROAD)) return 'site';
  if (st.some(s => s.structureType !== STRUCTURE_CONTAINER && s.structureType !== STRUCTURE_RAMPART)) return 'blocked';
  if (room.lookForAt(LOOK_CONSTRUCTION_SITES, x, y).length) return 'blocked';
  return 'open';
}
// Pure: core build finished? (no non-road sites at home, extension count at the RCL limit, source-A link built)
function coreDone(nExt, extMax, nLink, linkMax, coreSites) { return coreSites === 0 && nExt >= extMax && nLink >= Math.min(linkMax, 3); }
function run() {
  const home = Game.rooms[HOME]; if (!home || !home.controller || !home.controller.my || home.controller.level < 6) return;
  const m = mem(); if (m.off || m.phase === 'done') return;
  if (Game.time % 50 && m.t) return; // m.t: last run tick (first run immediately)
  m.t = Game.time;
  const P = require('../utils/plan').get(HOME), T = tiles(P);
  if (m.phase === 'core') {
    const rcl = home.controller.level, st = home.find(FIND_MY_STRUCTURES);
    const coreSites = home.find(FIND_MY_CONSTRUCTION_SITES).filter(s => s.structureType !== STRUCTURE_ROAD && s.structureType !== STRUCTURE_RAMPART && s.structureType !== STRUCTURE_WALL).length;
    if (!coreDone(st.filter(s => s.structureType === STRUCTURE_EXTENSION).length, CONTROLLER_STRUCTURES.extension[rcl], st.filter(s => s.structureType === STRUCTURE_LINK).length, CONTROLLER_STRUCTURES.link[rcl], coreSites)) return;
    advance(m, 'core');
  }
  const ph = m.phase; if (ph === 'done') return;
  const R = require('./remote');
  if (ph !== 'home' && R.paused(ph)) { m.note = 'paused ' + ph; return; }
  const s = status(T[ph], look);
  m.prog = { road: s.road, site: s.site, open: s.open.length, unseen: s.unseen, blocked: s.blocked, total: s.total };
  if (s.complete) return advance(m, ph);
  // batch: at most BATCH open road sites of this phase per room
  const perRoom = {};
  for (const t of T[ph]) if (look(t[0], t[1], t[2]) === 'site') perRoom[t[0]] = (perRoom[t[0]] || 0) + 1;
  for (const [r, x, y] of s.open) {
    if ((perRoom[r] || 0) >= BATCH) continue;
    const rv = Game.rooms[r].createConstructionSite(x, y, STRUCTURE_ROAD);
    if (rv === OK) perRoom[r] = (perRoom[r] || 0) + 1; else (m.bad = m.bad || {})[r + ':' + x + ':' + y] = rv;
  }
}
function advance(m, from) {
  const next = PHASES[PHASES.indexOf(from) + 1];
  (m.log = m.log || []).push([from, Game.time]); m.phase = next; delete m.prog;
  console.log(`ROADS phase ${from} done -> ${next} t=${Game.time}`);
}
// Repair: our route roads below 50% (remote rooms are not covered by layout repairables) — builder target
function repairTarget(minFrac) {
  minFrac = minFrac || 0.5; const R = require('./remote'); let best = null;
  const H = typeof Game !== 'undefined' && Game.rooms && Game.rooms[HOME]; if (!H || !H.controller || H.controller.level < 6) return null; // gated: RCL6+
  for (const r of ['W45N8']) {
    const room = typeof Game !== 'undefined' && Game.rooms && Game.rooms[r]; if (!room || R.paused(r)) continue;
    for (const s of room.find(FIND_STRUCTURES)) {
      if (s.structureType !== STRUCTURE_ROAD || !isRouteTile(r, s.pos.x, s.pos.y)) continue;
      const f = s.hits / s.hitsMax; if (f < minFrac && (!best || f < best.f)) best = { s, f };
    }
  }
  return best ? best.s : null;
}
module.exports = { PHASES, BATCH, tiles, status, coreDone, phase, done, paved, run, repairTarget, isHomeTile, isRouteTile, _memo: memo };
