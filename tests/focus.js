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
// healer on exit strip, RA inside -> shoot the RA (net 300-72 adj heal)
sq = [c('r1', 3, 25, '8R 8M'), c('h', 1, 25, '6H 6M')]; assert.strictEqual(F.pick(T, sq).h.id, 'r1');
// lone edge tank, not hurting us -> hold fire
assert.strictEqual(F.pick(T, [c('t', 0, 25, '14T 14M')]), null);
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
