// Low-bucket creep order + shedding (src/utils/cpuorder.js). node tests/cpu_order.js
const assert = require('assert'), fs = require('fs'), o = require('../src/utils/cpuorder');
const C = { a: { memory: { role: 'w8hauler' } }, b: { memory: { role: 'queen' } }, c: { memory: { role: 'w8defender' } },
  d: { memory: { role: 'upgrader' } }, e: { memory: { role: 'defender' } }, f: { memory: {} } };
assert.deepStrictEqual(o.order(C, 10000), ['a', 'b', 'c', 'd', 'e', 'f']); // normal: untouched
assert.deepStrictEqual(o.order(C, 1999), ['c', 'e', 'b', 'a', 'd', 'f']); // combat, refill, then economy (stable)
assert.strictEqual(o.shed(C.a, 1500, 496, 500), true);
assert.strictEqual(o.shed(C.a, 1500, 400, 500), false);
assert.strictEqual(o.shed(C.c, 100, 999, 500), false); // combat never shed
assert.strictEqual(o.shed(C.b, 100, 999, 500), false); // queen never shed
assert.strictEqual(o.shed(C.a, 10000, 999, 500), false); // full bucket: never
const m = fs.readFileSync(__dirname + '/../src/main.js', 'utf8');
assert(m.includes('cpuorder.order(Game.creeps, Game.cpu.bucket)'), 'main.js must iterate creeps via cpuorder.order');
assert(m.includes('cpuorder.shed(c, Game.cpu.bucket'), 'main.js must shed economy creeps near tickLimit');
console.log('cpu_order ok');
