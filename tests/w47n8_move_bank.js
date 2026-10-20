// 10-20 14:4x strategy review: spawn-move bank (w8move prep) - idle builders park instead of upgrading from storage, and a fresh
// builder (moveReady 'ttl' needs TTL >= 700) is queued once storage is within 3k of MOVE_E even with 0 sites and walls at the cap
const assert = require('assert'), path = require('path');
Object.assign(global, { _: require('lodash'), FIND_MY_STRUCTURES: 10, FIND_MY_CONSTRUCTION_SITES: 1, FIND_MY_SPAWNS: 2, FIND_MY_CREEPS: 3, FIND_STRUCTURES: 5,
  FIND_HOSTILE_CREEPS: 4, FIND_DROPPED_RESOURCES: 6, FIND_SOURCES_ACTIVE: 7, FIND_SOURCES: 8, FIND_HOSTILE_STRUCTURES: 9,
  STRUCTURE_EXTENSION: 'extension', STRUCTURE_SPAWN: 'spawn', STRUCTURE_TOWER: 'tower', STRUCTURE_ROAD: 'road', STRUCTURE_RAMPART: 'rampart', STRUCTURE_CONTAINER: 'container',
  STRUCTURE_STORAGE: 'storage', STRUCTURE_WALL: 'constructedWall', STRUCTURE_LINK: 'link', RESOURCE_ENERGY: 'energy', LOOK_STRUCTURES: 'ls', LOOK_CONSTRUCTION_SITES: 'lc', OK: 0,
  ERR_RCL_NOT_ENOUGH: -14, TERRAIN_MASK_WALL: 1, BODYPART_COST: { work: 100, carry: 50, move: 50, attack: 80, ranged_attack: 150, heal: 250, tough: 10, claim: 600 },
  WORK: 'work', CARRY: 'carry', MOVE: 'move', ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack', HEAL: 'heal', TOUGH: 'tough', CLAIM: 'claim',
  Memory: { ops: { w8layout: 'approved' } }, Game: { time: 1000, rooms: {}, creeps: {}, spawns: {}, cpu: { getUsed: () => 0 } } });
const W = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'index.js'));
const RL = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'roles.js'));
const C = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'config.js'));
const pos = (x, y) => ({ x, y, roomName: 'W47N8', getRangeTo: (o, oy) => (typeof o === 'number' ? Math.max(Math.abs(x - o), Math.abs(y - oy)) : Math.max(Math.abs(x - (o.pos || o).x), Math.abs(y - (o.pos || o).y))),
  inRangeTo: (o, r, r2) => (typeof o === 'number' ? Math.max(Math.abs(x - o), Math.abs(y - r)) <= r2 : Math.max(Math.abs(x - (o.pos || o).x), Math.abs(y - (o.pos || o).y)) <= r),
  isNearTo: o => Math.max(Math.abs(x - (o.pos || o).x), Math.abs(y - (o.pos || o).y)) <= 1, findClosestByRange: () => null, lookFor: () => [] });
// (1) spawn: prep + storage 13.5k, only old builders -> w8builder; with a fresh builder alive -> not a builder
const out = [];
const room = { name: 'W47N8', energyAvailable: 1800, energyCapacityAvailable: 1800, memory: {}, controller: { level: 5, my: true, ticksToDowngrade: 80000, progress: 0, progressTotal: 1 },
  storage: { store: { energy: 13500 }, pos: pos(35, 32) }, find: () => [], lookForAt: () => [], getTerrain: () => ({ get: () => 0 }), visual: { text() {} } };
Game.rooms.W47N8 = room;
const spawn = { name: 'Spawn2', room, pos: pos(15, 18), spawning: null, store: { energy: 300 },
  spawnCreep: (body, name, o) => { out.push(o && o.memory && o.memory.role); return 0; } };
Game.spawns.Spawn2 = spawn;
const cr = (role, ttl, extra) => { const n = role + ttl; Game.creeps[n] = Object.assign({ name: n, memory: { role, home: 'W47N8', si: 0 }, ticksToLive: ttl, body: [{ type: 'work' }, { type: 'carry' }, { type: 'move' }], getActiveBodyparts: () => 6, pos: pos(20, 20), room }, extra); return Game.creeps[n]; };
cr('w8miner', 1400); Game.creeps.w8miner1399 = Object.assign({}, Game.creeps.w8miner1400, { name: 'w8miner1399', memory: { role: 'w8miner', home: 'W47N8', si: 1 } });
cr('w8hauler', 1000); cr('w8hauler', 1001); cr('w8hauler', 1002); cr('w8filler', 1200); cr('w8upgrader', 1300); cr('w8builder', 650);
Memory.ops.w8move = { phase: 'prep' };
const run = () => { out.length = 0; try { W.spawnRun(spawn); } catch (e) { out.push('ERR ' + e.message); } return out[0]; };
const a = run(); assert.strictEqual(a, 'w8builder', 'prep near MOVE_E, builder TTL 650 -> fresh builder queued, got ' + a);
room.storage.store.energy = 4000; const b = run(); assert.notStrictEqual(b, 'w8builder', 'bank far from MOVE_E -> no builder yet');
room.storage.store.energy = 13500; cr('w8builder', 1450); const c2 = run(); assert.notStrictEqual(c2, 'w8builder', 'fresh builder alive -> no extra');
Memory.ops.w8move.phase = 'done'; delete Game.creeps.w8builder1450; const d = run(); assert.notStrictEqual(d, 'w8builder', 'not banking -> rule off');
// (2) builder with nothing to build/repair: parks during prep (no upgrade, no storage withdraw); upgrades again once the move is done
Memory.ops.w8move.phase = 'prep'; const acts = [];
const bc = cr('w8builder', 1200, { id: 'b1', memory: { role: 'w8builder', home: 'W47N8', w: true }, store: Object.assign({ energy: 300 }, { getFreeCapacity: () => 0, getCapacity: () => 300 }),
  pos: Object.assign(pos(C.UPG_EXTRA[0][0], C.UPG_EXTRA[0][1]), { findClosestByRange: () => null }), fatigue: 0, owner: { username: 'Misaki030112' },
  upgradeController: () => acts.push('upgrade'), withdraw: () => acts.push('withdraw'), repair: () => acts.push('repair'), build: () => acts.push('build'), move: () => acts.push('move'), moveTo: () => acts.push('moveTo'), say() {} });
room.controller.pos = pos(C.UPG_EXTRA[0][0] + 1, C.UPG_EXTRA[0][1]); room.controller.sign = { username: 'Misaki030112', text: require(path.join(__dirname, '..', 'src', 'utils', 'sign.js')).SIGN };
RL.w8builder.run(bc); assert.ok(!acts.includes('upgrade') && !acts.includes('withdraw'), 'prep: idle builder parks, acts ' + acts);
Memory.ops.w8move.phase = 'done'; acts.length = 0; RL.w8builder.run(bc); assert.ok(acts.includes('upgrade'), 'after move: fallback upgrade again, acts ' + acts);
console.log('w47n8 move bank ok');
