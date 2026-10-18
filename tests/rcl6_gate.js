// RCL6 mineral/market block (docs/RCL6.md, strategy review 10-15): with plan.RCL6_MINERALS off, RCL6 plans only the
// source-A link + 10 extensions; terminal / labs / extractor / mineral container are not planned. node tests/rcl6_gate.js
const path = require('path'), assert = require('assert');
const plan = require(path.join(__dirname, '..', 'src', 'utils', 'plan.js'));
const at = r => plan.upTo('W46N8', r);
const count = (r, t) => at(r).filter(s => s.type === t).length;
const cases = [
  ['gate ON (Misaki 10-18 09:30)', () => assert.strictEqual(plan.RCL6_MINERALS, true)],
  ['RCL6: terminal 35,31, extractor 40,24, 3 labs, mineral container 41,24 (off the 39,24 haul road)', () => { assert.strictEqual(count(6, 'terminal'), 1); assert.strictEqual(count(6, 'extractor'), 1); assert.strictEqual(count(6, 'lab'), 3);
    assert.ok(at(6).some(s => s.type === 'container' && s.x === 41 && s.y === 24)); }],
  ['RCL6: no mineral container 39,24', () => assert.ok(!at(6).some(s => s.type === 'container' && s.x === 39 && s.y === 24))],
  ['RCL6 new structures = source-A link 30,11 + 10 extensions', () => {
    const n = at(6).filter(s => s.rcl === 6); assert.strictEqual(n.filter(s => s.type !== 'road').length, 17); assert.strictEqual(n.filter(s => s.type === 'road').length, 9, 'v5 filler-tile roads (32,34 is the RCL8 link: plan drops it)');
    assert.deepStrictEqual(n.filter(s => s.type === 'link').map(s => [s.x, s.y]), [[30, 11]]);
    assert.strictEqual(n.filter(s => s.type === 'extension').length, 10); }],
  ['RCL6 extension total 40 (controller limit)', () => assert.strictEqual(count(6, 'extension'), 40)],
  ['RCL6 build energy (ext + link) <= 35k', () => { const C = { extension: 3000, link: 5000 };
    const e = at(6).filter(s => s.rcl === 6).reduce((t, s) => t + (C[s.type] || 0), 0); assert.ok(e <= 35000, e); }],
];
let fail = 0;
for (const [n, f] of cases) { try { f(); console.log('ok  ', n); } catch (e) { fail++; console.log('FAIL', n, e.message); } }
process.exit(fail ? 1 : 0);
