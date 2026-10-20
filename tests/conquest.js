// roles/conquest.js pure parts: safety, target prio (CLAIM first), kite, bodies, matrix, spawn gate
const path = require('path'), assert = require('assert');
Object.assign(global, {
  _: require('lodash'),
  ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack', HEAL: 'heal', CARRY: 'carry', WORK: 'work',
  CLAIM: 'claim', MOVE: 'move', RESOURCE_ENERGY: 'energy',
  BODYPART_COST: { move: 50, work: 100, carry: 50, attack: 80, ranged_attack: 150, heal: 250, claim: 600, tough: 10 },
});
const C = require(path.join(__dirname, '..', 'src/roles/conquest.js'));
const cr = (parts, x = 10, y = 10, hits = 100, id = 'h') => ({
  id, body: parts.map(type => ({ type, hits: 100 })), pos: { x, y }, hits,
});
const cost = b => b.reduce((a, p) => a + BODYPART_COST[p], 0);

assert.strictEqual(cost(C.SQUAD_BODY()), 1800, 'squad 1800');
assert.strictEqual(C.SQUAD_BODY().filter(p => p === 'ranged_attack').length, 6);
assert.strictEqual(C.SQUAD_BODY().filter(p => p === 'heal').length, 2);
assert.strictEqual(cost(C.BREAKER_BODY()), 1950, 'breaker 1950');
assert.strictEqual(C.BREAKER_BODY().filter(p => p === 'claim').length, 3);
assert.strictEqual(cost(C.WORKER_BODY()), 1600, 'worker 1600 (8W8C8M, Misaki 15:25 faster)');

const squad = [{ hits: 1600, hitsMax: 1600, heal: 2 }, { hits: 1600, hitsMax: 1600, heal: 2 }]; // 48 heal
assert.strictEqual(C.danger(squad, [cr(['work', 'carry', 'move'])], []), null, 'economy safe');
assert.strictEqual(C.danger(squad, [cr(['ranged_attack', 'ranged_attack', 'move'])], []), null, '20 dps < 48 heal');
assert.ok(C.danger(squad, [cr(Array(3).fill('attack'))], []), '90 dps > 48 heal');
assert.ok(C.danger([{ hits: 1000, hitsMax: 1600, heal: 2 }, { hits: 1600, hitsMax: 1600, heal: 2 }], [], []), 'hits<70%');
assert.ok(C.danger(squad, [], [{ store: { energy: 50 } }]), 'tower');
assert.strictEqual(C.danger(squad, [], [{ store: { energy: 0 } }]), null, 'empty tower');

// CLAIM (reserver) outranks healer
const t = C.pickTarget({ x: 10, y: 10 }, [
  cr(['heal', 'move'], 11, 10, 100, 'healer'),
  cr(['claim', 'claim', 'move'], 20, 20, 100, 'reserver'),
  cr(['attack', 'move'], 12, 10, 100, 'melee'),
]);
assert.strictEqual(t.id, 'reserver', 'CLAIM first');
assert.strictEqual(C.prio(cr(['claim', 'move'])), 0);
assert.strictEqual(C.prio(cr(['heal', 'move'])), 1);
assert.strictEqual(C.prio(cr(['attack', 'move'])), 2);
assert.strictEqual(C.pickTarget({ x: 10, y: 10 }, [cr(['work'], 11, 10, 100, 'm'), cr(['carry'], 14, 10, 100, 'h')]).id, 'h', 'hauler before miner');
// shared focus sticks
assert.strictEqual(C.pickTarget({ x: 10, y: 10 }, [cr(['heal'], 11, 10, 100, 'a'), cr(['claim'], 30, 30, 100, 'b')], 'a').id, 'a', 'focus sticky');

// kite: step away from melee at range 2
const me = { pos: { x: 20, y: 20 } };
const melee = cr(['attack', 'move'], 20, 21, 100, 'm');
const step = C.kiteStep(me, melee, null, [melee]);
assert.ok(step, 'kite returns a step');
assert.ok(Math.max(Math.abs(step.x - 20), Math.abs(step.y - 21)) >= 2, 'kite increases range from melee');

// matrix
const m = { v: {}, set(x, y, c) { this.v[x * 50 + y] = c; }, get(x, y) { return this.v[x * 50 + y] || 0; } };
C.matrixFor('W47N9', m); assert.strictEqual(m.get(25, 25), 255, 'W47N9 forbidden');
const m2 = Object.assign({}, m, { v: {} }); C.matrixFor('W47N8', m2);
assert.strictEqual(m2.get(20, 7), 255); assert.strictEqual(m2.get(20, 8), 0, 'y<8 blocked');
for (const [x, y] of C.PATROL) assert.ok(y >= 8, 'patrol y>=8');

// spawn gate
global.Memory = {}; global.Game = { creeps: {}, rooms: {}, time: 1 };
const room = { storage: { store: { energy: 8000 } }, name: 'W46N8' };
assert.strictEqual(C.wantSpawn(room), null, 'no flags');
assert.strictEqual((Memory.ops = { cq: { spawn: true, claim: true, cmd: 'go' } }, C.wantSpawn(room)), null, 'unarmed = inert');
Memory.ops = { cq: { armed: true, spawn: true, cmd: 'hold' } };
const w1 = C.wantSpawn(room);
assert.ok(w1 && w1.role === 'cqsquad', 'spawn squad');
assert.strictEqual(cost(w1.body), 1800);
Game.creeps = { a: { memory: { role: 'cqsquad' } }, b: { memory: { role: 'cqsquad' } } };
assert.strictEqual(C.wantSpawn(room), null, 'squad full; spawn flag cleared');
assert.strictEqual(Memory.ops.cq.spawn, false);

Memory.ops.cq.claim = true; Memory.ops.cq.cmd = 'go';
Game.creeps = {}; Game.rooms = {};
const w2 = C.wantSpawn(room);
assert.ok(w2 && w2.role === 'cqbreaker', 'claim -> breaker');
assert.strictEqual(cost(w2.body), 1950);

Memory.ops.cq.cmd = 'retreat';
assert.strictEqual(C.wantSpawn(room), null, 'retreat stops spawning');

assert.strictEqual(C.STORAGE_FLOOR, 3100);
// claim-era sites (spawn 15,18 / tower 14,28 / their ramparts) only on a fresh room; at RCL5 the W47N8 layout owns sites
assert.strictEqual(C.claimSites({ level: 2 }), true, 'fresh claim places sites');
assert.strictEqual(C.claimSites({ level: 5 }), false, 'RCL5: pioneers place no ramparts/sites');
console.log('conquest tests ok');
