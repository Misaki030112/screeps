// RCL6 mineral line: hauler mineralRun + mminer gating. node tests/mineral_line.js
const path = require('path'), assert = require('assert'), src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, { STRUCTURE_SPAWN: 'spawn', STRUCTURE_EXTENSION: 'extension', STRUCTURE_TOWER: 'tower', RESOURCE_ENERGY: 'energy', STRUCTURE_CONTAINER: 'container', STRUCTURE_EXTRACTOR: 'extractor', LOOK_STRUCTURES: 'structure', FIND_MINERALS: 116, _: require('lodash'), Game: { time: 1, getObjectById: () => null } });
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
let K = null; stub('utils/roomcache.js', { at: () => K, all: () => [], sites: () => [] });
stub('utils/move.js', { to: () => true }); stub('utils/salvage.js', {}); stub('utils/trace.js', { why() {} });
const H = require(src('roles/hauler.js')), plan = require(src('utils/plan.js')), P = plan.get('W46N8');
const term = { id: 't', pos: { x: 35, y: 31 } };
const creep = (store = {}) => { const st = Object.assign({}, store); st.getCapacity = () => 300; return { memory: { home: 'W46N8' }, store: st, got: [], withdraw(k, r) { this.got.push(['w', r]); return 0; }, transfer(d, r) { this.got.push(['t', r]); return 0; } }; };
const room = { name: 'W46N8', terminal: term, storage: null };
const cont = o => { const s = Object.assign({}, o); s.getFreeCapacity = () => 2000 - Object.values(o).reduce((a, b) => a + b, 0); return { store: s }; };
let c = creep(); K = cont({ O: 200 }); assert.strictEqual(H.mineralRun(c, room, P), false, 'small pile waits');
K = cont({ O: 400 }); assert.strictEqual(H.mineralRun(c, room, P), true); assert.deepStrictEqual(c.got, [['w', 'O']], '>= carry capacity -> withdraw');
c = creep({ O: 300 }); assert.strictEqual(H.mineralRun(c, room, P), true); assert.deepStrictEqual(c.got, [['t', 'O']], 'deliver to terminal');
c = creep({ energy: 50 }); K = cont({ O: 1900 }); assert.strictEqual(H.mineralRun(c, room, P), false, 'carrying energy: normal job');
assert.deepStrictEqual(P.pos.mineralMiner, [41, 24]);
console.log('mineral line ok');
