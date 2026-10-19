// 10-20 07:4x (2room eval): a due hub filler spawns before local defenders unless armed hostiles are inside the base
const assert = require('assert'), path = require('path');
Object.assign(global, { _: require('lodash'), FIND_MY_STRUCTURES: 10, FIND_MY_CONSTRUCTION_SITES: 1, FIND_MY_SPAWNS: 2, FIND_MY_CREEPS: 3, FIND_STRUCTURES: 5,
  FIND_DROPPED_RESOURCES: 6, FIND_HOSTILE_CREEPS: 4, STRUCTURE_EXTENSION: 'extension', STRUCTURE_SPAWN: 'spawn', STRUCTURE_TOWER: 'tower', STRUCTURE_ROAD: 'road',
  STRUCTURE_RAMPART: 'rampart', STRUCTURE_CONTAINER: 'container', STRUCTURE_STORAGE: 'storage', STRUCTURE_WALL: 'constructedWall', RESOURCE_ENERGY: 'energy',
  LOOK_STRUCTURES: 'ls', LOOK_CONSTRUCTION_SITES: 'lc', OK: 0, WORK: 'work', CARRY: 'carry', MOVE: 'move', ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack',
  HEAL: 'heal', TOUGH: 'tough', CLAIM: 'claim',
  BODYPART_COST: { work: 100, carry: 50, move: 50, attack: 80, ranged_attack: 150, heal: 250, tough: 10, claim: 600 },
  Memory: { ops: {} }, Game: { time: 5000, rooms: {}, creeps: {} } });
const src = p => path.join(__dirname, '..', 'src', 'rooms', 'w47n8', p);
const FL = require(src('fill.js')), FM = require(src('fillmeter.js'));
FM.tick = () => {}; FM.spent = () => {}; FM.wait = () => {}; FM.idle = () => {};
FL.body = () => ['carry', 'carry', 'move'];
const W = require(src('index.js'));
const room = { name: 'W47N8', energyAvailable: 1300, energyCapacityAvailable: 1300, controller: { level: 4, my: true, ticksToDowngrade: 40000 },
  storage: { store: { energy: 800 } }, memory: {}, find: () => [], lookForAt: () => [] };
Game.rooms.W47N8 = room;
function run({ fillerDue, inBase }) {
  FL.want = () => fillerDue;
  Memory.ops.w8roster = { t: Game.time, w8: 2, home: 1 };
  room.memory.threat8 = inBase ? { inBase: true, t: Game.time } : undefined;
  let role = null;
  const spawn = { room, pos: { x: 15, y: 18, getRangeTo: () => 10 }, spawning: null,
    spawnCreep: (b, name, o) => { role = o.memory.role; return 0; } };
  W.spawnRun(spawn); return role;
}
assert.strictEqual(run({ fillerDue: true, inBase: false }), 'w8filler', 'due filler before local defenders (threat outside the room)');
assert.strictEqual(run({ fillerDue: true, inBase: true }), 'w8defender', 'armed hostiles inside the base: defender first');
assert.strictEqual(run({ fillerDue: false, inBase: false }), 'w8defender', 'no filler due: defender as before');
console.log('w47n8 filler-first ok');
