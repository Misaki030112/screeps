// Patrol 2026-11-11 creep audit (official room history 84198000-84200099):
// 1) spawn.birthDirs never offers a boxed-in tile (W46N8 Spawn3 30,34 -> 31,33 / 31,35): queens born there were recycled at once.
// 2) utils/combatmove: W47N8 combat creeps search with creeps ignored (incomplete creep-aware search walked w8guard84199224 into
//    the NE dead end 35,10 for ~900 t); one creep-aware search only after 3 stuck ticks.
// node tests/creep_audit_1111.js -> exits 1 on failure
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, { WORK: 'work', CARRY: 'carry', MOVE: 'move', RESOURCE_ENERGY: 'energy', STRUCTURE_LINK: 'link', TERRAIN_MASK_WALL: 1, OK: 0,
  _: require('lodash'), Game: { time: 100, creeps: {}, rooms: {} }, Memory: {} });
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
// stamp B around Spawn3 30,34: extensions everywhere except filler tiles 31,33 / 31,35 (each boxed in), link 32,34
const tiles = { '30,34': 'S', '31,33': 'F', '31,35': 'F', '32,34': 'L' };
for (const x of [30, 31, 32, 33, 34]) for (const y of [32, 33, 34, 35, 36]) if (!tiles[x + ',' + y]) tiles[x + ',' + y] = 'E';
const P = { raw: { stamps: { B: { tiles } } }, pos: {} };
const at = {};
for (const k in tiles) { if (tiles[k] === 'F') continue; const [x, y] = k.split(',').map(Number); at[x * 50 + y] = { [tiles[k] === 'S' ? 'spawn' : tiles[k] === 'L' ? 'link' : 'extension']: 'id' + k }; }
stub('utils/plan.js', { get: () => P, key: (x, y) => x * 50 + y });
stub('utils/roomcache.js', { get: () => ({ at }), all: () => [], at: () => null, sites: () => [] });
stub('utils/move.js', { to: () => true });
stub('utils/trace.js', { why: () => {} });
stub('managers/remote.js', { CFG: {} });
const S = require(src('managers/spawn.js'));
const room = { name: 'W46N8', getTerrain: () => ({ get: () => 0 }) };
const sp = { room, pos: { x: 30, y: 34 } };
const DXY = { 1: [0, -1], 2: [1, -1], 3: [1, 0], 4: [1, 1], 5: [0, 1], 6: [-1, 1], 7: [-1, 0], 8: [-1, -1] };
const tileOf = d => (30 + DXY[d][0]) + ',' + (34 + DXY[d][1]);
const cases = [
  ['queen: boxed-in 31,33 / 31,35 never offered; outside tiles remain', () => {
    const d = S.birthDirs(sp, 'queen');
    assert.ok(!d.map(tileOf).includes('31,33') && !d.map(tileOf).includes('31,35'), JSON.stringify(d.map(tileOf)));
    assert.ok(d.map(tileOf).includes('29,34'));
  }],
  ['an inside tile with a free neighbour stays first for the queen', () => {
    const save = at[32 * 50 + 32]; delete at[32 * 50 + 32]; // 32,32 free -> 31,33 can leave
    try { const d = S.birthDirs(sp, 'queen').map(tileOf); assert.ok(d.includes('31,33') && d.indexOf('31,33') < d.indexOf('29,34'), JSON.stringify(d)); } finally { at[32 * 50 + 32] = save; }
  }],
];
// combatmove
const CMV = require(src('utils/combatmove.js'));
function creep(x, y) {
  const c = { pos: { x, y, inRangeTo: (tx, ty, r) => Math.max(Math.abs(tx - c.pos.x), Math.abs(ty - c.pos.y)) <= r }, memory: { _move: { dest: {} } }, fatigue: 0, calls: [],
    moveTo: (tx, ty, o) => { c.calls.push(o); return 0; } };
  return c;
}
cases.push(['search ignores creeps; after 3 stuck ticks one creep-aware search (no reuse), then back', () => {
  const c = creep(35, 10), cb = () => {};
  for (let t = 1; t <= 5; t++) { Game.time = 1000 + t; CMV.to(c, 29, 5, 0, cb, 2); }
  const ic = c.calls.map(o => o.ignoreCreeps);
  assert.deepStrictEqual(ic, [true, true, true, false, true], JSON.stringify(ic));
  assert.strictEqual(c.calls[3].reusePath, 0); assert.strictEqual(c.calls[0].reusePath, 2); assert.strictEqual(c.calls[0].costCallback, cb);
  assert.strictEqual(c.calls[0].maxRooms, 1);
}]);
cases.push(['moving or fatigued creeps never switch to the creep-aware search', () => {
  const c = creep(35, 10);
  for (let t = 1; t <= 6; t++) { Game.time = 2000 + t; c.pos.x = 35 + t; CMV.to(c, 29, 5, 0, null, 2); }
  const f = creep(35, 10); f.fatigue = 4;
  for (let t = 1; t <= 6; t++) { Game.time = 3000 + t; CMV.to(f, 29, 5, 0, null, 2); }
  assert.ok(c.calls.concat(f.calls).every(o => o.ignoreCreeps === true));
}]);
cases.push(['in range: no move, no search', () => { const c = creep(29, 6); Game.time = 4000; assert.strictEqual(CMV.to(c, 29, 5, 1, null, 2), 0); assert.strictEqual(c.calls.length, 0); }]);
let fail = 0; for (const [n, f] of cases) { try { f(); console.log('ok  ', n); } catch (e) { fail++; console.log('FAIL', n, e.message); } }
console.log(`creep audit 11-11: ${cases.length - fail}/${cases.length}`); process.exit(fail ? 1 : 0);
