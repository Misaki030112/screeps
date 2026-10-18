// Hauler pickup in build hold (src/roles/hauler.js hubPickup): hub -> ctl link is off, so the home hauler waits on the
// manager tile and drains the hub link (>= min(free, SEND)); the source-A container only when it holds a full load.
// Outside the hold it keeps the fixed miner container. node tests/hauler_hub_pickup.js -> exits 1 on failure
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, { RESOURCE_ENERGY: 'energy', STRUCTURE_CONTAINER: 'container', STRUCTURE_TOWER: 'tower', FIND_MY_CREEPS: 1, FIND_DROPPED_RESOURCES: 2, Game: { time: 100, creeps: {}, getObjectById: () => null }, _: { filter: (o, f) => Object.values(o).filter(f) } });
let W;
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
const P = { pos: { controllerContainer: [30, 30], fillerContainerA: [35, 24], controllerDrop: [31, 29], miners: [[31, 12]], storageDoor: [36, 32], manager: [36, 30] }, any: {} };
const box = (id, x, y, e, cap) => ({ id, pos: { x, y }, store: { energy: e, getFreeCapacity: () => cap - e } });
stub('utils/plan.js', { get: () => P, key: (x, y) => x * 50 + y });
stub('utils/move.js', { to: (c, x, y) => { W.moved = [x, y]; return W.arrived; } });
stub('utils/roomcache.js', { at: (room, x, y) => (x === 31 ? W.ka : null), all: () => [] });
stub('utils/trace.js', { why: (c, k) => { W.why = k; } });
stub('utils/salvage.js', { dump: () => false, retire: () => false, pick: () => null });
stub('roles/queen.js', { fillRoute: () => false });
stub('managers/threat.js', { holding: () => false });
stub('managers/walls.js', { noUpgrade: () => W.hold });
stub('managers/links.js', { SEND: 400, roles: () => ({ hub: W.hub, sources: [box('sa', 30, 11, 0, 800)] }) });
const H = require(src('roles/hauler.js'));
function run(o, mem) {
  W = Object.assign({ hold: true, arrived: true, hub: box('hub', 37, 29, 0, 800), ka: box('ka', 31, 12, 40, 2000) }, o);
  const room = { name: 'W46N8', energyAvailable: 2300, energyCapacityAvailable: 2300, storage: box('st', 37, 31, 9000, 1e6), memory: {} };
  const c = { name: 'hauler1', room, memory: Object.assign({ home: 'W46N8' }, mem), store: { energy: 0, getFreeCapacity: () => 800, getCapacity: () => 800 }, pos: { findInRange: () => [] },
    withdraw: t => { W.took = t.id; return 0; } };
  W.moved = null; H.run(c); return Object.assign({ c }, W);
}
const cases = [
  ['hold: walks to the manager tile, not the source-A container', () => assert.deepStrictEqual(run({ arrived: false }).moved, [36, 30])],
  ['hold: hub >= 400 -> withdraws from hub and delivers', () => { const r = run({ hub: box('hub', 37, 29, 450, 800) }); assert.strictEqual(r.took, 'hub'); assert.strictEqual(r.c.memory.working, true); }],
  ['hold: hub < 400 -> waits (p), no intent', () => { const r = run({ hub: box('hub', 37, 29, 300, 800) }); assert.strictEqual(r.took, undefined); assert.strictEqual(r.why, 'p'); }],
  ['hold: container A holds a full load (link stalled) -> back to the container', () => assert.deepStrictEqual(run({ arrived: false, ka: box('ka', 31, 12, 900, 2000) }).moved, [31, 12])],
  ['hold: stale legacy flag lp=1 -> still the hub (lp cleared)', () => { const r = run({ arrived: false }, { lp: 1 }); assert.deepStrictEqual(r.moved, [36, 30]); assert.strictEqual(r.c.memory.lp, undefined); }],
  ['no hold: fixed miner container as before', () => assert.deepStrictEqual(run({ hold: false, arrived: false }).moved, [31, 12])],
];
let fail = 0; for (const [n, f] of cases) { try { f(); console.log('ok  ', n); } catch (e) { fail++; console.log('FAIL', n, e.message); } }
console.log(`hauler hub pickup: ${cases.length - fail}/${cases.length}`); process.exit(fail ? 1 : 0);
