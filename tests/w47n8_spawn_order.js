// 14:57: spawn energy order (hub first, Spawn2 + temp exts last), hauler fill order, RCL7 temp-extension swap, RCL7 hub spawn site
const assert = require('assert'), path = require('path');
Object.assign(global, { _: require('lodash'), FIND_MY_STRUCTURES: 10, FIND_MY_CONSTRUCTION_SITES: 1, FIND_MY_SPAWNS: 2, FIND_MY_CREEPS: 3, FIND_STRUCTURES: 5,
  STRUCTURE_EXTENSION: 'extension', STRUCTURE_SPAWN: 'spawn', STRUCTURE_TOWER: 'tower', STRUCTURE_ROAD: 'road', STRUCTURE_RAMPART: 'rampart', STRUCTURE_CONTAINER: 'container',
  STRUCTURE_STORAGE: 'storage', STRUCTURE_WALL: 'constructedWall', RESOURCE_ENERGY: 'energy', LOOK_STRUCTURES: 'ls', LOOK_CONSTRUCTION_SITES: 'lc', OK: 0, ERR_RCL_NOT_ENOUGH: -14,
  WORK: 'work', CARRY: 'carry', MOVE: 'move', ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack', HEAL: 'heal', TOUGH: 'tough', CLAIM: 'claim', FIND_HOSTILE_CREEPS: 4,
  Memory: { ops: { w8layout: 'approved' } }, Game: { time: 1000, rooms: {}, creeps: {} } });
const W = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'index.js'));
const L = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'layout.js'));
const RL = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'roles.js'));
let id = 0; const pos = (x, y) => ({ x, y, roomName: 'W47N8', getRangeTo: o => Math.max(Math.abs(x - (o.pos || o).x), Math.abs(y - (o.pos || o).y)), inRangeTo: (o, r) => Math.max(Math.abs(x - (o.pos || o).x), Math.abs(y - (o.pos || o).y)) <= r,
  findClosestByRange: a => _.min(a, o => Math.max(Math.abs(x - o.pos.x), Math.abs(y - o.pos.y))) });
const S = []; const mk = (t, x, y, free = 50) => { const s = { id: 's' + id++, structureType: t, my: true, pos: pos(x, y), store: { energy: 0, getFreeCapacity: () => free }, destroy() { this.dead = true; return 0; } }; S.push(s); return s; };
const spawn2 = mk('spawn', 15, 18); for (const [x, y] of L.TEMP_EXT) mk('extension', x, y);
const hubE = L.ORDER.extension.slice(0, 45).map(([x, y]) => mk('extension', x, y));
const sites = [];
const room = { name: 'W47N8', energyAvailable: 5600, energyCapacityAvailable: 5600, controller: { level: 7, my: true }, storage: { store: { energy: 60000 } },
  find: (t, o) => (t === 10 || t === 5 ? S.filter(s => !s.dead) : t === 1 ? sites : t === 2 ? [spawn2] : []).filter(o && o.filter || (() => true)),
  lookForAt: (k, x, y) => (k === 'ls' ? S.filter(s => !s.dead && s.pos.x === x && s.pos.y === y) : sites.filter(s => s.pos.x === x && s.pos.y === y)),
  getTerrain: () => ({ get: () => 0 }), createConstructionSite: (x, y, t) => { sites.push({ structureType: t, pos: pos(x, y) }); return 0; } };
// (1) spawn energy order
const ord = W.energyOrder(room), idx = s => ord.indexOf(s);
assert.strictEqual(ord.length, S.length, 'every extension/spawn included');
const tempIdx = S.filter(s => s.structureType === 'extension' && L.TEMP_EXT.some(([x, y]) => s.pos.x === x && s.pos.y === y)).map(idx);
assert.ok(Math.min(idx(spawn2), ...tempIdx) > Math.max(...hubE.map(idx)), 'Spawn2 + temp exts drawn last');
assert.ok(idx(hubE.find(s => s.pos.x === 32 && s.pos.y === 31)) < idx(hubE[44]), 'nearest core first');
// hauler fill order: a hauler next to Spawn2 still goes to a hub extension first
Game.rooms.W47N8 = room; const hc = { id: 'h', memory: {}, room: Object.assign({}, room, { find: (t, o) => (t === 3 ? [] : room.find(t, o)) }), pos: pos(16, 17) };
const ft = RL._fill ? RL._fill(hc) : null;
if (RL._fill) assert.ok(!(ft.pos.x === 15 && ft.pos.y === 18) && !L.TEMP_EXT.some(([x, y]) => ft.pos.x === x && ft.pos.y === y), 'hauler fills hub first: ' + JSON.stringify(ft.pos));
// (2) swap gates
const hubSpawn = () => mk('spawn', 34, 30);
assert.strictEqual(W.swapTemp(room), null, 'no hub spawn 34,30 -> no swap');
hubSpawn(); room.storage.store.energy = 40000; assert.strictEqual(W.swapTemp(room), null, 'storage <= 50k -> no swap');
room.storage.store.energy = 60000; room.energyAvailable = 5000; assert.strictEqual(W.swapTemp(room), null, 'spawn energy not full -> no swap');
room.energyAvailable = 5600; sites.push({ structureType: 'extension', pos: pos(1, 1) }); assert.strictEqual(W.swapTemp(room), null, 'pending extension site -> wait');
sites.length = 0;
const slot = W.swapTemp(room); assert.deepStrictEqual(slot, L.ORDER.extension[45], 'next unbuilt v3b slot');
assert.ok(S.find(s => s.pos.x === L.TEMP_EXT[0][0] && s.pos.y === L.TEMP_EXT[0][1]).dead, 'first temp ext destroyed (one at a time)');
assert.strictEqual(S.filter(s => s.dead).length, 1, 'only one'); assert.ok(!spawn2.dead, 'Spawn2 kept');
// (3) RCL7 layout places hub spawn 34,30 first when missing
S.splice(S.indexOf(S.find(s => s.structureType === 'spawn' && s.pos.x === 32)), 1); sites.length = 0; Game.time = 2000;
for (const x of [24, 25, 26, 27, 28, 29, 30, 31, 8, 9, 10, 11]) mk('constructedWall', x, 3); mk('container', 33, 33);
W.layoutRun(room); assert.ok(sites.some(s => s.structureType === 'spawn' && s.pos.x === 34 && s.pos.y === 30), 'RCL7: spawn site 34,30 placed');
console.log('w47n8 spawn order ok');
