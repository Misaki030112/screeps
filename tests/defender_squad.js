// RCL7 remote defender body + squad size (default 1, max 4). node tests/defender_squad.js
const path = require('path'), assert = require('assert');
global.ATTACK = 'attack'; global.RANGED_ATTACK = 'ranged_attack'; global.HEAL = 'heal'; global.MOVE = 'move';
global.WORK = 'work'; global.CARRY = 'carry'; global.CLAIM = 'claim'; global.TOUGH = 'tough';
global.RESOURCE_ENERGY = 'energy';
global.BODYPART_COST = { attack: 80, move: 50, ranged_attack: 150, heal: 250, work: 100, carry: 50, tough: 10, claim: 600 };
global._ = {
  sum: (a, f) => (Array.isArray(a) ? a : []).reduce((s, x) => s + (f ? f(x) : x), 0),
  filter: (a, f) => Object.values(a || {}).filter(f),
  some: (a, f) => Object.values(a || {}).some(f),
  countBy: (a, f) => { const o = {}; for (const x of Object.values(a || {})) { const k = typeof f === 'function' ? f(x) : x[f]; o[k] = (o[k] || 0) + 1; } return o; },
};
global.Game = { time: 1, creeps: {}, rooms: {}, cpu: { bucket: 10000 } };
global.Memory = { remote: {}, ops: {}, defense: { remoteDefender: true }, username: 'Misaki' };
const S = require(path.join(__dirname, '..', 'src/managers/spawn.js'));
const T = require(path.join(__dirname, '..', 'src/managers/threat.js'));
const cost = b => b.reduce((s, p) => s + BODYPART_COST[p], 0);
const n = (b, p) => b.filter(x => x === p).length;

const small = S.B.defender(1300);
assert.strictEqual(n(small, RANGED_ATTACK), 5);
assert.strictEqual(n(small, HEAL), 1);
assert.strictEqual(n(small, MOVE), 6);
assert.strictEqual(cost(small), 1300);

const big = S.B.defender(5600);
assert.strictEqual(n(big, RANGED_ATTACK), 19, 'RCL7 ranged');
assert.strictEqual(n(big, HEAL), 6);
assert.strictEqual(n(big, MOVE), 25);
assert.strictEqual(big.length, 50);
assert.strictEqual(cost(big), 5600);
assert.ok(cost(S.B.defender(4000)) <= 4000);
assert.strictEqual(T.DEF.fullBody, 5600);
assert.strictEqual(cost(S.B.defender(T.DEF.fullBody)), T.DEF.fullBody, 'fullBody is the max defender recipe cost');
assert.strictEqual(S.B.defender(T.DEF.fullBody).length, 50);
assert.ok(S.B.defender(T.DEF.fullBody - 1).length < 50, 'one energy under fullBody is not the max body');
assert.strictEqual(n(S.B.coreBuster(T.DEF.fullBody), ATTACK), 25, 'same cap maxes the core buster');

const bust = S.B.coreBuster(1300);
assert.strictEqual(n(bust, ATTACK), 10);
assert.strictEqual(cost(bust), 1300);
const bust7 = S.B.coreBuster(5600);
assert.strictEqual(n(bust7, ATTACK), 25);
assert.strictEqual(n(bust7, MOVE), 25);
assert.strictEqual(cost(bust7), 3250);
assert.ok(cost(bust7) <= 5600);

const solo = { st: 'THREAT', last: [{ ttl: 1400 }] };
const pair = { st: 'DEFEND', last: [{ heal: true }, { ttl: 1000 }] };
const wave = { st: 'DEFEND', last: [{}, {}, {}, {}] };
const core = { st: 'THREAT', mission: 'core', last: [] };
const corePlus = { st: 'DEFEND', mission: 'core', last: [{ ttl: 500 }] };
assert.strictEqual(T.squadSize(solo), 1);
assert.strictEqual(T.squadSize(pair), 2);
// One smallRanged (3 RA) or one boosted small melee is still 1: the 5600 kite out-heals them.
assert.strictEqual(T.squadSize({ st: 'DEFEND', last: [{ ranged3: true }] }), 1);
assert.strictEqual(T.squadSize({ st: 'DEFEND', last: [{ boosted: true, ra: 1 }] }), 1);
assert.strictEqual(T.squadSize({ st: 'DEFEND', last: [{ ra: 6 }] }), 3, 'ranged-heavy (>=6 RA) is 3');
assert.strictEqual(T.squadSize({ st: 'DEFEND', last: [{ boosted: true }, { ttl: 800 }] }), 3, 'boosted pair is 3');
assert.strictEqual(T.squadSize(wave), 4);
assert.strictEqual(T.squadSize(core), 1);
assert.strictEqual(T.squadSize(corePlus), 4);
assert.strictEqual(T.squadSize({ st: 'SAFE', last: wave.last }), 0);
assert.strictEqual(T.squadSize({ st: 'DEFEND', last: solo.last, extra: 5 }), 4);

const thin = { name: 'W46N8', controller: { level: 7 }, energyCapacityAvailable: 5600, energyAvailable: 5600, storage: { store: { energy: 12000 } } };
const fat = { name: 'W46N8', controller: { level: 7 }, energyCapacityAvailable: 5600, energyAvailable: 5600, storage: { store: { energy: 20000 } } };
assert.strictEqual(S.extrasOk(thin), false);
assert.strictEqual(S.extrasOk(fat), true);
const soft = { name: 'W47N8', controller: { level: 7 }, storage: { store: { energy: 20000 } } };
Memory.ops.w8day = { softCap2: 1 };
assert.strictEqual(S.extrasOk(soft), false);
Memory.ops.w8day.softCap2 = 0;
assert.strictEqual(S.extrasOk(Object.assign({}, soft, { storage: { store: { energy: 16000 } } })), true);

// Body #1 is the max recipe for energyCapacityAvailable even when energyAvailable is short.
// The spawn holds and the queen fills; the body is not shrunk to leave sooner.
// The 15k floor does not block body #1. Extras still need it, and they hold the queue too.
{
  const orig = {
    wantDefender: T.wantDefender, armed: T.armed, state: T.state,
    squadAlive: T.squadAlive, squadSize: T.squadSize, energyHold: T.energyHold,
    coreMission: T.coreMission,
  };
  T.wantDefender = () => 'W45N8';
  T.armed = () => true;
  T.state = () => ({ st: 'THREAT', mission: 'solo', last: [{ ttl: 1400 }] });
  T.squadAlive = () => 0;
  T.squadSize = () => 1;
  T.energyHold = () => false;
  T.coreMission = () => false;
  try {
    const softRoom = { name: 'W46N8', controller: { level: 7 }, energyCapacityAvailable: 5600, energyAvailable: 4680, storage: { store: { energy: 12000 } } };
    const planSoft = S.planDefender(softRoom);
    assert.ok(planSoft, 'plan #1 under the 15k floor and a short pile');
    assert.strictEqual(planSoft.cost, 5600, 'body #1 is the max recipe, not ea 4680');
    assert.strictEqual(planSoft.body.length, 50);
    assert.strictEqual(planSoft.hold, true);
    // nearFull (5500/5600): home ext 31,34 is unfillable; size to the payable pile, do not deadlock.
    const near = Object.assign({}, softRoom, { energyAvailable: 5500 });
    const planNear = S.planDefender(near);
    assert.ok(planNear, 'plan #1 when the pile is nearFull');
    assert.strictEqual(planNear.cost, 5400, 'nearFull 5500/5600 sizes the kite to 18RA+6H+24M, not 5600');
    assert.strictEqual(planNear.body.filter(p => p === RANGED_ATTACK).length, 18);
    assert.strictEqual(planNear.body.filter(p => p === HEAL).length, 6);
    assert.strictEqual(planNear.body.filter(p => p === MOVE).length, 24);
    assert.strictEqual(planNear.hold, true);
    const planFull = S.planDefender(Object.assign({}, softRoom, { energyAvailable: 5600 }));
    assert.strictEqual(planFull.cost, 5600, 'a truly full pile still gets the 19RA max kite');
    T.squadAlive = () => 1;
    T.squadSize = () => 2;
    const blocked = S.planDefender(softRoom);
    assert.strictEqual(blocked, null, 'extra body still respects the 15k floor');
    const planExtra = S.planDefender(Object.assign({}, softRoom, { energyAvailable: 4680, storage: { store: { energy: 20000 } } }));
    assert.ok(planExtra, 'extra body plans under fat stor');
    assert.strictEqual(planExtra.cost, 5600, 'extra body still sized to full cap');
    assert.strictEqual(planExtra.hold, true, 'an owed extra holds non-defense spawns until it can be paid');
    T.coreMission = () => true;
    T.squadAlive = () => 0;
    T.squadSize = () => 1;
    const bust = S.planDefender(Object.assign({}, softRoom, { energyAvailable: 1300, storage: { store: { energy: 4000 } } }));
    assert.strictEqual(bust.core, 1);
    assert.strictEqual(bust.cost, 3250, 'core buster is 25 ATTACK + 25 MOVE, not the 1300 10+10');
    assert.strictEqual(bust.hold, true);
  } finally {
    Object.assign(T, orig);
  }
}

// A judged combat wave (healer + boosted ranged, four creeps) still spawns kite extras
// under the 15k home floor and the W47 softCap 25k floor. A solo's peacetime extra does not.
// The body is the 19 RA + 25 MOVE + 6 HEAL recipe, not a melee ATTACK body.
{
  const orig = {
    wantDefender: T.wantDefender, armed: T.armed, state: T.state,
    squadAlive: T.squadAlive, squadSize: T.squadSize, energyHold: T.energyHold,
    coreMission: T.coreMission,
  };
  const wave = { st: 'THREAT', mission: 'guard', last: [
    { attack: 1, ra: 1 }, { ra: 3 }, { ra: 3, boosted: true }, { heal: true, boosted: true },
  ]};
  T.wantDefender = () => 'W47N7';
  T.armed = () => true;
  T.energyHold = () => false;
  T.coreMission = () => false;
  T.state = () => wave;
  T.squadAlive = () => 1;
  T.squadSize = () => 4;
  try {
    Memory.ops.w8day = { softCap2: 1 };
    const broke = { name: 'W47N8', controller: { level: 7 }, energyCapacityAvailable: 5600, energyAvailable: 220, storage: { store: { energy: 0 } } };
    const plan = S.planDefender(broke);
    assert.ok(plan, 'extras spawn while W47 storage is 0 and softCap is on');
    assert.strictEqual(plan.cost, 5600);
    assert.strictEqual(plan.hold, true);
    assert.strictEqual(n(plan.body, ATTACK), 0, 'ranged+heal wave is a kite body, not melee');
    assert.strictEqual(n(plan.body, RANGED_ATTACK), 19);
    assert.strictEqual(n(plan.body, HEAL), 6);
    assert.strictEqual(n(plan.body, MOVE), 25);
    const home = { name: 'W46N8', controller: { level: 7 }, energyCapacityAvailable: 5600, energyAvailable: 2750, storage: { store: { energy: 12854 } } };
    const planH = S.planDefender(home);
    assert.ok(planH, 'extras spawn under the 15k home floor');
    assert.strictEqual(planH.cost, 5600);
    assert.strictEqual(n(planH.body, ATTACK), 0);
    T.state = () => ({ st: 'DEFEND', mission: 'solo', last: [{ ttl: 1400 }], extra: 1 });
    T.squadAlive = () => 1;
    T.squadSize = () => 2;
    assert.strictEqual(S.planDefender(home), null, 'a solo peacetime extra still respects the 15k floor');
  } finally {
    Object.assign(T, orig);
    Memory.ops.w8day = { softCap2: 0 };
  }
}

console.log('defender squad ok');
