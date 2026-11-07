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
assert.strictEqual(T.squadSize({ st: 'DEFEND', last: [{ ranged3: true }] }), 3);
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

// 12h 2026-11-07: body #1 sizes to current ea (≥1300), not full RCL7 cap — peacetime soft
// economies rarely hit lastFull, so waiting for cost=5600 held the spawn forever on solo Invaders.
{
  const orig = {
    wantDefender: T.wantDefender, armed: T.armed, state: T.state,
    squadAlive: T.squadAlive, squadSize: T.squadSize, energyHold: T.energyHold,
  };
  T.wantDefender = () => 'W45N8';
  T.armed = () => true;
  T.state = () => ({ st: 'THREAT', mission: 'solo', last: [{ ttl: 1400 }] });
  T.squadAlive = () => 0;
  T.squadSize = () => 1;
  T.energyHold = () => false;
  try {
    const softRoom = { name: 'W46N8', controller: { level: 7 }, energyCapacityAvailable: 5600, energyAvailable: 4680, storage: { store: { energy: 19000 } } };
    const planSoft = S.planDefender(softRoom);
    assert.ok(planSoft, 'plan #1 under soft ea');
    assert.ok(planSoft.cost <= 4680, 'body #1 cost ' + planSoft.cost + ' must fit ea 4680 (not wait for 5600)');
    assert.ok(planSoft.cost >= 1300, 'body #1 still fight-capable');
    assert.strictEqual(planSoft.hold, true);
    const planFull = S.planDefender(Object.assign({}, softRoom, { energyAvailable: 5600 }));
    assert.strictEqual(planFull.cost, 5600, 'full ea still builds max body');
    // extras (have≥1) keep full-cap sizing
    T.squadAlive = () => 1;
    T.squadSize = () => 2;
    const planExtra = S.planDefender(Object.assign({}, softRoom, { energyAvailable: 4680, storage: { store: { energy: 20000 } } }));
    assert.ok(planExtra, 'extra body plans under fat stor');
    assert.strictEqual(planExtra.cost, 5600, 'extra body still sized to full cap');
    assert.strictEqual(planExtra.hold, false);
  } finally {
    Object.assign(T, orig);
  }
}

console.log('defender squad ok');
