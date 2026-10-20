// Floor-time route-road builder (src/roles/builder.js routeJob, strategy review 2026-10-20 17:4x).
// spawn.js spawns ONE road builder at the 15k floor when a W45N8 route road is < 30% (roads.repairTarget(0.3)). Before the fix the
// builder could only refill from the remote container for road SITES, so with only a repair job it got no energy (defLow), idled 50 t
// and recycled, and spawn.js spawned the next one: 7 spawn/recycle cycles in ~1400 t while W45N8 2,12 kept decaying.
// Now: refill at the W45N8 container, route roads < 50% go before home road sites, and the remote repair stays sticky.
// node tests/builder_route_repair.js -> exits 1 on failure
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, {
  RESOURCE_ENERGY: 'energy', STRUCTURE_ROAD: 'road', STRUCTURE_CONTAINER: 'container', STRUCTURE_WALL: 'constructedWall', STRUCTURE_RAMPART: 'rampart',
  STRUCTURE_LINK: 'link', LEFT: 7, RIGHT: 3, TOP: 1, BOTTOM: 5, OK: 0, ERR_NOT_ENOUGH_RESOURCES: -6,
  FIND_MY_CONSTRUCTION_SITES: 114, LOOK_CONSTRUCTION_SITES: 'constructionSite', LOOK_STRUCTURES: 'structure',
  Game: { rooms: {}, creeps: {}, time: 1 }, _: { min: (a, f) => a.reduce((b, x) => (f(x) < f(b) ? x : b)), max: (a, f) => a.reduce((b, x) => (f(x) > f(b) ? x : b)) },
});
let W;
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
const P = { pos: { controllerDrop: [31, 29], fillerContainerA: [35, 24], controllerContainer: [30, 30], controllerLink: null }, any: {}, standing: new Set() };
stub('utils/plan.js', { get: () => P, key: (x, y) => x * 50 + y });
stub('utils/move.js', { to: (c, x, y) => { W.moved = [x, y]; return c.pos.x === x && c.pos.y === y || W.inRange; }, invalidate: () => {} });
stub('utils/roomcache.js', { at: () => null, all: () => [], sites: () => W.homeSites, invalidate: () => {} });
stub('utils/trace.js', { why: (c, k) => { W.why = k; } });
stub('utils/salvage.js', { retire: () => { W.retired = true; return true; } });
const RCFG = { W45N8: { cont: [13, 11], roads: [[2, 12]], live: true } };
stub('managers/remote.js', { CFG: RCFG, paused: () => false, route: r => ['W46N8', r], exitTile: (r, a) => (a === 'W45N8' ? [0, 14] : [49, 14]) });
stub('managers/roads.js', { repairTarget: f => { const r = W.route.filter(s => s.hits / s.hitsMax < (f || 0.5)); return r.length ? _.min(r, s => s.hits / s.hitsMax) : null; }, isHomeTile: () => false });
stub('managers/walls.js', { defLow: () => true, siege: () => false, noUpgrade: () => false, decaying: () => null, belowFloor: () => false,
  repairJob: () => null, FLOOR: 5000, defReserve: () => 15000, spend: () => {} });
stub('managers/threat.js', { reserve: () => 1300 });
stub('managers/links.js', { roles: () => ({}) });
stub('roles/hauler.js', { pickups: () => [] });
const B = require(src('roles/builder.js'));

const road = (room, x, y, hits, max) => ({ id: `r${room}${x},${y}`, pos: { roomName: room, x, y }, hits, hitsMax: max, structureType: STRUCTURE_ROAD });
function world(o) {
  const r212 = road('W45N8', 2, 12, 6000, 25000), r1210 = road('W45N8', 12, 10, 1800, 5000);
  const homeSite = { id: 'hs', pos: { roomName: 'W46N8', x: 42, y: 25 }, progress: 0, progressTotal: 300, structureType: STRUCTURE_ROAD };
  const k = { id: 'k', pos: { roomName: 'W45N8', x: 13, y: 11 }, structureType: STRUCTURE_CONTAINER, store: { [RESOURCE_ENERGY]: 1500 } };
  W = Object.assign({ route: [r212, r1210], homeSites: [homeSite], moved: null, why: null, retired: false, inRange: false }, o || {});
  const objs = { [r212.id]: r212, [r1210.id]: r1210, hs: homeSite, k };
  Game.getObjectById = id => objs[id] || null;
  const home = { name: 'W46N8', storage: { pos: { x: 37, y: 31, roomName: 'W46N8' }, store: { [RESOURCE_ENERGY]: 14700 } }, controller: { level: 6 },
    find: () => [], lookForAt: () => [] };
  const R = { name: 'W45N8', find: () => [], lookForAt: (t, x, y) => (t === 'structure' && x === 13 && y === 11 ? [k] : []) };
  Game.rooms.W46N8 = home; Game.rooms.W45N8 = R;
  return { r212, r1210, homeSite, k, home, R };
}
function creep(room, e, mem, x, y) {
  const st = { [RESOURCE_ENERGY]: e, getFreeCapacity: () => 250 - st[RESOURCE_ENERGY], getUsedCapacity: () => st[RESOURCE_ENERGY] };
  return { name: 'builderT', room, store: st, memory: Object.assign({ role: 'builder', home: 'W46N8' }, mem), ticksToLive: 1400,
    pos: { x, y, roomName: room.name, getRangeTo: () => 10 }, getActiveBodyparts: () => 5,
    withdraw: t => { W.withdrew = t; }, build: t => { W.built = t; return 0; }, repair: t => { W.repaired = t; return 0; }, move: d => { W.dir = d; } };
}
const cases = [
  ['empty builder at the 15k floor, only a route REPAIR job: walks to W45N8 for energy, never recycles', () => {
    const w = world();
    const c = creep(w.home, 0, { working: false }, 35, 29);
    for (let i = 0; i < 80; i++) { W.moved = null; B.run(c); }
    assert.strictEqual(W.retired, false, 'must not recycle (old code: 50t waiting_feed then recycle, spawn.js respawns it)');
    assert.deepStrictEqual(W.moved, [49, 14], 'heads for the W46N8 -> W45N8 exit');
  }],
  ['in W45N8 at the container: withdraws there', () => {
    const w = world({ inRange: true });
    const c = creep(w.R, 0, { working: false }, 13, 12);
    B.run(c);
    assert.strictEqual(W.withdrew, w.k);
  }],
  ['loaded builder: route road < 50% goes before a home road site', () => {
    const w = world();
    const c = creep(w.home, 250, { working: true }, 38, 29);
    B.run(c);
    assert.strictEqual(c.memory.t, w.r212.id, 'worst route road first');
    assert.deepStrictEqual(W.moved, [49, 14], 'walks to W45N8, not to home site 42,25');
  }],
  ['remote repair stays sticky while home sites exist (no 2,12 <-> 12,10 bounce)', () => {
    const w = world({ inRange: true });
    const c = creep(w.R, 250, { working: true, t: 'rW45N812,10' }, 12, 11);
    B.run(c);
    assert.strictEqual(c.memory.t, w.r1210.id);
    assert.strictEqual(W.repaired, w.r1210);
  }],
  ['all route roads >= 50%: floor builder with no energy still recycles (no immortal builder)', () => {
    const w = world();
    w.r212.hits = 20000; w.r1210.hits = 4000;
    const c = creep(w.home, 0, { working: false }, 35, 29);
    for (let i = 0; i < 80 && !W.retired; i++) B.run(c);
    assert.strictEqual(W.retired, true);
  }],
];
cases.push(['spawn.js: an alive builder does not cost an upgrader slot when the room wants no builder (route builder at the floor)', () => {
  const sp = require('fs').readFileSync(src('managers/spawn.js'), 'utf8');
  assert.ok(sp.includes('if (nSites && (roadBuilder || !T.builder)) T.upgrader = targets('), 'old rule kept upgrader at 1 while the road builder lived');
}]);
let fail = 0;
for (const [n, f] of cases) { try { f(); console.log('ok   ' + n); } catch (e) { fail++; console.log('FAIL ' + n + '\n     ' + e.message); } }
process.exit(fail ? 1 : 0);
