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
