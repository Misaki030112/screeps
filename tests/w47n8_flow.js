// 15:10 W47N8 flow fixes: 2C:1M local hauler body, rhauler extension fill limited to range 3 (fillTarget rng)
const assert = require('assert'), path = require('path');
Object.assign(global, { _: require('lodash'), FIND_MY_STRUCTURES: 10, FIND_MY_CREEPS: 3, STRUCTURE_EXTENSION: 'extension', STRUCTURE_SPAWN: 'spawn', STRUCTURE_TOWER: 'tower',
  RESOURCE_ENERGY: 'energy', WORK: 'work', CARRY: 'carry', MOVE: 'move', ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack', HEAL: 'heal', TOUGH: 'tough', CLAIM: 'claim',
  Memory: { ops: {} }, Game: { time: 1, rooms: {}, creeps: {} } });
const W = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'index.js'));
const RL = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'roles.js'));
const cnt = (b, p) => b.filter(x => x === p).length;
let b = W.bodyFor('w8hauler', 1300); assert.deepStrictEqual([cnt(b, 'carry'), cnt(b, 'move')], [10, 5], '10C5M at 1300');
b = W.bodyFor('w8hauler', 300); assert.strictEqual(cnt(b, 'carry'), cnt(b, 'move'), '1:1 below 450');
const pos = (x, y) => ({ x, y, inRangeTo: (o, r) => Math.max(Math.abs(x - o.pos.x), Math.abs(y - o.pos.y)) <= r,
  findClosestByRange: a => (a.length ? _.min(a, o => Math.max(Math.abs(x - o.pos.x), Math.abs(y - o.pos.y))) : null) });
const ext = (x, y) => ({ id: 'e' + x + y, structureType: 'extension', pos: pos(x, y), store: { getFreeCapacity: () => 50 } });
const far = ext(36, 31), near = ext(15, 30);
const room = { find: (t, o) => (t === 3 ? [] : [far, near]).filter(o && o.filter || (() => true)) };
const c = { id: 'r', memory: {}, room, pos: pos(13, 26) };
assert.strictEqual(RL._fill(c, false, 3), null, 'no extension within 3 -> none');
c.pos = pos(14, 29); assert.strictEqual(RL._fill(c, false, 3), near, 'on-the-way extension within 3'); c.memory = {};
c.pos = pos(13, 26); assert.ok(RL._fill(c, false), 'default range unlimited');
console.log('w47n8 flow ok');
