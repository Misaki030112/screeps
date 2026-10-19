// W47N8 defence doctrine (docs/DEFENSE_W47N8.md): border defender trigger/body, tower focus (healer > ranged > melee, net > 0, energy
// floor, drain tanks ignored), combat model vs BustJetter's squad, assessment gate (spawn only when it changes the outcome), defPlan.
const assert = require('assert'), path = require('path');
Object.assign(global, { _: require('lodash'), WORK: 'work', CARRY: 'carry', MOVE: 'move', CLAIM: 'claim', ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack', HEAL: 'heal', TOUGH: 'tough',
  BODYPART_COST: { work: 100, carry: 50, move: 50, ranged_attack: 150, heal: 250 }, FIND_HOSTILE_CREEPS: 2, Memory: { ops: {} }, Game: { time: 5000, rooms: {}, creeps: {} } });
const W = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'index.js'));
const TH = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'threat.js'));
const D = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'defense.js'));
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
// role never leaves the room: the cost callback blocks y<=3 (north of the seal) and all exit tiles; uses defPlan
const src = require('fs').readFileSync(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'roles.js'), 'utf8');
assert.ok(/w8defender\(c\) \{[\s\S]{0,400}if \(!home\(c\)\) return;/.test(src) && /for \(let y = 0; y <= 3; y\+\+\) m\.set\(i, y, 255\)/.test(src) && /D\.defPlan\(/.test(src), 'home() + seal/exit block + defPlan present');
// ---- tower focus (towerPick)
const c = (id, x, y, b, hits) => { const bd = body(b); return { id, pos: { x, y }, body: bd, hits: hits || bd.length * 100, hitsMax: bd.length * 100 }; };
const T1 = [{ pos: { x: 33, y: 35 }, energy: 890 }];
assert.strictEqual(D.towerPick(T1, [c('d', 27, 1, { tough: 14, move: 14 }), c('h', 28, 1, { heal: 7, move: 7 })]), null, 'drain tanks + healer north of the seal: hold fire');
assert.strictEqual(D.towerPick(T1, [c('d', 27, 1, { tough: 14, move: 14 })]), null, 'lone drain tank north of the seal: never shot (not hurting, not inside)');
assert.strictEqual(D.towerPick(T1, [c('r', 27, 1, { ranged_attack: 7, move: 7 })], { hurting: new Set(['r']) }).h.id, 'r', 'armed creep shooting our wall, out-damaged: fire');
assert.strictEqual(D.towerPick(T1, [c('r', 27, 1, { ranged_attack: 7, move: 7 }), c('h', 27, 0, { heal: 7, move: 7 }), c('g', 28, 0, { heal: 6, move: 6 })], { hurting: new Set(['r']) }), null, 'armed + 2 healers at the seal, tower 150 vs heal 156 -> net<=0, hold');
// in base: healer > ranged > melee, then fastest kill
let sq = [c('m', 30, 30, { attack: 10, move: 10 }), c('r', 31, 30, { ranged_attack: 7, move: 7 }), c('h', 31, 31, { heal: 6, move: 6 })];
assert.strictEqual(D.towerPick(T1, sq).h.id, 'h', 'healer first');
assert.strictEqual(D.towerPick(T1, sq.slice(0, 2)).h.id, 'r', 'ranged before melee');
assert.strictEqual(D.towerPick(T1, sq.slice(0, 1)).h.id, 'm', 'melee when alone');
// sticky prev when about to die, even if a healer is present
sq[0].hits = 300; assert.strictEqual(D.towerPick(T1, sq, { prev: 'm' }).h.id, 'm', 'finish the near-dead previous target');
// out-healed healer skipped -> next class with net>0
const ball = [c('h1', 20, 10, { heal: 7, move: 7 }), c('h2', 20, 11, { heal: 7, move: 7 }), c('h3', 21, 10, { heal: 6, move: 6 }), c('r', 21, 11, { ranged_attack: 11, move: 11 })];
assert.strictEqual(D.towerPick(T1, ball), null, 'tower r>=20 vs 240 heal: nothing killable -> hold fire (no drain)');
// energy floor: non-urgent target only from towers >= FLOOR; urgent (in-base armed / hurting / claim / dying) from all
const low = [{ pos: { x: 33, y: 35 }, energy: 300 }];
assert.strictEqual(D.towerPick(low, [c('t', 30, 20, { tough: 14, move: 14 })]), null, 'unarmed in base, tower 300 < FLOOR: keep energy');
assert.ok(D.towerPick(low, [c('a', 30, 20, { attack: 10, move: 10 })]), 'armed in base: fire below floor');
assert.ok(D.towerPick(low, [c('k', 30, 1, { claim: 1, move: 1 })]), 'claimer anywhere: fire');
// drain ban (focus.track): banned non-urgent target skipped
assert.strictEqual(D.towerPick(T1, [c('t', 30, 20, { tough: 14, move: 14 })], { banned: new Set(['t']) }), null, 'banned drain creep: hold');
// ---- combat model: BustJetter's W48N9 squad (2 RA, 2 melee, 3 healers, unboosted)
const fc = D.fromCounts, SQ = () => [fc({ ranged_attack: 11, move: 11 }), fc({ ranged_attack: 7, move: 7 }), fc({ tough: 5, move: 15, attack: 10 }), fc({ tough: 4, move: 12, attack: 8 }),
  fc({ heal: 6, move: 6 }), fc({ heal: 7, move: 7 }), fc({ heal: 6, move: 6 })];
const d4 = W.bodyFor('w8defender', 1300), d5 = W.bodyFor('w8defender', 1800);
assert.strictEqual(D.sim(SQ(), [32], d4, 2).result, 'lose', 'RCL4 seal: 1 tower + 2 defenders lose');
assert.strictEqual(D.sim(SQ(), [19], d4, 2).result, 'lose', 'RCL4 Spawn2: lose');
assert.strictEqual(D.sim(SQ(), [3], d4, 0).result, 'win', 'RCL4 core (tower r<=5): tower alone wins');
assert.strictEqual(D.sim(SQ(), [19, 19], d5, 0).result, 'win', 'RCL5 Spawn2: 2 towers win alone');
let a = D.assess(SQ(), [32], d4, { inside: false }); assert.ok(!a.spawn && a.why === 'unwinnable' && a.advise === '', 'full squad at the seal: no defenders (2600 energy saved), no advice yet');
a = D.assess(SQ(), [19], d4, { inside: true }); assert.ok(!a.spawn && a.advise === 'safemode', 'full squad inside, unwinnable: advise safe mode (never activated)');
a = D.assess([fc({ ranged_attack: 7, move: 7 })], [32], d4); assert.ok(!a.spawn && a.why === 'towers win', 'lone RA: tower handles it, no defenders');
a = D.assess([fc({ tough: 5, move: 15, attack: 10 }), fc({ heal: 6, move: 6 }), fc({ heal: 7, move: 7 })], [32], d4); assert.ok(a.spawn, 'melee + 2 healers at the seal: towers lose, towers + 2 kiting defenders win -> spawn');
assert.strictEqual(D.assess([fc({ tough: 14, move: 14 }), fc({ heal: 7, move: 7 })], [32], d4).why, 'unarmed', 'drain group: never spawns');
// ---- defender plan
const me = (x, y, hits = 1200) => ({ pos: { x, y }, hits, hitsMax: 1200, ra: 5 });
const tw = [{ x: 33, y: 35 }];
let p = D.defPlan(me(27, 6), [c('m', 27, 4, { attack: 10, move: 10 })], { towers: tw }); assert.strictEqual(p.move, 'flee', 'melee within 2 -> kite away'); assert.strictEqual(p.shoot.id, 'm', 'and shoot it');
p = D.defPlan(me(27, 6, 600), [c('r', 27, 2, { ranged_attack: 7, move: 7 })], { towers: tw }); assert.ok(p.hurt && p.move === 'retreat', '<60% -> retreat to tower');
p = D.defPlan(Object.assign(me(27, 6, 1100), { hurt: true }), [c('r', 27, 2, { ranged_attack: 7, move: 7 })], { towers: tw }); assert.ok(p.hurt, 'stays hurt until 95%');
p = D.defPlan(me(27, 6), [c('r', 26, 3, { ranged_attack: 7, move: 7 }), c('h', 27, 3, { heal: 6, move: 6 })], { towers: tw, focus: 'r' }); assert.strictEqual(p.shoot.id, 'r', 'tower focus in range: same target');
p = D.defPlan(me(27, 6), [c('r', 26, 4, { ranged_attack: 3, move: 3 }), c('h', 27, 4, { heal: 1, move: 1 })], { towers: tw }); assert.strictEqual(p.shoot.id, 'h', 'own pick: healer first');
p = D.defPlan(me(27, 6), [c('d', 27, 2, { tough: 14, move: 14 })], { towers: tw }); assert.ok(!p.shoot && p.move === 'post', 'drain tank north of seal: ignore, stay on post');
p = D.defPlan(me(27, 6), [], { towers: tw, quiet: 150 }); assert.strictEqual(p.move, 'recycle', 'quiet 100+ ticks: recycle');
p = D.defPlan(me(27, 6), [c('r', 20, 15, { ranged_attack: 11, move: 11 })], { towers: tw, win: false }); assert.strictEqual(p.move, 'retreat', 'unwinnable: back into tower cover');
p = D.defPlan(me(30, 30), [c('r', 20, 15, { ranged_attack: 11, move: 11 })], { towers: tw, win: false }); assert.strictEqual(p.move, 'hold', 'unwinnable and covered: hold, do not chase');
p = D.defPlan(me(30, 30), [c('r', 20, 15, { ranged_attack: 11, move: 11 })], { towers: tw, win: true }); assert.strictEqual(p.move, 'approach', 'winnable: approach to range 3');
p = D.defPlan(me(27, 6), [c('a', 26, 7, { ranged_attack: 2, move: 2 }), c('b', 27, 8, { ranged_attack: 2, move: 2 }), c('e', 28, 7, { ranged_attack: 2, move: 2 })], { towers: tw }); assert.ok(p.mass, '3 at range 1-2: rangedMassAttack');
console.log('w47n8 defense ok');
