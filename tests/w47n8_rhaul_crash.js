// 11-13 01:1x live (tick ~84229650): stor ~0–500, avail ~458/5600, W47N7 containers 2000/2000,
// no w8rhauler, but spawn waited on w8mminer at 1350. Income has to move before that sink,
// and the first rhauler has to be a road body this room can pay — not the 1250 cap body, not 2C2M.
// node tests/w47n8_rhaul_crash.js
const assert = require('assert'), path = require('path');
const d = path.join(__dirname, '..', 'src', 'rooms', 'w47n8');
Object.assign(global, {
  STRUCTURE_CONTAINER: 'container', STRUCTURE_EXTRACTOR: 'extractor', STRUCTURE_TERMINAL: 'terminal',
  STRUCTURE_SPAWN: 'spawn', STRUCTURE_EXTENSION: 'extension', STRUCTURE_TOWER: 'tower', STRUCTURE_STORAGE: 'storage',
  STRUCTURE_LINK: 'link', STRUCTURE_ROAD: 'road', STRUCTURE_WALL: 'constructedWall', STRUCTURE_RAMPART: 'rampart',
  STRUCTURE_LAB: 'lab', STRUCTURE_FACTORY: 'factory', LOOK_STRUCTURES: 'structure', LOOK_CREEPS: 'creep',
  LOOK_CONSTRUCTION_SITES: 'constructionSite',
  FIND_MINERALS: 116, FIND_MY_STRUCTURES: 108, FIND_MY_CREEPS: 106, FIND_HOSTILE_CREEPS: 103,
  FIND_HOSTILE_STRUCTURES: 109, STRUCTURE_INVADER_CORE: 'invaderCore',
  FIND_DROPPED_RESOURCES: 105, FIND_STRUCTURES: 107, FIND_SOURCES_ACTIVE: 104, FIND_MY_SPAWNS: 112,
  FIND_MY_CONSTRUCTION_SITES: 114, FIND_SOURCES: 103, RESOURCE_ENERGY: 'energy',
  WORK: 'work', MOVE: 'move', CARRY: 'carry', ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack',
  HEAL: 'heal', TOUGH: 'tough', CLAIM: 'claim',
  BODYPART_COST: { work: 100, move: 50, carry: 50, attack: 80, ranged_attack: 150, heal: 250, tough: 10, claim: 600 },
  OK: 0, ERR_NOT_ENOUGH_ENERGY: -6,
  Memory: { ops: {} },
  Game: { time: 84229650, rooms: {}, creeps: {}, getObjectById: () => null },
});
// Screeps ships lodash 3, where _.sum(col, iteratee) exists. Lodash 4 moved that to sumBy.
const __ld = require('lodash');
if (typeof __ld.sumBy === 'function') {
  const _sum = __ld.sum.bind(__ld);
  __ld.sum = (col, iter) => (typeof iter === 'function' ? __ld.sumBy(col, iter) : _sum(col));
}
global._ = __ld;
const C = require(path.join(d, 'config')), W = require(path.join(d, 'index.js'));
const cost = b => b.reduce((s, p) => s + BODYPART_COST[p], 0);
const cnt = (b, t) => b.filter(p => p === t).length;
const part = (t, n) => Array(n).fill({ type: t });
const road = (b) => cnt(b, WORK) === 1 && cnt(b, CARRY) === 2 * cnt(b, MOVE) - 1;

assert.strictEqual(C.RCL6_MINERALS, true, 'mineral gate stays on');
assert.strictEqual(C.RCL6_LABS, false);
assert.strictEqual(C.RCL7_INDUSTRY, false);
assert.strictEqual(cost(W.bodyFor('w8rhauler', 5600)), 1250, 'healthy cap rhauler stays 15C1W8M');
assert.strictEqual(cost(W.bodyFor('w8mminer', 5600)), 1350, 'cap mineral miner stays 12W3M');

const sites = Array.from({ length: 11 }, (_, i) => ({
  structureType: i ? 'lab' : 'factory', progress: 0, progressTotal: 50000,
}));
const st = {};
const put = (x, y, o) => { (st[x * 50 + y] = st[x * 50 + y] || []).push(Object.assign({ pos: { x, y } }, o)); };
put(37, 44, { structureType: 'container', store: { energy: 0, K: 0, getFreeCapacity: () => 1600 } });
put(37, 45, { structureType: 'extractor' });
const mineral = { mineralAmount: 70000, mineralType: 'K', pos: { x: 37, y: 45 } };
let remoteE = 2000;
const remote = {
  name: 'W47N7',
  find: (k, o) => {
    let a = [];
    if (k === FIND_STRUCTURES) a = [
      { structureType: 'container', pos: { x: 18, y: 17 }, store: { energy: remoteE } },
      { structureType: 'container', pos: { x: 31, y: 34 }, store: { energy: remoteE } },
    ];
    else if (k === FIND_DROPPED_RESOURCES) a = [];
    return o && o.filter ? a.filter(o.filter) : a;
  },
};
const room = {
  name: C.ROOM, energyAvailable: 458, energyCapacityAvailable: 5600,
  controller: { level: 7, my: true, ticksToDowngrade: 100000 },
  storage: { store: { energy: 500 }, pos: { x: 35, y: 32 } },
  terminal: { store: { energy: 0 }, pos: { x: 35, y: 33 } },
  memory: {},
  lookForAt: (k, x, y) => k === LOOK_STRUCTURES ? (st[x * 50 + y] || []) : [],
  find: (k, o) => {
    let a = [];
    if (k === FIND_MY_STRUCTURES || k === FIND_STRUCTURES) a = Object.values(st).flat();
    else if (k === FIND_MINERALS) a = [mineral];
    else if (k === FIND_MY_CREEPS) a = Object.values(Game.creeps);
    else if (k === FIND_MY_CONSTRUCTION_SITES) a = sites;
    else if (k === FIND_HOSTILE_CREEPS || k === FIND_DROPPED_RESOURCES || k === FIND_MY_SPAWNS) a = [];
    return o && o.filter ? a.filter(o.filter) : a;
  },
};
Game.rooms[C.ROOM] = room;
Game.rooms[C.REMOTE.room] = remote;

function creep(role, extra, body) {
  const b = body || part(WORK, 6).concat(part(MOVE, 1));
  return {
    memory: Object.assign({ role, home: C.ROOM, arr: 1 }, extra),
    ticksToLive: 1400, spawning: false, body: b,
    getActiveBodyparts(t) { return this.body.filter(p => p.type === t).length; },
    pos: { x: 20, y: 20, inRangeTo: () => false, getRangeTo: () => 5 },
  };
}
function fleet(rhBodies) {
  const o = {
    m0: creep('w8miner', { si: 0 }),
    m1: creep('w8miner', { si: 1 }),
    h0: creep('w8hauler', {}, part(CARRY, 10).concat(part(MOVE, 5))),
    h1: creep('w8hauler', {}, part(CARRY, 10).concat(part(MOVE, 5))),
    f0: creep('w8filler', {}, part(CARRY, 4).concat(part(MOVE, 2))),
    f1: creep('w8filler', {}, part(CARRY, 4).concat(part(MOVE, 2))),
    r0: creep('w8rminer', { si: 0 }, part(WORK, 6).concat(part(CARRY, 1), part(MOVE, 3))),
    r1: creep('w8rminer', { si: 1 }, part(WORK, 6).concat(part(CARRY, 1), part(MOVE, 3))),
  };
  (rhBodies || []).forEach((b, i) => { o['rh' + i] = creep('w8rhauler', {}, b); });
  return o;
}
let got = null;
const spawn = {
  name: 'Spawn4', room, spawning: null,
  pos: { x: 34, y: 30, getRangeTo: () => 12 },
  spawnCreep: (b, n, o) => { got = { role: o.memory.role, body: b, cost: cost(b) }; return 0; },
};
function run(opts) {
  Game.time += 1;
  room._sg = null;
  got = null;
  room.energyAvailable = opts.avail;
  room.energyCapacityAvailable = 5600;
  room.storage.store.energy = opts.stor;
  remoteE = opts.remoteE == null ? 2000 : opts.remoteE;
  Game.creeps = fleet(opts.rh);
  Memory.ops = {
    w8model: { links: true, lcarry: 9, rcarry: 49, upw: 31 },
    r7: { by: 'Misaki', endTime: Game.time + 50000 },
  };
  W.spawnRun(spawn);
  const wc = Memory.ops.w8fm && Memory.ops.w8fm.wc;
  return { got, wc, wait: Memory.ops.w8sg && Memory.ops.w8sg.waitCost };
}

// Live crash: stor ~500, avail 458, both remote containers full, no rhauler.
// 11 lab/factory sites and zero upgraders are present so a sink could have won.
{
  const r = run({ stor: 500, avail: 458 });
  assert.ok(r.got, 'crashed room must spawn, not wait, got wait ' + JSON.stringify(r.wc));
  assert.strictEqual(r.got.role, 'w8rhauler', 'stor ~500 + full W47N7 + no rhauler => w8rhauler, not ' + r.got.role);
  assert.ok(r.got.cost <= 458, 'body must be payable from avail 458, cost ' + r.got.cost);
  assert.ok(r.got.cost < 1250, 'must not wait on / spawn only the 1250 cap body');
  assert.ok(road(r.got.body), 'road shape (2 heavy : 1 MOVE + WORK), not 1:1 2C2M: ' + r.got.body);
  assert.ok(cnt(r.got.body, CARRY) >= 3, 'more carry than a 2C2M');
  assert.strictEqual(r.got.cost, 350, 'largest road body 458 can pay is 3C1W2M');
}
{
  const r = run({ stor: 0, avail: 458 });
  assert.strictEqual(r.got && r.got.role, 'w8rhauler', 'stor 0 is the same band');
  assert.strictEqual(r.got && r.got.cost, 350);
}
// Cannot pay even the bootstrap road body: wait for 350, never 1250 and never a 2C2M spawn.
{
  const r = run({ stor: 0, avail: 200 });
  assert.strictEqual(r.got, null, '200 cannot buy a road rhauler');
  assert.deepStrictEqual(r.wc && r.wc.slice(0, 2), ['w8rhauler', 350], 'wait boot road body, not cap/mminer: ' + JSON.stringify(r.wc));
  assert.strictEqual(r.wait, 350);
}
// More energy still in the crash: grow toward the cap body, do not sit on 3C and do not demand 1250.
{
  const r = run({ stor: 500, avail: 800 });
  assert.strictEqual(r.got && r.got.role, 'w8rhauler');
  assert.strictEqual(r.got && r.got.cost, 800, '9C1W5M fits in 800 and is under the 1250 cap');
  assert.ok(road(r.got.body));
  assert.strictEqual(cnt(r.got.body, CARRY), 9);
}
// A 3C bootstrap must not become the fleet. Next hauler waits for the mid road body (7C1W4M=650).
{
  const boot = part(CARRY, 3).concat(part(WORK, 1), part(MOVE, 2));
  const r = run({ stor: 500, avail: 458, rh: [boot] });
  assert.strictEqual(r.got, null, 'do not mint another 350 while one rhauler is alive');
  assert.deepStrictEqual(r.wc && r.wc.slice(0, 2), ['w8rhauler', 650], 'mid body, not mminer/1250: ' + JSON.stringify(r.wc));
  assert.strictEqual(r.wait, 650);
}
// Once avail can pay the cap body, spawn that, even if storage is still empty.
{
  const boot = part(CARRY, 3).concat(part(WORK, 1), part(MOVE, 2));
  const r = run({ stor: 500, avail: 2000, rh: [boot] });
  assert.strictEqual(r.got && r.got.role, 'w8rhauler');
  assert.strictEqual(r.got && r.got.cost, 1250);
}
// Carry floor already met: mineral miner is allowed again (it is not banned for the whole crash).
{
  const fat = part(CARRY, 50).concat(part(MOVE, 25));
  const r = run({ stor: 500, avail: 458, rh: [fat] });
  assert.strictEqual(r.got, null);
  assert.strictEqual(r.wc && r.wc[0], 'w8mminer', 'haul staffed => mineral may wait, not another rhauler');
  assert.strictEqual(r.wc && r.wc[1], 1350);
}
// No stranded remote pile: do not skip the mineral miner just because storage is thin.
{
  const r = run({ stor: 500, avail: 458, remoteE: 0 });
  assert.strictEqual(r.got, null);
  assert.strictEqual(r.wc && r.wc[0], 'w8mminer');
}
// Bank at the soft floor: minerals resume ahead of the rhauler floor (17:4x), same remote pile.
{
  const r = run({ stor: W.LEAN_SOFT, avail: 5600 });
  assert.strictEqual(r.got && r.got.role, 'w8mminer', 'healthy bank resumes w8mminer, got ' + (r.got && r.got.role));
}
// Emergency line itself is no longer "well below": existing order (mminer, then the rhauler floor).
{
  const r = run({ stor: W.LEAN_ARM, avail: 5600 });
  assert.strictEqual(r.got && r.got.role, 'w8mminer', 'stor at LEAN_ARM is not the crash band');
}

assert.strictEqual(C.RCL6_MINERALS, true);
assert.strictEqual(C.RCL6_LABS, false);
assert.strictEqual(C.RCL7_INDUSTRY, false);
console.log('w47n8_rhaul_crash ok');
