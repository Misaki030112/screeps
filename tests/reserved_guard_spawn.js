// W47N8 spawns the shared defender role when a room it reserves (W47N7) is in THREAT.
// node tests/reserved_guard_spawn.js
const assert = require('assert'), path = require('path');
// Minimal lodash 3 surface (Screeps). _.sum(list, iteratee) is the lodash 3 form.
const _ = {
  sum: (list, fn) => { let s = 0; for (const x of Object.values(list || {})) s += fn ? fn(x) : x; return s; },
  filter: (list, fn) => Object.values(list || {}).filter(fn),
  some: (list, fn) => Object.values(list || {}).some(fn),
  min: (list, fn) => Object.values(list || {}).reduce((a, b) => (fn(b) < fn(a) ? b : a)),
  countBy: (list, fn) => { const o = {}; for (const x of Object.values(list || {})) { const k = fn(x); o[k] = (o[k] || 0) + 1; } return o; },
};
Object.assign(global, { _, FIND_MY_STRUCTURES: 10, FIND_MY_CONSTRUCTION_SITES: 1, FIND_MY_SPAWNS: 2, FIND_MY_CREEPS: 3, FIND_STRUCTURES: 5,
  FIND_DROPPED_RESOURCES: 6, FIND_HOSTILE_CREEPS: 4, FIND_HOSTILE_STRUCTURES: 9, STRUCTURE_EXTENSION: 'extension', STRUCTURE_SPAWN: 'spawn', STRUCTURE_TOWER: 'tower',
  STRUCTURE_ROAD: 'road', STRUCTURE_RAMPART: 'rampart', STRUCTURE_CONTAINER: 'container', STRUCTURE_STORAGE: 'storage', STRUCTURE_WALL: 'constructedWall',
  STRUCTURE_INVADER_CORE: 'invaderCore', RESOURCE_ENERGY: 'energy', LOOK_STRUCTURES: 'ls', LOOK_CONSTRUCTION_SITES: 'lc', OK: 0,
  WORK: 'work', CARRY: 'carry', MOVE: 'move', ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack', HEAL: 'heal', TOUGH: 'tough', CLAIM: 'claim',
  BODYPART_COST: { work: 100, carry: 50, move: 50, attack: 80, ranged_attack: 150, heal: 250, tough: 10, claim: 600 } });
const home = { controller: { level: 6, my: true, ticksToDowngrade: 40000 }, energyCapacityAvailable: 2300, energyAvailable: 1800,
  memory: { lastFull: 1 }, storage: { store: { energy: 20000 } }, find: () => [], lookForAt: () => [] };
global.Game = { time: 5000, cpu: { bucket: 10000 }, rooms: { W47N8: null }, creeps: {}, spawns: {} };
global.Memory = { username: 'Misaki', remote: {}, creeps: {}, defense: { remoteDefender: true },
  ops: { r7: { on: true, by: 'Misaki', endTime: 8000 } } };
const src = p => path.join(__dirname, '..', 'src', 'rooms', 'w47n8', p);
const FL = require(src('fill.js'));
FL.want = () => false;
const W = require(src('index.js'));
const T = require(path.join(__dirname, '..', 'src', 'managers', 'threat.js'));
const room = Object.assign({ name: 'W47N8' }, home);
Game.rooms.W47N8 = room;
Memory.remote.W47N7 = { res: { username: 'Misaki', ticksToEnd: 3000 }, seen: 5000, th: { st: 'THREAT', since: 4900, why: 'guard', foes: 1, foeSeen: 4990 } };
assert.strictEqual(T.reservedByUs('W47N7'), true);
assert.strictEqual(T.reservedByUs('W47N9'), false);
assert.strictEqual(T.wantDefender('W47N8'), 'W47N7');
assert.strictEqual(T.armed('W47N7'), true);
let spawned = null;
const spawn = { room, pos: { x: 15, y: 18, getRangeTo: () => 10 }, spawning: null,
  spawnCreep: (b, name, o) => { spawned = { name, role: o.memory.role, remote: o.memory.remote, cost: b.reduce((s, p) => s + BODYPART_COST[p], 0) }; return 0; } };
W.spawnRun(spawn);
assert.ok(spawned, 'expected a spawn');
assert.strictEqual(spawned.role, 'defender');
assert.strictEqual(spawned.remote, 'W47N7');
assert.ok(spawned.cost <= 1300, 'defender body cost ' + spawned.cost);
assert.strictEqual(Memory.remote.W47N7.th.def, spawned.name);
// quiet reserved room: no defender, economy continues
spawned = null;
Memory.remote.W47N7.th = { st: 'SAFE', since: 5000 };
W.spawnRun(spawn);
assert.notStrictEqual(spawned && spawned.role, 'defender', 'SAFE reservation does not spawn a defender, got ' + (spawned && spawned.role));
console.log('reserved guard spawn ok');
