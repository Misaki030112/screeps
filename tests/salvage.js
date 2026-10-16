// Salvage (src/utils/salvage.js): worth-the-trip scoring, decay, hostile exclusion, per-pile reservation, retire.
// node tests/salvage.js -> exits 1 on failure
const path = require('path'), assert = require('assert');
Object.assign(global, { RESOURCE_ENERGY: 'energy', FIND_DROPPED_RESOURCES: 106, FIND_TOMBSTONES: 118, FIND_RUINS: 123, FIND_HOSTILE_CREEPS: 103, ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack',
  _: { filter: (o, f) => Object.values(o).filter(f) } });
const S = require(path.join(__dirname, '..', 'src', 'utils', 'salvage.js'));
const pos = (x, y) => ({ x, y, roomName: 'W46N8', getRangeTo(o) { const p = o.pos || o; return Math.max(Math.abs(p.x - x), Math.abs(p.y - y)); }, isNearTo(o) { return this.getRangeTo(o) <= 1; } });
let world;
function room() { return { name: 'W46N8', find: t => (world[t] || []) }; }
function creep(name, x, y, free, mem = {}) { const c = { name, pos: pos(x, y), memory: mem, store: { energy: 0, getFreeCapacity: () => free } }; Object.defineProperty(c, 'room', { get: room }); return c; }
const drop = (id, x, y, a) => ({ id, pos: pos(x, y), resourceType: 'energy', amount: a });
const tomb = (id, x, y, a) => ({ id, pos: pos(x, y), store: { energy: a } });
let T = 1;
function setup(w, creeps) { world = w; T++; global.Game = { time: T, creeps: {}, spawns: {}, getObjectById: id => [].concat(...Object.values(w)).find(o => o.id === id) }; for (const c of creeps) Game.creeps[c.name] = c; }
const cases = [
  ['scout tombstone 45 is below MIN -> ignored', () => { const c = creep('h', 30, 30, 700); setup({ 118: [tomb('t', 31, 30, 45)] }, [c]); assert.strictEqual(S.pick(c), null); }],
  ['650 dropped 3 tiles away -> picked', () => { const c = creep('h', 30, 30, 700); setup({ 106: [drop('d', 33, 30, 650)] }, [c]); assert.strictEqual(S.pick(c).id, 'd'); assert.strictEqual(c.memory.salv, 'd'); }],
  ['small pile far away not worth the trip', () => { const c = creep('h', 30, 30, 700); setup({ 106: [drop('d', 30, 45, 120)] }, [c]); assert.strictEqual(S.pick(c), null); }],
  ['decay counted: 1500 drop loses 2/tile', () => assert.strictEqual(S.score(drop('d', 0, 0, 1500), 10, 2000, 0), 1480)],
  ['tombstone does not decay en route', () => assert.strictEqual(S.score(tomb('t', 0, 0, 700), 10, 2000, 0), 700)],
  ['armed hostile within 5 -> skipped', () => { const c = creep('h', 30, 30, 700); const h = { pos: pos(34, 30), body: [{ type: 'attack', hits: 100 }] }; setup({ 106: [drop('d', 33, 30, 650)], 103: [h] }, [c]); assert.strictEqual(S.pick(c), null); }],
  ['unarmed scout nearby does not block', () => { const c = creep('h', 30, 30, 700); const h = { pos: pos(34, 30), body: [{ type: 'tough', hits: 100 }] }; setup({ 106: [drop('d', 33, 30, 650)], 103: [h] }, [c]); assert.strictEqual(S.pick(c).id, 'd'); }],
  ['reservation: second hauler does not chase a pile the first covers', () => { const a = creep('a', 30, 30, 700), b = creep('b', 31, 30, 700); setup({ 106: [drop('d', 33, 30, 650)] }, [a, b]); assert.strictEqual(S.pick(a).id, 'd'); assert.strictEqual(S.pick(b), null); }],
  ['reservation: big pile is shared when one carrier cannot take it all', () => { const a = creep('a', 30, 30, 400), b = creep('b', 31, 30, 400); setup({ 106: [drop('d', 33, 30, 1000)] }, [a, b]); assert.strictEqual(S.pick(a).id, 'd'); assert.strictEqual(S.pick(b).id, 'd'); }],
  ['sticky target survives next tick', () => { const a = creep('a', 30, 30, 700); setup({ 106: [drop('d', 33, 30, 650)] }, [a]); S.pick(a); setup({ 106: [drop('d', 33, 30, 649)] }, [a]); assert.strictEqual(S.pick(a).id, 'd'); }],
  ['retire: old + carrying -> deliver (no recycle)', () => { const c = creep('h', 30, 30, 0); c.ticksToLive = 20; c.store.energy = 300; setup({}, [c]); assert.strictEqual(S.retire(c, 50), false); assert.strictEqual(c.memory.working, true); }],
  ['retire: old + empty next to spawn -> recycle', () => { const c = creep('h', 34, 28, 700); c.ticksToLive = 20; let rec = 0; setup({}, [c]); Game.spawns.S = { pos: pos(35, 28), recycleCreep: () => { rec++; return 0; } }; assert.strictEqual(S.retire(c, 50), true); assert.strictEqual(rec, 1); }],
  ['retire: young -> no-op', () => { const c = creep('h', 30, 30, 700); c.ticksToLive = 900; setup({}, [c]); assert.strictEqual(S.retire(c, 50), false); }],
];
let fail = 0; for (const [n, f] of cases) { try { f(); console.log('ok  ', n); } catch (e) { fail++; console.log('FAIL', n, e.message); } }
process.exit(fail ? 1 : 0);
