// Wall phase + RCL6 banking (src/managers/walls.js, spawn targets). node tests/walls_bank.js -> exits 1 on failure
global.Memory = Object.assign(global.Memory || {}, { roads: { phase: 'done' } }); // road plan finished (docs/ROADS.md): wall banking rules apply
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, { WORK: 'work', CARRY: 'carry', MOVE: 'move', RESOURCE_ENERGY: 'energy', STRUCTURE_LINK: 'link', STRUCTURE_CONTAINER: 'container', STRUCTURE_SPAWN: 'spawn', STRUCTURE_EXTENSION: 'extension', STRUCTURE_TOWER: 'tower', FIND_HOSTILE_CREEPS: 103, _: { filter: () => [] }, Game: { time: 1000 } });
let W;
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
const P = { pos: { upgraders: [[29, 30], [30, 31], [31, 30]], controllerContainer: [30, 30], fillerContainerA: [35, 24], fillers: [], miners: [] }, raw: { stamps: {} }, any: {} };
stub('utils/plan.js', { get: () => P, key: (x, y) => x * 50 + y });
stub('roles/builder.js', { remoteRoadSite: () => null }); // remote road builder gate (spawn.targets)
stub('utils/move.js', { to: () => true });
stub('utils/roomcache.js', { all: () => [], at: () => null, get: () => ({ at: [] }), sites: () => [] });
stub('utils/trace.js', { why: () => {} });
stub('managers/threat.js', { reserve: () => 1300, holding: () => W.holding });
const S = require(src('managers/spawn.js')), WL = require(src('managers/walls.js'));
const log = console.log; console.log = () => {};
function room(o) {
  W = Object.assign({ rcl: 6, storage: 5000, ema: 1500, sites: 0, holding: false, hostiles: [], mem: {} }, o);
  return { name: 'W46N8', memory: W.mem, controller: { level: W.rcl }, energyCapacityAvailable: 2300, storage: { store: { energy: W.storage } }, find: () => W.hostiles };
}
const up = o => { const r = room(o); return S.targets(r, {}, 0, W.ema, W.sites).upgrader; };
const player = { owner: { username: 'BustJetter' }, body: [{ type: 'attack', hits: 100 }] };
const now = Date.now;
const cases = [
  ['RCL5: no banking (2 + extras as before)', () => assert.strictEqual(up({ rcl: 5, storage: 9000 }), 3)],
  ['RCL6 core build (sites): 1 upgrader', () => assert.strictEqual(up({ sites: 3 }), 1)],
  ['RCL6 sites=0, storage 5k: bank -> 1 upgrader', () => assert.strictEqual(up({ storage: 5000 }), 1)],
  ['RCL6 storage 19999: still bank', () => assert.strictEqual(up({ storage: 19999 }), 1)],
  ['storage 20000 calm: latch build, extras allowed', () => { const m = {}; assert.strictEqual(up({ storage: 20000, mem: m }), 3); assert.strictEqual(m.walls.why, 'bank'); }],
  ['latched: dip below 20k never re-banks', () => { const m = { walls: { started: 5 } }; assert.strictEqual(up({ storage: 1000, ema: 1500, mem: m }), 2); }],
  ['storage 25k but remote threat holding: keep banking', () => { const m = {}; assert.strictEqual(up({ storage: 25000, holding: true, mem: m }), 1); assert.ok(!m.walls); }],
  ['storage 25k but hostile in home: keep banking', () => { const m = {}; assert.strictEqual(up({ storage: 25000, hostiles: [player], mem: m }), 1); assert.ok(!m.walls); }],
  ['early start after novice end: player combat creep in home', () => { Date.now = () => WL.NOVICE_END; const m = {}; assert.strictEqual(WL.phase(room({ storage: 100, hostiles: [player], mem: m })), 'build'); assert.strictEqual(m.walls.why, 'player'); Date.now = now; }],
  ['before novice end: player creep does not start walls early', () => { Date.now = () => WL.NOVICE_END - 1; assert.strictEqual(WL.phase(room({ storage: 100, hostiles: [player] })), 'bank'); Date.now = now; }],
  ['novice end = 2026-10-28 03:33 UTC+8', () => assert.strictEqual(new Date(WL.NOVICE_END).toISOString(), '2026-10-27T19:33:00.000Z')],
  ['RCL<6 phase off', () => assert.strictEqual(WL.phase(room({ rcl: 5 })), 'off')],
];
let fail = 0; for (const [n, f] of cases) { try { f(); log('ok  ', n); } catch (e) { fail++; log('FAIL', n, e.message); } }
process.exit(fail ? 1 : 0);
