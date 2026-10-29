// Hauler labRun wires managers/labs.task (dormant without Memory.ops.labs). node tests/labs_hauler.js
const path = require('path'), assert = require('assert'), src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, {
  STRUCTURE_LAB: 'lab', STRUCTURE_CONTAINER: 'container', STRUCTURE_SPAWN: 'spawn',
  STRUCTURE_EXTENSION: 'extension', STRUCTURE_TOWER: 'tower', STRUCTURE_LINK: 'link',
  RESOURCE_ENERGY: 'energy', FIND_MY_STRUCTURES: 108, OK: 0, _: require('lodash'),
  Game: { time: 1, getObjectById: id => OBJS[id] || null },
  Memory: {},
});
const OBJS = {};
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
stub('utils/roomcache.js', { at: () => null, all: () => [], sites: () => [] });
stub('utils/move.js', { to: () => true });
stub('utils/salvage.js', {});
stub('utils/trace.js', { why() {} });
stub('managers/walls.js', { noUpgrade: () => false });
stub('managers/links.js', { roles: () => ({ hub: null, sources: [] }), SEND: 800 });
stub('utils/plan.js', { get: () => ({ pos: { mineralMiner: [41, 24], miners: [], storageDoor: [36, 29], controllerContainer: [30, 30], controllerDrop: [30, 30], upgraders: [], manager: [36, 30] }, any: {} }), key: (x, y) => x * 50 + y });

const lab = (id, x, y, store = {}) => {
  const o = { id, structureType: 'lab', store, cooldown: 0, pos: { x, y, getRangeTo: o2 => Math.max(Math.abs(o2.pos.x - x), Math.abs(o2.pos.y - y)) } };
  OBJS[id] = o; return o;
};
const term = { id: 't', store: { K: 500, O: 30000 }, pos: { x: 35, y: 31 } }; OBJS.t = term;
const labs = [lab('o', 34, 22), lab('a', 33, 21), lab('b', 35, 21)];
const room = {
  name: 'W46N8', terminal: term, storage: null,
  find: () => labs,
};
const H = require(src('roles/hauler.js'));
const creep = (store = {}) => {
  const s = Object.assign({}, store);
  s.getCapacity = () => 300;
  s.getFreeCapacity = () => 300 - Object.keys(store).reduce((a, k) => a + store[k], 0);
  return {
    memory: { home: 'W46N8' }, store: s, got: [],
    withdraw(src, r) { this.got.push(['w', src.id, r]); return 0; },
    transfer(dst, r) { this.got.push(['t', dst.id, r]); return 0; },
  };
};

assert.strictEqual(H.labRun(creep(), room), false, 'no ops.labs -> dormant');
Memory.ops = { labs: { W46N8: 'KO' } };
const c1 = creep();
assert.strictEqual(H.labRun(c1, room), true, 'loads K into input lab');
assert.deepStrictEqual(c1.got, [['w', 't', 'K']]);
const c2 = creep({ K: 100 });
assert.strictEqual(H.labRun(c2, room), true, 'delivers held K to lab a');
assert.ok(c2.got[0][0] === 't' && c2.got[0][1] === 'a' && c2.got[0][2] === 'K');
const gone = OBJS.a; delete OBJS.a;
const cMiss = creep({ K: 100 });
assert.strictEqual(H.labRun(cMiss, room), true, 'missing lab id still runs');
assert.deepStrictEqual(cMiss.got, [['t', term.id, 'K']], 'held K aimed at a missing lab dumps to terminal');
OBJS.a = gone;
const c3 = creep({ energy: 50 });
assert.strictEqual(H.labRun(c3, room), false, 'carrying energy: skip');
console.log('labs hauler ok');
