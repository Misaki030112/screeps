// 11-11 15:xx: W47N8 west 1-wide wrap (8,18-22 / 11,25) packed because upgraders left their stands
// and walked the south ctl→hub exit, turning loaded haulers onto the long west wrap.
// 12,26 was both UPG_STAND and the west-wrap trunk. pickTile miss must not fall through to getEnergy
// while the battery is live or the upgrader is 1-CARRY stay.
// node tests/w8_upg_stand_trunk.js -> exits 1 on failure
const path = require('path'), assert = require('assert'), fs = require('fs');
const src = p => path.join(__dirname, '..', 'src', p);
const C = require(src('rooms/w47n8/config.js'));
const ROADS = new Set(require(src('rooms/w47n8/roads.js')).ROADS.map(([x, y]) => x + ',' + y));
const TRUNK = ['11,25', '12,26', '12,27', '12,28', '13,27', '13,29', '14,28', '14,30'];
const cases = [
  ['12,26 is no longer a stand (it is the west-wrap trunk into the ctl pocket)', () => {
    assert.ok(!C.UPG_STAND.some(([x, y]) => x === 12 && y === 26), JSON.stringify(C.UPG_STAND));
  }],
  ['UPG_STAND tiles are off ROADSET / hauler trunks (ctl-haul, west wrap, south hub exit)', () => {
    const on = C.UPG_STAND.map(([x, y]) => x + ',' + y).filter(k => ROADS.has(k) || TRUNK.includes(k));
    assert.deepStrictEqual(on, [], JSON.stringify(on));
  }],
  ['three stands, each in range 1 of the ctl container or link (withdraw)', () => {
    assert.strictEqual(C.UPG_STAND.length, 3);
    const bat = [C.CTL_CONT, C.CTL_LINK];
    for (const [x, y] of C.UPG_STAND) {
      assert.ok(bat.some(([bx, by]) => Math.max(Math.abs(x - bx), Math.abs(y - by)) <= 1), x + ',' + y);
    }
  }],
  ['roles.js: pickTile miss + stay/battery returns (does not fall through to getEnergy)', () => {
    const t = fs.readFileSync(src('rooms/w47n8/roles.js'), 'utf8');
    assert.ok(/pickTile miss/.test(t));
    assert.ok(/delete c\.memory\.st;\s*const stay = c\.store\.getCapacity\(\) <= 50;/.test(t));
    assert.ok(/if \(c\.store\[E\] \|\| cont\.store\[E\] \|\| stay\) return;/.test(t));
  }],
];
let fail = 0; for (const [n, f] of cases) { try { f(); console.log('ok  ', n); } catch (e) { fail++; console.log('FAIL', n, e.message); } }
console.log(`w8 upg stand trunk: ${cases.length - fail}/${cases.length}`); process.exit(fail ? 1 : 0);
