// W47N7 2026-10-31 (Misaki: "rdef83982033 能不能别挡路，在这种位置驻守呢 27,19 ?? 并且有点活人感，四处巡逻").
// The idle defender held its kill spot 18,1 next to the exit 18,0 (rhauler lane) for good. Now: post 27,19, wander around it,
// never stop on a road/container/exit lane or next to a source/controller/container; an Invader still gets engaged at once.
// node tests/defender_guard_idle.js
const fs = require('fs'), path = require('path'), assert = require('assert');
const ROOT = path.join(__dirname, '..');
Object.assign(global, {
  TOP: 1, TOP_RIGHT: 2, RIGHT: 3, BOTTOM_RIGHT: 4, BOTTOM: 5, BOTTOM_LEFT: 6, LEFT: 7, TOP_LEFT: 8,
  ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack', HEAL: 'heal', MOVE: 'move', WORK: 'work',
  FIND_HOSTILE_CREEPS: 4, FIND_MY_SPAWNS: 2, FIND_STRUCTURES: 10, FIND_SOURCES: 11, FIND_MINERALS: 12, FIND_CONSTRUCTION_SITES: 13,
  FIND_MY_CREEPS: 14, FIND_HOSTILE_STRUCTURES: 15, LOOK_CREEPS: 'lc', STRUCTURE_ROAD: 'road', STRUCTURE_CONTAINER: 'container',
  STRUCTURE_CONTROLLER: 'controller', TERRAIN_MASK_WALL: 1, TERRAIN_MASK_SWAMP: 2,
  RoomPosition: function (x, y, roomName) { this.x = x; this.y = y; this.roomName = roomName; },
});
global.Memory = { username: 'Misaki', remote: { W47N7: { th: { st: 'SAFE' } } }, defense: { remotePatrol: true }, ops: { r7: { on: 1 } } };
global.Game = { time: 1000, creeps: {}, rooms: {}, spawns: {} };
const T7 = fs.readFileSync(path.join(ROOT, 'data/terrain_W47N7.txt'), 'utf8');
const tget = (x, y) => (x < 0 || y < 0 || x > 49 || y > 49) ? 1 : (T7[y * 50 + x] === '1' || T7[y * 50 + x] === '3') ? 1 : T7[y * 50 + x] === '2' ? 2 : 0;
const ROADS = require(path.join(ROOT, 'src/rooms/w47n8/remote_roads.js')).ROADS;
const S = (type, x, y) => ({ structureType: type, pos: { x, y } });
const structs = ROADS.map(([x, y]) => S('road', x, y)).concat([S('container', 18, 17), S('container', 31, 34)]);
const sources = [{ pos: { x: 17, y: 17 } }, { pos: { x: 30, y: 35 } }];
let hostiles = [];
const room = { name: 'W47N7', controller: { my: false, pos: { x: 38, y: 26 } }, getTerrain: () => ({ get: tget }),
  find: t => t === FIND_STRUCTURES ? structs : t === FIND_SOURCES ? sources : t === FIND_HOSTILE_CREEPS ? hostiles : [],
  lookForAt: () => [] };
Game.rooms.W47N7 = room;
function bindPos(p) {
  p.roomName = 'W47N7';
  p.getRangeTo = function (t) { const q = t.pos || t; return Math.max(Math.abs(this.x - q.x), Math.abs(this.y - q.y)); };
  p.inRangeTo = function (a, b, r) { const q = typeof a === 'object' ? (a.pos || a) : { x: a, y: b }; const rr = typeof a === 'object' ? b : r;
    return Math.max(Math.abs(this.x - q.x), Math.abs(this.y - q.y)) <= rr; };
  p.isNearTo = function (o) { return this.inRangeTo(o, 1); };
  p.findInRange = () => []; p.findClosestByRange = () => null;
  return p;
}
const D9 = [[0, 0], [0, -1], [1, -1], [1, 0], [1, 1], [0, 1], [-1, 1], [-1, 0], [-1, -1]];
function bfs(x, y, gx, gy, range) { // first step of a shortest walkable path (stand-in for PathFinder)
  if (Math.max(Math.abs(x - gx), Math.abs(y - gy)) <= range) return null;
  const q = [[x, y]], prev = new Map(), seen = new Set([x * 50 + y]);
  while (q.length) { const [cx, cy] = q.shift();
    for (let d = 1; d <= 8; d++) { const nx = cx + D9[d][0], ny = cy + D9[d][1], k = nx * 50 + ny;
      if (nx < 1 || ny < 1 || nx > 48 || ny > 48 || tget(nx, ny) === 1 || seen.has(k)) continue;
      seen.add(k); prev.set(k, cx * 50 + cy); q.push([nx, ny]);
      if (Math.max(Math.abs(nx - gx), Math.abs(ny - gy)) <= range) { let cur = k; while (prev.get(cur) !== x * 50 + y) cur = prev.get(cur);
        return [((cur / 50) | 0) - x, (cur % 50) - y]; } } }
  return null;
}
let moveToCalls = 0, shots = 0;
const creep = { name: 'rdef83982033', my: true, hits: 1200, hitsMax: 1200, ticksToLive: 1200, fatigue: 0, room,
  memory: { role: 'defender', remote: 'W47N7', home: 'W47N8', lk: [19, 2] }, pos: bindPos({ x: 18, y: 1 }),
  body: [].concat(Array(5).fill({ type: 'ranged_attack', hits: 100 }), Array(6).fill({ type: 'move', hits: 100 }), [{ type: 'heal', hits: 100 }]),
  heal() {}, rangedAttack() { shots++; }, rangedMassAttack() { shots++; },
  move(d) { const s = D9[d] || [0, 0]; if (tget(this.pos.x + s[0], this.pos.y + s[1]) !== 1) { this.pos.x += s[0]; this.pos.y += s[1]; } },
  moveTo(t) { moveToCalls++; const q = t.pos || t; const s = bfs(this.pos.x, this.pos.y, q.x, q.y, 3); if (s) { this.pos.x += s[0]; this.pos.y += s[1]; } } };
Game.creeps[creep.name] = creep;
// stub utils/move.to with the BFS step (the real one needs PathFinder)
const movePath = path.join(ROOT, 'src/utils/move.js');
require.cache[movePath] = { id: movePath, filename: movePath, loaded: true, exports: {
  foreignSites: (rn, m) => m, invalidate() {},
  to(c, x, y, range = 0) { const s = bfs(c.pos.x, c.pos.y, x, y, range); if (!s) return true; c.pos.x += s[0]; c.pos.y += s[1]; return false; } } };
const GP = require(path.join(ROOT, 'src/utils/guardpost.js'));
const remote = require(path.join(ROOT, 'src/managers/remote.js'));
const threat = require(path.join(ROOT, 'src/managers/threat.js'));
threat.reservedByUs = () => true;
const C = remote.cfgFor('W47N7');
assert.ok(C && C.guardOnly, 'W47N7 guard cfg');
const bad = GP.badSet(room);
assert.ok(GP.ok(27, 19, tget, bad), '27,19 is an ok idle tile');
assert.deepStrictEqual(GP.postFor(room, C), [27, 19], 'W47N7 post = 27,19');
for (const [x, y] of ROADS) for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) assert.ok(!GP.ok(x + dx, y + dy, tget, bad), 'road / road-side not ok ' + (x + dx) + ',' + (y + dy));
assert.ok(!GP.ok(18, 1, tget, bad) && !GP.ok(17, 18, tget, bad) && !GP.ok(37, 25, tget, bad), 'exit lane / source / controller neighbours not ok');
Memory.remote.W48N7 = { post: [18, 1] };
assert.ok(GP.ok(...GP.postFor({ name: 'W48N7', getTerrain: () => ({ get: tget }), find: () => [], controller: null }, {}), tget, new Set()), 'override is snapped to an ok tile');
// fallback room: no post configured -> nearest ok tile to the centre
assert.ok(GP.ok(...GP.postFor({ name: 'W1N1', getTerrain: () => ({ get: tget }), find: () => [], controller: null }, {}), tget, new Set()), 'auto post ok');

const roles = require(path.join(ROOT, 'src/roles/remote.js'));
const seen = new Set(), stops = [];
let last = null, still = 0;
for (let t = 0; t < 400; t++) {
  Game.time = 2000 + t; roles.defender.run(creep);
  const k = creep.pos.x + ',' + creep.pos.y;
  if (k === last) still++; else { if (still >= 3) stops.push(last); still = 0; }
  last = k; if (t > 60) seen.add(k);
}
assert.ok(creep.memory.lk === undefined, 'kill-spot hold dropped once the FSM is SAFE');
assert.ok(stops.length >= 5, 'patrol pauses at several waypoints: ' + stops.join(' '));
for (const s of stops) { const [x, y] = s.split(',').map(Number);
  assert.ok(GP.ok(x, y, tget, bad), 'stopped on a bad tile ' + s);
  assert.ok(Math.max(Math.abs(x - 27), Math.abs(y - 19)) <= GP.PATROL_R, 'stop within patrol radius ' + s); }
assert.ok(new Set(stops).size >= 3, 'wanders between distinct tiles: ' + stops.join(' '));
assert.strictEqual(moveToCalls, 0, 'idle uses move.to only');
// an Invader shows up: the engage path takes over the same tick (moveTo/shot), patrol state dropped
Memory.remote.W47N7.th = { st: 'DEFEND', def: creep.name, since: 2400, why: 'invader' };
const inv = { id: 'inv9', owner: { username: 'Invader' }, hits: 1000, hitsMax: 1000, pos: bindPos({ x: 27, y: 12 }),
  body: [{ type: 'ranged_attack', hits: 100 }, { type: 'move', hits: 100 }] };
hostiles = [inv];
creep.pos.x = 27; creep.pos.y = 19; Game.time = 2500;
roles.defender.run(creep);
assert.ok(moveToCalls === 1 && creep.memory.gp === undefined && creep.memory.tg === 'inv9', 'engage pre-empts patrol');
// kill spot hold while still DEFEND: next to the exit lane -> nearest ok tile, not 18,1
hostiles = []; creep.memory.lk = [19, 2]; creep.pos.x = 18; creep.pos.y = 1;
for (let t = 0; t < 10; t++) { Game.time = 2600 + t; roles.defender.run(creep); }
assert.ok(GP.ok(creep.pos.x, creep.pos.y, tget, bad) && Math.max(Math.abs(creep.pos.x - 19), Math.abs(creep.pos.y - 2)) <= 3, 'kill-spot hold off the lane: ' + creep.pos.x + ',' + creep.pos.y);
console.log('defender_guard_idle ok; stops', stops.join(' '));
