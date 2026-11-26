// RCL8 export W46N8 -> W47N8 (src/managers/export.js, roles/hauler.js exportFill). node tests/rcl8_export.js -> exits 1 on failure
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, { RESOURCE_ENERGY: 'energy', OK: 0, FIND_HOSTILE_CREEPS: 103, Memory: {}, Game: { time: 100, rooms: {}, creeps: {}, market: {} }, _: require('lodash') });
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
let S = {};
stub('managers/threat.js', { holding: () => !!S.hold });
stub('managers/home.js', { alert: () => !!S.alert });
const X = require(src('managers/export.js'));
const box = (e, free) => ({ store: { energy: e, getFreeCapacity: () => free } });
function world(o = {}) {
  S = o; Memory.ops = o.ops || {};
  const home = { name: 'W46N8', controller: { my: true, level: o.hl || 8, ticksToDowngrade: o.ttd || 199000 }, storage: box(o.hs ?? 30000, 1e6),
    terminal: Object.assign(box(o.ht ?? 0, o.htFree ?? 200000), { cooldown: o.cd || 0, send: (r, a, to) => { S.sent = [r, a, to]; return 0; } }),
    find: () => (o.hostiles ? [{}] : []) };
  const col = { name: 'W47N8', controller: { my: true, level: o.cl || 7 }, storage: box(o.cs ?? 20000, 1e6), terminal: box(o.ct ?? 1000, o.ctFree ?? 280000) };
  Game.rooms = { W46N8: home, W47N8: col }; return { home, col };
}
const cases = [
  ['exporting: home RCL8 + colony RCL7 with terminals', () => { world(); assert.strictEqual(X.exporting(), true); }],
  ['exporting off: console switch', () => { world({ ops: { export: false } }); assert.strictEqual(X.exporting(), false); }],
  ['exporting off: colony reached RCL8', () => { world({ cl: 8 }); assert.strictEqual(X.exporting(), false); }],
  ['exporting off: home not RCL8', () => { world({ hl: 7 }); assert.strictEqual(X.exporting(), false); }],
  ['homeUpgrade8: exporting, timer healthy -> 0', () => { const { home } = world(); assert.strictEqual(X.homeUpgrade8(home), 0); }],
  ['homeUpgrade8: exporting, timer < 100k -> 1 guard', () => { const { home } = world({ ttd: 99999 }); assert.strictEqual(X.homeUpgrade8(home), 1); }],
  ['homeUpgrade8: colony RCL8 -> back to 1', () => { const { home } = world({ cl: 8 }); assert.strictEqual(X.homeUpgrade8(home), 1); }],
  ['fillAmount: storage 19999 -> 0 (15k cushion + build band first)', () => { const { home } = world({ hs: 19999 }); assert.strictEqual(X.fillAmount(home), 0); }],
  ['fillAmount: storage 21000 -> keeps 18k (3000)', () => { const { home } = world({ hs: 21000 }); assert.strictEqual(X.fillAmount(home), 3000); }],
  ['fillAmount: storage 40000, terminal 2500 -> tops up to 6000', () => { const { home } = world({ hs: 40000, ht: 2500 }); assert.strictEqual(X.fillAmount(home), 3500); }],
  ['fillAmount: hostiles in home -> 0', () => { const { home } = world({ hs: 40000, hostiles: 1 }); assert.strictEqual(X.fillAmount(home), 0); }],
  ['fillAmount: remote defence holding -> 0', () => { const { home } = world({ hs: 40000, hold: 1 }); assert.strictEqual(X.fillAmount(home), 0); }],
  ['fillAmount: colony full (150k) -> 0', () => { const { home } = world({ hs: 40000, cs: 149500, ct: 500 }); assert.strictEqual(X.fillAmount(home), 0); }],
  ['run: terminal 5200 -> sends 5000 energy to W47N8', () => { world({ ht: 5200 }); Game.time = 105; X.run(); assert.deepStrictEqual(S.sent, ['energy', 5000, 'W47N8']); assert.strictEqual(Memory.ops.exportStat.n, 1); assert.strictEqual(Memory.ops.exportStat.fee, 164); }],
  ['run: off-tick -> nothing', () => { world({ ht: 9000 }); Game.time = 106; X.run(); assert.strictEqual(S.sent, undefined); }],
  ['run: terminal below batch+fee -> waits', () => { world({ ht: 5100 }); Game.time = 110; X.run(); assert.strictEqual(S.sent, undefined); }],
  ['run: cooldown -> waits', () => { world({ ht: 9000, cd: 3 }); Game.time = 110; X.run(); assert.strictEqual(S.sent, undefined); }],
  ['run: colony terminal nearly full -> colTermFull', () => { world({ ht: 9000, ctFree: 12000 }); Game.time = 110; X.run(); assert.strictEqual(S.sent, undefined); assert.strictEqual(Memory.ops.exportStat.why, 'colTermFull'); }],
  ['run: hostiles -> why=hostiles, no send', () => { world({ ht: 9000, hostiles: 1 }); Game.time = 110; X.run(); assert.strictEqual(S.sent, undefined); assert.strictEqual(Memory.ops.exportStat.why, 'hostiles'); }],
];
// fee check: ceil(5000*(1-e^-1/30)) = 164 (3.28%)
cases.push(['fee formula 5000 -> 164', () => { assert.strictEqual(X.fee(5000), 164); }]);
let fail = 0; for (const [n, f] of cases) { try { f(); console.log('ok  ', n); } catch (e) { fail++; console.log('FAIL', n, e.message); } }
console.log(`rcl8 export: ${cases.length - fail}/${cases.length}`); process.exit(fail ? 1 : 0);
