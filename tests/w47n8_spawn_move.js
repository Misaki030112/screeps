// 10-20 13:39 (Misaki): Spawn2 15,18 -> 34,30 relocation state machine + necessary-rampart filter
const assert = require('assert'), path = require('path');
Object.assign(global, { _: require('lodash'), FIND_MY_STRUCTURES: 10, FIND_MY_CONSTRUCTION_SITES: 1, FIND_MY_SPAWNS: 2, FIND_MY_CREEPS: 3, FIND_STRUCTURES: 5, FIND_HOSTILE_CREEPS: 4,
  STRUCTURE_EXTENSION: 'extension', STRUCTURE_SPAWN: 'spawn', STRUCTURE_TOWER: 'tower', STRUCTURE_ROAD: 'road', STRUCTURE_RAMPART: 'rampart', STRUCTURE_CONTAINER: 'container',
  STRUCTURE_STORAGE: 'storage', STRUCTURE_WALL: 'constructedWall', RESOURCE_ENERGY: 'energy', LOOK_STRUCTURES: 'ls', LOOK_CONSTRUCTION_SITES: 'lc', OK: 0,
  WORK: 'work', CARRY: 'carry', MOVE: 'move', ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack', HEAL: 'heal', TOUGH: 'tough', CLAIM: 'claim',
  Memory: { ops: { w8layout: 'approved' } }, Game: { time: 1000, rooms: {}, creeps: {} } });
const W = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'index.js'));
const L = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'layout.js'));
assert.ok(!L.ORDER.spawn.some(([x, y]) => x === 15 && y === 18), '15,18 no longer a spawn slot');
const S = [], sites = [], hostiles = [];
const mk = (t, x, y) => { const s = { id: t + x + ',' + y, structureType: t, my: true, pos: { x, y }, hits: 40000, destroy() { S.splice(S.indexOf(this), 1); return 0; } }; S.push(s); return s; };
const sp = mk('spawn', 15, 18); mk('storage', 35, 32); mk('tower', 33, 35);
for (const [x, y] of [[15, 18], [35, 32], [33, 35], [34, 30], [29, 3], [33, 32], [36, 31]]) mk('rampart', x, y);
const room = { name: 'W47N8', energyAvailable: 1800, energyCapacityAvailable: 1800, controller: { level: 5 }, storage: { store: { energy: 5000 } },
  find: (t, o) => (t === 2 ? S.filter(s => s.structureType === 'spawn') : t === 4 ? hostiles : t === 1 ? sites : S).filter(o && o.filter || (() => true)),
  lookForAt: (k, x, y) => (k === 'ls' ? S : sites).filter(s => s.pos.x === x && s.pos.y === y),
  createConstructionSite: (x, y, t) => { sites.push({ structureType: t, pos: { x, y } }); return 0; } };
// ramparts: keep gate, spawn, storage, tower, hub slot 34,30; drop empty 33,32 / 36,31
const keep = S.filter(s => s.structureType === 'rampart' && W.rampNeeded(room, s)).map(s => s.pos.x + ',' + s.pos.y).sort();
assert.deepStrictEqual(keep, ['15,18', '29,3', '34,30', '33,35', '35,32'].sort(), 'necessary ramparts: ' + keep);
const r36 = S.find(s => s.id === 'rampart36,31'); r36.hits = 1000; Memory.ops.w8hold = { [r36.id]: 40000 };
// GATE_TOWER=100k + soft: park needed ramps at band + soft off so only hold-decay could fire — must still skip r36
for (const id of ['rampart29,3', 'rampart34,30', 'rampart15,18', 'rampart35,32', 'rampart33,35']) {
  const r = S.find(s => s.id === id); if (r) r.hits = 100000;
}
room.storage.store.energy = 4999;
assert.ok(W.rampHold(room) === null, 'unneeded decayed rampart not repaired');
assert.notStrictEqual(W.rampHold(room), r36, 'unneeded never selected');
room.storage.store.energy = 5000;
for (const id of ['rampart29,3', 'rampart34,30', 'rampart15,18', 'rampart35,32', 'rampart33,35']) {
  const r = S.find(s => s.id === id); if (r) r.hits = 40000;
}
const r34 = S.find(s => s.id === 'rampart34,30'); r34.hits = 1; Memory.ops.w8hold = { [r34.id]: 1 };
assert.strictEqual(W.rampHold(room), r34, 'fresh 1-hit spawn-slot rampart is ramped up (else it decays away)');
r34.hits = 40000; Memory.ops.w8hold = {};
// creeps
const cr = (role, ttl) => { Game.creeps[role + ttl + Math.random()] = { memory: { role, home: 'W47N8' }, ticksToLive: ttl }; };
cr('w8miner', 900); cr('w8miner', 300); cr('w8hauler', 800); cr('w8hauler', 800); cr('w8builder', 1000);
Memory.ops.w8move = { phase: 'prep' };
W.moveRun(room); assert.strictEqual(Memory.ops.w8move.phase, 'prep'); assert.ok(Memory.ops.w8move.why.includes('storage') && Memory.ops.w8move.why.includes('ttl'));
room.storage.store.energy = 17000; cr('w8miner', 1400); hostiles.push({});
W.moveRun(room); assert.deepStrictEqual(Memory.ops.w8move.why, ['threat'], 'hostile blocks');
hostiles.pop(); Memory.ops.w8n9a = Game.time - 50; W.moveRun(room); assert.deepStrictEqual(Memory.ops.w8move.why, ['threat'], 'armed in W47N9 recently blocks');
Memory.ops.w8n9a = Game.time - 200; Memory.ops.w8threatN = Game.time; // W48N9 camp keeps TH.on(), must not block
W.moveRun(room); assert.strictEqual(Memory.ops.w8move.phase, 'build'); assert.ok(!S.includes(sp), 'old spawn destroyed');
W.moveRun(room); assert.ok(sites.some(s => s.structureType === 'spawn' && s.pos.x === 34 && s.pos.y === 30), 'site at 34,30');
const n = sites.length; W.moveRun(room); assert.strictEqual(sites.length, n, 'one site only');
mk('spawn', 34, 30); W.moveRun(room); assert.strictEqual(Memory.ops.w8move.phase, 'ext');
const keep2 = S.filter(s => s.structureType === 'rampart' && W.rampNeeded(room, s)).map(s => s.pos.x + ',' + s.pos.y);
assert.ok(!keep2.includes('15,18'), 'old spawn rampart decays after move');
// ext phase: west temp exts relocate in one batch now, no storage gate (storage 256 live at 20:0x)
room.getTerrain = () => ({ get: () => 0 }); room.storage.store.energy = 200;
for (const [x, y] of L.TEMP_EXT) mk('extension', x, y);
hostiles.push({}); W.moveRun(room); assert.strictEqual(S.filter(s => s.structureType === 'extension').length, 5, 'hostile: no destroy'); hostiles.pop();
sites.push({ structureType: 'extension', pos: { x: 1, y: 1 } }); W.moveRun(room); assert.strictEqual(S.filter(s => s.structureType === 'extension').length, 5, 'pending ext site: wait'); sites.pop();
room.energyCapacityAvailable = 1400; W.moveRun(room); assert.strictEqual(S.filter(s => s.structureType === 'extension').length, 3, 'cap floor 1300 -> only 2');
room.energyCapacityAvailable = 1800; sites.length = 0; W.moveRun(room);
assert.strictEqual(S.filter(s => s.structureType === 'extension').length, 0, 'rest destroyed');
const es = sites.filter(s => s.structureType === 'extension');
assert.strictEqual(es.length, 3); assert.ok(es.every(s => L.ORDER.extension.some(([x, y]) => x === s.pos.x && y === s.pos.y)), 'sites in hub ORDER slots');
assert.ok(!es.some(s => [[33, 30], [33, 31], [35, 31], [39, 30]].some(([x, y]) => x === s.pos.x && y === s.pos.y)), 'spawn exits / slots kept free');
W.moveRun(room); assert.strictEqual(Memory.ops.w8move.phase, 'done', 'no temp exts -> done');
console.log('w47n8 spawn move ok');
