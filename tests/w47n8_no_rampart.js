// 17:15 (Misaki): W47N8 places no rampart sites (drops unbuilt ones) and builders/wall mode raise seal walls only
const assert = require('assert'), fs = require('fs'), path = require('path');
const d = path.join(__dirname, '..', 'src', 'rooms', 'w47n8');
const idx = fs.readFileSync(path.join(d, 'index.js'), 'utf8'), roles = fs.readFileSync(path.join(d, 'roles.js'), 'utf8');
const prio = idx.match(/const PRIO = \[([^\]]*)\]/)[1];
assert.ok(!/rampart/.test(prio), 'no rampart in PRIO');
// 10-20 13:30 exception: only the C.GATE tile (29,3) gets a rampart site; everything else stays rampart-free
const C8 = require(path.join(d, 'config.js')); assert.deepStrictEqual(C8.GATE, [[29, 3]], 'single gate');
// 10-20 15:5x second exception: the spawn-move target slot (34,30) gets its rampart before the spawn site (necessary rampart)
assert.strictEqual((idx.match(/createConstructionSite\([^)]*STRUCTURE_RAMPART/g) || []).length, 2, 'rampart site calls: gate + spawn slot');
assert.ok(/if \(isGate\(x, y\)\) \{[^\n]*\n[^\n]*\n[^\n]*STRUCTURE_RAMPART/.test(idx), 'rampart site only in the gate branch');
assert.ok(/STRUCTURE_RAMPART && !isGate\(s\.pos\.x, s\.pos\.y\) && !\(s\.pos\.x === L\.ORDER\.spawn\[0\]\[0\] && s\.pos\.y === L\.ORDER\.spawn\[0\]\[1\]\) \}\)\) s\.remove\(\)/.test(idx), 'unbuilt non-gate rampart sites removed');
const wl = idx.match(/const wallsLow = [^\n]*/)[0]; assert.ok(!/RAMPART/.test(wl.replace(/STRUCTURE_RAMPART && isGate/g, '')), 'wall mode: gate rampart only');
const wj = roles.slice(roles.indexOf('function wallJob'), roles.indexOf('// ---- W47N7 remote')); assert.ok(!/RAMPART/.test(wj.replace(/STRUCTURE_RAMPART && \(C\.GATE/g, '').replace(/STRUCTURE_WALL \|\| s\.structureType === STRUCTURE_RAMPART\) && s\.pos\.y === 3/, '').replace(/rep\.structureType === STRUCTURE_RAMPART/, '')), 'wallJob seal walls + gate only');
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
  { id: 'storR', structureType: 'rampart', hits: 49000, pos: { x: 35, y: 32 } },
];
const structs = [
  { structureType: 'spawn', pos: { x: 34, y: 30 } },
  { structureType: 'tower', pos: { x: 33, y: 35 } },
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
assert.strictEqual(W.rampHold(roomSoft).id, 'towR', 'SOFT_MIN=0 peacetime: lowest soft KEY raised at stor 2k');
assert.strictEqual(Memory.ops.w8soft.why, 'ok', 'w8soft.why ok');
assert.strictEqual(Memory.ops.w8soft.storE, 2000, 'w8soft.storE');
// local threat blocks soft raise (neighbor threatN alone must not)
Memory.ops.w8threat = Game.time;
assert.strictEqual(W.rampHold(roomSoft), null, 'local threat: soft raise off');
assert.strictEqual(Memory.ops.w8soft.why, 'threat', 'w8soft.why threat');
delete Memory.ops.w8threat;
Memory.ops.w8threatN = Game.time; // neighbor staging
assert.strictEqual(W.rampHold(roomSoft).id, 'towR', 'neighbor w8threatN alone: soft still raises');
assert.strictEqual(Memory.ops.w8soft.why, 'ok', 'w8soft.why ok under threatN');
delete Memory.ops.w8threatN;
rs2[1].hits = 100000; rs2[2].hits = 100000;
assert.strictEqual(W.rampHold(roomSoft), null, 'all at SOFT_RAMP: nothing');
assert.strictEqual(Memory.ops.w8hold.towR, 48000, 'hold never raised by soft path');
assert.ok(Memory.ops.w8soft && Memory.ops.w8soft.tgt === 100000, 'w8soft observability');
console.log('w47n8 soft ramp staging ok');
