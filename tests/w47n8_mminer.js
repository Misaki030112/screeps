// 2026-10-31 11:4x strategy: dormant w8mminer + w8hauler mineralRun (lean KO). Gates stay false — code ready only.
const assert = require('assert'), path = require('path');
const d = path.join(__dirname, '..', 'src', 'rooms', 'w47n8');
Object.assign(global, {
  STRUCTURE_CONTAINER: 'container', STRUCTURE_EXTRACTOR: 'extractor', STRUCTURE_TERMINAL: 'terminal',
  STRUCTURE_SPAWN: 'spawn', STRUCTURE_EXTENSION: 'extension', STRUCTURE_TOWER: 'tower', STRUCTURE_STORAGE: 'storage',
  STRUCTURE_LINK: 'link', STRUCTURE_ROAD: 'road', STRUCTURE_WALL: 'constructedWall', STRUCTURE_RAMPART: 'rampart',
  STRUCTURE_LAB: 'lab', LOOK_STRUCTURES: 'structure', LOOK_CREEPS: 'creep', LOOK_SOURCES: 'source',
  LOOK_CONSTRUCTION_SITES: 'constructionSite',
  FIND_MINERALS: 116, FIND_MY_STRUCTURES: 108, FIND_MY_CREEPS: 106, FIND_HOSTILE_CREEPS: 103,
  FIND_DROPPED_RESOURCES: 105, FIND_STRUCTURES: 107, FIND_SOURCES_ACTIVE: 104, FIND_MY_SPAWNS: 112,
  FIND_MY_CONSTRUCTION_SITES: 114, FIND_SOURCES: 103, RESOURCE_ENERGY: 'energy',
  WORK: 'work', MOVE: 'move', CARRY: 'carry', ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack',
  HEAL: 'heal', TOUGH: 'tough', CLAIM: 'claim',
  BODYPART_COST: { work: 100, move: 50, carry: 50, attack: 80, ranged_attack: 150, heal: 250, tough: 10, claim: 600 },
  OK: 0, ERR_NOT_ENOUGH_ENERGY: -6,
  _: require('lodash'), Memory: { ops: { w8model: { links: true, lcarry: 9, rcarry: 49, upw: 31 } } },
  Game: { time: 50, rooms: {}, creeps: {}, getObjectById: () => null },
});
const C = require(path.join(d, 'config')), W = require(path.join(d, 'index.js'));
const roles = require(path.join(d, 'roles.js'));
const cost = b => b.reduce((s, p) => s + BODYPART_COST[p], 0);
const cnt = (b, t) => b.filter(p => p === t).length;

assert.strictEqual(C.RCL6_MINERALS, true, 'Misaki flip: mineral gate on');
assert.deepStrictEqual(C.MINERAL_CONT, [37, 44]);

// bodyFor: same shape as home mminer (WORK*n + 3 MOVE), fits budget, no CARRY
// body cost = n*100+150; min 2W needs e>=350 (same as home mminer — spawn waits if avail < cost)
for (const e of [350, 550, 800, 1300, 2300]) {
  const b = W.bodyFor('w8mminer', e);
  assert.ok(cost(b) <= e, 'fits ' + e + ': ' + b);
  assert.strictEqual(cnt(b, MOVE), 3, '3 MOVE @' + e);
  assert.ok(cnt(b, WORK) >= 2 && cnt(b, WORK) <= 12, 'WORK range @' + e);
  assert.strictEqual(cnt(b, CARRY), 0, 'no CARRY (drop into container)');
}
assert.deepStrictEqual([cnt(W.bodyFor('w8mminer', 1300), WORK), cnt(W.bodyFor('w8mminer', 1300), MOVE)], [11, 3]);

// mineralRun dormant while gate off (temp)
C.RCL6_MINERALS = false;
const term = { pos: { x: 35, y: 33 }, store: {} };
let pile = 800;
const roomBase = {
  name: C.ROOM, terminal: term,
  lookForAt: (k, x, y) => {
    if (k === LOOK_STRUCTURES && x === 37 && y === 44) {
      const s = { K: pile }; s.getFreeCapacity = () => 2000 - (s.K || 0);
      return [{ structureType: 'container', store: s, pos: { x: 37, y: 44 } }];
    }
    return [];
  },
};
Game.rooms[C.ROOM] = roomBase;
const creep = (store = {}) => {
  const st = Object.assign({ energy: 0 }, store);
  st.getCapacity = () => 400;
  return {
    memory: { home: C.ROOM, role: 'w8hauler' }, store: st, got: [],
    pos: { x: 37, y: 44, isNearTo() { return true; }, inRangeTo() { return true; }, getRangeTo() { return 0; } },
    room: roomBase, withdraw(k, r) { this.got.push(['w', r]); return 0; },
    transfer(d, r) { this.got.push(['t', r]); return 0; },
    moveTo() { return 0; },
  };
};
assert.strictEqual(roles._mineralRun(creep()), false, 'gate off → no mineralRun');

// gate on: small pile waits; >= MIN_RUN(500) withdraws; held mineral delivers to terminal
C.RCL6_MINERALS = true;
pile = 200;
assert.strictEqual(roles._mineralRun(creep()), false, 'small pile waits');
pile = 600;
let c = creep();
assert.strictEqual(roles._mineralRun(c), true);
assert.deepStrictEqual(c.got, [['w', 'K']], '>= MIN_RUN → withdraw K');
c = creep({ K: 400 });
assert.strictEqual(roles._mineralRun(c), true);
assert.deepStrictEqual(c.got, [['t', 'K']], 'deliver K to terminal');
c = creep({ energy: 50 });
pile = 1900;
assert.strictEqual(roles._mineralRun(c), false, 'carrying energy: normal job');
C.RCL6_MINERALS = true;

// spawnRun: with economy fleet filled, gate off → never w8mminer; gate on + line ready → w8mminer
{
  const mk = (role, extra = {}) => ({
    memory: Object.assign({ role, home: C.ROOM }, extra),
    ticksToLive: 1000, spawning: false, body: [{ type: WORK }, { type: WORK }, { type: WORK }, { type: WORK }, { type: WORK }, { type: MOVE }],
    getActiveBodyparts: t => t === WORK ? 5 : 0, pos: { x: 20, y: 20, inRangeTo: () => false },
  });
  // miners + 2 haulers + filler + 3 upgraders (links floor) so spawn falls through to surplus/mminer
  const fleet = {
    a: mk('w8miner', { si: 0 }), b: mk('w8miner', { si: 1 }),
    c: mk('w8hauler'), d: mk('w8hauler'),
    e: mk('w8filler'),
    f: mk('w8upgrader'), g: mk('w8upgrader'), h: mk('w8upgrader'),
  };
  // pad hauler bodies so rCarry / body filters don't crash
  for (const k of Object.keys(fleet)) {
    if (fleet[k].memory.role === 'w8hauler') fleet[k].body = Array(10).fill({ type: CARRY }).concat(Array(5).fill({ type: MOVE }));
    if (fleet[k].memory.role === 'w8filler') fleet[k].body = [{ type: CARRY }, { type: CARRY }, { type: MOVE }];
    if (fleet[k].memory.role === 'w8upgrader') fleet[k].body = Array(8).fill({ type: WORK }).concat([{ type: CARRY }, { type: MOVE }, { type: MOVE }]);
  }
  Game.creeps = fleet;

  const st = {};
  const put = (x, y, o) => { (st[x * 50 + y] = st[x * 50 + y] || []).push(o); };
  put(37, 44, { structureType: 'container', store: { getFreeCapacity: () => 1500, K: 0 }, pos: { x: 37, y: 44 } });
  put(37, 45, { structureType: 'extractor', pos: { x: 37, y: 45 } });
  const mineral = { mineralAmount: 50000, mineralType: 'K', pos: { x: 37, y: 45 } };

  const room = {
    name: C.ROOM, energyAvailable: 2300, energyCapacityAvailable: 2300,
    controller: { level: 6, my: true, ticksToDowngrade: 50000, progress: 3000000, progressTotal: 3645000 },
    storage: { store: { energy: 25000 }, pos: { x: 35, y: 32 } },
    terminal: term, memory: {},
    lookForAt: (k, x, y) => k === LOOK_STRUCTURES ? (st[x * 50 + y] || []) : [],
    find: (k, o) => {
      let a = [];
      if (k === FIND_MY_STRUCTURES || k === FIND_STRUCTURES) a = Object.values(st).flat();
      else if (k === FIND_MINERALS) a = [mineral];
      else if (k === FIND_MY_CREEPS) a = Object.values(Game.creeps);
      else if (k === FIND_MY_CONSTRUCTION_SITES) a = [];
      else if (k === FIND_HOSTILE_CREEPS) a = [];
      else if (k === FIND_DROPPED_RESOURCES) a = [];
      return o && o.filter ? a.filter(o.filter) : a;
    },
  };
  Game.rooms[C.ROOM] = room;

  function runSpawn() {
    let got = null;
    const spawn = {
      room, spawning: null, pos: { x: 34, y: 30, getRangeTo: () => 10 },
      spawnCreep: (b, n, o) => { got = o.memory; return 0; },
    };
    W.spawnRun(spawn);
    return got && got.role;
  }

  C.RCL6_MINERALS = false;
  assert.notStrictEqual(runSpawn(), 'w8mminer', 'gate off: must not spawn w8mminer');

  C.RCL6_MINERALS = true;
  assert.strictEqual(runSpawn(), 'w8mminer', 'gate on + line ready → spawn w8mminer');
  // already have a live mminer → no second
  fleet.mm = mk('w8mminer');
  Game.creeps = fleet;
  assert.notStrictEqual(runSpawn(), 'w8mminer', 'one live w8mminer is enough');
  C.RCL6_MINERALS = false;
}


// 17:4x strategy: soft-cap must NOT starve first w8mminer (Overmind mineral ahead of upgrade).
// stor 10k < LEAN_SOFT → soft wants ≤2 upgraders; with 0 upgraders the OLD queue picked w8upgrader first.
{
  const mk = (role, extra = {}) => ({
    memory: Object.assign({ role, home: C.ROOM }, extra),
    ticksToLive: 1000, spawning: false, body: [{ type: WORK }, { type: WORK }, { type: WORK }, { type: WORK }, { type: WORK }, { type: MOVE }],
    getActiveBodyparts: t => t === WORK ? 5 : 0, pos: { x: 20, y: 20, inRangeTo: () => false },
  });
  const fleet = {
    a: mk('w8miner', { si: 0 }), b: mk('w8miner', { si: 1 }),
    c: mk('w8hauler'), d: mk('w8hauler'),
    e: mk('w8filler'),
    // deliberately ZERO upgraders under soft-cap band
  };
  for (const k of Object.keys(fleet)) {
    if (fleet[k].memory.role === 'w8hauler') fleet[k].body = Array(10).fill({ type: CARRY }).concat(Array(5).fill({ type: MOVE }));
    if (fleet[k].memory.role === 'w8filler') fleet[k].body = [{ type: CARRY }, { type: CARRY }, { type: MOVE }];
  }
  Game.creeps = fleet;
  const st = {};
  const put = (x, y, o) => { (st[x * 50 + y] = st[x * 50 + y] || []).push(o); };
  put(37, 44, { structureType: 'container', store: { getFreeCapacity: () => 1500, K: 0 }, pos: { x: 37, y: 44 } });
  put(37, 45, { structureType: 'extractor', pos: { x: 37, y: 45 } });
  const mineral = { mineralAmount: 50000, mineralType: 'K', pos: { x: 37, y: 45 } };
  const room = {
    name: C.ROOM, energyAvailable: 2300, energyCapacityAvailable: 2300,
    controller: { level: 7, my: true, ticksToDowngrade: 50000, progress: 3000000, progressTotal: 5256000 },
    storage: { store: { energy: 10000 }, pos: { x: 35, y: 32 } },
    terminal: term, memory: {},
    lookForAt: (k, x, y) => k === LOOK_STRUCTURES ? (st[x * 50 + y] || []) : [],
    find: (k, o) => {
      let a = [];
      if (k === FIND_MY_STRUCTURES || k === FIND_STRUCTURES) a = Object.values(st).flat();
      else if (k === FIND_MINERALS) a = [mineral];
      else if (k === FIND_MY_CREEPS) a = Object.values(Game.creeps);
      else if (k === FIND_MY_CONSTRUCTION_SITES) a = [];
      else if (k === FIND_HOSTILE_CREEPS) a = [];
      else if (k === FIND_DROPPED_RESOURCES) a = [];
      else if (k === FIND_STRUCTURES) a = Object.values(st).flat();
      return o && o.filter ? a.filter(o.filter) : a;
    },
  };
  Game.rooms[C.ROOM] = room;
  let got = null;
  const spawn = {
    room, spawning: null, pos: { x: 34, y: 30, getRangeTo: () => 10 },
    spawnCreep: (b, n, o) => { got = o.memory; return 0; },
  };
  C.RCL6_MINERALS = true;
  W.spawnRun(spawn);
  assert.strictEqual(got && got.role, 'w8mminer', '17:4x soft-cap with 0 upg → still w8mminer first, got=' + (got && got.role));
  C.RCL6_MINERALS = false;
}



// 14:4x: mineralSend dormant + live path; termFuel parks energy for fees
{
  assert.strictEqual(typeof W.mineralSend, 'function', 'mineralSend exported');
  Memory.ops = Memory.ops || {};
  // rebuild dayObs sendOk via a minimal room
  const termStore = { K: 0, energy: 0 };
  const homeTermStore = { energy: 0 };
  homeTermStore.getFreeCapacity = () => 50000;
  const sent = [];
  const term = {
    store: termStore, cooldown: 0, storeCapacity: 300000,
    send(res, amt, dest) { sent.push([res, amt, dest]); return 0; },
  };
  const homeTerm = { store: homeTermStore, storeCapacity: 300000 };
  const stMap = {};
  const put = (x, y, o) => { (stMap[x * 50 + y] = stMap[x * 50 + y] || []).push(o); };
  put(37, 44, { structureType: 'container', store: { getFreeCapacity: () => 1500, K: 0 }, pos: { x: 37, y: 44 } });
  put(37, 45, { structureType: 'extractor', pos: { x: 37, y: 45 } });
  const mineral = { mineralAmount: 50000, mineralType: 'K', pos: { x: 37, y: 45 } };
  const room = {
    name: C.ROOM, energyAvailable: 2300, energyCapacityAvailable: 2300,
    controller: { level: 7, my: true, ticksToDowngrade: 50000, progress: 0, progressTotal: 1 },
    storage: { store: { energy: 25000 }, pos: { x: 35, y: 32 } },
    terminal: term, memory: {},
    lookForAt: (k, x, y) => k === LOOK_STRUCTURES ? (stMap[x * 50 + y] || []) : [],
    find: (k, o) => {
      let a = [];
      if (k === FIND_MY_STRUCTURES || k === FIND_STRUCTURES) a = Object.values(stMap).flat();
      else if (k === FIND_MINERALS) a = [mineral];
      else if (k === FIND_MY_CREEPS) a = Object.values(Game.creeps || {});
      else if (k === FIND_MY_CONSTRUCTION_SITES) a = [];
      else if (k === FIND_HOSTILE_CREEPS) a = [];
      else if (k === FIND_DROPPED_RESOURCES) a = [];
      else if (k === FIND_MY_SPAWNS) a = [];
      return o && o.filter ? a.filter(o.filter) : a;
    },
  };
  Game.rooms[C.ROOM] = room;
  Game.rooms.W46N8 = { name: 'W46N8', terminal: homeTerm };
  Game.market = { calcTransactionCost: (amt) => Math.ceil(amt * 0.033) };
  Game.time = 100;
  Game.creeps = Game.creeps || {};

  // gate off: sendWhy=gate, no send intent
  C.RCL6_MINERALS = false;
  termStore.K = 2000; termStore.energy = 500;
  sent.length = 0;
  W.mineralSend(room);
  assert.strictEqual(Memory.ops.w8min.sendWhy, 'gate');
  assert.strictEqual(Memory.ops.w8min.sendOk, 1);
  assert.strictEqual(sent.length, 0, 'no send while gate off');

  // gate on, no K
  C.RCL6_MINERALS = true;
  termStore.K = 0;
  W.mineralSend(room);
  assert.strictEqual(Memory.ops.w8min.sendWhy, 'noK');

  // gate on, K but no energy for cost
  termStore.K = 2000; termStore.energy = 0;
  W.mineralSend(room);
  assert.strictEqual(Memory.ops.w8min.sendWhy, 'noE');
  assert.ok(Memory.ops.w8min.needE > 0);

  // gate on, ready → send
  termStore.energy = 500;
  sent.length = 0;
  W.mineralSend(room);
  assert.strictEqual(Memory.ops.w8min.sendWhy, 'sent', 'sendWhy=' + Memory.ops.w8min.sendWhy);
  assert.strictEqual(sent.length, 1);
  assert.strictEqual(sent[0][0], 'K');
  assert.strictEqual(sent[0][2], 'W46N8');
  assert.ok(sent[0][1] >= 100 && sent[0][1] <= 5000);

  // 11:4x: thin stor (<LEAN_ARM) → SEND_BATCH_THIN=1000
  room.storage.store.energy = 5000;
  termStore.K = 8000; termStore.energy = 500; sent.length = 0;
  W.mineralSend(room);
  assert.strictEqual(Memory.ops.w8min.sendWhy, 'sent');
  assert.strictEqual(sent[0][1], 1000, 'thin batch=' + sent[0][1]);
  assert.strictEqual(Memory.ops.w8min.batch, 1000);
  assert.ok(Memory.ops.w8min.homeFree >= 100);
  assert.ok(Memory.ops.w8min.fee > 0);
  // full cushion → SEND_BATCH=5000
  room.storage.store.energy = 25000;
  termStore.K = 8000; termStore.energy = 500; sent.length = 0;
  W.mineralSend(room);
  assert.strictEqual(sent[0][1], 5000, 'full batch=' + sent[0][1]);
  assert.strictEqual(Memory.ops.w8min.batch, 5000);
  room.storage.store.energy = 25000;

  // cooldown
  term.cooldown = 5; sent.length = 0;
  W.mineralSend(room);
  assert.strictEqual(Memory.ops.w8min.sendWhy, 'cd');
  assert.strictEqual(sent.length, 0);
  term.cooldown = 0;

  // dayObs: sendOk=1, gaps no longer include send
  Memory.ops.w8layout = 'approved';
  // minimal globals for dayObs towers etc already covered by room.find
  W.dayObs(room);
  const m = Memory.ops.w8min;
  assert.strictEqual(m.sendOk, 1);
  assert.ok(m.gaps.indexOf('send') < 0, 'gaps=' + m.gaps);
  assert.strictEqual(m.hasCode, 1);

  // termFuel: gate off → false; gate on + K waiting + low termE → withdraw storage
  C.RCL6_MINERALS = false;
  assert.strictEqual(roles._termFuel(creep()), false);
  C.RCL6_MINERALS = true;
  termStore.K = 500; termStore.energy = 50;
  const fuelC = creep();
  fuelC.pos.isNearTo = (t) => t === room.storage || (t && t.pos && t.pos.x === 35);
  // creep() isNearTo always true — withdraw storage
  assert.strictEqual(roles._termFuel(fuelC), true);
  assert.deepStrictEqual(fuelC.got, [['w', 'energy']], 'termFuel withdraws energy from storage');
  const fuelC2 = creep({ energy: 200 });
  fuelC2.pos.isNearTo = () => true;
  assert.strictEqual(roles._termFuel(fuelC2), true);
  assert.deepStrictEqual(fuelC2.got, [['t', 'energy']], 'termFuel transfers energy to terminal');

  // 11:4x: thin post-minBuild stor (500–1999) still fuels; below 500 refuses
  room.storage.store.energy = 800;
  termStore.K = 500; termStore.energy = 50;
  const fuelThin = creep();
  fuelThin.pos.isNearTo = (t) => t === room.storage || (t && t.pos && t.pos.x === 35);
  assert.strictEqual(roles._termFuel(fuelThin), true, 'termFuel at stor 800');
  room.storage.store.energy = 400;
  const fuelStarved = creep();
  fuelStarved.pos.isNearTo = (t) => t === room.storage || (t && t.pos && t.pos.x === 35);
  assert.strictEqual(roles._termFuel(fuelStarved), false, 'termFuel refuses stor <500');
  room.storage.store.energy = 25000;

  C.RCL6_MINERALS = false;
}

// 11:4x: threat soft (TH.localOn / w8threat) keeps w8upgrader ≤2 after stor≥LEAN_SOFT.
// Peace / w8threatN-only still spawn the 3rd (no sites → base 3) once the cushion is full.
{
  const savedT = Game.time;
  Game.time = savedT + 100; // bust fill.js duty cache from earlier spawnRuns
  const upBody = Array(10).fill({ type: 'work' }).concat([{ type: 'carry' }, { type: 'move' }, { type: 'move' }]);
  const mk = (role) => ({
    memory: { role, home: C.ROOM },
    ticksToLive: 1000, spawning: false,
    body: role === 'w8upgrader' ? upBody : [{ type: 'work' }, { type: 'work' }, { type: 'work' }, { type: 'work' }, { type: 'work' }, { type: 'work' }, { type: 'move' }],
    getActiveBodyparts(t) { return this.body.filter(p => p.type === t).length; },
    pos: { x: 20, y: 20, inRangeTo: () => false },
  });
  const st = {};
  const put = (x, y, o) => { (st[x * 50 + y] = st[x * 50 + y] || []).push(Object.assign({ pos: { x, y, inRangeTo: () => false } }, o)); };
  put(33, 30, { structureType: 'spawn', store: { energy: 300, getCapacity: () => 300, getFreeCapacity: () => 0 } }); // ORDER.spawn[1]
  put(22, 7, { structureType: 'tower', store: { energy: 900, getFreeCapacity: () => 0 } }); // ORDER.tower[2]
  put(37, 44, { structureType: 'container', store: { energy: 0, getFreeCapacity: () => 2000 } });
  const room = {
    name: C.ROOM, energyAvailable: 2300, energyCapacityAvailable: 2300,
    controller: { level: 7, my: true, ticksToDowngrade: 100000 },
    storage: { store: { energy: 30000 }, pos: { x: 35, y: 32 } },
    terminal: { store: {} }, memory: {},
    lookForAt: (k, x, y) => k === 'structure' ? (st[x * 50 + y] || []) : [],
    find: (k, o) => {
      let a = [];
      if (k === FIND_MY_CREEPS) a = Object.values(Game.creeps);
      return o && o.filter ? a.filter(o.filter) : a;
    },
  };
  let got = null;
  const spawn = {
    room, spawning: null, pos: { x: 34, y: 30, getRangeTo: () => 10 },
    spawnCreep: (b, n, o) => { got = o.memory; return 0; },
  };
  const fleet = (nUp) => {
    const o = {
      a: mk('w8miner'), b: mk('w8miner'),
      c: mk('w8hauler'), d: mk('w8hauler'),
    };
    o.a.memory.si = 0; o.b.memory.si = 1;
    for (let i = 0; i < nUp; i++) o['u' + i] = mk('w8upgrader');
    return o;
  };
  const run = (nUp, stor, ops) => {
    got = null;
    room.storage.store.energy = stor;
    Game.creeps = fleet(nUp);
    const keep = { w8model: Memory.ops.w8model };
    Memory.ops = Object.assign(keep, ops || {});
    W.spawnRun(spawn);
    return got && got.role;
  };
  C.RCL6_MINERALS = true;
  assert.strictEqual(run(2, 30000, {}), 'w8upgrader', 'peace stor≥25k no sites → 3rd upgrader');
  assert.strictEqual(run(2, 30000, { w8threat: Game.time }), null, 'threat soft stor≥25k → stay ≤2');
  assert.strictEqual(run(1, 30000, { w8threat: Game.time }), 'w8upgrader', 'threat soft still fills up to 2');
  assert.strictEqual(run(2, 30000, { w8threatN: Game.time }), 'w8upgrader', 'w8threatN alone does not hold ≤2');
  assert.strictEqual(run(2, 20000, {}), null, 'stor<LEAN_SOFT still ≤2 with threat off');
  assert.strictEqual(W.threatSoft(), false);
  assert.strictEqual(W.softCap2(20000), true);
  assert.strictEqual(W.softCap2(30000), false);
  Memory.ops = { w8model: { links: true, lcarry: 9, rcarry: 49, upw: 31 } };
  Game.time = savedT;
  C.RCL6_MINERALS = false;
}

console.log('w47n8_mminer ok');
