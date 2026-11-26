// STATIONARY_FILL stays OFF at RCL7 (strategy 2026-10-30 02:4x, docs/RCL7.md). Enabling would zero queens and only
// staff stamp A (4 fillers) before stamp B/C links exist — assert the gate and queen-regime targets.
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
const plan = require(src('utils/plan.js'));

const cases = [
  ['STATIONARY_FILL stays false', () => assert.strictEqual(plan.STATIONARY_FILL, false)],
  ['LINK_PLAN A: hub+ctl@5, srcA@6, l4 stampB@7, no l5/l6 (filler links dropped)', () => {
    assert.deepStrictEqual(plan.LINK_PLAN.hub, [37, 29, 5]);
    assert.deepStrictEqual(plan.LINK_PLAN.ctl, [30, 31, 5]);
    assert.deepStrictEqual(plan.LINK_PLAN.srcA, [30, 11, 6]);
    assert.deepStrictEqual(plan.LINK_PLAN.l4, [32, 34, 7]);
    assert.strictEqual(plan.LINK_PLAN.l5, undefined);
    assert.strictEqual(plan.LINK_PLAN.l6, undefined);
  }],
  ['12 filler stands + manager (layout) — more than T.filler=4', () => {
    const P = plan.get('W46N8');
    assert.strictEqual(P.pos.fillers.length, 12);
    assert.deepStrictEqual(P.pos.manager, [36, 30]);
  }],
];

Object.assign(global, {
  WORK: 'work', CARRY: 'carry', MOVE: 'move', RESOURCE_ENERGY: 'energy',
  STRUCTURE_LINK: 'link', STRUCTURE_CONTAINER: 'container', STRUCTURE_SPAWN: 'spawn',
  STRUCTURE_EXTENSION: 'extension', STRUCTURE_TOWER: 'tower', STRUCTURE_STORAGE: 'storage',
  STRUCTURE_RAMPART: 'rampart', STRUCTURE_WALL: 'constructedWall', STRUCTURE_ROAD: 'road',
  STRUCTURE_EXTRACTOR: 'extractor', STRUCTURE_TERMINAL: 'terminal',
  ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack', HEAL: 'heal', TOUGH: 'tough', CLAIM: 'claim',
  BODYPART_COST: { move: 50, work: 100, carry: 50, attack: 80, ranged_attack: 150, heal: 250, claim: 600, tough: 10 },
  FIND_HOSTILE_CREEPS: 103, FIND_MY_CREEPS: 102, FIND_STRUCTURES: 107, FIND_MY_STRUCTURES: 108,
  FIND_MY_CONSTRUCTION_SITES: 114, FIND_CONSTRUCTION_SITES: 111, FIND_DROPPED_RESOURCES: 106,
  FIND_SOURCES: 105, FIND_MINERALS: 116,
});
global._ = global._ || {
  filter: (a, f) => Object.values(a).filter(f),
  sum: (a, f) => a.reduce((t, x) => t + f(x), 0),
  countBy: (a, f) => a.reduce((o, x) => (o[f(x)] = (o[f(x)] || 0) + 1, o), {}),
};

cases.push(['RCL7 queen regime: queen=2 filler=0 manager=0 hauler=1', () => {
  const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
  delete require.cache[require.resolve(src('managers/spawn.js'))];
  stub('utils/roomcache.js', { all: (r, t) => t === 'link' ? [1, 2, 3, 4] : [], at: () => null, get: () => ({ at: [] }), sites: () => [] });
  stub('roles/builder.js', { remoteRoadSite: () => null });
  stub('utils/move.js', { to: () => true });
  stub('utils/trace.js', { why: () => {} });
  stub('managers/threat.js', { reserve: () => 5600, holding: () => false });
  global.Memory = { rooms: { W46N8: {} }, ops: {}, remotes: {} };
  global.Game = { time: 1000, rooms: {}, creeps: {}, spawns: {} };
  const S = require(src('managers/spawn.js'));
  const room = {
    name: 'W46N8', memory: {}, controller: { level: 7 }, energyCapacityAvailable: 5600,
    storage: { store: { energy: 20000 } }, find: () => [],
  };
  const T = S.targets(room, {}, 0, 900, 0);
  assert.strictEqual(T.queen, 2, 'queens');
  assert.strictEqual(T.filler, 0, 'fillers');
  assert.strictEqual(T.manager, 0, 'manager');
  assert.strictEqual(T.hauler, 1, 'hauler');
}]);

let fail = 0;
for (const [n, f] of cases) {
  try { f(); console.log('ok  ', n); }
  catch (e) { fail++; console.log('FAIL', n, e.message); }
}
process.exit(fail ? 1 : 0);
