// 10-19 21:4x strategy review: W47N7 rminer 6W (repair blocks harvest; 5W mined ~9/t) + learned replacement lead
const assert = require('assert'), path = require('path');
Object.assign(global, { _: require('lodash'), WORK: 'work', CARRY: 'carry', MOVE: 'move', ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack', HEAL: 'heal', TOUGH: 'tough', CLAIM: 'claim',
  RESOURCE_ENERGY: 'energy', Memory: { ops: {} }, Game: { time: 1000, rooms: {}, creeps: {} } });
const W = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'index.js'));
const cnt = (b, t) => b.filter(p => p === t).length, cost = b => b.reduce((a, p) => a + ({ work: 100, carry: 50, move: 50 })[p], 0);
const b13 = W.bodyFor('w8rminer', 1300);
assert.deepStrictEqual([cnt(b13, 'work'), cnt(b13, 'carry'), cnt(b13, 'move')], [6, 1, 3], '6W1C3M at cap 1300: ' + b13);
assert.strictEqual(cost(b13), 800);
// 1 tile/t on road: fatigue = non-MOVE, non-empty-CARRY parts x1 <= 2 x MOVE
assert.ok(cnt(b13, 'work') <= 2 * cnt(b13, 'move'), 'road speed 1');
assert.deepStrictEqual(W.bodyFor('w8rminer', 800), b13, 'cap 800 -> same body');
const b55 = W.bodyFor('w8rminer', 550); assert.ok(cost(b55) <= 550 && cnt(b55, 'work') === 4, 'cap 550 -> 4W: ' + b55);
for (const e of [300, 400, 550, 700, 800, 1300, 5600]) assert.ok(cost(W.bodyFor('w8rminer', e)) <= Math.max(e, 300), 'fits ' + e);
// lead: learned walk + spawn + 20, default walk 90, clamp 40..180
const c = { body: b13 };
assert.strictEqual(W.rmLead8(1, c), 90 + 30 + 20, 'default');
Memory.ops.w8rlead = { 0: 48, 1: 70 };
assert.strictEqual(W.rmLead8(0, c), 48 + 30 + 20); assert.strictEqual(W.rmLead8(1, c), 70 + 30 + 20);
Memory.ops.w8rlead = { 0: 5, 1: 900 };
assert.strictEqual(W.rmLead8(0, c), 40 + 50); assert.strictEqual(W.rmLead8(1, c), 180 + 50, 'clamped');
console.log('w47n8 rminer ok');
