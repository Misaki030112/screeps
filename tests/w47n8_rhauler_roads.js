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
console.log('w47n8 rhauler roads ok');
