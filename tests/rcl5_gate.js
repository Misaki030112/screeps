// RCL5 transition (docs/RCL5.md): with plan.STATIONARY_FILL off the queen regime continues at RCL5 even with 2 links
// (no fillers / manager), link sites are skipped, tower sites come before extensions, and tower rampart growth is throttled.
// node tests/rcl5_gate.js -> exits 1 on failure
const path = require('path'), assert = require('assert'), fs = require('fs');
const src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, { FIND_HOSTILE_CREEPS: 103, WORK: 'work', CARRY: 'carry', MOVE: 'move', RESOURCE_ENERGY: 'energy', STRUCTURE_LINK: 'link', STRUCTURE_CONTAINER: 'container',
  STRUCTURE_SPAWN: 'spawn', STRUCTURE_EXTENSION: 'extension', STRUCTURE_TOWER: 'tower', STRUCTURE_RAMPART: 'rampart', STRUCTURE_ROAD: 'road', _: { filter: () => [] } });
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
const P = { pos: { upgraders: [[29, 30], [30, 31], [31, 30]], controllerContainer: [30, 30], fillerContainerA: [35, 24], fillers: [], miners: [] }, raw: { stamps: {} }, any: {} };
let FLAG = false, LINKS = 2;
stub('utils/plan.js', { get: () => P, key: (x, y) => x * 50 + y, get STATIONARY_FILL() { return FLAG; } });
stub('roles/builder.js', { remoteRoadSite: () => null }); // remote road builder gate (spawn.targets)
stub('utils/move.js', { to: () => true });
stub('utils/roomcache.js', { all: (r, t) => (t === 'link' ? Array(LINKS).fill({}) : []), at: () => null, get: () => ({ at: [] }), sites: () => [] });
stub('utils/trace.js', { why: () => {} });
stub('managers/threat.js', { reserve: () => 1300, holding: () => false });
const S = require(src('managers/spawn.js')), TW = require(src('managers/tower.js'));
const T = (rcl, o = {}) => { FLAG = !!o.flag; LINKS = o.links === undefined ? 2 : o.links;
  return S.targets({ name: 'W46N8', controller: { level: rcl }, energyCapacityAvailable: 1800, storage: { store: { energy: 2000 } }, memory: {}, find: () => [] }, {}, 0, 500, 0); };
const ramp = hits => ({ structureType: 'rampart', hits });
const cases = [
  ['flag off, RCL5 + 2 links: queen stays, no fillers/manager', () => { const t = T(5); assert.deepStrictEqual([t.queen, t.filler, t.manager], [1, 0, 0]); }],
  ['flag off, RCL6 + 3 links: still queen, home hauler kept', () => { const t = T(6, { links: 3 }); assert.deepStrictEqual([t.queen, t.filler, t.manager], [1, 0, 0]); assert.ok(t.hauler >= 1); }],
  ['flag on, RCL5 + 2 links: original v2 switch (queen 0, fillers 4, manager 1)', () => { const t = T(5, { flag: true }); assert.deepStrictEqual([t.queen, t.filler, t.manager], [0, 4, 1]); }],
  ['flag on, RCL5 + 1 link: queen until 2 links', () => { const t = T(5, { flag: true, links: 1 }); assert.deepStrictEqual([t.queen, t.filler], [1, 0]); }],
  ['layout: tower before extension; link skipped while flag off', () => { const L = fs.readFileSync(src('managers/layout.js'), 'utf8');
    const pr = eval(L.match(/const PRIORITY = (\[[^\]]+\])/)[1]); assert.ok(pr.indexOf('tower') < pr.indexOf('extension'));
    assert.ok(pr.indexOf('extension') < pr.indexOf('link')); }],
  ['builder PRIO: tower before extension (matches layout)', () => { const B = fs.readFileSync(src('roles/builder.js'), 'utf8');
    const m = B.match(/const PRIO = (\{[^}]+\})/); assert.ok(m, 'PRIO missing');
    const pr = eval('('+m[1]+')'); assert.ok(pr.tower < pr.extension, 'tower='+pr.tower+' ext='+pr.extension); }],
  ['tower: RCL5 rampart at 60k (above RCL4 50k) repairs only every 5th tick', () => {
    assert.strictEqual(TW.growthPaused(ramp(60000), 5, 101), true); assert.strictEqual(TW.growthPaused(ramp(60000), 5, 100), false); }],
  ['tower: rampart below previous target (fresh/damaged) full speed', () => assert.strictEqual(TW.growthPaused(ramp(30000), 5, 101), false)],
  ['tower: RCL3 (no previous target) and non-ramparts never throttled', () => {
    assert.strictEqual(TW.growthPaused(ramp(15000), 3, 101), false); assert.strictEqual(TW.growthPaused({ structureType: 'road', hits: 4000 }, 5, 101), false); }],
];
// ---- link plan A (real plan.js + links.js)
cases.push(...(() => {
  delete require.cache[require.resolve(src('utils/plan.js'))]; delete require.cache[require.resolve(src('managers/links.js'))];
  const realPlan = require(src('utils/plan.js'));
  const links = (o) => Object.entries(o).map(([n, [x, y, en, cd]]) => ({ n, pos: { x, y }, store: { energy: en }, cooldown: cd || 0, sent: [], transferEnergy(t) { this.sent.push(t.n); } }));
  const runLinks = (L) => { stub('utils/plan.js', realPlan); stub('utils/roomcache.js', { all: () => L });
    delete require.cache[require.resolve(src('managers/links.js'))]; global.Game = { time: 3 }; require(src('managers/links.js')).run({ name: 'W46N8' }); return L; };
  const up = (r) => realPlan.upTo('W46N8', r).filter(s => s.type === 'link').map(s => [s.x, s.y]).sort();
  return [
    ['plan A: RCL5 links = hub 37,29 + ctl 30,31 (no stamp-A 35,26)', () => assert.deepStrictEqual(up(5), [[30, 31], [37, 29]])],
    ['plan A: RCL6 adds source A 30,11', () => assert.deepStrictEqual(up(6), [[30, 11], [30, 31], [37, 29]])],
    ['links: hub >= SEND sends to low ctl link', () => { const L = runLinks(links({ hub: [37, 29, 600], ctl: [30, 31, 100] })); assert.deepStrictEqual(L[0].sent, ['ctl']); }],
    ['links: ctl link above threshold -> hub holds', () => { const L = runLinks(links({ hub: [37, 29, 800], ctl: [30, 31, 500] })); assert.deepStrictEqual(L[0].sent, []); }],
    ['links: hub below SEND holds', () => { const L = runLinks(links({ hub: [37, 29, 300], ctl: [30, 31, 0] })); assert.deepStrictEqual(L[0].sent, []); }],
    ['links: source A -> ctl when low, else -> hub', () => {
      let L = runLinks(links({ hub: [37, 29, 0], ctl: [30, 31, 0], a: [30, 11, 800] })); assert.deepStrictEqual(L[2].sent, ['ctl']);
      L = runLinks(links({ hub: [37, 29, 0], ctl: [30, 31, 700], a: [30, 11, 800] })); assert.deepStrictEqual(L[2].sent, ['hub']); }],
  ];
})());
let fail = 0; for (const [n, f] of cases) { try { f(); console.log('ok  ', n); } catch (e) { fail++; console.log('FAIL', n, e.message); } }
console.log(`rcl5 gate: ${cases.length - fail}/${cases.length}`); process.exit(fail ? 1 : 0);
