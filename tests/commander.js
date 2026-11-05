// Commander overlay + duty rank (docs/COMMANDER.md). node tests/commander.js
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
const W = { objs: {} };
global.OK = 0;
global.RESOURCE_ENERGY = 'energy';
global.Game = { time: 5000, cpu: { bucket: 9000 }, getObjectById: id => W.objs[id] || null, creeps: {}, rooms: {}, spawns: {} };
global.Memory = { creeps: {}, ops: {} };
const cmd = require(src('utils/cmd.js'));
const intent = require(src('utils/intent.js'));
let n = 0;
const it = (name, fn) => { try { fn(); n++; } catch (e) { console.error('FAIL', name); throw e; } };
function reset(t) {
  W.objs = {};
  global.Memory = { creeps: {}, ops: {} };
  Game.time = t == null ? Game.time + 1 : t;
  intent.resetCache();
}
function pos(x, y) {
  return {
    x, y,
    getRangeTo(p) { const t = p.pos || p; return Math.max(Math.abs(this.x - t.x), Math.abs(this.y - t.y)); },
    isNearTo(p) { return this.getRangeTo(p) <= 1; },
  };
}
function creep(extra) {
  const c = {
    name: 'H', hits: 500, hitsMax: 500, said: [], moved: null, did: null, healed: null,
    memory: { role: 'hauler', working: true, dst: 'keep', raidOrder: { hold: 1 } },
    store: { energy: 0, getFreeCapacity: () => 0 },
    room: { name: 'W46N8', energyAvailable: 2000, energyCapacityAvailable: 2000, controller: { id: 'ctl' }, storage: null, memory: {}, find: () => [] },
    say(s) { this.said.push(s); },
    moveTo(p, o) { this.moved = { x: p.x, y: p.y, room: p.roomName || p.room, o }; },
    transfer(t, r, a) { this.did = ['transfer', t.id, r, a]; return 0; },
    rangedAttack(t) { this.did = ['rangedAttack', t.id]; return 0; },
    attack(t) { this.did = ['attack', t.id]; return 0; },
    heal(t) { this.healed = (t && t.id) || 'self'; return 0; },
    drop(r) { this.did = ['drop', r]; return 0; },
    getActiveBodyparts() { return 0; },
  };
  c.pos = pos(5, 5);
  return Object.assign(c, extra || {});
}
const duty = (role, sig) => intent.pick(role, sig).duty;
const quiet = { threat: 0, war: false, softCap: false, floor: 'ok', spawnPressure: false, remoteDefense: false, labs: false, repairDebt: false, bucketLow: false, hurt: false, combatBody: false };

it('unarmed consume does not create Memory.cmd', () => {
  reset(5100);
  const c = creep();
  assert.strictEqual(cmd.armed(), false);
  assert.strictEqual(cmd.consumeCreep(c), false);
  assert.strictEqual(Memory.cmd, undefined);
  assert.strictEqual(c.memory.raidOrder.hold, 1);
  assert.strictEqual(c.memory._cmd, undefined);
});

it('setCreep arms, default ttl 200, does not touch ops or raidOrder', () => {
  reset(5200);
  Memory.ops = { w47n9: { on: true, pauseCivilians: true }, w8day: { softCap2: 1 } };
  const o = cmd.setCreep('H', { act: 'idle', say: 'hi', by: 'test' });
  assert.strictEqual(Memory.cmd.on, 1);
  assert.strictEqual(o.ttl, 200);
  assert.strictEqual(o.until, 5400);
  assert.strictEqual(Memory.ops.w47n9.on, true);
  assert.strictEqual(Memory.ops.w8day.softCap2, 1);
  assert.strictEqual(Memory.creeps.H, undefined);
  const c = creep();
  Memory.creeps.H = c.memory;
  assert.strictEqual(cmd.consumeCreep(c), true);
  assert.deepStrictEqual(c.said, ['hi']);
  assert.strictEqual(c.memory._cmd, 1);
  assert.strictEqual(c.memory.role, 'hauler');
  assert.strictEqual(c.memory.working, true);
  assert.strictEqual(c.memory.dst, 'keep');
  assert.deepStrictEqual(c.memory.raidOrder, { hold: 1 });
  assert.strictEqual(cmd.consumeCreep(c), true);
  assert.strictEqual(c.said.length, 1, 'same tick does not run the act twice');
});

it('disarm ignores orders but keeps them; arm resumes; release clears only the order', () => {
  reset(5300);
  const c = creep();
  Memory.creeps.H = c.memory;
  Memory.ops.w47n9 = { on: false };
  cmd.setCreep('H', { act: 'idle', ttl: 50 });
  assert.strictEqual(cmd.consumeCreep(c), true);
  assert.strictEqual(cmd.disarm(), true);
  assert.strictEqual(cmd.consumeCreep(c), false);
  assert.ok(Memory.cmd.c.H);
  assert.strictEqual(c.memory._cmd, undefined);
  assert.strictEqual(cmd.arm(), true);
  assert.strictEqual(cmd.consumeCreep(c), true);
  assert.strictEqual(cmd.releaseCreep('H'), true);
  assert.strictEqual(Memory.cmd.c.H, undefined);
  assert.strictEqual(cmd.consumeCreep(c), false);
  assert.strictEqual(c.memory._cmd, undefined);
  assert.deepStrictEqual(c.memory.raidOrder, { hold: 1 });
  assert.strictEqual(Memory.ops.w47n9.on, false);
});

it('ttl expiry deletes the order and resumes', () => {
  reset(5400);
  const c = creep();
  cmd.setCreep('H', { act: 'say', say: 'z', ttl: 10 });
  assert.strictEqual(cmd.consumeCreep(c), true);
  Game.time = 5410;
  assert.strictEqual(cmd.consumeCreep(c), false);
  assert.strictEqual(Memory.cmd.c.H, undefined);
  assert.strictEqual(c.memory._cmd, undefined);
});

it('sticky ignores the clock; malformed on:1 without a deadline is dropped', () => {
  reset(5500);
  const c = creep();
  cmd.setCreep('H', { act: 'idle', sticky: 1 });
  Game.time = 9000;
  assert.strictEqual(cmd.consumeCreep(c), true);
  cmd.releaseCreep('H');
  Memory.cmd.c.Z = { on: 1, act: 'idle' };
  const z = creep(); z.name = 'Z';
  Game.time = 9001;
  assert.strictEqual(cmd.consumeCreep(z), false);
  assert.strictEqual(Memory.cmd.c.Z, undefined);
});

it('move once releases on arrival and does not touch role memory', () => {
  reset(5600);
  const c = creep();
  cmd.setCreep('H', { act: 'move', pos: { room: 'W46N8', x: 8, y: 5 }, range: 1, once: 1 });
  assert.strictEqual(cmd.consumeCreep(c), true);
  assert.strictEqual(c.moved.x, 8);
  assert.ok(Memory.cmd.c.H);
  c.pos.x = 8;
  Game.time++;
  assert.strictEqual(cmd.consumeCreep(c), true);
  assert.strictEqual(Memory.cmd.c.H, undefined);
  assert.strictEqual(c.memory.dst, 'keep');
});

it('attack without a target holds; fallback lets the role run; no hostile search', () => {
  reset(5700);
  let finds = 0;
  const c = creep();
  c.room.find = () => { finds++; return []; };
  cmd.setCreep('H', { act: 'attack', ttl: 5 });
  assert.strictEqual(cmd.consumeCreep(c), true);
  assert.strictEqual(c.did, null);
  assert.strictEqual(finds, 0);
  cmd.setCreep('H', { act: 'attack', ttl: 5, fallback: 1 });
  Game.time++;
  assert.strictEqual(cmd.consumeCreep(c), false);
  assert.ok(Memory.cmd.c.H, 'fallback keeps the order');
});

it('rangedAttack fires in range and self-heals when asked', () => {
  reset(5800);
  const hostile = { id: 'bad', pos: pos(6, 6) };
  W.objs.bad = hostile;
  const c = creep();
  c.hits = 100;
  cmd.setCreep('H', { act: 'rangedAttack', id: 'bad', heal: 'self', ttl: 5 });
  assert.strictEqual(cmd.consumeCreep(c), true);
  assert.deepStrictEqual(c.did, ['rangedAttack', 'bad']);
  assert.strictEqual(c.healed, 'self');
  assert.strictEqual(c.moved, null);
});

it('tower order attacks the named id and once clears; a sibling tower is independent', () => {
  reset(5900);
  const bad = { id: 'bad' }, other = { id: 'other' };
  W.objs.bad = bad; W.objs.other = other;
  const calls = [];
  const tA = { id: 'tA', attack(x) { calls.push(['A', x.id]); return 0; }, heal() { calls.push('heal'); return 0; }, repair() { calls.push('rep'); return 0; } };
  const tB = { id: 'tB', attack(x) { calls.push(['B', x.id]); return 0; } };
  cmd.setStruct('tA', { act: 'attack', id: 'other', once: 1, ttl: 5 });
  assert.strictEqual(cmd.consumeTower(tA), true);
  assert.strictEqual(cmd.consumeTower(tB), false);
  assert.deepStrictEqual(calls, [['A', 'other']]);
  assert.strictEqual(Memory.cmd.s.tA, undefined);
  assert.strictEqual(cmd.consumeTower(tA), false);
});

it('link transfer and idle lab do not set ops.labs', () => {
  reset(6000);
  const to = { id: 'L2' }; W.objs.L2 = to;
  const link = { id: 'L1', cooldown: 0, transferEnergy(t, a) { this.sent = [t.id, a]; return 0; } };
  cmd.setStruct('L1', { act: 'transfer', id: 'L2', amount: 200, ttl: 3 });
  assert.strictEqual(cmd.consumeLink(link), true);
  assert.deepStrictEqual(link.sent, ['L2', 200]);
  const lab = { id: 'lab', runReaction() { throw new Error('auto reaction'); } };
  cmd.setStruct('lab', { act: 'idle', ttl: 3 });
  assert.strictEqual(cmd.consumeLab(lab), true);
  assert.strictEqual(Memory.ops.labs, undefined);
  const a = { id: 'in1' }, b = { id: 'in2' };
  W.objs.in1 = a; W.objs.in2 = b;
  let reacted = 0;
  const lab2 = { id: 'lab2', runReaction(x, y) { reacted++; assert.strictEqual(x, a); assert.strictEqual(y, b); return 0; } };
  Game.time++;
  cmd.setStruct('lab2', { act: 'react', in1: 'in1', in2: 'in2', once: 1, ttl: 3 });
  assert.strictEqual(cmd.consumeLab(lab2), true);
  assert.strictEqual(reacted, 1);
  assert.strictEqual(Memory.cmd.s.lab2, undefined);
});

it('spawn idle blocks without a body; spawn with allow uses the given body and defaults to hauler', () => {
  reset(6100);
  let spawned = null;
  const spawn = { id: 'sp', pos: pos(1, 1), spawnCreep(body, name, opts) { spawned = { body, name, opts }; return 0; }, recycleCreep() { return 0; } };
  cmd.setStruct('sp', { act: 'spawn', ttl: 5 });
  assert.strictEqual(cmd.consumeSpawn(spawn), true);
  assert.strictEqual(spawned, null);
  Game.time++;
  cmd.setStruct('sp', { act: 'spawn', allow: 1, body: ['move', 'carry'], name: 'Cmd1', once: 1, ttl: 5 });
  assert.strictEqual(cmd.consumeSpawn(spawn), true);
  assert.deepStrictEqual(spawned.body, ['move', 'carry']);
  assert.strictEqual(spawned.name, 'Cmd1');
  assert.strictEqual(spawned.opts.memory.role, 'hauler');
  assert.strictEqual(Memory.cmd.s.sp, undefined);
});

it('terminal block is a lookup; releaseAll clears _cmd and does not touch ops', () => {
  reset(6200);
  Memory.ops.w8min = { sendWhy: 'old' };
  const term = { id: 'term' };
  assert.strictEqual(cmd.blocks(term), false);
  cmd.setStruct('term', { act: 'idle', ttl: 4 });
  assert.strictEqual(cmd.blocks(term), true);
  const c = creep(); Memory.creeps.H = c.memory; c.memory._cmd = 1;
  cmd.setCreep('H', { act: 'idle', ttl: 4 });
  assert.ok(cmd.releaseAll() >= 1);
  assert.deepStrictEqual(Memory.cmd.c, {});
  assert.deepStrictEqual(Memory.cmd.s, {});
  assert.strictEqual(c.memory._cmd, undefined);
  assert.strictEqual(Memory.ops.w8min.sendWhy, 'old');
});

it('rank: quiet haul, spawn pressure, threat flee, softCap bank, war drops upgrade', () => {
  assert.strictEqual(duty('hauler', quiet), 'haul');
  assert.strictEqual(duty('hauler', Object.assign({}, quiet, { spawnPressure: true })), 'fillSpawn');
  const hot = intent.rank('hauler', Object.assign({}, quiet, { spawnPressure: true, spawnHot: true }))[0];
  const warm = intent.rank('hauler', Object.assign({}, quiet, { spawnPressure: true }))[0];
  assert.ok(hot.w > warm.w);
  assert.strictEqual(duty('hauler', Object.assign({}, quiet, { threat: 3 })), 'flee');
  assert.strictEqual(duty('hauler', Object.assign({}, quiet, { threat: 3, combatBody: true })), 'fillTower');
  assert.strictEqual(duty('hauler', Object.assign({}, quiet, { floor: 'band', softCap: true })), 'bank');
  const capped = intent.rank('hauler', Object.assign({}, quiet, { floor: 'band', softCap: true })).map(r => r.duty);
  assert.ok(!capped.includes('upgrade'));
  assert.strictEqual(duty('hauler', Object.assign({}, quiet, { floor: 'ok' })), 'haul');
  assert.ok(intent.rank('hauler', quiet).some(r => r.duty === 'upgrade'));
  const war = intent.rank('hauler', Object.assign({}, quiet, { war: true, labs: true })).map(r => r.duty);
  assert.ok(!war.includes('upgrade') && !war.includes('lab'));
  assert.strictEqual(duty('guard', Object.assign({}, quiet, { hurt: true, threat: 3 })), 'kite');
  assert.strictEqual(duty('guard', Object.assign({}, quiet, { threat: 2 })), 'focus');
  assert.strictEqual(duty('w8defender', quiet), 'idle');
  assert.strictEqual(duty('guard', Object.assign({}, quiet, { remoteDefense: true })), 'hold');
  assert.strictEqual(intent.family('raid9'), 'mil');
  assert.strictEqual(intent.family('hauler'), 'econ');
});

it('signals read published memory and do not find()', () => {
  reset(6300);
  let finds = 0;
  Memory.ops = { w8day: { softCap2: 1, contLow: 2 }, w8threat: 6000, w47n9: { on: false } };
  const room = {
    name: 'W47N8', memory: {}, energyAvailable: 100, energyCapacityAvailable: 1000,
    storage: { store: { energy: 12000 } },
    find() { finds++; return []; },
  };
  const c = creep(); c.room = room; c.hits = 100; c.hitsMax = 400;
  intent.resetCache();
  const s = intent.signals(c);
  assert.strictEqual(finds, 0);
  assert.strictEqual(s.softCap, true);
  assert.strictEqual(s.floor, 'under');
  assert.strictEqual(s.spawnPressure, true);
  assert.strictEqual(s.spawnHot, true);
  assert.strictEqual(s.threat, 2);
  assert.strictEqual(s.hurt, true);
  assert.strictEqual(s.repairDebt, true);
  assert.strictEqual(s.war, false);
});

it('obey fillSpawn delivers when loaded and does not when empty; steer does not act', () => {
  reset(6400);
  global.FIND_MY_STRUCTURES = 1;
  global.STRUCTURE_SPAWN = 'spawn';
  global.STRUCTURE_EXTENSION = 'extension';
  const spawn = { id: 'sp', structureType: 'spawn', pos: pos(6, 5), store: { getFreeCapacity: () => 50 } };
  const c = creep();
  c.store.energy = 400;
  c.room.find = () => [spawn];
  cmd.setCreep('H', { duty: 'fillSpawn', ttl: 10 });
  intent.stamp(c);
  assert.strictEqual(c._duty, 'fillSpawn');
  assert.strictEqual(c._dutyWhy, 'cmd');
  assert.strictEqual(intent.obey(c), true);
  assert.deepStrictEqual(c.did, ['transfer', 'sp', 'energy', undefined]);
  assert.strictEqual(c.memory.dst, 'keep');
  Game.time++;
  c.store.energy = 0; c.did = null;
  c._dutyWhy = null; c._dutyTick = -1;
  assert.strictEqual(intent.obey(c), false);
  assert.strictEqual(c.did, null);
  cmd.releaseCreep('H');
  Memory.cmd.steer = 1; Memory.cmd.on = 1;
  Game.time++;
  const c2 = creep();
  assert.strictEqual(intent.stamp(c2), 'haul');
  assert.strictEqual(c2._dutyWhy, 'steer');
  assert.strictEqual(intent.obey(c2), false);
  assert.strictEqual(c2.memory.duty, undefined);
});

it('guard duty hold does not attack; hauler act idle skips the deliver script', () => {
  reset(6500);
  const stub = (p, exp) => { const r = require.resolve(src(p)); require.cache[r] = { id: r, filename: r, loaded: true, exports: exp }; };
  stub('utils/move.js', { to() { throw new Error('move'); } });
  stub('managers/home.js', { hostiles() { throw new Error('hostiles'); }, flee() { return false; } });
  stub('utils/focus.js', { pick() { throw new Error('pick'); } });
  const G = require(src('roles/guard.js'));
  const g = creep({ name: 'G' });
  g.memory = { role: 'guard', home: 'W46N8', hurt: false };
  Memory.creeps.G = g.memory;
  cmd.setCreep('G', { duty: 'hold', pos: { room: 'W46N8', x: 10, y: 10 }, ttl: 5 });
  G.run(g);
  assert.strictEqual(g.moved.x, 10);
  assert.strictEqual(g.did, null);
  stub('utils/plan.js', { get: () => ({ pos: { miners: [[1, 1]], controllerContainer: [2, 2], fillerContainerA: [3, 3], controllerDrop: [2, 3], storageDoor: [4, 4] } }), key: (x, y) => x + ',' + y });
  stub('utils/roomcache.js', { at: () => null, all: () => [] });
  stub('utils/trace.js', { why() {} });
  stub('utils/salvage.js', { dump: () => false, retire: () => false, pick: () => null });
  stub('roles/queen.js', { fillRoute() { throw new Error('queen'); } });
  const H = require(src('roles/hauler.js'));
  const h = creep();
  h.store.energy = 700;
  cmd.setCreep('H', { act: 'idle', say: 'park', ttl: 5 });
  Game.time++;
  H.run(h);
  assert.deepStrictEqual(h.said, ['park']);
  assert.strictEqual(h.moved, null);
  assert.strictEqual(h.memory.dst, 'keep');
  assert.deepStrictEqual(h.memory.raidOrder, { hold: 1 });
});

console.log('commander ok', n);
