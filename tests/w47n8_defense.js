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
  assert.ok(!b.includes('heal'), 'no HEAL (17:34: towers heal) @' + e); }
assert.strictEqual(W.bodyFor('w8defender', 2300).length, 22, 'RCL4/5 local body: up to 11RA11M');
assert.deepStrictEqual(require('lodash').countBy(D.raBody(2300, 25)), { ranged_attack: 11, move: 11 }, 'home defender at cap 2300: 11RA11M (2200)');
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
assert.strictEqual(D.towerPick(T1, sq).h.id, 'h', 'healer always first (Misaki 17:40)');
assert.strictEqual(D.towerPick(T1, sq.slice(0, 2)).h.id, 'r', 'ranged before melee');
assert.strictEqual(D.towerPick(T1, sq.slice(0, 1)).h.id, 'm', 'melee when alone');
// sticky prev when about to die, even if a healer is present
sq[0].hits = 300; assert.strictEqual(D.towerPick(T1, sq, { prev: 'm' }).h.id, 'm', 'finish the near-dead previous target');
assert.strictEqual(D.towerPick(T1, [c('r1', 30, 30, { ranged_attack: 7, move: 7 }), c('r2', 31, 30, { ranged_attack: 7, move: 7 }, 500)]).h.id, 'r2', 'within a class: lowest hp');
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
// ---- defender plan (Misaki 17:36-17:40: wall posts, HP rule 60/90, healer > ranged > melee)
const me = (x, y, hits = 2200) => ({ pos: { x, y }, hits, hitsMax: 2200 });
const tw = [{ x: 33, y: 35 }];
let p = D.defPlan(me(29, 4), [c('r', 29, 1, { ranged_attack: 8, move: 8 }), c('h', 30, 1, { heal: 7, move: 7 }), c('m', 28, 2, { attack: 10, move: 10 })], { towers: tw });
assert.strictEqual(p.shoot.id, 'h', 'at the wall: healer first'); assert.notStrictEqual(p.move, 'flee', 'melee north of the seal cannot reach y=4: no kiting');
p = D.defPlan(me(29, 4), [c('r', 29, 1, { ranged_attack: 8, move: 8 }), c('r2', 30, 1, { ranged_attack: 6, move: 6 }, 300)], { towers: tw }); assert.strictEqual(p.shoot.id, 'r2', 'lowest hp within class');
p = D.defPlan(me(29, 4), [c('r', 29, 1, { ranged_attack: 8, move: 8 }), c('h', 30, 1, { heal: 7, move: 7 })], { towers: tw, focus: 'h' }); assert.strictEqual(p.shoot.id, 'h', 'tower focus in range: same target');
p = D.defPlan(me(29, 4, 1400), [c('r', 29, 1, { ranged_attack: 8, move: 8 })], { towers: tw }); assert.ok(!p.hurt && p.move !== 'retreat', '64% hp: stays at the wall');
p = D.defPlan(me(29, 4, 1300), [c('r', 29, 1, { ranged_attack: 8, move: 8 })], { towers: tw }); assert.ok(p.hurt && p.move === 'retreat' && p.goal.y === 35, '<60%: retreat to the tower');
p = D.defPlan(Object.assign(me(30, 20, 1900), { hurt: true }), [c('r', 29, 1, { ranged_attack: 8, move: 8 })], { towers: tw }); assert.ok(p.hurt, '86%: still retreating');
p = D.defPlan(Object.assign(me(30, 20, 1980), { hurt: true }), [c('r', 29, 1, { ranged_attack: 8, move: 8 })], { towers: tw }); assert.ok(!p.hurt && p.move === 'post' && p.goal.y === 4, '>=90%: back to the wall post');
// posts: right behind the seal (y=4) on the segment nearest the enemy, spread by idx, never the 27,4 swamp
assert.deepStrictEqual(D.postTile(31, 0), { x: 31, y: 4 }); assert.deepStrictEqual(D.postTile(31, 1), { x: 29, y: 4 }, 'second defender spread 2 tiles');
assert.deepStrictEqual(D.postTile(9, 0), { x: 9, y: 4 }, 'west seal segment'); assert.ok([0, 1, 2, 3].every(i => D.postTile(27, i).x !== 27), 'no swamp post');
p = D.defPlan(me(25, 8), [c('r', 31, 1, { ranged_attack: 8, move: 8 })], { towers: tw }); assert.deepStrictEqual([p.move, p.goal], ['post', { x: 31, y: 4 }], 'enemy at x31 north: go to 31,4');
p = D.defPlan(me(25, 8), [], { towers: tw, enemyX: 31, quiet: 10 }); assert.deepStrictEqual(p.goal, { x: 31, y: 4 }, 'alert from W47N9 (x31): pre-stage at 31,4');
p = D.defPlan(me(27, 6), [c('m', 27, 7, { attack: 10, move: 10 })], { towers: tw }); assert.strictEqual(p.move, 'flee', 'melee inside the seal within 2 -> kite');
p = D.defPlan(me(27, 6), [c('d', 27, 2, { tough: 14, move: 14 })], { towers: tw }); assert.ok(!p.shoot, 'drain tank north of seal: ignored');
p = D.defPlan(me(27, 6), [], { towers: tw, quiet: 150 }); assert.strictEqual(p.move, 'recycle', 'quiet 100+ ticks: recycle');
p = D.defPlan(me(27, 6), [c('a', 26, 7, { ranged_attack: 2, move: 2 }), c('b', 27, 8, { ranged_attack: 2, move: 2 }), c('e', 28, 7, { ranged_attack: 2, move: 2 })], { towers: tw }); assert.ok(p.mass, '3 within 2: rangedMassAttack');
// ---- joint planner (one place for W46N8 + W47N8; Misaki 17:45: baseline 1 home defender, extra only if it turns a loss into a win)
const P = f => D.plan(Object.assign({ towerR: [32], homeOk: true, homeCap: 2300, w8Cap: 1300 }, f));
const B9 = a => a.map(fc), RA = (k) => ({ ranged_attack: k, move: k }), HL = k => ({ heal: k, move: k });
let pl = P({ force: B9([RA(6), RA(8)]) }); assert.deepStrictEqual([pl.home, pl.w8, pl.win], [1, 0, true], 'pair: baseline home 1 even though towers win');
pl = P({ force: B9([RA(6), RA(8), HL(7), HL(7)]) }); assert.deepStrictEqual([pl.home, pl.w8], [1, 1], 'pair + 2 healers: baseline + fewest local that win');
pl = P({ force: B9([RA(6), RA(8), HL(7), HL(7), HL(7)]) }); assert.ok(pl.home >= 1 && pl.home <= 2, 'pair + 3 healers: baseline, a 2nd only if it wins');
if (pl.home === 2) assert.ok(pl.win, '2nd home defender only when it turns it into a win'); else assert.ok(!pl.win && pl.w8 === 0, 'unwinnable: baseline only, no local fed');
pl = P({ force: SQ() }); assert.deepStrictEqual([pl.home, pl.w8, pl.win], [2, 2, true], 'full squad RCL4: only 2 home + 2 local (all four 11RA/6RA) win in the model');
pl = P({ force: SQ(), homeCap: 1300 }); assert.deepStrictEqual([pl.home, pl.w8, pl.win], [1, 0, false], 'full squad, small home bodies: unwinnable -> baseline only, nothing else fed');
pl = P({ force: SQ(), towerR: [19], inside: true, homeOk: false }); assert.strictEqual(pl.advise, 'safemode', 'inside + unwinnable (home busy): advise safe mode');
pl = P({ force: B9([RA(6), RA(8)]), homeOk: false }); assert.strictEqual(pl.home, 0, 'home threatened: no support');
assert.strictEqual(P({ force: B9([{ tough: 14, move: 14 }, HL(7)]) }).home, 0, 'drain group (unarmed): no support');
for (const f of [[RA(6), RA(8), HL(7), HL(7), HL(7)], [RA(11), HL(6), HL(6)], [RA(11), RA(7), HL(7), HL(7), HL(6)]]) { const r = P({ force: B9(f) });
  assert.ok(r.home <= 2 && r.w8 <= 2 && (r.home < 2 || r.win), 'support capped; 2nd home only on a win ' + JSON.stringify(r)); }
// ---- seal repair under fire
const wl = (x, hits) => ({ pos: { x, y: 3 }, hits });
const ws = [wl(24, 50000), wl(29, 42000), wl(30, 30000), wl(10, 1000)];
assert.strictEqual(D.repairPick(ws, [c('r', 29, 1, { ranged_attack: 8, move: 8 })]).pos.x, 30, 'lowest wall in reach of the enemy (west 10,3 unattacked ignored)');
assert.strictEqual(D.repairPick(ws, [c('d', 29, 1, { tough: 8, move: 8 })]), null, 'unarmed: no combat repair');
const st = D.repairStand(wl(30, 1), [c('r', 30, 1, { ranged_attack: 8, move: 8 })]);
assert.ok(st.y > 3 && Math.max(Math.abs(st.x - 30), st.y - 3) <= 3 && Math.max(Math.abs(st.x - 30), st.y - 1) >= 4, 'repair stand in range 3 of the wall, out of enemy range 3: ' + JSON.stringify(st));
console.log('w47n8 defense ok');
// home-sent marker must survive main.js's first-tick memory cleanup (it deletes 'src' on creeps without v2)
{ const s = require('fs').readFileSync(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'index.js'), 'utf8');
  assert.ok(/jd: HOME, born: Game\.time, v2: 1/.test(s) && !/src: HOME/.test(s), 'home defender marked jd + v2'); console.log('w47n8 jd marker ok'); }
