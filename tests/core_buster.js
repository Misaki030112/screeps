// Melee invader-core buster: body, spawn flag, and role (attack the core only).
// node tests/core_buster.js
const path = require('path'), assert = require('assert');
const ROOT = path.join(__dirname, '..');
const _ = {
  filter: (a, f) => Object.values(a || {}).filter(f),
  some: (a, f) => Object.values(a || {}).some(f),
  sum: (a, f) => Object.values(a || {}).reduce((s, x) => s + (f ? f(x) : x), 0),
  countBy: (a, f) => { const o = {}; for (const x of Object.values(a || {})) { const k = f(x); o[k] = (o[k] || 0) + 1; } return o; },
};
const DXY = { 1: [0, -1], 2: [1, -1], 3: [1, 0], 4: [1, 1], 5: [0, 1], 6: [-1, 1], 7: [-1, 0], 8: [-1, -1] };
Object.assign(global, {
  _, TOP: 1, TOP_RIGHT: 2, RIGHT: 3, BOTTOM_RIGHT: 4, BOTTOM: 5, BOTTOM_LEFT: 6, LEFT: 7, TOP_LEFT: 8,
  ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack', HEAL: 'heal', MOVE: 'move', WORK: 'work', CARRY: 'carry', TOUGH: 'tough', CLAIM: 'claim',
  FIND_HOSTILE_CREEPS: 4, FIND_HOSTILE_STRUCTURES: 9, FIND_MY_SPAWNS: 2, FIND_CREEPS: 3, FIND_STRUCTURES: 5,
  FIND_CONSTRUCTION_SITES: 6, FIND_HOSTILE_CONSTRUCTION_SITES: 7, FIND_MY_CONSTRUCTION_SITES: 8,
  STRUCTURE_ROAD: 'road', STRUCTURE_CONTAINER: 'container', STRUCTURE_RAMPART: 'rampart', STRUCTURE_INVADER_CORE: 'invaderCore',
  RESOURCE_ENERGY: 'energy', LOOK_CREEPS: 'lc', LOOK_STRUCTURES: 'ls',
  TERRAIN_MASK_WALL: 1, TERRAIN_MASK_SWAMP: 2, OK: 0, ERR_BUSY: -4, ERR_NOT_ENOUGH_ENERGY: -6,
  BODYPART_COST: { attack: 80, move: 50, ranged_attack: 150, heal: 250, work: 100, carry: 50, tough: 10, claim: 600 },
  RoomPosition: function (x, y, roomName) { this.x = x; this.y = y; this.roomName = roomName; },
});
global.PathFinder = {
  CostMatrix: class { constructor() { this.d = {}; } get(x, y) { return this.d[x + ',' + y] || 0; } set(x, y, v) { this.d[x + ',' + y] = v; } clone() { const c = new PathFinder.CostMatrix(); Object.assign(c.d, this.d); return c; } },
  search: () => ({ path: [], incomplete: true, cost: Infinity }),
};
const R = require(path.join(ROOT, 'src/roles/remote.js'));
const S = require(path.join(ROOT, 'src/managers/spawn.js'));
const T = require(path.join(ROOT, 'src/managers/threat.js'));

const body = S.B.coreBuster(1300);
const nA = body.filter(p => p === ATTACK).length, nM = body.filter(p => p === MOVE).length;
assert.strictEqual(nA, 10, '10 ATTACK');
assert.strictEqual(nM, 10, '10 MOVE');
assert.strictEqual(nA * 80 + nM * 50, 1300);
assert.strictEqual(Math.ceil(100000 / (nA * 30)), 334, '100k core at 300 dps');
assert.ok(!body.includes(RANGED_ATTACK) && !body.includes(HEAL), 'buster is melee only');

assert.strictEqual(R.coreAct({ room: 'W45N7', remote: 'W45N7', fighting: true, edge: false, hasCore: true, range: 1 }), 'attack');
assert.strictEqual(R.coreAct({ room: 'W45N7', remote: 'W45N7', fighting: true, edge: false, hasCore: true, range: 4 }), 'approach');
assert.strictEqual(R.coreAct({ room: 'W46N8', remote: 'W45N7', fighting: true, edge: false, hasCore: false, range: 99 }), 'travel');
assert.strictEqual(R.coreAct({ room: 'W45N7', remote: 'W45N7', fighting: false, edge: false, hasCore: true, range: 1 }), 'recycle');
assert.strictEqual(R.coreAct({ room: 'W47N9', remote: 'W45N7', fighting: true, edge: false, hasCore: true, range: 1 }), 'leave');
assert.strictEqual(R.coreAct({ room: 'W47N8', remote: 'W47N9', fighting: true, edge: false, hasCore: true, range: 1 }), 'leave');

const core = { id: 'core1', structureType: 'invaderCore', hits: 100000, pos: { x: 9, y: 42 } };
const player = { id: 'p1', owner: { username: 'BustJetter' }, body: [{ type: 'attack', hits: 100 }] };
const attacked = [], moved = [];
function creepAt(x, y, roomName) {
  const c = {
    name: 'bust1', owner: { username: 'Misaki' }, hits: 1000, hitsMax: 1000, ticksToLive: 1400, fatigue: 0,
    room: {
      name: roomName,
      getTerrain: () => ({ get: () => 0 }),
      find: t => t === FIND_HOSTILE_STRUCTURES && roomName === 'W45N7' ? [core] : [],
      lookForAt: () => [],
    },
    memory: { role: 'defender', remote: 'W45N7', home: 'W46N8', core: 1 },
    body: body.map(type => ({ type, hits: 100 })),
    pos: {
      x, y, roomName,
      getRangeTo(t) { const p = t.pos || t; return Math.max(Math.abs(x - p.x), Math.abs(y - p.y)); },
      inRangeTo(a, b, r) {
        if (typeof a === 'object') return Math.max(Math.abs(x - a.x), Math.abs(y - a.y)) <= (b > 8 ? b : r || b);
        return Math.max(Math.abs(x - a), Math.abs(y - b)) <= r;
      },
      isNearTo(o) { const p = o.pos || o; return Math.max(Math.abs(x - p.x), Math.abs(y - p.y)) <= 1; },
      getDirectionTo(tx, ty) {
        if (typeof tx === 'object') { ty = tx.y; tx = tx.x; }
        const dx = Math.sign(tx - x), dy = Math.sign(ty - y);
        return +Object.keys(DXY).find(k => DXY[k][0] === dx && DXY[k][1] === dy);
      },
      findClosestByRange: () => Game.spawns.Spawn1,
    },
    attack(t) { attacked.push(t); },
    rangedAttack() { throw new Error('buster must not rangedAttack'); },
    rangedMassAttack() { throw new Error('buster must not rangedMassAttack'); },
    move(d) { moved.push(d); },
    moveTo() { moved.push('moveTo'); },
    heal() { throw new Error('buster has no heal'); },
  };
  return c;
}
global.Memory = { username: 'Misaki', remote: { W45N7: { th: { st: 'DEFEND', def: 'bust1', mission: 'core', why: 'dispatched', corePos: [9, 42] } } }, defense: { remotePatrol: true }, ops: {}, creeps: {} };
global.Game = { time: 5000, cpu: { bucket: 10000 }, creeps: { player }, rooms: {}, spawns: { Spawn1: { pos: { x: 35, y: 28 }, recycleCreep(c) { c.memory.recycled = 1; } } } };

let c = creepAt(10, 42, 'W45N7');
Game.rooms.W45N7 = c.room; Game.creeps.bust1 = c;
R.defender.run(c);
assert.deepStrictEqual(attacked, [core], 'adjacent: attack the core, not the player creep');
assert.strictEqual(moved.length, 0, 'already adjacent: no step');

attacked.length = 0; moved.length = 0;
c = creepAt(9, 40, 'W45N7');
Game.rooms.W45N7 = c.room; Game.creeps.bust1 = c;
R.defender.run(c);
assert.strictEqual(attacked.length, 0, 'out of range: do not attack');
assert.ok(moved.length === 1, 'approach takes one step toward the core, got ' + moved.join(','));
const step = DXY[moved[0]];
assert.ok(step && Math.max(Math.abs(9 + step[0] - 9), Math.abs(40 + step[1] - 42)) < 2, 'step closes on 9,42');

attacked.length = 0;
c = creepAt(25, 25, 'W47N9');
c.memory.remote = 'W45N7';
R.defender.run(c);
assert.strictEqual(attacked.length, 0, 'W47N9: never attack');

attacked.length = 0;
Memory.remote.W45N7.th = { st: 'SAFE', since: 1 };
c = creepAt(35, 29, 'W46N8');
c.room.find = () => [];
Game.rooms.W46N8 = c.room;
R.defender.run(c);
assert.strictEqual(attacked.length, 0, 'fight over: do not keep attacking');
assert.strictEqual(c.memory.recycled, 1, 'fight over: recycle at the home spawn');

Memory.remote.W45N7.th = { st: 'THREAT', mission: 'core', why: 'core', since: 1 };
assert.strictEqual(S.defenderOrder('W45N7').core, 1);
assert.strictEqual(S.defenderOrder('W45N7').body.filter(p => p === ATTACK).length, 10);
Memory.remote.W45N7.th = { st: 'THREAT', mission: 'solo', why: 'solo', since: 1 };
assert.strictEqual(S.defenderOrder('W45N7').core, 0);
assert.ok(S.defenderOrder('W45N7').body.includes(RANGED_ATTACK), 'creep invaders keep the ranged body');
assert.ok(!S.defenderOrder('W45N7').body.includes(ATTACK));

// home spawn actually requests the melee body when the FSM says core
Memory.username = 'Misaki';
Memory.defense = { remoteDefender: true };
Memory.remote.W45N7 = { res: { username: 'Misaki', ticksToEnd: 2000 }, seen: 90000, claim2: 90000,
  th: { st: 'THREAT', mission: 'core', why: 'core', since: 89900 } };
const home = {
  name: 'W46N8', energyAvailable: 1400, energyCapacityAvailable: 1300,
  controller: { level: 5 }, storage: { store: { energy: 5000 } },
  memory: { lastFull: 89990, sources: [] }, find: () => [],
};
Game.time = 90000;
Game.rooms = { W46N8: home };
Game.creeps = { queen1: { name: 'queen1', memory: { role: 'queen', home: 'W46N8' }, room: { name: 'W46N8' }, ticksToLive: 1400, spawning: false, body: [{ type: 'carry' }] } };
const spawned = [];
const spawn = {
  room: home, spawning: null, pos: { x: 35, y: 28, getRangeTo: () => 8 },
  spawnCreep: (b, name, o) => { spawned.push({ name, body: b, mem: o.memory }); return OK; },
};
assert.strictEqual(T.armed('W45N7'), true);
assert.strictEqual(T.wantDefender('W46N8'), 'W45N7');
S.run(spawn);
assert.strictEqual(spawned.length, 1, 'one spawn');
assert.strictEqual(spawned[0].mem.role, 'defender');
assert.strictEqual(spawned[0].mem.remote, 'W45N7');
assert.strictEqual(spawned[0].mem.core, 1);
assert.strictEqual(spawned[0].body.filter(p => p === ATTACK).length, 10);
assert.strictEqual(spawned[0].body.filter(p => p === MOVE).length, 10);
assert.strictEqual(Memory.remote.W45N7.th.def, spawned[0].name);
console.log('core_buster ok');
