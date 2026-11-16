// Home hauler body. KO labs, or a terminal mineral park, spawn 16C8M (1200e).
// Labs off and no park: link-era 6C3M (450e). The 1050 storage-era cap stays for the energy-only body.
// node tests/spawn_hauler_body.js
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, {
  WORK: 'work', CARRY: 'carry', MOVE: 'move', RESOURCE_ENERGY: 'energy',
  STRUCTURE_LINK: 'link',
  Memory: { ops: {} },
});
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
stub('utils/plan.js', { get: () => null, key: (x, y) => x * 50 + y, STATIONARY_FILL: false });
stub('utils/roomcache.js', { all: () => [], at: () => null, get: () => ({ at: [] }), sites: () => [] });
const S = require(src('managers/spawn.js'));
const L = require(src('managers/labs.js'));

const COST = { carry: 50, move: 50, work: 100 };
const n = (b, p) => b.filter(x => x === p).length;
const cost = b => b.reduce((s, p) => s + COST[p], 0);
function box(id, store, free) {
  const o = { id, store: Object.assign({}, store), pos: { x: 10, y: 10 } };
  o.store.getFreeCapacity = () => free;
  return o;
}
function home(o) {
  o = o || {};
  const term = o.terminal === null ? null : box('t', o.term || { O: 3000, K: 3000, KO: 0 }, o.free == null ? 20000 : o.free);
  const stor = o.storage === null ? null : box('s', Object.assign({ energy: o.energy == null ? 20000 : o.energy }, o.stor || {}), o.sFree == null ? 900000 : o.sFree);
  return { name: o.name || 'W46N8', terminal: term, storage: stor };
}
function labs(on) { Memory.ops = on ? { labs: { W46N8: 'KO' } } : {}; }
function energyBudget() { return S.bodyEnergy('hauler', 300, 5600, 300, true, true); }
function body(room, rcl, links, cap) { return S.homeHaulerBody(room, energyBudget(), rcl == null ? 7 : rcl, links == null ? 3 : links, cap == null ? 5600 : cap); }

const cases = [
  ['storage-era bodyEnergy stays 1050; the mineral body lifts it', () => {
    assert.strictEqual(S.bodyEnergy('hauler', 5600, 5600, 5600, true, true), 1050);
    assert.strictEqual(energyBudget(), 1050);
    assert.strictEqual(S.bodyEnergy('hauler', 300, 1300, 300, true, false), 300);
  }],
  ['labs on, terminal buffers exact and free: 16C8M even with no park task', () => {
    labs(true);
    const rm = home({ free: 20000, energy: 15557 });
    assert.strictEqual(L.parkTask(rm, { idle: false }), null);
    assert.strictEqual(L.parkTask(rm, { idle: true }), null);
    assert.strictEqual(S.homeHaulMineral(rm), true);
    const b = body(rm);
    assert.strictEqual(n(b, 'carry'), 16);
    assert.strictEqual(n(b, 'move'), 8);
    assert.strictEqual(cost(b), 1200);
    assert.deepStrictEqual(b, S.B.queen(1200));
    assert.deepStrictEqual(b, S.B.roadHauler(1200));
    assert.deepStrictEqual(Memory.ops.labs, { W46N8: 'KO' });
  }],
  ['labs on, terminal tight, surplus O: 16C8M (park is the live job)', () => {
    labs(true);
    const rm = home({ term: { O: 125976, K: 175792, KO: 36, energy: 0 }, free: 400, energy: 15557 });
    const t = L.parkTask(rm, { idle: false });
    assert.strictEqual(t.res, 'O');
    assert.ok(t.amt > 100000, 'urgent park is the surplus O, got ' + (t && t.amt));
    assert.notStrictEqual(t.res, 'energy');
    const b = body(rm);
    assert.strictEqual(n(b, 'carry'), 16);
    assert.strictEqual(n(b, 'move'), 8);
    assert.strictEqual(cost(b), S.HAUL_MINERAL_E);
    assert.deepStrictEqual(Memory.ops.labs, { W46N8: 'KO' });
  }],
  ['labs on, terminal not tight, idle surplus still 16C8M', () => {
    labs(true);
    const rm = home({ term: { O: 125976, K: 3000, KO: 0 }, free: 20000, energy: 20000 });
    const t = L.parkTask(rm, { idle: true });
    assert.strictEqual(t && t.res, 'O');
    assert.strictEqual(t.amt, 125976 - 3000);
    assert.strictEqual(L.parkTask(rm, { idle: false }), null, 'not tight: urgent park waits');
    const b = body(rm);
    assert.strictEqual(n(b, 'carry'), 16);
    assert.strictEqual(n(b, 'move'), 8);
  }],
  ['labs off, no park: link-era 6C3M, including a physically full terminal', () => {
    labs(false);
    const quiet = home({ free: 20000, energy: 20000 });
    assert.strictEqual(L.parkTask(quiet, { idle: false }), null);
    assert.strictEqual(L.parkTask(quiet, { idle: true }), null);
    assert.strictEqual(S.homeHaulMineral(quiet), false);
    const small = body(quiet);
    assert.strictEqual(n(small, 'carry'), 6);
    assert.strictEqual(n(small, 'move'), 3);
    assert.strictEqual(cost(small), S.HAUL_LINK_E);
    const full = home({ term: { O: 125976, K: 175792, KO: 36 }, free: 400, energy: 15557 });
    assert.strictEqual(L.parkTask(full, { idle: false }), null, 'labs off: tight terminal is not a park');
    assert.strictEqual(L.parkTask(full, { idle: true }), null);
    assert.strictEqual(S.homeHaulMineral(full), false);
    const b = body(full);
    assert.strictEqual(n(b, 'carry'), 6);
    assert.strictEqual(n(b, 'move'), 3);
    assert.strictEqual(cost(b), 450);
    assert.ok(!Memory.ops.labs, 'reading a full terminal does not set labs');
  }],
  ['labs off, below link era: storage hauler stays 14C7M from the 1050 cap', () => {
    labs(false);
    const rm = home();
    const e = S.bodyEnergy('hauler', 300, 1700, 300, true, true);
    assert.strictEqual(e, 1050);
    const b = S.homeHaulerBody(rm, e, 5, 1, 1700);
    assert.strictEqual(n(b, 'carry'), 14);
    assert.strictEqual(n(b, 'move'), 7);
    assert.strictEqual(cost(b), 1050);
  }],
  ['mineral body never exceeds the room energy cap', () => {
    labs(true);
    const b = body(home(), 7, 3, 900);
    assert.strictEqual(n(b, 'carry'), 12);
    assert.strictEqual(n(b, 'move'), 6);
    assert.ok(cost(b) <= 900);
    assert.notStrictEqual(n(b, 'carry'), 16);
  }],
  ['W46N8 labs do not enlarge another room', () => {
    labs(true);
    const w47 = home({ name: 'W47N8', term: { O: 125976, K: 175792, KO: 36 }, free: 400, energy: 20000 });
    assert.strictEqual(L.cfg(w47), null);
    assert.strictEqual(L.parkTask(w47, { idle: false }), null);
    assert.strictEqual(S.homeHaulMineral(w47), false);
    const b = body(w47);
    assert.strictEqual(n(b, 'carry'), 6);
    assert.strictEqual(n(b, 'move'), 3);
    assert.deepStrictEqual(Memory.ops.labs, { W46N8: 'KO' });
  }],
  ['no terminal: labs flag does not select the mineral body', () => {
    labs(true);
    const rm = home({ terminal: null });
    assert.strictEqual(S.homeHaulMineral(rm), false);
    const b = body(rm);
    assert.strictEqual(n(b, 'carry'), 6);
    assert.strictEqual(n(b, 'move'), 3);
  }],
  ['remote and off-road hauler recipes are unchanged; one hauler role in the queue', () => {
    const off = S.B.hauler(800);
    assert.strictEqual(n(off, 'carry'), 8);
    assert.strictEqual(n(off, 'move'), 8);
    const paved = S.B.roadHauler(1200, 16);
    assert.strictEqual(n(paved, 'carry'), 16);
    assert.strictEqual(n(paved, 'move'), 8);
    const order = S.spawnOrder({ hauler: 0, upgrader: 2 }, { hauler: 1, upgrader: 2 }, 0);
    assert.strictEqual(order.filter(r => r === 'hauler').length, 1);
  }],
];
let fail = 0;
for (const [name, fn] of cases) {
  try { fn(); console.log('ok  ', name); }
  catch (e) { fail++; console.log('FAIL', name, e.message); }
}
console.log(`spawn hauler body: ${cases.length - fail}/${cases.length}`);
process.exit(fail ? 1 : 0);
