// Upgrader target (src/managers/spawn.js targets): base 2 (1 with sites); extra ones from the ctl container EMA (1 per 700)
// only when storage holds SURPLUS 1000 above the queen ferry floor max(defender reserve, spawn capacity). No storage: EMA only.
// node tests/spawn_upgraders.js -> exits 1 on failure
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, { RESOURCE_ENERGY: 'energy', STRUCTURE_LINK: 'link', STRUCTURE_CONTAINER: 'container', STRUCTURE_SPAWN: 'spawn', STRUCTURE_EXTENSION: 'extension', STRUCTURE_TOWER: 'tower', _: { filter: () => [] } });
let W;
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
const P = { pos: { upgraders: [[29, 30], [30, 31], [31, 30]], controllerContainer: [30, 30], fillerContainerA: [35, 24], fillers: [], miners: [] }, raw: { stamps: {} }, any: {} };
stub('utils/plan.js', { get: () => P, key: (x, y) => x * 50 + y });
stub('utils/move.js', { to: () => true });
stub('utils/roomcache.js', { all: () => [], at: () => null, get: () => ({ at: [] }), sites: () => [] });
stub('utils/trace.js', { why: () => {} });
stub('managers/threat.js', { reserve: () => W.reserve, holding: () => false });
const S = require(src('managers/spawn.js'));
function up(o) {
  W = Object.assign({ reserve: 1300, storage: 0, ema: 900, sites: 0, hasStorage: true }, o);
  const room = { name: 'W46N8', controller: { level: 4 }, energyCapacityAvailable: 1300, storage: W.hasStorage ? { store: { energy: W.storage } } : undefined };
  return S.targets(room, {}, 0, W.ema, W.sites).upgrader;
}
const cases = [
  ['storage at old gate 1300 (ferry not started) -> 2', () => assert.strictEqual(up({ storage: 1300 }), 2)],
  ['storage 2299 < floor 1300 + 1000 -> 2', () => assert.strictEqual(up({ storage: 2299 }), 2)],
  ['storage 2300 + ctl EMA 900 -> 3', () => assert.strictEqual(up({ storage: 2300 }), 3)],
  ['storage surplus but ctl EMA low -> 2', () => assert.strictEqual(up({ storage: 5000, ema: 300 }), 2)],
  ['higher defender reserve raises the floor', () => { assert.strictEqual(up({ storage: 2300, reserve: 2000 }), 2); assert.strictEqual(up({ storage: 3000, reserve: 2000 }), 3); }],
  ['no storage: EMA only (pre-storage behaviour)', () => assert.strictEqual(up({ hasStorage: false, ema: 1400 }), 3)],
  ['capped by upgrader spots', () => assert.strictEqual(up({ storage: 9000, ema: 5000 }), 3)],
  ['sites: base 1', () => assert.strictEqual(up({ sites: 2, storage: 0 }), 1)],
];
let fail = 0; for (const [n, f] of cases) { try { f(); console.log('ok  ', n); } catch (e) { fail++; console.log('FAIL', n, e.message); } }
console.log(`spawn upgraders: ${cases.length - fail}/${cases.length}`); process.exit(fail ? 1 : 0);
