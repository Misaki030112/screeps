// w8guard84238816 stood on 33,28: the exit-only cost matrix searched through extension 32,27.
// With structures (roads 1, container/rampart open, other structures 255) the first step is 32,29.
// node tests/military_structures.js
const path = require('path'), fs = require('fs'), assert = require('assert');
const ROOT = path.join(__dirname, '..');
const TERR = fs.readFileSync(path.join(ROOT, 'data/terrain_W47N8.txt'), 'utf8').trim();
const ROADS = require(path.join(ROOT, 'src/rooms/w47n8/roads.js')).ROADS;
const ROOM = 'W47N8';
const DIRS = { 1: [0, -1], 2: [1, -1], 3: [1, 0], 4: [1, 1], 5: [0, 1], 6: [-1, 1], 7: [-1, 0], 8: [-1, -1] };
const terr = (x, y) => TERR.charCodeAt(y * 50 + x) - 48; // 0 plain, 1 wall, 2 swamp, 3 wall+swamp
const wall = (x, y) => (terr(x, y) & 1) !== 0;
const swamp = (x, y) => (terr(x, y) & 2) !== 0;

class CM {
  constructor() { this.a = new Uint8Array(2500); }
  get(x, y) { return this.a[x * 50 + y]; }
  set(x, y, v) { this.a[x * 50 + y] = v; }
  clone() { const c = new CM(); c.a = this.a.slice(); return c; }
}
const ext = (x, y) => ({ structureType: 'extension', pos: { x, y }, my: true });
const structs = [ext(32, 27), ext(32, 28), { structureType: 'container', pos: { x: 32, y: 29 } }]
  .concat(ROADS.map(([x, y]) => ({ structureType: 'road', pos: { x, y } })));
let forced = null, searches = 0, last = null;
function search(from, goal, opts) {
  searches++;
  const room = from.roomName || ROOM;
  const mat = opts && opts.roomCallback ? opts.roomCallback(room) : null;
  if (forced) { last = { matrix: mat, path: forced.path, incomplete: !!forced.incomplete }; return forced; }
  if (mat === false) { last = { matrix: mat, path: [], incomplete: true }; return { path: [], incomplete: true }; }
  const plain = (opts && opts.plainCost) || 2, swampC = (opts && opts.swampCost) || 10;
  const range = goal.range || 0, gx = goal.pos.x, gy = goal.pos.y;
  const cost = (x, y) => {
    if (wall(x, y)) return 255;
    const v = mat && mat.get ? mat.get(x, y) : 0;
    if (v >= 255) return 255;
    if (v > 0) return v;
    return swamp(x, y) ? swampC : plain;
  };
  const INF = 1e15, dist = new Float64Array(2500), prev = new Int32Array(2500);
  dist.fill(INF); prev.fill(-1);
  const start = from.x * 50 + from.y;
  dist[start] = 0;
  const used = new Uint8Array(2500);
  let end = -1;
  for (let n = 0; n < 2500; n++) {
    let k = -1, best = INF;
    for (let i = 0; i < 2500; i++) if (!used[i] && dist[i] < best) { best = dist[i]; k = i; }
    if (k < 0) break;
    used[k] = 1;
    const x = Math.floor(k / 50), y = k % 50;
    if (Math.max(Math.abs(x - gx), Math.abs(y - gy)) <= range) { end = k; break; }
    for (let d = 1; d <= 8; d++) {
      const nx = x + DIRS[d][0], ny = y + DIRS[d][1];
      if (nx < 0 || ny < 0 || nx > 49 || ny > 49) continue;
      const c = cost(nx, ny);
      if (c >= 255) continue;
      const nk = nx * 50 + ny;
      if (dist[k] + c < dist[nk]) { dist[nk] = dist[k] + c; prev[nk] = k; }
    }
  }
  const path = [];
  if (end >= 0) {
    let k = end;
    while (k !== start && k >= 0) { path.push({ x: Math.floor(k / 50), y: k % 50 }); k = prev[k]; }
    path.reverse();
  }
  last = { matrix: mat, path, incomplete: end < 0, cost: end < 0 ? Infinity : dist[end] };
  return { path, incomplete: end < 0, cost: last.cost };
}
global.OK = 0;
global.ERR_TIRED = -11;
global.ERR_NO_PATH = -2;
global.LOOK_CREEPS = 'creep';
global.TERRAIN_MASK_WALL = 1;
global.TERRAIN_MASK_SWAMP = 2;
global.FIND_STRUCTURES = 1;
global.FIND_CONSTRUCTION_SITES = 2;
global.FIND_MY_CONSTRUCTION_SITES = 3;
global.FIND_HOSTILE_CONSTRUCTION_SITES = 4;
global.FIND_CREEPS = 5;
global.STRUCTURE_ROAD = 'road';
global.STRUCTURE_CONTAINER = 'container';
global.STRUCTURE_RAMPART = 'rampart';
global.STRUCTURE_EXTENSION = 'extension';
global.RoomPosition = function (x, y, roomName) { this.x = x; this.y = y; this.roomName = roomName; };
global.PathFinder = { CostMatrix: CM, search };
const room = {
  name: ROOM,
  getTerrain: () => ({ get: terr }),
  find(type) {
    if (type === FIND_STRUCTURES) return structs;
    return [];
  },
  lookForAt: () => [],
};
global.Game = { time: 84238970, creeps: {}, rooms: { [ROOM]: room }, getObjectById: () => null };
global.Memory = {};

const CMV = require(path.join(ROOT, 'src/utils/combatmove.js'));
const mil = require(path.join(ROOT, 'src/utils/military.js'));
const move = require(path.join(ROOT, 'src/utils/move.js'));

// Same exit / seal paint as roles.js w8guard, w8defender, w8healer. No structure costs.
const exits = (m) => { for (let i = 0; i < 50; i++) { m.set(i, 0, 255); m.set(0, i, 255); m.set(49, i, 255); m.set(i, 49, 255); } return m; };
const guardCb = (rn, m) => (rn !== ROOM ? false : exits(m));
const defenderCb = (rn, m) => {
  if (rn !== ROOM) return false;
  for (let i = 0; i < 50; i++) for (let y = 0; y <= 3; y++) m.set(i, y, 255);
  return exits(m);
};
const healerCb = (rn, m) => {
  if (rn !== ROOM) return false;
  for (let i = 0; i < 50; i++) for (let y = 0; y <= 4; y++) m.set(i, y, 255);
  return exits(m);
};
function creep(role, x, y) {
  const c = {
    name: role + '84238816', my: true, spawning: false, fatigue: 0,
    memory: { role, _move: { path: 'stale' }, _m: { k: 'stale' } },
    room, moves: [],
    pos: { x, y, roomName: ROOM },
  };
  c.pos.getDirectionTo = (tx, ty) => {
    for (const k of Object.keys(DIRS)) if (c.pos.x + DIRS[k][0] === tx && c.pos.y + DIRS[k][1] === ty) return +k;
    return 0;
  };
  c.pos.inRangeTo = (tx, ty, r) => Math.max(Math.abs(c.pos.x - tx), Math.abs(c.pos.y - ty)) <= r;
  c.move = d => c.moves.push(d);
  c.moveTo = () => { c.moves.push('moveTo'); return 0; };
  return c;
}
function dest(c) {
  const d = c.moves[c.moves.length - 1];
  if (!d || !DIRS[d]) return null;
  return { x: c.pos.x + DIRS[d][0], y: c.pos.y + DIRS[d][1] };
}
const xy = p => p.x + ',' + p.y;
const building = (x, y) => structs.some(s => s.pos.x === x && s.pos.y === y && s.structureType === 'extension');

const guard = creep('w8guard', 33, 28);
searches = 0;
assert.strictEqual(CMV.to(guard, 29, 5, 0, guardCb, 2), 0, 'composed step returns OK');
const step1 = dest(guard);
assert.ok(step1, 'guard issued a move');
assert.deepStrictEqual([step1.x, step1.y], [32, 29], 'first step is the container/road at 32,29, got ' + step1.x + ',' + step1.y);
assert.ok(!building(step1.x, step1.y), 'first step is not an extension');
assert.deepStrictEqual(last.path.slice(0, 4).map(xy), ['32,29', '31,28', '31,27', '31,26'], last.path.slice(0, 8).map(xy).join(' -> '));
assert.strictEqual(last.incomplete, false, 'structure-aware search completes');
assert.strictEqual(last.path.length, 28, 'live path length with structures, got ' + last.path.length);
assert.strictEqual(last.matrix.get(32, 27), 255, 'extension 32,27 is impassable in the search matrix');
assert.strictEqual(last.matrix.get(32, 28), 255, 'extension 32,28 is impassable in the search matrix');
assert.ok(last.matrix.get(32, 29) > 0 && last.matrix.get(32, 29) < 255, 'container/road 32,29 stays walkable');
assert.strictEqual(last.matrix.get(24, 0), 255, 'guard callback still blocks exit tiles');
assert.ok(last.matrix.get(29, 4) < 255, 'guard callback does not seal the inner rows');
assert.strictEqual(move.matrix(ROOM, false).get(24, 0), 50, 'exit paint stays on the clone; civilian matrix keeps cost 50');
assert.ok(!guard.memory._move && !guard.memory._m, 'military step drops both path caches');
const searchesAfter = searches;
guard.moves = [];
assert.strictEqual(CMV.to(guard, 29, 5, 0, guardCb, 2), 0);
assert.strictEqual(searches, searchesAfter + 1, 'the next tick searches again');
assert.deepStrictEqual([dest(guard).x, dest(guard).y], [32, 29]);

for (const [role, cb, sealY] of [['w8defender', defenderCb, 3], ['w8healer', healerCb, 4]]) {
  const c = creep(role, 33, 28);
  assert.strictEqual(CMV.to(c, 29, 5, 0, cb, 3), 0, role);
  const d = dest(c);
  assert.deepStrictEqual([d.x, d.y], [32, 29], role + ' first step, got ' + d.x + ',' + d.y);
  assert.ok(!building(d.x, d.y));
  assert.strictEqual(last.matrix.get(29, sealY), 255, role + ' seal row stays blocked');
  assert.strictEqual(last.matrix.get(32, 27), 255, role + ' sees the extension');
  assert.strictEqual(last.matrix.get(0, 10), 255, role + ' still blocks exits');
}

// Same callback, but step() is handed the exit-only matrix directly (no structure seed).
// Live shape: complete, 26 steps, first tile extension 32,27. That move must not be issued.
const blind = creep('w8guard', 33, 28);
forced = null;
const blindSt = mil.step(blind, 29, 5, 0, rn => (rn === ROOM ? exits(new CM()) : false));
assert.strictEqual(blindSt, 'no', 'structure-blind path is not followed');
assert.strictEqual(blind.moves.length, 0, 'no move onto the extension');
assert.strictEqual(last.incomplete, false);
assert.strictEqual(last.path.length, 26, 'blind search length, got ' + last.path.length);
assert.deepStrictEqual([last.path[0].x, last.path[0].y], [32, 27], 'blind search still names the extension');
assert.ok(building(32, 27));

// Incomplete result that names the extension is dropped too. A walkable incomplete step is kept.
forced = { path: [{ x: 32, y: 27 }, { x: 31, y: 26 }], incomplete: true };
const inc = creep('w8guard', 33, 28);
assert.strictEqual(CMV.to(inc, 29, 5, 0, guardCb, 2), -2, 'incomplete path onto a building returns ERR_NO_PATH');
assert.strictEqual(inc.moves.length, 0);
forced = { path: [{ x: 32, y: 29 }], incomplete: true };
const incOk = creep('w8guard', 33, 28);
assert.strictEqual(CMV.to(incOk, 29, 5, 0, guardCb, 2), 0, 'incomplete path onto a walkable tile is still taken');
assert.deepStrictEqual([dest(incOk).x, dest(incOk).y], [32, 29]);
forced = null;

// Adjacent to the extension: the one-tile fallback must not step onto it either.
const beside = creep('w8guard', 31, 27);
assert.strictEqual(CMV.to(beside, 32, 27, 0, guardCb, 2), -2);
assert.strictEqual(beside.moves.length, 0, 'fallback does not enter the extension');

// Civilians keep the stuck-3 moveTo cache. They do not take the military search.
const hauler = creep('hauler', 20, 20);
const before = searches;
assert.strictEqual(CMV.to(hauler, 22, 22, 0, guardCb, 5), 0);
assert.strictEqual(hauler.moves[0], 'moveTo');
assert.strictEqual(searches, before, 'civilian move does not run the military search');

console.log('military structures ok');
