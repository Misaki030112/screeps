// 10-20 04:4x strategy review: W47N7 reserver spawned by W47N8 once its cap >= 1800 (shorter walk), home only as fallback
const assert = require('assert'), path = require('path');
Object.assign(global, { _: require('lodash'), CLAIM: 'claim', MOVE: 'move', FIND_MY_SPAWNS: 2,
  Memory: { ops: { r7: { on: 1, by: 'Misaki', endTime: 0 } } }, Game: { time: 1000, rooms: {}, creeps: {} } });
const R = require(path.join(__dirname, '..', 'src', 'roles', 'reserve7.js'));
const w8 = cap => ({ name: 'W47N8', controller: { my: true }, energyCapacityAvailable: cap, find: () => [{}] });
const set = (left, cap) => { Memory.ops.r7.endTime = Game.time + left; Game.rooms = cap ? { W47N8: w8(cap) } : {}; };
// RCL4 W47N8 (cap 1300): home spawns as before, W47N8 does not
set(2400, 1300); assert.ok(R.wantSpawn('W46N8'), 'home spawns while W47N8 cap < 1800'); assert.strictEqual(R.wantSpawn('W47N8'), null, 'W47N8 waits for RCL5');
assert.strictEqual(R.wantSpawn().mem.home, 'W46N8', 'default caller = home');
// RCL5 W47N8: W47N8 spawns, home steps back
set(2400, 1800); const w = R.wantSpawn('W47N8');
assert.ok(w && w.mem.home === 'W47N8' && w.body.length === 4, 'W47N8 spawns 2C2M with home W47N8');
assert.strictEqual(R.wantSpawn('W46N8'), null, 'home does not double-spawn');
// fallback: reservation under 1000 -> home spawns too (W47N8 spawn busy)
set(900, 1800); assert.ok(R.wantSpawn('W46N8'), 'home fallback below 1000');
// enough reservation -> nobody
set(2600, 1800); assert.strictEqual(R.wantSpawn('W47N8'), null); assert.strictEqual(R.wantSpawn('W46N8'), null);
// a live reserve7 blocks both
set(2400, 1800); Game.creeps = { a: { memory: { role: 'reserve7' }, ticksToLive: 400 } };
assert.strictEqual(R.wantSpawn('W47N8'), null); assert.strictEqual(R.wantSpawn('W46N8'), null);
Game.creeps = {};
// W47N8 not visible / not ours -> home
set(2400, 0); assert.ok(R.wantSpawn('W46N8')); assert.strictEqual(R.wantSpawn('W47N8'), null);
console.log('reserve7_owner ok');
