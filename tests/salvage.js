// Salvage (src/utils/salvage.js): worth-the-trip scoring, decay, hostile exclusion, per-pile reservation, retire.
// node tests/salvage.js -> exits 1 on failure
const path = require('path'), assert = require('assert');
Object.assign(global, { RESOURCE_ENERGY: 'energy', FIND_DROPPED_RESOURCES: 106, FIND_TOMBSTONES: 118, FIND_RUINS: 123, FIND_HOSTILE_CREEPS: 103, LOOK_STRUCTURES: 'structure', TERRAIN_MASK_WALL: 1, ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack',
  _: { filter: (o, f) => Object.values(o).filter(f), sum: a => a.reduce((x, y) => x + y, 0), max: (a, f) => a.reduce((b, x) => b === -Infinity || f(x) > f(b) ? x : b, -Infinity) } });
const S = require(path.join(__dirname, '..', 'src', 'utils', 'salvage.js'));
const pos = (x, y) => ({ x, y, roomName: 'W46N8', getRangeTo(o) { const p = o.pos || o; return Math.max(Math.abs(p.x - x), Math.abs(p.y - y)); }, isNearTo(o) { return this.getRangeTo(o) <= 1; } });
let world, ROOM;
function makeRoom() { ROOM = { name: 'W46N8', find: t => (world[t] || []) }; return ROOM; }
function creep(name, x, y, free, mem = {}) { const c = { name, pos: pos(x, y), memory: mem, store: { energy: 0, getFreeCapacity: () => free, getUsedCapacity() { return Object.keys(this).filter(k => typeof this[k] === 'number').reduce((a, k) => a + this[k], 0); } } }; Object.defineProperty(c, 'room', { get: () => ROOM || makeRoom() }); return c; }
const drop = (id, x, y, a) => ({ id, pos: pos(x, y), resourceType: 'energy', amount: a });
const tomb = (id, x, y, a) => ({ id, pos: pos(x, y), store: { energy: a } });
let T = 1, STOR = null;
function setup(w, creeps) { world = w; T++; makeRoom(); global.Game = { time: T, creeps: {}, spawns: {}, rooms: { W46N8: { storage: STOR } }, getObjectById: id => [].concat(...Object.values(w)).find(o => o.id === id) }; for (const c of creeps) Game.creeps[c.name] = c; }
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
  ['loot: Invader boost tombstone ignored without storage', () => { STOR = null; const c = creep('h', 30, 30, 700); setup({ 118: [{ id: 'i', pos: pos(32, 30), store: { energy: 0, GO: 10, KO: 5, ZH: 5, UH: 5 } }] }, [c]); assert.strictEqual(S.pick(c), null); }],
  ['loot: with storage, small boost tombstone nearby is picked and withdrawn largest-first', () => { STOR = { my: true, pos: pos(35, 28), store: { getFreeCapacity: () => 1e5 } }; const c = creep('h', 30, 30, 700); const t = { id: 'i', pos: pos(31, 30), store: { energy: 0, GO: 10, KO: 5, ZH: 5, UH: 5 } };
    setup({ 118: [t] }, [c]); assert.strictEqual(S.pick(c).id, 'i'); let got; c.withdraw = (o, k) => { got = k; return 0; }; S.take(c, t); assert.strictEqual(got, 'GO'); assert.strictEqual(c.memory.salv, 'i'); STOR = null; }],
  ['loot: energy withdrawn before minerals', () => { STOR = { my: true, pos: pos(35, 28), store: { getFreeCapacity: () => 1e5 } }; const c = creep('h', 30, 30, 700); const t = { id: 'i', pos: pos(31, 30), store: { energy: 60, GO: 10 } }; setup({ 118: [t] }, [c]);
    let got; c.withdraw = (o, k) => { got = k; return 0; }; S.take(c, t); assert.strictEqual(got, 'energy'); STOR = null; }],
  ['dump: carrying GO goes to storage first', () => { const st = { my: true, pos: pos(31, 30), store: { getFreeCapacity: () => 1e5 } }; STOR = st; const c = creep('h', 30, 30, 700); c.store.GO = 10; c.memory.home = 'W46N8'; setup({}, [c]);
    let tr; c.transfer = (s, k) => { tr = k; return 0; }; assert.strictEqual(S.dump(c), true); assert.strictEqual(tr, 'GO'); STOR = null; }],
  ['enclosed drop (no walkable neighbour) ignored', () => {
    const c = creep('h', 33, 31, 700); const d = drop('enc', 31, 33, 960);
    setup({ 106: [d] }, [c]);
    const blocked = new Set(['30,32','30,33','30,34','31,32','31,34','32,32','32,33','32,34']);
    c.room.lookForAt = (look, x, y) => blocked.has(x + ',' + y) ? [{ structureType: 'extension' }] : [];
    assert.strictEqual(S.reachable(c.room, d.pos), false);
    assert.strictEqual(S.pick(c), null);
    assert.strictEqual(c.memory.salv, undefined);
  }],
  ['enclosed sticky salv cleared so hauler resumes work', () => {
    const c = creep('h', 33, 31, 700); c.memory.salv = 'enc'; const d = drop('enc', 31, 33, 960);
    setup({ 106: [d] }, [c]);
    const blocked = new Set(['30,32','30,33','30,34','31,32','31,34','32,32','32,33','32,34']);
    c.room.lookForAt = (look, x, y) => blocked.has(x + ',' + y) ? [{ structureType: 'extension' }] : [];
    assert.strictEqual(S.pick(c), null);
    assert.strictEqual(c.memory.salv, undefined);
  }],
  ['creep already next to enclosed pile may finish it', () => {
    const c = creep('h', 31, 33, 700); const d = drop('enc', 31, 33, 960);
    setup({ 106: [d] }, [c]);
    const blocked = new Set(['30,32','30,33','30,34','31,32','31,34','32,32','32,33','32,34']);
    c.room.lookForAt = (look, x, y) => blocked.has(x + ',' + y) ? [{ structureType: 'extension' }] : [];
    assert.strictEqual(S.reachable(c.room, d.pos, c.pos), true);
    assert.strictEqual(S.pick(c).id, 'enc');
  }],
];
let fail = 0; for (const [n, f] of cases) { try { f(); console.log('ok  ', n); } catch (e) { fail++; console.log('FAIL', n, e.message); } }
process.exit(fail ? 1 : 0);
