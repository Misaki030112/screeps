// Builder + v4 barrier job (roles/builder.js <- managers/walls.repairJob/spend). node tests/builder_walls.js -> exit 1 on failure
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, { RESOURCE_ENERGY: 'energy', STRUCTURE_ROAD: 'road', STRUCTURE_WALL: 'constructedWall', STRUCTURE_RAMPART: 'rampart', STRUCTURE_CONTAINER: 'container', OK: 0, WORK: 'work',
  Game: { rooms: {}, creeps: {}, time: 1, getObjectById: id => OBJ[id] }, _: { min: (a, f) => a.reduce((b, x) => (f(x) < f(b) ? x : b)), max: (a, f) => a[0] } });
let OBJ = {}, JOB = null, SPENT = 0, SITES = [];
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
stub('utils/plan.js', { get: () => ({ pos: { controllerDrop: [31, 29], fillerContainerA: [35, 24] }, any: {} }), key: (x, y) => x * 50 + y });
stub('utils/move.js', { to: () => true, invalidate: () => {} });
stub('utils/roomcache.js', { at: () => null, all: () => [], sites: () => SITES, invalidate: () => {} });
stub('utils/trace.js', { why: () => {} });
stub('managers/remote.js', { CFG: {}, paused: () => true });
stub('managers/threat.js', { reserve: () => 1300 });
stub('roles/hauler.js', { pickups: () => [] });
let DK = null;
let BF = false;
stub('managers/walls.js', { DECAY_CAP: 10000, decaying: (r, taken) => (DK && !taken.has(DK.id) ? DK : null), repairJob: () => JOB, belowFloor: () => BF, spend: (r, e) => { SPENT += e; } });
const B = require(src('roles/builder.js'));
const home = { name: 'W46N8', storage: { pos: { x: 37, y: 31 }, store: { energy: 20000 } }, controller: { id: 'ctl' } };
Game.rooms.W46N8 = home;
function creep(mem) {
  const c = { room: home, memory: Object.assign({ role: 'builder', home: 'W46N8', working: true }, mem), pos: { x: 30, y: 12, getRangeTo: () => 3 },
    store: { energy: 50, [RESOURCE_ENERGY]: 50, getFreeCapacity: () => 0 }, getActiveBodyparts: () => 5, build: () => 0, transfer: () => 0,
    repair: t => { c.rep = t.id; t.hits += 500; return 0; } };
  return c;
}
const cases = [
  ['no sites/roads: takes the barrier job, repairs, debits WORK energy', () => {
    OBJ = { w1: { id: 'w1', hits: 30000, hitsMax: 3e8, pos: { x: 26, y: 7, roomName: 'W46N8' } } }; JOB = { id: 'w1', cap: 40000 }; SPENT = 0;
    const c = creep(); B.run(c); assert.strictEqual(c.rep, 'w1'); assert.strictEqual(c.memory.tcap, 40000); assert.strictEqual(SPENT, 5);
  }],
  ['sticks to the barrier until its chunk cap, then re-picks', () => {
    const c = creep({ t: 'w1', tcap: 40000 }); OBJ.w1.hits = 39000; JOB = { id: 'w2', cap: 1 }; B.run(c); assert.strictEqual(c.rep, 'w1');
    OBJ.w1.hits = 40000; OBJ.w2 = { id: 'w2', hits: 10, hitsMax: 3e8, pos: { x: 27, y: 7, roomName: 'W46N8' } }; JOB = { id: 'w2', cap: 10010 };
    const d = creep({ t: 'w1', tcap: 40000 }); B.run(d); assert.strictEqual(d.rep, 'w2'); assert.strictEqual(d.memory.tcap, 10010);
  }],
  ['a new site outranks the barrier chunk', () => {
    OBJ.s1 = { id: 's1', progress: 0, progressTotal: 300, structureType: 'extension', pos: { x: 33, y: 26, roomName: 'W46N8' } }; SITES = [OBJ.s1];
    const c = creep({ t: 'w2', tcap: 10010 }); c.build = t => { c.built = t.id; return 0; }; B.run(c); assert.strictEqual(c.built, 's1'); assert.ok(!c.memory.tcap); SITES = [];
  }],
  ['v5: barriers below the 10k floor outrank a road site', () => {
    const r1 = { id: 'r1', progress: 0, progressTotal: 300, structureType: 'road', pos: { x: 33, y: 20, roomName: 'W46N8' } }; OBJ.r1 = r1; SITES = [r1]; BF = true;
    const c = creep(); B.run(c); assert.strictEqual(c.memory.t, JOB.id); BF = false; SITES = [];
  }],
  ['a decaying gate outranks a site and stays sticky until DECAY_CAP; a 2nd builder leaves it to the first', () => {
    OBJ.g1 = { id: 'g1', hits: 1, hitsMax: 3e8, structureType: 'rampart', pos: { x: 25, y: 16, roomName: 'W46N8' } }; DK = OBJ.g1; SITES = [OBJ.s1];
    const c = creep(); B.run(c); assert.strictEqual(c.rep, 'g1'); assert.strictEqual(c.memory.tcap, 10000); assert.ok(c.memory.urgent);
    Game.creeps.a = c; DK = OBJ.g1; OBJ.g1.hits = 6000;
    const d = creep(); d.build = t => { d.built = t.id; return 0; }; B.run(d); assert.strictEqual(d.built, 's1'); assert.ok(!d.memory.urgent);
    DK = null; c.rep = null; B.run(c); assert.strictEqual(c.rep, 'g1', 'sticky above floor until cap');
    OBJ.g1.hits = 10000; c.build = t => { c.built = t.id; return 0; }; B.run(c); assert.strictEqual(c.built, 's1'); assert.ok(!c.memory.urgent);
    delete Game.creeps.a; SITES = [];
  }],
  ['v5 low carry: a fresh far target sends the builder to refill first; a near one is worked', () => {
    OBJ = { w9: { id: 'w9', hits: 10000, hitsMax: 3e8, pos: { x: 6, y: 27, roomName: 'W46N8' } } }; JOB = { id: 'w9', cap: 20000 }; SITES = [];
    const far = creep(); far.store.getFreeCapacity = () => 500; far.pos.getRangeTo = () => 25; B.run(far);
    assert.ok(!far.rep); assert.strictEqual(far.memory.working, false); assert.ok(!far.memory.t);
    const near = creep(); near.store.getFreeCapacity = () => 500; near.pos.getRangeTo = () => 3; B.run(near); assert.strictEqual(near.rep, 'w9');
    const full = creep(); full.pos.getRangeTo = () => 25; B.run(full); assert.strictEqual(full.memory.t, 'w9', 'full carry walks to the far target');
  }],
  ['no job and nothing else: parks (no barrier repair)', () => { JOB = null; const c = creep(); c.store.energy = 0; c.store[RESOURCE_ENERGY] = 0; c.memory.working = false; B.run(c); assert.ok(!c.rep); }],
];
let fail = 0; for (const [n, f] of cases) { try { f(); console.log('ok  ', n); } catch (e) { fail++; console.log('FAIL', n, e.message.replace(/\n/g, ' ')); } }
process.exit(fail ? 1 : 0);
