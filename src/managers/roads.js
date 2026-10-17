// RCL6 road plan (docs/ROADS.md, Misaki 2026-10-17 17:40 UTC+8): after RCL6 the order is
//   core   RCL6 core build (10 ext + link 30,11, placed by layout.js) must be finished first
//   home   trunk roads to the wall gates (defense.trunks with_gate: TR, W, S) + home leg of the remote haul routes
//   W45N8  remote haul road in W45N8 (route storage -> container 13,11)
//   (W45N7 road dropped by Misaki 2026-10-17 17:47: W45N7 haulers stay 8C8M)
//   done   -> walls.phase() may start banking / building barriers
// Only active at controller.level >= 6. Sites in batches (BATCH per room, every 50 ticks). Memory.roads.off = true pauses
// placement (walls stay gated). Memory.roads.skip = true un-gates walls immediately (manual override).
const ROUTES = require('../layouts/remote_routes');
// v2 (Misaki 2026-10-17 22:20 "先修运输路"): order by hauler traffic (creep_ticks entries/day): haul = storage->W45N8 exit
// leg + TR tiles shared with it; W45N8 = remote leg (rerouted onto the plain y9-11 band haulers actually walk, no new swamp);
// home = wall-gate trunks (W, S, TR swamp spur) LAST, then walls.
const PHASES = ['core', 'haul', 'W45N8', 'econ', 'home', 'done']; // W45N7 road dropped (Misaki 2026-10-17 17:47)
const BATCH = 15, HOME = 'W46N8'; // 5 left builders no_task 19% (batch done, waiting for the 50t replan)
// W45N8 remote leg override: plan 4,10 5,9 (swamp) 6,8 7,7 8,7 9,8 10,8 had 0 traffic; haulers walk 4,11 5,11 6,10 7,9 8,9 9,9 10,9 (all plain)
// econ: unroaded home tiles >=300 hauler/queen entries/day (creep_ticks 24h, 22:18): 35,26 861, 36,25 603, 34,25 409, 35,31 393
// (48,21 715 is the W45N7 leg, dropped by Misaki). Re-check with the heatmap before adding more.
const ECON = [[35, 26], [36, 25], [34, 25], [35, 31]];
const W45N8_LEG = [[0, 14], [1, 13], [2, 12], [3, 11], [4, 11], [5, 11], [6, 10], [7, 9], [8, 9], [9, 9], [10, 9], [11, 9], [12, 10]];
const memo = {};
// Tiles per phase: { phase: [[room, x, y], ...] } (deduplicated, earlier phase wins)
function tiles(P) {
  if (memo.t) return memo.t;
  const seen = new Set(), out = { haul: [], W45N8: [], econ: [], home: [] };
  const busy = (r, x, y) => { if (r !== HOME || !P || !P.any) return false; const w = P.any[x * 50 + y]; return !!(w && w.type !== 'road' && (w.rcl || 0) <= 6); };
  const add = (ph, r, x, y) => { if (busy(r, x, y) || x <= 0 || y <= 0 || x >= 49 || y >= 49) return; // exit tiles: createConstructionSite -> ERR_INVALID_TARGET (-7, live 83705660)
    const k = r + ':' + x + ':' + y; if (seen.has(k)) return; seen.add(k); out[ph].push([r, x, y]); };
  for (const [rm, x, y] of ROUTES.W45N8) if (rm === HOME) add('haul', rm, x, y); // storage 38,30 -> exit 49,14 (W45N7-only leg dropped)
  for (const [x, y] of W45N8_LEG) add('W45N8', 'W45N8', x, y);
  for (const [x, y] of ECON) add('econ', HOME, x, y);
  const d = P && P.raw && P.raw.defense, order = ['TR', 'S', 'W']; // trunks last; within them short/cheap first
  if (d) for (const g of order.concat(Object.keys(d.trunks).filter(k => order.indexOf(k) < 0)))
    if (d.trunks[g] && d.trunks[g].mode === 'with_gate') for (const [x, y] of d.trunks[g].new_tiles) add('home', HOME, x, y);
  return (memo.t = out);
}
function isHomeTile(x, y) { const P = require('../utils/plan').get(HOME); const T = tiles(P); return [].concat(T.haul, T.econ, T.home).some(([, a, b]) => a === x && b === y); }
function isRouteTile(r, x, y) { const T = memo.t || tiles(require('../utils/plan').get(HOME)); return [].concat(T.haul, T.econ, T.home, T.W45N8).some(([rm, a, b]) => rm === r && a === x && b === y); }
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
  const m = mem(); if (PHASES.indexOf(m.phase) < 0) { console.log(`ROADS bad phase ${m.phase} -> core`); m.phase = 'core'; } // console typo guard
  if (!m.v2) migrate(m, home); // one-shot: v1 'home' (trunks first) -> v2 'haul'; drop untouched (0-progress) trunk sites
  if (m.off || m.phase === 'done') return;
  if (Game.time % (m.idle ? 10 : 50) && m.t) return; // replan every 10t while a phase has no open sites left to place // m.t: last run tick (first run immediately)
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
  if (ph === 'W45N8' && R.paused(ph)) { m.note = 'paused ' + ph; return; }
  const s = status(T[ph], look);
  m.prog = { road: s.road, site: s.site, open: s.open.length, unseen: s.unseen, blocked: s.blocked, total: s.total };
  if (s.complete) return advance(m, ph);
  // v2.1 (Misaki 22:45 "存了1w多能量…建造速度好慢"): the economic phases (haul, W45N8, econ) get sites IN PARALLEL so builders
  // never starve on a 2-4 tile tail (live 22:45: haul 12/16 -> 2 sites, 2 builders, storage 12.3k). Phase still advances in order
  // (walls gate unchanged); trunks ('home') are only placed once the phase reaches 'home' (Misaki: 主干道保留在最后).
  const par = PHASES.indexOf(ph) <= PHASES.indexOf('econ') ? PHASES.slice(PHASES.indexOf(ph), PHASES.indexOf('econ') + 1) : [ph];
  const R2 = require('./remote'), perRoom = {}, open = [];
  for (const p of par) for (const t of T[p]) { const v = look(t[0], t[1], t[2]); if (v === 'site') perRoom[t[0]] = (perRoom[t[0]] || 0) + 1; else if (v === 'open' && !(t[0] !== HOME && R2.paused(t[0]))) open.push(t); }
  m.idle = !Object.keys(perRoom).length;
  m.par = par.join('+');
  for (const [r, x, y] of open) {
    if ((perRoom[r] || 0) >= BATCH) continue;
    const rv = Game.rooms[r].createConstructionSite(x, y, STRUCTURE_ROAD);
    if (rv === OK) perRoom[r] = (perRoom[r] || 0) + 1; else (m.bad = m.bad || {})[r + ':' + x + ':' + y] = rv;
  }
}
function migrate(m, home) {
  m.v2 = true; if (m.phase !== 'home') return;
  m.phase = 'haul'; delete m.prog; (m.log = m.log || []).push(['v2', Game.time]);
  const P = require('../utils/plan').get(HOME), T = tiles(P), keep = new Set(T.haul.map(([, x, y]) => x + ':' + y));
  for (const c of home.find(FIND_MY_CONSTRUCTION_SITES)) if (c.structureType === STRUCTURE_ROAD && !c.progress && !keep.has(c.pos.x + ':' + c.pos.y) && T.home.some(([, x, y]) => x === c.pos.x && y === c.pos.y)) c.remove();
  console.log(`ROADS v2 migrate home -> haul t=${Game.time}`);
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
