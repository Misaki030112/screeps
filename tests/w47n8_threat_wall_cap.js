// 2026-10-20 06:3x strategy review: under threat mode (W47N9 camp keeps w8threatN fresh) the seal walls go ahead of sites and
// upgrading only up to the 50k threat floor. At RCL5 WALL_TARGET is 100k; the old code put that whole raise (~60k energy) ahead of
// tower 24,8 and capped upgraders at 1-2. The per-RCL target above 50k stays a surplus job.
const assert = require('assert'), path = require('path');
const d = path.join(__dirname, '..', 'src', 'rooms', 'w47n8');
const K = { LOOK_STRUCTURES: 'structure', LOOK_CONSTRUCTION_SITES: 'constructionSite', FIND_MY_CONSTRUCTION_SITES: 114, FIND_STRUCTURES: 107,
  FIND_HOSTILE_CREEPS: 103, FIND_MY_CREEPS: 102, FIND_DROPPED_RESOURCES: 106, FIND_SOURCES_ACTIVE: 104, FIND_MY_STRUCTURES: 108,
  STRUCTURE_WALL: 'constructedWall', STRUCTURE_TOWER: 'tower', STRUCTURE_CONTAINER: 'container', STRUCTURE_EXTENSION: 'extension',
  STRUCTURE_SPAWN: 'spawn', STRUCTURE_ROAD: 'road', STRUCTURE_RAMPART: 'rampart', STRUCTURE_STORAGE: 'storage', STRUCTURE_LINK: 'link',
  ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack', HEAL: 'heal', WORK: 'work', CARRY: 'carry', MOVE: 'move', TOUGH: 'tough', RESOURCE_ENERGY: 'energy', OK: 0 };
const T0 = 1000;
Object.assign(global, K, { _: require('lodash'), Memory: { ops: { w8threatN: T0 - 10 } }, Game: { time: T0, rooms: {}, creeps: {}, spawns: {} },
  RoomPosition: function (x, y, r) { this.x = x; this.y = y; this.roomName = r; this.inRangeTo = (a, b, rr) => Math.max(Math.abs(a - x), Math.abs(b - y)) <= rr; } });
const C = require(path.join(d, 'config')), TH = require(path.join(d, 'threat')), R = require(path.join(d, 'roles'));
const rng = (p, q) => Math.max(Math.abs(p.x - q.x), Math.abs(p.y - q.y));
const mkPos = (x, y) => ({ x, y, roomName: 'W47N8', getRangeTo: o => rng({ x, y }, o.pos || o), inRangeTo: (o, r, rr) => (typeof o === 'number' ? Math.max(Math.abs(o - x), Math.abs(r - y)) <= rr : rng({ x, y }, o.pos || o) <= r),
  isNearTo: o => rng({ x, y }, o.pos || o) <= 1, findClosestByRange(k, o) { const a = Array.isArray(k) ? k : room.find(k, o); return _.min(a, s => rng({ x, y }, s.pos)) === Infinity ? null : (a.length ? _.min(a, s => rng({ x, y }, s.pos)) : null); },
  findInRange: () => [] });
function mkRoom(rcl, wallHits, sites) {
  const walls = C.SEAL.map(([x, y]) => ({ id: 'w' + x, structureType: STRUCTURE_WALL, hits: wallHits, pos: mkPos(x, y) }));
  return { name: 'W47N8', controller: { level: rcl }, storage: null, sites,
    find: (k, o) => { const a = k === FIND_STRUCTURES ? walls : k === FIND_MY_CONSTRUCTION_SITES ? sites : []; return o && o.filter ? a.filter(o.filter) : a; },
    lookForAt: () => [] };
}
let room = mkRoom(5, 50001, [{ id: 'tw', structureType: STRUCTURE_TOWER, pos: mkPos(24, 8) }]); Game.rooms.W47N8 = room;
assert.ok(TH.on(), 'threat mode on (fresh w8threatN)');
assert.strictEqual(TH.urgentTarget(), 50000, 'urgent wall target under threat = 50k floor');
assert.strictEqual(R._wallJob(room, null, TH.urgentTarget()), null, 'RCL5 seal walls at 50k: nothing urgent');
assert.ok(R._wallJob(room, null), 'RCL5 seal walls below 100k still a (surplus) job');
// builder with energy at RCL5 under threat: builds tower 24,8 instead of raising walls to 100k
let built = null, repaired = null;
const c = { name: 'b1', id: 'b1', room, pos: mkPos(24, 10), memory: { role: 'w8builder', w: true }, store: { energy: 100, getFreeCapacity: () => 0 },
  build: s => (built = s), repair: s => (repaired = s), moveTo: () => 0, getActiveBodyparts: () => 5 };
R.w8builder.run(c);
assert.ok(built && built.id === 'tw' && !repaired, 'builder builds tower 24,8 first under threat at RCL5 (built=' + (built && built.id) + ' repaired=' + (repaired && repaired.id) + ')');
// below the 50k floor the walls still go first under threat
room = mkRoom(5, 30000, [{ id: 'tw', structureType: STRUCTURE_TOWER, pos: mkPos(24, 8) }]); Game.rooms.W47N8 = room; built = repaired = null;
c.room = room; c.memory = { role: 'w8builder', w: true }; c.pos = mkPos(25, 5);
R.w8builder.run(c);
assert.ok(repaired && !built, 'seal walls under 50k still go ahead of sites under threat');
// spawn side: wall mode (1-2 upgraders) uses the floor, not the RCL target
const idx = require('fs').readFileSync(path.join(d, 'index.js'), 'utf8');
assert.ok(/const wallsLow = [^\n]*TH\.urgentTarget\(\)/.test(idx), 'wallsLow threshold uses TH.urgentTarget()');
console.log('w47n8 threat wall cap ok');
