// 10-20 18:0x (Misaki 17:55): W47N8 kept roads form ONE 8-connected network and reach the gate 29,3 and both north wall segments (range 3)
const assert = require('assert'), R = require('../src/rooms/w47n8/roads.js');
const S = new Set(R.ROADS.map(([x, y]) => x * 50 + y)), seen = new Set([[...S][0]]), st = [[...S][0]];
while (st.length) { const k = st.pop(), x = Math.floor(k / 50), y = k % 50;
  for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) { const q = (x + dx) * 50 + y + dy; if (S.has(q) && !seen.has(q)) { seen.add(q); st.push(q); } } }
assert.strictEqual(seen.size, S.size, 'road plan split: ' + (S.size - seen.size) + ' tiles not connected');
assert.ok(S.has(29 * 50 + 3), 'gate 29,3 road kept');
const near = xs => xs.every(wx => R.ROADS.some(([x, y]) => Math.max(Math.abs(x - wx), Math.abs(y - 3)) <= 3));
assert.ok(near([8, 9, 10, 11]) && near([24, 25, 26, 27, 28, 29, 30, 31]), 'every north wall tile within repair range of a kept road');
console.log('w47n8 roads connected ok', S.size);
// 10-20 18:1x (Misaki 18:08): inter-room exit corridors must stay in the plan: east link to W46N8 (w8link 38,30..48,23) and south to W47N7
const EX = { W46N8: [[38, 30], [39, 30], [40, 31], [41, 30], [42, 29], [43, 28], [44, 27], [45, 26], [46, 25], [47, 24], [48, 23]], W47N7: [[17, 47], [18, 48], [18, 49]] };
for (const r in EX) for (const [x, y] of EX[r]) assert.ok(S.has(x * 50 + y), 'exit corridor to ' + r + ' missing ' + x + ',' + y);
const LK = require('../src/layouts/w8link.js');
assert.ok(LK.W46N8.some(([x, y]) => x === 1 && y === 23), 'home leg of the W47N8 link starts at W46N8 1,23');
console.log('w47n8 exit corridors ok');
