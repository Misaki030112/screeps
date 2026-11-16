// Boxed-in birth (W46N8 Spawn3 30,34 -> filler 31,33 / 31,35).
// hauler84302303 was born onto 31,33 at tick 84302303 and sat empty until 84302840: every neighbour is an
// extension, Spawn3, or the link. Bare PathFinder walks through extensions; move.to costs them at 255 and
// finds no path. birthDirs already refuses those tiles. A creep already standing there (console spawn, no
// directions, direction fallback) must leave on the spot — any role, not only a queen.
// Recycle at an adjacent spawn that is not spawning once carried energy is banked; otherwise the queen hatch
// (pickup, transfer, then recycle or suicide). node tests/trapped_hatch.js -> exits 1 on failure
const path = require('path'), fs = require('fs'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, {
  WORK: 'work', CARRY: 'carry', MOVE: 'move', RESOURCE_ENERGY: 'energy', OK: 0,
  STRUCTURE_SPAWN: 'spawn', STRUCTURE_EXTENSION: 'extension', STRUCTURE_TOWER: 'tower',
  STRUCTURE_LINK: 'link', STRUCTURE_ROAD: 'road', STRUCTURE_CONTAINER: 'container', STRUCTURE_RAMPART: 'rampart',
  TERRAIN_MASK_WALL: 1, LOOK_RESOURCES: 'resource', FIND_DROPPED_RESOURCES: 106,
  FIND_MY_SPAWNS: 112, FIND_MY_STRUCTURES: 108,
  _: { filter: (o, f) => Object.values(o || {}).filter(f) }, Game: { time: 84302303, creeps: {}, rooms: {} }, Memory: {},
});
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
const tiles = { '30,34': 'S', '31,33': 'F', '31,35': 'F', '32,34': 'L' };
for (const x of [30, 31, 32, 33, 34]) for (const y of [32, 33, 34, 35, 36]) if (!tiles[x + ',' + y]) tiles[x + ',' + y] = 'E';
const P = { raw: { stamps: { B: { tiles } } }, pos: {} };
const world = { at: {}, free: {}, busy: {} };
let terrainGet = () => 0;
const drops = [];
const acts = [];
stub('utils/plan.js', { get: () => P, key: (x, y) => x * 50 + y });
stub('utils/roomcache.js', { get: () => ({ at: world.at }), all: () => [], at: () => null, sites: () => [] });
stub('utils/move.js', { to: () => { acts.push(['move']); return false; } });
stub('utils/trace.js', { why() {} });
stub('managers/remote.js', { CFG: {} });
const Q = require(src('roles/queen.js'));
const S = require(src('managers/spawn.js'));
const room = { name: 'W46N8', memory: {}, getTerrain: () => ({ get: (x, y) => terrainGet(x, y) }) };
function loadStamp() {
  const at = {};
  for (const k in tiles) {
    if (tiles[k] === 'F') continue;
    const [x, y] = k.split(',').map(Number);
    const type = tiles[k] === 'S' ? 'spawn' : tiles[k] === 'L' ? 'link' : 'extension';
    at[x * 50 + y] = { [type]: tiles[k] === 'S' ? 'Spawn3' : type + x + '_' + y };
  }
  return at;
}
function structures() {
  const structs = [], spawns = [];
  for (const k of Object.keys(world.at)) {
    const n = +k, x = Math.floor(n / 50), y = n % 50, cell = world.at[k];
    for (const t of Object.keys(cell)) {
      const id = cell[t];
      const o = {
        id, structureType: t, pos: { x, y }, spawning: world.busy[id] || null,
        store: { getFreeCapacity: () => world.free[id] || 0 },
        recycleCreep(c) { acts.push(['recycle', id]); c.died = 'recycle'; return 0; },
      };
      structs.push(o);
      if (t === 'spawn') spawns.push(o);
    }
  }
  return { structs, spawns };
}
function creep(x, y, o = {}) {
  const energy = o.energy || 0, cap = o.cap == null ? 800 : o.cap;
  const c = {
    name: o.name || 'hauler84302303', spawning: !!o.spawning, room,
    memory: { role: o.role || 'hauler', home: 'W46N8' },
    store: { energy, getFreeCapacity: () => cap - energy, getCapacity: () => cap },
    pos: {
      x, y,
      lookFor(type) { return type === LOOK_RESOURCES ? drops.filter(d => d.pos.x === x && d.pos.y === y) : []; },
      findInRange(type, range, opts) {
        const { structs, spawns } = structures();
        const list = type === FIND_MY_SPAWNS ? spawns : type === FIND_MY_STRUCTURES ? structs : type === FIND_DROPPED_RESOURCES ? drops : [];
        return list.filter(s => Math.max(Math.abs(s.pos.x - x), Math.abs(s.pos.y - y)) <= range && (!opts || !opts.filter || opts.filter(s)));
      },
    },
    pickup(d) { acts.push(['pickup', d.id]); },
    transfer(t, res) { acts.push(['transfer', t.id, res]); },
    suicide() { acts.push(['suicide']); c.died = 'suicide'; },
  };
  c.store[RESOURCE_ENERGY] = energy;
  return c;
}
function reset() {
  acts.length = 0; drops.length = 0;
  world.at = loadStamp(); world.free = {}; world.busy = {}; terrainGet = () => 0;
}
const DXY = { 1: [0, -1], 2: [1, -1], 3: [1, 0], 4: [1, 1], 5: [0, 1], 6: [-1, 1], 7: [-1, 0], 8: [-1, -1] };
const tileOf = d => (30 + DXY[d][0]) + ',' + (34 + DXY[d][1]);
const sp = { room, pos: { x: 30, y: 34 } };
const cases = [
  ['empty hauler on 31,33 recycles at free Spawn3 the same tick', () => {
    reset();
    const c = creep(31, 33);
    assert.strictEqual(Q.freeTrapped(c), true);
    assert.deepStrictEqual(acts, [['recycle', 'Spawn3']]);
    assert.strictEqual(c.died, 'recycle');
  }],
  ['builder on the same tile recycles too (not a queen-only hatch)', () => {
    reset();
    const c = creep(31, 33, { role: 'builder', name: 'builder1' });
    assert.strictEqual(Q.freeTrapped(c), true);
    assert.deepStrictEqual(acts, [['recycle', 'Spawn3']]);
  }],
  ['31,35 is the same box', () => {
    reset();
    const c = creep(31, 35, { role: 'miner' });
    assert.strictEqual(Q.freeTrapped(c), true);
    assert.deepStrictEqual(acts, [['recycle', 'Spawn3']]);
  }],
  ['carried energy is transferred before recycle, even when the spawn is free', () => {
    reset();
    world.free.Spawn3 = 300;
    const c = creep(31, 33, { energy: 400 });
    assert.strictEqual(Q.freeTrapped(c), true);
    assert.deepStrictEqual(acts, [['transfer', 'Spawn3', 'energy']]);
    assert.ok(!c.died);
  }],
  ['energy goes to an extension with room when the spawn store is full', () => {
    reset();
    world.free.extension30_32 = 50;
    const c = creep(31, 33, { energy: 50 });
    assert.strictEqual(Q.freeTrapped(c), true);
    assert.deepStrictEqual(acts, [['transfer', 'extension30_32', 'energy']]);
  }],
  ['stranded drop on the tile is picked up before recycle', () => {
    reset();
    drops.push({ id: 'pile', resourceType: 'energy', amount: 200, pos: { x: 31, y: 33 } });
    const c = creep(31, 33);
    assert.strictEqual(Q.freeTrapped(c), true);
    assert.deepStrictEqual(acts, [['pickup', 'pile']]);
  }],
  ['spawn is spawning: do not recycle and do not suicide', () => {
    reset();
    world.busy.Spawn3 = { name: 'other' };
    const c = creep(31, 33);
    assert.strictEqual(Q.freeTrapped(c), true);
    assert.deepStrictEqual(acts, []);
    assert.ok(!c.died);
  }],
  ['a free spawn is used when another adjacent spawn is busy', () => {
    reset();
    world.at[32 * 50 + 32] = { spawn: 'SpawnFree' };
    world.busy.Spawn3 = { name: 'other' };
    const c = creep(31, 33);
    assert.strictEqual(Q.freeTrapped(c), true);
    assert.deepStrictEqual(acts, [['recycle', 'SpawnFree']]);
  }],
  ['no adjacent spawn: suicide (hatch), not a sit', () => {
    reset();
    world.at[30 * 50 + 34] = { extension: 'extension30_34' };
    const c = creep(31, 33);
    assert.strictEqual(Q.canEscape(c), false);
    assert.strictEqual(Q.freeTrapped(c), true);
    assert.deepStrictEqual(acts, [['suicide']]);
  }],
  ['no spawn but an extension has room: transfer first, suicide only once empty', () => {
    reset();
    world.at[30 * 50 + 34] = { extension: 'extension30_34' };
    world.free.extension30_34 = 50;
    const c = creep(31, 33, { energy: 40 });
    assert.strictEqual(Q.freeTrapped(c), true);
    assert.deepStrictEqual(acts, [['transfer', 'extension30_34', 'energy']]);
  }],
  ['road, container, or rampart neighbour is a way out', () => {
    reset();
    for (const type of ['road', 'container', 'rampart']) {
      acts.length = 0;
      world.at = loadStamp();
      world.at[32 * 50 + 32] = { [type]: type + '1' };
      const c = creep(31, 33);
      assert.strictEqual(Q.canEscape(c), true, type);
      assert.strictEqual(Q.freeTrapped(c), false, type);
      assert.deepStrictEqual(acts, [], type);
    }
  }],
  ['road under an extension is still boxed', () => {
    reset();
    world.at[32 * 50 + 32] = { road: 'r1', extension: 'extension32_32' };
    const c = creep(31, 33);
    assert.strictEqual(Q.canEscape(c), false);
    assert.strictEqual(Q.freeTrapped(c), true);
    assert.deepStrictEqual(acts, [['recycle', 'Spawn3']]);
  }],
  ['open neighbour: hauler beside Spawn3 is not recycled', () => {
    reset();
    const c = creep(29, 34);
    assert.strictEqual(Q.canEscape(c), true);
    assert.strictEqual(Q.freeTrapped(c), false);
    assert.deepStrictEqual(acts, []);
  }],
  ['terrain wall is not a way out', () => {
    reset();
    world.at = {};
    terrainGet = () => 1;
    const c = creep(10, 10, { role: 'upgrader' });
    assert.strictEqual(Q.canEscape(c), false);
    assert.strictEqual(Q.freeTrapped(c), true);
    assert.deepStrictEqual(acts, [['suicide']]);
  }],
  ['still spawning: not hatched (birth tile is not occupied yet)', () => {
    reset();
    const c = creep(31, 33, { spawning: true });
    assert.strictEqual(Q.freeTrapped(c), false);
    assert.deepStrictEqual(acts, []);
  }],
  ['birthDirs still drops boxed 31,33 / 31,35 for a hauler and a queen', () => {
    reset();
    for (const role of ['hauler', 'queen', 'builder']) {
      const d = S.birthDirs(sp, role).map(tileOf);
      assert.ok(!d.includes('31,33') && !d.includes('31,35'), role + ' ' + JSON.stringify(d));
    }
    const q = S.birthDirs(sp, 'queen').map(tileOf);
    assert.ok(q.includes('30,33') && q.indexOf('30,33') < q.indexOf('29,34'), JSON.stringify(q));
    const h = S.birthDirs(sp, 'hauler').map(tileOf);
    assert.strictEqual(h[0], '29,35', JSON.stringify(h));
  }],
  ['an inside tile with a free neighbour is offered again (filter not widened)', () => {
    reset();
    delete world.at[32 * 50 + 32];
    const d = S.birthDirs(sp, 'queen').map(tileOf);
    assert.ok(d.includes('31,33') && d.indexOf('31,33') < d.indexOf('29,34'), JSON.stringify(d));
    assert.ok(!d.includes('31,35'), JSON.stringify(d));
  }],
  ['every side trapped: birthDirs falls back to the full list instead of offering nothing', () => {
    reset();
    terrainGet = () => 1;
    const d = S.birthDirs(sp, 'hauler');
    assert.strictEqual(d.length, 8);
    assert.ok(d.map(tileOf).includes('31,33'));
  }],
  ['main.js hatches every creep after spawn-finish and before shed or the role', () => {
    const main = fs.readFileSync(src('main.js'), 'utf8');
    const loop = main.slice(main.indexOf('for (const n of cpuorder.order'));
    const at = s => loop.indexOf(s);
    assert.ok(at('if (c.spawning) continue') >= 0 && at('if (c.spawning) continue') < at('freeTrapped'));
    assert.ok(at('roles.queen.freeTrapped(c)') < at('cpuorder.shed'));
    assert.ok(at('roles.queen.freeTrapped(c)') < at('(roles[c.memory.role] || roles.harvester).run(c)'));
    const queen = fs.readFileSync(src('roles/queen.js'), 'utf8');
    assert.ok(/if \(freeTrapped\(c\)\) return/.test(queen));
  }],
];
let fail = 0;
for (const [name, fn] of cases) {
  try { fn(); console.log('ok  ', name); }
  catch (e) { fail++; console.log('FAIL', name, e.stack || e.message); }
}
console.log(`trapped hatch: ${cases.length - fail}/${cases.length}`);
process.exit(fail ? 1 : 0);
