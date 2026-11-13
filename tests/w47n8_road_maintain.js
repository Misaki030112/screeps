// 11-13 (Misaki t84238893): decayed W47N8 planned roads were not re-sited while labs + the hub
// container held the non-rampart site budget. layoutRun must place a road site anyway, and must
// not call createConstructionSite on an exit tile (18,49 → ERR_INVALID_TARGET).
const assert = require('assert'), path = require('path');
const d = path.join(__dirname, '..', 'src', 'rooms', 'w47n8');
const K = { LOOK_STRUCTURES: 'structure', LOOK_CONSTRUCTION_SITES: 'constructionSite', FIND_MY_SPAWNS: 112, FIND_MY_CONSTRUCTION_SITES: 114,
  FIND_MY_STRUCTURES: 108, OK: 0, ERR_RCL_NOT_ENOUGH: -14, ERR_INVALID_TARGET: -7 };
const T = ['spawn', 'extension', 'road', 'wall', 'rampart', 'link', 'storage', 'tower', 'observer', 'powerSpawn', 'extractor', 'lab', 'terminal', 'container', 'nuker', 'factory'];
for (const t of T) K['STRUCTURE_' + (t === 'powerSpawn' ? 'POWER_SPAWN' : t.toUpperCase())] = t;
const CS = { spawn: [0, 1, 1, 1, 1, 1, 1, 2, 3], extension: [0, 0, 5, 10, 20, 30, 40, 50, 60], tower: [0, 0, 0, 1, 1, 2, 2, 3, 6], link: [0, 0, 0, 0, 0, 2, 3, 4, 6],
  storage: [0, 0, 0, 0, 1, 1, 1, 1, 1], container: Array(9).fill(5), road: Array(9).fill(2500), wall: [0, 0, 2500, 2500, 2500, 2500, 2500, 2500, 2500],
  rampart: [0, 0, 2500, 2500, 2500, 2500, 2500, 2500, 2500], terminal: [0, 0, 0, 0, 0, 0, 1, 1, 1], extractor: [0, 0, 0, 0, 0, 0, 1, 1, 1],
  lab: [0, 0, 0, 0, 0, 0, 3, 6, 10], factory: [0, 0, 0, 0, 0, 0, 0, 1, 1], powerSpawn: Array(8).fill(0).concat([1]), nuker: Array(8).fill(0).concat([1]), observer: Array(8).fill(0).concat([1]) };
Object.assign(global, K, { _: require('lodash'), CONTROLLER_STRUCTURES: CS, Memory: { ops: { w8layout: 'approved' } }, Game: { time: 100, rooms: {}, creeps: {} } });
const L = require(path.join(d, 'layout')), C = require(path.join(d, 'config')), W = require(path.join(d, 'index.js')), R = require(path.join(d, 'roads'));
const link = require(path.join(__dirname, '..', 'src', 'layouts', 'w8link')).W47N8;
const baseRoads = R.ROADS.filter(([x, y]) => !R.MINERAL.some(([a, b]) => a === x && b === y));
const planned = baseRoads.concat(R.MINERAL).concat(link);
const key = (x, y) => x + ',' + y;
const exits = planned.filter(([x, y]) => x === 0 || y === 0 || x === 49 || y === 49);
assert.deepStrictEqual(exits, [[18, 49]], 'kept network exit tile is 18,49');
const OPEN = [8, 18], SHARE = C.HUB_CONT, GATE = [29, 3], CONT_SITE = [8, 19];
for (const [x, y] of [OPEN, SHARE, GATE, CONT_SITE]) assert.ok(planned.some(([a, b]) => a === x && b === y), 'planned tile ' + key(x, y));
assert.ok(!L.ORDER.lab.slice(0, 6).some(([x, y]) => key(x, y) === key(OPEN[0], OPEN[1])), 'open road tile is not a lab');

function mkRoom(opts) {
  opts = opts || {};
  const st = {}, sites = [], calls = [];
  const add = (x, y, t) => { (st[x * 50 + y] = st[x * 50 + y] || []).push({ structureType: t, pos: { x, y } }); };
  for (const [x, y] of C.SEAL) if (!(x === GATE[0] && y === GATE[1])) add(x, y, 'wall');
  add(34, 30, 'spawn'); add(33, 30, 'spawn');
  add(24, 8, 'tower'); add(33, 35, 'tower');
  if (!opts.missTower) add(22, 7, 'tower');
  add(35, 32, 'storage');
  add(SHARE[0], SHARE[1], 'container');
  const skip = new Set([key(OPEN[0], OPEN[1]), key(SHARE[0], SHARE[1]), key(GATE[0], GATE[1]), key(18, 49), key(CONT_SITE[0], CONT_SITE[1])]);
  for (const [x, y] of planned) if (!skip.has(key(x, y))) add(x, y, 'road');
  const ramp = { structureType: 'rampart', pos: { x: GATE[0], y: GATE[1] }, remove() { this.gone = true; } };
  const contSite = { structureType: 'container', pos: { x: CONT_SITE[0], y: CONT_SITE[1] }, remove() { this.gone = true; } };
  sites.push(ramp, contSite);
  for (const [x, y] of L.ORDER.lab.slice(0, 6)) sites.push({ structureType: 'lab', pos: { x, y }, remove() { this.gone = true; } });
  return { sites, calls, ramp, contSite, controller: { level: 7, progress: 0, progressTotal: 1000 },
    find: (k, o) => { const a = k === FIND_MY_SPAWNS ? [{}] : k === FIND_MY_CONSTRUCTION_SITES ? sites : []; return o && o.filter ? a.filter(o.filter) : a; },
    lookForAt: (k, x, y) => k === LOOK_STRUCTURES ? (st[x * 50 + y] || []) : sites.filter(s => s.pos.x === x && s.pos.y === y),
    createConstructionSite(x, y, t) {
      calls.push(t + ' ' + x + ',' + y);
      const n = Object.values(st).flat().filter(s => s.structureType === t).length + sites.filter(s => s.structureType === t).length;
      if (n >= CS[t][7]) return ERR_RCL_NOT_ENOUGH;
      const site = { structureType: t, pos: { x, y }, remove() { const i = sites.indexOf(site); if (i >= 0) sites.splice(i, 1); } };
      sites.push(site); return OK; } };
}
function roadsAt(room) { return room.sites.filter(s => s.structureType === 'road').map(s => key(s.pos.x, s.pos.y)); }

// Off cadence (layout tick, not the 100t maintain tick): a full lab queue still blocks nothing new,
// and the decayed tile stays unpaved until the maintain tick.
Game.time = 20;
{ const room = mkRoom(); W.layoutRun(room);
  assert.deepStrictEqual(roadsAt(room), [], 'off-cadence: no road site while labs are queued');
  assert.ok(!room.calls.some(c => c === 'road 18,49'), 'off-cadence: exit not requested');
  assert.strictEqual(room.sites.filter(s => s.structureType === 'lab').length, 6, 'labs kept'); }

// Cadence tick, 6 lab sites already queued, planned road tile empty → road site. Exit skipped.
// Hub container structure shares 33,33; gate rampart site and a container site are not removed to pave.
Game.time = 100;
{ const room = mkRoom(); W.layoutRun(room);
  const got = roadsAt(room).sort();
  assert.ok(got.includes('8,18'), 'empty planned tile 8,18 re-sited while labs are queued: ' + got);
  assert.ok(got.includes(key(SHARE[0], SHARE[1])), 'road site shares the hub container tile: ' + got);
  assert.ok(room.lookForAt(LOOK_STRUCTURES, SHARE[0], SHARE[1]).some(s => s.structureType === 'container'), 'hub container structure kept');
  assert.ok(!got.includes('18,49'), 'exit 18,49 not sited: ' + got);
  assert.ok(!room.calls.some(c => c === 'road 18,49'), 'exit 18,49 never passed to createConstructionSite: ' + room.calls.filter(c => c.startsWith('road')));
  assert.ok(!got.includes('29,3'), 'no road stacked on the gate rampart site');
  assert.ok(!room.ramp.gone, 'gate rampart site not removed to place a road');
  assert.ok(!got.includes('8,19'), 'no road stacked on the container site');
  assert.ok(!room.contSite.gone, 'container site not removed to place a road');
  assert.strictEqual(room.sites.filter(s => s.structureType === 'lab').length, 6, 'queued labs not cancelled'); }

// Day-critical tower still missing: do not spend the tick on roads. Tower site is placed; labs stay.
Game.time = 100;
{ const room = mkRoom({ missTower: true }); W.layoutRun(room);
  assert.ok(room.sites.some(s => s.structureType === 'tower' && s.pos.x === 22 && s.pos.y === 7), 'day-crit tower 22,7 re-queued');
  assert.ok(!roadsAt(room).includes('8,18'), 'day-crit: missing road waits, got ' + roadsAt(room));
  assert.strictEqual(room.sites.filter(s => s.structureType === 'lab').length, 6, 'day-crit does not cancel labs'); }

assert.strictEqual(C.RCL6_LABS, false, 'RCL6_LABS untouched');
assert.strictEqual(C.RCL7_INDUSTRY, false, 'RCL7_INDUSTRY untouched');
assert.strictEqual(C.RCL6_MINERALS, true, 'RCL6_MINERALS untouched');
console.log('w47n8 road maintain ok');
