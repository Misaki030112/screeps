// W47N9 wartime raid: east-line formation, memory knobs, spawn split, civilian pause.
// node tests/raid9.js
const assert = require('assert'), fs = require('fs'), path = require('path');
const L = require('lodash');
const _ = Object.assign({}, L, {
  min: (a, f) => (f ? (L.minBy ? L.minBy(a, f) : L.min(a, f)) : L.min(a)),
  sum: (a, f) => (f ? (L.sumBy ? L.sumBy(a, f) : L.sum(a, f)) : L.sum(a)),
});
Object.assign(global, {
  _: _, TOUGH: 'tough', WORK: 'work', ATTACK: 'attack', MOVE: 'move', RANGED_ATTACK: 'ranged_attack', HEAL: 'heal',
  FIND_HOSTILE_CREEPS: 'hostile', Memory: {}, Game: { time: 1, creeps: {}, spawns: {} },
});
const R = require(path.join(__dirname, '..', 'src', 'roles', 'raid9.js'));
const src = fs.readFileSync(path.join(__dirname, '..', 'src', 'roles', 'raid9.js'), 'utf8');
const spawnSrc = fs.readFileSync(path.join(__dirname, '..', 'src', 'managers', 'spawn.js'), 'utf8');
const colSrc = fs.readFileSync(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'index.js'), 'utf8');
assert.ok(!src.includes('.activateSafeMode('), 'raid must never activate safe mode');
assert.ok(spawnSrc.indexOf('wantSpawn(room, avail)') > spawnSrc.lastIndexOf('remoteSpawn'), 'home raid follows remote logistics');
assert.ok(colSrc.indexOf('wantSpawn(room, avail)') > colSrc.indexOf("want = 'w8rminer'"), 'colony raid follows rminer');
assert.ok(!spawnSrc.includes('ERR_NOT_ENOUGH_ENERGY;\n    const rv = spawn.spawnCreep(w.body'));

const P = (x, y) => ({ x, y });
const cost = { tough: 10, attack: 80, move: 50, work: 100, ranged_attack: 150, heal: 250 };
const c = b => b.reduce((a, p) => a + cost[p], 0);
assert.strictEqual(R.DISMANTLER().length, 50);
assert.strictEqual(c(R.DISMANTLER()), 3620);
assert.deepStrictEqual(R.DISMANTLER().slice(0, 2).concat(R.DISMANTLER().filter(p => p === 'work').length, R.DISMANTLER().filter(p => p === 'move').length), ['tough', 'tough', 24, 24]);
assert.strictEqual(c(R.MELEE()), 3140);
assert.strictEqual(R.MELEE().length, 50);
assert.strictEqual(c(R.RANGED()), 3250);
assert.strictEqual(R.RANGED().filter(p => p === 'ranged_attack').length, 15);
assert.strictEqual(c(R.HEALER()), 5400);
assert.strictEqual(R.HEALER().length, 36);
// RCL7 cap 5300 cannot spawn 18H18M; the live body is the largest 1:1 that fits.
assert.strictEqual(c(R.healBody(5300)), 5100);
assert.strictEqual(R.healBody(5300).length, 34);
assert.strictEqual(R.bodyFor('d', 5300).length, 50);
assert.strictEqual(R.bodyFor('d', 2300), null);
assert.deepStrictEqual(R.MAX, { d: 4, m: 6, r: 6, h: 10 });
assert.deepStrictEqual(R.NEED, { d: 1, m: 1, r: 0, h: 1 });
assert.deepStrictEqual(R.ENTRY, { x: 38, y: 49 });
assert.strictEqual(R.MIN_DPS, 1240);
assert.strictEqual(R.DPS_ONE, 1200);

const room = (name, avail, cap) => ({ name, energyAvailable: avail, energyCapacityAvailable: cap == null ? 5300 : cap });
Memory.ops = { w47n9: { on: true } };
Game.creeps = {};
assert.strictEqual(R.wantSpawn(room('W45N8', 8000)), null);
assert.strictEqual(R.wantSpawn(room('W46N8', 8000)).mem.kind, 'm', 'squad: attack first when tied');
assert.strictEqual(R.wantSpawn(room('W47N8', 8000)).mem.kind, 'm', 'squad shared roster — attack still first');
// with one m alive, next is d
Game.creeps = { c0: { memory: { role: 'raid9', kind: 'm', k: 0 } } };
assert.strictEqual(R.wantSpawn(room('W46N8', 8000)).mem.kind, 'd', 'squad: d after m');
Game.creeps = { c0: { memory: { role: 'raid9', kind: 'm', k: 0 } }, c1: { memory: { role: 'raid9', kind: 'd', k: 0 } } };
assert.strictEqual(R.wantSpawn(room('W47N8', 8000)).mem.kind, 'h', 'squad: h completes the trio');
assert.strictEqual(R.wantSpawn(room('W47N8', 8000)).body.length, 34, 'colony healer fits RCL7');
Game.creeps = {};
const defer = R.wantSpawn(room('W46N8', 500));
assert.strictEqual(defer.defer, true);
assert.strictEqual(defer.mem.kind, 'm');
assert.ok(defer.cost > 500);
Memory.ops.w47n9.pauseSpawn = true;
assert.strictEqual(R.wantSpawn(room('W46N8', 8000)), null);
delete Memory.ops.w47n9.pauseSpawn;

const got = { d: 0, m: 0, r: 0, h: 0 }, seq = [];
Game.creeps = {};
Game.time = 1;
for (let i = 0; i < 40; i++) {
  const rm = i % 2 === 0 ? room('W46N8', 8000) : room('W47N8', 8000);
  const w = R.wantSpawn(rm);
  if (!w || w.defer) break;
  seq.push((rm.name === 'W46N8' ? 'H' : 'C') + w.mem.kind);
  got[w.mem.kind]++;
  Game.creeps['c' + i] = { memory: w.mem };
  R.noteSpawned();
}
assert.deepStrictEqual(got, { d: 4, m: 6, r: 6, h: 10 });
assert.strictEqual(seq[0], 'Hm', 'squad starts with attack');
assert.ok(seq[1] === 'Cd' || seq[1] === 'Cm', 'colony fills next scarcest');
assert.strictEqual(R.wantSpawn(room('W46N8', 8000)), null);
assert.strictEqual(R.wantSpawn(room('W47N8', 8000)), null);
assert.ok(Memory.ops.w47n9.n >= 26);
// a death frees a slot; stream does not wait for a wave
delete Game.creeps.c0;
const refill = R.wantSpawn(room('W47N8', 8000));
assert.ok(refill && !refill.defer && (refill.mem.kind === 'm' || refill.mem.kind === 'd' || refill.mem.kind === 'h'));

Memory.ops.w47n9.garrison = true;
assert.strictEqual(R.wantSpawn(room('W46N8', 8000)), null);
assert.ok(!R.pauseCivilians(), 'garrison stands the economy back up');
delete Memory.ops.w47n9.garrison;
Memory.ops.w47n9.safe = 1;
assert.strictEqual(R.wantSpawn(room('W46N8', 8000)), null);
delete Memory.ops.w47n9.safe;
assert.ok(R.pauseCivilians(), 'on pauses civilians');
Memory.ops.w47n9.pauseCivilians = false;
assert.ok(!R.pauseCivilians(), 'explicit false keeps development');
Memory.ops.w47n9.on = false;
Memory.ops.w47n9.pauseCivilians = true;
assert.ok(R.pauseCivilians(), 'explicit flag pauses even if on is false');
delete Memory.ops.w47n9.pauseCivilians;
assert.ok(!R.pauseCivilians());

// 14:4x wartime storage floors — missing storage still allows spawn (legacy tests); thin stor blocks.
Memory.ops.w47n9 = { on: true };
Game.creeps = {};
assert.strictEqual(R.WAR_STOR.home, 12000);
assert.strictEqual(R.WAR_STOR.stage, 15000);
assert.ok(R.warStorOk(room('W46N8', 8000)), 'no storage → allow');
const thinHome = Object.assign(room('W46N8', 8000), { storage: { store: { energy: 11000 } } });
assert.ok(!R.warStorOk(thinHome), 'home under 12k blocks');
assert.strictEqual(R.wantSpawn(thinHome), null, 'wantSpawn null under home floor');
const okHome = Object.assign(room('W46N8', 8000), { storage: { store: { energy: 13000 } } });
assert.ok(R.warStorOk(okHome));
assert.strictEqual(R.wantSpawn(okHome).mem.kind, 'm', 'squad: attack first above floor');
const thinCol = Object.assign(room('W47N8', 8000), { storage: { store: { energy: 14000 } } });
assert.strictEqual(R.wantSpawn(thinCol), null, 'colony under 15k blocks');
const okCol = Object.assign(room('W47N8', 8000), { storage: { store: { energy: 20000 } } });
assert.strictEqual(R.wantSpawn(okCol).mem.kind, 'm', 'squad shared: attack first');
Memory.ops.w47n9.storFloorHome = 5000;
assert.ok(R.wantSpawn(thinHome).mem.kind === 'm', 'storFloorHome override');
delete Memory.ops.w47n9.storFloorHome;

const Tgt = { builder: 4, upgrader: 2, hauler: 1 };
Memory.ops.w47n9 = { on: true };
R.applyPause(Tgt, { controller: { ticksToDowngrade: 100000 } });
assert.strictEqual(Tgt.builder, 0);
assert.strictEqual(Tgt.upgrader, 0);
assert.strictEqual(Tgt.hauler, 1, 'logistics target untouched');
const Tlow = { builder: 2, upgrader: 2 };
R.applyPause(Tlow, { controller: { ticksToDowngrade: 5000 } });
assert.strictEqual(Tlow.upgrader, 1, 'one upgrader while the controller can downgrade');
assert.deepStrictEqual(R.namesToRecycle([
  { name: 'u1', role: 'w8upgrader', ttl: 100, spawning: false },
  { name: 'u2', role: 'w8upgrader', ttl: 800, spawning: false },
  { name: 'b1', role: 'w8builder', ttl: 400, spawning: false },
  { name: 'm1', role: 'w8miner', ttl: 1000, spawning: false },
], 1), ['u1', 'b1']);
assert.deepStrictEqual(R.namesToRecycle([
  { name: 'u2', role: 'w8upgrader', ttl: 800 },
  { name: 'b1', role: 'w8builder', ttl: 10 },
], 0), ['u2', 'b1']);

Game.spawns = { Spawn1: { my: true, pos: { roomName: 'W46N8', x: 35, y: 28 }, recycleCreep(c) { c.recycled = true; } } };
const bld = { memory: { role: 'builder', home: 'W46N8' }, pos: { roomName: 'W46N8', x: 10, y: 10, isNearTo() { return false; } }, moveTo() { this.moved = true; } };
assert.strictEqual(R.recycleCivilian(bld), true);
assert.ok(bld.moved);
bld.pos.isNearTo = () => true;
assert.strictEqual(R.recycleCivilian(bld), true);
assert.ok(bld.recycled);
assert.strictEqual(R.recycleCivilian({ memory: { role: 'hauler' }, pos: bld.pos }), false);

// mouths: 1200 dps cannot beat 1240 repair, so 2 dismantlers stack on one seal. A single is never assigned.
const one = R.assignSeals(1, R.MOUTH_DUAL, 1240, 1200, 2);
assert.strictEqual(one.open.length, 0);
const two = R.assignSeals(2, R.MOUTH_DUAL, 1240, 1200, 2);
assert.strictEqual(two.open.length, 1);
assert.strictEqual(two.open[0].n, 2);
assert.strictEqual(two.open[0].x, 38);
const wide = R.assignSeals(4, R.MOUTH_WIDE, 1240, 1200, 2);
assert.strictEqual(wide.open.length, 1, 'y43 cap 2 covers one mouth');
const opened = R.assignSeals(4, R.MOUTH_WIDE, 1240, 1200, 4);
assert.strictEqual(opened.open.length, 2);
assert.deepStrictEqual(opened.open.map(m => m.x), [37, 38]);
const posts = R.assignment([
  { id: 'd0', kind: 'd', k: 0 }, { id: 'd1', kind: 'd', k: 1 }, { id: 'd2', kind: 'd', k: 2 },
  { id: 'm0', kind: 'm', k: 0 }, { id: 'r0', kind: 'r', k: 0 }, { id: 'h0', kind: 'h', k: 0 }, { id: 'h1', kind: 'h', k: 1 },
], { mouths: R.MOUTH_DUAL, minDps: 1240, dps: 1200, maxY43: 2 });
assert.strictEqual(posts.posts.d0.y, 43);
assert.strictEqual(posts.posts.d1.y, 43);
assert.notStrictEqual(posts.posts.d0.x, posts.posts.d1.x);
assert.strictEqual(posts.posts.d2.y, 45);
assert.strictEqual(posts.posts.m0.y, 44);
assert.strictEqual(posts.posts.r0.y, 46);
assert.ok(posts.posts.h0.y === 47 || posts.posts.h0.y === 48);
assert.ok(!(posts.posts.h0.x === 38 && posts.posts.h0.y === 47));
assert.ok(!(posts.posts.h1.x === 38 && posts.posts.h1.y === 47));
assert.deepStrictEqual(R.swampStep({ x: 38, y: 47 }, { x: 38, y: 43 }), { x: 37, y: 47 });
assert.deepStrictEqual(R.swampStep({ x: 38, y: 47 }, { x: 40, y: 43 }), { x: 39, y: 47 });
assert.strictEqual(R.swampStep({ x: 38, y: 46 }, { x: 38, y: 43 }), null);
assert.ok(R.stepOntoSwamp({ x: 38, y: 48 }, { x: 38, y: 43 }));
assert.ok(!R.stepOntoSwamp({ x: 37, y: 47 }, { x: 39, y: 43 }));

assert.strictEqual(R.pullMode(0.8, 0.7, 0.45), null);
assert.strictEqual(R.pullMode(0.7, 0.7, 0.45), 'soft');
assert.strictEqual(R.pullMode(0.45, 0.7, 0.45), 'hard');
assert.ok(R.shouldYield({ x: 38, y: 44 }, 'r', [{ kind: 'd', pos: { x: 38, y: 46 } }], { x: 38, y: 42 }));
assert.ok(!R.shouldYield({ x: 38, y: 46 }, 'r', [{ kind: 'd', pos: { x: 38, y: 44 } }], { x: 38, y: 42 }));
assert.ok(!R.shouldYield({ x: 38, y: 44 }, 'd', [{ kind: 'd', pos: { x: 38, y: 46 } }], { x: 38, y: 42 }));

const me = P(38, 44);
const fight = { id: 'F', pos: P(39, 42), hits: 400, armed: true, nearTower: false };
const filler = { id: 'C', pos: P(39, 37), hits: 200, armed: false, energy: 400, nearTower: true };
const tRamp = { id: 'TR', pos: P(39, 37), structureType: 'rampart', hits: 5000, towerTile: true };
const t1 = { id: 'T1', pos: P(39, 37), structureType: 'tower', hits: 3000 };
const t2 = { id: 'T2', pos: P(34, 28), structureType: 'tower', hits: 3000 };
const block = { id: 'BL', pos: P(38, 40), structureType: 'constructedWall', hits: 1000 };
const spawn = { id: 'S', pos: P(26, 29), structureType: 'spawn', hits: 5000 };
const road = { id: 'R', pos: P(38, 45), structureType: 'road', hits: 100 };
const seal = { id: 'BR', pos: P(38, 42), structureType: 'rampart', hits: 80000 };
const optIn = { phase: 'inside_towers', towerOrder: [{ x: 39, y: 37 }, { x: 34, y: 28 }] };
assert.strictEqual(R.pick(me, { creeps: [fight, filler], structs: [tRamp, t1, t2, block, spawn] }, optIn).id, 'F');
assert.strictEqual(R.pick(me, { creeps: [filler], structs: [tRamp, t1, spawn] }, optIn).id, 'C');
assert.strictEqual(R.pick(me, { creeps: [], structs: [tRamp, t1, block, spawn] }, optIn).id, 'TR');
assert.strictEqual(R.pick(me, { creeps: [], structs: [t2, t1, spawn] }, optIn).id, 'T1');
assert.strictEqual(R.pick(me, { creeps: [], structs: [block, spawn, road] }, optIn).id, 'BL');
assert.strictEqual(R.pick(me, { creeps: [], structs: [spawn, road] }, optIn).id, 'S');
assert.strictEqual(R.pick(me, { creeps: [fight], structs: [t1] }, Object.assign({ sticky: 'T1' }, optIn)).id, 'F', 'fight outranks a sticky tower');
assert.strictEqual(R.pick(me, { creeps: [], structs: [t1, spawn] }, Object.assign({ sticky: 'T1' }, optIn)).id, 'T1');
assert.strictEqual(R.pick(me, { creeps: [fight], structs: [seal] }, { phase: 'breach', mouth: { x: 38, y: 42 } }).id, 'BR');
assert.strictEqual(R.pick(me, { creeps: [fight], structs: [seal] }, { phase: 'punch', mouth: { x: 38, y: 42 } }).id, 'F');
assert.strictEqual(R.pick(me, { creeps: [], structs: [] }, { phase: 'breach', mouth: { x: 38, y: 42 } }), null);

const ops = {};
R.syncPhase(ops, { phase: 'breach' });
assert.strictEqual(ops.phase, 'breach');
R.syncPhase(ops, { phase: 'punch' });
assert.strictEqual(ops.phase, 'punch');
R.syncPhase(ops, { phase: 'breach' });
assert.strictEqual(ops.phase, 'punch', 'no regress');
ops.phase = 'inside_clean';
R.syncPhase(ops, { phase: 'punch' });
assert.strictEqual(ops.phase, 'inside_clean', 'operator can hold a later phase');
ops.flee = { t: 1, why: 'overrun' };
R.syncPhase(ops, { phase: 'inside_clean' });
assert.strictEqual(ops.phase, 'fallback');
const held = { phase: 'fallback' };
R.syncPhase(held, { phase: 'breach' });
assert.strictEqual(held.phase, 'fallback');
assert.strictEqual(R.observe({ structs: [seal], creeps: [] }, [{ x: 38, y: 42 }], []).phase, 'breach');
assert.strictEqual(R.observe({ structs: [], creeps: [] }, [{ x: 38, y: 42 }], []).phase, 'punch');
assert.strictEqual(R.observe({ structs: [t1], creeps: [] }, [{ x: 38, y: 42 }], [{ pos: { y: 40 }, inRoom: true }]).phase, 'inside_towers');
assert.strictEqual(R.observe({ structs: [spawn], creeps: [] }, [{ x: 38, y: 42 }], [{ pos: { y: 30 }, inRoom: true }]).phase, 'inside_clean');

Game.time = 50;
const creep = { memory: { raidOrder: { moveTo: { x: 38, y: 44 }, until: 49 } } };
assert.strictEqual(R.manualOrder(creep), null);
assert.ok(!creep.memory.raidOrder);
const hold = { memory: { raidOrder: { hold: true, until: 60 } } };
assert.strictEqual(R.manualOrder(hold).hold, true);
const cleared = { memory: { raidOrder: { clear: true, attack: 'x' } } };
assert.strictEqual(R.manualOrder(cleared), null);

const cr = (kind, roomName, x, y) => ({ memory: { role: 'raid9', kind }, room: { name: roomName }, pos: { x, y } });
// full squad 1d+1m+1h on lip
assert.ok(R.assaultReady([cr('d', 'W47N8', 38, 1), cr('m', 'W47N8', 37, 1), cr('h', 'W47N8', 39, 2)]));
assert.ok(R.assaultReady([cr('d', 'W47N9', 38, 45), cr('m', 'W47N8', 37, 1), cr('h', 'W47N8', 39, 2)]));
assert.ok(!R.assaultReady([cr('d', 'W47N8', 38, 1), cr('d', 'W47N8', 37, 1)]), 'no attack+heal');
assert.ok(!R.assaultReady([cr('d', 'W47N8', 38, 1), cr('h', 'W47N8', 38, 2)]), 'missing melee');
assert.ok(!R.assaultReady([cr('m', 'W47N8', 38, 1), cr('h', 'W47N8', 38, 2)]), 'missing dismantler');
// far from lip (y>3) does not count
assert.ok(!R.assaultReady([cr('d', 'W47N8', 38, 10), cr('m', 'W47N8', 37, 10), cr('h', 'W47N8', 39, 10)]));
assert.ok(!R.shouldRegroup([cr('d', 'W47N9', 38, 43)]));
assert.ok(R.shouldRegroup([cr('h', 'W47N8', 38, 2)]));
Game.time = 80;
const go = { on: true };
R.syncGo(go, [cr('d', 'W47N8', 38, 1), cr('m', 'W47N8', 37, 2), cr('h', 'W47N8', 39, 1)]);
assert.strictEqual(go.go, 80);
const stay = { on: true, go: 10 };
R.syncGo(stay, [cr('h', 'W47N9', 38, 47), cr('d', 'W46N8', 1, 1)]);
assert.strictEqual(stay.go, 10);
const reset = { on: true, go: 10 };
R.syncGo(reset, [cr('d', 'W46N8', 1, 1), cr('h', 'W47N8', 38, 2)]);
assert.ok(!reset.go);
assert.ok(R.useMass(P(5, 5), [{ pos: P(5, 6) }, { pos: P(6, 6) }, { pos: P(6, 5) }]));
const H = (id, x, y, hits, hitsMax = 1000) => ({ id, pos: P(x, y), hits, hitsMax });
assert.strictEqual(R.healPlan(H('me', 10, 10, 1000), []), null);
assert.strictEqual(R.healPlan(H('me', 10, 10, 900), [H('a', 11, 10, 1000)]).mode, 'heal');
assert.ok(R.armedParts([{ attack: 20, ranged: 20 }, { attack: 0, ranged: 0 }]) >= 40);
assert.ok(R.armedParts([{ attack: 0, ranged: 6 }]) < 40);
const focused = R.mouthsOf({ focusSeal: { x: 39, y: 42 }, mouths: [{ x: 38, y: 42 }, { x: 39, y: 42 }] }, 'breach');
assert.strictEqual(focused[0].x, 39);
assert.strictEqual(focused[1].x, 38);


// alternate spawn (squad off): under-cap d/m interleave (never fill-all-d then m)
Memory.ops.w47n9 = { on: true, squad: false, alternate: true, lastKind: 'd', max: { d: 6, m: 6, r: 0, h: 0 } };
assert.strictEqual(R.wantKind('W46N8', { d: 3, m: 0 }, { d: 6, m: 6, r: 0, h: 0 }, 5300), 'm', 'after d, next is m');
Memory.ops.w47n9.lastKind = 'm';
assert.strictEqual(R.wantKind('W46N8', { d: 3, m: 3 }, { d: 6, m: 6, r: 0, h: 0 }, 5300), 'd', 'after m, next is d when tied');
assert.strictEqual(R.wantKind('W46N8', { d: 2, m: 4 }, { d: 6, m: 6, r: 0, h: 0 }, 5300), 'd', 'fewer d wins');
Memory.ops.w47n9.alternate = false;
assert.strictEqual(R.wantKind('W46N8', { d: 3, m: 0 }, { d: 6, m: 6, r: 0, h: 0 }, 5300), 'd', 'prefer order when alternate off');
// squad on: tied d/m/h → attack first
Memory.ops.w47n9 = { on: true, squad: true };
assert.strictEqual(R.wantKind('W46N8', { d: 0, m: 0, h: 0 }, { d: 4, m: 4, r: 2, h: 4 }, 5300), 'm', 'squad tie → m');
assert.strictEqual(R.wantKind('W46N8', { d: 1, m: 1, h: 0 }, { d: 4, m: 4, r: 2, h: 4 }, 5300), 'h', 'squad completes trio');
assert.strictEqual(R.wantKind('W46N8', { d: 2, m: 2, h: 2 }, { d: 4, m: 4, r: 2, h: 4 }, 5300), 'm', 'squad next wave attack');
delete Memory.ops.w47n9;


// noOverrun default: armed hostiles do NOT auto-flee (Misaki 2026-11-04 — only SM aborts)
Memory.ops.w47n9 = { on: true, noOverrun: true };
assert.strictEqual(R.overrun({ find() { throw new Error('should not scan'); } }), false, 'noOverrun blocks before find');
Memory.ops.w47n9 = { on: true }; // undefined noOverrun => still OFF
assert.strictEqual(R.overrun({ find() { throw new Error('should not scan'); } }), false, 'default off');
// stale flee.why=overrun is scrubbed when noOverrun is on
Memory.ops.w47n9 = { on: true, noOverrun: true, flee: { t: 1, why: 'overrun' }, garrison: true, phase: 'fallback' };
assert.ok(R.clearStaleOverrun(Memory.ops.w47n9));
assert.ok(!Memory.ops.w47n9.flee);
assert.ok(!Memory.ops.w47n9.garrison);
assert.strictEqual(Memory.ops.w47n9.phase, 'breach');
// abort flee is NOT scrubbed
Memory.ops.w47n9 = { on: true, flee: { t: 1, why: 'abort' }, garrison: true, phase: 'fallback' };
assert.ok(!R.clearStaleOverrun(Memory.ops.w47n9));
assert.strictEqual(Memory.ops.w47n9.flee.why, 'abort');
// opt-in overrun still works when noOverrun===false
Memory.ops.w47n9 = { on: true, noOverrun: false, overrunMin: 40 };
assert.ok(R.overrun({ find() { return [{ getActiveBodyparts: (p) => p === 'attack' ? 25 : (p === 'ranged_attack' ? 20 : 0) }]; } }));
delete Memory.ops.w47n9;

// squad=false restores prefer order
Memory.ops.w47n9 = { on: true, squad: false };
Game.creeps = {};
assert.strictEqual(R.wantSpawn(room('W46N8', 8000)).mem.kind, 'd', 'squad off: home prefer d');
assert.strictEqual(R.wantSpawn(room('W47N8', 8000)).mem.kind, 'h', 'squad off: colony prefer h');
delete Memory.ops.w47n9;

console.log('raid9 ok');
