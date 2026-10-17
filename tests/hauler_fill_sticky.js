// Hauler deliver mode (src/roles/hauler.js): one fill-vs-drop-off decision per load. Spawn waves swing energyAvailable
// across the 30% line; a loaded hauler must not flip ctl -> fill route -> ctl mid-trip (patrol 10-17: 140t legs).
// node tests/hauler_fill_sticky.js -> exits 1 on failure
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, { RESOURCE_ENERGY: 'energy', STRUCTURE_CONTAINER: 'container', STRUCTURE_TOWER: 'tower', FIND_MY_CREEPS: 1, FIND_DROPPED_RESOURCES: 2, Game: { time: 100, creeps: {}, getObjectById: id => W.objs[id] || null }, _: { filter: (o, f) => Object.values(o).filter(f), max: (a, f) => a.reduce((m, x) => (f(x) > f(m) ? x : m)) } });
let W;
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
const P = { pos: { controllerContainer: [30, 30], fillerContainerA: [35, 24], controllerDrop: [31, 29], miners: [[31, 12]], storageDoor: [37, 30] }, any: {} };
const cont = (id, x, y, e, cap) => ({ id, pos: { x, y }, structureType: 'container', store: { energy: e, getFreeCapacity: () => cap - e } });
stub('utils/plan.js', { get: () => P, key: (x, y) => x * 50 + y });
stub('utils/move.js', { to: (c, x, y) => { W.moved = [x, y]; return false; } });
stub('utils/roomcache.js', { at: (room, x, y) => (x === 30 ? W.cc : x === 35 ? W.fc : x === 31 ? cont('a', 31, 12, 0, 2000) : null), all: () => [] });
stub('utils/trace.js', { why: () => {} });
stub('utils/salvage.js', { dump: () => false, retire: () => false, pick: () => null });
stub('roles/queen.js', { fillRoute: c => { W.fillCalls++; if (!W.needy) return false; W.moved = [34, 27]; return true; } });
stub('managers/threat.js', { holding: () => false });
const H = require(src('roles/hauler.js'));
function mk(o) {
  W = Object.assign({ objs: {}, fillCalls: 0, needy: true, cc: cont('cc', 30, 30, 200, 2000), fc: cont('fc', 35, 24, 1000, 2000) }, o);
  W.objs.cc = W.cc; W.objs.fc = W.fc;
  const room = { name: 'W46N8', energyAvailable: 1800, energyCapacityAvailable: 1800, storage: null, memory: { queenAlive: 100 } };
  const st = { energy: 700, getFreeCapacity: () => 0, getCapacity: () => 700 };
  const c = { name: 'hauler1', room, memory: { home: 'W46N8', working: true }, store: st, pos: { x: 35, y: 22, findInRange: () => [] }, transfer: () => 0 };
  return c;
}
const step = (c, e) => { c.room.energyAvailable = e; W.moved = null; H.run(c); Game.time++; return W.moved; };
const cases = [
  ['full room, loaded -> heads to ctl container', () => { const c = mk(); assert.deepStrictEqual(step(c, 1800), [30, 30]); assert.strictEqual(c.memory.dst, 'cc'); }],
  ['queen alive, already heading to ctl, room drops below 30% -> keeps going to ctl', () => { const c = mk(); step(c, 1800); assert.deepStrictEqual(step(c, 400), [30, 30]); assert.strictEqual(W.fillCalls, 0); }],
  ['fresh load (no dst) with room below 30% -> fill route', () => { const c = mk(); assert.deepStrictEqual(step(c, 400), [34, 27]); assert.strictEqual(c.memory.fl, 1); }],
  ['on fill route, room rises above 30% -> stays on fill route (no flip back)', () => { const c = mk(); step(c, 400); assert.deepStrictEqual(step(c, 900), [34, 27]); }],
  ['on fill route, nothing needy -> leaves fill mode and delivers to ctl', () => { const c = mk(); step(c, 400); W.needy = false; assert.deepStrictEqual(step(c, 1800), [30, 30]); assert.strictEqual(c.memory.fl, undefined); }],
  ['empty -> fill flag cleared', () => { const c = mk(); step(c, 400); c.store.energy = 0; c.store.getFreeCapacity = () => 700; c.memory.working = true; step(c, 400); assert.strictEqual(c.memory.fl, undefined); }],
  ['no queen: fill at 90% threshold even mid-trip', () => { const c = mk(); step(c, 1800); c.room.memory.queenAlive = 0; assert.deepStrictEqual(step(c, 1500), [34, 27]); }],
];
let fail = 0; for (const [n, f] of cases) { try { f(); console.log('ok  ', n); } catch (e) { fail++; console.log('FAIL', n, e.message); } }
console.log(`hauler fill sticky: ${cases.length - fail}/${cases.length}`); process.exit(fail ? 1 : 0);
