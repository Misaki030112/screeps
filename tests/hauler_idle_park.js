// Idle home hauler parking (src/roles/hauler.js idlePark): with nothing to pick it waits within 3 of the ctl drop on a free
// plain tile that is not a road and not next to an upgrader spot (10-19 23:13: parked on 30,29 it forced a new 1-MOVE upgrader
// through swamp 30,28; walk-in 100 t). Uses the live W46N8 terrain/structures around the controller.
// node tests/hauler_idle_park.js -> exits 1 on failure
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, { RESOURCE_ENERGY: 'energy', STRUCTURE_CONTAINER: 'container', LOOK_STRUCTURES: 's', LOOK_CONSTRUCTION_SITES: 'cs', LOOK_CREEPS: 'c',
  Game: { time: 100, creeps: {}, getObjectById: () => null },
  _: { filter: (o, f) => Object.values(o).filter(f), min: (a, f) => a.reduce((b, x) => (f(x) < f(b) ? x : b)) } });
let W;
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
const P = { pos: { controllerDrop: [31, 29], upgraders: [[30, 30], [31, 30], [29, 30], [31, 31], [29, 31]] } };
for (const [p, e] of [['utils/plan.js', { get: () => P }], ['utils/move.js', { to: (c, x, y, r) => { W.moved = [x, y, r]; return false; } }],
  ['utils/roomcache.js', {}], ['utils/trace.js', {}], ['utils/salvage.js', {}], ['roles/queen.js', {}], ['managers/threat.js', {}],
  ['managers/walls.js', {}], ['managers/links.js', {}]]) stub(p, e);
const H = require(src('roles/hauler.js'));
// W46N8 rows y=26..33, x=26..34 (live 10-19 23:52): terrain . plain ~ swamp # wall; structure letter or _
const MAP = { 26: '~_ ~_ ~_ ~_ ~_ ~r ~e .e .e', 27: '~_ ~_ ~_ ~_ ~r ~_ .e .e .r', 28: '~_ ~_ ~_ ~_ ~_ .r ._ .e .e', 29: '#_ #_ ._ ._ ._ .r .r ._ ._',
  30: '#_ #_ #_ ._ .c ._ ._ .r .r', 31: '#_ #_ #_ .r .l ._ ._ ~r .r', 32: '#_ #_ #c .r .e .e ~e ~e .e' };
const cell = (x, y) => (MAP[y] && x >= 26 && x <= 34) ? MAP[y].split(' ')[x - 26] : '#_';
function run(creeps = {}, pos = [30, 29], mem = {}, spawns = []) {
  W = { moved: null };
  const room = { find: () => spawns.map(([x, y]) => ({ pos: { x, y } })), getTerrain: () => ({ get: (x, y) => ({ '.': 0, '#': 1, '~': 2 })[cell(x, y)[0]] }),
    lookForAt: (k, x, y) => k === 's' ? (cell(x, y)[1] === '_' ? [] : [1]) : k === 'c' ? (creeps[x + ',' + y] ? [creeps[x + ',' + y]] : []) : [] };
  const c = { memory: mem, pos: { x: pos[0], y: pos[1], getRangeTo: (x, y) => Math.max(Math.abs(x - pos[0]), Math.abs(y - pos[1])) } };
  H.idlePark(c, room, P); return { c, moved: W.moved };
}
const cases = [
  ['from 30,29 it leaves the upgrader approach for the nearest free plain non-road tile (32,28)', () => assert.deepStrictEqual(run().moved, [32, 28, 0])],
  ['the chosen tile is remembered', () => assert.deepStrictEqual(run().c.memory.pk, [32, 28])],
  ['32,28 taken by another creep -> next free tile (33,29)', () => assert.deepStrictEqual(run({ '32,28': { name: 'q' } }).moved, [33, 29, 0])],
  ['never a tile next to an upgrader spot, a road, or swamp', () => { const [x, y] = run().moved; assert.ok(![[30, 29], [29, 29], [31, 29], [32, 29], [30, 28]].some(([a, b]) => a === x && b === y)); }],
  ['no free tile -> old behaviour (range 3 of the drop)', () => assert.deepStrictEqual(run({ '32,28': {}, '33,29': {}, '34,29': {} }).moved, [31, 29, 3])],
  ['11-11: never beside a spawn (34,29 is Spawn1 35,28 birth/recycle tile)', () => { global.FIND_MY_SPAWNS = 112;
    try { assert.deepStrictEqual(run({ '32,28': {}, '33,29': {} }, [30, 29], {}, [[35, 28]]).moved, [31, 29, 3]); } finally { delete global.FIND_MY_SPAWNS; } }],
];
let fail = 0; for (const [n, f] of cases) { try { f(); console.log('ok  ', n); } catch (e) { fail++; console.log('FAIL', n, e.message); } }
console.log(`hauler idle park: ${cases.length - fail}/${cases.length}`); process.exit(fail ? 1 : 0);
