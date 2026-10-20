// 10-20 18:1x (Misaki: move at 19:30 despite the W47N9 border): Memory.ops.w8move.force skips ONLY the w8n9a check
const assert = require('assert'), path = require('path');
Object.assign(global, { _: require('lodash'), FIND_MY_STRUCTURES: 10, FIND_MY_CONSTRUCTION_SITES: 1, FIND_MY_SPAWNS: 2, FIND_MY_CREEPS: 3, FIND_STRUCTURES: 5, FIND_HOSTILE_CREEPS: 4,
  STRUCTURE_EXTENSION: 'extension', STRUCTURE_SPAWN: 'spawn', STRUCTURE_TOWER: 'tower', STRUCTURE_ROAD: 'road', STRUCTURE_RAMPART: 'rampart', STRUCTURE_CONTAINER: 'container',
  STRUCTURE_STORAGE: 'storage', STRUCTURE_WALL: 'constructedWall', RESOURCE_ENERGY: 'energy', LOOK_STRUCTURES: 'ls', LOOK_CONSTRUCTION_SITES: 'lc', OK: 0,
  WORK: 'work', CARRY: 'carry', MOVE: 'move', ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack', HEAL: 'heal', TOUGH: 'tough', CLAIM: 'claim',
  Memory: { ops: { w8layout: 'approved' } }, Game: { time: 1000, rooms: {}, creeps: {} } });
const W = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'index.js'));
const C = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'config.js'));
const S = [], sites = [], hostiles = [];
const mk = (t, x, y, e) => { const s = { id: t + x + ',' + y, structureType: t, my: true, pos: { x, y }, hits: 150000, store: { energy: e || 0 }, destroy() { S.splice(S.indexOf(this), 1); return 0; } }; S.push(s); return s; };
const sp = mk('spawn', 15, 18); mk('storage', 35, 32); const t1 = mk('tower', 33, 35, 1000); mk('tower', 24, 8, 1000); mk('rampart', 34, 30);
for (const [x, y] of C.SEAL) mk(x === 29 ? 'rampart' : 'constructedWall', x, y);
const room = { name: 'W47N8', energyAvailable: 1800, energyCapacityAvailable: 1800, controller: { level: 5 }, storage: { store: { energy: 20000 } },
  find: (t, o) => (t === 2 ? S.filter(s => s.structureType === 'spawn') : t === 4 ? hostiles : t === 1 ? sites : t === 10 ? S.filter(s => s.my) : S).filter(o && o.filter || (() => true)),
  lookForAt: (k, x, y) => (k === 'ls' ? S : sites).filter(s => s.pos.x === x && s.pos.y === y),
  createConstructionSite: (x, y, t) => { sites.push({ structureType: t, pos: { x, y } }); return 0; } };
const P = (x, y) => ({ x, y, inRangeTo: (a, b, r) => Math.max(Math.abs(a - x), Math.abs(b - y)) <= r });
const cr = (role, ttl, pos, e) => { const c = { memory: { role, home: 'W47N8' }, ticksToLive: ttl, pos: pos || P(1, 1), store: { energy: e || 0 } }; Game.creeps[role + ttl] = c; return c; };
cr('w8miner', 900); cr('w8miner', 950); cr('w8hauler', 800); cr('w8hauler', 810); const b = cr('w8builder', 1000, P(10, 10), 300);
Memory.ops.w8n9a = Game.time - 5; Memory.ops.w8move = { phase: 'prep' };
W.moveRun(room); assert.deepStrictEqual(Memory.ops.w8move.why, ['threat'], 'no force: border blocks');
Memory.ops.w8move.force = 1; W.moveRun(room);
assert.deepStrictEqual(Memory.ops.w8move.why.sort(), ['builderpos', 'guard'], 'force: border skipped, position + guard required: ' + Memory.ops.w8move.why);
b.pos = P(34, 32); cr('w8guard', 1400); t1.store.energy = 500; W.moveRun(room); assert.deepStrictEqual(Memory.ops.w8move.why, ['towers']);
t1.store.energy = 900; S.find(s => s.pos.x === 8 && s.pos.y === 3).hits = 90000; W.moveRun(room); assert.deepStrictEqual(Memory.ops.w8move.why, ['walls']);
S.find(s => s.pos.x === 8 && s.pos.y === 3).hits = 150000;
hostiles.push({ owner: { username: 'X' }, body: [{ type: 'ranged_attack', hits: 100 }], pos: { x: 30, y: 10 } });
W.moveRun(room); assert.strictEqual(Memory.ops.w8move.phase, 'hold', 'armed hostile inside -> hold'); assert.ok(S.includes(sp), 'old spawn kept');
W.moveRun(room); assert.strictEqual(Memory.ops.w8move.phase, 'hold', 'hold never resumes on its own');
hostiles.pop(); Memory.ops.w8move.phase = 'prep'; W.moveRun(room);
assert.strictEqual(Memory.ops.w8move.phase, 'build', 'all met -> destroy'); assert.ok(!S.includes(sp));
W.moveRun(room); assert.ok(sites.some(s => s.structureType === 'spawn' && s.pos.x === 34 && s.pos.y === 30), 'spawn site 34,30');
console.log('w47n8 forced move ok');
