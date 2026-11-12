// 2026-11-12 patrol: rdef84218203 bounced W47N8 18,49 <-> W47N7 18,0 for 172 t because
// "fight from the exit if an Invader is within 4" skipped stepIn. A creep that ends the
// tick on y=0 is sent back. node tests/defender_exit_bounce.js
const fs = require('fs'), path = require('path'), assert = require('assert');
const ROOT = path.join(__dirname, '..');
const _ = {
  filter: (a, f) => Object.values(a || {}).filter(f),
  some: (a, f) => Object.values(a || {}).some(f),
  sum: (a, f) => Object.values(a || {}).reduce((s, x) => s + (f ? f(x) : x), 0),
};
Object.assign(global, {
  _, TOP: 1, TOP_RIGHT: 2, RIGHT: 3, BOTTOM_RIGHT: 4, BOTTOM: 5, BOTTOM_LEFT: 6, LEFT: 7, TOP_LEFT: 8,
  ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack', HEAL: 'heal', MOVE: 'move', WORK: 'work', CARRY: 'carry', TOUGH: 'tough',
  FIND_HOSTILE_CREEPS: 4, FIND_MY_CREEPS: 1, FIND_CREEPS: 3, FIND_MY_SPAWNS: 2, LOOK_STRUCTURES: 'ls', LOOK_CREEPS: 'lc',
  TERRAIN_MASK_WALL: 1, TERRAIN_MASK_SWAMP: 2,
  RoomPosition: function (x, y, roomName) { this.x = x; this.y = y; this.roomName = roomName; },
});
global.Memory = { username: 'Misaki', remote: { W47N7: { th: { st: 'DEFEND', def: 'rdef1', since: 1, why: 'invader' } } }, defense: { remotePatrol: true }, ops: {} };
global.Game = { time: 100, creeps: {}, rooms: {}, spawns: {} };

const T7 = fs.readFileSync(path.join(ROOT, 'data/terrain_W47N7.txt'), 'utf8');
const terrain = { get: (x, y) => { const ch = T7[y * 50 + x]; return ch === '1' || ch === '3' ? 1 : ch === '2' ? 2 : 0; } };

function invader(x, y) {
  return {
    id: 'inv' + x + ',' + y, owner: { username: 'Invader' }, hits: 1000, hitsMax: 1000, ticksToLive: 1000,
    pos: { x, y,
      getRangeTo: (a, b) => (typeof a === 'object' ? Math.max(Math.abs(x - a.x), Math.abs(y - a.y)) : Math.max(Math.abs(x - a), Math.abs(y - b))),
      inRangeTo: (a, b, r) => {
        if (typeof a === 'object') return Math.max(Math.abs(x - a.x), Math.abs(y - a.y)) <= b;
        return Math.max(Math.abs(x - a), Math.abs(y - b)) <= r;
      }
    },
    body: [
      { type: 'move', hits: 100 }, { type: 'move', hits: 100 }, { type: 'move', hits: 100 },
      { type: 'move', hits: 100 }, { type: 'move', hits: 100 },
      { type: 'ranged_attack', hits: 100 }, { type: 'ranged_attack', hits: 100 }, { type: 'ranged_attack', hits: 100 },
    ],
  };
}

function makeRoom(name, hostiles) {
  return {
    name,
    controller: { my: false },
    getTerrain: () => terrain,
    find: (t) => t === FIND_HOSTILE_CREEPS ? hostiles : [],
    lookForAt: () => [],
    findInRange() { return []; },
  };
}

function makeCreep(room, x, y) {
  const shots = [], moved = [], moveTo = [];
  const creep = {
    name: 'rdef1', owner: { username: 'Misaki' }, hits: 5000, hitsMax: 5000, ticksToLive: 1200,
    room, memory: { role: 'defender', remote: 'W47N7', home: 'W47N8' },
    pos: {
      x, y,
      getRangeTo: (t) => Math.max(Math.abs(x - t.pos.x), Math.abs(y - t.pos.y)),
      inRangeTo: (a, b, r) => {
        const t = (a && a.pos) ? a.pos : a;
        const range = (typeof t === 'object' && r === undefined) ? b : r;
        return Math.max(Math.abs(x - t.x), Math.abs(y - t.y)) <= range;
      },
      isNearTo: () => false,
      findInRange: () => [],
    },
    body: Array(19).fill({ type: 'ranged_attack', hits: 100 })
      .concat(Array(25).fill({ type: 'move', hits: 100 }))
      .concat(Array(6).fill({ type: 'heal', hits: 100 })),
    heal() {},
    rangedAttack(t) { shots.push(t && t.id); },
    rangedMassAttack() {},
    moveTo(t, o) { moveTo.push([t && (t.x || (t.pos && t.pos.x)), t && (t.y || (t.pos && t.pos.y)), o && o.maxRooms]); },
    move(d) { moved.push(d); },
    shots, moved, moveTo,
  };
  return creep;
}

const roles = require(path.join(ROOT, 'src/roles/remote.js'));

// Case: on W47N7 18,0 with an Invader at 18,3 (range 3, within the old "fight from here" window).
{
  const inv = invader(18, 3);
  const room = makeRoom('W47N7', [inv]);
  const c = makeCreep(room, 18, 0);
  // pos.findInRange used by stepIn
  room.findInRange = () => [];
  c.pos.findInRange = () => [];
  c.room = room;
  Game.rooms.W47N7 = room;
  Game.creeps.rdef1 = c;
  roles.defender.run(c);
  assert.ok(c.moved.length > 0, 'must step off the exit, got moves=' + JSON.stringify(c.moved));
  assert.ok(c.moved.includes(BOTTOM) || c.moved.includes(BOTTOM_LEFT) || c.moved.includes(BOTTOM_RIGHT),
    'stepIn from 18,0 should go south, got ' + JSON.stringify(c.moved));
  assert.ok(c.shots.length > 0, 'still shoots the exit-camp Invader this tick, shots=' + JSON.stringify(c.shots));
  assert.strictEqual(c.moveTo.length, 0, 'must not moveTo while still on the exit');
}

// Control: already inside the room (18,5) vs Invader at 18,3 — may kite/approach, but must not step onto y=0.
{
  const inv = invader(18, 3);
  const room = makeRoom('W47N7', [inv]);
  const c = makeCreep(room, 18, 5);
  c.pos.findInRange = () => [];
  Game.rooms.W47N7 = room;
  Game.creeps.rdef1 = c;
  roles.defender.run(c);
  assert.ok(!c.moved.includes(TOP), 'inside the room, must not step back onto the exit, moves=' + JSON.stringify(c.moved));
}

console.log('defender_exit_bounce tests passed');
