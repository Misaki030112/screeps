// Stuck-2 detour guard (src/utils/move.js): when a creep blocks the cached path, the creep-avoiding repath is
// taken only if it costs at most DETOUR more than the rest of the blocked path; otherwise the creep keeps its
// path and waits for the stuck-4 swap. node tests/move_detour.js -> exits 1 on failure
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
const SWAMP = new Set(['33,30', '33,29', '33,28']); // detour tiles
let altCost, moves, searches;
class CM { constructor() { this.d = {}; } get(x, y) { return this.d[x + ',' + y] || 0; } set(x, y, v) { this.d[x + ',' + y] = v; } clone() { const c = new CM(); Object.assign(c.d, this.d); return c; } }
Object.assign(global, { TERRAIN_MASK_WALL: 1, TERRAIN_MASK_SWAMP: 2, FIND_STRUCTURES: 1, FIND_CONSTRUCTION_SITES: 2, FIND_MY_CONSTRUCTION_SITES: 3, FIND_CREEPS: 4, LOOK_CREEPS: 'creep',
  STRUCTURE_ROAD: 'road', STRUCTURE_CONTAINER: 'container', STRUCTURE_RAMPART: 'rampart', Game: { time: 100, rooms: {} },
  RoomPosition: function (x, y, r) { this.x = x; this.y = y; this.roomName = r; },
  PathFinder: { CostMatrix: CM, search: () => { searches++; return { path: [{ x: 33, y: 30 }, { x: 33, y: 29 }, { x: 33, y: 28 }, { x: 34, y: 27 }], cost: altCost }; } } });
stub('utils/trace.js', { repath() {}, stuck() {}, arrive() {} });
stub('utils/plan.js', { get: () => ({ standing: new Set() }) });
const move = require(src('utils/move.js'));
const enc = (x, y) => String.fromCharCode(x * 50 + y + 192);
const room = { name: 'W1N1', find: () => [], getTerrain: () => ({ get: (x, y) => (SWAMP.has(x + ',' + y) ? 2 : 0) }), lookForAt: () => [] };
Game.rooms.W1N1 = room;
function blocked(cost) {
  altCost = cost; moves = []; searches = 0;
  // cached path (plain tiles, rest cost 4 x 2 = 8) 34,31 -> 34,30 -> 34,29 -> 34,28 -> 34,27 (goal 34,27 range 0); creep stuck on 34,31 for 2 ticks
  const p = [enc(34, 31), enc(34, 30), enc(34, 29), enc(34, 28), enc(34, 27)].join('');
  const c = { name: 'h', room, fatigue: 0, pos: { x: 34, y: 31, getDirectionTo: (x, y) => (y < 31 ? (x > 34 ? 2 : x < 34 ? 8 : 1) : 3) }, move: d => moves.push(d), memory: {} };
  move.to(c, 34, 27, 0); // computes version so the cached path below is current
  moves = []; searches = 0;
  c.memory._m = { k: '34,27,0', p, s: 1, l: enc(34, 31), v: c.memory._m.v, n: 4, t0: 90 };
  move.to(c, 34, 27, 0);
  return { c, p };
}
const cases = [
  ['costly creep-avoiding path (swamp detour) -> keep blocked road path, no move', () => {
    const { c, p } = blocked(8 + 13); assert.strictEqual(c.memory._m.p, p); assert.deepStrictEqual(moves, []); assert.strictEqual(searches, 1); }],
  ['cheap creep-avoiding path -> take it and move', () => {
    const { c, p } = blocked(8 + 12); assert.notStrictEqual(c.memory._m.p, p); assert.deepStrictEqual(moves, [8]); }],
  ['stuck 3 after a kept path -> no new search, keeps pushing toward the blocker', () => {
    const { c } = blocked(99); searches = 0; moves = []; move.to(c, 34, 27, 0); assert.strictEqual(searches, 0); assert.deepStrictEqual(moves, [1]); }],
];
let fail = 0; for (const [n, f] of cases) { try { f(); console.log('ok  ', n); } catch (e) { fail++; console.log('FAIL', n, e.stack); } }
console.log(`move detour: ${cases.length - fail}/${cases.length}`); process.exit(fail ? 1 : 0);
