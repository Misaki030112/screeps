// Home roles, raid9 conflict order, squad helpers, observer/nuker/factory.
// node tests/commander_roles.js
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
global._ = require('lodash');
Object.assign(global, {
  OK: 0, ERR_NOT_IN_RANGE: -9, RESOURCE_ENERGY: 'energy', HEAL: 'heal', ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack',
  WORK: 'work', MOVE: 'move', CARRY: 'carry', CLAIM: 'claim', TOUGH: 'tough',
  STRUCTURE_SPAWN: 'spawn', STRUCTURE_EXTENSION: 'extension', STRUCTURE_TOWER: 'tower', STRUCTURE_LINK: 'link',
  STRUCTURE_CONTAINER: 'container', STRUCTURE_STORAGE: 'storage', STRUCTURE_ROAD: 'road', STRUCTURE_RAMPART: 'rampart',
  STRUCTURE_LAB: 'lab', STRUCTURE_TERMINAL: 'terminal', STRUCTURE_EXTRACTOR: 'extractor', STRUCTURE_WALL: 'constructedWall',
  FIND_MY_SPAWNS: 1, FIND_MY_CREEPS: 2, FIND_HOSTILE_CREEPS: 3, FIND_STRUCTURES: 4, FIND_MY_STRUCTURES: 5,
  FIND_SOURCES: 6, FIND_DROPPED_RESOURCES: 7, FIND_CONSTRUCTION_SITES: 8, FIND_MINERALS: 9,
  LOOK_STRUCTURES: 'structure', LOOK_CREEPS: 'creep', LOOK_SOURCES: 'source', LOOK_CONSTRUCTION_SITES: 'constructionSite',
  TOP: 1, BOTTOM: 5, LEFT: 7, RIGHT: 3,
});
const W = { objs: {} };
global.Game = {
  time: 7000, cpu: { bucket: 9000 }, creeps: {}, rooms: {}, spawns: {},
  getObjectById: id => W.objs[id] || null,
};
global.Memory = { creeps: {}, ops: {} };
const cmd = require(src('utils/cmd.js'));
let n = 0;
const it = (name, fn) => { try { fn(); n++; } catch (e) { console.error('FAIL', name); console.error(e); throw e; } };
function pos(x, y) {
  return {
    x, y, roomName: 'W47N8',
    getRangeTo(p) { const t = p.pos || p; return Math.max(Math.abs(this.x - t.x), Math.abs(this.y - t.y)); },
    isNearTo(p) { return this.getRangeTo(p) <= 1; },
  };
}
function creep(name, extra) {
  const c = {
    name, hits: 500, hitsMax: 500, said: [], moved: null,
    memory: { role: 'miner', v2: 1 },
    store: { energy: 0, getFreeCapacity: () => 50, getCapacity: () => 50 },
    room: { name: 'W46N8', memory: {}, controller: { my: true }, energyAvailable: 100, energyCapacityAvailable: 100 },
    say(s) { this.said.push(s); },
    moveTo(p) { this.moved = { x: p.x, y: p.y }; },
    getActiveBodyparts() { return 0; },
    harvest() { throw new Error('harvest ' + name); },
    upgradeController() { throw new Error('upgrade ' + name); },
    build() { throw new Error('build ' + name); },
    attackController() { throw new Error('attackController ' + name); },
    reserveController() { throw new Error('reserve ' + name); },
  };
  c.pos = pos(5, 5);
  return Object.assign(c, extra || {});
}
function idle(name, role) {
  const c = creep(name);
  c.memory.role = role;
  Memory.creeps[name] = c.memory;
  cmd.setCreep(name, { act: 'idle', say: role, ttl: 10 });
  return c;
}

it('setMany and setSquad do not touch raidOrder or ops', () => {
  Game.time = 7100;
  Memory.ops = { w47n9: { on: true }, w8day: { softCap2: 1 } };
  const raidOrder = { hold: 1, moveTo: [10, 10] };
  Game.creeps = {
    A: { name: 'A', memory: { role: 'raid9', kind: 'h', home: 'W47N8', raidOrder }, room: { name: 'W47N8' } },
    B: { name: 'B', memory: { role: 'raid9', kind: 'd', home: 'W47N8', raidOrder: { hold: 1 } }, room: { name: 'W47N8' } },
    C: { name: 'C', memory: { role: 'hauler', home: 'W46N8' }, room: { name: 'W46N8' } },
  };
  assert.deepStrictEqual(cmd.setSquad({}, { duty: 'hold' }), []);
  assert.deepStrictEqual(cmd.setSquad({ role: 'raid9', kind: 'h' }, { duty: 'hold', pos: { room: 'W47N8', x: 1, y: 2 }, ttl: 30 }), ['A']);
  assert.strictEqual(Memory.cmd.c.B, undefined);
  assert.strictEqual(Memory.cmd.c.C, undefined);
  assert.strictEqual(Game.creeps.A.memory.raidOrder, raidOrder);
  assert.strictEqual(Memory.ops.w47n9.on, true);
  assert.strictEqual(Memory.ops.w8day.softCap2, 1);
  const many = cmd.setMany(['A', 'B'], { act: 'idle', ttl: 12, say: 'sq' });
  assert.deepStrictEqual(many, ['A', 'B']);
  assert.strictEqual(Memory.cmd.c.A.act, 'idle');
  assert.strictEqual(Memory.cmd.c.B.say, 'sq');
  assert.strictEqual(Game.creeps.A.memory.raidOrder.hold, 1);
  assert.strictEqual(cmd.releaseMany(['A', 'B']), 2);
  assert.strictEqual(Memory.cmd.c.A, undefined);
  assert.strictEqual(Game.creeps.A.memory.raidOrder.moveTo[0], 10);
});

it('raid9: duty beats raidOrder, forceGo still applies, release resumes raidOrder', () => {
  Game.time = 7200;
  global._ = require('lodash');
  const raid = require(src('roles/raid9.js'));
  Memory.ops = { w47n9: { on: true, phase: 'fallback', forceGo: 1, flee: 1, garrison: 1 } };
  const order = { hold: 1, moveTo: [10, 10] };
  const c = creep('R9');
  c.memory = { role: 'raid9', kind: 'm', home: 'W47N8', raidOrder: order, v2: 1 };
  Memory.creeps.R9 = c.memory;
  c.room.name = 'W47N8';
  cmd.setCreep('R9', { duty: 'hold', pos: { room: 'W47N8', x: 12, y: 12 }, ttl: 20 });
  raid.run(c);
  assert.strictEqual(c.moved.x, 12);
  assert.strictEqual(c.memory.raidOrder, order);
  assert.strictEqual(Memory.ops.w47n9.forceGo, undefined);
  assert.strictEqual(Memory.ops.w47n9.flee, undefined);
  assert.strictEqual(Memory.ops.w47n9.phase, 'breach');
  cmd.releaseCreep('R9');
  Game.time++;
  c.moved = null;
  c._dutyWhy = null; c._dutyTick = -1; c._cmdTick = -1;
  raid.run(c);
  assert.strictEqual(c.moved, null, 'raidOrder.hold resumes and does not walk moveTo');
  assert.strictEqual(c.memory.raidOrder, order);
});

it('home and remote roles yield before their body', () => {
  Game.time = 7300;
  const miner = require(src('roles/miner.js'));
  const upgrader = require(src('roles/upgrader.js'));
  const builder = require(src('roles/builder.js'));
  const queen = require(src('roles/queen.js'));
  const filler = require(src('roles/filler.js'));
  const manager = require(src('roles/manager.js'));
  const mminer = require(src('roles/mminer.js'));
  const harvester = require(src('roles/harvester.js'));
  const reserve7 = require(src('roles/reserve7.js'));
  const remote = require(src('roles/remote.js'));
  const runs = [
    ['miner', miner], ['upgrader', upgrader], ['builder', builder], ['queen', queen],
    ['filler', filler], ['manager', manager], ['mminer', mminer], ['harvester', harvester],
    ['reserve7', reserve7],
    ['rhauler', remote.rhauler], ['rminer', remote.rminer], ['reserver', remote.reserver], ['defender', remote.defender],
  ];
  for (const [role, mod] of runs) {
    Game.time++;
    const c = idle(role + '1', role);
    if (role === 'queen') c.room.memory = {};
    (mod.run || mod)(c);
    assert.deepStrictEqual(c.said, [role], role);
    if (role === 'queen') assert.strictEqual(c.room.memory.queenAlive, Game.time);
  }
});

it('observer observes, nuker waits without allow, factory calls nothing', () => {
  Game.time = 7400;
  let seen = null, launched = null, produced = 0;
  const obs = { id: 'ob', structureType: 'observer', observe(rn) { seen = rn; return 0; } };
  const nk = { id: 'nk', structureType: 'nuker', launchNuke(p) { launched = p; return 0; } };
  const fac = { id: 'fac', structureType: 'factory', produce() { produced++; return 0; } };
  W.objs.ob = obs; W.objs.nk = nk; W.objs.fac = fac;
  cmd.setStruct('ob', { act: 'observe', room: 'W48N9', ttl: 5 });
  cmd.setStruct('nk', { act: 'launch', pos: { room: 'W47N9', x: 25, y: 25 }, ttl: 5 });
  cmd.setStruct('fac', { act: 'produce', ttl: 5 });
  cmd.runHeldStructures();
  assert.strictEqual(seen, 'W48N9');
  assert.strictEqual(launched, null);
  assert.strictEqual(produced, 0);
  cmd.setStruct('nk', { act: 'launch', allow: 1, pos: { room: 'W47N9', x: 25, y: 25 }, once: 1, ttl: 5 });
  Game.time++;
  cmd.runHeldStructures();
  assert.strictEqual(launched.x, 25);
  assert.strictEqual(launched.roomName, 'W47N9');
  assert.strictEqual(Memory.cmd.s.nk, undefined);
  cmd.disarm();
  assert.strictEqual(cmd.yieldCreep(creep('Z')), false);
});

console.log('commander roles ok', n);
