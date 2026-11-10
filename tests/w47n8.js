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
// 11-04 14:4x: post-abort maint — container debt arms builder without full spawn energy / %50 throttle
Memory.ops = { w8model: { links: true, lcarry: 9, rcarry: 49, upw: 31 }, w8day: { softE: 1 } };
const postAbort = {
  a: mk('w8miner', 'W47N8', { si: 0 }), b: mk('w8miner', 'W47N8', { si: 1 }),
  c: mk('w8hauler', 'W47N8'), d: mk('w8hauler', 'W47N8'),
  e: mk('w8upgrader', 'W47N8'), f: mk('w8upgrader', 'W47N8'),
  // fillers so filler rules do not claim the spawn
  g: mk('w8filler', 'W47N8'), h: mk('w8filler', 'W47N8')
};
const weakCont = {
  structureType: 'container', hits: 90000, hitsMax: 250000,
  pos: { x: 13, y: 26 }, store: { energy: 0 }
};
Game.time = 1001; // odd — old %50 gate would miss
assert.strictEqual(run(postAbort, 0, 3200, {
  storage: { store: { energy: 18000 } },
  energyCapacityAvailable: 5600,
  _structs: [weakCont]
}).role, 'w8builder', '14:4x: cont<50% spawns maint at eAvail 3200/5600 (not full cap)');
// road-only debt still wants full cap (no builder when eAvail partial)
const weakRoad = {
  structureType: 'road', hits: 1000, hitsMax: 5000,
  pos: { x: 34, y: 30 }
};
assert.strictEqual(run(postAbort, 0, 3200, {
  storage: { store: { energy: 18000 } },
  energyCapacityAvailable: 5600,
  _structs: [weakRoad]
}), null, '14:4x: roadCrit-only does not arm maint under partial spawn energy');
// 11-05 20:2x: severe cont debt (≥3 <50%) arms a 2nd maint builder while softCap bank (Overmind repairTicks)
{
  const withOne = Object.assign({}, postAbort, { i: mk('w8builder', 'W47N8') });
  const threeWeak = [
    { structureType: 'container', hits: 30000, hitsMax: 250000, pos: { x: 13, y: 26 }, store: { energy: 0 } },
    { structureType: 'container', hits: 40000, hitsMax: 250000, pos: { x: 26, y: 11 }, store: { energy: 0 } },
    { structureType: 'container', hits: 50000, hitsMax: 250000, pos: { x: 11, y: 43 }, store: { energy: 0 } }
  ];
  assert.strictEqual(run(withOne, 0, 3200, {
    storage: { store: { energy: 18000 } },
    energyCapacityAvailable: 5600,
    _structs: threeWeak
  }).role, 'w8builder', '20:2x: contLow≥3 spawns 2nd maint at eAvail 3200/5600');
  // two weak conts + 1 builder: do NOT spawn 3rd / 2nd
  assert.strictEqual(run(withOne, 0, 3200, {
    storage: { store: { energy: 18000 } },
    energyCapacityAvailable: 5600,
    _structs: threeWeak.slice(0, 2)
  }), null, '20:2x: only 2 conts <50% keeps max 1 maint builder');
}
// 17:4x 11-04: soft-band surplus blocked — hysteresis softCap2 OFF must NOT spawn 4th while stor<LEAN_SOFT
{
  assert.strictEqual(Cfg.HUB_LINK, true);
  const ctlCont = { structureType: 'container', store: { energy: 1500 }, pos: { x: Cfg.CTL_CONT[0], y: Cfg.CTL_CONT[1] } };
  const ctlLink = { structureType: 'link', store: { energy: 400 }, pos: { x: Cfg.CTL_LINK[0], y: Cfg.CTL_LINK[1] } };
  const hubLink = { structureType: 'link', store: { energy: 200 }, pos: { x: 33, y: 34 } };
  const cells = {};
  for (const s of [ctlCont, ctlLink, hubLink]) {
    const k = s.pos.x * 50 + s.pos.y;
    (cells[k] = cells[k] || []).push(s);
  }
  const look = (k, x, y) => k === LOOK_STRUCTURES ? (cells[x * 50 + y] || []) : [];
  const base3 = {
    a: mk('w8miner', 'W47N8', { si: 0 }), b: mk('w8miner', 'W47N8', { si: 1 }),
    c: mk('w8hauler', 'W47N8'), d: mk('w8hauler', 'W47N8'), e: mk('w8hauler', 'W47N8'),
    f: mk('w8upgrader', 'W47N8'), g: mk('w8upgrader', 'W47N8'), h: mk('w8upgrader', 'W47N8'),
    i: mk('w8filler', 'W47N8'), j: mk('w8filler', 'W47N8')
  };
  Memory.ops = { w8model: { links: true, lcarry: 9, rcarry: 49, upw: 31 }, w8day: { softE: 0, leanBank: 0 } };
  const softBandGot = run(base3, 0, 5600, {
    storage: { store: { energy: 23598 } },
    energyCapacityAvailable: 5600,
    lookForAt: look
  });
  assert.ok(!softBandGot || softBandGot.role !== 'w8upgrader',
    '17:4x: soft-band hysteresis must not surplus-spawn 4th upgrader: ' + JSON.stringify(softBandGot));
  Memory.ops = { w8model: { links: true, lcarry: 9, rcarry: 49, upw: 31 }, w8day: { softE: 0, leanBank: 0 } };
  assert.strictEqual(run(base3, 0, 5600, {
    storage: { store: { energy: 26000 } },
    energyCapacityAvailable: 5600,
    lookForAt: look
  }).role, 'w8upgrader', '17:4x: stor≥25k + hub+feedOk still allows surplus 4th');
}
delete Memory.ops;
Object.assign(full, { e: mk('w8upgrader', 'W47N8'), f: mk('w8upgrader', 'W47N8') });
assert.strictEqual(run(full, 3).role, 'w8builder');
assert.strictEqual(W.selfSufficient(), false, 'no room visible -> not self-sufficient');
Memory.ops = { w8move: { phase: 'build', t0: 4 } };
assert.strictEqual(W.selfSufficient(), true, 'planned spawn move (build phase) -> no home pioneers');
Memory.ops.w8move.phase = 'done'; assert.strictEqual(W.selfSufficient(), false, 'move done + no spawn visible -> pioneers allowed (real loss)');
delete Memory.ops;
// 11-10 patrol: a long-walking si0 miner with no arr must not cover source A
Game.time = 1000;
const lost = mk('w8miner', 'W47N8', { si: 0, born: 100 }); // age 900, no arr
assert.strictEqual(run({ a: lost }).si, 0, 'lost walker (no arr, age >> lead) does not cover its source');
assert.strictEqual(run({ a: mk('w8miner', 'W47N8', { si: 0, born: 100, arr: 200 }) }).si, 1, 'arrived miner still covers');
assert.strictEqual(run({ a: mk('w8miner', 'W47N8', { si: 0, born: 980 }) }).si, 1, 'young walker still covers');
Game.time = 5;
console.log('w47n8 ok');
