// 2026-10-19 strategy review: at RCL5 W47N8 queues tower 2 before the 10 new extensions and nothing new while a tower site stands
const assert = require('assert'), path = require('path');
const d = path.join(__dirname, '..', 'src', 'rooms', 'w47n8');
const K = { LOOK_STRUCTURES: 'structure', LOOK_CONSTRUCTION_SITES: 'constructionSite', FIND_MY_SPAWNS: 112, FIND_MY_CONSTRUCTION_SITES: 114,
  FIND_MY_STRUCTURES: 108, OK: 0, ERR_RCL_NOT_ENOUGH: -14 };
const T = ['spawn', 'extension', 'road', 'wall', 'rampart', 'link', 'storage', 'tower', 'observer', 'powerSpawn', 'extractor', 'lab', 'terminal', 'container', 'nuker', 'factory'];
for (const t of T) K['STRUCTURE_' + (t === 'powerSpawn' ? 'POWER_SPAWN' : t.toUpperCase())] = t;
const CS = { spawn: [0, 1, 1, 1, 1, 1, 1, 2, 3], extension: [0, 0, 5, 10, 20, 30, 40, 50, 60], tower: [0, 0, 0, 1, 1, 2, 2, 3, 6], link: [0, 0, 0, 0, 0, 2, 3, 4, 6],
  storage: [0, 0, 0, 0, 1, 1, 1, 1, 1], container: Array(9).fill(5), road: Array(9).fill(2500), wall: [0, 0, 2500, 2500, 2500, 2500, 2500, 2500, 2500],
  rampart: [0, 0, 2500, 2500, 2500, 2500, 2500, 2500, 2500], terminal: [0, 0, 0, 0, 0, 0, 1, 1, 1], extractor: [0, 0, 0, 0, 0, 0, 1, 1, 1],
  lab: [0, 0, 0, 0, 0, 0, 3, 6, 10], factory: [0, 0, 0, 0, 0, 0, 0, 1, 1], powerSpawn: Array(8).fill(0).concat([1]), nuker: Array(8).fill(0).concat([1]), observer: Array(8).fill(0).concat([1]) };
Object.assign(global, K, { _: require('lodash'), CONTROLLER_STRUCTURES: CS, Memory: { ops: { w8layout: 'approved' } }, Game: { time: 20, rooms: {}, creeps: {} } });
const L = require(path.join(d, 'layout')), C = require(path.join(d, 'config')), W = require(path.join(d, 'index.js'));
function mkRoom(rcl, built) { // built: [[x,y,type]]
  const st = {}, sites = [];
  const add = (x, y, t) => (st[x * 50 + y] = st[x * 50 + y] || []).push({ structureType: t, pos: { x, y } });
  for (const [x, y, t] of built) add(x, y, t);
  return { sites, controller: { level: rcl },
    find: (k, o) => { const a = k === FIND_MY_SPAWNS ? [{}] : k === FIND_MY_CONSTRUCTION_SITES ? sites : []; return o && o.filter ? a.filter(o.filter) : a; },
    lookForAt: (k, x, y) => k === LOOK_STRUCTURES ? (st[x * 50 + y] || []) : sites.filter(s => s.pos.x === x && s.pos.y === y),
    createConstructionSite(x, y, t) {
      const n = Object.values(st).flat().filter(s => s.structureType === t).length + sites.filter(s => s.structureType === t).length;
      if (n >= CS[t][rcl]) return ERR_RCL_NOT_ENOUGH; sites.push({ structureType: t, pos: { x, y }, remove() {} }); return OK; } };
}
const base = [].concat(C.SEAL.map(([x, y]) => [x, y, 'wall']), [[15, 18, 'spawn'], [35, 32, 'storage'], [C.HUB_CONT[0], C.HUB_CONT[1], 'container']],
  L.ORDER.extension.slice(0, 20).map(([x, y]) => [x, y, 'extension']), [[L.ORDER.tower[0][0], L.ORDER.tower[0][1], 'tower']]);
// RCL5 just reached: only the tower site goes up
let room = mkRoom(5, base); W.layoutRun(room);
assert.deepStrictEqual(room.sites.map(s => s.structureType), ['tower'], 'RCL5: tower 2 alone first, got ' + room.sites.map(s => s.structureType));
assert.deepStrictEqual([room.sites[0].pos.x, room.sites[0].pos.y], L.ORDER.tower[1]);
W.layoutRun(room); assert.strictEqual(room.sites.length, 1, 'nothing new while the tower site stands');
// tower 2 built -> extensions (and the rest) resume
room = mkRoom(5, base.concat([[L.ORDER.tower[1][0], L.ORDER.tower[1][1], 'tower']])); W.layoutRun(room);
assert.ok(room.sites.filter(s => s.structureType === 'extension').length >= 5, 'extensions after tower: ' + room.sites.map(s => s.structureType));
// RCL4 (tower cap reached): unchanged behaviour, no tower site, extensions not blocked
room = mkRoom(4, base.filter(b => b[2] !== 'extension' || L.ORDER.extension.slice(0, 18).some(([x, y]) => x === b[0] && y === b[1]))); W.layoutRun(room);
assert.ok(!room.sites.some(s => s.structureType === 'tower') && room.sites.filter(s => s.structureType === 'extension').length === 2, 'RCL4 ext refill: ' + room.sites.map(s => s.structureType));
console.log('w47n8 tower first ok');
