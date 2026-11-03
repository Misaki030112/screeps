// 2026-11-03 11:38 strategy: builder prefers owned containers <50% over roads (Overmind WorkerOverlord /
// RoadLogistics critical=25%). Old rr() pooled both → roads starved ctl/hub/minCont at ~25%.
const assert = require('assert'), path = require('path');
const d = path.join(__dirname, '..', 'src', 'rooms', 'w47n8');
const K = {
  LOOK_STRUCTURES: 'structure', LOOK_CREEPS: 'creep', LOOK_CONSTRUCTION_SITES: 'constructionSite',
  FIND_MY_CONSTRUCTION_SITES: 114, FIND_STRUCTURES: 107, FIND_MY_STRUCTURES: 108, FIND_MINERALS: 116,
  FIND_HOSTILE_CREEPS: 103, FIND_MY_CREEPS: 102, FIND_DROPPED_RESOURCES: 106, FIND_SOURCES_ACTIVE: 104,
  FIND_TOMBSTONES: 105, FIND_RUINS: 124,
  STRUCTURE_WALL: 'constructedWall', STRUCTURE_TOWER: 'tower', STRUCTURE_CONTAINER: 'container',
  STRUCTURE_EXTENSION: 'extension', STRUCTURE_SPAWN: 'spawn', STRUCTURE_ROAD: 'road',
  STRUCTURE_RAMPART: 'rampart', STRUCTURE_STORAGE: 'storage', STRUCTURE_LINK: 'link', STRUCTURE_TERMINAL: 'terminal',
  STRUCTURE_EXTRACTOR: 'extractor',
  WORK: 'work', CARRY: 'carry', MOVE: 'move', RESOURCE_ENERGY: 'energy', OK: 0,
};
Object.assign(global, K, {
  _: require('lodash'),
  Memory: { ops: {} },
  Game: { time: 5000, rooms: {}, creeps: {}, spawns: {}, getObjectById: id => Game._objs[id] },
  RoomPosition: function (x, y, r) { this.x = x; this.y = y; this.roomName = r; },
});
Game._objs = {};
const C = require(path.join(d, 'config'));
const R = require(path.join(d, 'roles'));
const W = require(path.join(d, 'index'));
const SG = require(path.join(__dirname, '..', 'src', 'utils', 'sign'));

const rng = (p, q) => Math.max(Math.abs(p.x - q.x), Math.abs(p.y - q.y));
const mkPos = (x, y) => ({
  x, y, roomName: 'W47N8',
  getRangeTo: o => rng({ x, y }, o.pos || o),
  inRangeTo: (o, r, rr) => (typeof o === 'number' ? Math.max(Math.abs(o - x), Math.abs(r - y)) <= rr : rng({ x, y }, o.pos || o) <= r),
  isNearTo: o => rng({ x, y }, o.pos || o) <= 1,
  findClosestByRange(k, o) {
    const a = Array.isArray(k) ? k : room.find(k, o);
    if (!a.length) return null;
    return _.min(a, s => rng({ x, y }, s.pos));
  },
  findInRange: () => [],
});

function S(id, type, x, y, hits, hitsMax) {
  const s = { id, structureType: type, hits, hitsMax: hitsMax || hits, pos: mkPos(x, y), store: { energy: 0 } };
  Game._objs[id] = s;
  return s;
}

const ctlCont = S('ctl', STRUCTURE_CONTAINER, C.CTL_CONT[0], C.CTL_CONT[1], 60000, 250000); // 24%
const hubCont = S('hub', STRUCTURE_CONTAINER, C.HUB_CONT[0], C.HUB_CONT[1], 60000, 250000);
const nearRoad = S('rd', STRUCTURE_ROAD, 13, 27, 1000, 5000); // 20%, on roads.js near ctl
const structs = [ctlCont, hubCont, nearRoad];
for (const [x, y] of C.SEAL) structs.push(S('w' + x + '_' + y, STRUCTURE_WALL, x, y, 400000, 3e8));

let room = {
  name: 'W47N8',
  controller: { level: 7, progress: 1e5, progressTotal: 1e7, pos: mkPos(15, 25), sign: { username: 'Misaki', text: SG.SIGN } },
  storage: { store: { energy: 30000 } },
  energyAvailable: 5600, energyCapacityAvailable: 5600,
  find: (k, o) => {
    const a = (k === FIND_STRUCTURES || k === FIND_MY_STRUCTURES) ? structs
      : k === FIND_MY_CONSTRUCTION_SITES ? []
      : k === FIND_MINERALS ? []
      : k === FIND_HOSTILE_CREEPS ? [] : [];
    return o && o.filter ? a.filter(o.filter) : a.slice();
  },
  lookForAt: (look, x, y) => {
    if (look === LOOK_STRUCTURES) return structs.filter(s => s.pos.x === x && s.pos.y === y);
    if (look === LOOK_CREEPS) return [];
    return [];
  },
};
Game.rooms.W47N8 = room;

let repaired = null;
const builder = {
  name: 'b1', id: 'b1', room,
  pos: mkPos(C.CTL_CONT[0], C.CTL_CONT[1] + 1),
  memory: { role: 'w8builder', home: 'W47N8', w: true },
  store: { energy: 200, getFreeCapacity: () => 0, getCapacity: () => 200 },
  getActiveBodyparts: () => 5,
  repair: s => { repaired = s; return OK; },
  build: () => OK, moveTo: () => OK, move: () => OK, say() {},
};
Game.creeps.b1 = builder;

// force energyBank off so maintenance band is active
const realEB = W.energyBank;
W.energyBank = () => false;

R.w8builder.run(builder);
assert.ok(repaired, 'builder repairs something');
assert.strictEqual(repaired.structureType, STRUCTURE_CONTAINER,
  'prefer container <50% over closer road at 20%; got ' + repaired.structureType + ' hits=' + repaired.hits);
assert.ok(repaired.hits < repaired.hitsMax * 0.5);
assert.strictEqual(builder.memory.rj, repaired.id, 'sticky rj restored');

// --- upgrader: only lexicographically-first standee repairs ctl cont <50%
ctlCont.hits = 60000;
ctlCont.store.energy = 800;
const upgActs = [];
function mkUpg(name, x, y) {
  const c = {
    name, id: name, room, owner: { username: 'Misaki' },
    pos: mkPos(x, y),
    memory: { role: 'w8upgrader', home: 'W47N8', w: true },
    store: { energy: 50, getFreeCapacity: () => 0, getCapacity: () => 50 },
    getActiveBodyparts: p => (p === WORK ? 10 : 1),
    repair: s => { upgActs.push(name + ':repair'); repaired = s; return OK; },
    upgradeController: () => { upgActs.push(name + ':upg'); return OK; },
    withdraw: () => OK, moveTo: () => OK, move: () => OK, say() {},
  };
  return c;
}
const [sx, sy] = C.UPG_STAND[0];
const uA = mkUpg('u_a', sx, sy);
const uB = mkUpg('u_b', C.UPG_STAND[1][0], C.UPG_STAND[1][1]);
Game.creeps = { u_a: uA, u_b: uB };
repaired = null;
R.w8upgrader.run(uA);
R.w8upgrader.run(uB);
const repairs = upgActs.filter(a => a.endsWith(':repair'));
assert.strictEqual(repairs.length, 1, 'exactly one upgrader repairs: ' + JSON.stringify(upgActs));
assert.ok(upgActs.some(a => a.endsWith(':upg')), 'sibling still upgrades: ' + JSON.stringify(upgActs));
assert.strictEqual(repaired.id, 'ctl');

// --- 14:4x: critical roads <25% outrank deep seal wallJob (containers already ≥50%)
ctlCont.hits = 130000; // 52%
hubCont.hits = 130000;
nearRoad.hits = nearRoad.hitsMax; // healthy far road — must not distract
const sealRoad = S('rds', STRUCTURE_ROAD, 25, 7, 950, 5000); // 19%, beside north seal (live roadCrit sample)
structs.push(sealRoad);
builder.memory.rj = undefined;
builder.memory.rjt = 0;
builder.pos = mkPos(25, 6); // beside seal wall — old order would sticky-fortify forever
repaired = null;
Game.creeps = { b1: builder };
Game.time = 5100;
R.w8builder.run(builder);
assert.ok(repaired, 'builder repairs with healthy containers');
assert.strictEqual(repaired.structureType, STRUCTURE_ROAD,
  'prefer road <25% over deep seal wallJob; got ' + repaired.structureType + ' hits=' + (repaired && repaired.hits));
assert.strictEqual(repaired.id, 'rds');

// sticky fortify must break when roadCrit appears
const sealWall = structs.find(s => s.structureType === STRUCTURE_WALL && s.pos.y === 3);
assert.ok(sealWall, 'seal wall fixture');
builder.memory.rj = sealWall.id;
builder.memory.rjt = Game.time + 100; // sticky not expired
repaired = null;
R.w8builder.run(builder);
assert.strictEqual(repaired && repaired.structureType, STRUCTURE_ROAD,
  'break sticky seal when roadCrit; got ' + (repaired && repaired.structureType));
assert.strictEqual(repaired.id, 'rds');

// --- dayObs repair-debt fields (restore container debt fixtures from 11:3x)
ctlCont.hits = 60000;
hubCont.hits = 60000;
Game.creeps = {};
Game.time = 6000;
W.dayObs(room);
assert.ok(Memory.ops.w8day.contMinPct <= 25, 'contMinPct=' + Memory.ops.w8day.contMinPct);
assert.ok(Memory.ops.w8day.contLow >= 2, 'contLow=' + Memory.ops.w8day.contLow);
assert.ok(typeof Memory.ops.w8day.roadCrit === 'number');
assert.ok(Memory.ops.w8day.roadCrit >= 1, 'roadCrit counts sealRoad: ' + Memory.ops.w8day.roadCrit);

W.energyBank = realEB;
console.log('ok w47n8_repair_prio');
