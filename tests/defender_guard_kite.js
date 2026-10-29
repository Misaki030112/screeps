// GUARD remote (W47N7) kite must use cfgFor — CFG[W47N7] is undefined and C.avoid used to throw (patrol 2026-10-29).
// node tests/defender_guard_kite.js
const fs = require('fs'), path = require('path'), assert = require('assert'), vm = require('vm');
const ROOT = path.join(__dirname, '..');
const _ = {
  filter: (a, f) => Object.values(a || {}).filter(f),
  some: (a, f) => Object.values(a || {}).some(f),
  sum: (a, f) => Object.values(a || {}).reduce((s, x) => s + (f ? f(x) : x), 0),
};
Object.assign(global, {
  _, TOP: 1, TOP_RIGHT: 2, RIGHT: 3, BOTTOM_RIGHT: 4, BOTTOM: 5, BOTTOM_LEFT: 6, LEFT: 7, TOP_LEFT: 8,
  ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack', HEAL: 'heal', MOVE: 'move', WORK: 'work', CARRY: 'carry', TOUGH: 'tough',
  FIND_HOSTILE_CREEPS: 4, FIND_MY_SPAWNS: 2, LOOK_STRUCTURES: 'ls', LOOK_CREEPS: 'lc',
  STRUCTURE_ROAD: 'road', RESOURCE_ENERGY: 'energy',
  TERRAIN_MASK_WALL: 1, TERRAIN_MASK_SWAMP: 2,
  RoomPosition: function (x, y, roomName) { this.x = x; this.y = y; this.roomName = roomName; },
});
global.Memory = { username: 'Misaki', remote: { W47N7: { th: { st: 'DEFEND', def: 'rdef1', since: 1, why: 'invader' } } }, defense: { remotePatrol: true }, ops: {} };
global.Game = { time: 100, creeps: {}, rooms: {}, spawns: {} };

const terrain = { get: () => 0 };
const room = {
  name: 'W47N7', controller: { my: false },
  getTerrain: () => terrain,
  find: (t) => t === FIND_HOSTILE_CREEPS ? [inv] : [],
  lookForAt: () => [],
};
const inv = {
  id: 'inv1', owner: { username: 'Invader' }, hits: 800, hitsMax: 1000, ticksToLive: 1000,
  pos: { x: 18, y: 2, getRangeTo: (a, b) => {
    if (typeof a === 'object') return Math.max(Math.abs(18 - a.x), Math.abs(2 - a.y));
    return Math.max(Math.abs(18 - a), Math.abs(2 - b));
  }, inRangeTo: (a, b, r) => {
    if (typeof a === 'object') return Math.max(Math.abs(18 - a.x), Math.abs(2 - a.y)) <= b;
    return Math.max(Math.abs(18 - a), Math.abs(2 - b)) <= r;
  } },
  body: [
    { type: 'tough', hits: 100 }, { type: 'tough', hits: 100 },
    { type: 'move', hits: 100 }, { type: 'move', hits: 100 }, { type: 'move', hits: 100 }, { type: 'move', hits: 100 },
    { type: 'ranged_attack', hits: 100 }, { type: 'work', hits: 100 }, { type: 'attack', hits: 100 }, { type: 'move', hits: 100 },
  ],
};
const moved = [];
const creep = {
  name: 'rdef1', owner: { username: 'Misaki' }, hits: 1200, hitsMax: 1200, ticksToLive: 1400,
  room, memory: { role: 'defender', remote: 'W47N7', home: 'W47N8' },
  pos: {
    x: 18, y: 5,
    getRangeTo: (t) => Math.max(Math.abs(18 - t.pos.x), Math.abs(5 - t.pos.y)),
    inRangeTo: (a, b, r) => {
      if (typeof a === 'object') return Math.max(Math.abs(18 - a.x), Math.abs(5 - a.y)) <= b;
      return Math.max(Math.abs(18 - a), Math.abs(5 - b)) <= r;
    },
    isNearTo: () => false,
  },
  body: [
    { type: 'ranged_attack', hits: 100 }, { type: 'ranged_attack', hits: 100 }, { type: 'ranged_attack', hits: 100 },
    { type: 'ranged_attack', hits: 100 }, { type: 'ranged_attack', hits: 100 },
    { type: 'move', hits: 100 }, { type: 'move', hits: 100 }, { type: 'move', hits: 100 },
    { type: 'move', hits: 100 }, { type: 'move', hits: 100 }, { type: 'move', hits: 100 },
    { type: 'heal', hits: 100 },
  ],
  heal() {}, rangedAttack() {}, rangedMassAttack() {}, moveTo() {},
  move(d) { moved.push(d); },
};
Game.rooms.W47N7 = room;
Game.creeps.rdef1 = creep;

const remote = require(path.join(ROOT, 'src/managers/remote.js'));
assert.ok(remote.cfgFor('W47N7'), 'cfgFor returns GUARD W47N7');
assert.strictEqual(remote.CFG.W47N7, undefined, 'CFG has no W47N7 (regression trigger)');

const roles = require(path.join(ROOT, 'src/roles/remote.js'));
assert.doesNotThrow(() => roles.defender.run(creep), 'defender kite must not throw on GUARD remote');
assert.ok(moved.length >= 0, 'ran without throw');
console.log('defender_guard_kite ok');
