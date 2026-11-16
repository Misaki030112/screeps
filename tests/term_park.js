// Home terminal park: surplus O, then K, then KO into storage. Leaves ACT_*_BUF.
// Does not withdraw energy and does not run while storage is under the 15k floor.
// node tests/term_park.js
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, {
  RESOURCE_ENERGY: 'energy', STRUCTURE_LAB: 'lab', STRUCTURE_SPAWN: 'spawn',
  STRUCTURE_EXTENSION: 'extension', STRUCTURE_TOWER: 'tower', STRUCTURE_CONTAINER: 'container',
  STRUCTURE_LINK: 'link', OK: 0,
  Game: { time: 1, getObjectById: id => OBJS[id] || null, creeps: {} },
  Memory: { ops: {}, defense: { reserveE: 15000 } },
});
const OBJS = {};
const L = require(src('managers/labs.js'));

function term(store, free) {
  const o = { id: 't', store: Object.assign({}, store), storeCapacity: 300000, pos: { x: 10, y: 10 } };
  o.store.getFreeCapacity = () => free;
  OBJS.t = o;
  return o;
}
function stor(store, free) {
  const o = { id: 's', store: Object.assign({ energy: 20000 }, store), pos: { x: 12, y: 12 } };
  o.store.getFreeCapacity = () => free == null ? 900000 : free;
  OBJS.s = o;
  return o;
}
function roomOf(t, s) {
  return { name: 'W46N8', terminal: t, storage: s };
}

assert.strictEqual(L.TERM_FREE_TARGET, 6000);
assert.strictEqual(L.parkTask(roomOf(term({ O: 10000, K: 10000 }, 0), stor())), null, 'labs flag off: no park');

Memory.ops.labs = { W46N8: 'KO' };
{
  const t = L.parkTask(roomOf(term({ O: 126976, K: 172792, KO: 36, energy: 0 }, 0), stor()), { idle: false });
  assert.strictEqual(t.res, 'O', 'surplus O first');
  assert.strictEqual(t.amt, 126976 - 3000);
  assert.strictEqual(t.from, 't');
  assert.strictEqual(t.to, 's');
  assert.notStrictEqual(t.res, 'energy');
}
{
  const t = L.parkTask(roomOf(term({ O: 3000, K: 172792, KO: 36 }, 0), stor()), { idle: false });
  assert.strictEqual(t.res, 'K', 'then excess K');
  assert.strictEqual(t.amt, 172792 - 3000);
  assert.ok(t.amt > 0 && t.from === 't' && t.to === 's');
}
{
  const t = L.parkTask(roomOf(term({ O: 3000, K: 3000, KO: 36 }, 0), stor()), { idle: false });
  assert.strictEqual(t.res, 'KO');
  assert.strictEqual(t.amt, 36);
  assert.strictEqual(t.to, 's');
}
assert.strictEqual(L.parkTask(roomOf(term({ O: 3000, K: 3000, KO: 0 }, 0), stor()), { idle: false }), null, 'buffers stay in the terminal');
assert.strictEqual(L.parkTask(roomOf(term({ O: 126976, K: 172792, KO: 36 }, 6000), stor()), { idle: false }), null, '6000 free is enough for a dump plus a send');
{
  const t = L.parkTask(roomOf(term({ O: 126976, K: 4000, KO: 0 }, 20000), stor({ O: 0 })), { idle: true });
  assert.strictEqual(t.res, 'O', 'idle keeps draining surplus once the terminal is not tight');
  assert.strictEqual(t.amt, 126976 - 3000);
}
{
  const t = L.parkTask(roomOf(term({ O: 2000, K: 3000, KO: 0 }, 20000), stor({ O: 8000 })), { idle: true });
  assert.strictEqual(t.res, 'O');
  assert.strictEqual(t.from, 's', 'storage puts O back up to the terminal buffer');
  assert.strictEqual(t.to, 't');
  assert.strictEqual(t.amt, 1000);
}
assert.strictEqual(L.parkTask(roomOf(term({ O: 1000, K: 3000 }, 0), stor({ O: 0 })), { idle: false }), null, 'tight terminal does not refill');
assert.strictEqual(Memory.ops.labs.W46N8, 'KO', 'park does not write the labs flag');

const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
stub('utils/roomcache.js', { at: () => null, all: () => [], sites: () => [] });
stub('utils/move.js', { to: () => true });
stub('utils/salvage.js', { dump: () => false, retire: () => false, pick: () => null, take: () => {} });
stub('utils/trace.js', { why() {} });
stub('managers/walls.js', { noUpgrade: () => false, defLow: () => false });
stub('managers/links.js', { roles: () => ({ hub: null, sources: [] }), SEND: 800 });
stub('utils/plan.js', { get: () => ({ pos: { mineralMiner: [41, 24], miners: [], storageDoor: [36, 29], controllerContainer: [30, 30], controllerDrop: [30, 30], upgraders: [], manager: [36, 30], fillers: [], fillerContainerA: [35, 24] }, any: {} }), key: (x, y) => x * 50 + y });
stub('roles/queen.js', { storageFloor: () => 15000, fillRoute: () => false });
const H = require(src('roles/hauler.js'));

function creep(store, mem, cap = 300) {
  const s = Object.assign({}, store);
  s.getCapacity = () => cap;
  s.getFreeCapacity = () => {
    let used = 0;
    for (const k in s) if (typeof s[k] === 'number') used += s[k];
    return Math.max(0, cap - used);
  };
  return {
    memory: Object.assign({ home: 'W46N8' }, mem), store: s, got: [],
    withdraw(src, r, amt) {
      assert.ok(amt > 0 && amt <= s.getFreeCapacity(), 'withdraw ' + amt + ' exceeds free ' + s.getFreeCapacity());
      assert.ok(amt <= ((src.store && src.store[r]) || 0), 'withdraw ' + amt + ' exceeds source');
      this.got.push(['w', src.id, r, amt]);
      s[r] = (s[r] || 0) + amt;
      if (src.store && typeof src.store[r] === 'number') src.store[r] -= amt;
      return 0;
    },
    transfer(dst, r) {
      const n = s[r] || 0;
      this.got.push(['t', dst.id, r, n]);
      if (dst.store) dst.store[r] = (dst.store[r] || 0) + n;
      s[r] = 0;
      return 0;
    },
  };
}
{
  const t = term({ O: 9000, K: 3000, KO: 0, energy: 0 }, 0);
  const s = stor({ energy: 14000 });
  const c = creep({});
  assert.strictEqual(H.termPark(c, roomOf(t, s), false), false, 'under the 15k floor the hauler does not park');
  assert.deepStrictEqual(c.got, []);
}
{
  const t = term({ O: 9000, K: 8000, KO: 10, energy: 0 }, 0);
  const s = stor({ energy: 20000 });
  const c = creep({});
  assert.strictEqual(H.termPark(c, roomOf(t, s), false), true);
  assert.deepStrictEqual(c.got, [['w', 't', 'O', 300]], '300 carry takes 300 of a 6000 O surplus');
  assert.ok(c.got.every(g => g[0] !== 'w' || g[3] <= 300));
  assert.strictEqual(H.termPark(c, roomOf(t, s), false), true, 'delivers that load before withdrawing again');
  assert.strictEqual(c.got[1][0], 't');
  assert.strictEqual(c.got[1][1], 's');
  assert.strictEqual(c.got[1][2], 'O');
  assert.strictEqual(c.store.O || 0, 0);
  const carry = creep({ O: 300 }, { tp: 1, tpFrom: 't', tpTo: 's', tpRes: 'O', tpAmt: 6000 });
  assert.strictEqual(H.termPark(carry, roomOf(t, s), false), true);
  assert.strictEqual(carry.got[0][0], 't');
  assert.strictEqual(carry.got[0][2], 'O', 'delivers the mineral to storage');
  assert.ok(!carry.got.some(g => g[2] === 'energy'));
}
{
  const t = term({ O: 126976, K: 172792, KO: 36, energy: 0 }, 0);
  const s = stor({ energy: 20000 });
  const c = creep({});
  const rm = roomOf(t, s);
  assert.strictEqual(H.termPark(c, rm, false), true);
  assert.deepStrictEqual(c.got, [['w', 't', 'O', 300]], '123976 O surplus is taken 300 at a time');
  assert.strictEqual(H.termPark(c, rm, false), true);
  assert.strictEqual(c.store.O || 0, 0);
  c.got = [];
  assert.strictEqual(H.termPark(c, rm, false), true, 'second trip');
  assert.deepStrictEqual(c.got, [['w', 't', 'O', 300]]);
  assert.ok(!c.got.some(g => g[2] === 'energy' || g[2] === 'K' || g[2] === 'KO'));
}
console.log('term park ok');
