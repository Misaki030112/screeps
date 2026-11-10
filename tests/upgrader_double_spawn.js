// Home upgrader double-start (patrol 2026-11-10 12:24, W46N8 RCL7).
// Storage crossing allowExtra (floor 15000 + SURPLUS 1000 = 16000) clears upBank and sets tUp=2.
// spawnCreep does not put the creep in Game.creeps until the next tick, so two idle spawns both
// saw nUp 1 and each started a 1550 — live nUp 3. tUp=2 must stay nUp 2. The 3rd-upgrader gate
// (ctl EMA >= 700) may still start the two bodies that land on tUp=3.
// node tests/upgrader_double_spawn.js -> exits 1 on failure
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
  Game: { time: 1000, creeps: {}, spawns: {}, rooms: {} },
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
stub('utils/plan.js', { get: () => P, key: (x, y) => x * 50 + y, STATIONARY_FILL: false });
stub('roles/builder.js', { remoteRoadSite: () => null });
stub('utils/move.js', { to: () => true });
stub('utils/roomcache.js', { all: () => [], at: () => null, get: () => ({ at: [] }), sites: () => [] });
stub('utils/trace.js', { why: () => {} });
stub('utils/cmd.js', { consumeSpawn: () => false, armed: () => false, yieldCreep: () => false });
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
stub('roles/hauler.js', { pickups: () => [] });
stub('roles/raid9.js', { pauseCivilians: () => false, wantSpawn: () => null, applyPause: T => T });
stub('roles/probe.js', { wantSpawn: () => false });
stub('roles/reserve7.js', { wantSpawn: () => null });
stub('roles/conquest.js', { guardWant: () => null, wantSpawn: () => null, noteSpawned: () => {} });
stub('roles/quad.js', { wantSpawn: () => null });
stub('rooms/w47n8/index.js', { homeWant: () => null });
stub('rooms/w47n8/fillmeter.js', { tick: () => {} });
const S = require(src('managers/spawn.js'));

function creep(role, extra) {
  return Object.assign({
    name: role + '_' + Math.random().toString(16).slice(2),
    memory: { role, home: 'W46N8' },
    room: { name: 'W46N8' },
    ticksToLive: 1400,
    spawning: false,
    body: Array(17),
  }, extra);
}

// visible: spawnCreep also inserts the creep (some runtimes do this before the other spawn runs).
// The quota must not double-count that body, and must still see an intent the census missed.
function pair(o) {
  Game.time = o.time;
  Memory.stats = {};
  const ups = [];
  for (let i = 0; i < (o.upgraders || 0); i++) ups.push(creep('upgrader'));
  if (o.spawning) ups.push(creep('upgrader', { spawning: true, ticksToLive: undefined, name: 'upgrading' }));
  Game.creeps = {};
  for (const c of [creep('queen'), creep('queen'), creep('hauler')].concat(ups)) Game.creeps[c.name] = c;
  const room = {
    name: 'W46N8',
    energyAvailable: 5600,
    energyCapacityAvailable: 5600,
    controller: { level: 7, ticksToDowngrade: 100000 },
    storage: { store: { energy: o.storage } },
    memory: { upBank: o.upBank, sources: [], ctlEma: o.ema || 0, ctlEmaT: o.time, lastFull: o.time },
    find: () => [],
  };
  const spawned = [];
  const mk = (id) => ({
    id, spawning: null, room, pos: { x: 35, y: 28, roomName: 'W46N8' },
    spawnCreep: (body, name, opts) => {
      spawned.push({ role: opts.memory.role, name, cost: body.reduce((s, p) => s + BODYPART_COST[p], 0) });
      if (o.visible) Game.creeps[name] = { name, memory: opts.memory, room: { name: 'W46N8' }, spawning: true, body, ticksToLive: undefined };
      return OK;
    },
  });
  S.run(mk('Spawn1'));
  S.run(mk('Spawn2'));
  return { spawned, ups: spawned.filter(s => s.role === 'upgrader'), T: room.memory.roleTargets, mem: room.memory };
}

const cases = [
  ['allowExtra cross, upBank clears, tUp=2, one alive, intent hidden: one start (not nUp 3)', () => {
    const r = pair({ time: 841000, storage: 16000, upBank: 1, upgraders: 1 });
    assert.strictEqual(r.T.upgrader, 2, 'tUp');
    assert.strictEqual(r.mem.upBank, undefined, 'upBank cleared at reserve+1000');
    assert.strictEqual(r.ups.length, 1, 'starts ' + JSON.stringify(r.spawned));
    assert.strictEqual(1 + r.ups.length, 2, 'live nUp');
    assert.strictEqual(r.ups[0].cost, 1550);
  }],
  ['same crossing but the runtime inserts the creep before spawn 2: still one start', () => {
    const r = pair({ time: 841010, storage: 16000, upBank: 1, upgraders: 1, visible: true });
    assert.strictEqual(r.T.upgrader, 2);
    assert.strictEqual(r.ups.length, 1, JSON.stringify(r.spawned));
  }],
  ['gap of 2 (none alive, tUp=2): both spawns may start one', () => {
    const r = pair({ time: 841020, storage: 16000, upgraders: 0 });
    assert.strictEqual(r.T.upgrader, 2);
    assert.strictEqual(r.ups.length, 2, JSON.stringify(r.spawned));
  }],
  ['gap of 2 and the first creep is visible immediately: second spawn still fills tUp', () => {
    const r = pair({ time: 841030, storage: 16000, upgraders: 0, visible: true });
    assert.strictEqual(r.ups.length, 2, JSON.stringify(r.spawned));
  }],
  ['3rd-upgrader gate stays: ctl EMA 700 at 16000, tUp=3, one alive -> two starts (nUp 3)', () => {
    const r = pair({ time: 841040, storage: 16000, upBank: 1, upgraders: 1, ema: 700 });
    assert.strictEqual(r.T.upgrader, 3, 'allowExtra + EMA still opens the third');
    assert.strictEqual(r.ups.length, 2, JSON.stringify(r.spawned));
    assert.strictEqual(1 + r.ups.length, 3);
  }],
  ['just under allowExtra with upBank: tUp stays 1, no second upgrader', () => {
    const r = pair({ time: 841050, storage: 15999, upBank: 1, upgraders: 1 });
    assert.strictEqual(r.T.upgrader, 1);
    assert.strictEqual(r.mem.upBank, 1);
    assert.strictEqual(r.ups.length, 0, JSON.stringify(r.spawned));
  }],
  ['a spawning upgrader already in Game.creeps counts, so tUp=2 does not start another', () => {
    const r = pair({ time: 841060, storage: 16000, upgraders: 1, spawning: true });
    assert.strictEqual(r.T.upgrader, 2);
    assert.strictEqual(r.ups.length, 0, JSON.stringify(r.spawned));
  }],
];
let fail = 0;
for (const [n, f] of cases) {
  try { f(); console.log('ok  ', n); }
  catch (e) { fail++; console.log('FAIL', n, e.message); }
}
console.log(`upgrader double spawn: ${cases.length - fail}/${cases.length}`);
process.exit(fail ? 1 : 0);
