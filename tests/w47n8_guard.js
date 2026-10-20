// 10-20 15:25 (Misaki): W47N8 melee gate guard: body, catchable, guardPlan, planner melee option
const assert = require('assert'), path = require('path');
Object.assign(global, { _: require('lodash'), WORK: 'work', CARRY: 'carry', MOVE: 'move', CLAIM: 'claim', ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack', HEAL: 'heal', TOUGH: 'tough',
  BODYPART_COST: { work: 100, carry: 50, move: 50, attack: 80, tough: 10, ranged_attack: 150, heal: 250 }, FIND_HOSTILE_CREEPS: 2, Memory: { ops: {} }, Game: { time: 5000, rooms: {}, creeps: {} } });
const D = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'defense.js'));
const W = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'index.js'));
const cnt = b => require('lodash').countBy(b), cost = b => b.reduce((s, p) => s + BODYPART_COST[p], 0);
assert.deepStrictEqual(cnt(D.meleeBody(1800)), { tough: 2, attack: 16, move: 9 });
assert.deepStrictEqual(cnt(W.bodyFor('w8guard', 1800)), { tough: 2, attack: 16, move: 9 });
for (const e of [300, 550, 1300, 1800, 5600]) { const b = D.meleeBody(e); assert.ok(cost(b) <= e && b.length <= 50, 'fits ' + e);
  assert.ok(2 * b.filter(p => p === 'move').length >= b.length - b.filter(p => p === 'move').length, 'full speed on road ' + e); }
const fc = D.fromCounts;
const kiter = fc({ ranged_attack: 8, move: 8 }), mel = fc({ tough: 4, attack: 8, move: 12 }), dis = fc({ work: 10, move: 10 }), slow = fc({ ranged_attack: 10, move: 3 }), dec = fc({ tough: 20, move: 5 });
assert.ok(!D.catchable(kiter) && D.catchable(mel) && D.catchable(dis) && D.catchable(slow) && !D.catchable(dec));
const P = (pos, b, id) => Object.assign({ id: id || 'h' + pos.x + pos.y, pos, hits: b.hits }, b);
const me = { pos: { x: 29, y: 4 }, hits: 2700, hitsMax: 2700 }, T = { towers: [{ x: 24, y: 8 }] };
// quiet -> hold 29,4; hostiles near -> gate
assert.strictEqual(D.guardPlan(me, [], T).move, 'hold');
assert.deepStrictEqual(D.guardPlan(me, [P({ x: 20, y: 1 }, kiter)], T).goal, D.GATE);
// kiter by the gate: no sally, stays on gate
const onGate = Object.assign({}, me, { pos: { x: 29, y: 3 } });
assert.strictEqual(D.guardPlan(onGate, [P({ x: 30, y: 0 }, kiter)], T).move, 'hold');
// dismantler near gate: sally; adjacent: hit it
assert.strictEqual(D.guardPlan(onGate, [P({ x: 32, y: 2 }, dis)], T).move, 'sally');
const a = D.guardPlan(onGate, [P({ x: 30, y: 2 }, dis, 'd')], T); assert.strictEqual(a.hit.id, 'd'); assert.strictEqual(a.move, 'hold');
// no sally into a covering heavy kiter
assert.notStrictEqual(D.guardPlan(onGate, [P({ x: 32, y: 2 }, dis), P({ x: 33, y: 0 }, kiter)], T).move, 'sally');
// TOUGH-only decoy ignored
assert.strictEqual(D.guardPlan(onGate, [P({ x: 30, y: 2 }, dec)], T).hit, null);
// HP rule
assert.strictEqual(D.guardPlan(Object.assign({}, me, { hits: 1500 }), [P({ x: 30, y: 2 }, mel)], T).move, 'retreat');
assert.strictEqual(D.guardPlan(Object.assign({}, me, { hits: 2300, hurt: true }), [P({ x: 30, y: 2 }, mel)], T).move, 'retreat');
// priority: healer over melee when both adjacent
const hl = fc({ heal: 6, move: 6 }); const pr = D.guardPlan(onGate, [P({ x: 30, y: 2 }, mel, 'm'), P({ x: 28, y: 2 }, hl, 'h')], T); assert.strictEqual(pr.hit.id, 'h');
// planner: vs pure kiters melee adds nothing -> never picks melee; vs melee/dismantler squad melee may be picked
const base = { towerR: [8, 32], inside: false, homeOk: true, homeCap: 2300, w8Cap: 1800 };
const pk = D.plan(Object.assign({ force: [kiter, fc({ ranged_attack: 8, move: 8, heal: 1 }), fc({ ranged_attack: 8, move: 8, heal: 1 })] }, base));
assert.strictEqual(pk.w8m, 0, 'kiters: no melee');
const brk = [fc({ tough: 4, attack: 8, move: 12 }), fc({ tough: 4, attack: 8, move: 12 }), fc({ heal: 7, move: 7 }), fc({ heal: 6, move: 6 }), fc({ work: 15, move: 15 })];
const pm = D.plan(Object.assign({ force: brk }, base)); console.log('breach squad plan', JSON.stringify(pm));
// sim: guard DPS counted only vs catchable
const s0 = D.sim([dis], [40], [D.raBody(1800, 12)], 0, {}), s1 = D.sim([dis], [40], [D.meleeBody(1800)], 0, {});
assert.ok(s1.ticks < s0.ticks, 'guard kills a dismantler faster ' + s1.ticks + ' vs ' + s0.ticks);
console.log('dismantler kill ticks ranged', s0.ticks, 'guard', s1.ticks, 'w8guard ok');
