// W47N8 room module: bodies fit cap, spawn order miner->hauler->upgrader->builder, home creeps ignored.
const assert = require('assert'), path = require('path');
Object.assign(global, { _: require('lodash'), WORK: 'work', CARRY: 'carry', MOVE: 'move', CLAIM: 'claim',
  BODYPART_COST: { work: 100, carry: 50, move: 50 }, FIND_MY_CONSTRUCTION_SITES: 1, FIND_MY_SPAWNS: 2, Game: { time: 5, creeps: {}, rooms: {} } });
const W = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'index.js'));
const cost = b => b.reduce((s, p) => s + BODYPART_COST[p], 0);
for (const e of [300, 550, 800, 1300]) for (const r of ['w8miner', 'w8hauler', 'w8upgrader', 'w8builder']) assert.ok(cost(W.bodyFor(r, e)) <= e, r + '@' + e);
function run(creeps, sites = 0, avail = 300) {
  Game.creeps = creeps; let got = null;
  const spawn = { spawning: null, room: { energyCapacityAvailable: 300, energyAvailable: avail, find: t => (t === 1 ? Array(sites) : []) },
    spawnCreep: (b, n, o) => { got = o.memory; return 0; } };
  W.spawnRun(spawn); return got;
}
const mk = (role, home, extra = {}) => ({ memory: Object.assign({ role, home }, extra), ticksToLive: 1000 });
assert.strictEqual(run({}).role, 'w8miner');
assert.strictEqual(run({}).si, 0);
assert.strictEqual(run({ a: mk('w8miner', 'W47N8', { si: 0 }) }).si, 1);
assert.strictEqual(run({ a: mk('w8miner', 'W47N8', { si: 0 }), b: mk('w8miner', 'W47N8', { si: 1 }) }).role, 'w8hauler');
// home creeps (home W46N8) are not counted
assert.strictEqual(run({ a: mk('miner', 'W46N8'), b: mk('w8miner', 'W46N8', { si: 0 }) }).role, 'w8miner');
const full = { a: mk('w8miner', 'W47N8', { si: 0 }), b: mk('w8miner', 'W47N8', { si: 1 }), c: mk('w8hauler', 'W47N8'), d: mk('w8hauler', 'W47N8') };
assert.strictEqual(run(full).role, 'w8upgrader');
Object.assign(full, { e: mk('w8upgrader', 'W47N8'), f: mk('w8upgrader', 'W47N8') });
assert.strictEqual(run(full, 3).role, 'w8builder');
assert.strictEqual(W.selfSufficient(), false, 'no room visible -> not self-sufficient');
console.log('w47n8 ok');
