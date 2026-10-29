// raid9 breach@39,42 targeting + continuous dual-room spawn. node tests/raid9.js
const assert = require('assert'), path = require('path');
Object.assign(global, { _: require('lodash'), TOUGH: 'tough', ATTACK: 'attack', MOVE: 'move', RANGED_ATTACK: 'ranged_attack', HEAL: 'heal', Memory: {}, Game: { time: 1, creeps: {} } });
const R = require(path.join(__dirname, '..', 'src', 'roles', 'raid9.js'));
const P = (x, y) => ({ x, y });
const me = P(39, 45);
const tower = { id: 'T', pos: P(39, 37), structureType: 'tower', hits: 3000 };
const tower2 = { id: 'T2', pos: P(34, 28), structureType: 'tower', hits: 3000 };
const spawn = { id: 'S', pos: P(26, 29), structureType: 'spawn', hits: 5000 };
const ext = { id: 'E', pos: P(20, 40), structureType: 'extension', hits: 1000 };
const road = { id: 'R', pos: P(25, 44), structureType: 'road', hits: 1000 };
const breachRamp = { id: 'BR', pos: P(39, 42), structureType: 'rampart', hits: 84000 };
const nearRamp = { id: 'NR', pos: P(40, 42), structureType: 'rampart', hits: 82000 };
const farRamp = { id: 'FR', pos: P(26, 29), structureType: 'rampart', hits: 84000 };
const feeder = { id: 'F', pos: P(35, 30), energy: 800, hits: 1700, armed: false };
const armed = { id: 'D', pos: P(38, 40), energy: 0, hits: 500, armed: true };

// 1) breach barrier beats towers/spawn/creeps
assert.deepStrictEqual(R.pick(me, { creeps: [armed, feeder], structs: [tower, spawn, ext, road, breachRamp, farRamp] }), { id: 'BR', pri: 1 });
assert.deepStrictEqual(R.pick(me, { creeps: [], structs: [nearRamp, tower] }), { id: 'NR', pri: 1 });
// 2) breach open -> towers before spawn/creeps
assert.deepStrictEqual(R.pick(me, { creeps: [armed, feeder], structs: [tower, tower2, spawn, ext, farRamp] }), { id: 'T', pri: 2 });
// 3) towers gone -> armed creeps before structures
assert.deepStrictEqual(R.pick(me, { creeps: [armed, feeder], structs: [spawn, ext, road] }), { id: 'D', pri: 3 });
assert.deepStrictEqual(R.pick(me, { creeps: [feeder], structs: [spawn, ext] }), { id: 'F', pri: 3 });
// 4) no creeps -> other structures (spawn preferred), roads/ramparts skipped
assert.deepStrictEqual(R.pick(me, { creeps: [], structs: [spawn, ext, road, farRamp] }), { id: 'S', pri: 4 });
assert.deepStrictEqual(R.pick(me, { creeps: [], structs: [ext, road] }), { id: 'E', pri: 4 });
assert.strictEqual(R.pick(me, { creeps: [], structs: [road, farRamp] }), null);
// ranged mass
assert.ok(R.useMass(P(5, 5), [{ pos: P(5, 7) }, { pos: P(7, 7) }, { pos: P(8, 8) }]));
assert.ok(!R.useMass(P(5, 5), [{ pos: P(5, 8) }]));
// bodies within caps
const cost = { tough: 10, attack: 80, move: 50, ranged_attack: 150, heal: 250 }, c = b => b.reduce((a, p) => a + cost[p], 0);
assert.ok(c(R.MELEE()) <= 2300 && c(R.RANGED()) <= 2300 && c(R.HEALER()) <= 2300);
assert.ok(R.MELEE().length <= 50 && R.HEALER().includes('heal'));
assert.strictEqual(R.WAVE, 6);
assert.deepStrictEqual(R.NEED, { m: 2, r: 2, h: 2 });
assert.deepStrictEqual(R.BREACH, { x: 39, y: 42 });
// continuous dual-room spawn: fill missing kinds until WAVE; both HOME and STAGE
Memory.ops = { w47n9: { on: true } };
Game.creeps = {};
assert.strictEqual(R.wantSpawn({ name: 'W45N8' }), null);
const kinds = [];
for (let i = 0; i < 10; i++) {
  const room = i % 2 === 0 ? { name: 'W46N8' } : { name: 'W47N8' };
  const w = R.wantSpawn(room);
  if (!w) break;
  kinds.push(w.mem.kind);
  const name = 'r' + i;
  Game.creeps[name] = { name, memory: w.mem };
  R.noteSpawned();
}
assert.deepStrictEqual(kinds, ['m', 'm', 'r', 'r', 'h', 'h']);
assert.strictEqual(R.wantSpawn({ name: 'W46N8' }), null);
assert.strictEqual(R.wantSpawn({ name: 'W47N8' }), null);
// death frees a spawn slot (continuous waves)
delete Game.creeps.r0;
const refill = R.wantSpawn({ name: 'W47N8' });
assert.ok(refill && refill.mem.kind === 'm');
// safe / garrison / flee stop spawning
Memory.ops.w47n9.garrison = true;
assert.strictEqual(R.wantSpawn({ name: 'W46N8' }), null);
delete Memory.ops.w47n9.garrison;
Memory.ops.w47n9.safe = 1;
assert.strictEqual(R.wantSpawn({ name: 'W46N8' }), null);
delete Memory.ops.w47n9.safe;
assert.ok(R.pauseCivilians());
Memory.ops.w47n9.on = false;
assert.ok(!R.pauseCivilians());
// heal plan
const H = (id, x, y, hits, hitsMax = 1000) => ({ id, pos: P(x, y), hits, hitsMax });
const meH = H('me', 10, 10, 1000);
assert.strictEqual(R.healPlan(meH, [H('a', 11, 10, 1000)]), null);
assert.deepStrictEqual(R.healPlan(H('me', 10, 10, 900), [H('a', 11, 10, 1000)]).id, 'me');
assert.strictEqual(R.healPlan(meH, [H('a', 13, 10, 500)]).mode, 'ranged');
// formation slots by kind
assert.deepStrictEqual(R.slotOf(0, 'm'), [38, 1]);
assert.deepStrictEqual(R.slotOf(1, 'm'), [39, 1]);
assert.deepStrictEqual(R.slotOf(0, 'r'), [38, 2]);
assert.deepStrictEqual(R.slotOf(0, 'h'), [40, 2]);
// garrison slots distinct
{ const gs = [0, 1, 2, 3, 4, 5].map(R.gSlotOf);
  assert.strictEqual(new Set(gs.map(String)).size, 6); }
// overrun
assert.ok(R.armedParts([{ attack: 0, ranged: 6 }, { attack: 0, ranged: 6 }]) >= 12);
assert.ok(R.armedParts([{ attack: 0, ranged: 6 }]) < 12);
// launch / regroup. creep = kind, room, x, y
const cr = (kind, room, x, y) => ({ memory: { role: 'raid9', kind }, room: { name: room }, pos: { x, y } });
assert.strictEqual(R.NEAR_EXIT, 3);
assert.strictEqual(R.LAUNCH, 2);
assert.ok(R.inAssaultZone(cr('m', 'W47N8', 10, 1)));
assert.ok(R.inAssaultZone(cr('h', 'W47N8', 41, R.NEAR_EXIT)));
assert.ok(R.inAssaultZone(cr('h', 'W47N9', 39, 45)));
assert.ok(!R.inAssaultZone(cr('m', 'W47N8', 38, R.NEAR_EXIT + 1)));
assert.ok(!R.inAssaultZone(cr('m', 'W46N8', 38, 1)));
// preferred: two melee on the lip, not on exact slots; healers still home / already in TARGET
{
  const alive = [cr('m', 'W47N8', 10, 1), cr('m', 'W47N8', 12, 1), cr('r', 'W46N8', 20, 20), cr('h', 'W47N9', 39, 45)];
  assert.ok(R.assaultReady(alive));
  assert.ok(!R.shouldRegroup(alive));
}
// one melee + one ranged on the lip is enough; a healer off-slot does not block
assert.ok(R.assaultReady([cr('m', 'W47N8', 38, 1), cr('r', 'W47N8', 5, 2), cr('h', 'W46N8', 1, 1)]));
// two ranged on the hold-back row
assert.ok(R.assaultReady([cr('r', 'W47N8', 38, 3), cr('r', 'W47N8', 39, 3)]));
// melee already in TARGET + ranged on the lip: do not require the melee to return to a slot
assert.ok(R.assaultReady([cr('m', 'W47N9', 39, 42), cr('r', 'W47N8', 38, 2)]));
// healers on exact slots do not count; one combat is not a wave
assert.ok(!R.assaultReady([cr('m', 'W47N8', 38, 1), cr('h', 'W47N8', 40, 2), cr('h', 'W47N8', 41, 2)]));
// combat still walking up (south of the lip / still home) does not launch
assert.ok(!R.assaultReady([cr('m', 'W47N8', 38, 4), cr('m', 'W47N8', 39, 4), cr('r', 'W46N8', 10, 10)]));
// old gate: healer already in TARGET used to block "all 6 on exact slots"
{
  const alive = [
    cr('m', 'W47N8', 38, 1), cr('m', 'W47N8', 39, 1),
    cr('r', 'W47N8', 38, 2), cr('r', 'W47N8', 39, 2),
    cr('h', 'W47N8', 40, 2), cr('h', 'W47N9', 39, 44),
  ];
  assert.ok(R.assaultReady(alive));
  Game.time = 100;
  const P = { on: true };
  R.syncGo(P, alive);
  assert.strictEqual(P.go, 100);
}
// live stall: 4 parked on y=1, short of WAVE, not on exact x — still launch
{
  Game.time = 100;
  const P = { on: true };
  R.syncGo(P, [cr('m', 'W47N8', 37, 1), cr('m', 'W47N8', 36, 1), cr('r', 'W47N8', 40, 1), cr('h', 'W47N8', 41, 1)]);
  assert.strictEqual(P.go, 100);
}
// one death, others still in the room or on the lip: keep go (even if alive < WAVE and target is briefly empty)
{
  const P = { on: true, go: 50 };
  R.syncGo(P, [cr('m', 'W47N9', 39, 43), cr('h', 'W47N8', 40, 2), cr('r', 'W46N8', 10, 10)]);
  assert.strictEqual(P.go, 50);
  const parked = { on: true, go: 50 };
  R.syncGo(parked, [cr('m', 'W47N8', 38, 1), cr('r', 'W47N8', 39, 1), cr('h', 'W47N8', 41, 1)]);
  assert.strictEqual(parked.go, 50);
}
// assault force gone (home / deep stage only, healers alone on the lip, or nobody left): clear go
{
  const P = { on: true, go: 50 };
  R.syncGo(P, [cr('m', 'W46N8', 10, 10), cr('r', 'W47N8', 25, 20)]);
  assert.ok(!P.go);
  const healers = { on: true, go: 50 };
  R.syncGo(healers, [cr('h', 'W47N8', 40, 2), cr('h', 'W47N8', 41, 1)]);
  assert.ok(!healers.go);
  const dead = { on: true, go: 50 };
  R.syncGo(dead, []);
  assert.ok(!dead.go);
}
// a creep still inside TARGET holds go, including a lone healer — do not abandon the breach
{
  const P = { on: true, go: 50 };
  R.syncGo(P, [cr('h', 'W47N9', 39, 44), cr('m', 'W46N8', 10, 10)]);
  assert.strictEqual(P.go, 50);
}
// safe / garrison do not launch; an existing go timestamp is not refreshed while the wave holds
{
  Game.time = 100;
  const held = { on: true, garrison: true };
  R.syncGo(held, [cr('m', 'W47N8', 38, 1), cr('m', 'W47N8', 39, 1)]);
  assert.ok(!held.go);
  const stamped = { on: true, go: 40 };
  R.syncGo(stamped, [cr('m', 'W47N8', 38, 1), cr('m', 'W47N8', 39, 1)]);
  assert.strictEqual(stamped.go, 40);
}
console.log('raid9 ok');
