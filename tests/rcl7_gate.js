// RCL7 industry block (docs/RCL7.md, strategy review 2026-10-19): with plan.RCL7_INDUSTRY off, RCL7 plans spawn 2 + tower 3 +
// 10 extensions + link only (no factory, no labs 4-6); the RCL6 mineral line keeps its home hauler at RCL7. node tests/rcl7_gate.js
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
const plan = require(src('utils/plan.js'));
const at = r => plan.upTo('W46N8', r), count = (r, t) => at(r).filter(s => s.type === t).length;
const C = { spawn: 15000, extension: 3000, link: 5000, tower: 5000, lab: 50000, factory: 100000, container: 5000 };
const cases = [
  ['gate OFF', () => assert.strictEqual(plan.RCL7_INDUSTRY, false)],
  ['RCL7: no factory, labs stay 3 (RCL6 set)', () => { assert.strictEqual(count(7, 'factory'), 0); assert.strictEqual(count(7, 'lab'), 3); assert.strictEqual(count(6, 'lab'), 3); }],
  ['RCL7 new = spawn 30,34 + tower 39,23 + 10 ext + link', () => { const n = at(7).filter(s => s.rcl === 7 && s.type !== 'road');
    assert.deepStrictEqual(n.filter(s => s.type === 'spawn').map(s => [s.x, s.y]), [[30, 34]]);
    assert.deepStrictEqual(n.filter(s => s.type === 'tower').map(s => [s.x, s.y]), [[39, 23]]);
    assert.strictEqual(n.filter(s => s.type === 'extension').length, 10); assert.strictEqual(n.length, 13); }],
  ['RCL7 build energy <= 55k', () => { const e = at(7).filter(s => s.rcl === 7).reduce((t, s) => t + (C[s.type] || 0), 0); assert.ok(e <= 55000, e); }],
  ['RCL8 still plans no factory while the gate is off', () => assert.strictEqual(count(8, 'factory'), 0)],
];
// home hauler target at RCL7 with 4 links (queen regime): 1, not 0
Object.assign(global, { WORK: 'work', CARRY: 'carry', MOVE: 'move', RESOURCE_ENERGY: 'energy', STRUCTURE_LINK: 'link', STRUCTURE_CONTAINER: 'container', STRUCTURE_SPAWN: 'spawn', STRUCTURE_EXTENSION: 'extension', STRUCTURE_TOWER: 'tower' });
cases.push(['RCL7 + 4 links, STATIONARY_FILL off -> T.hauler 1', () => {
  const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
  delete require.cache[require.resolve(src('managers/spawn.js'))];
  stub('utils/roomcache.js', { all: (r, t) => t === 'link' ? [1, 2, 3, 4] : [], at: () => null, get: () => ({ at: [] }), sites: () => [] });
  stub('roles/builder.js', { remoteRoadSite: () => null }); stub('utils/move.js', { to: () => true }); stub('utils/trace.js', { why: () => {} });
  stub('managers/threat.js', { reserve: () => 5600, holding: () => false });
  global._ = global._ || { filter: (a, f) => Object.values(a).filter(f), sum: (a, f) => a.reduce((t, x) => t + f(x), 0), countBy: (a, f) => a.reduce((o, x) => (o[f(x)] = (o[f(x)] || 0) + 1, o), {}) };
  Object.assign(global, { FIND_HOSTILE_CREEPS: 103, FIND_MY_CREEPS: 102, FIND_STRUCTURES: 107, FIND_MY_STRUCTURES: 108, FIND_MY_CONSTRUCTION_SITES: 114, FIND_CONSTRUCTION_SITES: 111, FIND_DROPPED_RESOURCES: 106, FIND_SOURCES: 105, FIND_MINERALS: 116, STRUCTURE_STORAGE: 'storage', STRUCTURE_RAMPART: 'rampart', STRUCTURE_WALL: 'constructedWall', STRUCTURE_ROAD: 'road', STRUCTURE_EXTRACTOR: 'extractor', STRUCTURE_TERMINAL: 'terminal', ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack', HEAL: 'heal', TOUGH: 'tough', CLAIM: 'claim', BODYPART_COST: { move: 50, work: 100, carry: 50, attack: 80, ranged_attack: 150, heal: 250, claim: 600, tough: 10 } });
  global.Memory = { rooms: { W46N8: {} }, ops: {}, remotes: {} }; global.Game = { time: 1000, rooms: {}, creeps: {}, spawns: {} };
  const S = require(src('managers/spawn.js'));
  const room = { name: 'W46N8', memory: {}, controller: { level: 7 }, energyCapacityAvailable: 5600, storage: { store: { energy: 20000 } }, find: () => [] };
  assert.strictEqual(S.targets(room, {}, 0, 900, 0).hauler, 1);
}]);
let fail = 0;
for (const [n, f] of cases) { try { f(); console.log('ok  ', n); } catch (e) { fail++; console.log('FAIL', n, e.message); } }
process.exit(fail ? 1 : 0);
