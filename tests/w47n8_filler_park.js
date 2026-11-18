// Full w8fillers with nothing to fill used to swap off POST 34,32 every tick.
// The one that arrived stopped calling move.to, so its stuck counter never reset and the
// pair bounced ~11 ticks (until stuck-8) on 34,32↔33,31 / 33,33 / 34,33 / 35,31, store still 1200.
// Park drops the path and will not step onto a post another filler already holds.
// node tests/w47n8_filler_park.js
const assert = require('assert'), fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..');
const T = fs.readFileSync(path.join(ROOT, 'data/terrain_W47N8.txt'), 'utf8').trim();
const C = require(path.join(ROOT, 'src/rooms/w47n8/config.js'));
const L = require(path.join(ROOT, 'src/rooms/w47n8/layout.js'));

assert.deepStrictEqual(C.SPAWN, [15, 18], 'spawn anchor stays');
assert.ok(L.ORDER.extension.some(([x, y]) => x === 32 && y === 34), 'extension 32,34 stays');

const DXY = { 1: [0, -1], 2: [1, -1], 3: [1, 0], 4: [1, 1], 5: [0, 1], 6: [-1, 1], 7: [-1, 0], 8: [-1, -1] };
function dirTo(x1, y1, x2, y2) {
  const dx = x2 - x1, dy = y2 - y1;
  if (!dx && !dy) return 0;
  const adx = Math.abs(dx), ady = Math.abs(dy);
  if (adx > ady * 2) return dx > 0 ? 3 : 7;
  if (ady > adx * 2) return dy > 0 ? 5 : 1;
  if (dx > 0 && dy < 0) return 2;
  if (dx > 0 && dy > 0) return 4;
  if (dx < 0 && dy > 0) return 6;
  return 8;
}
class RoomPosition {
  constructor(x, y, r) { this.x = x; this.y = y; this.roomName = r || 'W47N8'; }
  getRangeTo(a, b) { const p = typeof a === 'number' ? { x: a, y: b } : (a.pos || a); return Math.max(Math.abs(this.x - p.x), Math.abs(this.y - p.y)); }
  inRangeTo(a, b, c) { return typeof a === 'number' ? this.getRangeTo(a, b) <= c : this.getRangeTo(a) <= b; }
  isNearTo(a, b) { return this.getRangeTo(a, b) <= 1; }
  getDirectionTo(x, y) { const p = typeof x === 'number' ? { x, y } : (x.pos || x); return dirTo(this.x, this.y, p.x, p.y); }
}
class CM {
  constructor() { this.a = new Uint8Array(2500); }
  get(x, y) { return this.a[x * 50 + y]; }
  set(x, y, v) { this.a[x * 50 + y] = v; }
  clone() { const c = new CM(); c.a = this.a.slice(); return c; }
}
function search(origin, goal, opts) {
  const range = goal.range || 0, gx = goal.pos.x, gy = goal.pos.y, mat = opts.roomCallback && opts.roomCallback(origin.roomName);
  const plain = opts.plainCost || 1, swamp = opts.swampCost || 5;
  const cost = (x, y) => {
    if (x < 1 || y < 1 || x > 48 || y > 48) return 255;
    const ter = T.charCodeAt(y * 50 + x) - 48;
    if (ter & 1) return 255;
    const mc = mat ? mat.get(x, y) : 0;
    if (mc === 255) return 255;
    if (mc > 0) return mc;
    return ter & 2 ? swamp : plain;
  };
  const key = (x, y) => x * 50 + y, dist = new Map([[key(origin.x, origin.y), 0]]), prev = new Map(), q = [[0, origin.x, origin.y]];
  let best = null, bestG = 1e9;
  while (q.length) {
    q.sort((a, b) => a[0] - b[0]);
    const [g, x, y] = q.shift();
    if (g !== dist.get(key(x, y))) continue;
    if (!(x === origin.x && y === origin.y) && Math.max(Math.abs(x - gx), Math.abs(y - gy)) <= range) { best = [x, y]; bestG = g; break; }
    for (const [dx, dy] of Object.values(DXY)) {
      const nx = x + dx, ny = y + dy, cc = cost(nx, ny);
      if (cc >= 255) continue;
      const ng = g + cc, nk = key(nx, ny);
      if (ng < (dist.get(nk) ?? 1e9)) { dist.set(nk, ng); prev.set(nk, key(x, y)); q.push([ng, nx, ny]); }
    }
  }
  if (!best) return { path: [], incomplete: true, cost: Infinity };
  const path = []; let k = key(best[0], best[1]);
  while (k !== key(origin.x, origin.y)) { path.push({ x: Math.floor(k / 50), y: k % 50 }); k = prev.get(k); }
  path.reverse();
  return { path, incomplete: false, cost: bestG };
}
global.RoomPosition = RoomPosition;
global.PathFinder = { CostMatrix: CM, search };
global._ = { minBy: (a, f) => a.reduce((b, x) => (b == null || f(x) < f(b) ? x : b), null) };
Object.assign(global, {
  FIND_MY_STRUCTURES: 10, FIND_STRUCTURES: 5, FIND_MY_CREEPS: 3, FIND_MY_CONSTRUCTION_SITES: 1,
  FIND_CONSTRUCTION_SITES: 11, FIND_HOSTILE_CONSTRUCTION_SITES: 12, FIND_CREEPS: 13,
  STRUCTURE_EXTENSION: 'extension', STRUCTURE_SPAWN: 'spawn', STRUCTURE_TOWER: 'tower', STRUCTURE_ROAD: 'road',
  STRUCTURE_RAMPART: 'rampart', STRUCTURE_CONTAINER: 'container', STRUCTURE_STORAGE: 'storage', STRUCTURE_LINK: 'link',
  STRUCTURE_TERMINAL: 'terminal', RESOURCE_ENERGY: 'energy', LOOK_STRUCTURES: 'ls', LOOK_CREEPS: 'creep',
  OK: 0, ERR_NOT_IN_RANGE: -9, ERR_FULL: -8, ERR_NOT_ENOUGH_RESOURCES: -6, ERR_TIRED: -11,
  CARRY: 'carry', MOVE: 'move', TERRAIN_MASK_WALL: 1, TERRAIN_MASK_SWAMP: 2,
  Memory: { ops: {} }, RawMemory: { segments: {}, setActiveSegments() {} },
  Game: { time: 5000, rooms: {}, creeps: {}, getObjectById: id => OBJ[id] },
});
let OBJ = {}, creeps = [];
const st = (cap, e) => {
  const s = { energy: e };
  Object.defineProperties(s, {
    getFreeCapacity: { value: () => cap - s.energy },
    getCapacity: { value: () => cap },
    getUsedCapacity: { value: () => s.energy },
  });
  return s;
};
const BLOCK = new Set(['spawn', 'extension', 'tower', 'storage', 'link', 'terminal']);
function add(t, x, y, e, cap) {
  const s = { id: t + x + '_' + y, structureType: t, my: true, pos: new RoomPosition(x, y), hits: 1, hitsMax: 1 };
  if (cap) s.store = st(cap, e || 0);
  OBJ[s.id] = s; return s;
}
function build() {
  OBJ = {}; creeps = [];
  for (const [x, y] of L.ORDER.extension.slice(0, 10)) add('extension', x, y, 100, 100);
  add('spawn', 34, 30, 300, 300);
  add('spawn', 33, 30, 300, 300);
  add('storage', 35, 32, 3000, 1e6);
  add('terminal', 33, 32, 0, 300000);
  add('link', 32, 33, 800, 800); // primed: idle must not ferry
  add('container', 33, 33, 0, 2000);
  add('container', 13, 26, 1500, 2000);
  add('link', 13, 25, 800, 800);
  for (const [x, y] of [[34, 32], [33, 31], [33, 33], [34, 33], [35, 31], [33, 34], [32, 35]]) add('road', x, y);
  const all = () => Object.values(OBJ);
  const room = {
    name: 'W47N8', controller: { level: 7, my: true }, memory: {},
    get energyAvailable() { return all().filter(s => s.structureType === 'extension' || s.structureType === 'spawn').reduce((a, s) => a + s.store.energy, 0); },
    get energyCapacityAvailable() { return all().filter(s => s.structureType === 'extension' || s.structureType === 'spawn').reduce((a, s) => a + s.store.getCapacity(), 0); },
    find: t => (t === 10 || t === 5) ? all() : (t === 3 || t === 13) ? creeps.slice() : [],
    lookForAt: (k, x, y) => k === 'ls' ? all().filter(s => s.pos.x === x && s.pos.y === y)
      : (k === 'creep' ? creeps.filter(c => c.pos.x === x && c.pos.y === y) : []),
    getTerrain: () => ({ get: (x, y) => T.charCodeAt(y * 50 + x) - 48 }),
  };
  room.storage = all().find(s => s.structureType === 'storage');
  Game.rooms.W47N8 = room;
  Game.creeps = {};
  return room;
}
function walkable(x, y) {
  if (x <= 0 || y <= 0 || x >= 49 || y >= 49) return false;
  if ((T.charCodeAt(y * 50 + x) - 48) & 1) return false;
  return !Object.values(OBJ).some(s => BLOCK.has(s.structureType) && s.pos.x === x && s.pos.y === y);
}
let nid = 1;
function mk(x, y, energy, name) {
  const body = Array(24).fill('carry').concat(Array(12).fill('move'));
  const c = {
    id: 'c' + nid, name, memory: { role: 'w8filler', home: 'W47N8' },
    body: body.map(type => ({ type, hits: 100 })), pos: new RoomPosition(x, y), fatigue: 0,
    ticksToLive: 1400, my: true, spawning: false,
    get room() { return Game.rooms.W47N8; },
    getActiveBodyparts: t => body.filter(p => p === t).length,
    move(d) { if (this.fatigue > 0) return -11; this._dir = d; return 0; },
    transfer(s) {
      if (!this.pos.isNearTo(s)) return -9;
      const a = Math.min(this.store.energy, s.store.getFreeCapacity());
      if (a <= 0) return -8;
      this._act = () => { this.store.energy -= a; s.store.energy += a; };
      return 0;
    },
    withdraw(s) {
      if (!this.pos.isNearTo(s)) return -9;
      const a = Math.min(s.store.energy, this.store.getFreeCapacity());
      if (a <= 0) return -6;
      this._act = () => { s.store.energy -= a; this.store.energy += a; };
      return 0;
    },
  };
  c.store = st(1200, energy);
  nid++; creeps.push(c); Game.creeps[name] = c; return c;
}
function tcost(x, y) { return Object.values(OBJ).some(s => s.structureType === 'road' && s.pos.x === x && s.pos.y === y) ? 1 : 2; }
function step(F) {
  for (const c of creeps) { c._act = null; c._dir = null; }
  for (const c of creeps) { F.run(c); if (c._act) c._act(); }
  for (const c of creeps) {
    c._nx = null;
    if (!c._dir || c.fatigue > 0) continue;
    const [dx, dy] = DXY[c._dir];
    c._nx = c.pos.x + dx; c._ny = c.pos.y + dy;
  }
  for (const c of creeps) if (c._nx != null && walkable(c._nx, c._ny)) {
    const occ = creeps.filter(o => o !== c && o.pos.x === c._nx && o.pos.y === c._ny);
    if (occ.length && occ.every(o => o._nx == null || (o._nx === o.pos.x && o._ny === o.pos.y))) continue;
    const loaded = Math.ceil(c.store.energy / 50);
    c.fatigue += tcost(c._nx, c._ny) * Math.min(loaded, c.getActiveBodyparts('carry'));
    c.pos = new RoomPosition(c._nx, c._ny);
  }
  for (const c of creeps) c.fatigue = Math.max(0, c.fatigue - 2 * c.getActiveBodyparts('move'));
  Game.time++;
}
const enc = (x, y) => String.fromCharCode(x * 50 + y + 192);
function hot(c, x, y) {
  // Live shape: already stuck on the approach tile, target still POST.
  c.memory._m = { k: '34,32,0', p: enc(x, y) + enc(34, 32), s: 7, v: 1, n: 1, t0: Game.time, l: enc(x, y) };
}

delete require.cache[require.resolve(path.join(ROOT, 'src/rooms/w47n8/fill.js'))];
delete require.cache[require.resolve(path.join(ROOT, 'src/utils/move.js'))];
const F = require(path.join(ROOT, 'src/rooms/w47n8/fill.js'));
assert.deepStrictEqual(F.POST, [34, 32]);
assert.strictEqual(F.POST_COST, 4);

function run(n, fn) {
  Game.time += 2000;
  build();
  const cs = fn();
  const seen = [];
  for (let i = 0; i < n; i++) { step(F); seen.push(cs.map(c => c.pos.x + ',' + c.pos.y + ':' + c.store.energy).join('|')); }
  return seen;
}
function stable(seen, from) {
  const tail = seen.slice(from);
  assert.ok(tail.length >= 8, 'need a stable tail');
  assert.ok(tail.every(s => s === tail[0]), 'kept moving after park:\n' + tail.join('\n'));
}

// Hot stuck memory, the live failure: both full, post + pocket. Must not bounce.
{
  const seen = run(16, () => {
    const a = mk(34, 32, 1200, 'A'), b = mk(33, 31, 1200, 'B');
    hot(a, 34, 32); hot(b, 33, 31);
    return [a, b];
  });
  stable(seen, 0);
  assert.ok(seen[0].startsWith('34,32:1200|'), 'the filler on the post stays: ' + seen[0]);
  assert.ok(seen.every(s => s.includes('1200')), 'carry stays full while parked');
}
// Same bounce from the other three live pairs, plus a filler that still has to walk in.
{
  for (const [x, y] of [[33, 33], [34, 33], [35, 31]]) {
    const seen = run(16, () => [mk(34, 32, 1200, 'A'), mk(x, y, 1200, 'B')]);
    stable(seen, 1);
    assert.ok(seen[seen.length - 1].startsWith('34,32:1200|'), x + ',' + y + ' left the post empty: ' + seen[seen.length - 1]);
  }
  const seen = run(8, () => [mk(35, 31, 1200, 'solo')]);
  assert.ok(seen[0].startsWith('34,32:1200'), 'a lone full filler still takes an open post');
  stable(seen, 0);
}
// An empty filler may still take the post to withdraw. Fill rules are unchanged.
// Once both carries are full, they stand — no second round of swapping.
{
  let empty;
  const seen = run(24, () => { empty = mk(33, 31, 0, 'empty'); return [mk(34, 32, 1200, 'full'), empty]; });
  assert.ok(empty.store.energy > 0, 'empty filler withdrew, e=' + empty.store.energy + ' trace ' + seen.slice(0, 6).join(' / '));
  const both = seen.filter(s => s.split('|').every(p => p.endsWith(':1200')));
  assert.ok(both.length >= 8, 'both carries full for a stretch: ' + seen.join(' / '));
  stable(both, both.length - 8);
}
// Duty is not loosened: a drained spawn is still filled, then the filler parks on the post.
{
  let spawn;
  const seen = run(20, () => {
    spawn = Object.values(OBJ).find(s => s.structureType === 'spawn' && s.pos.x === 34 && s.pos.y === 30);
    spawn.store.energy = 0;
    return [mk(34, 32, 1200, 'A')];
  });
  assert.ok(spawn.store.energy > 0, 'spawn 34,30 was not filled');
  assert.ok(seen[seen.length - 1].startsWith('34,32:'), 'returns to the post after the fill: ' + seen[seen.length - 1]);
}
console.log('w47n8 filler park ok');
