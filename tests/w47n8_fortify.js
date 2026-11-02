// 11-02 16:2x (Misaki t375u "加固城防，尤其面对他那一方"): Memory.defense knobs lift the W47N8 north seal (w8seal, up to
// WALL_TARGET[rcl]=1M at RCL7) and KEY ramparts (w8key), each behind a storage gate; far towers skip high repairs.
const assert = require('assert'), fs = require('fs'), path = require('path');
const d = path.join(__dirname, '..', 'src', 'rooms', 'w47n8');
Object.assign(global, { _: require('lodash'), FIND_MY_STRUCTURES: 1, FIND_STRUCTURES: 2, STRUCTURE_RAMPART: 'rampart', STRUCTURE_TOWER: 'tower', STRUCTURE_STORAGE: 'storage',
  STRUCTURE_SPAWN: 'spawn', STRUCTURE_WALL: 'constructedWall', LOOK_STRUCTURES: 'ls', RESOURCE_ENERGY: 'energy', Memory: { ops: {} }, Game: { time: 10, rooms: {}, creeps: {} } });
const TH = require(path.join(d, 'threat')), C = require(path.join(d, 'config')), W = require(path.join(d, 'index.js'));
// --- seal cap
Memory.ops.w8move = { phase: 'done' };
assert.strictEqual(TH.planTarget(7, C.WALL_TARGET[7]), 300000, 'no knob: old 300k cap');
Memory.defense = { w8seal: 1000000 };
assert.strictEqual(TH.planTarget(7, C.WALL_TARGET[7]), 1000000, 'w8seal=1M at RCL7 -> 1M');
assert.strictEqual(TH.planTarget(7, 2000000), 1000000, 'knob caps above base');
assert.strictEqual(TH.planTarget(6, 300000), 300000, 'clamped to base (never below STAGE3)');
assert.strictEqual(TH.planTarget(5, 100000), 300000, 'RCL5 behaviour unchanged');
assert.strictEqual(TH.planTarget(4, 50000), 50000);
Memory.defense.w8seal = 200000; assert.strictEqual(TH.planTarget(7, 1000000), 300000, 'knob below STAGE3 ignored (never lowers)');
Memory.ops.w8move.phase = 'prep'; Memory.defense.w8seal = 1000000; assert.strictEqual(TH.planTarget(7, 1000000), 100000, 'move pending still 100k');
delete Memory.ops.w8move;
assert.strictEqual(TH.sealMinE(), 25000, 'default = LEAN_SOFT'); Memory.defense.w8sealMinE = 4000; assert.strictEqual(TH.sealMinE(), 4000); delete Memory.defense.w8sealMinE;
// spawn rule 6 soft-gates deep raise via sealDeepOk (+ SEAL_EDGE intensity)
const idx = fs.readFileSync(path.join(d, 'index.js'), 'utf8');
assert.ok(/TH\.sealDeepOk\(storS\)/.test(idx), 'builder spawn: deep raise uses sealDeepOk');
assert.ok(/TH\.SEAL_EDGE/.test(idx), 'builder spawn: SEAL_EDGE intensity for 2nd builder');
assert.ok(/updateSealPark/.test(idx), 'spawnRun refreshes sticky seal park');
// --- KEY soft target
const rs = [{ id: 'spawnR', structureType: 'rampart', hits: 300000, pos: { x: 34, y: 30 } },
  { id: 'towN', structureType: 'rampart', hits: 120000, pos: { x: 24, y: 8 } },
  { id: 'storR', structureType: 'rampart', hits: 100500, pos: { x: 35, y: 32 } }];
const structs = [{ structureType: 'spawn', pos: { x: 34, y: 30 } }, { structureType: 'tower', pos: { x: 24, y: 8 } }, { structureType: 'storage', pos: { x: 35, y: 32 } }];
const room = { find: () => rs, storage: { store: { energy: 9000 } }, lookForAt: (k, x, y) => structs.filter(s => s.pos.x === x && s.pos.y === y) };
assert.strictEqual(W.rampHold(room), null, 'no w8key: KEY at >=100k not raised');
Memory.defense.w8key = 300000;
assert.strictEqual(W.rampHold(room).id, 'storR', 'w8key=300k, storage 9k >= 8k: lowest KEY raised');
assert.strictEqual(Memory.ops.w8soft.tgt, 300000);
room.storage.store.energy = 7000;
assert.strictEqual(W.rampHold(room), null, 'storage below w8keyMinE: back to SOFT_RAMP');
Memory.defense.w8keyMinE = 6000; assert.strictEqual(W.rampHold(room).id, 'storR', 'w8keyMinE knob');
Memory.ops.w8threat = Game.time; assert.strictEqual(W.rampHold(room), null, 'local threat: towers keep energy for combat');
// --- tower range filter
assert.ok(/r\.hits < \(C\.GATE_TOWER \|\| 0\) \|\| [^\n]*getRangeTo\(r\) <= KEY_REP_R\)\) t\.repair\(r\)/.test(idx), 'towers: above GATE_TOWER only within KEY_REP_R');
// --- wallJob deep raise gated by sealDeepOk (11-02 17:4x + 11-03 02:4x soft-gate)
const R = require(path.join(d, 'roles.js'));
Memory.defense = { w8seal: 1000000 };
delete Memory.ops.w8sealPark;
delete Memory.ops.w8threat; // KEY test left localOn sticky — softThin must be clear for peacetime sealDeepOk
const sealWall = { id: 'sw1', structureType: 'constructedWall', hits: 310000, pos: { x: 10, y: 3 } };
const roomLow = {
  controller: { level: 7 },
  storage: { store: { energy: 20000 } },
  find: (t, o) => (o && o.filter ? [sealWall].filter(o.filter) : [sealWall]),
};
assert.strictEqual(R._wallJob(roomLow, null), null, 'stor < sealMinE: wallJob caps at STAGE3, seal@310k idle');
roomLow.storage.store.energy = 25000;
assert.strictEqual(R._wallJob(roomLow, null).id, 'sw1', 'stor >= sealMinE 25k + park clear: wallJob aims at w8seal=1M');
// 02:4x: softCap2 still parks deep seal even when Memory sealMinE override is below LEAN_SOFT
Memory.defense.w8sealMinE = 5000;
roomLow.storage.store.energy = 6000;
assert.strictEqual(R._wallJob(roomLow, null), null, 'override 5k at stor 6k still softCap-parked (no deep seal under softCap2)');
delete Memory.defense.w8sealMinE;
// sticky park: stor fat but w8sealPark held until nUp recovers
roomLow.storage.store.energy = 30000;
Memory.ops.w8sealPark = 1;
assert.strictEqual(R._wallJob(roomLow, null), null, 'sticky w8sealPark clamps deep seal at stor 30k');
assert.strictEqual(TH.sealDeepOk(30000), false, 'sealDeepOk false while parked');
TH.updateSealPark(30000, 3, 0);
assert.strictEqual(Memory.ops.w8sealPark, 0, 'park clears when softThin off + nUp>=base');
assert.strictEqual(R._wallJob(roomLow, null).id, 'sw1', 'after park clear deep seal resumes');
// threat soft at fat storage parks deep seal
Memory.ops.w8threat = Game.time;
assert.strictEqual(TH.sealDeepOk(30000), false, 'local threat softThin parks deep seal');
assert.strictEqual(R._wallJob(roomLow, null), null, 'threat soft: wallJob caps at STAGE3');
delete Memory.ops.w8threat;
delete Memory.ops.w8sealPark;
console.log('w47n8 fortify ok');
