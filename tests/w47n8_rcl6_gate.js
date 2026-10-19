// 2026-10-20 03:4x strategy review: at RCL6 W47N8 must not place terminal / extractor / labs / extractor trunk / hub link 33,34
// while config RCL6_MINERALS / HUB_LINK are off (no code uses them); extensions + the 2 planned links still go up.
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
const L = require(path.join(d, 'layout')), C = require(path.join(d, 'config')), W = require(path.join(d, 'index.js')), R = require(path.join(d, 'roads'));
function mkRoom(rcl, built) {
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
// RCL6 with everything RCL5 built (30 ext, 2 towers, 2 links) and every target road built: run layout until it stops placing
const roads = R.ROADS.filter(([x, y]) => !R.MINERAL.some(([a, b]) => a === x && b === y)).concat(require('../src/layouts/w8link').W47N8);
const base = [].concat(C.SEAL.map(([x, y]) => [x, y, 'wall']), [[15, 18, 'spawn'], [35, 32, 'storage'], [C.HUB_CONT[0], C.HUB_CONT[1], 'container'], [13, 26, 'container']],
  L.ORDER.extension.slice(0, 30).map(([x, y]) => [x, y, 'extension']), [[33, 35, 'tower'], [24, 8, 'tower'], [C.CTL_LINK[0], C.CTL_LINK[1], 'link'], [C.SOURCES[0].link[0], C.SOURCES[0].link[1], 'link']],
  roads.map(([x, y]) => [x, y, 'road']));
assert.strictEqual(C.RCL6_MINERALS, false); assert.strictEqual(C.HUB_LINK, false);
const placed = [];
for (let i = 0; i < 6; i++) { const r = mkRoom(6, base.concat(placed.map(s => [s.pos.x, s.pos.y, s.structureType]))); W.layoutRun(r); placed.push(...r.sites); }
const types = placed.map(s => s.structureType);
for (const t of ['terminal', 'extractor', 'lab']) assert.ok(!types.includes(t), 'RCL6: no ' + t + ' site while RCL6_MINERALS is off, got ' + types);
assert.ok(!placed.some(s => s.structureType === 'link'), 'RCL6: no hub link 33,34 while HUB_LINK is off');
assert.ok(!placed.some(s => s.structureType === 'road' && R.MINERAL.some(([a, b]) => a === s.pos.x && b === s.pos.y)), 'RCL6: no extractor trunk road');
assert.strictEqual(types.filter(t => t === 'extension').length, 10, 'RCL6: the 10 new extensions still go up, got ' + types);
// RCL5 unchanged: both planned links are placed (ctl 13,25 + source A 26,12)
{ const b5 = base.filter(b => b[2] !== 'link'); const r = mkRoom(5, b5); W.layoutRun(r);
  const ls = r.sites.filter(s => s.structureType === 'link').map(s => s.pos.x + ',' + s.pos.y).sort();
  assert.deepStrictEqual(ls, ['13,25', '26,12'], 'RCL5 links unchanged: ' + ls); }
console.log('w47n8 rcl6 gate ok');
