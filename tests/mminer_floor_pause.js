// mminer must not recycle on the defence-floor pause (walls.defLow), only on a real stop. node tests/mminer_floor_pause.js
const path = require('path'), assert = require('assert'), src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, { RESOURCE_ENERGY: 'energy', STRUCTURE_EXTRACTOR: 'extractor', LOOK_STRUCTURES: 'structure', FIND_MINERALS: 116, _: require('lodash') });
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
let low = false, moved = [];
stub('utils/cmd.js', { yieldCreep: () => false });
stub('utils/move.js', { to: (c, x, y) => { moved.push([x, y]); return false; } });
stub('managers/walls.js', { defLow: () => low });
const M = require(src('roles/mminer.js'));
const sp = { pos: { roomName: 'W46N8', x: 35, y: 28 }, rec: 0, recycleCreep() { this.rec++; } };
const room = { name: 'W46N8', memory: { roleTargets: { mminer: 0 } } };
global.Game = { rooms: { W46N8: room }, spawns: { s1: sp }, getObjectById: () => null };
const creep = () => ({ memory: { home: 'W46N8' }, room, pos: { isNearTo: () => true, findInRange: () => [] }, harvest() {} });
low = true; M.run(creep()); assert.strictEqual(sp.rec, 0, 'floor pause: keep the paid body, no recycle');
assert.deepStrictEqual(moved, [[41, 24]], 'floor pause: still walks to the mineral tile');
low = false; M.run(creep()); assert.strictEqual(sp.rec, 1, 'real stop (target 0 above floor): recycle');
room.memory.roleTargets.mminer = 1; M.run(creep()); assert.strictEqual(sp.rec, 1, 'target 1: work');
console.log('mminer floor pause ok');
