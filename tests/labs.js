// Lab scaffold (managers/labs.js): dormant without flag, output = lab in range 2 of both, reaction + task. node tests/labs.js
const path = require('path'), assert = require('assert');
Object.assign(global, { FIND_MY_STRUCTURES: 108, STRUCTURE_LAB: 'lab', OK: 0, Memory: {} });
const L = require(path.join(__dirname, '..', 'src', 'managers', 'labs.js'));
let ran = 0;
const lab = (id, x, y, store = {}) => ({ id, structureType: 'lab', store, cooldown: 0, pos: { x, y, getRangeTo: o => Math.max(Math.abs(o.pos.x - x), Math.abs(o.pos.y - y)) }, runReaction: () => (ran++, 0) });
const mk = (s1, s2, s3, term = {}) => { const labs = [lab('o', 34, 22, s1), lab('a', 33, 21, s2), lab('b', 35, 21, s3)];
  return { name: 'W46N8', labs, terminal: { id: 't', store: term }, find: () => labs }; };
let r = mk({}, { K: 100 }, { O: 100 });
assert.strictEqual(L.run(r), 0, 'no flag -> dormant'); assert.strictEqual(L.task(r, r.labs), null);
Memory.ops = { labs: { W46N8: 'KO' } };
assert.strictEqual(L.roles(r.labs).out.id, 'o', 'output 34,22'); assert.deepStrictEqual(L.roles(r.labs).ins.map(l => l.id), ['a', 'b']);
assert.strictEqual(L.run(r), 1, 'reacts'); assert.strictEqual(ran, 1);
r = mk({}, { K: 3 }, { O: 100 }); assert.strictEqual(L.run(r), 0, 'short reagent');
r = mk({}, {}, {}, { K: 500, O: 30000 }); assert.deepStrictEqual(L.task(r, r.labs), { from: 't', to: 'a', res: 'K' }, 'load K');
r = mk({}, { O: 50 }, {}, { K: 500 }); assert.deepStrictEqual(L.task(r, r.labs), { from: 'a', to: 't', res: 'O' }, 'empty wrong');
r = mk({ KO: 1500 }, { K: 2000 }, { O: 2000 }); assert.deepStrictEqual(L.task(r, r.labs), { from: 'o', to: 't', res: 'KO' }, 'unload output');
Memory.ops = { labs: { W46N8: 'XX' } }; assert.strictEqual(L.cfg(r), null, 'unknown compound ignored');
console.log('labs ok');
