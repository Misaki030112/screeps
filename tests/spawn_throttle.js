// Home spawn throttle (11-10): one idle cascade per room, and the same skip while a body is
// wanted but energyAvailable is still short. A tick that can pay, a hostile, or a commander
// order still runs the full pass. node tests/spawn_throttle.js
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, {
  WORK: 'work', CARRY: 'carry', MOVE: 'move', ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack',
  HEAL: 'heal', CLAIM: 'claim', TOUGH: 'tough',
  RESOURCE_ENERGY: 'energy',
  STRUCTURE_LINK: 'link', STRUCTURE_CONTAINER: 'container', STRUCTURE_SPAWN: 'spawn',
  STRUCTURE_EXTENSION: 'extension', STRUCTURE_TOWER: 'tower',
  FIND_HOSTILE_CREEPS: 3, FIND_SOURCES: 5, FIND_MY_SPAWNS: 2, FIND_MINERALS: 116,
  BODYPART_COST: { work: 100, carry: 50, move: 50, attack: 80, ranged_attack: 150, heal: 250, claim: 600, tough: 10 },
  ERR_NOT_ENOUGH_ENERGY: -6, ERR_BUSY: -4, ERR_NAME_EXISTS: -3, OK: 0,
  Game: { time: 5000, creeps: {}, spawns: {}, rooms: {} },
  Memory: { defense: { reserveE: 15000 }, ops: {}, stats: {} },
  _: {
    filter: (a, f) => (Array.isArray(a) ? a : Object.values(a || {})).filter(f),
    sum: (a, f) => (Array.isArray(a) ? a : []).reduce((s, x) => s + (typeof f === 'function' ? f(x) : (x[f] || 0)), 0),
    countBy: (a, f) => { const o = {}; for (const x of (a || [])) { const k = f(x); o[k] = (o[k] || 0) + 1; } return o; },
    some: (a, f) => (Array.isArray(a) ? a : Object.values(a || {})).some(f),
  },
});
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
const P = {
  pos: {
    upgraders: [[30, 30], [31, 30], [29, 30]],
    controllerContainer: [30, 30], controllerLink: [30, 31],
    fillerContainerA: [35, 24], fillers: [], miners: [],
  },
  raw: { stamps: {} }, any: {},
};
let passes = 0;
let cmdArmed = false;
let cmdHits = 0;
stub('utils/plan.js', { get: () => P, key: (x, y) => x * 50 + y, STATIONARY_FILL: false });
stub('roles/builder.js', { remoteRoadSite: () => null });
stub('utils/move.js', { to: () => true });
stub('utils/roomcache.js', { all: () => [], at: () => null, get: () => ({ at: [] }), sites: () => [] });
stub('utils/trace.js', { why: () => {} });
stub('utils/cmd.js', {
  consumeSpawn: (sp) => { cmdHits++; if (cmdArmed && sp._take) { sp._took = true; return true; } return false; },
  armed: () => cmdArmed,
  yieldCreep: () => false,
});
stub('managers/threat.js', {
  reserve: () => 15000, holding: () => false, wantDefender: () => null, armed: () => false,
  energyHold: () => false, noteSpawn: () => {}, state: () => ({ st: 'SAFE' }), squadAlive: () => 0, squadSize: () => 1,
});
stub('managers/roads.js', { phase: () => 'done', repairTarget: () => null, paved: () => false });
stub('managers/remote.js', { CFG: {}, paused: () => false, mem: () => ({}) });
stub('managers/home.js', { on: () => false, active: () => false, wantGuards: () => 0, alert: () => false, flee: () => false });
stub('managers/walls.js', {
  phase: () => 'done', noUpgrade: () => false, wantBuilder: () => false, reserved: () => 0,
  budgetE: () => 0, fund: () => 0, defReserve: () => 15000, defLow: () => false, stepHeld: () => true,
  siege: () => false, fundSpend: () => false, UP_SAFE: 20000,
});
stub('roles/queen.js', { storageFloor: () => 15000 });
stub('roles/hauler.js', { pickups: () => { passes++; return []; } });
stub('roles/raid9.js', { pauseCivilians: () => false, wantSpawn: () => null, applyPause: T => T, noteSpawned: () => {} });
stub('roles/probe.js', { wantSpawn: () => false });
stub('roles/reserve7.js', { wantSpawn: () => null });
stub('roles/conquest.js', { guardWant: () => null, wantSpawn: () => null, noteSpawned: () => {} });
stub('roles/quad.js', { wantSpawn: () => null });
stub('rooms/w47n8/index.js', { homeWant: () => null });
stub('rooms/w47n8/fillmeter.js', { tick: () => {} });
const S = require(src('managers/spawn.js'));

function creep(role) {
  return {
    name: role + '_' + Math.random().toString(16).slice(2),
    memory: { role, home: 'W46N8' },
    room: { name: 'W46N8' },
    ticksToLive: 1400,
    spawning: false,
    body: Array(17),
  };
}
function world(o) {
  Game.time = o.time;
  passes = 0;
  const creeps = [creep('queen'), creep('queen'), creep('hauler')];
  for (let i = 0; i < (o.upgraders == null ? 2 : o.upgraders); i++) creeps.push(creep('upgrader'));
  Game.creeps = {};
  for (const c of creeps) Game.creeps[c.name] = c;
  const hostiles = o.hostiles || [];
  const room = {
    name: 'W46N8',
    energyAvailable: o.energy == null ? 5600 : o.energy,
    energyCapacityAvailable: 5600,
    controller: { level: 7, ticksToDowngrade: 100000 },
    storage: { store: { energy: o.storage == null ? 20000 : o.storage } },
    memory: { sources: [], ctlEma: 0, ctlEmaT: o.time, lastFull: o.time },
    find: (t) => (t === 3 ? hostiles : []),
  };
  const spawned = [];
  const mk = (id) => ({
    id, name: id, spawning: null, room, pos: { x: 35, y: 28, roomName: 'W46N8' },
    spawnCreep: (body, name, opts) => {
      spawned.push(opts.memory.role);
      return 0;
    },
  });
  return { room, spawned, a: mk('Spawn1'), b: mk('Spawn2') };
}

// Two idle spawns, nothing wanted: the second must not walk run1.
{
  Memory.stats = {};
  const w = world({ time: 5000, upgraders: 2, energy: 5600 });
  S.run(w.a);
  S.run(w.b);
  assert.strictEqual(passes, 1, 'two idle spawns, one full cascade, passes=' + passes);
  assert.strictEqual(w.spawned.length, 0);
  assert.ok(Memory.stats.sw.W46N8.ne > 5000, 'idle arms the skip window');
}

// Wanted upgrader, energy short: second spawn skips, and the next short tick skips both.
{
  Memory.stats = {};
  const w = world({ time: 6000, upgraders: 1, energy: 1000, storage: 16000 });
  S.run(w.a);
  S.run(w.b);
  assert.strictEqual(passes, 1, 'waiting spawn does not cascade twice');
  assert.strictEqual(w.spawned.length, 0, 'cannot pay 1550 from 1000');
  assert.ok(Memory.stats.sw.W46N8.waitCost > 1000, 'remembers the queued cost');
  Game.time = 6001;
  w.room.energyAvailable = 1000;
  const before = passes;
  S.run(w.a);
  S.run(w.b);
  assert.strictEqual(passes, before, 'still short: both spawns stay off run1');
  assert.strictEqual(w.spawned.length, 0);
}

// Energy arrives inside the window: the body starts this tick, not IDLE_EVERY later.
{
  Memory.stats = {};
  const w = world({ time: 7000, upgraders: 1, energy: 1000, storage: 16000 });
  S.run(w.a);
  assert.strictEqual(w.spawned.length, 0);
  Game.time = 7001;
  w.room.energyAvailable = 5600;
  S.run(w.a);
  assert.ok(w.spawned.includes('upgrader'), 'affordable queued body starts the same tick ' + JSON.stringify(w.spawned));
}

// Hostile forces the cascade even while the idle window is open.
{
  Memory.stats = {};
  const w = world({ time: 8000, upgraders: 2, energy: 5600 });
  S.run(w.a);
  assert.strictEqual(passes, 1);
  Game.time = 8001;
  w.room.find = () => [{ my: false }];
  S.run(w.a);
  assert.strictEqual(passes, 2, 'hostile tick runs run1 again');
}

// Commander armed, even if this spawn's order does not consume it, still runs the cascade.
{
  Memory.stats = {};
  cmdArmed = false;
  const w = world({ time: 9000, upgraders: 2, energy: 5600 });
  S.run(w.a);
  Game.time = 9001;
  cmdArmed = true;
  cmdHits = 0;
  w.a._take = true;
  S.run(w.a);
  assert.strictEqual(w.a._took, true, 'commander spawn still runs inside the idle window');
  assert.ok(cmdHits >= 1);
  cmdArmed = false;
}
console.log('spawn throttle ok');
