// Home RCL8 independent plan (2026-11-26 Misaki t514u/t516u): managers/rcl8.js gates, labs product cap, standing boost lab.
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, { RESOURCE_ENERGY: 'energy', RANGED_ATTACK: 'ranged_attack', ATTACK: 'attack', STRUCTURE_LAB: 'lab', FIND_MY_STRUCTURES: 108, OK: 0,
  Game: { time: 1000, creeps: {}, getObjectById: id => OBJ[id] || null }, Memory: { ops: { labs: { W46N8: 'KO' } } } });
const OBJ = {};
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
let BUSY = false;
stub('managers/home.js', { active: () => BUSY });
stub('utils/move.js', { to: () => true });
const R8 = require(src('managers/rcl8.js')), L = require(src('managers/labs.js')), B = require(src('managers/boost.js'));
const room = (lvl, e) => ({ name: 'W46N8', memory: {}, controller: { level: lvl }, storage: { store: { energy: e } } });
const cases = [];
const t = (n, f) => cases.push([n, f]);
t('RCL7: nothing deferred, ramp target unchanged', () => { const r = room(7, 0); assert.strictEqual(R8.deferSite(r, { structureType: 'nuker' }), false); assert.strictEqual(R8.rampTarget(r, 1e6), 1e6); });
t('RCL8, storage 10k: power spawn + nuker deferred, observer/extension not', () => { const r = room(8, 10000);
  assert.strictEqual(R8.deferSite(r, { structureType: 'powerSpawn' }), true); assert.strictEqual(R8.deferSite(r, { structureType: 'nuker' }), true);
  assert.strictEqual(R8.deferSite(r, { structureType: 'observer' }), false); assert.strictEqual(R8.deferSite(r, { structureType: 'extension' }), false); });
t('RCL8 optional sites: open at 40k, stay open to 20k, close below', () => { const r = room(8, 40000), s = { structureType: 'nuker' };
  assert.strictEqual(R8.deferSite(r, s), false); r.storage.store.energy = 21000; assert.strictEqual(R8.deferSite(r, s), false);
  r.storage.store.energy = 19999; assert.strictEqual(R8.deferSite(r, s), true); r.storage.store.energy = 39000; assert.strictEqual(R8.deferSite(r, s), true); });
t('RCL8 rampart cap: 1M until storage 60k, 3M until it drops under 40k', () => { const r = room(8, 30000);
  assert.strictEqual(R8.rampTarget(r, 3e6), 1e6); r.storage.store.energy = 60000; assert.strictEqual(R8.rampTarget(r, 3e6), 3e6);
  r.storage.store.energy = 41000; assert.strictEqual(R8.rampTarget(r, 3e6), 3e6); r.storage.store.energy = 39000; assert.strictEqual(R8.rampTarget(r, 3e6), 1e6); });
// labs
const lab = (id, x, y, store) => (OBJ[id] = { id, structureType: 'lab', store: Object.assign({}, store), cooldown: 0, pos: { x, y, getRangeTo(o) { return Math.max(Math.abs(o.pos.x - x), Math.abs(o.pos.y - y)); } }, runReaction() { this.r = (this.r || 0) + 1; return 0; } });
function home(labs, term, stor) { OBJ.t = { id: 't', store: Object.assign({}, term), pos: { x: 35, y: 31 } }; OBJ.s = { id: 's', store: Object.assign({}, stor), pos: { x: 37, y: 31 } };
  return { name: 'W46N8', terminal: OBJ.t, storage: OBJ.s, memory: {}, find: () => labs }; }
const six = () => [lab('A', 34, 22), lab('C', 33, 21, { K: 1000 }), lab('B', 35, 21), lab('F', 34, 20), lab('E', 33, 22, { O: 1000 }), lab('D', 34, 23)];
t('labs: KO stock >= 60k -> no reaction, no input loads', () => { const labs = six(), ro = L.roles(labs); ro.ins[0].store = { K: 1000 }; ro.ins[1].store = { O: 1000 };
  const r = home(labs, { K: 3000, O: 3000 }, { KO: 95000, energy: 5000 }); Game.creeps = {};
  assert.strictEqual(L.run(r), 0); assert.ok(!ro.out.r, 'runReaction not called'); ro.ins[0].store = { K: 10 };
  assert.strictEqual(L.task(r, labs), null, 'no K load while capped'); });
t('labs: KO stock 50k -> reaction runs', () => { const labs = six(), ro = L.roles(labs); ro.ins[0].store = { K: 1000 }; ro.ins[1].store = { O: 1000 };
  const r = home(labs, { K: 3000, O: 3000 }, { KO: 50000 }); Game.creeps = {}; assert.strictEqual(L.run(r), 1); });
t('labs: Memory.ops.labCap = 0 disables the cap', () => { Memory.ops.labCap = 0; const labs = six(), ro = L.roles(labs); ro.ins[0].store = { K: 1000 }; ro.ins[1].store = { O: 1000 };
  const r = home(labs, {}, { KO: 95000 }); Game.creeps = {}; assert.strictEqual(L.run(r), 1); delete Memory.ops.labCap; });
// standing boost lab
t('boost stock: empty free lab -> KO from the terminal up to 1500', () => { const labs = six(); const r = home(labs, { KO: 400 }, { KO: 90000, energy: 4000 }); Game.creeps = {};
  const j = B.stockTask(r); assert.strictEqual(j.res, 'KO'); assert.strictEqual(j.from, 't'); assert.strictEqual(j.amt, 400); });
t('boost stock: terminal dry -> KO from storage', () => { const labs = six(); const r = home(labs, {}, { KO: 90000, energy: 4000 }); const j = B.stockTask(r); assert.strictEqual(j.from, 's'); assert.strictEqual(j.amt, 1500); });
t('boost stock: KO full, energy 0, storage 4k (< 5k + 1000) -> nothing', () => { const labs = six(); const r = home(labs, {}, { KO: 90000, energy: 4000 });
  const pick = B.pickLab(r).lab; pick.store = { KO: 1500 }; assert.strictEqual(B.stockTask(r), null); });
t('boost stock: KO full, storage 9k -> 1000 energy', () => { const labs = six(); const r = home(labs, {}, { KO: 90000, energy: 9000 }); B.pickLab(r).lab.store = { KO: 1500 };
  const j = B.stockTask(r); assert.deepStrictEqual([j.res, j.amt, j.from], ['energy', 1000, 's']); });
t('boost stock: within RESTOCK -> no trip', () => { const labs = six(); const r = home(labs, {}, { KO: 90000, energy: 9000 }); B.pickLab(r).lab.store = { KO: 1300, energy: 800 }; assert.strictEqual(B.stockTask(r), null); });
t('boost stock: foreign mineral in the boost lab goes back to the terminal', () => { const labs = six(); const r = home(labs, {}, { KO: 90000 }); const l = B.pickLab(r).lab; l.store = { GO: 135 };
  const j = B.stockTask(r); assert.deepStrictEqual([j.from, j.to, j.res, j.amt], [l.id, 't', 'GO', 135]); });
const kite = (r) => ({ name: 'd1', spawning: false, memory: { role: 'defender', home: 'W46N8' }, room: r, pos: { x: 35, y: 28 },
  body: Array.from({ length: 25 }, () => ({ type: 'ranged_attack', hits: 100 })).concat(Array.from({ length: 25 }, () => ({ type: 'move', hits: 100 }))) });
t('stocked lab: a fresh 25 RA kite boosts at once (750 KO, 500 energy)', () => { const labs = six(); const r = home(labs, {}, { KO: 90000, energy: 4000 }); const l = B.pickLab(r).lab;
  l.store = { KO: 1500, energy: 1000 }; l.boostCreep = c => { l.b = 1; return 0; }; const c = kite(r); Game.creeps = { d1: c };
  assert.strictEqual(B.plan(r, c).act, 'ready'); assert.strictEqual(B.hold(c), false); assert.strictEqual(l.b, 1); assert.strictEqual(c.memory.boosted, 1); });
t('lab short: waits at most 30 ticks, then leaves unboosted', () => { const labs = six(); const r = home(labs, { KO: 0 }, { KO: 90000, energy: 9000 }); const c = kite(r); Game.creeps = { d1: c };
  Game.time = 2000; assert.strictEqual(B.hold(c), true); Game.time = 2031; assert.strictEqual(B.hold(c), false); assert.strictEqual(c.memory.noBoost, 1); });
t('home in combat, lab not ready -> no wait', () => { BUSY = true; const labs = six(); const r = home(labs, {}, { KO: 90000, energy: 9000 }); const c = kite(r); Game.creeps = { d1: c };
  assert.strictEqual(B.hold(c), false); assert.strictEqual(c.memory.noBoost, 1); BUSY = false; });
let fail = 0; for (const [n, f] of cases) { try { f(); console.log('ok  ', n); } catch (e) { fail++; console.log('FAIL', n, e.message); } }
console.log(`rcl8 independent: ${cases.length - fail}/${cases.length}`); process.exit(fail ? 1 : 0);
