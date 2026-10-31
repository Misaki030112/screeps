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
it('daily budget exhausted does not block solo/guard (Misaki: fight reserved Invaders)', () => {
  const soloR = run([[1, { inv: solo(), spawnsDay: C.maxPerDay }]]);
  assert.strictEqual(soloR.s.st, 'THREAT'); assert.strictEqual(soloR.s.mission, 'solo');
  const guardR = run([[1, { reserved: true, hereP: 1, spawnsDay: C.maxPerDay }]]);
  assert.strictEqual(guardR.s.st, 'THREAT'); assert.strictEqual(guardR.s.mission, 'guard');
});
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
it('lone invader core -> THREAT core -> DEFEND -> SAFE when the core is gone', () => {
  const r = run([[1, { core: true, corePos: [9, 42] }], [20, { core: true, def: 'spawning' }], [80, { core: true, def: 'out' }], [400, { core: true, def: 'out' }], [401, { core: false, def: 'out' }]]);
  assert.deepStrictEqual(r.states, ['THREAT', 'THREAT', 'DEFEND', 'DEFEND', 'SAFE']);
  assert.strictEqual(r.evs[0], 'threat:core');
  assert.strictEqual(r.s.st, 'SAFE');
  assert.deepStrictEqual(r.evs.filter(e => e === 'cleared:killed'), ['cleared:killed']);
});
it('core fight keeps THREAT/DEFEND with no vision while the buster is travelling', () => {
  const r = run([[1, { core: true, corePos: [9, 42] }], [40, { vis: false, def: 'spawning' }], [90, { vis: false, def: 'out' }], [200, { vis: false, def: 'out' }]]);
  assert.deepStrictEqual(r.states, ['THREAT', 'THREAT', 'DEFEND', 'DEFEND']);
  assert.strictEqual(r.s.mission, 'core');
});
it('core with a closed spawn gate -> WAIT that gate, then THREAT when it opens', () => {
  const closed = run([[1, { core: true, armed: false }]]);
  assert.strictEqual(closed.s.st, 'WAIT'); assert.strictEqual(closed.s.why, 'gate'); assert.strictEqual(closed.s.mission, 'core');
  assert.strictEqual(run([[1, { core: true, bucket: 1000 }]]).s.why, 'cpu');
  assert.strictEqual(run([[1, { core: true, deathsDay: 1 }]]).s.why, 'deaths');
  const re = run([[1, { core: true, armed: false }], [30, { core: true, armed: true }]]);
  assert.deepStrictEqual(re.states, ['WAIT', 'THREAT']); assert.strictEqual(re.s.mission, 'core');
});
it('core ignores maxPerDay budget (fight cores; do not WAIT while they chew containers)', () => {
  const r = run([[1, { core: true, spawnsDay: C.maxPerDay }]]);
  assert.strictEqual(r.s.st, 'THREAT'); assert.strictEqual(r.s.mission, 'core'); assert.strictEqual(r.evs[0], 'threat:core');
  // solo Invader also fights through budget (same Misaki rule as cores)
  assert.strictEqual(run([[1, { inv: solo(), spawnsDay: C.maxPerDay }]]).s.st, 'THREAT');
});
it('WAIT budget with mission=core re-arms to THREAT even without vision (projected core)', () => {
  const stuck = { st: 'WAIT', since: 1, why: 'budget', mission: 'core', corePos: [10, 44], until: 5000 };
  const r = run([[100, { vis: false, spawnsDay: C.maxPerDay }]], stuck);
  assert.strictEqual(r.s.st, 'THREAT'); assert.strictEqual(r.s.mission, 'core');
});
it('WAIT budget with live solo Invader re-arms to THREAT after budget exemption', () => {
  const stuck = { st: 'WAIT', since: 1, why: 'budget', until: 5000, last: solo(1400), seen: 1 };
  const r = run([[100, { inv: solo(1300), spawnsDay: C.maxPerDay }]], stuck);
  assert.strictEqual(r.s.st, 'THREAT'); assert.strictEqual(r.s.mission, 'solo');
});
it('core fight outlasts the creep defendTimeout and stops on coreDefendTimeout', () => {
  const r = run([[1, { core: true }], [10, { core: true, def: 'out' }], [600, { core: true, def: 'out' }], [10 + C.coreDefendTimeout + 1, { core: true, def: 'out' }]]);
  assert.strictEqual(r.states[2], 'DEFEND'); assert.strictEqual(r.s.st, 'WAIT'); assert.strictEqual(r.s.why, 'defend_timeout');
});
it('player creeps outrank a core: WAIT player, never a core buster and never a guard', () => {
  const r = run([[1, { reserved: true, core: true, hereP: 1, players: 1 }]]);
  assert.strictEqual(r.s.st, 'WAIT'); assert.strictEqual(r.s.why, 'player');
  assert.strictEqual(run([[1, { core: true, players: 1, hereP: 0 }]]).s.why, 'player'); // player on the route
});
it('solo DEFEND upgrades to core THREAT when the creep dies and a core remains', () => {
  const live = { st: 'DEFEND', since: 1, why: 'dispatched', mission: 'solo', def: 'd1', gone: 1, last: null, arrived: 1, early: true };
  const r = run([[50, { core: true, corePos: [9, 44], def: 'out' }]], live);
  assert.strictEqual(r.s.st, 'THREAT');
  assert.strictEqual(r.s.mission, 'core');
  assert.strictEqual(r.s.why, 'core');
  assert.strictEqual(r.s.def, undefined);
  assert.deepStrictEqual(r.s.corePos, [9, 44]);
});
it('solo THREAT with kite out upgrades to core (no DEFEND on a kite vs core)', () => {
  const live = { st: 'THREAT', since: 1, why: 'solo', mission: 'solo', def: 'd1' };
  const r = run([[10, { core: true, corePos: [9, 44], def: 'out' }]], live);
  assert.strictEqual(r.s.st, 'THREAT');
  assert.strictEqual(r.s.mission, 'core');
  assert.strictEqual(r.s.def, undefined);
});
it('solo invader still takes the ranged path when a core is also present', () => {
  assert.strictEqual(run([[1, { core: true, inv: solo() }]]).evs[0], 'threat:solo');
  assert.notStrictEqual(run([[1, { core: true, inv: solo() }]]).s.mission, 'core');
});
it('legacy WAIT why=core with vision re-arms to THREAT; blind timer still resumes', () => {
  const live = { st: 'WAIT', since: 1, why: 'core', until: 5000 };
  const seen = run([[10, { core: true }]], live);
  assert.strictEqual(seen.s.st, 'THREAT'); assert.strictEqual(seen.s.mission, 'core');
  const blind = run([[100, { vis: false }], [5000, { vis: false }]], { st: 'WAIT', since: 1, why: 'core', until: 5000 });
  assert.deepStrictEqual(blind.states, ['WAIT', 'SAFE']); assert.strictEqual(blind.evs.pop(), 'resume:core_recheck');
  const gone = run([[10, { core: false }]], { st: 'WAIT', since: 1, why: 'core', until: 5000 });
  assert.strictEqual(gone.s.st, 'SAFE'); assert.strictEqual(gone.evs.pop(), 'resume:core_gone');
});
it('core DEFEND does not early-resume miners (no creep HP to read)', () => {
  assert.strictEqual(T.earlyNext({ st: 'DEFEND', mission: 'core', last: null }, true), false);
  assert.strictEqual(T.earlyNext({ st: 'DEFEND', mission: 'solo', last: null }, true), true);
});
it('energyHold collects 1300 while a core is waiting on the energy gate', () => {
  global.Memory = { remote: { W45N7: { needE: true, th: { st: 'WAIT', why: 'gate', mission: 'core' } } } };
  global.Game = global.Game || { time: 1, rooms: {}, creeps: {} };
  assert.strictEqual(T.energyHold('W46N8'), true);
  Memory.remote.W45N7.th.mission = 'solo'; Memory.remote.W45N7.th.last = [];
  assert.strictEqual(T.energyHold('W46N8'), false);
});
it('a player appearing mid core fight aborts to WAIT player', () => {
  const r = run([[1, { core: true }], [20, { core: true, def: 'out' }], [30, { core: true, def: 'out', hereP: 1, players: 1 }]]);
  assert.strictEqual(r.states[1], 'DEFEND'); assert.strictEqual(r.s.st, 'WAIT'); assert.strictEqual(r.s.why, 'player');
  assert.notStrictEqual(r.s.mission, 'core');
});
it('WAIT on NPC ends early when vision shows the room clear', () => assert.deepStrictEqual(run([[1, { inv: solo(), armed: false }], [500, { inv: [] }]]).states, ['WAIT', 'SAFE']));
it('WAIT timer ends without vision', () => assert.deepStrictEqual(run([[1, { inv: solo(100), armed: false }], [180, { vis: false }], [182, { vis: false }]]).states, ['WAIT', 'WAIT', 'SAFE']));
it('memory loss / global reset: missing state starts SAFE and re-detects next tick', () => { assert.strictEqual(T.step(undefined, base({ inv: solo() }), C, 5).s.st, 'THREAT'); assert.strictEqual(T.step({}, base({}), C, 5).s.st, 'SAFE'); });
it('step is pure (does not mutate input state)', () => { const s = { st: 'SAFE', since: 1 }; T.step(s, base({ inv: solo() }), C, 2); assert.deepStrictEqual(s, { st: 'SAFE', since: 1 }); });
it('disarmed mid-THREAT/DEFEND -> WAIT gate (defender recycles)', () => {
  assert.deepStrictEqual(run([[1, { inv: solo() }], [2, { inv: solo(), armed: false, def: 'spawning' }]]).states, ['THREAT', 'WAIT']);
  assert.deepStrictEqual(run([[1, { inv: solo() }], [2, { inv: solo(), def: 'out' }], [3, { inv: solo(), armed: false, def: 'out' }]]).states, ['THREAT', 'DEFEND', 'WAIT']); });
it('player inside a room we reserve -> THREAT guard, then DEFEND (not a 1500 wait)', () => {
  const r = run([[1, { reserved: true, hereP: 1, players: 1 }], [2, { reserved: true, hereP: 1, players: 1, def: 'out' }]]);
  assert.strictEqual(r.states[0], 'THREAT'); assert.strictEqual(r.evs[0], 'threat:guard'); assert.strictEqual(r.s.st, 'DEFEND');
});
it('player only on the route or in the colony -> still WAIT player, even if the remote is reserved', () => {
  assert.strictEqual(run([[1, { reserved: true, hereP: 0, players: 1 }]]).s.why, 'player');
});
it('escalated invaders in a reserved room -> guard; unreserved stays wait-out', () => {
  assert.strictEqual(run([[1, { reserved: true, inv: solo().concat(solo()) }]]).s.why, 'guard');
  assert.strictEqual(run([[1, { inv: solo().concat(solo()) }]]).s.why, 'escalated');
});
it('dismantler (WORK, no attack) in a reserved room -> guard', () => {
  assert.strictEqual(run([[1, { reserved: true, work: 1 }]]).s.why, 'guard');
});
it('guard stays DEFEND past defendTimeout while hostiles remain', () => {
  const r = run([[1, { reserved: true, hereP: 1, players: 1 }], [2, { reserved: true, hereP: 1, players: 1, def: 'out' }], [900, { reserved: true, hereP: 1, players: 1, def: 'out' }]]);
  assert.strictEqual(r.s.st, 'DEFEND');
});
it('invader core is not a guard target when players are present', () => {
  assert.strictEqual(run([[1, { reserved: true, core: true, hereP: 1, players: 1 }]]).s.why, 'player');
  assert.notStrictEqual(run([[1, { reserved: true, core: true, hereP: 1, players: 1 }]]).s.st, 'THREAT');
});
it('short-TTL invader stays wait-out even when the room is reserved', () => {
  assert.strictEqual(run([[1, { reserved: true, inv: solo(200) }]]).s.why, 'short_ttl');
});
it('solo invader in a reserved room keeps the solo path', () => {
  assert.strictEqual(run([[1, { reserved: true, inv: solo() }]]).evs[0], 'threat:solo');
});
it('no vision keeps a reserved-room guard alive so the defender can arrive', () => {
  const r = run([[1, { reserved: true, hereP: 2, players: 2 }], [80, { vis: false, reserved: true, def: 'out' }]]);
  assert.strictEqual(r.states[0], 'THREAT'); assert.strictEqual(r.s.st, 'DEFEND');
});
it('lost vision longer than foeMemory drops the guard', () => {
  const r = run([[1, { reserved: true, hereP: 1, players: 1, def: 'out' }], [2, { reserved: true, hereP: 1, players: 1, def: 'out' }], [250, { vis: false, reserved: true, def: 'out' }]]);
  assert.strictEqual(r.states[1], 'DEFEND'); assert.strictEqual(r.s.st, 'SAFE');
});
it('pickHome never sends a guard at W47N9; W47N7 homes on W47N8', () => {
  const R = require(path.join(__dirname, '..', 'src/managers/remote.js'));
  assert.strictEqual(R.pickHome('W47N7', ['W46N8', 'W47N8']), 'W47N8');
  assert.strictEqual(R.pickHome('W47N9', ['W47N8', 'W46N8']), null);
  assert.strictEqual(R.pickHome('W45N8', ['W46N8', 'W47N8']), 'W46N8');
  assert.strictEqual(R.pickHome('W43N8', ['W46N8']), null); // distance 3, out of range
});
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
it('armed() while the controller is still reserved by us, with no CLAIM2 creep', () => {
  const home = { controller: { level: 5 }, energyCapacityAvailable: 1800, energyAvailable: 200, memory: { lastFull: 100 }, storage: { store: { energy: 2000 } } };
  global.Memory = { username: 'Misaki', remote: { W45N8: { res: { username: 'Misaki', ticksToEnd: 900 }, seen: 8000 } }, creeps: {}, defense: { remoteDefender: true }, ops: {} };
  global.Game = { time: 8000, rooms: { W46N8: home, W47N8: home }, creeps: {} };
  const R = require(path.join(__dirname, '..', 'src/managers/remote.js')); R.CFG.W45N8.defend = true;
  assert.strictEqual(T.armed('W45N8'), true, 'reservation alone keeps the defender armed');
  Memory.remote.W45N8.res = { username: 'Cody132', ticksToEnd: 900 };
  assert.strictEqual(T.armed('W45N8'), false, 'foreign reservation does not arm');
  Memory.ops.r7 = { by: 'Misaki', endTime: 9000 };
  assert.strictEqual(T.armed('W47N7'), true, 'W47N7 reservation (ops.r7) arms the colony defender');
  Memory.ops.r7.by = 'BustJetter';
  assert.strictEqual(T.armed('W47N7'), false, 'someone else holding W47N7 does not arm us');
  assert.strictEqual(T.reservedByUs('W47N9'), false);
});
it('armed() busts a core in a configured remote after the reservation is gone; W47N9 stays dark', () => {
  const home = { controller: { level: 5 }, energyCapacityAvailable: 1800, energyAvailable: 200, memory: { lastFull: 100 }, storage: { store: { energy: 2000 } }, find: () => [] };
  const coreRoom = { name: 'W45N7', find: t => t === FIND_HOSTILE_STRUCTURES ? [{ structureType: STRUCTURE_INVADER_CORE, pos: { x: 9, y: 42 } }] : [] };
  global.Memory = { username: 'Misaki', remote: { W45N7: {} }, creeps: {}, defense: { remoteDefender: true }, ops: {} };
  global.Game = { time: 88000, cpu: { bucket: 10000 }, rooms: { W46N8: home, W45N7: coreRoom, W47N9: coreRoom }, creeps: {} };
  const R = require(path.join(__dirname, '..', 'src/managers/remote.js'));
  assert.strictEqual(T.armed('W45N7'), true, 'configured remote with a core stays armed without a reservation');
  coreRoom.find = () => [];
  assert.strictEqual(T.armed('W45N7'), false, 'no core and no reservation does not arm');
  coreRoom.find = t => t === FIND_HOSTILE_STRUCTURES ? [{ structureType: STRUCTURE_INVADER_CORE, pos: { x: 9, y: 42 } }] : [];
  Game.time = 88001;
  Game.rooms.W47N7 = { name: 'W47N7', find: coreRoom.find };
  assert.ok(R.cfgFor('W47N7'), 'W47N7 core keeps the guard config after the reservation drops');
  assert.strictEqual(R.cfgFor('W47N9'), null, 'W47N9 is never a core target');
  assert.strictEqual(T.reservedByUs('W47N9'), false);
  assert.strictEqual(T.armed('W47N9'), false);
});
for (const [n, f] of cases) { try { f(); pass++; console.log('ok   ' + n); } catch (e) { console.log('FAIL ' + n + '\n     ' + e.message); } }
console.log(`${pass}/${cases.length} passed`); if (pass !== cases.length) process.exit(1);
