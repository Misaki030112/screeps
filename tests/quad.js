// quad pure helpers + inert gate. node tests/quad.js
const path = require('path'), assert = require('assert'), src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, { _: require('lodash'), RANGED_ATTACK: 'ranged_attack', HEAL: 'heal', MOVE: 'move', CLAIM: 'claim', WORK: 'work', CARRY: 'carry', ATTACK: 'attack', RESOURCE_ENERGY: 'energy',
  BODYPART_COST: { ranged_attack: 150, heal: 250, move: 50, claim: 600 }, Game: { time: 1, creeps: {} }, Memory: {} });
const Q = require(src('roles/quad.js')), CQ = require(src('roles/conquest.js'));
const T = (w = new Set(), s = new Set()) => (x, y) => w.has(x + ',' + y) ? 'wall' : s.has(x + ',' + y) ? 'swamp' : 'plain';
assert.strictEqual(Q.anchorCost(10, 10, T()), 2);
assert.strictEqual(Q.anchorCost(10, 10, T(new Set(['11,11']))), 255, 'any wall cell blocks the anchor');
assert.strictEqual(Q.anchorCost(10, 10, T(new Set(), new Set(['10,11']))), 10, 'swamp cell -> worst cost 10');
assert.strictEqual(Q.anchorCost(48, 10, T()), 255, 'edge: cell x=49 not allowed');
assert.strictEqual(Q.anchorCost(10, 10, T(), (x, y) => 1), 1, 'roads');
const P = (x, y) => ({ x, y, roomName: 'R' });
assert.deepStrictEqual(Q.formedAnchor({ 0: P(5, 5), 1: P(6, 5), 2: P(5, 6), 3: P(6, 6) }), { x: 5, y: 5, roomName: 'R' });
assert.strictEqual(Q.formedAnchor({ 0: P(5, 5), 1: P(6, 5), 2: P(5, 6), 3: P(7, 6) }), null);
const m = (n, x, y, hits) => ({ n, pos: P(x, y), hits, hitsMax: 1000 });
const me = m('a', 5, 5, 1000), b = m('b', 6, 5, 600), c = m('c', 8, 5, 300);
assert.deepStrictEqual(Q.healPick(me, [me, b, c]).map(x => x.n || x), ['b', 'heal'], 'adjacent hurt first');
assert.deepStrictEqual(Q.healPick(me, [me, c]).map(x => x.n || x), ['c', 'rangedHeal']);
assert.strictEqual(Q.healPick(me, [me]), null);
const body = Q.BODY(); assert.strictEqual(body.reduce((s, p) => s + BODYPART_COST[p], 0), 2300); assert.strictEqual(body.length, 18);
assert.strictEqual(CQ.BREAKER_BODY().reduce((s, p) => s + BODYPART_COST[p], 0), 1950);
// INERT: nothing spawns without Memory.ops.cq.armed === true, even with every other flag set
const room = { storage: { store: { energy: 50000 } } };
Memory.ops = { cq: { quadSpawn: true, spawn: true, claim: true, cmd: 'go' } };
assert.strictEqual(Q.wantSpawn(room), null); assert.strictEqual(CQ.wantSpawn(room), null);
Memory.ops.cq.armed = true; assert.strictEqual(Q.wantSpawn(room).role, 'cqquad');
Memory.ops.cq.cmd = 'retreat'; assert.strictEqual(Q.wantSpawn(room), null, 'retreat stops spawning');
Memory.ops.cq.cmd = 'go'; room.storage.store.energy = 7000; assert.strictEqual(Q.wantSpawn(room), null, 'home floor 8k');
// reserver first
const h = (id, parts, x) => ({ id, pos: P(x, 5), hits: 100, body: parts.map(t => ({ type: t, hits: 100 })), owner: { username: 'BustJetter' } });
assert.strictEqual(CQ.pickTarget(P(5, 5), [h('hauler', ['carry', 'move'], 6), h('res', ['claim', 'move'], 20)]).id, 'res');
console.log('quad ok');
