// 2026-10-29 23:4x strategy: RCL6 labs must have planned ramparts (live soft-target gap).
const assert = require('assert');
const L = require('../src/layouts/W46N8');
const labs6 = L.rcl['6'].lab;
const ramps6 = L.rcl['6'].rampart;
assert.ok(labs6 && labs6.length >= 3, 'RCL6 has labs');
for (const [x, y] of labs6) {
  assert.ok(ramps6.some(([a, b]) => a === x && b === y), `RCL6 lab ${x},${y} missing rampart`);
}
const labs7 = L.rcl['7'].lab || [];
const ramps7 = L.rcl['7'].rampart || [];
for (const [x, y] of labs7) {
  assert.ok(ramps7.some(([a, b]) => a === x && b === y), `RCL7 lab ${x},${y} missing rampart`);
}
const labs8 = L.rcl['8'].lab || [];
const ramps8 = L.rcl['8'].rampart || [];
for (const [x, y] of labs8) {
  assert.ok(ramps8.some(([a, b]) => a === x && b === y), `RCL8 lab ${x},${y} missing rampart`);
}
assert.strictEqual(L.counts.rampart, 37, 'rampart count includes lab covers');
console.log('lab_ramparts ok');

// 11-12: new lab/factory covers repair to 300k and stop. The three built RCL6 labs stay on the RCL7 1M target.
const path = require('path');
Object.assign(global, {
  _: require('lodash'),
  LOOK_STRUCTURES: 'structure', LOOK_CONSTRUCTION_SITES: 'constructionSite',
  FIND_STRUCTURES: 1, FIND_MY_CONSTRUCTION_SITES: 2, FIND_HOSTILE_CREEPS: 3, FIND_MY_CREEPS: 4,
  STRUCTURE_RAMPART: 'rampart', STRUCTURE_ROAD: 'road', STRUCTURE_CONTAINER: 'container',
  STRUCTURE_TOWER: 'tower', STRUCTURE_WALL: 'constructedWall', STRUCTURE_SPAWN: 'spawn', STRUCTURE_LAB: 'lab',
  RESOURCE_ENERGY: 'energy', OK: 0,
  Memory: {}, Game: { time: 10, creeps: {}, rooms: {}, cpu: { bucket: 10000 } },
});
const TW = require(path.join(__dirname, '..', 'src', 'managers', 'tower.js'));
const ramp = (x, y, hits) => ({ id: `r${x}_${y}`, structureType: 'rampart', pos: { x, y }, hits, hitsMax: 300000000 });
const rcl7 = 1000000;
assert.strictEqual(TW.coverTarget({ name: 'W46N8', lookForAt: () => [] }, ramp(35, 30, 1), rcl7), 300000, 'factory 35,30 cap 300k');
assert.strictEqual(TW.coverTarget({ name: 'W46N8', lookForAt: () => [] }, ramp(34, 23, 1), rcl7), 300000, 'new lab 34,23 cap 300k');
assert.strictEqual(TW.coverTarget({ name: 'W46N8', lookForAt: () => [] }, ramp(33, 22, 200000), rcl7), 300000, 'new lab still capped under 300k');
assert.strictEqual(TW.coverTarget({ name: 'W46N8', lookForAt: () => [] }, ramp(34, 20, 300000), rcl7), 300000, 'at 300k the cap stays 300k');
for (const [x, y] of [[34, 22], [35, 21], [33, 21]]) {
  assert.strictEqual(TW.coverTarget({ name: 'W46N8', lookForAt: () => [] }, ramp(x, y, 1000000), rcl7), rcl7, `legacy lab ${x},${y} stays on 1M`);
  assert.strictEqual(TW.coverTarget({ name: 'W46N8', lookForAt: () => [] }, ramp(x, y, 865000), rcl7), rcl7, `legacy lab ${x},${y} at rampHW still 1M`);
}
assert.strictEqual(TW.coverTarget({ name: 'W46N8', lookForAt: () => [] }, ramp(35, 28, 1000), rcl7), rcl7, 'spawn cover is not capped');
const offPlan = { name: 'W46N8', lookForAt: (k, x, y) => (k === 'structure' && x === 12 && y === 12 ? [{ structureType: 'factory' }] : []) };
assert.strictEqual(TW.coverTarget(offPlan, ramp(12, 12, 50), rcl7), 300000, 'factory structure off the plan is still a 300k cover');
assert.strictEqual(TW.IND_RAMP, 300000);
assert.strictEqual(TW.IND_LEGACY, 500000, 'gap so one repair tick cannot promote a 300k cover onto the 1M path');

// Tower scan: a 1-hit factory cover is the repair target and is excluded from the rampHW ratchet.
const byId = {};
const spawnR = ramp(35, 28, 1000000), labR = ramp(34, 22, 1000000), facR = ramp(35, 30, 1000);
const tower = { id: 'tw', structureType: 'tower', pos: { x: 36, y: 29 }, hits: 3000, hitsMax: 3000, store: { energy: 1000 }, repair() {}, heal() {}, attack() {} };
const lab = { id: 'lab', structureType: 'lab', pos: { x: 34, y: 22 } };
const spawn = { id: 'sp', structureType: 'spawn', pos: { x: 35, y: 28 } };
let structs = [spawnR, labR, facR, tower, lab, spawn];
for (const s of structs) byId[s.id] = s;
Game.getObjectById = id => byId[id] || null;
const cells = {};
for (const s of [lab, spawn]) (cells[s.pos.x * 50 + s.pos.y] = cells[s.pos.x * 50 + s.pos.y] || []).push(s);
const room = {
  name: 'W46N8', controller: { level: 7, my: true }, memory: {},
  storage: { store: { energy: 50000 } },
  lookForAt: (k, x, y) => (k === LOOK_STRUCTURES ? (cells[x * 50 + y] || []) : []),
  find: t => t === FIND_STRUCTURES ? structs : [],
};
const T = require(path.join(__dirname, '..', 'src', 'managers', 'tower.js'));
T.run(room);
assert.strictEqual(room.memory.towerRep, facR.id, 'fresh factory cover is repaired');
assert.strictEqual(room.memory.rampFloorRep, undefined, 'floor repair stays off while the cover is under its cap');
assert.ok(room.memory.rampHW >= 865000, 'rampHW follows the legacy covers, not the 1-hit factory: ' + room.memory.rampHW);
facR.hits = 300000;
Game.time = 40;
T.run(room);
assert.strictEqual(room.memory.towerRep, undefined, 'factory cover stops at 300k');
assert.ok(!room.memory.rampFloorRep, 'rampHW does not pull the 300k cover up: ' + room.memory.rampFloorRep);
labR.hits = 999000;
Game.time = 60;
T.run(room);
assert.strictEqual(room.memory.towerRep, labR.id, 'legacy lab still climbs toward 1M');

// Operator-placed lab/factory sites are kept. RCL7_INDUSTRY stays off, so nothing queues them.
Object.assign(global, {
  STRUCTURE_STORAGE: 'storage', STRUCTURE_TERMINAL: 'terminal', STRUCTURE_CONTROLLER: 'controller',
  STRUCTURE_LINK: 'link', STRUCTURE_EXTENSION: 'extension', STRUCTURE_FACTORY: 'factory',
  STRUCTURE_EXTRACTOR: 'extractor', STRUCTURE_OBSERVER: 'observer', STRUCTURE_NUKER: 'nuker',
  STRUCTURE_POWER_SPAWN: 'powerSpawn', STRUCTURE_LAB: 'lab',
  ERR_RCL_NOT_ENOUGH: -14, ERR_FULL: -8, ERR_INVALID_TARGET: -7,
});
const plan = require(path.join(__dirname, '..', 'src', 'utils', 'plan.js'));
assert.strictEqual(plan.RCL7_INDUSTRY, false);
const layout = require(path.join(__dirname, '..', 'src', 'managers', 'layout.js'));
const kept = { id: 'facsite', structureType: 'factory', pos: { x: 35, y: 30 }, progress: 0, progressTotal: 100000, remove() { this.gone = true; } };
const dropped = { id: 'junk', structureType: 'lab', pos: { x: 1, y: 1 }, progress: 0, progressTotal: 50000, remove() { this.gone = true; } };
// 1,1 is not a lab tile and has no lab structure — wait, structureType lab means indSite keeps it.
// A road site off-plan is the removal case. A factory site is the keep case.
dropped.structureType = 'road';
const homeSites = [kept, dropped];
const homeStructs = [{ id: 'st', structureType: 'storage', pos: { x: 37, y: 31 }, store: { energy: 20000 } }, spawn];
Game.time = 25;
const home = {
  name: 'W46N8', controller: { level: 7 }, memory: {},
  storage: { store: { energy: 20000 } },
  energyCapacityAvailable: 5600,
  find: t => t === FIND_STRUCTURES ? homeStructs : t === FIND_MY_CONSTRUCTION_SITES ? homeSites : [],
  lookForAt: () => [],
  createConstructionSite() { return 0; },
};
layout.run(home);
assert.ok(!kept.gone, 'factory site at 35,30 is kept while RCL7_INDUSTRY is off');
assert.ok(dropped.gone, 'off-plan road site is still removed');
console.log('lab/factory rampart cap ok');
