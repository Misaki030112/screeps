// W45N7 remote (Misaki 2026-10-16 14:39): multi-hop route, hauler ramp, CLAIM2-only reserver, defender smart targeting.
// node tests/w45n7.js -> exits 1 on failure
const path = require('path'), assert = require('assert'), fs = require('fs'), ROOT = path.join(__dirname, '..');
const src = p => path.join(ROOT, 'src', p);
Object.assign(global, { RESOURCE_ENERGY: 'energy', STRUCTURE_LINK: 'link', STRUCTURE_CONTAINER: 'container', CARRY: 'carry', MOVE: 'move', WORK: 'work', CLAIM: 'claim',
  RANGED_ATTACK: 'ranged_attack', HEAL: 'heal', BODYPART_COST: {}, Memory: {}, _: require('lodash') });
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: p, loaded: true, exports: exp }; };
let n = 0; const ok = (name, c) => { assert(c, name); n++; };
// 1) route + exits (real remote.js CFG; threat stubbed)
stub('managers/threat.js', { safe: () => true, state: () => ({ st: 'SAFE' }) });
const R = require(src('managers/remote.js'));
ok('route W45N7', JSON.stringify(R.route('W45N7')) === '["W46N8","W45N8","W45N7"]');
ok('route W45N8', JSON.stringify(R.route('W45N8')) === '["W46N8","W45N8"]');
ok('home->W45N8 via 49,21 for W45N7', R.exitTile('W45N7', 'W46N8', 'W45N8').join() === '49,21');
ok('W45N8 south exit', R.exitTile('W45N7', 'W45N8', 'W45N7').join() === '21,49');
ok('W45N7 back north', R.exitTile('W45N7', 'W45N7', 'W45N8').join() === '21,0');
ok('W45N8 legacy exits', R.exitTile('W45N8', 'W46N8', 'W45N8').join() === '49,14' && R.exitTile('W45N8', 'W45N8', 'W46N8').join() === '0,14');
const C7 = R.CFG.W45N7;
ok('container not on the Council site', C7.cont.join() !== '22,15' && C7.avoid.some(a => a.join() === '22,15'));
ok('haul fleet unchanged (5 / gap 60 / steady 240)', C7.haulers === 5 && C7.rhGap === 60 && C7.rhGapSteady === 240);
const T = fs.readFileSync(path.join(ROOT, 'data/terrain_W45N7.txt'), 'utf8'), wall = (x, y) => T[y * 50 + x] === '1' || T[y * 50 + x] === '3';
ok('container tile is open and next to the source', !wall(...C7.cont) && Math.max(Math.abs(C7.cont[0] - C7.src[0]), Math.abs(C7.cont[1] - C7.src[1])) === 1);
ok('patrol/scout tiles open', !wall(...C7.scout));
Memory.remotes = { W45N7: { off: true } }; ok('off switch pauses', R.paused('W45N7') && !R.paused('W45N8')); Memory.remotes = {};
// 2) spawn: hauler ramp + CLAIM2 only
stub('utils/plan.js', { get: () => null, key: (x, y) => x * 50 + y }); stub('utils/roomcache.js', {}); stub('roles/hauler.js', {}); stub('roles/queen.js', {});
const S = require(src('managers/spawn.js'));
ok('no haulers before container 60%', S.rhTarget(C7, { siteProg: 1000 }, 5000) === 0);
ok('2 haulers at >=60% with reserve', S.rhTarget(C7, { siteProg: 3200 }, 1500) === 2);
ok('bootstrap reserve 1300 gate', S.rhTarget(C7, { siteProg: 3200 }, 900) === 0);
ok('5 haulers once built', S.rhTarget(C7, { cont: { id: 'x' } }, 0) === 5);
ok('W45N8 unchanged (2)', S.rhTarget(R.CFG.W45N8, {}, 0) === 2);
const base = { nRes: 0, wantRes: 1, res: 0, cap: 1800, rmLive: 1, rhLive: 6, rhAll: 6, rhTarget: 6 };
ok('claim2Only waits at avail 1000', S.remoteNext(Object.assign({}, base, { avail: 1000, claim2Only: true })) !== 'reserver');
ok('claim2Only spawns at 1300', S.remoteNext(Object.assign({}, base, { avail: 1300, claim2Only: true })) === 'reserver');
ok('ramp: rhauler up to target', S.remoteNext(Object.assign({}, base, { avail: 800, res: 4000, rhLive: 3, rhAll: 3 })) === 'rhauler');
ok('gap blocks (rhLive 99)', S.remoteNext(Object.assign({}, base, { avail: 800, res: 4000, rhLive: 99, rhAll: 3 })) === null);
// 3) defender targeting
const F = require(src('utils/focus.js'));
const b = (t, k) => Array(k).fill(0).map(() => ({ type: t, hits: 100 }));
const h = (id, x, y, body) => ({ id, pos: { x, y }, hits: body.length * 100, hitsMax: body.length * 100, body });
const me = { x: 10, y: 10 };
const melee = h('m', 12, 10, b('attack', 3).concat(b('move', 3))), healer = h('h', 13, 10, b('heal', 1).concat(b('move', 1)));
ok('healer first when net>0', F.pickDef(me, 5, [melee, healer]).h.id === 'h');
const bigHeal = h('H', 13, 10, b('heal', 6).concat(b('move', 6)));
ok('healer we cannot out-damage -> fastest kill', F.pickDef(me, 5, [melee, bigHeal]).h.id !== undefined);
const c3 = [h('a', 11, 10, b('move', 2)), h('b', 11, 11, b('move', 2)), h('c', 12, 9, b('move', 2))];
ok('mass when 3 within 2', F.pickDef(me, 5, c3).mass === true);
ok('no mass when spread', F.pickDef(me, 5, [h('a', 13, 10, b('move', 2)), h('b', 13, 13, b('move', 2)), h('c', 7, 7, b('move', 2))]).mass === false);
const dying = h('d', 12, 12, b('move', 5)); dying.hits = 40; const fresh = h('f', 11, 10, b('heal', 1));
ok('sticky on dying prev', F.pickDef(me, 5, [dying, fresh], 'd').h.id === 'd');
ok('canWin vs small melee', F.canWin({ hits: 1300, ra: 5, heal: 1 }, melee, [melee]));
ok('cannot win vs 6-heal healer', !F.canWin({ hits: 1300, ra: 5, heal: 1 }, bigHeal, [bigHeal]));
console.log(`w45n7: ${n} ok`);
// 4) energyHold: WAIT(gate) on a solo Invader only because energy < 1300 -> hold spawns
delete require.cache[require.resolve(src('managers/threat.js'))];
const TH = require(src('managers/threat.js'));
Memory.remote = { W45N7: { needE: true, th: { st: 'WAIT', why: 'gate', last: [{ heal: false, ranged3: false }] } }, W45N8: { th: { st: 'SAFE' } } };
ok('energyHold on (gate + needE + solo)', TH.energyHold('W46N8') && TH.holding('W46N8'));
Memory.remote.W45N7.needE = false; ok('no hold when the gate is not energy', !TH.energyHold('W46N8'));
Memory.remote.W45N7.needE = true; Memory.remote.W45N7.th.last = [{ heal: true }]; ok('no hold for healer group', !TH.energyHold('W46N8'));
console.log(`w45n7 + energyHold: ${n} ok`);

// 5) stageOut: non-full rhaulers (half-full included) via-stage when the container is drained
const { stageOut, STAGE, waiterOrder, pocketAct, POCKET, waitStand, stepOffAvoid } = require(src('roles/remote.js'));
ok('low energy + 2 waiters: outsider stages', stageOut(null, 40, ['a', 'b']));
ok('low energy + 1 waiter: outsider enters', !stageOut(null, 40, ['a']));
ok('buffered energy: outsider enters even if 3 wait', !stageOut(null, STAGE.energy, ['a', 'b', 'c']));
ok('in-room closest 2 stay', !stageOut('a', 40, ['a', 'b', 'c']) && !stageOut('b', 40, ['a', 'b', 'c']));
ok('in-room 3rd leaves', stageOut('c', 40, ['a', 'b', 'c']));
ok('in-room alone stays', !stageOut('a', 40, ['a']));
const pocket = [
  { name: 'half', full: false, x: 21, y: 14 }, // partial load on a legal stand, dist 1
  { name: 'onavoid', full: false, x: 22, y: 15 }, // also dist 1; still a slot, but not a legal stand
  { name: 'leaving', full: true, x: 20, y: 14 }, // full, walking out, does not hold a slot
  { name: 'far', full: false, x: 21, y: 2 }, // empty, still in the remote, dist 13
];
const slots = waiterOrder(pocket, C7.cont[0], C7.cont[1]);
ok('waiter list keeps half-full, drops the full hauler', slots.join() === 'half,onavoid,far');
ok('stageOut: half-full waiter occupies a slot', stageOut(null, 40, ['half', 'empty']) && !stageOut(null, 40, ['half']));
ok('stageOut: third non-full leaves, half-full stays', stageOut('far', 40, slots) && !stageOut('half', 40, slots) && !stageOut('onavoid', 40, slots));
ok('stageOut: outsider stages while non-full haulers already fill the cap', stageOut(null, 40, slots));
ok('stageOut: energy bypass still lets a new empty in', !stageOut(null, STAGE.energy, slots));
// 5b) pocket: withdraw a thin container; 8C8M at 200 leaves after a short thin streak
ok('withdraw 1 on a thin container', pocketAct(0, 1, 0, 400).act === 'withdraw');
ok('withdraw 30 (below the old 50 gate)', pocketAct(0, 30, 40, 400).act === 'withdraw' && pocketAct(0, 30, 40, 400).wait === 0);
ok('withdraw 49', pocketAct(200, 49, 80, 400).act === 'withdraw');
ok('empty container does not withdraw', pocketAct(0, 0, 0, 400).act === 'wait');
ok('200 before the wait stays', pocketAct(200, 0, POCKET.wait - 2, 400).act === 'wait');
ok('leave-early at 200 after the wait', pocketAct(200, 0, POCKET.wait - 1, 400).act === 'leave' && pocketAct(200, 0, 83, 400).act === 'leave');
ok('100 after the wait leaves', pocketAct(POCKET.leave, 0, POCKET.wait - 1, 400).act === 'leave');
ok('below 100 does not leave', pocketAct(POCKET.leave - 1, 0, 80, 400).act === 'wait');
ok('empty never leaves on a thin streak', pocketAct(0, 0, 80, 400).act === 'wait');
ok('road hauler at 200 still waits', pocketAct(200, 0, POCKET.wait - 1, 1200).act === 'wait');
ok('road hauler still leaves at 60% after 31 thin ticks', pocketAct(720, 0, 30, 1200).act === 'leave' && pocketAct(720, 0, 29, 1200).act === 'wait');
// 5c) avoid (22,15) is not a wait stand; a creep on it steps to a legal neighbor
ok('avoid tile is not a wait stand', !waitStand(22, 15, C7.cont, C7.avoid, wall));
ok('container and the wall beside it are not wait stands', !waitStand(21, 15, C7.cont, C7.avoid, wall) && !waitStand(20, 15, C7.cont, C7.avoid, wall));
ok('legal pocket stands', [[20, 14], [21, 14], [22, 14], [22, 16]].every(([x, y]) => waitStand(x, y, C7.cont, C7.avoid, wall)));
const DELTA = { 1: [0, -1], 2: [1, -1], 3: [1, 0], 4: [1, 1], 5: [0, 1], 6: [-1, 1], 7: [-1, 0], 8: [-1, -1] };
const stepTo = (dir, x, y) => [x + DELTA[dir][0], y + DELTA[dir][1]];
const off = stepOffAvoid(22, 15, C7.cont, C7.avoid, (x, y) => wall(x, y) || (x === C7.src[0] && y === C7.src[1]));
const landed = stepTo(off, 22, 15);
ok('step off avoid onto a wait stand', off > 0 && waitStand(landed[0], landed[1], C7.cont, C7.avoid, wall) && landed.join() === '22,14');
const offBusy = stepOffAvoid(22, 15, C7.cont, C7.avoid, (x, y) => wall(x, y) || (x === 22 && y === 14) || (x === C7.src[0] && y === C7.src[1]));
const landedBusy = stepTo(offBusy, 22, 15);
ok('avoid with 22,14 taken steps to 22,16', waitStand(landedBusy[0], landedBusy[1], C7.cont, C7.avoid, wall) && landedBusy.join() === '22,16');
ok('not on avoid: no step', stepOffAvoid(21, 14, C7.cont, C7.avoid, wall) === 0);
// 6) viaTake: staged rhauler takes one load from the via (W45N8) container, leaving VIA_KEEP for its own haulers
const { viaTake, VIA_KEEP } = require(src('roles/remote.js'));
ok('via full container: take', viaTake(2000, 400));
ok('via keeps reserve: exact edge', viaTake(VIA_KEEP + 400, 400) && !viaTake(VIA_KEEP + 399, 400));
ok('via low: no take', !viaTake(900, 400));
ok('no free capacity: no take', !viaTake(2000, 0));
ok('unknown container: no take', !viaTake(undefined, 400));
// 7) via gate: W45N8 under threat -> W45N7 creeps don't walk through it
const { viaGate } = require(src('roles/remote.js'));
ok('via safe: no gate', viaGate(false, 'home', false) === null && viaGate(false, 'remote', true) === null);
ok('via unsafe: empty at home stays home', viaGate(true, 'home', false) === 'home');
ok('via unsafe: loaded at home delivers', viaGate(true, 'home', true) === null);
ok('via unsafe: loaded in remote holds', viaGate(true, 'remote', true) === 'hold');
ok('via unsafe: empty in remote works, no staging', viaGate(true, 'remote', false) === 'nostage');
ok('via unsafe: in via room carries on', viaGate(true, 'via', false) === null && viaGate(true, 'via', true) === null);
console.log(`w45n7 + stageOut + viaTake + viaGate: ${n} ok`);
