// 17:15 (Misaki): W47N8 places no rampart sites (drops unbuilt ones) and builders/wall mode raise seal walls only
const assert = require('assert'), fs = require('fs'), path = require('path');
const d = path.join(__dirname, '..', 'src', 'rooms', 'w47n8');
const idx = fs.readFileSync(path.join(d, 'index.js'), 'utf8'), roles = fs.readFileSync(path.join(d, 'roles.js'), 'utf8');
const prio = idx.match(/const PRIO = \[([^\]]*)\]/)[1];
assert.ok(!/rampart/.test(prio), 'no rampart in PRIO');
// 10-20 13:30 exception: only the C.GATE tile (29,3) gets a rampart site; everything else stays rampart-free
const C8 = require(path.join(d, 'config.js')); assert.deepStrictEqual(C8.GATE, [[29, 3]], 'single gate');
assert.strictEqual((idx.match(/createConstructionSite\([^)]*STRUCTURE_RAMPART/g) || []).length, 1, 'one rampart site call (gate)');
assert.ok(/if \(isGate\(x, y\)\) \{[^\n]*\n[^\n]*\n[^\n]*STRUCTURE_RAMPART/.test(idx), 'rampart site only in the gate branch');
assert.ok(/STRUCTURE_RAMPART && !isGate\(s\.pos\.x, s\.pos\.y\) \}\)\) s\.remove\(\)/.test(idx), 'unbuilt non-gate rampart sites removed');
const wl = idx.match(/const wallsLow = [^\n]*/)[0]; assert.ok(!/RAMPART/.test(wl.replace(/STRUCTURE_RAMPART && isGate/g, '')), 'wall mode: gate rampart only');
const wj = roles.slice(roles.indexOf('function wallJob'), roles.indexOf('// ---- W47N7 remote')); assert.ok(!/RAMPART/.test(wj.replace(/STRUCTURE_RAMPART && \(C\.GATE/g, '').replace(/STRUCTURE_WALL \|\| s\.structureType === STRUCTURE_RAMPART\) && s\.pos\.y === 3/, '').replace(/rep\.structureType === STRUCTURE_RAMPART/, '')), 'wallJob seal walls + gate only');
console.log('w47n8 no rampart ok');
// rampHold: first-seen hits become the hold; repair only once 1000 below it; never raised beyond
Object.assign(global, { _: require('lodash'), FIND_MY_STRUCTURES: 1, STRUCTURE_RAMPART: 'rampart', Memory: {}, Game: { time: 1, rooms: {}, creeps: {} } });
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
