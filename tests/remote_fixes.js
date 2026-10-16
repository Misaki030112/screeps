// W45N8 fight review fixes (2026-10-16): rminer repair rule, kite hold/inertia, threat early resume, remote birth directions.
// node tests/remote_fixes.js -> exits 1 on failure
const fs = require('fs'), path = require('path'), assert = require('assert'), ROOT = path.join(__dirname, '..');
Object.assign(global, { TERRAIN_MASK_WALL: 1, TERRAIN_MASK_SWAMP: 2, MOVE: 'move', ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack', _: require('lodash') });
let n = 0; const ok = (name, c, i) => { assert(c, name + ' ' + JSON.stringify(i === undefined ? '' : i)); n++; };
// 1) repair rule
const { repairNow } = require(path.join(ROOT, 'src/roles/remote.js'));
ok('urgent <30k repairs even with room', repairNow(29000, 40, 12, false));
ok('40k with room: harvest', !repairNow(40000, 40, 12, false));
ok('40k full: batch repair', repairNow(40000, 6, 12, false));
ok('60k full: no repair', !repairNow(60000, 6, 12, false));
ok('source empty: free repair <100k', repairNow(90000, 40, 12, true) && !repairNow(120000, 40, 12, true));
// 2) kite hold + inertia
const T = fs.readFileSync(path.join(ROOT, 'data/terrain_W45N8.txt'), 'utf8');
const wall = (x, y) => T[y * 50 + x] === '1' || T[y * 50 + x] === '3', swamp = (x, y) => T[y * 50 + x] === '2';
const room = { getTerrain: () => ({ get: (x, y) => wall(x, y) ? 1 : swamp(x, y) ? 2 : 0 }) };
const K = require(path.join(ROOT, 'src/utils/kite.js'));
const inv = (x, y) => ({ pos: { x, y }, fatigue: 0, body: Array(5).fill({ type: 'move', hits: 100 }) });
const st = (d, t, o) => K.step({ pos: { x: d[0], y: d[1] }, room }, t, false, [0, 14], o);
let hold = 0, tot = 0;
for (let x = 10; x <= 30; x++) for (let y = 4; y <= 11; y++) { if (wall(x, y) || swamp(x, y) || wall(x + 5, y) || swamp(x + 5, y)) continue; tot++; if (st([x, y], inv(x + 5, y), { approaching: true }) === 0) hold++; }
ok('approaching at 5, plain: hold', tot > 0 && hold === tot, [hold, tot]);
let flips = 0;
for (let x = 12; x <= 28; x++) for (let y = 4; y <= 11; y++) { if (wall(x, y) || swamp(x, y)) continue; const t = inv(x + 3, y);
  const a = st([x, y], t, {}); if (!a) continue; const b = st([x, y], t, { last: [0, 5, 6, 7, 8, 1, 2, 3, 4][a] });
  if (b !== a && b === [0, 5, 6, 7, 8, 1, 2, 3, 4][a]) flips++; }
ok('inertia never prefers reversing', flips === 0, flips);
// 5) early resume
global.Memory = {}; const th = require(path.join(ROOT, 'src/managers/threat.js'));
const D = { st: 'DEFEND' }, I = h => [{ hits: h, hitsMax: 1000 }];
ok('target 10% + defender in: early', th.earlyNext(Object.assign({}, D, { last: I(100) }), true));
ok('target 50%: not early', !th.earlyNext(Object.assign({}, D, { last: I(500) }), true));
ok('no defender in room: not early', !th.earlyNext(Object.assign({}, D, { last: I(100) }), false));
ok('dead (clearTicks wait): early', th.earlyNext(Object.assign({}, D, { last: null }), true));
ok('sticky at 20%', th.earlyNext(Object.assign({}, D, { last: I(200), early: true }), true) && !th.earlyNext(Object.assign({}, D, { last: I(200) }), true));
ok('healed >30%: off', !th.earlyNext(Object.assign({}, D, { last: I(400), early: true }), true));
ok('not DEFEND: off', !th.earlyNext({ st: 'WAIT', last: null, early: true }, true));
Memory.remote = { W45N8: { th: { st: 'DEFEND', early: true } } };
ok('safe(): rminer/rhauler only', th.safe('W45N8', 'rminer') && th.safe('W45N8', 'rhauler') && !th.safe('W45N8', 'reserver') && !th.safe('W45N8'));
console.log(`remote_fixes tests passed (${n})`);
