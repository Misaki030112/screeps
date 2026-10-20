// 10-20 23:4x strategy review: border pre-assessment scores the seal segment nearest the announced W47N9 group (Memory.ops.w8invNx).
// Old code always used the east seal 27,3 (towers 33,35 r32 + 24,8 r5 = 750 dps). At the west seal x 8-11 tower 24,8 is r13-16,
// so a group with ~36 HEAL that the east seal holds needs 2 local defenders on the west side.
const assert = require('assert'), path = require('path');
Object.assign(global, { _: require('lodash'), FIND_MY_STRUCTURES: 10, FIND_HOSTILE_CREEPS: 3, STRUCTURE_EXTENSION: 'extension', STRUCTURE_SPAWN: 'spawn', WORK: 'work', CARRY: 'carry', MOVE: 'move', CLAIM: 'claim',
  BODYPART_COST: { work: 100, carry: 50, move: 50 }, FIND_MY_CONSTRUCTION_SITES: 1, FIND_MY_SPAWNS: 2, FIND_MY_CREEPS: 3, RANGED_ATTACK: 'ranged_attack', FIND_DROPPED_RESOURCES: 4, FIND_STRUCTURES: 5, RESOURCE_ENERGY: 'energy', STRUCTURE_CONTAINER: 'container', Game: { time: 5, creeps: {}, rooms: {} }, Memory: {} });
const W = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'index.js'));
const D = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'defense.js'));
assert.deepStrictEqual(W.sealAt(10), { x: 10, y: 3 });
assert.deepStrictEqual(W.sealAt(17), { x: 10, y: 3 });
assert.deepStrictEqual(W.sealAt(27), { x: 27, y: 3 });
assert.deepStrictEqual(W.sealAt(undefined), { x: 27, y: 3 }, 'no x -> east seal (old behaviour)');
const rng = (t, p) => Math.max(Math.abs(t[0] - p.x), Math.abs(t[1] - p.y)), TW = [[33, 35], [24, 8]];
const trE = TW.map(t => rng(t, W.sealAt(27))), trW = TW.map(t => rng(t, W.sealAt(10)));
assert.deepStrictEqual(trE, [32, 5]); assert.deepStrictEqual(trW, [32, 14]);
// BustJetter's 21:45 W48N9 group + 3 more 4H healers (40 HEAL)
const B = [{ tough: 5, move: 15, attack: 10 }, { tough: 4, move: 12, attack: 8 }, { tough: 6, move: 18, attack: 12 }, { ranged_attack: 6, move: 6 }, { ranged_attack: 6, move: 6 }, { ranged_attack: 6, move: 6 }]
  .concat([4, 4, 4, 5, 6, 5, 4, 4, 4].map(h => ({ heal: h, move: h }))).map(D.fromCounts);
const plan = tr => D.plan({ force: B, towerR: tr, inside: false, homeOk: false, homeCap: 0, w8Cap: 1800, towerE: 1000, atkBoost: '', meleeUptime: 0 });
const pe = plan(trE), pw = plan(trW);
assert.strictEqual(pe.w8, 0, 'east seal: towers alone hold -> no local defenders ' + JSON.stringify(pe));
assert.ok(pw.w8 > 0 || pw.advise, 'west seal: towers alone lose -> defenders (or safe-mode advice) ' + JSON.stringify(pw));
console.log('w47n8 seal west ok', JSON.stringify({ east: pe, west: pw }));
