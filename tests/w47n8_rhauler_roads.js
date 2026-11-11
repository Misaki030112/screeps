// 10-20: W47N7 rhauler legs go through utils/move (road matrix, creeps not walls) via exit 18,0 <-> 18,49, not native moveTo
const assert = require('assert'), path = require('path');
Object.assign(global, { _: require('lodash'), TOP: 1, RIGHT: 3, BOTTOM: 5, LEFT: 7, WORK: 'work', CARRY: 'carry', MOVE: 'move', ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack',
  HEAL: 'heal', TOUGH: 'tough', CLAIM: 'claim', RESOURCE_ENERGY: 'energy', Memory: { ops: {} }, Game: { time: 1, rooms: {}, creeps: {} },
  RoomPosition: function (x, y, r) { Object.assign(this, { x, y, roomName: r }); } });
const RL = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'roles.js'));
const MV = require(path.join(__dirname, '..', 'src', 'utils', 'move.js'));
let calls = []; MV.to = (c, x, y, r) => { calls.push(['to', x, y, r]); return false; };
const cr = (room, x, y) => ({ room: { name: room }, pos: { x, y }, memory: {}, move: d => calls.push(['move', d]), moveTo: () => calls.push(['native']) });
const rm = RL._rmove;
calls = []; rm(cr('W47N7', 25, 20), 'W47N8', 15, 18, 1); assert.deepStrictEqual(calls, [['to', 18, 0, 0]], 'W47N7 -> W47N8 via 18,0');
calls = []; rm(cr('W47N8', 15, 30), 'W47N7', 31, 34, 1); assert.deepStrictEqual(calls, [['to', 18, 49, 0]], 'W47N8 -> W47N7 via 18,49');
calls = []; rm(cr('W47N7', 25, 20), 'W47N7', 31, 34, 1); assert.deepStrictEqual(calls, [['to', 31, 34, 1]], 'in-room move.to');
calls = []; rm(cr('W47N7', 18, 0), 'W47N7', 31, 34, 1); assert.deepStrictEqual(calls, [['move', 5]], 'just crossed: step in');
calls = []; rm(cr('W47N6', 25, 25), 'W47N7', 31, 34, 1); assert.deepStrictEqual(calls, [['native']], 'other rooms: native');
// 10-21: W46N8 -> W47N8 (home-sent joint defenders) via move.to to the fixed west exit 0,23, not native cross-room moveTo
const hm = RL._home;
calls = []; assert.strictEqual(hm(cr('W46N8', 35, 29)), false); assert.deepStrictEqual(calls, [['to', 0, 23, 0]], 'W46N8 -> W47N8 via 0,23');
calls = []; assert.strictEqual(hm(cr('W47N8', 49, 23)), true); assert.deepStrictEqual(calls, [], 'in W47N8: role runs');
calls = []; hm(cr('W45N8', 10, 10)); assert.deepStrictEqual(calls, [['native']], 'other rooms: native');
// 11-11 20:2x: rmove / fleeHome must step off the N exit, not native moveTo (w8rhauler84205404 164t bounce)
calls = []; rm(cr('W47N8', 18, 49), 'W47N8', 15, 18, 4); assert.deepStrictEqual(calls, [['move', 1]], 'W47N8 18,49 -> spawn: step in north');
calls = []; rm(cr('W47N7', 18, 0), 'W47N8', 15, 18, 4); assert.deepStrictEqual(calls, [['move', 1]], 'W47N7 18,0 -> W47N8: cross north');
const fh = RL._fleeHome;
const cr2 = (room, x, y, extra) => Object.assign(cr(room, x, y), { pos: { x, y, inRangeTo: (px, py, r) => Math.max(Math.abs(x - px), Math.abs(y - py)) <= r } }, extra || {});
calls = []; fh(cr2('W47N8', 18, 49)); assert.deepStrictEqual(calls, [['move', 1]], 'fleeHome on home exit: step in, not moveTo');
calls = []; fh(cr2('W47N7', 18, 0)); assert.deepStrictEqual(calls, [['move', 1]], 'fleeHome on remote exit: cross, not moveTo');
calls = []; fh(cr2('W47N7', 25, 20)); assert.deepStrictEqual(calls, [['to', 18, 0, 0]], 'fleeHome in W47N7: walk to 18,0');
calls = []; fh(cr2('W47N8', 15, 20)); assert.deepStrictEqual(calls, [], 'fleeHome already by spawn: hold');
calls = []; fh(cr2('W47N8', 30, 30)); assert.deepStrictEqual(calls, [['to', 15, 18, 4]], 'fleeHome inside W47N8 off-exit: walk to spawn');
calls = []; fh(cr2('W45N8', 10, 10)); assert.deepStrictEqual(calls, [['native']], 'fleeHome other rooms: native');
console.log('w47n8 rhauler roads ok');
// miners on their stand are stationary (never swapped); off-stand or other roles are not
const st = MV._stationary, C = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'config.js'));
const mk = (role, x, y, rn) => ({ memory: { role }, pos: { x, y }, room: { name: rn } });
assert.ok(st(mk('w8rminer', C.REMOTE.sources[0].stand[0], C.REMOTE.sources[0].stand[1], 'W47N7')), 'rminer on stand');
assert.ok(st(mk('w8miner', C.SOURCES[1].stand[0], C.SOURCES[1].stand[1], 'W47N8')), 'miner on stand');
assert.ok(!st(mk('w8rminer', 25, 25, 'W47N7')), 'rminer walking');
assert.ok(!st(mk('w8rhauler', C.REMOTE.sources[0].stand[0], C.REMOTE.sources[0].stand[1], 'W47N7')), 'hauler');
console.log('w47n8 stationary miners ok');
