// Remote defender energy reserve (2026-10-16): while threat.holding(), upgraders pause
// withdrawals (with storage too); spawn holds miners until avail>=1300 / spawn starts.
// node tests/defender_energy_hold.js -> exits 1 on failure
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, {
  RESOURCE_ENERGY: 'energy', STRUCTURE_LINK: 'link', STRUCTURE_CONTAINER: 'container',
  STRUCTURE_SPAWN: 'spawn', STRUCTURE_EXTENSION: 'extension', STRUCTURE_TOWER: 'tower',
  CARRY: 'carry', MOVE: 'move', WORK: 'work', CLAIM: 'claim',
  RANGED_ATTACK: 'ranged_attack', HEAL: 'heal',
  BODYPART_COST: { work: 100, carry: 50, move: 50, claim: 150, heal: 250, claim_attack: 150 },
  ERR_NOT_ENOUGH_ENERGY: -6, ERR_BUSY: -4, OK: 0,
  Game: { time: 1000, creeps: {} }, Memory: {},
  _: {
    filter: (a, f) => (Array.isArray(a) ? a : Object.values(a || {})).filter(f),
    sum: (a, f) => (Array.isArray(a) ? a : []).reduce((s, x) => s + (typeof f === 'function' ? f(x) : x[f] || 0), 0),
    countBy: (a, f) => { const o = {}; for (const x of a) { const k = f(x); o[k] = (o[k] || 0) + 1; } return o; },
    some: (a, f) => (Array.isArray(a) ? a : Object.values(a || {})).some(f),
  },
});
let HOLD = false, WANT = null, ARMED = true;
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
const P = { pos: { upgraders: [[30, 30]], controllerContainer: [30, 30], controllerLink: [30, 31], fillers: [[34, 25]], manager: [36, 30], miners: [] }, raw: { stamps: { A: { tiles: {} } } }, standing: new Set() };
stub('utils/plan.js', { get: () => P, key: (x, y) => x * 50 + y });
stub('utils/move.js', { to: () => true });
stub('utils/sign.js', { needs: () => false, SIGN: '' });
stub('utils/roomcache.js', {
  at: (room, x, y, t) => (t === 'link' ? W.link : t === 'container' ? W.cont : null),
  all: () => [], sites: () => [], get: () => ({ at: [] }),
});
stub('utils/trace.js', { why: () => {} });
stub('managers/threat.js', {
  holding: () => HOLD, wantDefender: () => WANT, armed: () => ARMED,
  reserve: () => 1300, noteSpawn: (r, n) => { W.noted = [r, n]; },
});
stub('managers/home.js', { on: () => false, active: () => false, wantGuards: () => 0 });
stub('managers/remote.js', { CFG: {}, paused: () => false, mem: () => ({}) });
stub('managers/walls.js', { phase: () => 'off', reserved: () => 0 });
stub('roles/hauler.js', { pickups: () => [], ctlLow: () => false, handoff: () => false });
stub('roles/queen.js', { storageFloor: () => 1300, fillRoute: () => false });

let W;
const U = require(src('roles/upgrader.js'));
const S = require(src('managers/spawn.js'));

function upRun(o) {
  HOLD = !!o.hold;
  W = { link: o.link, cont: o.cont };
  const withdrawn = [];
  const c = {
    room: { name: 'W46N8', storage: o.storage === false ? null : { id: 'st' }, controller: { my: true, owner: { username: 'x' } } },
    memory: { role: 'upgrader', spot: [30, 30] },
    store: { [RESOURCE_ENERGY]: o.carry || 0 },
    getActiveBodyparts: p => (p === 'work' ? 10 : 0),
    pos: { inRangeTo: () => true },
    upgradeController: () => {},
    withdraw: (s) => { withdrawn.push(s === W.link ? 'link' : s === W.cont ? 'cont' : '?'); return 0; },
    pickup: () => 0,
  };
  U.run(c);
  return withdrawn;
}

function spawnRun(o) {
  WANT = o.want === undefined ? 'W45N8' : o.want;
  ARMED = o.armed !== false;
  HOLD = !!WANT;
  W = { noted: null };
  const spawned = [];
  Game.time = 5000;
  Game.creeps = {};
  for (const [name, role] of Object.entries(o.creeps || { queen1: 'queen', miner1: 'miner' })) {
    Game.creeps[name] = {
      name, memory: { role, home: 'W46N8', sourceId: role === 'miner' ? 'srcA' : undefined },
      room: { name: 'W46N8' }, ticksToLive: 1000, spawning: false, body: Array(10),
    };
  }
  const room = {
    name: 'W46N8', energyAvailable: o.avail, energyCapacityAvailable: o.cap || 1800,
    controller: { level: 5 }, storage: { id: 'st' }, memory: { sources: ['srcA', 'srcB'], lastFull: 4990 },
    find: () => [{ id: 'srcA' }, { id: 'srcB' }],
  };
  // miners need Game.getObjectById for sources
  global.Game.getObjectById = id => (id === 'srcA' || id === 'srcB') ? { id } : null;
  const spawn = {
    spawning: false, room, pos: { x: 35, y: 28 },
    spawnCreep: (body, name, opts) => { spawned.push({ role: opts.memory.role, name, cost: body.length }); return 0; },
  };
  const rv = S.run(spawn);
  return { spawned, rv, noted: W.noted };
}

const cases = [
  ['upgrader holding + storage: no withdraw from link/cont', () => {
    assert.deepStrictEqual(upRun({ hold: true, carry: 0, link: { store: { energy: 400 } }, cont: { store: { energy: 500 } } }), []);
  }],
  ['upgrader not holding + storage: withdraws from link', () => {
    assert.deepStrictEqual(upRun({ hold: false, carry: 0, link: { store: { energy: 400 } }, cont: { store: { energy: 500 } } }), ['link']);
  }],
  ['upgrader holding without storage: still no withdraw', () => {
    assert.deepStrictEqual(upRun({ hold: true, storage: false, carry: 0, cont: { store: { energy: 500 } } }), []);
  }],
  ['upgrader holding but still has energy: upgrades, no withdraw', () => {
    assert.deepStrictEqual(upRun({ hold: true, carry: 50, link: { store: { energy: 400 } } }), []);
  }],
  ['spawn: want + avail>=1300 -> defender first', () => {
    const r = spawnRun({ avail: 1500, creeps: { queen1: 'queen' } });
    assert.strictEqual(r.spawned[0] && r.spawned[0].role, 'defender');
    assert.deepStrictEqual(r.noted, ['W45N8', r.spawned[0].name]);
  }],
  ['spawn: want + avail<1300 -> ERR_BUSY, no miner (reserve energy)', () => {
    const r = spawnRun({ avail: 900, creeps: { queen1: 'queen' } }); // miner missing would previously spawn
    // delete miners so old code would try to spawn miner; new code must return ERR_BUSY
    assert.strictEqual(r.rv, ERR_BUSY);
    assert.deepStrictEqual(r.spawned, []);
  }],
  ['spawn: want + avail<1300 + hauler but no queen -> spawn queen only', () => {
    const r = spawnRun({ avail: 400, creeps: { h1: 'hauler' } }); // hauler avoids emergency harvester path
    assert.strictEqual(r.spawned.length, 1);
    assert.strictEqual(r.spawned[0].role, 'queen');
  }],
  ['spawn: no want + missing miner -> miner still spawns (home path unchanged)', () => {
    const r = spawnRun({ avail: 800, want: null, creeps: { queen1: 'queen' } });
    assert.ok(r.spawned.some(s => s.role === 'miner'), JSON.stringify(r.spawned));
  }],
];
let fail = 0;
for (const [n, f] of cases) {
  try { f(); console.log('ok  ', n); }
  catch (e) { fail++; console.log('FAIL', n, e.message); }
}
console.log(`defender energy hold: ${cases.length - fail}/${cases.length}`);
process.exit(fail ? 1 : 0);
