// 2026-10-29 20:4x strategy review: at RCL7 W47N8 must place spawn2 + tower3 + 10 ext, NOT factory (100k) while RCL7_INDUSTRY is off.
// 2026-11-03 HUB_LINK nod: hub link 33,34 (~5k) is planned; labs/industry stay off. Spur roads for the 10 RCL7 extension slots must sit on the kept network.
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
      if (n >= CS[t][rcl]) return ERR_RCL_NOT_ENOUGH;
      const site = { structureType: t, pos: { x, y }, remove() { const i = sites.indexOf(site); if (i >= 0) sites.splice(i, 1); } };
      sites.push(site); return OK; } };
}
assert.strictEqual(C.RCL6_MINERALS, true); assert.strictEqual(C.RCL6_LABS, false); assert.strictEqual(C.HUB_LINK, true); assert.strictEqual(C.RCL7_INDUSTRY, false);
const roads = R.ROADS.filter(([x, y]) => !R.MINERAL.some(([a, b]) => a === x && b === y)).concat(require('../src/layouts/w8link').W47N8);
const base = [].concat(C.SEAL.map(([x, y]) => [x, y, 'wall']), [[34, 30, 'spawn'], [35, 32, 'storage'], [C.HUB_CONT[0], C.HUB_CONT[1], 'container'], [13, 26, 'container']],
  L.ORDER.extension.slice(0, 40).map(([x, y]) => [x, y, 'extension']), [[33, 35, 'tower'], [24, 8, 'tower'], [C.CTL_LINK[0], C.CTL_LINK[1], 'link'], [C.SOURCES[0].link[0], C.SOURCES[0].link[1], 'link']],
  roads.map(([x, y]) => [x, y, 'road']));
const placed = [];
for (let i = 0; i < 12; i++) { const r = mkRoom(7, base.concat(placed.map(s => [s.pos.x, s.pos.y, s.structureType]))); W.layoutRun(r); placed.push(...r.sites); }
const types = placed.map(s => s.structureType);
assert.ok(types.includes('terminal'), 'RCL7 lean: terminal while RCL6_MINERALS on');
assert.ok(types.includes('extractor'), 'RCL7 lean: extractor while RCL6_MINERALS on');
assert.ok(placed.some(s => s.structureType === 'container' && s.pos.x === 37 && s.pos.y === 44), 'RCL7 lean: mineral cont 37,44');
for (const t of ['lab', 'factory', 'powerSpawn', 'nuker', 'observer'])
  assert.ok(!types.includes(t), 'RCL7: no ' + t + ' while labs/industry off, got ' + types.filter(x => x === t));
assert.deepStrictEqual(placed.filter(s => s.structureType === 'link').map(s => s.pos.x + ',' + s.pos.y), ['33,34'], 'RCL7: hub link site 33,34');
assert.ok(placed.some(s => s.structureType === 'spawn' && s.pos.x === 33 && s.pos.y === 30), 'RCL7: spawn2 @33,30');
assert.ok(placed.some(s => s.structureType === 'tower' && s.pos.x === 22 && s.pos.y === 7), 'RCL7: tower3 @22,7');
assert.strictEqual(types.filter(t => t === 'extension').length, 10, 'RCL7: 10 new extensions, got ' + types.filter(t => t === 'extension').length);
// day-of order: spawn+tower before any extension (towerSite holds extensions)
{ const r = mkRoom(7, base); W.layoutRun(r);
  const first = r.sites.map(s => s.structureType + '@' + s.pos.x + ',' + s.pos.y);
  assert.ok(first.includes('spawn@33,30') && first.includes('tower@22,7'), 'day-of first sites: ' + first);
  assert.ok(!first.some(s => s.startsWith('extension')), 'no extensions while tower site stands: ' + first);
}
// RCL7 spur roads serve every new extension slot + tower3
const S = new Set(R.ROADS.map(([x, y]) => x + ',' + y));
const adj = (x, y) => { for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) if (S.has((x + dx) + ',' + (y + dy))) return true; return false; };
for (const [x, y] of L.ORDER.extension.slice(40, 50)) assert.ok(adj(x, y), 'RCL7 ext ' + x + ',' + y + ' orphaned from road plan');
assert.ok(adj(22, 7), 'tower3 22,7 has no adjacent road');
// network stays one piece
{ const SS = new Set(R.ROADS.map(([x, y]) => x * 50 + y)), start = [...SS][0], seen = new Set([start]), st = [start];
  while (st.length) { const k = st.pop(), x = Math.floor(k / 50), y = k % 50;
    for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) { const q = (x + dx) * 50 + y + dy; if (SS.has(q) && !seen.has(q)) { seen.add(q); st.push(q); } } }
  assert.strictEqual(seen.size, SS.size, 'road plan split after RCL7 spurs'); }
// 10-31 19:1x: day-of critical strips extension flood so tower3 can re-queue past the 6-site cap
{ const flooded = mkRoom(7, base);
  for (const [x, y] of L.ORDER.extension.slice(40, 50)) flooded.createConstructionSite(x, y, 'extension');
  assert.strictEqual(flooded.sites.filter(s => s.structureType === 'extension').length, 10, 'pre: 10 ext flood');
  W.layoutRun(flooded);
  assert.ok(!flooded.sites.some(s => s.structureType === 'extension'), 'dayCrit strips ext flood: ' + flooded.sites.map(s => s.structureType));
  assert.ok(flooded.sites.some(s => s.structureType === 'tower' && s.pos.x === 22 && s.pos.y === 7), 'tower3 re-queued after strip');
  assert.ok(flooded.sites.some(s => s.structureType === 'spawn' && s.pos.x === 33 && s.pos.y === 30), 'spawn2 still queued');
}
console.log('w47n8 rcl7 gate ok', placed.length, 'sites across ticks');
