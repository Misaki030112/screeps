// Military movement recalculates every call and a civilian on the next tile must swap.
// node tests/military_path.js
const path = require('path'), assert = require('assert');
const DIRS = { 1: [0, -1], 2: [1, -1], 3: [1, 0], 4: [1, 1], 5: [0, 1], 6: [-1, 1], 7: [-1, 0], 8: [-1, -1] };
function dirTo(ax, ay, bx, by) {
  for (const k of Object.keys(DIRS)) {
    const d = DIRS[k];
    if (ax + d[0] === bx && ay + d[1] === by) return +k;
  }
  return 0;
}
global.OK = 0;
global.LOOK_CREEPS = 'creep';
global.RIGHT = 3;
global.LEFT = 7;
global.Game = { time: 10, creeps: {}, getObjectById: () => null };
global.Memory = {};
global.RoomPosition = function (x, y, room) { this.x = x; this.y = y; this.roomName = room; };
let searches = 0;
global.PathFinder = {
  CostMatrix: class { set() {} get() { return 0; } },
  search(from, goal) {
    searches++;
    const tx = goal.pos.x, ty = goal.pos.y;
    // One step toward the goal on x, ignoring any cached path the creep may be holding.
    const nx = from.x + Math.sign(tx - from.x);
    const ny = from.y + Math.sign(ty - from.y);
    if (nx === from.x && ny === from.y) return { path: [], incomplete: false };
    return { path: [{ x: nx, y: ny }], incomplete: false };
  },
};
const mil = require(path.join(__dirname, '..', 'src/utils/military.js'));
const squad = require(path.join(__dirname, '..', 'src/utils/squad.js'));

function creep(role, x, y, name) {
  const c = {
    name, my: true, spawning: false, fatigue: 0,
    memory: { role, _move: { path: '7', time: 1 }, _m: { k: 'stale', p: 'left', s: 0 } },
    room: { name: 'W46N8', lookForAt: (t, lx, ly) => (t === 'creep' ? roomCreeps(lx, ly) : []) },
    pos: { x, y },
    moves: [],
  };
  c.pos.getDirectionTo = (tx, ty) => dirTo(c.pos.x, c.pos.y, tx, ty);
  c.move = d => { c.moves.push(d); };
  c.moveTo = () => { c.moves.push('moveTo'); };
  return c;
}
const creeps = [];
function roomCreeps(x, y) { return creeps.filter(c => c.pos.x === x && c.pos.y === y); }

const def = creep('defender', 10, 10, 'defender1');
creeps.push(def);
searches = 0;
const st1 = mil.step(def, 14, 10, 1);
assert.strictEqual(st1, 'moved');
assert.strictEqual(def.moves[0], 3, 'fresh search steps toward the goal, not the stale LEFT cache');
assert.ok(!def.memory._m && !def.memory._move, 'military step drops both path caches');
const st2 = mil.step(def, 14, 10, 1);
assert.strictEqual(st2, 'moved');
assert.strictEqual(searches, 2, 'second tick searches again');

Game.time = 11;
const hauler = creep('hauler', 11, 10, 'hauler1');
const guard = creep('guard', 12, 10, 'guard1');
creeps.length = 0;
creeps.push(def, hauler, guard);
def.pos.x = 10; def.moves.length = 0; hauler.moves.length = 0; guard.moves.length = 0;
Game.creeps = { hauler1: hauler, guard1: guard, defender1: def };
mil.step(def, 14, 10, 0);
assert.ok(mil._demand.map.hauler1, 'civilian on the next tile is demanded');
assert.ok(!mil._demand.map.guard1, 'another military creep is not forced to swap');
hauler.move(1); // its own role already chose a different step
mil.flush();
assert.strictEqual(hauler.moves[hauler.moves.length - 1], 7, 'flush overwrites the civilian move with the swap');
assert.strictEqual(def.moves[def.moves.length - 1], 3, 'military steps onto the civilian tile');

Game.time = 12;
const miner = creep('miner', 11, 10, 'miner1');
creeps.length = 0;
creeps.push(def, miner);
def.pos.x = 10; def.moves.length = 0;
Game.creeps = { miner1: miner };
mil.step(def, 14, 10, 0);
assert.strictEqual(mil.block(miner), true, 'civilian honors the swap at the start of its turn');
assert.strictEqual(miner.moves[0], 7);

assert.strictEqual(squad.fillRank(true, true, 'extension'), 0);
assert.strictEqual(squad.fillRank(true, true, 'spawn'), 0);
assert.ok(squad.fillRank(true, true, 'tower') > squad.fillRank(true, true, 'extension'), 'short pile: extensions before towers');
assert.ok(squad.fillRank(true, true, 'tower') < squad.fillRank(true, true, 'storage'), 'towers still beat non-spawn sinks');
assert.ok(squad.fillRank(true, false, 'tower') < squad.fillRank(true, false, 'extension'), 'full pile: towers first');
assert.strictEqual(squad.judge([{ ra: 1 }]), 1);
assert.strictEqual(squad.judge([{ heal: true }]), 2);
assert.strictEqual(squad.judge([{ ra: 8 }]), 3);
assert.strictEqual(squad.judge([{}, {}, {}, {}]), 4);

console.log('military path ok');
