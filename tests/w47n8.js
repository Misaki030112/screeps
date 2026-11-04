// W47N8 room module: bodies fit cap, spawn order miner->hauler->upgrader->builder, home creeps ignored.
const assert = require('assert'), path = require('path');
const __ld = require('lodash');
const _sum = __ld.sum.bind(__ld);
__ld.sum = (col, iter) => (typeof iter === 'function' ? __ld.sumBy(col, iter) : _sum(col)); // Screeps lodash3 compat
Object.assign(global, { _: __ld,
  FIND_MY_STRUCTURES: 10, FIND_HOSTILE_CREEPS: 3, FIND_MY_CONSTRUCTION_SITES: 1, FIND_MY_SPAWNS: 2, FIND_MY_CREEPS: 3,
  FIND_DROPPED_RESOURCES: 4, FIND_STRUCTURES: 5, FIND_MINERALS: 6,
  STRUCTURE_EXTENSION: 'extension', STRUCTURE_SPAWN: 'spawn', STRUCTURE_TOWER: 'tower', STRUCTURE_CONTAINER: 'container',
  STRUCTURE_EXTRACTOR: 'extractor', STRUCTURE_STORAGE: 'storage', STRUCTURE_TERMINAL: 'terminal', STRUCTURE_LINK: 'link',
  STRUCTURE_WALL: 'constructedWall', STRUCTURE_RAMPART: 'rampart', STRUCTURE_ROAD: 'road',
  WORK: 'work', CARRY: 'carry', MOVE: 'move', CLAIM: 'claim', RANGED_ATTACK: 'ranged_attack',
  BODYPART_COST: { work: 100, carry: 50, move: 50, ranged_attack: 150, attack: 80, heal: 250, tough: 10, claim: 600 },
  RESOURCE_ENERGY: 'energy', LOOK_STRUCTURES: 'structure', OK: 0, ERR_RCL_NOT_ENOUGH: -14,
  Game: { time: 5, creeps: {}, rooms: {} }, Memory: {} });
const W = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'index.js'));
const Cfg = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'config.js'));
const cost = b => b.reduce((s, p) => s + BODYPART_COST[p], 0);
for (const e of [300, 550, 800, 1300]) for (const r of ['w8miner', 'w8hauler', 'w8upgrader', 'w8builder']) assert.ok(cost(W.bodyFor(r, e)) <= e, r + '@' + e);
function run(creeps, sites = 0, avail = 300, roomExtra = {}) {
  Game.creeps = creeps; let got = null;
  const room = Object.assign({
    name: 'W47N8', energyCapacityAvailable: Math.max(avail, 300), energyAvailable: avail,
    controller: { level: 7, ticksToDowngrade: 100000 },
    find: (t, opts) => {
      if (t === 1) return Array.from({ length: sites }, () => ({ progressTotal: 1, progress: 0, structureType: 'road' }));
      if (t === FIND_STRUCTURES && roomExtra._structs) {
        const all = roomExtra._structs;
        return opts && opts.filter ? all.filter(opts.filter) : all;
      }
      return [];
    },
    lookForAt: () => []
  }, roomExtra);
  delete room._structs;
  const spawn = { spawning: null, pos: { getRangeTo: () => 10 }, room,
    spawnCreep: (b, n, o) => { got = o.memory; return 0; } };
  W.spawnRun(spawn); return got;
}
const mk = (role, home, extra = {}) => {
  const body = extra.body || (
    role === 'w8miner' ? [{ type: 'work' }, { type: 'work' }, { type: 'work' }, { type: 'work' }, { type: 'work' }, { type: 'move' }] :
    role === 'w8hauler' ? [{ type: 'carry' }, { type: 'carry' }, { type: 'move' }] :
    role === 'w8upgrader' ? [{ type: 'work' }, { type: 'carry' }, { type: 'move' }] :
    [{ type: 'work' }, { type: 'carry' }, { type: 'move' }]
  );
  const { body: _b, ...memExtra } = extra;
  return {
    memory: Object.assign({ role, home }, memExtra),
    ticksToLive: 1000,
    body,
    getActiveBodyparts: t => body.filter(p => p.type === t).length
  };
};
assert.strictEqual(run({}).role, 'w8miner');
assert.strictEqual(run({}).si, 0);
assert.strictEqual(run({ a: mk('w8miner', 'W47N8', { si: 0 }) }).si, 1);
assert.strictEqual(run({ a: mk('w8miner', 'W47N8', { si: 0 }), b: mk('w8miner', 'W47N8', { si: 1 }) }).role, 'w8hauler');
// home creeps (home W46N8) are not counted
assert.strictEqual(run({ a: mk('miner', 'W46N8'), b: mk('w8miner', 'W46N8', { si: 0 }) }).role, 'w8miner');
const full = { a: mk('w8miner', 'W47N8', { si: 0 }), b: mk('w8miner', 'W47N8', { si: 1 }), c: mk('w8hauler', 'W47N8'), d: mk('w8hauler', 'W47N8') };
assert.strictEqual(run(full).role, 'w8hauler', 'base hauler quota is 3 without links');
full.g = mk('w8hauler', 'W47N8');
assert.strictEqual(run(full).role, 'w8upgrader');
// 10-29: links:true drops floor to 2 — with 2 haulers + no loose piles skip to upgrader
Memory.ops = { w8model: { links: true, lcarry: 9, rcarry: 49, upw: 31 } };
const linked = { a: mk('w8miner', 'W47N8', { si: 0 }), b: mk('w8miner', 'W47N8', { si: 1 }), c: mk('w8hauler', 'W47N8'), d: mk('w8hauler', 'W47N8') };
assert.strictEqual(run(linked).role, 'w8upgrader', 'links:true hauler floor is 2');
// 11-02 02:4x: links HMAX — under soft-cap (2 upgraders, stor<LEAN_SOFT) surplus spawns 3rd hauler when source conts overflow
const linkedSoft = Object.assign({}, linked, {
  e: mk('w8upgrader', 'W47N8'), f: mk('w8upgrader', 'W47N8')
});
const srcCont = {
  structureType: 'container',
  pos: { x: Cfg.SOURCES[0].stand[0], y: Cfg.SOURCES[0].stand[1] },
  store: { energy: 2500 }
};
assert.strictEqual(run(linkedSoft, 0, 1300, {
  storage: { store: { energy: 18000 } },
  _structs: [srcCont]
}).role, 'w8hauler', 'links:true HMAX spawns 3rd hauler on loose>2000 under soft-cap');
// 11-04 08:4x: with 3 haulers already + loose>2000, HMAX rises to 4 (overflow valve for B/south)
const linkedSoft3 = Object.assign({}, linkedSoft, { g: mk('w8hauler', 'W47N8') });
assert.strictEqual(run(linkedSoft3, 0, 1300, {
  storage: { store: { energy: 18000 } },
  _structs: [srcCont]
}).role, 'w8hauler', 'links:true HMAX=4 spawns 4th hauler on loose>2000 under soft-cap');
delete Memory.ops;
Object.assign(full, { e: mk('w8upgrader', 'W47N8'), f: mk('w8upgrader', 'W47N8') });
assert.strictEqual(run(full, 3).role, 'w8builder');
assert.strictEqual(W.selfSufficient(), false, 'no room visible -> not self-sufficient');
Memory.ops = { w8move: { phase: 'build', t0: 4 } };
assert.strictEqual(W.selfSufficient(), true, 'planned spawn move (build phase) -> no home pioneers');
Memory.ops.w8move.phase = 'done'; assert.strictEqual(W.selfSufficient(), false, 'move done + no spawn visible -> pioneers allowed (real loss)');
delete Memory.ops;
console.log('w47n8 ok');
