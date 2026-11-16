// Default KO boost for home kites. Core busters are skipped. Lab energy is not pulled from
// storage under 20k. The boost lab is not a KO reaction input/output unless reactions pause.
// node tests/boost.js
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, {
  WORK: 'work', CARRY: 'carry', MOVE: 'move', ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack',
  HEAL: 'heal', RESOURCE_ENERGY: 'energy',
  STRUCTURE_LAB: 'lab', STRUCTURE_SPAWN: 'spawn', STRUCTURE_EXTENSION: 'extension', STRUCTURE_TOWER: 'tower',
  FIND_MY_STRUCTURES: 108, OK: 0,
  Game: { time: 5, creeps: {}, getObjectById: id => OBJS[id] || null },
  Memory: { ops: { labs: { W46N8: 'KO' } }, defense: { reserveE: 15000 } },
});
const OBJS = {};
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
stub('utils/move.js', { to: () => true });
const B = require(src('managers/boost.js'));
const L = require(src('managers/labs.js'));

function lab(id, x, y, store) {
  const o = {
    id, structureType: 'lab', store: Object.assign({}, store), cooldown: 0, boosts: 0,
    pos: { x, y, getRangeTo(o2) { return Math.max(Math.abs(o2.pos.x - x), Math.abs(o2.pos.y - y)); } },
    boostCreep(c) { this.boosts++; c._boosted = (c._boosted || 0) + 1; return 0; },
    runReaction() { o.reacts = (o.reacts || 0) + 1; return 0; },
  };
  OBJS[id] = o;
  return o;
}
const HOME = [
  lab('A', 34, 22), lab('C', 33, 21), lab('B', 35, 21),
  lab('F', 34, 20), lab('E', 33, 22), lab('D', 34, 23),
];
function room(labs, term, stor) {
  const t = { id: 't', store: Object.assign({}, term), pos: { x: 11, y: 11 } };
  const s = { id: 's', store: Object.assign({ energy: 21000 }, stor), pos: { x: 12, y: 12 } };
  OBJS.t = t; OBJS.s = s;
  return {
    name: 'W46N8', terminal: t, storage: s, labs,
    find: () => labs,
  };
}
function body(n, type) { return Array.from({ length: n }, () => ({ type, hits: 100 })); }
function kiteBody() { return body(19, 'ranged_attack').concat(body(25, 'move'), body(6, 'heal')); }
function creep(role, parts, rn, mem) {
  const rm = room(HOME);
  const c = {
    name: role + '1', spawning: false, body: parts, _boosted: 0,
    memory: Object.assign({ role, home: rn || 'W46N8' }, mem),
    room: rn && rn !== 'W46N8' ? { name: rn, find: () => [] } : rm,
    pos: { x: 35, y: 28 },
  };
  if (c.room === rm) c.room = rm;
  return c;
}
function arm(c, labs) {
  Game.creeps = { [c.name]: c };
  c.room = room(labs || HOME, c.room.terminal && c.room.terminal.store, c.room.storage && c.room.storage.store);
  c.room.name = 'W46N8';
  return c.room;
}

const ro = L.roles(HOME);
assert.ok(ro, 'six home labs still resolve a reaction pair');
const free = HOME.filter(l => l !== ro.out && ro.ins.indexOf(l) < 0);
assert.ok(free.length >= 1, 'a lab is outside the reaction pair');

// Core buster is not boosted.
{
  const c = creep('defender', body(25, 'attack').concat(body(25, 'move')));
  const rm = arm(c);
  assert.strictEqual(B.isKite(c), false);
  assert.strictEqual(B.plan(rm, c).act, 'skip');
  assert.strictEqual(B.hold(c), false);
  assert.strictEqual(c.memory.noBoost, 1);
  assert.ok(HOME.every(l => l.boosts === 0), 'boostCreep not called');
}

// Melee w8guard is not a kite. A 25 RA w8defender is.
{
  const g = creep('w8guard', body(16, 'attack').concat(body(9, 'move')));
  assert.strictEqual(B.isKite(g), false);
  const d = creep('w8defender', body(25, 'ranged_attack').concat(body(25, 'move')));
  assert.strictEqual(B.isKite(d), true);
}

// Funded boost lab, storage under 20k: boost without pulling storage energy.
{
  for (const l of HOME) { l.store = {}; l.boosts = 0; }
  free[0].store = { KO: 900, energy: 400 };
  const c = creep('defender', kiteBody());
  const rm = arm(c);
  rm.storage.store.energy = 16700;
  const p = B.plan(rm, c);
  assert.strictEqual(p.act, 'ready', 'lab already holds KO and energy');
  assert.strictEqual(p.pick.lab.id, free[0].id);
  assert.strictEqual(p.pick.pause, false);
  assert.ok(ro.ins.indexOf(p.pick.lab) < 0 && p.pick.lab !== ro.out);
  assert.strictEqual(B.haulTask(rm), null, 'no storage withdraw when the lab is full');
  assert.strictEqual(B.hold(c), false);
  assert.strictEqual(c.memory.boosted, 1);
  assert.strictEqual(free[0].boosts, 1);
  assert.strictEqual(c._boosted, 1);
}

// KO present, lab energy missing, storage under 20k: skip, do not dip.
{
  for (const l of HOME) { l.store = {}; l.boosts = 0; }
  free[0].store = { KO: 900, energy: 0 };
  const c = creep('guard', kiteBody());
  const rm = arm(c);
  rm.storage.store.energy = 16700;
  rm.terminal.store = { KO: 0, energy: 0 };
  const p = B.plan(rm, c);
  assert.strictEqual(p.act, 'skip');
  assert.strictEqual(p.why, 'energy');
  assert.strictEqual(B.haulTask(rm), null);
  assert.strictEqual(B.hold(c), false);
  assert.strictEqual(c.memory.noBoost, 1);
  assert.strictEqual(free[0].boosts, 0);
}

// Storage 20300 can only spare 300, a max kite needs 380: skip rather than cross 20k.
{
  for (const l of HOME) { l.store = {}; l.boosts = 0; }
  free[0].store = { KO: 900, energy: 0 };
  const c = creep('defender', kiteBody());
  const rm = arm(c);
  rm.storage.store.energy = 20300;
  assert.strictEqual(B.plan(rm, c).why, 'energy');
  assert.strictEqual(B.haulTask(rm), null);
}

// Storage safely above 20k: hauler fills 380 energy, then the kite is boosted.
{
  for (const l of HOME) { l.store = {}; l.boosts = 0; }
  free[0].store = { KO: 900, energy: 0 };
  const c = creep('defender', kiteBody());
  delete c.memory.noBoost;
  const rm = arm(c);
  rm.storage.store.energy = 21000;
  assert.strictEqual(B.plan(rm, c).act, 'wait');
  const job = B.haulTask(rm);
  assert.strictEqual(job.res, 'energy');
  assert.strictEqual(job.amt, 380);
  assert.strictEqual(job.from, 's');
  assert.strictEqual(job.to, free[0].id);
  assert.ok(21000 - job.amt >= 20000);
  assert.ok(ro.ins.every(l => l.id !== job.to) && ro.out.id !== job.to);
  assert.strictEqual(B.hold(c), true, 'waits until the lab has energy');
  assert.strictEqual(free[0].boosts, 0);
  free[0].store.energy = 380;
  assert.strictEqual(B.plan(rm, c).act, 'ready');
  assert.strictEqual(B.hold(c), false);
  assert.strictEqual(c.memory.boosted, 1);
  assert.strictEqual(free[0].boosts, 1);
}

// Not enough KO: leave unboosted. KO in the terminal: wait and fill the boost lab, not an input.
{
  for (const l of HOME) { l.store = {}; l.boosts = 0; }
  const c = creep('defender', kiteBody());
  delete c.memory.boosted;
  const rm = arm(c);
  rm.storage.store = { energy: 21000 };
  rm.terminal.store = { KO: 100, energy: 0 };
  assert.strictEqual(B.plan(rm, c).why, 'ko');
  rm.terminal.store.KO = 900;
  assert.strictEqual(B.plan(rm, c).act, 'wait');
  const job = B.haulTask(rm);
  assert.strictEqual(job.res, 'KO');
  assert.strictEqual(job.amt, 900);
  assert.strictEqual(job.from, 't');
  assert.strictEqual(job.to, free[0].id);
  free[0].store = { KO: 900, energy: 400 };
  assert.strictEqual(B.hold(c), false);
  assert.strictEqual(free[0].boosts, 1);
}

// KO that has already landed in the reaction output is moved to the boost lab, not left there.
{
  for (const l of HOME) { l.store = {}; l.boosts = 0; }
  ro.out.store = { KO: 900 };
  const c = creep('defender', kiteBody());
  delete c.memory.boosted; delete c.memory.noBoost; delete c.memory.bl;
  const rm = arm(c);
  rm.storage.store = { energy: 21000 };
  rm.terminal.store = { energy: 400 };
  const job = B.haulTask(rm);
  assert.ok(job, 'output KO is a haul source');
  assert.strictEqual(job.res, 'KO');
  assert.strictEqual(job.from, ro.out.id);
  assert.strictEqual(job.to, free[0].id);
  assert.ok(ro.ins.every(l => l.id !== job.to));
}

// Away from home (W47 rdef / local w8defender): do not boost and do not walk back.
{
  const c = creep('defender', kiteBody(), 'W47N8');
  assert.strictEqual(B.plan(c.room, c).why, 'away');
  assert.strictEqual(B.hold(c), false);
  assert.strictEqual(c.memory.noBoost, 1);
}

// Only the reaction trio: boost uses the output and reactions pause while the kite waits.
{
  const trio = [lab('o', 34, 22, { energy: 0 }), lab('a', 33, 21, { K: 1000 }), lab('b', 35, 21, { O: 1000 })];
  const c = creep('defender', kiteBody());
  delete c.memory.boosted; delete c.memory.noBoost; delete c.memory.bl;
  Game.creeps = { [c.name]: c };
  const rm = room(trio, { K: 3000, O: 3000, KO: 900, energy: 0 }, { energy: 21000 });
  c.room = rm;
  const pick = B.pickLab(rm);
  assert.strictEqual(pick.pause, true);
  assert.strictEqual(pick.lab.id, L.roles(trio).out.id);
  assert.strictEqual(B.blocksReaction(rm), true);
  assert.strictEqual(L.run(rm), 0, 'reaction pauses while the output lab is the boost lab');
  assert.ok(!trio.some(l => l.reacts), 'runReaction not called');
}

// A free lab keeps the reaction running.
{
  for (const l of HOME) { l.store = {}; l.reacts = 0; l.boosts = 0; }
  HOME.forEach(l => { if (ro.ins.indexOf(l) >= 0) l.store = l === ro.ins[0] ? { K: 50 } : { O: 50 }; });
  Game.creeps = {};
  const rm = room(HOME, { K: 3000, O: 3000, KO: 0 }, { energy: 21000 });
  assert.strictEqual(B.blocksReaction(rm), false);
  assert.strictEqual(L.run(rm), 1);
  assert.ok(ro.out.reacts >= 1, 'reaction still runs on its own output');
}

stub('utils/roomcache.js', { at: () => null, all: () => [], sites: () => [] });
stub('utils/salvage.js', { dump: () => false, retire: () => false, pick: () => null });
stub('utils/trace.js', { why() {} });
stub('managers/walls.js', { noUpgrade: () => false, defLow: () => false });
stub('managers/links.js', { roles: () => ({ hub: null, sources: [] }), SEND: 800 });
stub('roles/queen.js', { storageFloor: () => 15000, fillRoute: () => false });
stub('utils/plan.js', { get: () => ({ pos: { mineralMiner: [41, 24], miners: [], storageDoor: [36, 29], controllerContainer: [30, 30], controllerDrop: [30, 30], upgraders: [], manager: [36, 30], fillers: [], fillerContainerA: [35, 24] }, any: {} }), key: (x, y) => x * 50 + y });
const H = require(src('roles/hauler.js'));
{
  for (const l of HOME) { l.store = {}; l.boosts = 0; }
  free[0].store = { KO: 900, energy: 0 };
  const c = creep('defender', kiteBody());
  delete c.memory.boosted; delete c.memory.noBoost; delete c.memory.bl;
  const rm = arm(c);
  rm.storage.store.energy = 16700;
  const hauler = {
    memory: { home: 'W46N8' }, store: {}, got: [],
    withdraw(s, r, amt) { this.got.push(['w', s.id, r, amt]); return 0; },
    transfer() { return 0; },
  };
  assert.strictEqual(H.boostHaul(hauler, rm), false, 'hauler does not pull storage energy under 20k');
  assert.deepStrictEqual(hauler.got, []);
  rm.storage.store.energy = 21000;
  delete c.memory.noBoost;
  const slow = hauler300();
  assert.strictEqual(H.boostHaul(slow, rm), true);
  assert.deepStrictEqual(slow.got, [['w', 's', 'energy', 300]], '380 energy is taken 300 at a time');
  assert.strictEqual(H.boostHaul(slow, rm), true, 'delivers the energy before the next withdraw');
  assert.strictEqual(slow.store.energy || 0, 0);
  assert.strictEqual(free[0].store.energy, 300);
  slow.got = [];
  assert.strictEqual(H.boostHaul(slow, rm), true, 'second trip finishes the 80');
  assert.deepStrictEqual(slow.got, [['w', 's', 'energy', 80]]);
  assert.ok(slow.got.every(g => g[0] !== 'w' || g[3] <= 300));
  // Assigned at 21000, storage fell to 20100 before the withdraw. 20100 - 380 is under 20k.
  const late = {
    memory: { home: 'W46N8', bk: 1, bkFrom: 's', bkTo: free[0].id, bkRes: 'energy', bkAmt: 380 },
    store: {}, got: [],
    withdraw(s, r, amt) { this.got.push(['w', s.id, r, amt]); return 0; },
    transfer() { return 0; },
  };
  rm.storage.store.energy = 20100;
  assert.strictEqual(H.boostHaul(late, rm), false, 'resume does not finish a withdraw that crosses 20k');
  assert.deepStrictEqual(late.got, []);
  assert.ok(!late.memory.bk);
}
{
  for (const l of HOME) { l.store = {}; l.boosts = 0; }
  free[0].store = { energy: 400 };
  const c = creep('defender', kiteBody());
  delete c.memory.boosted; delete c.memory.noBoost; delete c.memory.bl;
  const rm = arm(c);
  rm.storage.store = { energy: 21000 };
  rm.terminal.store = { KO: 900, energy: 0 };
  const h = hauler300();
  assert.strictEqual(H.boostHaul(h, rm), true);
  assert.deepStrictEqual(h.got, [['w', 't', 'KO', 300]], '900 KO is taken 300 at a time');
  assert.strictEqual(H.boostHaul(h, rm), true);
  assert.strictEqual(h.store.KO || 0, 0);
  assert.strictEqual(free[0].store.KO, 300);
  h.got = [];
  assert.strictEqual(H.boostHaul(h, rm), true, 'second KO trip');
  assert.deepStrictEqual(h.got, [['w', 't', 'KO', 300]]);
  assert.ok(h.got.every(g => g[0] !== 'w' || g[3] <= 300));
}
function hauler300(store, mem) {
  const s = Object.assign({}, store);
  const cap = 300;
  s.getCapacity = () => cap;
  s.getFreeCapacity = () => {
    let used = 0;
    for (const k in s) if (typeof s[k] === 'number') used += s[k];
    return Math.max(0, cap - used);
  };
  return {
    memory: Object.assign({ home: 'W46N8' }, mem), store: s, got: [],
    withdraw(src, r, amt) {
      assert.ok(amt > 0 && amt <= s.getFreeCapacity(), 'withdraw ' + amt + ' > free');
      assert.ok(amt <= ((src.store && src.store[r]) || 0));
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
console.log('boost ok');
