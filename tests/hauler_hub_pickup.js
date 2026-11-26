// Hauler pickup in build hold (src/roles/hauler.js hubPickup): hub -> ctl link is off, so the home hauler waits on the
// manager tile and drains the hub link (>= min(free, SEND)); the source-A container only when it holds a full load.
// Outside the hold it keeps the fixed miner container unless that miner is link-fed (11-11: legacy pickup, no wait at an empty A). node tests/hauler_hub_pickup.js -> exits 1 on failure
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, { LOOK_RESOURCES: 'resource', LOOK_STRUCTURES: 'structure', LOOK_CONSTRUCTION_SITES: 'site', LOOK_CREEPS: 'creep', RESOURCE_ENERGY: 'energy', STRUCTURE_CONTAINER: 'container', STRUCTURE_TOWER: 'tower', FIND_MY_CREEPS: 1, FIND_DROPPED_RESOURCES: 2, Game: { time: 100, creeps: {}, getObjectById: () => null }, _: require('lodash') });
let W;
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
const P = { any: {}, pos: { controllerContainer: [30, 30], fillerContainerA: [35, 24], controllerDrop: [31, 29], miners: [[31, 12]], storageDoor: [36, 32], manager: [36, 30] }, any: {} };
const box = (id, x, y, e, cap) => ({ id, pos: { x, y }, store: { energy: e, getFreeCapacity: () => cap - e } });
stub('utils/plan.js', { get: () => P, key: (x, y) => x * 50 + y });
stub('utils/move.js', { to: (c, x, y) => { W.moved = [x, y]; return W.arrived; } });
stub('utils/roomcache.js', { at: (room, x, y) => (x === 31 && y === 12 ? W.ka : null), all: (room, t) => (t === 'container' && W.ka ? [W.ka] : []) });
stub('utils/trace.js', { why: (c, k) => { W.why = k; } });
stub('utils/salvage.js', { dump: () => false, retire: () => false, pick: () => null });
stub('roles/queen.js', { fillRoute: () => false });
stub('managers/threat.js', { holding: () => false });
stub('managers/walls.js', { noUpgrade: () => W.hold });
stub('managers/links.js', { SEND: 400, roles: () => ({ hub: W.hub, sources: W.src || [box('sa', 30, 11, 0, 800)] }) });
const H = require(src('roles/hauler.js'));
function run(o, mem) {
  W = Object.assign({ hold: true, arrived: true, hub: box('hub', 37, 29, 0, 800), ka: box('ka', 31, 12, 40, 2000) }, o);
  const room = { name: 'W46N8', energyAvailable: 2300, energyCapacityAvailable: 2300, storage: box('st', 37, 31, 9000, 1e6), memory: {},
    lookForAtArea: () => [], lookForAt: () => [], getTerrain: () => ({ get: () => 1 }) };
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
  // 11-11: A's container is link-fed (source link 30,11 adjacent): no 27-tile walk + 60 t wait at an empty container
  ['no hold, link-fed A, container 40: no trip to A (legacy -> idle park by the ctl drop)', () => assert.notDeepStrictEqual(run({ hold: false, arrived: false }).moved, [31, 12])],
  ['no hold, link-fed A, container 900 (link backed up): legacy fetch from A', () => assert.deepStrictEqual(run({ hold: false, arrived: false, ka: box('ka', 31, 12, 900, 2000) }).moved, [31, 12])],
  ['no hold, no source link beside the miner: fixed miner container as before', () => assert.deepStrictEqual(run({ hold: false, arrived: false, src: [box('sx', 20, 20, 0, 800)] }).moved, [31, 12])],
];
// 2026-11-26: RCL8 spawn 35,29 walled the manager tile 36,30 in (live W46N8 grid) -> stand on 38,30 (touches hub + storage)
const GRID = { '35,29': 'spawn', '36,29': 'tower', '37,29': 'link', '35,30': 'factory', '37,30': 'extension', '35,31': 'terminal', '36,31': 'extension', '37,31': 'storage', '36,28': 'extension', '37,28': 'extension', '38,30': 'road', '38,29': 'road', '38,28': 'road' };
const roomSealed = { name: 'W46N9', storage: box('st', 37, 31, 9000, 1e6), getTerrain: () => ({ get: () => 0 }), lookForAt: (t, x, y) => (GRID[x + ',' + y] ? [{ structureType: GRID[x + ',' + y] }] : []) };
cases.push(['sealed manager tile: hubStand -> 38,30 (beside hub and storage)', () => assert.deepStrictEqual(H.hubStand(roomSealed, box('hub', 37, 29, 0, 800), P), [38, 30])]);
cases.push(['open manager tile: hubStand keeps 36,30', () => { const g = Object.assign({}, GRID); delete g['35,29']; const rm = Object.assign({}, roomSealed, { name: 'W46N10', lookForAt: (t, x, y) => (g[x + ',' + y] ? [{ structureType: g[x + ',' + y] }] : []) }); assert.deepStrictEqual(H.hubStand(rm, box('hub', 37, 29, 0, 800), P), [36, 30]); }]);
let fail = 0; for (const [n, f] of cases) { try { f(); console.log('ok  ', n); } catch (e) { fail++; console.log('FAIL', n, e.message); } }
console.log(`hauler hub pickup: ${cases.length - fail}/${cases.length}`); process.exit(fail ? 1 : 0);
