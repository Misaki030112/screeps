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
  ['decaying: lowest gate rampart below the floor, skipping taken ones; walls ignored', () => {
    OBJ = {}; wall('g1', 47, 16, 6800, 'rampart'); wall('g2', 47, 17, 2961, 'rampart'); wall('g3', 6, 28, 2901, 'rampart'); wall('w1', 26, 7, 1);
    const r = room(); assert.strictEqual(W.decaying(r).id, 'g3'); assert.strictEqual(W.decaying(r, new Set(['g3'])).id, 'g2');
    assert.strictEqual(W.decaying(r, new Set(['g3', 'g2'])), null); assert.strictEqual(W.decaying(room({ mem: {} })), null, 'off before build phase');
    OBJ = {};
  }],
  ['plan: 6 gates, 41 walls, order gates -> walls -> roads (v5 enclose first)', () => {
    const L = W.lists(P); assert.strictEqual(L.gates.length, 6); assert.strictEqual(L.walls.length, 41);
    const kinds = L.order.map(o => o[1]); assert.deepStrictEqual(kinds.slice(0, 6), Array(6).fill('rampart'));
    assert.strictEqual(kinds.indexOf('road') > kinds.lastIndexOf('constructedWall'), true);
    assert.deepStrictEqual(L.order[0][0], [47, 16]);
    assert.ok(L.order.some(([[x, y], t]) => t === 'road' && x === 43 && y === 26), 'v5: BR trunk placed in wall phase'); assert.ok(L.order.some(([[x, y], t]) => t === 'road' && x === 26 && y === 15), 'v5: TL trunk');
    assert.ok(!L.order.some(([[x, y], t]) => t === 'road' && x === 30 && y === 30), 'no trunk road on the ctl container 30,30 (layout destroys it)');
    assert.ok(L.order.some(([[x, y], t]) => t === 'road' && x === 29 && y === 31), 'rest of W trunk kept');
  }],
  ['planned(): gate rampart / wall / trunk road; not other types', () => {
    assert.ok(W.planned(P, 47, 16, 'rampart')); assert.ok(W.planned(P, 26, 7, 'constructedWall')); assert.ok(W.planned(P, 46, 17, 'road'));
    assert.ok(!W.planned(P, 26, 7, 'road')); assert.ok(!W.planned(P, 35, 28, 'rampart'));
  }],
  ['phase off (RCL5): no sites, no job, no reserve', () => { const r = room({ rcl: 5, mem: {} }); assert.deepStrictEqual(W.placeSites(r, 5), []); assert.strictEqual(W.repairJob(r), null); assert.strictEqual(W.reserved(r), 0); }],
  ['build v5: 2 gate sites + 15 wall sites (own cap), no road before ring closed', () => { OBJ = {}; SITES = []; const r = room(); W.placeSites(r, 5);
    assert.deepStrictEqual(r.made.slice(0, 3), ['rampart 47,16', 'rampart 47,17', 'constructedWall 26,7']); assert.strictEqual(r.made.length, 17); assert.ok(!r.made.some(m => m.startsWith('road')));
    const r0 = room(); W.placeSites(r0, 0); assert.strictEqual(r0.made.length, 15, 'walls placed even with layout budget 0'); }],
  ['build: open barrier sites count against the caps', () => { OBJ = {}; SITES = [{ structureType: 'rampart', pos: { x: 47, y: 16 } }, { structureType: 'constructedWall', pos: { x: 26, y: 7 } }]; const r = room(); W.placeSites(r, 5); assert.strictEqual(r.made.length, 1 + 14); SITES = []; }],
  ['ring closed -> spur roads placed after barriers', () => { OBJ = {}; SITES = []; const L = W.lists(P); let i = 0;
    for (const [x, y] of L.gates) wall('g' + i++, x, y, 20000, 'rampart'); for (const [x, y] of L.walls) wall('w' + i++, x, y, 1);
    const r = room(); assert.ok(W.ringClosed(r, P)); W.placeSites(r, 5); assert.ok(r.made.length > 0 && r.made.every(m => m.startsWith('road'))); OBJ = {}; }],
  ['v5 hold: no upgrading in wall phase until ring closed and all >= 100k', () => { OBJ = {}; global.Memory = global.Memory || {};
    const r = room(); r.controller = { level: 6, my: true, ticksToDowngrade: 100000 }; assert.strictEqual(W.noUpgrade(r), true, 'ring open');
    const L = W.lists(P); let i = 0; for (const [x, y] of L.gates) wall('g' + i++, x, y, 100000, 'rampart'); for (const [x, y] of L.walls) wall('w' + i++, x, y, 100000);
    assert.strictEqual(W.noUpgrade(r), false, 'all 100k -> upgrade'); OBJ.w10.hits = 5; assert.strictEqual(W.noUpgrade(r), true);
    r.controller.ticksToDowngrade = 10000; assert.strictEqual(W.noUpgrade(r), false, 'downgrade safety'); OBJ = {}; }],
  ['repair job v5: nearest in lowest band, skips taken', () => { OBJ = {}; const m = { walls: { started: 1 } };
    const pos = { roomName: 'W46N8', getRangeTo: o => Math.max(Math.abs(o.x - 6), Math.abs(o.y - 28)) };
    for (const o of [wall('n', 26, 7, 100), wall('w', 6, 24, 500), wall('x', 6, 25, 15000)]) o.pos = { roomName: 'W46N8' };
    assert.strictEqual(W.repairJob(room({ mem: m }), pos).id, 'w', 'near west wall in band beats far NW lowest');
    assert.strictEqual(W.repairJob(room({ mem: m }), pos, new Set(['w'])).id, 'n'); assert.strictEqual(W.repairJob(room({ mem: m }), pos).cap, 10000); OBJ = {}; }],
  ['step target: lowest step not reached by all; even rise', () => {
    OBJ = {}; wall('a', 26, 7, 120000); wall('b', 27, 7, 50000); const r = room(); const B = W.barriers(r, P);
    assert.strictEqual(W.target(r, B), 100000); OBJ.b.hits = 100000; assert.strictEqual(W.target(r, W.barriers(r, P)), 300000); OBJ.b.hits = 5; assert.strictEqual(W.target(r, W.barriers(r, P)), 10000);
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
    assert.strictEqual(W.repairJob(room({ mem: m, storage: 5000 })), null); assert.strictEqual(W.wantBuilder(room({ mem: m, storage: 5000 })), false);
    assert.ok(W.repairJob(room({ mem: m, storage: 9000 })), 'v5: storage above 5k floor is wall budget');
    HOLD = true; assert.ok(W.repairJob(room({ mem: m, storage: 5000 }))); assert.ok(W.wantBuilder(room({ mem: m, storage: 5000 }))); HOLD = false;
  }],
  ['v5 rampart slack: decayed gate within SLACK keeps the step; topped to step+SLACK; taken band -> next free low', () => {
    OBJ = {}; const m = { walls: { started: 1 } }; wall('g', 44, 27, 9741, 'rampart'); wall('a', 26, 7, 12000); wall('b', 27, 7, 25000);
    const r = room({ mem: m }); assert.strictEqual(W.target(r, W.barriers(r, P)), 30000, 'gate 9741 counts as at the 10k step');
    assert.strictEqual(W.belowFloor(r), false);
    OBJ.a.hits = 31000; OBJ.b.hits = 31000; OBJ.g.hits = 26000; assert.strictEqual(W.target(r, W.barriers(r, P)), 100000, 'gate 26k (eff 31k) has reached 30k');
    OBJ.g.hits = 24000; assert.deepStrictEqual(W.repairJob(r), { id: 'g', cap: 34000 }, 'rampart topped to min(step+SLACK, +CHUNK)');
    OBJ.a.hits = 20000; OBJ.b.hits = 28500; OBJ.g.hits = 31000;
    assert.strictEqual(W.repairJob(r, null, new Set(['a'])).id, 'b', 'band (a) held -> next free below step, not a pile-up');
    assert.strictEqual(W.repairJob(r, null, new Set(['a', 'b'])).id, 'a', 'nothing free -> lowest');
    OBJ = {}; }],
  ['step hold (Misaki 10-19 20:51): RCL6 past 100k -> no job / no builder unless threat; RCL7 resumes 300k; storage floor = reserveE', () => {
    OBJ = {}; const m = { walls: { started: 1 } }; wall('a', 26, 7, 142101); wall('b', 27, 7, 154000); wall('g', 47, 16, 172000, 'rampart');
    const r = room({ mem: m, storage: 30000 }); assert.strictEqual(W.target(r, W.barriers(r, P)), 300000);
    assert.strictEqual(W.repairJob(r), null, 'step 2 held at RCL6'); assert.strictEqual(W.wantBuilder(r), false);
    Game.time++; assert.strictEqual(W.stepHeld(r), true);
    const r4 = Object.assign(room({ mem: {}, rcl: 4, storage: 800 }), { name: 'W47N8' }); assert.strictEqual(W.stepHeld(r4), false, 'same tick, other room: cache is per room');
    HOLD = true; Game.time++; assert.ok(W.repairJob(r), 'threat: attacked walls still repaired'); assert.strictEqual(W.stepHeld(r), false); HOLD = false;
    const r7 = room({ mem: m, rcl: 7, storage: 30000 }); Game.time++; assert.strictEqual(W.repairJob(r7).id, 'a', 'RCL7: step 300k resumes'); assert.strictEqual(W.stepHeld(r7), false);
    OBJ.a.hits = 60000; Game.time++; assert.strictEqual(W.repairJob(r).id, 'a', 'below 100k still repaired at RCL6'); assert.strictEqual(W.stepHeld(r), false);
    OBJ.a.hits = 142101; Game.time++; global.Memory = global.Memory || {}; Memory.defense = { reserveE: 15000 };
    Object.assign(global, { STRUCTURE_SPAWN: 'spawn', STRUCTURE_EXTENSION: 'extension', STRUCTURE_CONTAINER: 'container', STRUCTURE_TOWER: 'tower', STRUCTURE_STORAGE: 'storage', STRUCTURE_LINK: 'link', STRUCTURE_LAB: 'lab', STRUCTURE_TERMINAL: 'terminal', FIND_MY_CREEPS: 102, FIND_STRUCTURES: 107 });
    const Q = require(src('roles/queen.js')); r.energyCapacityAvailable = 2300;
    assert.strictEqual(Q.storageFloor(r), 15000, 'held: fund not reserved, floor = reserveE');
    Game.time++; HOLD = true; assert.strictEqual(Q.storageFloor(r), 1300 + W.reserved(r), 'threat: fund reserved again'); assert.ok(W.reserved(r) > 20000); HOLD = false;
    delete Memory.defense; OBJ = {}; }],
  ['RCL7 peacetime hold at 300k (strategy 08:4x): no auto 1M; pushBarrier / threat resume', () => {
    OBJ = {}; Game.time++; const m = { walls: { started: 1, fund: 40000, ft: Game.time } };
    wall('a', 26, 7, 300000); wall('b', 27, 7, 300000); wall('g', 47, 16, 300000, 'rampart');
    const r7 = room({ mem: m, rcl: 7, storage: 16000 });
    assert.strictEqual(W.target(r7, W.barriers(r7, P)), 1000000, 'next step is 1M');
    assert.strictEqual(W.stepHeld(r7), true, '1M held peacetime');
    assert.strictEqual(W.repairJob(r7), null, 'no 1M job');
    assert.strictEqual(W.fundSpend(r7), false, 'fundSpend off while held');
    assert.strictEqual(W.HOLD_STEP_RCL7, 300000);
    global.Memory = global.Memory || {}; Memory.defense = { pushBarrier: true };
    Game.time++; assert.strictEqual(W.stepHeld(r7), false, 'pushBarrier lifts hold');
    assert.ok(W.repairJob(r7), '1M job with pushBarrier');
    delete Memory.defense.pushBarrier; HOLD = true; Game.time++;
    assert.strictEqual(W.stepHeld(r7), false, 'threat lifts hold');
    assert.ok(W.repairJob(r7), 'threat repairs toward 1M');
    HOLD = false; delete Memory.defense; OBJ = {};
  }],
  ['all barriers at last step -> no job', () => { OBJ = {}; wall('a', 26, 7, 300000); assert.strictEqual(W.repairJob(room()), null); }],
];
let fail = 0; const log = (...a) => process.stdout.write(a.join(' ') + '\n');
for (const [n, f] of cases) { try { f(); log('ok  ', n); } catch (e) { fail++; log("FAIL", n, e.message.replace(/\n/g," ")); } }
process.exit(fail ? 1 : 0);
