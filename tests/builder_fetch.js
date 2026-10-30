// Builder energy pick (patrol 10-17 21:50 waiting_feed bug). node tests/builder_fetch.js
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, { RESOURCE_ENERGY: 'energy', STRUCTURE_CONTAINER: 'container', STRUCTURE_LINK: 'link', STRUCTURE_ROAD: 'road',
  FIND_DROPPED_RESOURCES: 1, FIND_TOMBSTONES: 2, LOOK_STRUCTURES: 'structure', TERRAIN_MASK_WALL: 1, _: require('lodash') });
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
const pos = (x, y) => ({ x, y, getRangeTo: o => Math.max(Math.abs(x - o.pos.x), Math.abs(y - o.pos.y)) });
const box = (id, x, y, e) => ({ id, pos: { x, y }, store: { energy: e } });
let W = {};
stub('utils/plan.js', { get: () => ({}), key: (x, y) => x * 50 + y });
stub('utils/move.js', { to: () => true });
stub('utils/roomcache.js', { at: (r, x, y) => W[`${x},${y}`] || null, all: () => [], sites: () => [] });
stub('utils/trace.js', { why: () => {} });
stub('managers/remote.js', { CFG: {} });
stub('managers/threat.js', { reserve: () => 1300 });
stub('managers/walls.js', { FLOOR: 5000, noUpgrade: () => false });
let srcA; stub('roles/hauler.js', { pickups: () => [srcA] });
const B = require(src('roles/builder.js'));
const c = { pos: pos(30, 12), store: { getFreeCapacity: () => 250 } };
const home = (st, drops = [], level) => ({ name: 'W46N8', storage: st, controller: level ? { level } : undefined, find: t => t === 1 ? drops : [] });
const cases = [
  ['far ctl container (1000) beats waiting; source A ignored', () => {
    W = {}; srcA = box('A', 31, 10, 1200); const ctl = box('ctl', 30, 30, 1000);
    assert.strictEqual(B.pickSource(c, home(box('st', 38, 30, 1200)), {}, [ctl], 35, 24).id, 'ctl'); }],
  ['storage above reserve picked', () => {
    W = {}; srcA = box('A', 31, 10, 1200);
    assert.strictEqual(B.pickSource(c, home(box('st', 38, 30, 3000)), {}, [], 35, 24).id, 'st'); }],
  ['RCL6: storage kept at walls.FLOOR 5k (live 10:07 builders drained 30k->17k toward 1300)', () => {
    W = {}; srcA = box('A', 31, 10, 0);
    assert.strictEqual(B.pickSource(c, home(box('st', 38, 30, 4000), [], 6), {}, [], 35, 24), null);
    assert.strictEqual(B.pickSource(c, home(box('st', 38, 30, 6000), [], 6), {}, [], 35, 24).id, 'st'); }],
  ['nothing hub -> source A only if keeps hauler load', () => {
    W = {}; srcA = box('A', 31, 10, 400);
    assert.strictEqual(B.pickSource(c, home(box('st', 38, 30, 500)), {}, [], 35, 24), null);
    srcA = box('A', 31, 10, 800);
    assert.strictEqual(B.pickSource(c, home(box('st', 38, 30, 500)), {}, [], 35, 24).id, 'A'); }],
  ['dropped energy counts', () => {
    W = {}; srcA = box('A', 31, 10, 0); const d = { id: 'd', pos: { x: 33, y: 15 }, amount: 300, resourceType: 'energy' };
    assert.strictEqual(B.pickSource(c, home(null, [d]), {}, [], 35, 24).id, 'd'); }],
  ['enclosed drop skipped; storage used instead (patrol 10-30 10:2x 31,33)', () => {
    W = {}; srcA = box('A', 31, 10, 0);
    const d = { id: 'enc', pos: { x: 31, y: 33 }, amount: 588, resourceType: 'energy' };
    const h = home(box('st', 38, 30, 16000), [d]);
    const blocked = new Set(['30,32','30,33','30,34','31,32','31,34','32,32','32,33','32,34']);
    h.lookForAt = (look, x, y) => blocked.has(x + ',' + y) ? [{ structureType: 'extension' }] : (x === 31 && y === 33 ? [{ structureType: 'road' }] : []);
    assert.strictEqual(B.pickSource(c, h, {}, [], 35, 24).id, 'st'); }],
];
let fail = 0; for (const [n, f] of cases) { try { f(); console.log('ok  ', n); } catch (e) { fail++; console.log('FAIL', n, e.message); } }
console.log(`builder fetch: ${cases.length - fail}/${cases.length}`); process.exit(fail ? 1 : 0);
