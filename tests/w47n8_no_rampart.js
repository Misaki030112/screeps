// 17:15 (Misaki): W47N8 places no empty-slot rampart via PRIO; 10-31: live KEY covers (tower/spawn/storage/terminal) keep/get sites
const assert = require('assert'), fs = require('fs'), path = require('path');
const d = path.join(__dirname, '..', 'src', 'rooms', 'w47n8');
const idx = fs.readFileSync(path.join(d, 'index.js'), 'utf8'), roles = fs.readFileSync(path.join(d, 'roles.js'), 'utf8');
const prio = idx.match(/const PRIO = \[([^\]]*)\]/)[1];
assert.ok(!/rampart/.test(prio), 'no rampart in PRIO');
// 10-20 13:30 exception: gate; 10-20 15:5x spawn slot; 10-31 KEY covers (placeKeyRamps)
const C8 = require(path.join(d, 'config.js')); assert.deepStrictEqual(C8.GATE, [[29, 3]], 'single gate');
assert.ok(/placeKeyRamps/.test(idx), 'placeKeyRamps present');
assert.ok(/keepRamp/.test(idx), 'keepRamp present');
assert.ok(/createConstructionSite\(x, y, STRUCTURE_RAMPART\)/.test(idx), 'KEY rampart site placement');
assert.ok(/!keepRamp\(room, s\.pos\.x, s\.pos\.y\)/.test(idx), 'unbuilt non-KEY rampart sites removed');
assert.ok(/if \(isGate\(x, y\)\) \{[^\n]*\n[^\n]*\n[^\n]*STRUCTURE_RAMPART/.test(idx), 'rampart site still in the gate branch');
const wl = idx.match(/const wallsLow = [^\n]*/)[0]; assert.ok(!/RAMPART/.test(wl.replace(/STRUCTURE_RAMPART && isGate/g, '')), 'wall mode: gate rampart only');
const wj = roles.slice(roles.indexOf('function wallJob'), roles.indexOf('// ---- W47N7 remote')); assert.ok(!/RAMPART/.test(wj.replace(/STRUCTURE_RAMPART && \(C\.GATE/g, '').replace(/STRUCTURE_WALL \|\| s\.structureType === STRUCTURE_RAMPART\) && s\.pos\.y === 3/, '').replace(/rep\.structureType === STRUCTURE_RAMPART/, '')), 'wallJob seal walls + gate only');
// layout plan lists north tower covers
const L = require(path.join(d, 'layout.js'));
assert.ok(L.ORDER.rampart.some(([x, y]) => x === 24 && y === 8), 'ORDER.rampart includes tower 24,8');
assert.ok(L.ORDER.rampart.some(([x, y]) => x === 22 && y === 7), 'ORDER.rampart includes tower 22,7');
console.log('w47n8 no rampart ok');
// rampHold: first-seen hits become the hold; repair only once 1000 below it; never raised beyond
Object.assign(global, { _: require('lodash'), FIND_MY_STRUCTURES: 1, STRUCTURE_RAMPART: 'rampart', STRUCTURE_TOWER: 'tower', STRUCTURE_STORAGE: 'storage', STRUCTURE_SPAWN: 'spawn', LOOK_STRUCTURES: 'ls', RESOURCE_ENERGY: 'energy', Memory: {}, Game: { time: 1, rooms: {}, creeps: {} } });
const W = require(path.join(d, 'index.js'));
const rs = [{ id: 'a', structureType: 'rampart', hits: 49800 }, { id: 'b', structureType: 'rampart', hits: 2000 }];
const room = { find: () => rs };
assert.strictEqual(W.rampHold(room), null, 'fresh: hold = current, nothing to do');
assert.deepStrictEqual(Memory.ops.w8hold, { a: 49800, b: 2000 });
rs[0].hits = 48900; assert.strictEqual(W.rampHold(room), null, 'within slack');
rs[0].hits = 48700; assert.strictEqual(W.rampHold(room).id, 'a', 'decayed >1000 below hold -> repair');
rs[0].hits = 49900; assert.strictEqual(Memory.ops.w8hold.a, 49800, 'hold never raised'); W.rampHold(room); assert.strictEqual(Memory.ops.w8hold.a, 49800);
rs.pop(); W.rampHold(room); assert.deepStrictEqual(Object.keys(Memory.ops.w8hold), ['a'], 'gone rampart dropped');
console.log('w47n8 rampHold ok');

// 14:4x soft staging; 17:4x SOFT_MIN=0 + peacetime=!localOn (neighbor w8threatN must not block)
const Csoft = require(path.join(d, 'config.js'));
assert.strictEqual(Csoft.GATE_TOWER, 100000, 'GATE_TOWER soft band');
assert.strictEqual(Csoft.SOFT_RAMP, 100000, 'SOFT_RAMP');
assert.strictEqual(Csoft.SOFT_MIN, 0, 'SOFT_MIN 0 (upgrade-first)');
Memory.ops = {}; Game.time = 10;
const rs2 = [
  { id: 'spawnR', structureType: 'rampart', hits: 20000, pos: { x: 34, y: 30 } },
  { id: 'towR', structureType: 'rampart', hits: 48000, pos: { x: 33, y: 35 } },
  { id: 'towN', structureType: 'rampart', hits: 1, pos: { x: 24, y: 8 } },
  { id: 'storR', structureType: 'rampart', hits: 49000, pos: { x: 35, y: 32 } },
];
const structs = [
  { structureType: 'spawn', pos: { x: 34, y: 30 } },
  { structureType: 'tower', pos: { x: 33, y: 35 } },
  { structureType: 'tower', pos: { x: 24, y: 8 } },
  { structureType: 'storage', pos: { x: 35, y: 32 } },
];
const roomSoft = {
  find: () => rs2,
  storage: { store: { energy: 2000 } },
  lookForAt: (k, x, y) => structs.filter(s => s.pos.x === x && s.pos.y === y),
};
// spawn-slot still lifts via GATE_TOWER (critical) even under soft path
assert.strictEqual(W.rampHold(roomSoft).id, 'spawnR', 'spawn below GATE_TOWER always');
rs2[0].hits = 100000;
// 17:4x: SOFT_MIN=0 → low storage still raises soft KEY (upgrade-first economy)
// lowest soft KEY is north tower 24,8 at 1 hit
assert.strictEqual(W.rampHold(roomSoft).id, 'towN', 'SOFT_MIN=0 peacetime: lowest soft KEY is naked tower 24,8');
assert.strictEqual(Memory.ops.w8soft.why, 'ok', 'w8soft.why ok');
assert.strictEqual(Memory.ops.w8soft.storE, 2000, 'w8soft.storE');
assert.strictEqual(Memory.ops.w8soft.tower, 1, 'w8soft.tower tracks min tower cover hits');
// local threat blocks soft raise (neighbor threatN alone must not)
Memory.ops.w8threat = Game.time;
assert.strictEqual(W.rampHold(roomSoft), null, 'local threat: soft raise off');
assert.strictEqual(Memory.ops.w8soft.why, 'threat', 'w8soft.why threat');
delete Memory.ops.w8threat;
Memory.ops.w8threatN = Game.time; // neighbor staging
assert.strictEqual(W.rampHold(roomSoft).id, 'towN', 'neighbor w8threatN alone: soft still raises');
assert.strictEqual(Memory.ops.w8soft.why, 'ok', 'w8soft.why ok under threatN');
delete Memory.ops.w8threatN;
rs2[1].hits = 100000; rs2[2].hits = 100000; rs2[3].hits = 100000;
assert.strictEqual(W.rampHold(roomSoft), null, 'all at SOFT_RAMP: nothing');
assert.strictEqual(Memory.ops.w8hold.towR, 48000, 'hold never raised by soft path');
assert.ok(Memory.ops.w8soft && Memory.ops.w8soft.tgt === 100000, 'w8soft observability');
console.log('w47n8 soft ramp staging ok');

// 11-12: lab/factory covers are held at 300k (not KEY, so the old hold ignored them) and are not raised by w8key.
Memory.ops = {}; Game.time = 50;
global.LOOK_CONSTRUCTION_SITES = 'lc';
global.STRUCTURE_LAB = 'lab'; global.STRUCTURE_FACTORY = 'factory';
const labR = { id: 'labR', structureType: 'rampart', hits: 1, pos: { x: 29, y: 38 } };
const facR = { id: 'facR', structureType: 'rampart', hits: 1, pos: { x: 35, y: 30 } };
const bare = { id: 'bare', structureType: 'rampart', hits: 1, pos: { x: 36, y: 31 } };
const keyRs = [
  { id: 'spawnR', structureType: 'rampart', hits: 100000, pos: { x: 34, y: 30 } },
  { id: 'towR', structureType: 'rampart', hits: 100000, pos: { x: 33, y: 35 } },
  { id: 'storR', structureType: 'rampart', hits: 100000, pos: { x: 35, y: 32 } },
];
const indStructs = [
  { structureType: 'spawn', pos: { x: 34, y: 30 } },
  { structureType: 'tower', pos: { x: 33, y: 35 } },
  { structureType: 'storage', pos: { x: 35, y: 32 } },
  { structureType: 'lab', pos: { x: 29, y: 38 } },
];
const indSites = [{ structureType: 'factory', pos: { x: 35, y: 30 } }];
const indRoom = {
  storage: { store: { energy: 9000 } },
  find: () => keyRs.concat([labR, facR, bare]),
  lookForAt: (k, x, y) => {
    if (k === LOOK_CONSTRUCTION_SITES) return indSites.filter(s => s.pos.x === x && s.pos.y === y);
    return indStructs.filter(s => s.pos.x === x && s.pos.y === y);
  },
};
assert.strictEqual(W.rampNeeded(indRoom, labR), true, 'lab cover is held');
assert.strictEqual(W.rampNeeded(indRoom, facR), true, 'factory site cover is held before the building exists');
assert.strictEqual(W.rampNeeded(indRoom, bare), false, 'empty rampart still decays');
assert.strictEqual(W.rampHold(indRoom).id, labR.id, '1-hit lab cover is repaired (else 300/100t deletes it)');
labR.hits = 100000; facR.hits = 100000;
assert.strictEqual(W.rampHold(indRoom).id, labR.id, 'lowest industry cover continues past SOFT_RAMP');
labR.hits = 300000; facR.hits = 250000;
assert.strictEqual(W.rampHold(indRoom).id, facR.id, 'the cover still under 300k is next');
facR.hits = 300000;
assert.strictEqual(W.rampHold(indRoom), null, 'both covers stop at 300k');
Memory.defense = { w8key: 1000000 };
labR.hits = 300000; facR.hits = 400000;
keyRs.forEach(r => { r.hits = 1000000; });
assert.strictEqual(W.rampHold(indRoom), null, 'w8key=1M does not pull a lab/factory cover past 300k');
facR.hits = 299000;
assert.strictEqual(W.rampHold(indRoom).id, facR.id, 'decay below 300k is repaired again');
Memory.ops.w8threat = Game.time;
facR.hits = 1;
assert.strictEqual(W.rampHold(indRoom).id, facR.id, 'local threat does not let a fresh cover decay away');
delete Memory.ops.w8threat;
delete Memory.defense;
console.log('w47n8 lab/factory 300k hold ok');

// Parent-placed rampart sites over a lab/factory survive layoutRun. Empty rampart sites still go.
// placeKeyRamps does not invent a cover (lab/factory stay out of KEY).
global.STRUCTURE_EXTENSION = 'extension';
global.STRUCTURE_CONTAINER = 'container';
global.STRUCTURE_ROAD = 'road';
global.STRUCTURE_WALL = 'constructedWall';
global.STRUCTURE_LINK = 'link';
global.STRUCTURE_TERMINAL = 'terminal';
global.STRUCTURE_EXTRACTOR = 'extractor';
global.FIND_MY_CONSTRUCTION_SITES = 114;
global.FIND_MY_SPAWNS = 112;
global.FIND_STRUCTURES = 107;
global.FIND_HOSTILE_CREEPS = 3;
global.FIND_MINERALS = 116;
global.OK = 0;
global.ERR_RCL_NOT_ENOUGH = -14;
Game.time = 80;
Game.creeps = {};
const rampSite = { structureType: 'rampart', pos: { x: 29, y: 38 }, remove() { this.gone = true; } };
const facSite = { structureType: 'rampart', pos: { x: 35, y: 30 }, remove() { this.gone = true; } };
const junkSite = { structureType: 'rampart', pos: { x: 10, y: 10 }, remove() { this.gone = true; } };
const labSite = { structureType: 'lab', pos: { x: 29, y: 38 }, progress: 0, progressTotal: 50000 };
const factorySite = { structureType: 'factory', pos: { x: 35, y: 30 }, progress: 0, progressTotal: 100000 };
const liveSites = [rampSite, facSite, junkSite, labSite, factorySite];
const made = [];
const sp = { structureType: 'spawn', my: true, pos: { x: 34, y: 30, inRangeTo: () => false }, store: { energy: 300 } };
const layRoom = {
  name: 'W47N8',
  controller: { level: 7, progress: 0, progressTotal: 1000, ticksToDowngrade: 100000 },
  storage: { store: { energy: 30000 } },
  energyAvailable: 5600, energyCapacityAvailable: 5600,
  memory: {},
  find: (t, o) => {
    let a = [];
    if (t === FIND_MY_CONSTRUCTION_SITES) a = liveSites;
    else if (t === FIND_MY_SPAWNS || t === FIND_MY_STRUCTURES) a = [sp];
    else if (t === FIND_STRUCTURES) a = [sp];
    return o && o.filter ? a.filter(o.filter) : a;
  },
  lookForAt: (k, x, y) => {
    if (k === LOOK_CONSTRUCTION_SITES) return liveSites.filter(s => s.pos.x === x && s.pos.y === y);
    if (x === 34 && y === 30) return [sp];
    return [];
  },
  createConstructionSite: (x, y, t) => { made.push(t + ' ' + x + ',' + y); return OK; },
  getTerrain: () => ({ get: () => 0 }),
};
Memory.ops = { w8layout: 'approved' };
W.layoutRun(layRoom);
assert.ok(!rampSite.gone, 'rampart site over a lab site is kept');
assert.ok(!facSite.gone, 'rampart site over a factory site is kept');
assert.ok(junkSite.gone, 'empty rampart site is still removed');
assert.ok(!labSite.gone && !factorySite.gone, 'lab and factory sites are not rampart-stripped');
assert.ok(!made.some(s => s === 'rampart 29,38' || s === 'rampart 35,30'), 'no auto rampart over the lab or factory: ' + made.join(';'));
const Cfg = require(path.join(d, 'config.js'));
assert.strictEqual(Cfg.RCL7_INDUSTRY, false);
assert.strictEqual(Cfg.RCL6_LABS, false);
console.log('w47n8 lab/factory rampart sites kept ok');
