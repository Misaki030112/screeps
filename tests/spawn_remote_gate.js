// Remote spawn gates (src/managers/spawn.js):
// - reserverBody from avail (not E=cap) so avail 650-1299 spawns CLAIM1 instead of blocking on CLAIM2
// - nearFull treats cap-100 as full so RCL5 build drain does not false-starve
// node tests/spawn_remote_gate.js -> exits 1 on failure
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
  ['CLAIM2 when avail>=1300', () => assert.deepStrictEqual(S.reserverBody(1300), ['claim', 'claim', 'move', 'move'])],
  ['CLAIM1 when avail=1200 (RCL5 build stuck', () => assert.deepStrictEqual(S.reserverBody(1200), ['claim', 'move'])],
  ['CLAIM1 at exactly 650', () => assert.deepStrictEqual(S.reserverBody(650), ['claim', 'move'])],
  ['nearFull exact cap', () => assert.strictEqual(S.nearFull(1400, 1400), true)],
  ['nearFull cap-100', () => assert.strictEqual(S.nearFull(1300, 1400), true)],
  ['nearFull below band', () => assert.strictEqual(S.nearFull(1299, 1400), false)],
  ['nearFull low cap', () => assert.strictEqual(S.nearFull(250, 300), true)],
  // remoteNext: producer before carriers (patrol 10-15 00:08: 1 rhauler, 0 rminer, cont 10e)
  ['1 rhauler + 0 rminer -> rminer', () => assert.strictEqual(S.remoteNext({ nRes: 1, wantRes: 1, res: 2943, avail: 1269, rmLive: 0, rhLive: 1, rhAll: 1 }), 'rminer')],
  ['rminer live + 1 rhauler -> rhauler', () => assert.strictEqual(S.remoteNext({ nRes: 1, wantRes: 1, res: 2943, avail: 1269, rmLive: 1, rhLive: 1, rhAll: 1 }), 'rhauler')],
  ['full set -> nothing', () => assert.strictEqual(S.remoteNext({ nRes: 1, wantRes: 1, res: 2943, avail: 1500, rmLive: 1, rhLive: 2, rhAll: 2 }), null)],
  ['no reserver, res<4000 -> reserver first', () => assert.strictEqual(S.remoteNext({ nRes: 0, wantRes: 1, res: 2943, avail: 700, rmLive: 0, rhLive: 0, rhAll: 0 }), 'reserver')],
  ['res>=4000 skips reserver', () => assert.strictEqual(S.remoteNext({ nRes: 0, wantRes: 1, res: 4100, avail: 1500, rmLive: 1, rhLive: 2, rhAll: 2 }), null)],
  ['2 dying + 1 new rhauler -> no 4th', () => assert.strictEqual(S.remoteNext({ nRes: 1, wantRes: 1, res: 3000, avail: 1500, rmLive: 1, rhLive: 1, rhAll: 3 }), null)],
];
let fail = 0;
for (const [n, f] of cases) {
  try { f(); console.log('ok  ', n); }
  catch (e) { fail++; console.log('FAIL', n, e.message); }
}
console.log(`spawn remote gate: ${cases.length - fail}/${cases.length}`);
process.exit(fail ? 1 : 0);
