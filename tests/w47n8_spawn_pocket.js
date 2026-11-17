// Spawn-pocket handoff. The filler idles on road 34,32, which is the cheap step from both hub
// spawns (33,30 / 34,30) onto the south road. yieldPost makes that tile cost more than the
// one-plain bypass 32,32 → 33,33, and less than the north walk out 32,29. Extension 32,34
// stays; C.SPAWN stays the old anchor (retargeting it would pull the live spawn off filler duty).
const assert = require('assert'), fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..');
const T = fs.readFileSync(path.join(ROOT, 'data/terrain_W47N8.txt'), 'utf8').trim();
const L = require(path.join(ROOT, 'src/rooms/w47n8/layout.js'));
const R = require(path.join(ROOT, 'src/rooms/w47n8/roads.js'));
const C = require(path.join(ROOT, 'src/rooms/w47n8/config.js'));
const F = require(path.join(ROOT, 'src/rooms/w47n8/fill.js'));

assert.deepStrictEqual(C.SPAWN, [15, 18], 'old spawn anchor stays; it is not the pocket bug');
assert.ok(L.ORDER.extension.some(([x, y]) => x === 32 && y === 34), 'extension 32,34 stays');
assert.deepStrictEqual(L.ORDER.link, [[32, 33]], 'hub link stays at 32,33');
assert.strictEqual(F.POST_COST, 4);

const fake = { a: new Uint8Array(2500), get(x, y) { return this.a[x * 50 + y]; }, set(x, y, v) { this.a[x * 50 + y] = v; } };
fake.set(34, 32, 1);
assert.strictEqual(F.yieldPost(fake), fake);
assert.strictEqual(fake.get(34, 32), 4, 'open post is yielded');
fake.set(34, 32, 255);
F.yieldPost(fake);
assert.strictEqual(fake.get(34, 32), 255, 'a blocked post stays blocked');
fake.set(34, 32, 1);
assert.strictEqual(F.yieldPost('W47N8', fake), fake);
assert.strictEqual(fake.get(34, 32), 4, 'moveTo-style (roomName, matrix) also yields the post');

const block = new Set();
function mark(list) { for (const [x, y] of list) block.add(x + ',' + y); }
mark(L.ORDER.spawn.slice(0, 2));
mark(L.ORDER.tower.slice(0, 3));
mark(L.ORDER.extension.slice(0, 50));
mark(L.ORDER.storage);
mark([[32, 33], [13, 25], [26, 12]]);
mark(L.ORDER.terminal);
const roads = new Set();
for (const p of R.ROADS) roads.add(p[0] + ',' + p[1]);
for (const p of L.ORDER.road || []) roads.add(p[0] + ',' + p[1]);

function route(sx, sy, gx, gy, range, extra) {
  const key = (x, y) => x * 50 + y;
  const h = (x, y) => Math.max(Math.abs(x - gx), Math.abs(y - gy));
  const cost = (x, y) => {
    if (x < 0 || y < 0 || x > 49 || y > 49) return 255;
    if (T[y * 50 + x] === '1' || block.has(x + ',' + y)) return 255;
    if (extra && extra.has(x + ',' + y)) return 255;
    if (x === 34 && y === 32) return F.POST_COST;
    if (roads.has(x + ',' + y)) return 1;
    return T[y * 50 + x] === '2' ? 10 : 2;
  };
  const open = [[0, 0, sx, sy]];
  const gs = new Map([[key(sx, sy), 0]]), prev = new Map(), seen = new Set();
  while (open.length) {
    open.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    const [, g, x, y] = open.shift();
    const k = key(x, y);
    if (seen.has(k) || g !== gs.get(k)) continue;
    seen.add(k);
    if (!(x === sx && y === sy) && h(x, y) <= range) {
      const path = []; let c = k;
      while (c !== undefined) { path.push(Math.floor(c / 50) + ',' + (c % 50)); c = prev.get(c); }
      return path.reverse();
    }
    for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) if (dx || dy) {
      const nx = x + dx, ny = y + dy, cc = (nx === sx && ny === sy) ? 0 : cost(nx, ny);
      if (cc >= 255) continue;
      const nk = key(nx, ny), ng = g + cc;
      if (ng < (gs.get(nk) ?? 1e9)) { gs.set(nk, ng); prev.set(nk, k); open.push([ng + 1.2 * h(nx, ny), ng, nx, ny]); }
    }
  }
  return null;
}
function south(path, label) {
  assert.ok(path, label + ' has a path');
  assert.ok(path.includes('32,32'), label + ' uses the 32,32 bypass: ' + path.slice(0, 8).join(' '));
  assert.ok(path.includes('32,35'), label + ' joins the south road at 32,35');
  assert.ok(!path.includes('34,32'), label + ' does not step on the filler post');
  assert.ok(!path.includes('32,29'), label + ' does not take the north walk');
}
for (const start of [[33, 30], [34, 30]]) {
  south(route(start[0], start[1], 12, 25, 0), start.join(',') + ' stand');
  south(route(start[0], start[1], 14, 26, 0), start.join(',') + ' stand 14,26');
  south(route(start[0], start[1], 14, 27, 0), start.join(',') + ' stand 14,27');
  south(route(start[0], start[1], 11, 43, 1), start.join(',') + ' source B');
  south(route(start[0], start[1], 27, 49, 0), start.join(',') + ' south exit');
}
const fallback = route(33, 30, 12, 25, 0, new Set(['32,32']));
assert.ok(fallback.includes('34,32') && !fallback.includes('32,29'), '32,32 blocked still uses the post, not the north walk: ' + fallback.slice(0, 8).join(' '));

// move.to's cached matrix paints the same cost (rhaulers, reserve7, hauler delivery).
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
class CM {
  constructor() { this.a = new Uint8Array(2500); }
  get(x, y) { return this.a[x * 50 + y]; }
  set(x, y, v) { this.a[x * 50 + y] = v; }
  clone() { const c = new CM(); c.a = this.a.slice(); return c; }
}
global.PathFinder = { CostMatrix: CM, search() { return { path: [], incomplete: true }; } };
const structs = R.ROADS.map(([x, y]) => ({ structureType: 'road', pos: { x, y } }));
global.Game = {
  time: 1, creeps: {},
  rooms: { W47N8: { name: 'W47N8', getTerrain: () => ({ get: (x, y) => T.charCodeAt(y * 50 + x) - 48 }), find: (type) => type === 1 ? structs : [] } },
};
const MV = require(path.join(ROOT, 'src/utils/move.js'));
assert.strictEqual(MV.matrix('W47N8', false).get(34, 32), F.POST_COST, 'move matrix yields the filler post');
assert.strictEqual(MV.matrix('W47N8', false).get(32, 32), 0, 'bypass plain 32,32 stays open');
console.log('w47n8 spawn pocket ok');
