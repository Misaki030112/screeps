// raid9 targeting priority + one-shot spawn gate. node tests/raid9.js
const assert = require('assert'), path = require('path');
Object.assign(global, { _: require('lodash'), TOUGH: 'tough', ATTACK: 'attack', MOVE: 'move', RANGED_ATTACK: 'ranged_attack', HEAL: 'heal', Memory: {}, Game: { time: 1 } });
const R = require(path.join(__dirname, '..', 'src', 'roles', 'raid9.js'));
const P = (x, y) => ({ x, y });
const me = P(25, 45);
const tower = { id: 'T', pos: P(34, 28), structureType: 'tower', hits: 3000 };
const spawn = { id: 'S', pos: P(26, 29), structureType: 'spawn', hits: 5000 };
const ext = { id: 'E', pos: P(20, 40), structureType: 'extension', hits: 1000 };
const road = { id: 'R', pos: P(25, 44), structureType: 'road', hits: 1000 };
const feeder = { id: 'F', pos: P(35, 30), energy: 800, hits: 1700 };
const emptyNearTower = { id: 'X', pos: P(33, 28), energy: 0, hits: 100 };
const farCarrier = { id: 'C', pos: P(10, 10), energy: 800, hits: 100 };
// 1) spawn beats tower-feeder (do not chase west while spawn stands)
assert.deepStrictEqual(R.pick(me, { creeps: [farCarrier, emptyNearTower, feeder], structs: [tower, spawn, ext, road] }), { id: 'S', pri: 1 });
// 2) no feeder still spawn
assert.deepStrictEqual(R.pick(me, { creeps: [farCarrier, emptyNearTower], structs: [tower, spawn, ext, road] }), { id: 'S', pri: 1 });
// 2b) spawn dead -> feeder becomes priority
assert.deepStrictEqual(R.pick(me, { creeps: [farCarrier, emptyNearTower, feeder], structs: [tower, ext, road] }), { id: 'F', pri: 2 });
// 3) spawn dead -> creep near a structure close to us first, else structures (tower first), roads ignored
const worker = { id: 'W', pos: P(21, 41), energy: 0, hits: 500 };
assert.deepStrictEqual(R.pick(P(22, 42), { creeps: [worker], structs: [tower, ext, road] }), { id: 'W', pri: 3 });
assert.deepStrictEqual(R.pick(me, { creeps: [worker], structs: [tower, ext, road] }), { id: 'T', pri: 3 });
assert.deepStrictEqual(R.pick(me, { creeps: [], structs: [ext, road] }), { id: 'E', pri: 3 });
assert.deepStrictEqual(R.pick(me, { creeps: [farCarrier], structs: [road] }), { id: 'C', pri: 4 });
assert.strictEqual(R.pick(me, { creeps: [], structs: [road] }), null);
// ranged mass
assert.ok(R.useMass(P(5, 5), [{ pos: P(5, 7) }, { pos: P(7, 7) }, { pos: P(8, 8) }]));
assert.ok(!R.useMass(P(5, 5), [{ pos: P(5, 8) }]));
// bodies within home cap 2300
const cost = { tough: 10, attack: 80, move: 50, ranged_attack: 150, heal: 250 }, c = b => b.reduce((a, p) => a + cost[p], 0);
assert.ok(c(R.MELEE()) <= 2300 && c(R.RANGED()) <= 2300 && R.MELEE().length <= 50);
// spawn gate: off -> null; 4 total, m r m r, never more
const room = { name: 'W46N8' };
assert.strictEqual(R.wantSpawn(room), null);
Memory.ops = { w47n9: { on: true } };
const kinds = [];
for (let i = 0; i < 6; i++) { const w = R.wantSpawn(room); if (!w) break; kinds.push(w.mem.kind); R.noteSpawned(); }
assert.deepStrictEqual(kinds, ['m', 'r', 'm', 'r']);
assert.strictEqual(R.wantSpawn({ name: 'W47N8' }), null);
// heal plan: nobody hurt -> null; lowest ratio wins incl. self; range modes
const H = (id, x, y, hits, hitsMax = 1000) => ({ id, pos: P(x, y), hits, hitsMax });
const meH = H('me', 10, 10, 1000);
assert.strictEqual(R.healPlan(meH, [H('a', 11, 10, 1000)]), null);
assert.deepStrictEqual(R.healPlan(H('me', 10, 10, 900), [H('a', 11, 10, 1000)]).id, 'me');
assert.strictEqual(R.healPlan(H('me', 10, 10, 900), [H('a', 11, 10, 1000)]).mode, 'heal');
assert.strictEqual(R.healPlan(H('me', 10, 10, 900), [H('a', 11, 11, 500)]).id, 'a');
assert.strictEqual(R.healPlan(meH, [H('a', 11, 11, 500)]).mode, 'heal');
assert.strictEqual(R.healPlan(meH, [H('a', 13, 10, 500)]).mode, 'ranged');
assert.strictEqual(R.healPlan(meH, [H('a', 20, 10, 500), H('b', 12, 10, 700)]).mode, 'far');
console.log('raid9 ok');
// formation: melee k0/k2 front row y=1, ranged k1/k3 behind y=2
assert.deepStrictEqual([0,1,2,3].map(R.slotOf), [[30,1],[30,2],[31,1],[31,2]]);
assert.deepStrictEqual(R.pick(me, { creeps: [{ id: 'D', pos: P(25, 43), armed: true, hits: 500 }], structs: [spawn] }), { id: 'D', pri: 1 });
assert.deepStrictEqual(R.pick(me, { creeps: [{ id: 'D', pos: P(25, 30), armed: true, hits: 500 }], structs: [spawn] }), { id: 'S', pri: 1 });
// garrison (after W47N9 safe mode): melee hug wall row y=4, ranged y=5, gate 29,3/29,4 and road 28,4 free, all distinct
{ const gs = [0, 1, 2, 3].map(R.gSlotOf);
  assert.deepStrictEqual(gs, [[30, 4], [30, 5], [31, 4], [31, 5]]);
  for (const g of gs) assert.ok(!(g[0] === 29 && g[1] <= 4) && !(g[0] === 28 && g[1] === 4));
  assert.strictEqual(new Set(gs.map(String)).size, 4); }
// overrun stop-loss threshold (Misaki 10-29 flank)
assert.strictEqual(R.armedParts([]), 0);
assert.strictEqual(R.armedParts([{ attack: 7, ranged: 0 }]), 7); // healer-only body counted 0 attack in live; 7A alone <12
assert.ok(R.armedParts([{ attack: 0, ranged: 6 }, { attack: 0, ranged: 6 }]) >= 12);
assert.ok(R.armedParts([{ attack: 14, ranged: 0 }]) >= 12);
assert.ok(R.armedParts([{ attack: 0, ranged: 6 }]) < 12);
console.log('raid9 overrun ok');
