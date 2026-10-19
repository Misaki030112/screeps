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
// rhauler delivery: spawn energy OK + a local hauler alive -> no extension detour; adjacent top-up in passing, walk on to the sink
{
  Object.assign(global, { FIND_DROPPED_RESOURCES: 6, FIND_STRUCTURES: 5, LOOK_STRUCTURES: 'ls', STRUCTURE_CONTAINER: 'container', STRUCTURE_STORAGE: 'storage', FIND_MY_CONSTRUCTION_SITES: 1,
    RoomPosition: function (x, y, r) { return { x, y, roomName: r }; } });
  const adjE = ext(20, 33), farE = ext(36, 31), stor = { id: 'st', structureType: 'storage', pos: pos(35, 32), store: { energy: 0, getFreeCapacity: () => 1e6 } };
  const hauler = { memory: { role: 'w8hauler' } };
  const R = { name: 'W47N8', energyAvailable: 900, energyCapacityAvailable: 1300, storage: stor, controller: {},
    find: (t, o) => (t === 3 ? [hauler] : t === 10 ? [adjE, farE] : []).filter(o && o.filter || (() => true)), lookForAt: () => [] };
  Game.rooms.W47N8 = R; Memory.ops = {};
  const log = [];
  const c = { id: 'rh', name: 'rh', memory: { role: 'w8rhauler', w: true }, room: R, ticksToLive: 1000, store: { energy: 800, getFreeCapacity: () => 0, getCapacity: () => 800 },
    pos: Object.assign(pos(21, 33), { isNearTo: o => Math.max(Math.abs(21 - o.pos.x), Math.abs(33 - o.pos.y)) <= 1,
      findInRange: (t, r, o) => [adjE, farE].filter(s => Math.max(Math.abs(21 - s.pos.x), Math.abs(33 - s.pos.y)) <= r).filter(o.filter) }),
    transfer: (t) => log.push('tr ' + t.id), moveTo: (p) => log.push('mv ' + p.x + ',' + p.y) };
  RL.w8rhauler.run(c);
  assert.deepStrictEqual(log, ['tr ' + adjE.id, 'mv 35,32'], 'top-up adjacent ext, move on to storage: ' + log);
  R.energyAvailable = 200; log.length = 0; RL.w8rhauler.run(c);
  assert.ok(log[0].startsWith('tr ') || log[0] === 'mv 20,33' || log[0] === 'mv 36,31', 'low spawn energy -> fill duty: ' + log);
  console.log('w47n8 rhauler delivery ok');
}
// 17:20 miner 6W (+1 CARRY only once the source link exists) and RCL5 link transfer
{
  Object.assign(global, { STRUCTURE_LINK: 'link' });
  const cnt = (b, p) => b.filter(x => x === p).length;
  Game.rooms.W47N8 = { lookForAt: () => [] };
  let b = W.bodyFor('w8miner', 1300); assert.deepStrictEqual([cnt(b, 'work'), cnt(b, 'carry'), cnt(b, 'move')], [6, 0, 1], '6W1M without link');
  b = W.bodyFor('w8miner', 550); assert.strictEqual(cnt(b, 'work'), 5, '5W at 550');
  let sent = 0;
  const la = { structureType: 'link', cooldown: 0, store: { energy: 800, getFreeCapacity: () => 0 }, transferEnergy: () => { sent++; return 0; } };
  const lk = { structureType: 'link', store: { energy: 0, getFreeCapacity: () => 800 } };
  Game.rooms.W47N8 = { lookForAt: (k, x, y) => (x === 26 && y === 12 ? [la] : x === 13 && y === 25 ? [lk] : []) };
  b = W.bodyFor('w8miner', 1300); assert.deepStrictEqual([cnt(b, 'work'), cnt(b, 'carry')], [6, 1], '6W1C1M with link');
  W.linkRun(); assert.strictEqual(sent, 1, 'source link -> ctl link');
  la.cooldown = 3; W.linkRun(); assert.strictEqual(sent, 1, 'cooldown respected');
  console.log('w47n8 miner/link ok');
}
