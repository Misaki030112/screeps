// RCL5 transition (docs/RCL5.md): with plan.STATIONARY_FILL off the queen regime continues at RCL5 even with 2 links
// (no fillers / manager), link sites are skipped, tower sites come before extensions, and tower rampart growth is throttled.
// node tests/rcl5_gate.js -> exits 1 on failure
const path = require('path'), assert = require('assert'), fs = require('fs');
const src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, { WORK: 'work', CARRY: 'carry', MOVE: 'move', RESOURCE_ENERGY: 'energy', STRUCTURE_LINK: 'link', STRUCTURE_CONTAINER: 'container',
  STRUCTURE_SPAWN: 'spawn', STRUCTURE_EXTENSION: 'extension', STRUCTURE_TOWER: 'tower', STRUCTURE_RAMPART: 'rampart', STRUCTURE_ROAD: 'road', _: { filter: () => [] } });
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
const P = { pos: { upgraders: [[29, 30], [30, 31], [31, 30]], controllerContainer: [30, 30], fillerContainerA: [35, 24], fillers: [], miners: [] }, raw: { stamps: {} }, any: {} };
let FLAG = false, LINKS = 2;
stub('utils/plan.js', { get: () => P, key: (x, y) => x * 50 + y, get STATIONARY_FILL() { return FLAG; } });
stub('utils/move.js', { to: () => true });
stub('utils/roomcache.js', { all: (r, t) => (t === 'link' ? Array(LINKS).fill({}) : []), at: () => null, get: () => ({ at: [] }), sites: () => [] });
stub('utils/trace.js', { why: () => {} });
stub('managers/threat.js', { reserve: () => 1300, holding: () => false });
const S = require(src('managers/spawn.js')), TW = require(src('managers/tower.js'));
const T = (rcl, o = {}) => { FLAG = !!o.flag; LINKS = o.links === undefined ? 2 : o.links;
  return S.targets({ name: 'W46N8', controller: { level: rcl }, energyCapacityAvailable: 1800, storage: { store: { energy: 2000 } } }, {}, 0, 500, 0); };
const ramp = hits => ({ structureType: 'rampart', hits });
const cases = [
  ['flag off, RCL5 + 2 links: queen stays, no fillers/manager', () => { const t = T(5); assert.deepStrictEqual([t.queen, t.filler, t.manager], [1, 0, 0]); }],
  ['flag off, RCL6 + 3 links: still queen, home hauler kept', () => { const t = T(6, { links: 3 }); assert.deepStrictEqual([t.queen, t.filler, t.manager], [1, 0, 0]); assert.ok(t.hauler >= 1); }],
  ['flag on, RCL5 + 2 links: original v2 switch (queen 0, fillers 4, manager 1)', () => { const t = T(5, { flag: true }); assert.deepStrictEqual([t.queen, t.filler, t.manager], [0, 4, 1]); }],
  ['flag on, RCL5 + 1 link: queen until 2 links', () => { const t = T(5, { flag: true, links: 1 }); assert.deepStrictEqual([t.queen, t.filler], [1, 0]); }],
  ['layout: tower before extension; link skipped while flag off', () => { const L = fs.readFileSync(src('managers/layout.js'), 'utf8');
    const pr = eval(L.match(/const PRIORITY = (\[[^\]]+\])/)[1]); assert.ok(pr.indexOf('tower') < pr.indexOf('extension'));
    assert.ok(/type === 'link' && !plan\.STATIONARY_FILL/.test(L)); }],
  ['tower: RCL5 rampart at 60k (above RCL4 50k) repairs only every 5th tick', () => {
    assert.strictEqual(TW.growthPaused(ramp(60000), 5, 101), true); assert.strictEqual(TW.growthPaused(ramp(60000), 5, 100), false); }],
  ['tower: rampart below previous target (fresh/damaged) full speed', () => assert.strictEqual(TW.growthPaused(ramp(30000), 5, 101), false)],
  ['tower: RCL3 (no previous target) and non-ramparts never throttled', () => {
    assert.strictEqual(TW.growthPaused(ramp(15000), 3, 101), false); assert.strictEqual(TW.growthPaused({ structureType: 'road', hits: 4000 }, 5, 101), false); }],
];
let fail = 0; for (const [n, f] of cases) { try { f(); console.log('ok  ', n); } catch (e) { fail++; console.log('FAIL', n, e.message); } }
console.log(`rcl5 gate: ${cases.length - fail}/${cases.length}`); process.exit(fail ? 1 : 0);
