// W47N8 upgrader bank (11-10) + one spawn-planning pass per room.
// node tests/w47n8_upbank.js
const assert = require('assert'), path = require('path');
const __ld = require('lodash');
const _sum = __ld.sum.bind(__ld);
__ld.sum = (col, iter) => (typeof iter === 'function' ? __ld.sumBy(col, iter) : _sum(col));
Object.assign(global, { _: __ld,
  FIND_MY_STRUCTURES: 10, FIND_HOSTILE_CREEPS: 3, FIND_MY_CONSTRUCTION_SITES: 1, FIND_MY_SPAWNS: 2, FIND_MY_CREEPS: 4,
  FIND_DROPPED_RESOURCES: 5, FIND_STRUCTURES: 6, FIND_MINERALS: 7,
  STRUCTURE_EXTENSION: 'extension', STRUCTURE_SPAWN: 'spawn', STRUCTURE_TOWER: 'tower', STRUCTURE_CONTAINER: 'container',
  STRUCTURE_STORAGE: 'storage', STRUCTURE_TERMINAL: 'terminal', STRUCTURE_LINK: 'link',
  STRUCTURE_WALL: 'constructedWall', STRUCTURE_RAMPART: 'rampart', STRUCTURE_ROAD: 'road',
  WORK: 'work', CARRY: 'carry', MOVE: 'move',
  BODYPART_COST: { work: 100, carry: 50, move: 50, ranged_attack: 150, attack: 80, heal: 250, tough: 10, claim: 600 },
  RESOURCE_ENERGY: 'energy', LOOK_STRUCTURES: 'structure', OK: 0,
  Game: { time: 100000, creeps: {}, rooms: {}, getObjectById: () => null }, Memory: { ops: {} } });
const W = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'index.js'));
const C = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'config.js'));
const L = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'layout.js'));
const cmd = require(path.join(__dirname, '..', 'src', 'utils', 'cmd.js'));

assert.strictEqual(W.LEAN_SOFT, 25000, 'seal line stays 25k');
assert.strictEqual(W.UP_STICKY, 30000); // 2026-11-26 RCL8 plan: was 40000
assert.strictEqual(W.UP_STICKY_T, 300); // was 500
assert.strictEqual(W.UP_REARM, 20000); // was 30000
assert.strictEqual(W.IDLE_EVERY, 4);

const cells = {};
function put(x, y, type, store) {
  const o = { structureType: type, pos: { x, y, inRangeTo: () => false }, store: store || (type === 'tower' ? { energy: 900 } : {}) };
  (cells[x * 50 + y] = cells[x * 50 + y] || []).push(o);
  return o;
}
put(L.ORDER.spawn[0][0], L.ORDER.spawn[0][1], 'spawn');
put(L.ORDER.spawn[1][0], L.ORDER.spawn[1][1], 'spawn');
put(L.ORDER.tower[0][0], L.ORDER.tower[0][1], 'tower');
put(L.ORDER.tower[1][0], L.ORDER.tower[1][1], 'tower');
put(L.ORDER.tower[2][0], L.ORDER.tower[2][1], 'tower');
put(L.ORDER.terminal[0][0], L.ORDER.terminal[0][1], 'terminal');
put(C.MINERAL_CONT[0], C.MINERAL_CONT[1], 'container', { energy: 0 });
let hostiles = [], sites = [];
const room = {
  name: 'W47N8',
  energyAvailable: 5600,
  energyCapacityAvailable: 5600,
  controller: { level: 7, ticksToDowngrade: 100000 },
  storage: { store: { energy: 18000 } },
  terminal: { store: {} },
  memory: {},
  lookForAt: (k, x, y) => (k === LOOK_STRUCTURES ? (cells[x * 50 + y] || []) : []),
  find: (t) => {
    if (t === FIND_HOSTILE_CREEPS) return hostiles;
    if (t === FIND_MY_CONSTRUCTION_SITES) return sites;
    return [];
  },
};
function creep(role, extra) {
  const body = Array(6).fill({ type: 'work' }).concat([{ type: 'carry' }, { type: 'move' }]);
  const c = {
    memory: Object.assign({ role, home: 'W47N8' }, extra),
    ticksToLive: 1400, spawning: false, body,
    getActiveBodyparts: (t) => body.filter(p => p.type === t).length,
    pos: { x: 20, y: 20, inRangeTo: () => false },
  };
  return c;
}
function fleet(nUp) {
  const o = {
    m0: creep('w8miner', { si: 0, arr: 1 }),
    m1: creep('w8miner', { si: 1, arr: 1 }),
    h0: creep('w8hauler'), h1: creep('w8hauler'),
  };
  for (let i = 0; i < nUp; i++) o['u' + i] = creep('w8upgrader');
  Game.creeps = o;
}
function boot(stor, nUp, ops) {
  room.storage.store.energy = stor;
  fleet(nUp);
  Memory.ops = Object.assign({
    w8model: { links: true, lcarry: 9, rcarry: 49, upw: 31 },
    w8day: { leanBank: 0, softE: 0 },
  }, ops || {});
  hostiles = [];
}
function pair() {
  const spawned = [];
  const mk = (name) => ({
    name, id: name, spawning: null, room,
    pos: { x: 34, y: 30, getRangeTo: () => 8 },
    spawnCreep: (b, n, o) => { spawned.push(o.memory); return OK; },
  });
  return { spawned, a: mk('SpawnA'), b: mk('SpawnB') };
}

// dayObs: 30k must hold for 300 ticks before keep becomes 3. 25k never opens 4–6.
{
  Game.time = 200000;
  boot(26000, 4);
  W.dayObs(room);
  assert.strictEqual(Memory.ops.w8day.upgKeep, 2, '26k keep=2');
  assert.strictEqual(Memory.ops.w8day.upLatched, 0);
  assert.strictEqual(Memory.ops.w8day.upgCeil, 2);
  assert.strictEqual((Memory.ops.w8recycle || []).length, 2, '4 upgraders trim to 2 at 26k');
  assert.strictEqual(W.LEAN_SOFT, 25000);

  Game.time = 201000;
  boot(30000, 4);
  W.dayObs(room);
  assert.strictEqual(Memory.ops.w8day.upLatched, 0, 'first tick at 30k does not latch');
  assert.strictEqual(Memory.ops.w8day.upgKeep, 2);
  const since = Memory.ops.w8up.since;
  assert.strictEqual(since, 201000);
  Game.time = since + 299;
  room.storage.store.energy = 31000;
  W.dayObs(room);
  assert.strictEqual(Memory.ops.w8day.upLatched, 0, '299 ticks at ≥30k still keep=2');
  assert.strictEqual(Memory.ops.w8day.upgKeep, 2);
  Game.time = since + 300;
  room.storage.store.energy = 29000; // dipped under 30k before the latch: streak resets
  W.dayObs(room);
  assert.strictEqual(Memory.ops.w8day.upLatched, 0, 'a dip under 30k before 300 ticks restarts the streak');
  assert.strictEqual(Memory.ops.w8up.since, 0);

  Game.time = 202000;
  room.storage.store.energy = 30000;
  W.dayObs(room);
  const since2 = Memory.ops.w8up.since;
  Game.time = since2 + 300;
  room.storage.store.energy = 32000;
  delete Memory.ops.w8recycle;
  W.dayObs(room);
  assert.strictEqual(Memory.ops.w8day.upLatched, 1);
  assert.strictEqual(Memory.ops.w8day.upgKeep, 3, 'after 300 ticks at ≥30k, steady 3');
  assert.strictEqual(Memory.ops.w8day.upgCeil, 3, 'not 4–6');
  assert.strictEqual((Memory.ops.w8recycle || []).length, 1, '4 upgraders trim to 3, not to 0');

  room.storage.store.energy = 25000;
  W.dayObs(room);
  assert.strictEqual(Memory.ops.w8day.upLatched, 1, '25k stays latched');
  assert.strictEqual(Memory.ops.w8day.upgKeep, 3);

  room.storage.store.energy = 19999;
  delete Memory.ops.w8recycle;
  W.dayObs(room);
  assert.strictEqual(Memory.ops.w8day.upLatched, 0, 'below 20k re-arms');
  assert.strictEqual(Memory.ops.w8day.upgKeep, 2);
  assert.ok((Memory.ops.w8recycle || []).length >= 2, 'drop back to 2');

  Memory.ops.w8up = { on: 1, since: 1 };
  Memory.ops.w8threat = Game.time;
  room.storage.store.energy = 50000;
  delete Memory.ops.w8recycle;
  W.dayObs(room);
  assert.strictEqual(W.threatSoft(), true);
  assert.strictEqual(Memory.ops.w8day.upLatched, 1, 'threat does not clear the latch');
  assert.strictEqual(Memory.ops.w8day.upgKeep, 2, 'threatSoft still caps keep at 2');
  assert.ok((Memory.ops.w8recycle || []).length >= 2);
  delete Memory.ops.w8threat;
}

// Spawn: brief 25k does not request a 3rd or a 4th. Latched bank requests one 3rd, never a 4th.
{
  Game.time = 300000;
  boot(26000, 3);
  const s = pair();
  W.spawnRun(s.a);
  assert.ok(!s.spawned.some(m => m.role === 'w8upgrader'), '26k with 3 upgraders does not spawn another ' + JSON.stringify(s.spawned));
  boot(26000, 2);
  const s2 = pair();
  W.spawnRun(s2.a);
  assert.ok(!s2.spawned.some(m => m.role === 'w8upgrader'), '26k with 2 upgraders stays at 2');

  boot(45000, 2, { w8up: { on: 1, since: 1 }, w8day: { leanBank: 0, softE: 0 } });
  const s3 = pair();
  W.spawnRun(s3.a);
  assert.strictEqual(s3.spawned.filter(m => m.role === 'w8upgrader').length, 1, 'latched bank starts the 3rd');
  boot(45000, 3, { w8up: { on: 1, since: 1 }, w8day: { leanBank: 0, softE: 0 } });
  const s4 = pair();
  W.spawnRun(s4.a);
  assert.ok(!s4.spawned.some(m => m.role === 'w8upgrader'), 'latched bank does not start a 4th');

  boot(45000, 2, { w8up: { on: 1, since: 1 }, w8threat: Game.time, w8day: { leanBank: 0, softE: 0 } });
  const s5 = pair();
  W.spawnRun(s5.a);
  assert.ok(!s5.spawned.some(m => m.role === 'w8upgrader'), 'threatSoft blocks the 3rd while latched');
}

// Two idle spawns: one planning pass. A wanted body that can be paid starts the same tick.
// A short-energy tick throttles. Hostiles and a commander order do not.
{
  Game.time = 400000;
  boot(18000, 2);
  room.energyAvailable = 5600;
  const idle = pair();
  W.spawnRun(idle.a);
  W.spawnRun(idle.b);
  assert.strictEqual(Memory.ops.w8sg.passes, 1, 'two idle spawns, one cascade');
  assert.strictEqual(Memory.ops.w8sg.skipTick, 1);
  assert.strictEqual(idle.spawned.length, 0, 'idle fleet spawns nothing ' + JSON.stringify(idle.spawned));

  Game.time = 401000;
  boot(18000, 1);
  room.energyAvailable = 200;
  room.energyCapacityAvailable = 5600;
  const wait = pair();
  W.spawnRun(wait.a);
  W.spawnRun(wait.b);
  assert.strictEqual(wait.spawned.length, 0, '200 energy cannot start a 10W upgrader');
  assert.strictEqual(Memory.ops.w8sg.passes, 1, 'the waiting sibling does not cascade');
  assert.ok(Memory.ops.w8sg.waitCost > 200);
  Game.time = 401001;
  room.energyAvailable = 200;
  const skipped = pair();
  W.spawnRun(skipped.a);
  W.spawnRun(skipped.b);
  assert.strictEqual(Memory.ops.w8sg.passes, 0, 'next tick still short: no cascade');
  assert.strictEqual(skipped.spawned.length, 0);
  Game.time = 401002;
  room.energyAvailable = 5600;
  const pay = pair();
  W.spawnRun(pay.a);
  assert.ok(pay.spawned.some(m => m.role === 'w8upgrader'), 'energy catch-up starts the upgrader this tick');

  Game.time = 402000;
  boot(18000, 2);
  room.energyAvailable = 5600;
  const arm = pair();
  W.spawnRun(arm.a);
  assert.strictEqual(Memory.ops.w8sg.passes, 1);
  Game.time = 402001;
  hostiles = [{ my: false, body: [], pos: { x: 10, y: 10 } }];
  const hot = pair();
  W.spawnRun(hot.a);
  assert.ok(Memory.ops.w8sg.passes >= 1, 'hostile forces a full pass inside the idle window');
  hostiles = [];

  Game.time = 403000;
  boot(18000, 2);
  room.energyAvailable = 5600;
  W.spawnRun(pair().a); // arm idle window
  Game.time = 403001;
  const ordered = pair();
  cmd.setStruct(ordered.a.id, { act: 'spawn', allow: 1, body: [MOVE], role: 'hauler', ttl: 5 });
  W.spawnRun(ordered.a);
  W.spawnRun(ordered.b);
  assert.ok(ordered.spawned.some(m => m.role === 'hauler'), 'commander spawn runs inside the idle window');
  assert.ok(Memory.ops.w8sg.passes >= 1, 'sibling spawn still plans while commander is armed');
  cmd.disarm();
}

// 11-12: open construction sites cap RCL7 upgraders at 1. The 40k latch and threatSoft return when the sites are gone.
{
  Game.time = 500000;
  const site = { structureType: 'lab', pos: { x: 29, y: 38 }, progress: 0, progressTotal: 50000 };
  sites = [site];
  boot(45000, 2, { w8up: { on: 1, since: 1 }, w8day: { leanBank: 0, softE: 0 } });
  W.dayObs(room);
  assert.strictEqual(Memory.ops.w8day.upgCeil, 1, 'sites: ceil 1 even after the 40k latch');
  assert.strictEqual(Memory.ops.w8day.upgKeep, 1, 'sites: keep 1');
  assert.strictEqual(Memory.ops.w8day.upLatched, 1, 'latch itself stays');
  assert.strictEqual((Memory.ops.w8recycle || []).length, 1, '2 upgraders trim to 1 while sites are up');
  assert.strictEqual(W.upgTarget(room), 1);
  const s = pair();
  W.spawnRun(s.a);
  assert.ok(!s.spawned.some(m => m.role === 'w8upgrader'), 'latched + sites does not spawn a 2nd or 3rd');

  boot(45000, 0, { w8up: { on: 1, since: 1 }, w8day: { leanBank: 0, softE: 0 } });
  const s0 = pair();
  W.spawnRun(s0.a);
  assert.strictEqual(s0.spawned.filter(m => m.role === 'w8upgrader').length, 1, 'sites still allow the one upgrader');

  boot(26000, 2, { w8day: { leanBank: 0, softE: 0 } });
  W.dayObs(room);
  assert.strictEqual(Memory.ops.w8day.upLatched, 0);
  assert.strictEqual(Memory.ops.w8day.upgCeil, 1, 'unsticky + sites is 1, not 2');
  assert.strictEqual(W.upgTarget(room), 1);

  sites = [];
  boot(45000, 2, { w8up: { on: 1, since: 1 }, w8day: { leanBank: 0, softE: 0 } });
  delete Memory.ops.w8recycle;
  W.dayObs(room);
  assert.strictEqual(Memory.ops.w8day.upgCeil, 3, 'sites gone: 40k latch keep is 3 again');
  assert.strictEqual(Memory.ops.w8day.upLatched, 1);
  assert.strictEqual((Memory.ops.w8recycle || []).length, 0, '2 upgraders under a keep of 3 are not trimmed');
  const s3 = pair();
  W.spawnRun(s3.a);
  assert.strictEqual(s3.spawned.filter(m => m.role === 'w8upgrader').length, 1, 'sites gone: latched bank starts the 3rd');

  boot(26000, 2, { w8day: { leanBank: 0, softE: 0 } });
  W.dayObs(room);
  assert.strictEqual(Memory.ops.w8day.upgCeil, 2, 'sites gone and unsticky: keep stays 2');
  Memory.ops.w8threat = Game.time;
  room.storage.store.energy = 50000;
  Memory.ops.w8up = { on: 1, since: 1 };
  W.dayObs(room);
  assert.strictEqual(Memory.ops.w8day.upgCeil, 2, 'sites gone: threatSoft still caps at 2');
  delete Memory.ops.w8threat;
}

// Busy spawn: the second census (construction-site find) is skipped once this tick already planned.
// A hostile still makes both busy spawns walk it. Neither spawn is dropped.
{
  Game.time = 600000;
  boot(18000, 2);
  room.energyAvailable = 5600;
  Memory.ops.w8sg = { ne: 0, waitCost: 0 };
  let sitesFound = 0;
  const prevFind = room.find;
  room.find = (t) => {
    if (t === FIND_MY_CONSTRUCTION_SITES) sitesFound++;
    return prevFind(t);
  };
  const both = pair();
  both.a.spawning = { name: 'a' };
  both.b.spawning = { name: 'b' };
  sitesFound = 0;
  W.spawnRun(both.a);
  W.spawnRun(both.b);
  assert.strictEqual(sitesFound, 1, 'two busy spawns, one construction-site find');
  assert.strictEqual(both.spawned.length, 0, 'a busy spawn does not spawn');

  Game.time = 600001;
  hostiles = [{ my: false, body: [{ type: 'attack', hits: 100 }] }];
  sitesFound = 0;
  W.spawnRun(both.a);
  W.spawnRun(both.b);
  assert.strictEqual(sitesFound, 2, 'hostile bypass: both busy spawns still census');
  hostiles = [];
  room.find = prevFind;
}
console.log('w47n8 upbank ok');
