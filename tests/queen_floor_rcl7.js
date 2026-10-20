// Queen ferry floor once the wall step hold lifts (home RCL7+, src/roles/queen.js storageFloor; strategy review 10-20 08:4x).
// At RCL7 the floor is reserve + reserved wall fund. Step 2 (300k) spends the 50k fund down to 0, and the floor then fell to the
// 1300 defender reserve: the ctl ferry would drain storage far below Memory.defense.reserveE (15k) in peacetime, and defLow then
// stopped builders and upgrader replacements (oscillation). The floor must never go below reserveE.
// node tests/queen_floor_rcl7.js -> exits 1 on failure
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, { STRUCTURE_SPAWN: 'spawn', STRUCTURE_EXTENSION: 'extension', STRUCTURE_TOWER: 'tower', RESOURCE_ENERGY: 'energy', _: require('lodash') });
let W;
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
stub('utils/plan.js', { get: () => null }); stub('utils/move.js', {}); stub('utils/roomcache.js', {});
stub('managers/threat.js', { reserve: () => W.reserve });
stub('managers/walls.js', { stepHeld: () => W.held, defReserve: () => W.dr, reserved: () => Math.min(W.fund, W.st) });
const Q = require(src('roles/queen.js'));
const floor = o => { W = Object.assign({ reserve: 1300, held: false, dr: 15000, fund: 50000, st: 15000 }, o); return Q.storageFloor({ name: 'W46N8', energyCapacityAvailable: 5600 }); };
const cases = [
  ['RCL6 held: floor is reserveE', () => assert.strictEqual(floor({ held: true }), 15000)],
  ['RCL7 fund full: floor = reserve + storage (ferry stops, storage banks for walls)', () => assert.strictEqual(floor({ st: 30000 }), 31300)],
  ['RCL7 fund drained to 0: floor stays at reserveE, not 1300', () => assert.strictEqual(floor({ fund: 0, st: 20000 }), 15000)],
  ['RCL7 fund 5k: floor stays at reserveE', () => assert.strictEqual(floor({ fund: 5000, st: 20000 }), 15000)],
  ['RCL7 fund 20k: reserve + fund above reserveE', () => assert.strictEqual(floor({ fund: 20000, st: 30000 }), 21300)],
  ['no reserveE set: old rule (reserve + fund)', () => assert.strictEqual(floor({ dr: 0, fund: 0, st: 20000 }), 1300)],
];
let fail = 0; for (const [n, f] of cases) { try { f(); console.log('ok  ', n); } catch (e) { fail++; console.log('FAIL', n, e.message); } }
console.log(`queen floor rcl7: ${cases.length - fail}/${cases.length}`); process.exit(fail ? 1 : 0);
