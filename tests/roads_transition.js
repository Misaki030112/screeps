// RCL5->6 transition sim for managers/roads.js run(): gate, init, core->home->W45N8->done, batch cap, no vision, paused, bad phase.
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, { Memory: {}, TERRAIN_MASK_WALL: 1, LOOK_STRUCTURES: 's', LOOK_CONSTRUCTION_SITES: 'c', STRUCTURE_ROAD: 'road',
  STRUCTURE_CONTAINER: 'container', STRUCTURE_RAMPART: 'rampart', STRUCTURE_WALL: 'constructedWall', STRUCTURE_EXTENSION: 'extension', STRUCTURE_LINK: 'link',
  FIND_MY_STRUCTURES: 'ms', FIND_MY_CONSTRUCTION_SITES: 'mc', FIND_STRUCTURES: 'st', OK: 0,
  CONTROLLER_STRUCTURES: { extension: { 5: 30, 6: 40 }, link: { 5: 2, 6: 3 } } });
let paused = false;
require.cache[require.resolve(src('managers/remote.js'))] = { id: 'r', filename: 'r', loaded: true, exports: { paused: () => paused } };
const R = require(src('managers/roads.js'));
console.log = () => {};
function mkRoom(name, o) {
  const roads = new Set(), sites = new Map();
  return { name, roads, sites, controller: o.ctl, getTerrain: () => ({ get: () => 0 }),
    lookForAt: (k, x, y) => k === 's' ? (roads.has(x + ',' + y) ? [{ structureType: 'road' }] : []) : (sites.has(x + ',' + y) ? [{ structureType: 'road' }] : []),
    find: k => k === 'ms' ? [].concat(Array(o.ext()).fill({ structureType: 'extension' }), Array(o.link()).fill({ structureType: 'link' })) : k === 'mc' ? o.core() : [],
    createConstructionSite(x, y) { sites.set(x + ',' + y, 1); return 0; } };
}
let ext = 30, link = 2, core = [];
const ctl = { my: true, level: 5 };
const home = mkRoom('W46N8', { ctl, ext: () => ext, link: () => link, core: () => core });
const W8 = mkRoom('W45N8', { ext: () => 0, link: () => 0, core: () => [] });
global.Game = { time: 1000, rooms: { W46N8: home, W45N8: W8 } };
const tick = n => { for (let i = 0; i < n; i++) { Game.time++; R.run(); } };
const finishSites = r => { for (const k of r.sites.keys()) r.roads.add(k); r.sites.clear(); };
const cases = [
  ['RCL5: no-op, Memory.roads untouched', () => { tick(100); assert.strictEqual(Memory.roads, undefined); }],
  ['RCL6: init core, waits for core build', () => { ctl.level = 6; core = [{ structureType: 'extension' }]; tick(1);
    assert.strictEqual(Memory.roads.phase, 'core'); tick(200); assert.strictEqual(Memory.roads.phase, 'core'); assert.strictEqual(home.sites.size, 0); }],
  ['core done -> haul, <=BATCH sites', () => { ext = 40; link = 3; core = []; tick(50); assert.strictEqual(Memory.roads.phase, 'haul'); assert.ok(home.sites.size <= R.BATCH && home.sites.size > 0); tick(50); assert.ok(home.sites.size <= R.BATCH); }],
  ['haul completes -> W45N8 (no early skip, no trunk sites yet)', () => { let g = 0; while (Memory.roads.phase === 'haul' && g++ < 100) { finishSites(home); tick(50); }
    assert.strictEqual(Memory.roads.phase, 'W45N8'); assert.ok(W8.sites.size <= R.BATCH); assert.ok(home.roads.size >= R.tiles().haul.length && home.roads.size <= R.tiles().haul.length + R.tiles().econ.length); }],
  ['v2.1 parallel: econ + W45N8 sites placed while haul open, never trunks', () => { const T = R.tiles(), trunk = new Set(T.home.map(t => t[1] + ',' + t[2]));
    assert.ok(W8.sites.size > 0); for (const k of home.sites.keys()) assert.ok(!trunk.has(k) || T.econ.concat(T.haul).some(t => t[1] + ',' + t[2] === k)); }],
  ['no vision: no progress, no crash', () => { delete Game.rooms.W45N8; tick(200); assert.strictEqual(Memory.roads.phase, 'W45N8'); assert.ok(Memory.roads.prog.unseen > 0); Game.rooms.W45N8 = W8; }],
  ['paused remote: no sites', () => { W8.sites.clear(); paused = true; tick(100); assert.strictEqual(W8.sites.size, 0); paused = false; }],
  ['W45N8 batch then econ -> home(trunks) -> done; walls gated until done', () => { tick(50); assert.ok(W8.sites.size > 0 && W8.sites.size <= R.BATCH); let g = 0;
    while (Memory.roads.phase === 'W45N8' && g++ < 100) { finishSites(W8); tick(50); } assert.strictEqual(W8.roads.size, 12); assert.ok(R.paved('W45N8'));
    assert.strictEqual(Memory.roads.phase, 'econ'); assert.ok(!R.done());
    while (Memory.roads.phase === 'econ' && g++ < 200) { finishSites(home); tick(50); } assert.strictEqual(Memory.roads.phase, 'home'); assert.ok(!R.done());
    while (Memory.roads.phase === 'home' && g++ < 300) { finishSites(home); tick(50); } assert.strictEqual(Memory.roads.phase, 'done'); assert.ok(R.done()); }],
  ['v1 migrate: phase home -> haul once', () => { Memory.roads = { phase: 'home', t: 1 }; tick(50); assert.ok(Memory.roads.v2 && Memory.roads.log.some(l => l[0] === 'v2') && Memory.roads.phase !== 'home'); }],
  ['off pauses; bad phase resets to core; RCL drop no-op', () => { Memory.roads = { phase: 'home', off: true, t: 1, v2: true }; const n = home.sites.size; tick(100); assert.strictEqual(home.sites.size, n);
    Memory.roads = { phase: 'W45N7', t: 1, v2: true }; tick(50); assert.notStrictEqual(Memory.roads.phase, 'W45N7');
    ctl.level = 5; Memory.roads = { phase: 'home', t: 1 }; tick(100); assert.strictEqual(Memory.roads.phase, 'home'); }],
];
let fail = 0;
for (const [n, f] of cases) { try { f(); process.stdout.write('ok   ' + n + '\n'); } catch (e) { fail++; process.stdout.write('FAIL ' + n + ' ' + e.message + '\n'); } }
process.exit(fail ? 1 : 0);
