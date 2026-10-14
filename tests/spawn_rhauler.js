// Remote rhauler early-replace cap (src/managers/spawn.js rhaulerNeed):
// live TTL>120 may be 0 while 2 dying remain → without allCount < target+1 we spawn 2 and briefly run 4 (~1600e wipe).
// node tests/spawn_rhauler.js -> exits 1 on failure
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, {
  RESOURCE_ENERGY: 'energy', STRUCTURE_LINK: 'link', STRUCTURE_CONTAINER: 'container',
  STRUCTURE_SPAWN: 'spawn', STRUCTURE_EXTENSION: 'extension', STRUCTURE_TOWER: 'tower',
  CARRY: 'carry', MOVE: 'move', WORK: 'work', CLAIM: 'claim',
  RANGED_ATTACK: 'ranged_attack', HEAL: 'heal', BODYPART_COST: {},
  _: { filter: () => [], sum: () => 0, countBy: () => ({}) },
});
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
stub('utils/plan.js', { get: () => ({ pos: { upgraders: [], controllerContainer: [30, 30], fillers: [] }, raw: { stamps: {} } }), key: (x, y) => x * 50 + y });
stub('utils/roomcache.js', { all: () => [], at: () => null, sites: () => [] });
stub('utils/trace.js', { why: () => {} });
stub('managers/threat.js', { reserve: () => 1300, wantDefender: () => null, noteSpawn: () => {} });
stub('managers/remote.js', { CFG: {}, paused: () => false, mem: () => ({}) });
stub('roles/hauler.js', { pickups: () => [] });
stub('roles/queen.js', { storageFloor: () => 1300 });
const S = require(src('managers/spawn.js'));
const cases = [
  ['both healthy: no spawn', () => assert.strictEqual(S.rhaulerNeed(2, 2), false)],
  ['one live one dying: spawn one overlap', () => assert.strictEqual(S.rhaulerNeed(1, 2), true)],
  ['both dying live=0 all=2: spawn first replacement', () => assert.strictEqual(S.rhaulerNeed(0, 2), true)],
  ['both dying + one new all=3: do NOT spawn second (was the 4-creep wipe)', () => assert.strictEqual(S.rhaulerNeed(0, 3), false)],
  ['live=1 all=3 (one new spawning, two dying): no third', () => assert.strictEqual(S.rhaulerNeed(1, 3), false)],
  ['zero creeps: spawn', () => assert.strictEqual(S.rhaulerNeed(0, 0), true)],
  ['one live only: spawn second', () => assert.strictEqual(S.rhaulerNeed(1, 1), true)],
  // old rule live<2 alone would still spawn here — this is the regression the patrol hit
  ['REGRESSION old live<2 with all=3 would spawn', () => assert.strictEqual(S.rhaulerNeed(0, 3), false)],
];
let fail = 0;
for (const [n, f] of cases) {
  try { f(); console.log('ok  ', n); }
  catch (e) { fail++; console.log('FAIL', n, e.message); }
}
console.log(`spawn rhauler: ${cases.length - fail}/${cases.length}`);
process.exit(fail ? 1 : 0);
