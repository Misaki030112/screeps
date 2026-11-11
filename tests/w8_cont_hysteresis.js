// 11-11 15:xx W47N8 builder container repair hysteresis (5 containers hover ~50%; builders flipped targets on every 15-tick rescan).
// Enter <50%, hold until >60%, no switch when another container crosses 50%; only a <10% job elsewhere pre-empts.
// node tests/w8_cont_hysteresis.js -> exits 1 on failure
const path = require('path'), assert = require('assert'), fs = require('fs');
const src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, { STRUCTURE_CONTAINER: 'container', STRUCTURE_ROAD: 'road' });
const H = require(src('rooms/w47n8/contrep.js'));
const cont = (id, pct) => ({ id, structureType: 'container', hitsMax: 250000, hits: Math.round(250000 * pct) });
const cases = [
  ['thresholds 50/60/10', () => { assert.deepStrictEqual([H.IN, H.OUT, H.CRASH], [0.5, 0.6, 0.1]); }],
  ['pick under 50% arms the hold; held through 50..60%; released above 60%', () => {
    const m = {}, k = cont('k', 0.4996); H.mark(m, k); assert.strictEqual(m.rjc, 1);
    for (const p of [0.4996, 0.52, 0.6]) { k.hits = 250000 * p; assert.ok(H.held(m, k), 'held at ' + p); }
    k.hits = 250000 * 0.6004; assert.ok(!H.held(m, k)); assert.ok(!('rjc' in m));
  }],
  ['pick at/above 50% (or a road / nothing) does not hold', () => {
    const m = {}; H.mark(m, cont('k', 0.55)); assert.ok(!H.held(m, cont('k', 0.55)));
    H.mark(m, { id: 'r', structureType: 'road', hits: 1, hitsMax: 5000 }); assert.ok(!m.rjc);
    m.rjc = 1; assert.ok(!H.held(m, null)); assert.ok(!m.rjc);
  }],
  ['roles.js: held target skips the 15-tick rescan / contUrgent break; only CRASH jobs pre-empt; pick arms mark', () => {
    const t = fs.readFileSync(src('rooms/w47n8/roles.js'), 'utf8');
    assert.ok(/const hold = CREP\.held\(c\.memory, rep\);/.test(t));
    assert.ok(/const crash = contNeed\(CREP\.CRASH\) \|\| roadNeed\(CREP\.CRASH\);\s*if \(crash && crash\.id !== rep\.id\)/.test(t));
    assert.ok(/const contUrgent = hold \? null : contNeed\(CREP\.IN\);/.test(t));
    assert.ok(/if \(!hold && \(!rep \|\| Game\.time >= \(c\.memory\.rjt \|\| 0\)/.test(t));
    assert.ok(/c\.memory\.rjt = Game\.time \+ 15; CREP\.mark\(c\.memory, rep\);/.test(t));
  }],
];
let fail = 0; for (const [n, f] of cases) { try { f(); console.log('ok  ', n); } catch (e) { fail++; console.log('FAIL', n, e.message); } }
console.log(`w8 cont hysteresis: ${cases.length - fail}/${cases.length}`); process.exit(fail ? 1 : 0);
