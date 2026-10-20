// 2026-10-21 02:4x strategy review (docs/PLAN_W47N8.md "RCL6 extensions"): the 10 RCL6 extension slots (ORDER.extension 30-39, after the
// 30 built at RCL5) must each touch a tile of the pruned road plan v4 (roads.js ROADS + w8link), so queens refill them from kept roads.
// Old order put 28,26 37,39 39,39 27,24 there, whose stand tiles (27-28,25 / 38,37-38) the v4 cut lets decay.
const assert = require('assert'), path = require('path');
const L = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'layout'));
const R = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'roads'));
const roads = new Set(R.ROADS.concat(require('../src/layouts/w8link').W47N8).map(([x, y]) => x + ',' + y));
const rcl6 = L.ORDER.extension.slice(30, 40);
for (const [x, y] of rcl6) {
  let ok = false; for (let a = -1; a <= 1; a++) for (let b = -1; b <= 1; b++) if ((a || b) && roads.has((x + a) + ',' + (y + b))) ok = true;
  assert.ok(ok, 'RCL6 ext ' + x + ',' + y + ' has no planned road neighbour');
}
assert.strictEqual(new Set(L.ORDER.extension.map(String)).size, 60, '60 unique ext slots');
console.log('w47n8 rcl6 ext roads ok');
