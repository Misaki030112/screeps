// W47N8 tower + colony role wrapper honour Memory.cmd (docs/COMMANDER.md).
// Peacetime (no cmd) still focus-fires. node tests/commander_tower.js
const assert = require('assert'), path = require('path');
global._ = require('lodash');
Object.assign(global, {
  FIND_MY_STRUCTURES: 1, FIND_HOSTILE_CREEPS: 2, FIND_MY_CREEPS: 3, FIND_STRUCTURES: 4,
  STRUCTURE_TOWER: 'tower', STRUCTURE_WALL: 'constructedWall', STRUCTURE_RAMPART: 'rampart',
  STRUCTURE_LINK: 'link', RESOURCE_ENERGY: 'energy', MOVE: 'move', CARRY: 'carry', CLAIM: 'claim',
  ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack', WORK: 'work', HEAL: 'heal', TOUGH: 'tough',
  LOOK_STRUCTURES: 'structure', OK: 0,
  Memory: { creeps: {} }, Game: { time: 1, creeps: {}, rooms: {}, spawns: {}, cpu: { bucket: 10000 }, getObjectById: () => null },
});
const W = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'index.js'));
const cmd = require(path.join(__dirname, '..', 'src', 'utils', 'cmd.js'));
let H;
const P = (x, y) => ({
  x, y, roomName: 'W47N8',
  getRangeTo: o => Math.max(Math.abs(x - (o.pos || o).x), Math.abs(y - (o.pos || o).y)),
  inRangeTo(o, r) { return this.getRangeTo(o) <= r; },
  findInRange: (t, r) => t === 2 ? H.filter(h => Math.max(Math.abs(h.pos.x - x), Math.abs(h.pos.y - y)) <= r) : [],
});
const body = o => Object.entries(o).flatMap(([t, n]) => Array(n).fill({ type: t, hits: 100 }));
const hc = (id, x, y, b) => { const bd = body(b); return { id, pos: P(x, y), body: bd, hits: bd.length * 100, hitsMax: bd.length * 100 }; };
let shots = [];
const tw = {
  id: 'tw', structureType: 'tower', pos: P(33, 35), store: { energy: 690 },
  attack: x => shots.push(x.id), heal() {}, repair() {},
};
const tw2 = {
  id: 'tw2', structureType: 'tower', pos: P(24, 8), store: { energy: 690 },
  attack: x => shots.push('b:' + x.id), heal() {}, repair(x) { shots.push('rep:' + x.id); },
};
const room = {
  name: 'W47N8', memory: {}, controller: { level: 7 },
  find: (t, o) => { const a = t === 1 ? [tw, tw2] : t === 2 ? H : t === 3 ? [] : []; return o && o.filter ? a.filter(o.filter) : a; },
};
const go = h => { H = h; shots = []; W.towerRun(room); return shots.slice(); };

assert.deepStrictEqual(go([hc('a', 30, 20, { attack: 10, move: 10 })]), ['a', 'b:a'], 'both towers fire when no commander order');
assert.ok(room.memory.threat8 && room.memory.threat8.inBase, 'threat8 still published');

const ramp = { id: 'ramp', pos: P(29, 3) };
Game.getObjectById = id => (id === 'ramp' ? ramp : null);
cmd.setStruct('tw2', { act: 'repair', id: 'ramp', ttl: 10 });
Game.time = 2;
assert.deepStrictEqual(go([hc('a', 30, 20, { attack: 10, move: 10 })]), ['a', 'rep:ramp'], 'ordered tower repairs; the other keeps firing');
assert.ok(room.memory.threat8 && room.memory.threat8.id === 'a', 'assessment still runs while one tower is taken');

cmd.releaseStruct('tw2');
cmd.disarm();
Game.time = 3;
tw._cmdTick = -1; tw2._cmdTick = -1;
assert.deepStrictEqual(go([hc('a', 30, 20, { attack: 10, move: 10 })]), ['a', 'b:a'], 'disarm restores both towers');

// Colony military + civilian wrappers: act/duty beat the role body and leave w8recycle in place.
const roles = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'roles.js'));
Memory.ops = { w8recycle: ['Def1', 'Haul1'] };
Game.time = 4;
cmd.arm();
const said = [];
const def = {
  name: 'Def1', memory: { role: 'w8defender', home: 'W47N8' },
  say(s) { said.push(s); }, room: null, pos: P(10, 10),
};
cmd.setCreep('Def1', { act: 'idle', say: 'hold', ttl: 5 });
roles.w8defender.run(def);
assert.deepStrictEqual(said, ['hold']);
assert.deepStrictEqual(Memory.ops.w8recycle, ['Def1', 'Haul1']);

Game.time = 5;
global.FIND_MY_STRUCTURES = 1;
global.STRUCTURE_SPAWN = 'spawn';
global.STRUCTURE_EXTENSION = 'extension';
const spawn = { id: 'sp2', structureType: 'spawn', pos: P(30, 30), store: { getFreeCapacity: () => 100 } };
let hauled = null;
const haul = {
  name: 'Haul1', memory: { role: 'w8hauler', home: 'W47N8', w: true },
  store: { energy: 300 },
  pos: Object.assign(P(30, 31), { findClosestByRange: list => list[0] }),
  room: { name: 'W47N8', find: () => [spawn], storage: null },
  transfer(t, r) { hauled = [t.id, r]; return 0; },
  moveTo() { throw new Error('body ran'); },
};
cmd.setCreep('Haul1', { duty: 'fillSpawn', ttl: 5 });
roles.w8hauler.run(haul);
assert.deepStrictEqual(hauled, ['sp2', 'energy']);
assert.ok(Memory.ops.w8recycle.includes('Haul1'));

cmd.releaseCreep('Def1');
cmd.releaseCreep('Haul1');
assert.strictEqual(Memory.creeps.Def1, undefined);
console.log('commander tower ok');
