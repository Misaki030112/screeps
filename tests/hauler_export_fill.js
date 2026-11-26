// Home hauler RCL8 export fill (src/roles/hauler.js exportFill): storage -> terminal from the manager tile, sticky memory.xf.
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, { RESOURCE_ENERGY: 'energy', Game: { time: 100, creeps: {}, getObjectById: () => null }, _: require('lodash') });
let W;
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
stub('utils/move.js', { to: (c, x, y) => { W.moved = [x, y]; return W.arrived; } });
stub('roles/queen.js', { fillRoute: () => false });
stub('utils/plan.js', { get: () => ({}), key: (x, y) => x * 50 + y });
stub('utils/roomcache.js', { at: () => null, all: () => [] });
stub('utils/trace.js', { why: () => {} });
stub('utils/salvage.js', { dump: () => false, retire: () => false, pick: () => null });
stub('managers/export.js', { HOME: 'W46N8', fillAmount: () => W.amt });
const H = require(src('roles/hauler.js'));
function mk(o, mem, e = 0) {
  W = Object.assign({ arrived: true, amt: 3000 }, o);
  const room = { name: 'W46N8', storage: { id: 'st', pos: { x: 37, y: 31 } }, terminal: { id: 'tm', pos: { x: 35, y: 31 } } };
  const c = { room, memory: Object.assign({ home: 'W46N8' }, mem), store: { energy: e, getCapacity: () => 800 },
    withdraw: (t, r, a) => { W.took = [t.id, a]; return 0; }, transfer: (t) => { W.gave = t.id; return 0; } };
  return { c, room };
}
const cases = [
  ['idle + fillAmount 3000 -> withdraws min(cap, 3000) from storage, xf set', () => { const { c, room } = mk({}); assert.strictEqual(H.exportFill(c, room, true), true); assert.deepStrictEqual(W.took, ['st', 800]); assert.strictEqual(c.memory.xf, 1); }],
  ['fillAmount 300 (<400) -> no trip', () => { const { c, room } = mk({ amt: 300 }); assert.strictEqual(H.exportFill(c, room, true), false); assert.strictEqual(c.memory.xf, undefined); }],
  ['carrying non-empty -> no start', () => { const { c, room } = mk({}, {}, 50); assert.strictEqual(H.exportFill(c, room, true), false); }],
  ['working hauler -> no start', () => { const { c, room } = mk({}, { working: true }); assert.strictEqual(H.exportFill(c, room, true), false); }],
  ['not the start slot -> no start', () => { const { c, room } = mk({}); assert.strictEqual(H.exportFill(c, room, false), false); }],
  ['xf + energy -> delivers to the terminal and clears xf', () => { const { c, room } = mk({}, { xf: 1 }, 800); assert.strictEqual(H.exportFill(c, room, false), true); assert.strictEqual(W.gave, 'tm'); assert.strictEqual(c.memory.xf, undefined); }],
  ['xf + walking -> keeps xf', () => { const { c, room } = mk({ arrived: false }, { xf: 1 }, 800); assert.strictEqual(H.exportFill(c, room, false), true); assert.strictEqual(c.memory.xf, 1); assert.deepStrictEqual(W.moved, [35, 31]); }],
  ['xf but empty (withdraw failed) -> clears xf, falls through', () => { const { c, room } = mk({}, { xf: 1 }, 0); assert.strictEqual(H.exportFill(c, room, false), false); assert.strictEqual(c.memory.xf, undefined); }],
  ['other home -> never', () => { const { c, room } = mk({}, { home: 'W47N8' }); assert.strictEqual(H.exportFill(c, room, true), false); }],
];
let fail = 0; for (const [n, f] of cases) { try { f(); console.log('ok  ', n); } catch (e) { fail++; console.log('FAIL', n, e.message); } }
console.log(`hauler export fill: ${cases.length - fail}/${cases.length}`); process.exit(fail ? 1 : 0);
