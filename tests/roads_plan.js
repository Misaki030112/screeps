// RCL6 road plan (docs/ROADS.md): phase tiles, pure status/coreDone, walls gated until roads done. node tests/roads_plan.js
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
global.Memory = {};
const plan = require(src('utils/plan.js')), R = require(src('managers/roads.js'));
const T = R.tiles(plan.get('W46N8'));
const cases = [
  ['phase order', () => assert.deepStrictEqual(R.PHASES, ['core', 'haul', 'W45N8', 'econ', 'home', 'done'])],
  ['tile counts', () => { assert.strictEqual(T.haul.length, 17); assert.strictEqual(T.econ.length, 4); assert.strictEqual(T.home.length, 37); assert.ok(T.home.every(([, x, y]) => !T.haul.some(([, a, b]) => a === x && b === y))); assert.strictEqual(T.W45N8.length, 13); assert.ok(!T.W45N7); assert.ok(!T.home.some(([, x, y]) => x >= 46 && y >= 18 && y <= 21)); }],
  ['no home tile on a planned RCL<=6 structure', () => { const P = plan.get('W46N8');
    for (const [, x, y] of [].concat(T.haul, T.econ, T.home)) { const w = P.any[x * 50 + y]; assert.ok(!w || w.type === 'road' || w.rcl > 6, `${x},${y}`); } }],
  ['status: complete only when every tile is road/blocked and seen', () => {
    const L = [['A', 1, 1], ['A', 1, 2], ['B', 1, 1]];
    assert.strictEqual(R.status(L, () => 'road').complete, true);
    assert.strictEqual(R.status(L, (r) => r === 'B' ? null : 'road').complete, false);
    const s = R.status(L, (r, x, y) => y === 2 ? 'open' : 'site'); assert.strictEqual(s.open.length, 1); assert.strictEqual(s.complete, false); }],
  ['coreDone', () => { assert.ok(!R.coreDone(30, 40, 3, 3, 0)); assert.ok(!R.coreDone(40, 40, 2, 3, 0)); assert.ok(!R.coreDone(40, 40, 3, 3, 1)); assert.ok(R.coreDone(40, 40, 3, 3, 0)); }],
  ['done/paved', () => {
    Memory.roads = undefined; assert.strictEqual(R.done(), false); assert.strictEqual(R.paved('W45N8'), false);
    Memory.roads = { phase: 'W45N8' }; assert.strictEqual(R.paved('W45N8'), false);
    Memory.roads = { phase: 'done' }; assert.ok(R.done() && R.paved('W45N8') && !R.paved('W45N7'));
    Memory.roads = { phase: 'home', skip: true }; assert.ok(R.done()); }],
  ['walls.phase returns "roads" at RCL6 until the road plan is done', () => {
    Object.assign(global, { RESOURCE_ENERGY: 'energy', FIND_HOSTILE_CREEPS: 1, FIND_MY_CONSTRUCTION_SITES: 2, Game: { time: 10 } });
    const stub = (p, e) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: e }; };
    stub('managers/home.js', { on: () => false, alert: () => false, active: () => false });
    stub('managers/threat.js', { holding: () => false });
    const W = require(src('managers/walls.js'));
    const room = { memory: {}, controller: { level: 6 }, storage: { store: { energy: 30000 } }, find: () => [] };
    Memory.roads = { phase: 'W45N8' }; assert.strictEqual(W.phase(room), 'roads'); assert.ok(!room.memory.walls);
    Memory.roads = { phase: 'done' }; assert.strictEqual(W.phase(room), 'build');
    const r5 = { memory: {}, controller: { level: 5 }, storage: room.storage, find: () => [] }; Memory.roads = undefined; assert.strictEqual(W.phase(r5), 'off'); }],
];
let fail = 0;
for (const [n, f] of cases) { try { f(); console.log('ok  ', n); } catch (e) { fail++; console.log('FAIL', n, e.message); } }
process.exit(fail ? 1 : 0);
