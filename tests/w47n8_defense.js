// 14:46 border ranged defenders: trigger only on an invasion move; kite body; never leaves W47N8 / never north of the seal
const assert = require('assert'), path = require('path');
Object.assign(global, { _: require('lodash'), WORK: 'work', CARRY: 'carry', MOVE: 'move', CLAIM: 'claim', ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack', HEAL: 'heal', TOUGH: 'tough',
  BODYPART_COST: { work: 100, carry: 50, move: 50, ranged_attack: 150, heal: 250 }, FIND_HOSTILE_CREEPS: 2, Memory: { ops: {} }, Game: { time: 5000, rooms: {}, creeps: {} } });
const W = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'index.js'));
const TH = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'threat.js'));
const cost = b => b.reduce((s, p) => s + BODYPART_COST[p], 0);
for (const e of [300, 800, 1099, 1100, 1300, 5600]) { const b = W.bodyFor('w8defender', e); assert.ok(cost(b) <= e && b.length <= 50, 'fits ' + e);
  assert.strictEqual(b.filter(p => p === 'move').length, b.length - b.filter(p => p === 'move').length, 'MOVE = non-MOVE (kites at full speed) @' + e);
  assert.strictEqual(b.includes('heal'), e >= 1100, 'heal only when energy allows @' + e); }
const R = (hs, name = 'W47N8') => ({ name, find: () => hs });
const body = o => Object.entries(o).flatMap(([t, n]) => Array(n).fill({ type: t, hits: 100 }));
assert.strictEqual(TH.invasion(), false, 'quiet');
TH.mark(R([{ pos: { y: 1 }, body: body({ tough: 14, move: 14 }) }, { pos: { y: 1 }, body: body({ heal: 7, move: 7 }) }])); assert.strictEqual(TH.invasion(), false, 'drain tanks/healers are not an invasion move');
TH.mark(R([{ pos: { y: 20 }, body: body({ ranged_attack: 5, move: 5 }) }], 'W47N7')); assert.strictEqual(TH.invasion(), false, 'armed in W47N7 is not W47N8');
TH.mark(R([{ my: true, pos: { y: 20 }, body: body({ ranged_attack: 5, move: 5 }) }])); assert.strictEqual(TH.invasion(), false, 'own creeps never count');
TH.mark(R([{ pos: { y: 1 }, body: body({ attack: 10, move: 10 }) }])); assert.strictEqual(TH.invasion(), true, 'armed hostile entering W47N8');
Game.time += 50; assert.strictEqual(TH.invasion(), false, 'clears 50 ticks after');
Memory.ops.w8invN = Game.time; assert.strictEqual(TH.invasion(), true, 'north watch: armed group at the W47N9 border');
Game.time += 300; assert.strictEqual(TH.invasion(), false, 'border signal expires after 300');
// role never leaves the room: the cost callback blocks y<=3 (north of the seal) and all exit tiles
const src = require('fs').readFileSync(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'roles.js'), 'utf8');
assert.ok(/w8defender\(c\) \{\s*if \(!home\(c\)\) return;/.test(src) && /for \(let y = 0; y <= 3; y\+\+\) m\.set\(i, y, 255\)/.test(src), 'home() + seal/exit block present');
console.log('w47n8 defense ok');
