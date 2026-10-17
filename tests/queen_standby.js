// Queen standby source choice (src/roles/queen.js): when spawn/tower are full and the controller container is low,
// ferry from storage any SURPLUS above the defender reserve (or spawn cap if unarmed) (partial OK; never below floor),
// else filler container A above 400 + carry.
// node tests/queen_standby.js -> exits 1 on failure
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, { STRUCTURE_LINK: 'link', RESOURCE_ENERGY: 'energy', STRUCTURE_CONTAINER: 'container', STRUCTURE_SPAWN: 'spawn', STRUCTURE_EXTENSION: 'extension', STRUCTURE_TOWER: 'tower', FIND_MY_CREEPS: 1, Game: { time: 1 } });
const store = (e, cap) => ({ energy: e, getCapacity: () => cap, getFreeCapacity: () => cap - e });
const obj = (x, y, e, cap) => ({ pos: { x, y }, store: Object.assign({ [RESOURCE_ENERGY]: e }, store(e, cap)) });
let W; // world for the current case
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
const P = { pos: { controllerContainer: [30, 30], fillerContainerA: [35, 24], fillers: [[34, 25]], manager: [36, 30], miners: [] }, any: {} };
stub('utils/plan.js', { get: () => P, key: (x, y) => x * 50 + y });
stub('utils/move.js', { to: (c, x, y) => { W.moved = [x, y]; return true; } });
stub('utils/roomcache.js', { at: (room, x, y) => (x === 30 ? W.cc : x === 35 ? W.fc : null), all: (room, t) => (t === 'tower' ? [] : []), get: () => ({ at: [] }) });
stub('utils/trace.js', { why: (c, k) => { W.why = k; } });
stub('managers/threat.js', { reserve: () => W.reserve });
stub('roles/hauler.js', { ctlLow: () => W.cc.store.energy < 1000, handoff: () => false, pickups: () => [] });
stub('managers/links.js', { ctlLinkLow: () => !!W.hub, roles: () => ({ hub: W.hub }) });
const RW = require(src('managers/walls.js')); const _nu = RW.noUpgrade; RW.noUpgrade = r => W.hold ? true : _nu(r);
const Q = require(src('roles/queen.js'));
function run(o) {
  W = Object.assign({ reserve: 1300, cc: obj(30, 30, 200, 2000), fc: obj(35, 24, 0, 2000), st: obj(37, 31, 0, 1e6), cap: 1300 }, o);
  const room = { name: 'W46N8', energyAvailable: W.cap, energyCapacityAvailable: W.cap, storage: W.st, memory: {} };
  const withdrawn = [];
  const c = { room, memory: {}, store: Object.assign({ [RESOURCE_ENERGY]: o.carry || 0 }, store(o.carry || 0, 400)), pos: { getRangeTo: () => 1, findInRange: () => [] },
    _e: o.carry || 0, withdraw: (t, _r, amt) => withdrawn.push({ src: t === W.st ? 'storage' : t === W.fc ? 'fc' : t === W.hub ? 'hub' : '?', amt }), transfer: (t) => { W.to = t === W.hub ? 'hub' : t === W.cc ? 'cc' : '?'; return 0; } };
  Q.run(c); return { withdrawn, why: W.why, to: W.to };
}
const cases = [
  ['storage full surplus -> ferry full carry from storage', () => assert.deepStrictEqual(run({ st: obj(37, 31, 2000, 1e6) }).withdrawn, [{ src: 'storage', amt: 400 }])],
  ['storage in old dead-band (floor..floor+carry) -> partial ferry', () => assert.deepStrictEqual(run({ st: obj(37, 31, 1500, 1e6) }).withdrawn, [{ src: 'storage', amt: 200 }])],
  ['storage exactly at floor -> park (no drain)', () => { const r = run({ st: obj(37, 31, 1300, 1e6) }); assert.deepStrictEqual(r.withdrawn, []); assert.strictEqual(r.why, 'f'); }],
  ['storage below floor, fc >= 400+carry -> ferry from fc', () => assert.deepStrictEqual(run({ st: obj(37, 31, 500, 1e6), fc: obj(35, 24, 1100, 2000) }).withdrawn, [{ src: 'fc', amt: undefined }])],
  ['not armed (reserve 0): floor is spawn capacity 1300', () => { assert.deepStrictEqual(run({ reserve: 0, st: obj(37, 31, 1300, 1e6) }).withdrawn, []); assert.deepStrictEqual(run({ reserve: 0, st: obj(37, 31, 1301, 1e6) }).withdrawn, [{ src: 'storage', amt: 1 }]); }],
  ['ctl container not low -> no ferry', () => assert.deepStrictEqual(run({ st: obj(37, 31, 9000, 1e6), cc: obj(30, 30, 1500, 2000) }).withdrawn, [])],
  ['plan A: ctl link low + hub link free -> ferry storage surplus even if ctl container is full', () => assert.deepStrictEqual(run({ st: obj(37, 31, 2000, 1e6), cc: obj(30, 30, 1500, 2000), hub: obj(37, 29, 0, 800) }).withdrawn, [{ src: 'storage', amt: 400 }])],
  ['plan A: carried surplus goes into the hub link, not the ctl container', () => assert.strictEqual(run({ carry: 400, st: obj(37, 31, 2000, 1e6), hub: obj(37, 29, 0, 800) }).to, 'hub')],
  ['plan A: hub link full -> falls back to ctl container ferry', () => assert.strictEqual(run({ carry: 400, st: obj(37, 31, 2000, 1e6), hub: obj(37, 29, 800, 800) }).to, 'cc')],
  ['plan A: hub wanted but storage at floor -> no drain', () => assert.deepStrictEqual(run({ st: obj(37, 31, 1300, 1e6), cc: obj(30, 30, 1500, 2000), hub: obj(37, 29, 0, 800) }).withdrawn, [])],
  // RCL5: spawn cap 1800 must NOT raise the floor above the defender reserve (else link ferry never starts)
  ['RCL5 cap 1800 + reserve 1300, storage 1500 -> partial ferry (not blocked by cap)', () => assert.deepStrictEqual(run({ cap: 1800, st: obj(37, 31, 1500, 1e6), hub: obj(37, 29, 0, 800) }).withdrawn, [{ src: 'storage', amt: 200 }])],
  ['RCL5 cap 1800 + reserve 1300, storage 1600 hub -> ferry into hub', () => assert.strictEqual(run({ cap: 1800, carry: 300, st: obj(37, 31, 1600, 1e6), hub: obj(37, 29, 0, 800) }).to, 'hub')],
  ['build hold: hub > 400 -> queen drains hub (to storage)', () => assert.deepStrictEqual(run({ hold: true, st: obj(37, 31, 9000, 1e6), hub: obj(37, 29, 799, 800) }).withdrawn, [{ src: 'hub', amt: undefined }])],
  ['build hold: hub <= 400 -> no drain, no storage ferry', () => assert.deepStrictEqual(run({ hold: true, st: obj(37, 31, 9000, 1e6), hub: obj(37, 29, 300, 800) }).withdrawn, [])],
];
let fail = 0; for (const [n, f] of cases) { try { f(); console.log('ok  ', n); } catch (e) { fail++; console.log('FAIL', n, e.message); } }
console.log(`queen standby: ${cases.length - fail}/${cases.length}`); process.exit(fail ? 1 : 0);
