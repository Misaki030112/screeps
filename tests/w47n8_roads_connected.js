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
