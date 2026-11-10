// Stamp B enclosure (src/roles/queen.js buildZones, 2026-11-10 11:26 W46N8).
// After RCL7, filler stands 31,33 and 31,35 are fully enclosed (Spawn3 30,34, link 32,34,
// extensions around them). hasEscape skips those stands. Extension 31,34 was then re-added
// as a range-1 orphan. Its only walkable neighbours are those two dead-end roads, which
// move.js costs at 255, so a queen outside the pocket can never arrive. She retargets and
// PathFinds the impossible goal (repath reason 'n') while orbiting 33,33 / 34,34 / 33,35.
// Reachable west-side orphans (30,32, 31,32, spawn 30,34, ...) must stay assigned.
// node tests/queen_stamp_b_reach.js -> exits 1 on failure
const path = require('path'), fs = require('fs'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, {
  STRUCTURE_SPAWN: 'spawn', STRUCTURE_EXTENSION: 'extension', STRUCTURE_TOWER: 'tower',
  STRUCTURE_ROAD: 'road', STRUCTURE_CONTAINER: 'container', STRUCTURE_RAMPART: 'rampart',
  STRUCTURE_LINK: 'link', RESOURCE_ENERGY: 'energy', TERRAIN_MASK_WALL: 1,
  FIND_HOSTILE_CONSTRUCTION_SITES: 105, FIND_HOSTILE_CREEPS: 103,
  _: { filter: (o, f) => Object.values(o).filter(f) }, Memory: {},
});
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
const plan = require(src('utils/plan.js'));
const structs = plan.upTo('W46N8', 7);
const byType = {}, at = {}, byId = {};
let n = 0;
for (const s of structs) {
  const id = 's' + (++n);
  const cap = s.type === 'spawn' ? 300 : s.type === 'extension' ? 50 : s.type === 'tower' ? 1000 : 0;
  const o = { id, structureType: s.type, pos: { x: s.x, y: s.y }, store: { energy: cap, getFreeCapacity: () => 0 } };
  byId[id] = o;
  (byType[s.type] || (byType[s.type] = [])).push(o);
  const k = s.x * 50 + s.y;
  at[k] = at[k] || {};
  at[k][s.type] = id;
}
const terrain = fs.readFileSync(path.join(__dirname, '..', 'data', 'terrain_W46N8.txt'), 'utf8').trim();
const moves = [];
stub('utils/roomcache.js', {
  get: () => ({ at }),
  all: (_r, t) => byType[t] || [],
  sites: () => [],
  at: () => null,
});
stub('utils/move.js', { to: (_c, x, y, r) => { moves.push([x, y, r]); return false; } });
stub('utils/trace.js', { why() {}, repath() {}, stuck() {}, arrive() {} });
stub('managers/home.js', { active: () => false });
global.Game = { time: 84179540, creeps: {}, getObjectById: id => byId[id] || null };
const Q = require(src('roles/queen.js'));
const room = {
  name: 'W46N8',
  getTerrain: () => ({ get: (x, y) => +terrain[y * 50 + x] || 0 }),
  find: () => [],
};
const has = (t, x, y) => structs.some(s => s.type === t && s.x === x && s.y === y);
const stopsOf = () => { Game.time++; return Q.buildZones(room).flat(); };
const where = (stops, x, y) => stops.filter(s => s.x === x && s.y === y).map(s => s.r);
function queen(x, y) {
  return {
    name: 'queen84178100', memory: { role: 'queen' }, spawning: false, room,
    store: { energy: 800, getFreeCapacity: () => 0, getCapacity: () => 800 },
    pos: {
      x, y,
      getRangeTo(a, b) { return Math.max(Math.abs(this.x - a), Math.abs(this.y - b)); },
      inRangeTo(a, b, r) { return this.getRangeTo(a, b) <= r; },
      isNearTo() { return false; },
    },
  };
}
function setFree(x, y, free) {
  const id = at[x * 50 + y] && (at[x * 50 + y].extension || at[x * 50 + y].spawn || at[x * 50 + y].tower);
  const o = byId[id];
  o.store.energy = (o.structureType === 'spawn' ? 300 : o.structureType === 'extension' ? 50 : 1000) - free;
  o.store.getFreeCapacity = () => free;
}
const cases = [
  ['fixture is the RCL7 enclosure (link 32,34, spawn 30,34, roads 31,33 and 31,35)', () => {
    assert.ok(has('link', 32, 34));
    assert.ok(has('spawn', 30, 34));
    assert.ok(has('extension', 31, 34));
    assert.ok(has('road', 31, 33) && has('road', 31, 35));
  }],
  ['enclosed filler stands are not range-0 stops', () => {
    const stops = stopsOf();
    assert.deepStrictEqual(where(stops, 31, 33), []);
    assert.deepStrictEqual(where(stops, 31, 35), []);
  }],
  ['extension 31,34 is not a range-1 target (unreachable from the open graph)', () => {
    assert.deepStrictEqual(where(stopsOf(), 31, 34), []);
  }],
  ['open stamp-B stands and west orphans that have an outside approach stay assigned', () => {
    const stops = stopsOf();
    for (const [x, y, r] of [[33, 33, 0], [33, 35, 0], [30, 32, 1], [30, 33, 1], [30, 34, 1], [30, 35, 1], [30, 36, 1], [31, 32, 1], [31, 36, 1]])
      assert.deepStrictEqual(where(stops, x, y), [r], 'missing ' + x + ',' + y + ' r' + r);
  }],
  ['lone queen is not given 31,34', () => {
    const c = queen(34, 34);
    Game.creeps = { queen84178100: c };
    const mine = Q.myStops(c, room);
    assert.ok(!mine.some(s => s.x === 31 && s.y === 34));
    assert.ok(mine.some(s => s.x === 33 && s.y === 33 && s.r === 0));
    assert.ok(mine.some(s => s.x === 31 && s.y === 32 && s.r === 1));
  }],
  ['only 31,34 empty: loaded queen does not path it', () => {
    setFree(31, 34, 50);
    moves.length = 0;
    const c = queen(34, 34);
    Game.creeps = { queen84178100: c };
    assert.strictEqual(Q.fillRoute(c), false);
    assert.deepStrictEqual(moves, []);
    setFree(31, 34, 0);
  }],
  ['31,34 and 31,32 both empty: queen paths the reachable orphan, from the orbit tiles too', () => {
    setFree(31, 34, 50);
    setFree(31, 32, 50);
    for (const [x, y] of [[34, 34], [33, 33], [33, 35]]) {
      moves.length = 0;
      const c = queen(x, y);
      Game.creeps = { queen84178100: c };
      assert.strictEqual(Q.fillRoute(c), true, 'at ' + x + ',' + y);
      assert.ok(moves.length >= 1, 'no move from ' + x + ',' + y);
      assert.ok(!moves.some(m => m[0] === 31 && m[1] === 34), 'pathed 31,34 from ' + x + ',' + y + ' -> ' + JSON.stringify(moves));
      assert.deepStrictEqual(moves[0], [31, 32, 1], 'from ' + x + ',' + y + ' -> ' + JSON.stringify(moves));
    }
    setFree(31, 34, 0);
    setFree(31, 32, 0);
  }],
];
let fail = 0;
for (const [name, fn] of cases) {
  try { fn(); console.log('ok  ', name); }
  catch (e) { fail++; console.log('FAIL', name, e.stack || e.message); }
}
console.log(`queen stamp B reach: ${cases.length - fail}/${cases.length}`);
process.exit(fail ? 1 : 0);
