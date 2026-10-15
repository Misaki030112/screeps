// v4 barrier phase (src/managers/walls.js): site order, step target, fund, repair job. node tests/walls_barriers.js -> exit 1 on failure
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
const L4 = require('lodash'), _3 = Object.assign({}, L4, { min: (a, f) => f ? L4.minBy(a, f) : L4.min(a) }); // Screeps runs lodash 3: _.min(arr, fn)
Object.assign(global, { _: _3, OK: 0, RESOURCE_ENERGY: 'energy', STRUCTURE_RAMPART: 'rampart', STRUCTURE_WALL: 'constructedWall', STRUCTURE_ROAD: 'road',
  LOOK_CONSTRUCTION_SITES: 'constructionSite', LOOK_STRUCTURES: 'structure', FIND_HOSTILE_CREEPS: 103, Game: { time: 1000, getObjectById: id => OBJ[id] } });
let OBJ = {}, SITES = [], HOLD = false;
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
stub('managers/threat.js', { holding: () => HOLD, reserve: () => 1300 });
stub('utils/roomcache.js', { at: (r, x, y, t) => Object.values(OBJ).find(s => s.x === x && s.y === y && s.structureType === t) || null, sites: () => SITES, all: () => [] });
const W = require(src('managers/walls.js')), plan = require(src('utils/plan.js')), P = plan.get('W46N8');
console.log = (() => { const l = console.log; return (...a) => { if (!String(a[0]).startsWith('WALLS')) l(...a); }; })();
function room(o = {}) {
  const made = [];
  return { name: 'W46N8', made, memory: o.mem || { walls: { started: 1 } }, controller: { level: o.rcl || 6 }, storage: { store: { energy: o.storage ?? 20000 } },
    find: () => o.hostiles || [], lookForAt: () => [], createConstructionSite: (x, y, t) => { made.push(`${t} ${x},${y}`); return 0; } };
}
const wall = (id, x, y, hits, t = 'constructedWall') => (OBJ[id] = { id, x, y, hits, structureType: t });
const cases = [
  ['plan: 6 gates, 41 walls, order gates -> trunk roads -> walls', () => {
    const L = W.lists(P); assert.strictEqual(L.gates.length, 6); assert.strictEqual(L.walls.length, 41);
    const kinds = L.order.map(o => o[1]); assert.deepStrictEqual(kinds.slice(0, 6), Array(6).fill('rampart'));
    assert.strictEqual(kinds.lastIndexOf('road') < kinds.indexOf('constructedWall'), true);
    assert.deepStrictEqual(L.order[0][0], [47, 16]);
    assert.ok(!L.order.some(([[x, y], t]) => t === 'road' && x === 41 && y === 23), 'on_demand BR trunk not placed');
  }],
  ['planned(): gate rampart / wall / trunk road; not other types', () => {
    assert.ok(W.planned(P, 47, 16, 'rampart')); assert.ok(W.planned(P, 26, 7, 'constructedWall')); assert.ok(W.planned(P, 46, 17, 'road'));
    assert.ok(!W.planned(P, 26, 7, 'road')); assert.ok(!W.planned(P, 35, 28, 'rampart'));
  }],
  ['phase off (RCL5): no sites, no job, no reserve', () => { const r = room({ rcl: 5, mem: {} }); assert.deepStrictEqual(W.placeSites(r, 5), []); assert.strictEqual(W.repairJob(r), null); assert.strictEqual(W.reserved(r), 0); }],
  ['build: at most 2 barrier sites, gates first', () => { OBJ = {}; SITES = []; const r = room(); W.placeSites(r, 5); assert.deepStrictEqual(r.made, ['rampart 47,16', 'rampart 47,17']); }],
  ['build: open barrier sites count against the cap', () => { OBJ = {}; SITES = [{ structureType: 'rampart', pos: { x: 47, y: 16 } }]; const r = room(); W.placeSites(r, 5); assert.strictEqual(r.made.length, 1); SITES = []; }],
  ['step target: lowest step not reached by all; even rise', () => {
    OBJ = {}; wall('a', 26, 7, 120000); wall('b', 27, 7, 50000); const r = room(); const B = W.barriers(r, P);
    assert.strictEqual(W.target(r, B), 100000); OBJ.b.hits = 100000; assert.strictEqual(W.target(r, W.barriers(r, P)), 300000);
  }],
  ['fund opens at 20k bank, accrues 10% x 23/t, debits', () => {
    const m = { walls: { started: 1 } }, r = room({ mem: m }); Game.time = 1000; assert.strictEqual(W.fund(r), 20000);
    Game.time = 1100; assert.ok(Math.abs(W.fund(r) - 20230) < 1e-6); W.spend(r, 5000); assert.ok(Math.abs(W.fund(r) - 15230) < 1e-6);
    assert.strictEqual(W.reserved(room({ mem: m, storage: 9000 })), 9000);
  }],
  ['repair job: lowest first, capped +10k / step', () => {
    OBJ = {}; wall('a', 26, 7, 95000); wall('b', 27, 7, 30000); const m = { walls: { started: 1 } };
    assert.deepStrictEqual(W.repairJob(room({ mem: m })), { id: 'b', cap: 40000 }); OBJ.b.hits = 99000; OBJ.a.hits = 99500;
    assert.deepStrictEqual(W.repairJob(room({ mem: m })), { id: 'b', cap: 100000 });
  }],
  ['no fund, no threat -> no job, no builder; threat lifts the cap', () => {
    OBJ = {}; wall('b', 27, 7, 30000); const m = { walls: { started: 1, fund: 0, ft: Game.time } };
    assert.strictEqual(W.repairJob(room({ mem: m })), null); assert.strictEqual(W.wantBuilder(room({ mem: m })), false);
    HOLD = true; assert.ok(W.repairJob(room({ mem: m }))); assert.ok(W.wantBuilder(room({ mem: m }))); HOLD = false;
  }],
  ['all barriers at last step -> no job', () => { OBJ = {}; wall('a', 26, 7, 300000); assert.strictEqual(W.repairJob(room()), null); }],
];
let fail = 0; const log = (...a) => process.stdout.write(a.join(' ') + '\n');
for (const [n, f] of cases) { try { f(); log('ok  ', n); } catch (e) { fail++; log("FAIL", n, e.message.replace(/\n/g," ")); } }
process.exit(fail ? 1 : 0);
