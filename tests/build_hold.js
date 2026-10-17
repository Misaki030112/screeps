// Build hold (Misaki 2026-10-17 21:00 "先停止升级，全力基建"): walls.noUpgrade + spawn targets. node tests/build_hold.js
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, { WORK: 'work', CARRY: 'carry', MOVE: 'move', RESOURCE_ENERGY: 'energy', STRUCTURE_LINK: 'link', STRUCTURE_CONTAINER: 'container', STRUCTURE_SPAWN: 'spawn', STRUCTURE_EXTENSION: 'extension', STRUCTURE_TOWER: 'tower', FIND_HOSTILE_CREEPS: 1, _: { filter: () => [] }, Memory: {} });
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
let roadsDone = false;
stub('managers/home.js', { on: () => false, alert: () => false, active: () => false });
stub('managers/roads.js', { done: () => roadsDone, phase: () => 'core', repairTarget: () => null });
stub('managers/threat.js', { reserve: () => 1300, holding: () => false });
const Wl = require(src('managers/walls.js'));
const room = (o = {}) => ({ name: 'W46N8', memory: {}, find: () => [], energyCapacityAvailable: 2000,
  controller: { my: true, level: o.level || 6, ticksToDowngrade: o.ttd == null ? 66000 : o.ttd }, storage: { store: { energy: o.storage || 1000 } } });
const cases = [
  ['roads phase, timer 66k -> hold', () => assert.strictEqual(Wl.noUpgrade(room()), true)],
  ['timer < 20000 -> no hold (safety upgrader)', () => assert.strictEqual(Wl.noUpgrade(room({ ttd: 19999 })), false)],
  ['RCL5 / RCL8 -> no hold', () => { assert.strictEqual(Wl.noUpgrade(room({ level: 5 })), false); assert.strictEqual(Wl.noUpgrade(room({ level: 8 })), false); }],
  ['Memory.roads.upgrade override -> no hold', () => { Memory.roads = { upgrade: 1 }; try { assert.strictEqual(Wl.noUpgrade(room()), false); } finally { Memory.roads = {}; } }],
  ['roads done -> bank phase, no hold', () => { roadsDone = true; try { assert.strictEqual(Wl.phase(room()), 'bank'); assert.strictEqual(Wl.noUpgrade(room()), false); } finally { roadsDone = false; } }],
];
// spawn targets with a stubbed walls module
let hold = true, ph = 'roads';
stub('managers/walls.js', { noUpgrade: () => hold, phase: () => ph, wantBuilder: () => false, reserved: () => 0 });
const P = { pos: { upgraders: [[29, 30], [30, 31], [31, 30]], controllerContainer: [30, 30], fillerContainerA: [35, 24], fillers: [], miners: [] }, raw: { stamps: {} }, any: {} };
stub('utils/plan.js', { get: () => P, key: (x, y) => x * 50 + y });
stub('roles/builder.js', { remoteRoadSite: () => null });
stub('utils/move.js', { to: () => true });
stub('utils/roomcache.js', { all: () => [], at: () => null, get: () => ({ at: [] }), sites: () => [] });
stub('utils/trace.js', { why: () => {} });
const S = require(src('managers/spawn.js'));
const T = (o) => { hold = o.hold; ph = o.ph || 'roads'; return S.targets(room({ storage: o.storage }), {}, 0, 900, o.sites); };
cases.push(
  ['hold: 0 upgraders', () => assert.strictEqual(T({ hold: true, sites: 5, storage: 1000 }).upgrader, 0)],
  ['no hold in roads (timer low): 1 upgrader', () => assert.strictEqual(T({ hold: false, sites: 5, storage: 1000 }).upgrader, 1)],
  ['bank phase after roads: max 1 upgrader even with surplus', () => assert.strictEqual(T({ hold: false, ph: 'bank', sites: 0, storage: 15000 }).upgrader, 1)],
  ['hold + storage 3000 + >=3 sites: 3 builders', () => assert.strictEqual(T({ hold: true, sites: 5, storage: 3000 }).builder, 3)],
  ['hold + storage 2999: 2 builders', () => assert.strictEqual(T({ hold: true, sites: 5, storage: 2999 }).builder, 2)],
  ['no hold: 2 builders max at home sites', () => assert.strictEqual(T({ hold: false, sites: 5, storage: 9000 }).builder, 2)],
);
let fail = 0; for (const [n, f] of cases) { try { f(); console.log('ok  ', n); } catch (e) { fail++; console.log('FAIL', n, e.message); } }
console.log(`build hold: ${cases.length - fail}/${cases.length}`); process.exit(fail ? 1 : 0);
