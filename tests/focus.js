// node tests/focus.js : tower focus-fire choice (src/utils/focus.js)
const assert = require('assert'), F = require('../src/utils/focus');
const B = (s) => s.split(' ').flatMap(t => { const [n, k] = [parseInt(t), t.replace(/\d+/, '')]; return Array(n).fill({ type: { R: 'ranged_attack', H: 'heal', M: 'move', T: 'tough', A: 'attack' }[k], hits: 100 }); });
const c = (id, x, y, b) => { const body = B(b); return { id, pos: { x, y }, body, hits: body.length * 100 }; };
const T = [{ pos: { x: 36, y: 29 }, energy: 1000 }, { pos: { x: 37, y: 33 }, energy: 890 }];
assert.strictEqual(F.towerDmg(5), 600); assert.strictEqual(F.towerDmg(20), 150); assert.strictEqual(F.towerDmg(12), 390);
// squad (2x RA + 6 HEAL) inside west side: healer first
let sq = [c('r1', 10, 25, '8R 8M'), c('r2', 10, 26, '9R 9M'), c('h', 9, 25, '6H 6M')];
assert.strictEqual(F.pick(T, sq).h.id, 'h');
// healer exactly heals self 72: net = 300-72
assert.ok(Math.abs(F.pick(T, sq).net - 228) < 1e-6);
// healer on exit strip, RA inside -> healer priority still applies (edge no longer exempt)
sq = [c('r1', 3, 25, '8R 8M'), c('h', 1, 25, '6H 6M')]; assert.strictEqual(F.pick(T, sq).h.id, 'h');
// lone edge tank (pbefv33 4T4M at 1,27) -> shoot by default
assert.strictEqual(F.pick(T, [c('t', 1, 27, '4T 4M')]).h.id, 't');
// drain pattern: damaged -> healed back twice -> banned; then held on edge, shot if inward or hurting us
{ const m = {}, k = c('t', 1, 27, '4T 4M'); let t = 0, b;
  const step = (hits) => { k.hits = hits; b = F.track(m, [k], ++t, 't', 20); };
  step(800); step(500); step(800); assert.ok(!b.has('t')); step(300); F.track(m, [], ++t); step(800);
  assert.ok(b.has('t'), 'banned after 2 cycles');
  assert.strictEqual(F.pick(T, [k], { banned: b }), null);
  assert.ok(F.pick(T, [Object.assign({}, k, { pos: { x: 5, y: 27 } })], { banned: b }), 'inward -> fire');
  assert.ok(F.pick(T, [k], { banned: b, hurting: new Set(['t']) }), 'hurting -> fire');
  const low = Object.assign({}, k, { hits: 200 }); assert.ok(F.pick(T, [low], { banned: b }), 'killable -> fire');
  b = F.track(m, [k], t + F.BAN + 1, null, 0); assert.ok(!b.has('t'), 'ban expires'); }
// heavy heal ball out-heals: 4 boosted healers around a tank -> net<=0 -> hold
const xb = id => { const k = c(id, 20, 21, '10H 10M'); k.body = k.body.map(p => p.type === 'heal' ? Object.assign({}, p, { boost: 'XLHO2' }) : p); return k; };
assert.strictEqual(F.pick(T, [c('t', 20, 20, '10T 10M'), xb('a'), xb('b')]), null);
// ... unless it is hurting us
assert.ok(F.pick(T, [c('t', 20, 20, '10T 10M'), xb('a'), xb('b')], { hurting: new Set(['t']) }));
// boosted tough reduces damage
const bt = c('bt', 30, 30, '5T 5M'); bt.body = bt.body.map(p => p.type === 'tough' ? Object.assign({}, p, { boost: 'XGHO2' }) : p);
assert.ok(F.effective(bt, 1000) < 1000);
// sticky near-kill prev
sq = [c('r1', 30, 25, '8R 8M'), c('h', 30, 27, '6H 6M')]; sq[0].hits = 300;
assert.strictEqual(F.pick(T, sq, { prev: 'r1' }).h.id, 'r1');
// sim: towers alone vs squad parked in the west side (x=8): ticks to kill all, energy used
sq = [c('r1', 8, 25, '8R 8M'), c('r2', 8, 26, '9R 9M'), c('h', 7, 25, '6H 6M')]; let tick = 0, e = 0;
while (sq.length && tick < 200) { tick++; const p = F.pick(T, sq); if (!p) break; e += 20;
  for (const h of sq) h.hits = Math.min(h.body.length * 100, h.hits + F.healOn(h, sq) * (h === p.h ? 0 : 0));
  p.h.hits -= p.net; sq = sq.filter(h => h.hits > 0); }
assert.ok(!sq.length, 'towers must kill the squad'); console.log(`focus ok; towers-only sim: squad dead in ${tick} ticks, ${e} tower energy`);
{ // 10-16 dpefwd3: big tank lightly scratched (5000->4700) and healed twice is NOT a drain
  const F = require('../src/utils/focus'), mem = {}, h = { id: 't', hits: 5000, hitsMax: 5000, body: [] };
  let b; for (let i = 0; i < 3; i++) { h.hits = 4700; F.track(mem, [h], i * 2, 't', 20); h.hits = 5000; b = F.track(mem, [h], i * 2 + 1); }
  require('assert').ok(!b.has('t'), 'light scratches must not ban');
  for (let i = 0; i < 2; i++) { h.hits = 3000; F.track(mem, [h], 10 + i * 2, 't', 20); h.hits = 5000; b = F.track(mem, [h], 11 + i * 2); }
  require('assert').ok(b.has('t'), 'real knock-down cycles ban'); console.log('focus dpefwd3 ok');
}
{ // 17:48 tower heal rule: < 60% only; no-HEAL creeps first, then lowest hp%
  const F = require('../src/utils/focus'), A = require('assert');
  const k = (id, hits, max, heal) => ({ id, hits, hitsMax: max, body: heal ? [{ type: 'heal', hits: 100 }] : [{ type: 'ranged_attack', hits: 100 }] });
  A.strictEqual(F.healPick([k('a', 700, 1000)]), null, '70%: no heal');
  A.strictEqual(F.healPick([k('a', 500, 1000, true), k('b', 550, 1000)]).id, 'b', 'no-HEAL creep first even if higher %');
  A.strictEqual(F.healPick([k('a', 500, 1000), k('b', 300, 1000)]).id, 'b', 'then lowest %');
  console.log('focus healPick ok'); }
