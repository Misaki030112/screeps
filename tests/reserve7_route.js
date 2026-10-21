// 10-21: reserver must walk fixed exits via move.to (old: native moveTo, creeps = walls -> north detour from Spawn2)
const assert = require('assert'), path = require('path'), Module = require('module');
Object.assign(global, { _: require('lodash'), CLAIM: 'claim', MOVE: 'move', TOP: 1, RIGHT: 3, BOTTOM: 5, LEFT: 7, Memory: { ops: {} }, Game: { time: 1, rooms: {}, creeps: {} } });
global.RoomPosition = function (x, y, r) { this.x = x; this.y = y; this.roomName = r; };
const calls = []; const mv = path.join(__dirname, '..', 'src', 'utils', 'move.js');
require.cache[mv] = { id: mv, filename: mv, loaded: true, exports: { to: (c, x, y, r) => { calls.push([c.room.name, x, y, r]); return false; } } };
const R = require(path.join(__dirname, '..', 'src', 'roles', 'reserve7.js'));
const mk = (room, x, y) => { const c = { room: { name: room }, pos: { x, y, isNearTo: () => false }, memory: {}, moved: null };
  c.moveTo = () => { c.native = true; }; c.move = d => { c.moved = d; }; return c; };
let c = mk('W47N8', 34, 31); R.run(c); assert.ok(!c.native, 'no native moveTo in W47N8'); assert.deepStrictEqual(calls.pop(), ['W47N8', 27, 49, 0], 'W47N8 -> south exit 27,49');
c = mk('W47N8', 27, 49); R.run(c); assert.strictEqual(c.moved, 5, 'cross at the exit');
c = mk('W46N8', 30, 20); R.run(c); assert.deepStrictEqual(calls.pop(), ['W46N8', 0, 23, 0], 'home -> west exit');
c = mk('W47N7', 27, 0); R.run(c); assert.strictEqual(c.moved, 5, 'step off border');
c = mk('W47N7', 27, 1); R.run(c); assert.deepStrictEqual(calls.pop(), ['W47N7', 38, 26, 1]);
console.log('reserve7_route ok');
