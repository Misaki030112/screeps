// Paused remote→builder (src/roles/builder.js): repair planned roads/containers below 80%;
// when no build work, a remapped creep (memory.remote) upgrades from fc/source containers — never idles no_task
// and never withdraws storage below the defender reserve.
// node tests/builder_remote.js -> exits 1 on failure
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, {
  RESOURCE_ENERGY: 'energy', STRUCTURE_ROAD: 'road', STRUCTURE_CONTAINER: 'container',
  STRUCTURE_SPAWN: 'spawn', STRUCTURE_EXTENSION: 'extension', STRUCTURE_TOWER: 'tower',
  OK: 0, FIND_MY_CONSTRUCTION_SITES: 114, LOOK_CONSTRUCTION_SITES: 'constructionSite',
  Game: { rooms: {}, time: 1 }, _: { min: (a, f) => a[0], max: (a, f) => a.reduce((b, x) => (f(x) > f(b) ? x : b)) },
});
let W;
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
const P = {
  pos: { controllerDrop: [31, 29], fillerContainerA: [35, 24], miners: [[31, 12]], controllerContainer: [30, 30] },
  any: { [35 * 50 + 24]: { type: 'container' }, [38 * 50 + 30]: { type: 'road' }, [31 * 50 + 12]: { type: 'container' } },
};
stub('utils/plan.js', { get: () => P, key: (x, y) => x * 50 + y });
stub('utils/move.js', { to: (c, x, y) => { W.moved = [x, y]; return true; }, invalidate: () => {} });
stub('utils/roomcache.js', {
  at: (room, x, y) => (x === 35 && y === 24 ? W.fc : x === 31 && y === 12 ? W.srcA : null),
  all: (room, t) => (t === STRUCTURE_ROAD ? W.roads : t === STRUCTURE_CONTAINER ? W.containers : []),
  sites: () => W.sites || [],
  invalidate: () => {},
  get: () => ({ at: [] }),
});
stub('utils/trace.js', { why: (c, k) => { W.why = k; } });
const RCFG = {};
stub('managers/remote.js', { CFG: RCFG, paused: r => !(RCFG[r] && RCFG[r].live) });
stub('managers/threat.js', { reserve: () => 1300 });
stub('roles/hauler.js', { pickups: () => [W.srcA].filter(Boolean) });
const B = require(src('roles/builder.js'));

function run(o) {
  W = Object.assign({
    roads: [], containers: [], sites: [], fc: null, srcA: null, upgraded: false, withdrawn: null, why: null, moved: null,
  }, o);
  const store = (e, cap) => ({ energy: e, getCapacity: () => cap, getFreeCapacity: () => cap - e, [RESOURCE_ENERGY]: e });
  const home = {
    name: 'W46N8', storage: { pos: { x: 37, y: 31 }, store: store(W.storageE || 100, 1e6) },
    controller: { id: 'ctl' },
  };
  Game.rooms.W46N8 = home;
  const mem = Object.assign({ role: 'rminer', remote: 'W45N8', home: 'W46N8', working: false }, o.mem || {});
  if (o.noRemote) delete mem.remote;
  const c = {
    room: home, memory: mem,
    store: Object.assign(store(o.carry || 0, 50), { [RESOURCE_ENERGY]: o.carry || 0 }),
    pos: { x: 38, y: 30, getRangeTo: () => 2 },
    withdraw: (t) => { W.withdrawn = t === W.fc ? 'fc' : t === W.srcA ? 'srcA' : t === home.storage ? 'storage' : '?'; },
    transfer: () => 0,
    upgradeController: () => { W.upgraded = true; },
    build: () => 0, repair: () => { W.repaired = true; return 0; },
    getActiveBodyparts: () => 5,
  };
  B.run(c);
  return W;
}

const road = (x, y, hits, max = 5000) => ({ pos: { x, y }, hits, hitsMax: max, structureType: STRUCTURE_ROAD, id: `r${x},${y}` });
const cont = (x, y, hits, e = 200) => ({
  pos: { x, y }, hits, hitsMax: 250000, structureType: STRUCTURE_CONTAINER, id: `c${x},${y}`,
  store: Object.assign({ energy: e, [RESOURCE_ENERGY]: e }, { getCapacity: () => 2000, getFreeCapacity: () => 2000 - e }),
});

const cases = [
  ['road at 70% hits is repairable (threshold 80%)', () => {
    const r = run({
      roads: [road(38, 30, 3500)], containers: [],
      fc: cont(35, 24, 200000, 400), mem: { working: true, t: undefined }, carry: 50,
    });
    // with working+carry and a hurt road, should repair (set target / move)
    assert.ok(r.moved || r.repaired, 'expected move-to-repair or repair');
  }],
  ['road at 85% hits is NOT repairable -> remote upgrades', () => {
    const r = run({
      roads: [road(38, 30, 4250)], containers: [cont(35, 24, 200000)],
      fc: cont(35, 24, 200000, 400), carry: 50, storageE: 100,
    });
    assert.strictEqual(r.upgraded, true);
    assert.notStrictEqual(r.why, 'n');
  }],
  ['remote empty: withdraw fc, never storage when storage below reserve', () => {
    const r = run({
      roads: [road(38, 30, 5000)], containers: [],
      fc: cont(35, 24, 200000, 400), carry: 0, storageE: 100,
    });
    assert.strictEqual(r.withdrawn, 'fc');
  }],
  ['non-remote builder with storage + no work -> no_task (unchanged)', () => {
    const r = run({
      roads: [], containers: [], fc: cont(35, 24, 200000, 400), carry: 0, storageE: 5000,
      mem: { role: 'builder', home: 'W46N8' }, noRemote: true,
    });
    assert.strictEqual(r.why, 'n');
    assert.strictEqual(r.upgraded, false);
  }],
  ['remote road builder in the remote room refills from that remote container (keeps 400)', () => {
    RCFG.W45N8 = { cont: [13, 11], roads: [[2, 12]], live: true };
    global.LOOK_STRUCTURES = 'structure';
    const k = cont(13, 11, 250000, 2000), site = { id: 's1', pos: { roomName: 'W45N8', x: 2, y: 12 }, progress: 0, progressTotal: 1500, structureType: 'road' };
    Game.getObjectById = id => (id === 's1' ? site : null);
    let got = null;
    const R = { name: 'W45N8', lookForAt: (t, x, y) => (t === 'structure' && x === 13 && y === 11 ? [k] : t === 'constructionSite' && x === 2 && y === 12 ? [site] : []) };
    Game.rooms.W45N8 = R;
    W = { sites: [], roads: [], containers: [] };
    const store = { energy: 0, [RESOURCE_ENERGY]: 0, getCapacity: () => 250, getFreeCapacity: () => 250, getUsedCapacity: () => 0 };
    const c = { room: R, memory: { role: 'builder', home: 'W46N8', t: 's1', working: false }, store, pos: { x: 6, y: 11, getRangeTo: () => 7 },
      withdraw: t => { got = t; } };
    Game.rooms.W46N8 = { name: 'W46N8', storage: { pos: { x: 37, y: 31 }, store: { [RESOURCE_ENERGY]: 4000 } } };
    B.run(c);
    assert.strictEqual(got, k);
    k.store[RESOURCE_ENERGY] = 600; got = null; B.run(c);
    assert.notStrictEqual(got, k, 'must leave >=400 for rhaulers');
    delete RCFG.W45N8; delete Game.getObjectById;
  }],
];
let fail = 0;
for (const [n, f] of cases) {
  try { f(); console.log('ok  ', n); }
  catch (e) { fail++; console.log('FAIL', n, e.message); }
}
console.log(`builder remote: ${cases.length - fail}/${cases.length}`);
process.exit(fail ? 1 : 0);
