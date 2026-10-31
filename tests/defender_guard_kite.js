// GUARD remote (W47N7) kite must use cfgFor — CFG[W47N7] is undefined and C.avoid used to throw (patrol 2026-10-29).
// node tests/defender_guard_kite.js
const fs = require('fs'), path = require('path'), assert = require('assert'), vm = require('vm');
const ROOT = path.join(__dirname, '..');
const _ = {
  filter: (a, f) => Object.values(a || {}).filter(f),
  some: (a, f) => Object.values(a || {}).some(f),
  sum: (a, f) => Object.values(a || {}).reduce((s, x) => s + (f ? f(x) : x), 0),
};
Object.assign(global, {
  _, TOP: 1, TOP_RIGHT: 2, RIGHT: 3, BOTTOM_RIGHT: 4, BOTTOM: 5, BOTTOM_LEFT: 6, LEFT: 7, TOP_LEFT: 8,
  ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack', HEAL: 'heal', MOVE: 'move', WORK: 'work', CARRY: 'carry', TOUGH: 'tough',
  FIND_HOSTILE_CREEPS: 4, FIND_MY_SPAWNS: 2, LOOK_STRUCTURES: 'ls', LOOK_CREEPS: 'lc',
  STRUCTURE_ROAD: 'road', RESOURCE_ENERGY: 'energy',
  TERRAIN_MASK_WALL: 1, TERRAIN_MASK_SWAMP: 2,
  RoomPosition: function (x, y, roomName) { this.x = x; this.y = y; this.roomName = roomName; },
});
global.Memory = { username: 'Misaki', remote: { W47N7: { th: { st: 'DEFEND', def: 'rdef1', since: 1, why: 'invader' } } }, defense: { remotePatrol: true }, ops: {} };
global.Game = { time: 100, creeps: {}, rooms: {}, spawns: {} };

const terrain = { get: () => 0 };
const room = {
  name: 'W47N7', controller: { my: false },
  getTerrain: () => terrain,
  find: (t) => t === FIND_HOSTILE_CREEPS ? [inv] : [],
  lookForAt: () => [],
};
const inv = {
  id: 'inv1', owner: { username: 'Invader' }, hits: 800, hitsMax: 1000, ticksToLive: 1000,
  pos: { x: 18, y: 2, getRangeTo: (a, b) => {
    if (typeof a === 'object') return Math.max(Math.abs(18 - a.x), Math.abs(2 - a.y));
    return Math.max(Math.abs(18 - a), Math.abs(2 - b));
  }, inRangeTo: (a, b, r) => {
    if (typeof a === 'object') return Math.max(Math.abs(18 - a.x), Math.abs(2 - a.y)) <= b;
    return Math.max(Math.abs(18 - a), Math.abs(2 - b)) <= r;
  } },
  body: [
    { type: 'tough', hits: 100 }, { type: 'tough', hits: 100 },
    { type: 'move', hits: 100 }, { type: 'move', hits: 100 }, { type: 'move', hits: 100 }, { type: 'move', hits: 100 },
    { type: 'ranged_attack', hits: 100 }, { type: 'work', hits: 100 }, { type: 'attack', hits: 100 }, { type: 'move', hits: 100 },
  ],
};
const moved = [];
const creep = {
  name: 'rdef1', owner: { username: 'Misaki' }, hits: 1200, hitsMax: 1200, ticksToLive: 1400,
  room, memory: { role: 'defender', remote: 'W47N7', home: 'W47N8' },
  pos: {
    x: 18, y: 5,
    getRangeTo: (t) => Math.max(Math.abs(18 - t.pos.x), Math.abs(5 - t.pos.y)),
    inRangeTo: (a, b, r) => {
      if (typeof a === 'object') return Math.max(Math.abs(18 - a.x), Math.abs(5 - a.y)) <= b;
      return Math.max(Math.abs(18 - a), Math.abs(5 - b)) <= r;
    },
    isNearTo: () => false,
  },
  body: [
    { type: 'ranged_attack', hits: 100 }, { type: 'ranged_attack', hits: 100 }, { type: 'ranged_attack', hits: 100 },
    { type: 'ranged_attack', hits: 100 }, { type: 'ranged_attack', hits: 100 },
    { type: 'move', hits: 100 }, { type: 'move', hits: 100 }, { type: 'move', hits: 100 },
    { type: 'move', hits: 100 }, { type: 'move', hits: 100 }, { type: 'move', hits: 100 },
    { type: 'heal', hits: 100 },
  ],
  heal() {}, rangedAttack() {}, rangedMassAttack() {}, moveTo() {},
  move(d) { moved.push(d); },
};
Game.rooms.W47N7 = room;
Game.creeps.rdef1 = creep;

const remote = require(path.join(ROOT, 'src/managers/remote.js'));
assert.ok(remote.cfgFor('W47N7'), 'cfgFor returns GUARD W47N7');
assert.strictEqual(remote.CFG.W47N7, undefined, 'CFG has no W47N7 (regression trigger)');

const roles = require(path.join(ROOT, 'src/roles/remote.js'));
assert.doesNotThrow(() => roles.defender.run(creep), 'defender kite must not throw on GUARD remote');
assert.ok(moved.length >= 0, 'ran without throw');

// W47N7 2026-10-31: a melee Invader that is not walking into us (busy on a miner/structure).
// Range used to count as "approaching" whenever WE stepped closer, so kw reset, kite held at range 4-6,
// and rangedAttack never fired. Real terrain pocket 33,29 vs 28,24.
const T7 = fs.readFileSync(path.join(ROOT, 'data/terrain_W47N7.txt'), 'utf8');
const wall7 = (x, y) => x < 1 || y < 1 || x > 48 || y > 48 || T7[y * 50 + x] === '1' || T7[y * 50 + x] === '3';
const D9 = [[0, 0], [0, -1], [1, -1], [1, 0], [1, 1], [0, 1], [-1, 1], [-1, 0], [-1, -1]];
room.getTerrain = () => ({ get: (x, y) => wall7(x, y) ? 1 : (T7[y * 50 + x] === '2' ? 2 : 0) });
function bfs(x, y, gx, gy, range) {
  if (Math.max(Math.abs(x - gx), Math.abs(y - gy)) <= range) return null;
  const q = [[x, y]], prev = new Map(), seen = new Set([x * 50 + y]);
  while (q.length) {
    const [cx, cy] = q.shift();
    for (let d = 1; d <= 8; d++) {
      const nx = cx + D9[d][0], ny = cy + D9[d][1], k = nx * 50 + ny;
      if (wall7(nx, ny) || seen.has(k)) continue;
      seen.add(k); prev.set(k, cx * 50 + cy); q.push([nx, ny]);
      if (Math.max(Math.abs(nx - gx), Math.abs(ny - gy)) <= range) {
        let cur = k; while (prev.get(cur) !== x * 50 + y) cur = prev.get(cur);
        return [((cur / 50) | 0) - x, (cur % 50) - y];
      }
    }
  }
  return null;
}
function bindPos(p) {
  p.getRangeTo = function (t) { const q = t.pos || t; return Math.max(Math.abs(this.x - q.x), Math.abs(this.y - q.y)); };
  p.inRangeTo = function (a, b, r) {
    if (typeof a === 'object' && a.pos) return Math.max(Math.abs(this.x - a.pos.x), Math.abs(this.y - a.pos.y)) <= (r === undefined ? b : r);
    if (typeof a === 'object') return Math.max(Math.abs(this.x - a.x), Math.abs(this.y - a.y)) <= b;
    return Math.max(Math.abs(this.x - a), Math.abs(this.y - b)) <= r;
  };
  p.isNearTo = function (o) { const q = o.pos || o; return Math.max(Math.abs(this.x - q.x), Math.abs(this.y - q.y)) <= 1; };
}
bindPos(inv.pos); bindPos(creep.pos);
inv.pos.x = 28; inv.pos.y = 24;
creep.pos.x = 33; creep.pos.y = 29;
creep.memory = { role: 'defender', remote: 'W47N7', home: 'W47N8' };
let shots = 0;
creep.rangedAttack = () => { shots++; };
creep.rangedMassAttack = () => { shots++; };
creep.move = (d) => { const s = D9[d] || [0, 0]; const nx = creep.pos.x + s[0], ny = creep.pos.y + s[1]; if (!wall7(nx, ny)) { creep.pos.x = nx; creep.pos.y = ny; } };
creep.moveTo = (t) => { const q = t.pos || t; const s = bfs(creep.pos.x, creep.pos.y, q.x, q.y, 3); if (s) { creep.pos.x += s[0]; creep.pos.y += s[1]; } };
for (let t = 0; t < 30; t++) { Game.time = 200 + t; roles.defender.run(creep); }
const endR = Math.max(Math.abs(creep.pos.x - 28), Math.abs(creep.pos.y - 24));
assert.ok(shots > 0 && endR <= 3, 'stationary melee on W47N7 must be closed and shot, shots=' + shots + ' range=' + endR + ' at ' + creep.pos.x + ',' + creep.pos.y);
console.log('defender_guard_kite ok');
