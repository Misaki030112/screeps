// Unit tests for the pure threat FSM (src/managers/threat.js step/classify) + the enable gate (armed()).
// node tests/threat_fsm.js  -> exits 1 on failure
const path = require('path'), assert = require('assert');
global._ = { some: (o, f) => Object.values(o).some(f), filter: (o, f) => Object.values(o).filter(f) };
Object.assign(global, { HEAL: 'heal', RANGED_ATTACK: 'ranged_attack', CLAIM: 'claim', RESOURCE_ENERGY: 'energy', FIND_HOSTILE_CREEPS: 1, FIND_HOSTILE_STRUCTURES: 2, STRUCTURE_INVADER_CORE: 'invaderCore' });
const T = require(path.join(__dirname, '..', 'src/managers/threat.js'));
const C = Object.assign({}, T.DEF);
const solo = (ttl = 1400) => [{ x: 40, y: 49, ttl, heal: false, ranged3: false }];
const base = o => Object.assign({ vis: true, inv: [], players: 0, core: false, hurtNoInv: false, bucket: 10000, armed: true, def: 'none', spawnsDay: 0, deathsDay: 0 }, o);
let pass = 0; const cases = [];
const it = (name, f) => cases.push([name, f]);
// run a scripted sequence: [[tick, obs], ...] -> list of states, events
function run(seq, s0) { let s = s0 || null; const states = [], evs = []; for (const [t, o] of seq) { const r = T.step(s, base(o), C, t); s = r.s; states.push(s.st); evs.push(...r.ev.map(e => e.ev + ':' + e.why)); } return { s, states, evs }; }
it('quiet room stays SAFE', () => assert.deepStrictEqual(run([[1, {}], [2, {}]]).states, ['SAFE', 'SAFE']));
it('happy path SAFE->THREAT->DEFEND->SAFE(killed)', () => {
  const r = run([[100, { inv: solo() }], [101, { inv: solo(), vis: false }], [137, { vis: false, def: 'spawning' }], [140, { vis: false, def: 'out' }], [180, { inv: solo(1300), def: 'out' }], [230, { inv: [], def: 'out' }], [241, { inv: [], def: 'out' }]]);
  assert.deepStrictEqual(r.states, ['THREAT', 'THREAT', 'THREAT', 'DEFEND', 'DEFEND', 'DEFEND', 'SAFE']);
  assert.deepStrictEqual(r.evs, ['threat:solo', 'defend:dispatched', 'cleared:killed']);
});
it('gate closed (flag off / RCL<4 / no CLAIM2) -> WAIT wait-out, never THREAT', () => { const r = run([[1, { inv: solo(), armed: false }]]); assert.strictEqual(r.s.st, 'WAIT'); assert.strictEqual(r.s.why, 'gate'); assert.strictEqual(r.s.until, 1 + 1400 + C.waitBuffer); });
it('WAIT gate clears with solo still present -> THREAT (re-arm)', () => assert.deepStrictEqual(run([[1, { inv: solo(), armed: false }], [50, { inv: solo(1350), armed: true }]]).states, ['WAIT', 'THREAT']));
it('CPU bucket low -> WAIT cpu', () => assert.strictEqual(run([[1, { inv: solo(), bucket: 1000 }]]).s.why, 'cpu'));
it('daily budget exhausted -> WAIT budget', () => assert.strictEqual(run([[1, { inv: solo(), spawnsDay: C.maxPerDay }]]).s.why, 'budget'));
it('after a defender death today -> WAIT deaths', () => assert.strictEqual(run([[1, { inv: solo(), deathsDay: 1 }]]).s.why, 'deaths'));
it('WAIT deaths: death ages out of the day window with solo present -> THREAT (re-arm)', () => assert.deepStrictEqual(run([[1, { inv: solo(), deathsDay: 1 }], [50, { inv: solo(1350), deathsDay: 0 }]]).states, ['WAIT', 'THREAT']));
it('short TTL Invader not worth it -> WAIT', () => assert.strictEqual(run([[1, { inv: solo(200) }]]).s.why, 'short_ttl'));
it('healer / pair / 3xRA -> WAIT escalated', () => {
  assert.strictEqual(run([[1, { inv: [{ ttl: 1400, heal: true }] }]]).s.why, 'escalated');
  assert.strictEqual(run([[1, { inv: solo().concat(solo()) }]]).s.why, 'escalated');
  assert.strictEqual(run([[1, { inv: [{ ttl: 1400, ranged3: true }] }]]).s.why, 'escalated');
});
it('Invader dies/expires while defender spawning -> SAFE cancel (defender then recycles)', () => {
  const r = run([[1, { inv: solo() }], [20, { def: 'spawning', inv: [] }]]); assert.deepStrictEqual(r.evs, ['threat:solo', 'cancel:gone']);
});
it('no vision: last known TTL is projected; expiry -> cancel', () => {
  const r = run([[1, { inv: solo(400) }], [402, { vis: false }]]); assert.deepStrictEqual(r.evs, ['threat:solo', 'cancel:gone']);
  assert.strictEqual(run([[1, { inv: solo(400) }], [300, { vis: false }]]).s.why, 'short_ttl'); // projected TTL fell below minTtl: wait-out
});
it('readiness timeout (energy/spawn busy 200 ticks) -> WAIT timeout', () => {
  const r = run([[1, { inv: solo() }], [150, { inv: solo(1250) }], [202, { inv: solo(1200) }]]); assert.deepStrictEqual(r.states, ['THREAT', 'THREAT', 'WAIT']); assert.strictEqual(r.s.why, 'timeout');
});
it('spawning defender does not time out', () => assert.strictEqual(run([[1, { inv: solo() }], [205, { inv: solo(1200), def: 'spawning' }]]).s.st, 'THREAT'));
it('second Invader / healer arrives mid-fight -> WAIT escalated (defender recycles)', () => {
  const r = run([[1, { inv: solo() }], [40, { def: 'out', inv: solo() }], [60, { def: 'out', inv: solo().concat([{ ttl: 1500, heal: true }]) }]]); assert.strictEqual(r.s.st, 'WAIT'); assert.strictEqual(r.s.why, 'escalated');
});
it('player combat creep at any time -> WAIT player 1500, not cleared by vision', () => {
  const r = run([[1, { inv: solo() }], [40, { def: 'out', players: 1 }], [100, { players: 0 }], [1539, {}], [1541, {}]]); assert.deepStrictEqual(r.states, ['THREAT', 'WAIT', 'WAIT', 'WAIT', 'SAFE']);
});
it('our creep hurt with no Invader visible => treated as player', () => assert.strictEqual(run([[1, { hurtNoInv: true }]]).s.why, 'player'));
it('defender dies -> WAIT defender_died (deaths counter then blocks today)', () => {
  const r = run([[1, { inv: solo() }], [40, { def: 'out', inv: solo() }], [80, { def: 'dead', inv: solo(1300) }]]); assert.strictEqual(r.s.why, 'defender_died');
});
it('defender recycled (TTL) mid-fight -> WAIT defender_expired', () => assert.strictEqual(run([[1, { inv: solo() }], [40, { def: 'out', inv: solo() }], [80, { def: 'none', inv: solo() }]]).s.why, 'defender_expired'));
it('fight too long -> WAIT defend_timeout', () => assert.strictEqual(run([[1, { inv: solo() }], [40, { def: 'out', inv: solo() }], [500, { def: 'out', inv: solo(900) }]]).s.why, 'defend_timeout'));
it('invader core -> WAIT; stay WAIT while core visible past recheck; SAFE when gone', () => {
  const r = run([[1, { core: true }], [600, { core: true }], [1100, { core: true }], [1200, { core: false }]]);
  assert.deepStrictEqual(r.states, ['WAIT', 'WAIT', 'WAIT', 'SAFE']); assert.strictEqual(r.evs.pop(), 'resume:core_gone');
});
it('invader core WAIT: timer expiry without vision -> SAFE core_recheck (regain vision)', () => {
  // after t=600 extend until=1100; at 1100 with no vision resume so remotes can look again
  const r = run([[1, { core: true }], [600, { core: true }], [700, { vis: false }], [1100, { vis: false }]]);
  assert.deepStrictEqual(r.states, ['WAIT', 'WAIT', 'WAIT', 'SAFE']); assert.strictEqual(r.evs.pop(), 'resume:core_recheck');
});
it('invader core: SAFE recheck then core still there -> WAIT again', () => {
  const r = run([[1, { core: true }], [600, { core: true }], [1100, { vis: false }], [1150, { core: true }]]);
  assert.deepStrictEqual(r.states, ['WAIT', 'WAIT', 'SAFE', 'WAIT']); assert.strictEqual(r.s.why, 'core');
});
it('WAIT on NPC ends early when vision shows the room clear', () => assert.deepStrictEqual(run([[1, { inv: solo(), armed: false }], [500, { inv: [] }]]).states, ['WAIT', 'SAFE']));
it('WAIT timer ends without vision', () => assert.deepStrictEqual(run([[1, { inv: solo(100), armed: false }], [180, { vis: false }], [182, { vis: false }]]).states, ['WAIT', 'WAIT', 'SAFE']));
it('memory loss / global reset: missing state starts SAFE and re-detects next tick', () => { assert.strictEqual(T.step(undefined, base({ inv: solo() }), C, 5).s.st, 'THREAT'); assert.strictEqual(T.step({}, base({}), C, 5).s.st, 'SAFE'); });
it('step is pure (does not mutate input state)', () => { const s = { st: 'SAFE', since: 1 }; T.step(s, base({ inv: solo() }), C, 2); assert.deepStrictEqual(s, { st: 'SAFE', since: 1 }); });
it('disarmed mid-THREAT/DEFEND -> WAIT gate (defender recycles)', () => {
  assert.deepStrictEqual(run([[1, { inv: solo() }], [2, { inv: solo(), armed: false, def: 'spawning' }]]).states, ['THREAT', 'WAIT']);
  assert.deepStrictEqual(run([[1, { inv: solo() }], [2, { inv: solo(), def: 'out' }], [3, { inv: solo(), armed: false, def: 'out' }]]).states, ['THREAT', 'DEFEND', 'WAIT']); });
// armed() gate in Game context
it('armed(): flag + RCL4 stable 1500t + full + CLAIM2 reserver', () => {
  const home = { controller: { level: 4 }, energyCapacityAvailable: 1300, energyAvailable: 0, memory: { lastFull: 0 } };
  global.Memory = { remote: {}, creeps: {}, defense: { remoteDefender: true } }; global.Game = { time: 1000, rooms: { W46N8: home }, creeps: {} };
  const R = require(path.join(__dirname, '..', 'src/managers/remote.js')); R.CFG.W45N8.defend = true;
  home.memory.lastFull = 1000; assert.strictEqual(T.armed('W45N8'), false); // RCL4 just reached
  Game.time = 2600; home.memory.lastFull = 2590; assert.strictEqual(T.armed('W45N8'), false); // no CLAIM2
  Game.creeps.r = { memory: { role: 'reserver', remote: 'W45N8' }, getActiveBodyparts: () => 2 }; assert.strictEqual(T.armed('W45N8'), true);
  R.CFG.W45N8.defend = false; assert.strictEqual(T.armed('W45N8'), false); R.CFG.W45N8.defend = true;
  home.energyCapacityAvailable = 800; assert.strictEqual(T.armed('W45N8'), false); // lost RCL4 capacity resets the stability clock
  // RCL5 build: lastFull stale but energyAvailable covers defender cost -> still armed
  home.controller.level = 5; home.energyCapacityAvailable = 1800; home.energyAvailable = 1400;
  home.memory = {}; Game.time = 5000; assert.strictEqual(T.armed('W45N8'), true);
  home.energyAvailable = 400; assert.strictEqual(T.armed('W45N8'), false); // cannot afford and lastFull missing
  home.storage = { store: { [RESOURCE_ENERGY]: 1600 } }; assert.strictEqual(T.armed('W45N8'), true); // dual-remote: storage covers defender
  home.storage.store[RESOURCE_ENERGY] = 500; assert.strictEqual(T.armed('W45N8'), false); // storage too low
  home.storage = null; home.memory.lastFull = 4900; assert.strictEqual(T.armed('W45N8'), true); // recently near-full still counts
  delete Memory.defense; assert.strictEqual(T.armed('W45N8'), true); // default ON (Misaki 10:39: keep remote anti-Invader)
  Memory.defense = { remoteDefender: false }; assert.strictEqual(T.armed('W45N8'), false); // explicit off still works
});
for (const [n, f] of cases) { try { f(); pass++; console.log('ok   ' + n); } catch (e) { console.log('FAIL ' + n + '\n     ' + e.message); } }
console.log(`${pass}/${cases.length} passed`); if (pass !== cases.length) process.exit(1);
