// Final-plan convergence: <=5 containers alive at any RCL, removals only from layout.remove, 6 links by RCL8.
const assert = require('assert');
Object.assign(global, { STRUCTURE_CONTAINER: 'container', STRUCTURE_LINK: 'link', STRUCTURE_STORAGE: 'storage', STRUCTURE_SPAWN: 'spawn', STRUCTURE_TOWER: 'tower', STRUCTURE_TERMINAL: 'terminal', STRUCTURE_CONTROLLER: 'controller', STRUCTURE_RAMPART: 'rampart', STRUCTURE_ROAD: 'road', STRUCTURE_CONTAINER_: 0, EXTENSION_ENERGY_CAPACITY: [], Memory: {}, _: require('lodash') });
const plan = require('../src/utils/plan');
const P = plan.get('W46N8');
for (let r = 1; r <= 8; r++) {
  const c = plan.upTo('W46N8', r).filter(s => s.type === 'container' && !(s.removeAt && r >= s.removeAt));
  assert(c.length <= 5, `RCL${r}: ${c.length} containers`);
}
assert(!P.any[plan.key(30, 27)] || P.any[plan.key(30, 27)].type === 'road', 'filler container 30,27 not planned (v5: road to stamp-C stop 31,26)');
assert.strictEqual(plan.upTo('W46N8', 8).filter(s => s.type === 'link').length, 6);
assert.strictEqual(plan.upTo('W46N8', 6).filter(s => s.type === 'link').length, 3);
assert.strictEqual(P.any[plan.key(38, 32)].removeAt, 4); assert.strictEqual(P.any[plan.key(31, 12)].removeAt, 6);
// obsoleteContainer: only listed containers with a link/storage next to them
const L = require('../src/managers/layout');
const pos = (x, y) => ({ x, y, getRangeTo: o => Math.max(Math.abs(o.x - x), Math.abs(o.y - y)) });
const S = (t, x, y) => ({ structureType: t, pos: pos(x, y) });
assert.strictEqual(L.obsoleteContainer({}, P, 5, [S('container', 34, 34), S('container', 30, 30), S('storage', 37, 31)]), undefined);
assert.deepStrictEqual(L.obsoleteContainer({}, P, 5, [S('container', 38, 32), S('storage', 37, 31)]).pos.x, 38);
assert.strictEqual(L.obsoleteContainer({}, P, 6, [S('container', 31, 12)]), undefined, 'A container kept until its link exists');
assert.strictEqual(L.obsoleteContainer({}, P, 6, [S('container', 31, 12), S('link', 30, 11)]).pos.y, 12);
console.log('containers_links ok');
