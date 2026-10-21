// idle guard/defender tiles never on gate 29,3, the tile inside it 29,4, or kept roads. node tests/w8_idle_offpath.js
const assert = require('assert'); global._ = require('lodash');
const D = require('../src/rooms/w47n8/defense.js');
const bad = new Set(['29,3', '29,4', '28,4', '26,5', '27,5']);
assert.ok(!bad.has(D.GHOLD.x + ',' + D.GHOLD.y));
for (const [x, y] of D.IDLE) assert.ok(!bad.has(x + ',' + y) && !(x >= 30 && x <= 31 && y >= 4 && y <= 5), x + ',' + y);
const p = D.guardPlan({ pos: { x: 29, y: 4 }, hits: 100, hitsMax: 100 }, [], {});
assert.strictEqual(p.move, 'post'); assert.deepStrictEqual([p.goal.x, p.goal.y], [29, 5]);
console.log('w8 idle offpath ok');
