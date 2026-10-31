// Soft-upgrade bank fixes (patrol 2026-11-01): defLow zeros T.mminer; setRoleTargets exported; surplus upgrader recycle.
// node tests/soft_upgrade_bank.js
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, {
  WORK: 'work', CARRY: 'carry', MOVE: 'move', RESOURCE_ENERGY: 'energy',
  STRUCTURE_LINK: 'link', STRUCTURE_CONTAINER: 'container', STRUCTURE_SPAWN: 'spawn',
  STRUCTURE_EXTENSION: 'extension', STRUCTURE_TOWER: 'tower', FIND_MINERALS: 116,
  Game: { time: 100, creeps: {}, spawns: {}, rooms: {} },
  _: { filter: (a, f) => (Array.isArray(a) ? a : Object.values(a || {})).filter(f), countBy: (a, f) => a.reduce((m, x) => { const k = f(x); m[k] = (m[k] || 0) + 1; return m; }, {}), sum: () => 0 },
  Memory: { ops: {}, defense: { reserveE: 15000 } },
});
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
const P = { pos: { upgraders: [[29, 30], [30, 31]], controllerContainer: [30, 30], controllerLink: [30, 31], fillerContainerA: [35, 24], fillers: [], miners: [], mineralMiner: [41, 24] }, raw: { stamps: {} }, any: {} };
stub('utils/plan.js', { get: () => P, key: (x, y) => x * 50 + y, STATIONARY_FILL: false });
stub('roles/builder.js', { remoteRoadSite: () => null });
stub('utils/move.js', { to: () => true });
const cont = { store: { getFreeCapacity: () => 1800, energy: 0 } };
stub('utils/roomcache.js', { all: (r, t) => (t === 'extractor' || t === STRUCTURE_LINK ? [{} ,{},{}] : []), at: (r, x, y) => (x === 41 && y === 24 ? cont : (x === 30 && y === 30 ? { store: { energy: 0 } } : null)), get: () => ({ at: [] }), sites: () => [] });
stub('utils/trace.js', { why: () => {} });
stub('managers/threat.js', { reserve: () => 0, holding: () => false, wantDefender: () => null, armed: () => false, energyHold: () => false, noteSpawn: () => {} });
stub('managers/roads.js', { phase: () => 'done', repairTarget: () => null });
stub('roles/hauler.js', { pickups: () => [] });
stub('roles/raid9.js', { pauseCivilians: () => false, wantSpawn: () => null });
stub('roles/probe.js', { wantSpawn: () => false });
stub('roles/reserve7.js', { wantSpawn: () => null });
stub('roles/conquest.js', { guardWant: () => null, wantSpawn: () => null, noteSpawned: () => {} });
stub('roles/quad.js', { wantSpawn: () => null });
stub('rooms/w47n8/index.js', { homeWant: () => null });
stub('rooms/w47n8/fillmeter.js', { tick: () => {} });
stub('managers/home.js', { on: () => false, active: () => false, wantGuards: () => 0, alert: () => false });
let defLow = true, stepHeld = true;
stub('managers/walls.js', {
  phase: () => 'build', noUpgrade: () => false, wantBuilder: () => false, reserved: () => 0, budgetE: () => 0, fund: () => 0,
  defReserve: () => 15000, defLow: () => defLow, stepHeld: () => stepHeld, siege: () => false, fundSpend: () => false, UP_SAFE: 3000,
});
const S = require(src('managers/spawn.js'));

// targets() alone still allows mminer when extractor+container (defLow applied in setRoleTargets/run1)
const roomBase = () => ({
  name: 'W46N8', controller: { level: 7, ticksToDowngrade: 20000 }, energyCapacityAvailable: 5600,
  storage: { store: { energy: 14000, O: 17324 } }, terminal: { store: { O: 120000 } },
  find: () => [{ mineralType: 'O', mineralAmount: 30000 }],
  memory: {},
});
Memory.ops = undefined;
const mmOpen = S.targets(roomBase(), {}, 0, 900, 0).mminer;
assert.strictEqual(mmOpen, 1, 'targets alone still opens mminer when uncapped');

Game.creeps = {};
const room = roomBase();
Game.rooms.W46N8 = room;
defLow = true;
const T = S.setRoleTargets(room);
assert.ok(T, 'setRoleTargets returns T');
assert.strictEqual(T.mminer, 0, 'defLow -> T.mminer 0');
assert.strictEqual(room.memory.roleTargets.mminer, 0, 'roleTargets.mminer persisted');

defLow = false;
room.storage.store.energy = 20000;
const T2 = S.setRoleTargets(room);
assert.strictEqual(T2.mminer, 1, 'above floor -> mminer back (uncapped)');

Memory.ops = { mineralCap: 50000 };
const T3 = S.setRoleTargets(room);
assert.strictEqual(T3.mminer, 0, 'mineralCap stops mminer even above floor');

// upgrader surplus recycle: load role with stubs
delete require.cache[require.resolve(src('roles/upgrader.js'))];
const recycled = [];
const moved = [];
const upA = { name: 'upgrader1', memory: { role: 'upgrader', home: 'W46N8', spot: [29, 30] }, store: { energy: 0 }, pos: { x: 29, y: 30, roomName: 'W46N8', isNearTo: () => true, inRangeTo: () => true }, room, getActiveBodyparts: () => 14 };
const upB = { name: 'upgrader2', memory: { role: 'upgrader', home: 'W46N8', spot: [30, 30] }, store: { energy: 0 }, pos: { x: 30, y: 30, roomName: 'W46N8', isNearTo: () => true, inRangeTo: () => true }, room, getActiveBodyparts: () => 14 };
Game.creeps = { upgrader1: upA, upgrader2: upB };
Game.spawns = { Spawn1: { pos: { x: 35, y: 28, roomName: 'W46N8' }, recycleCreep: (c) => recycled.push(c.name) } };
room.controller = Object.assign(room.controller, { my: true, owner: { username: 'x' }, level: 7 });
room.memory.roleTargets = { upgrader: 1 };
stub('utils/sign.js', { needs: () => false, SIGN: 'x' });
const U = require(src('roles/upgrader.js'));
U.run(upB);
assert.deepStrictEqual(recycled, ['upgrader2'], '2nd upgrader recycled when want=1');
// Kept creep (index 0) is covered by the indexOf < want guard; no need to drive the full upgrade path here.

console.log('soft_upgrade_bank ok');
