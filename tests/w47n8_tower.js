// W47N8 drain-aware tower: hold fire on out-healed tanks north of the seal, shoot in-base armed creeps and claimers.
const assert = require('assert'), path = require('path');
global._ = require('lodash'); Object.assign(global, { FIND_MY_STRUCTURES: 1, FIND_HOSTILE_CREEPS: 2, FIND_MY_CREEPS: 3, FIND_STRUCTURES: 4, STRUCTURE_TOWER: 'tower', STRUCTURE_WALL: 'constructedWall', STRUCTURE_RAMPART: 'rampart',
  RESOURCE_ENERGY: 'energy', MOVE: 'move', CARRY: 'carry', CLAIM: 'claim', ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack', WORK: 'work', HEAL: 'heal', TOUGH: 'tough', Memory: {}, Game: { time: 1, creeps: {}, rooms: {} } });
const W = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'index.js'));
let H;
const P = (x, y) => ({ x, y, getRangeTo: o => Math.max(Math.abs(x - (o.pos || o).x), Math.abs(y - (o.pos || o).y)),
  findInRange: (t, r) => t === 2 ? H.filter(h => Math.max(Math.abs(h.pos.x - x), Math.abs(h.pos.y - y)) <= r) : [] });
const body = o => Object.entries(o).flatMap(([t, n]) => Array(n).fill({ type: t, hits: 100 }));
const hc = (id, x, y, b) => { const bd = body(b); return { id, pos: P(x, y), body: bd, hits: bd.length * 100, hitsMax: bd.length * 100 }; };
let shots = [], heals = [], mine = []; const tw = { structureType: 'tower', pos: P(33, 35), store: { energy: 690 }, attack: x => shots.push(x.id), heal: x => heals.push(x.id) };
const room = { memory: {}, find: (t, o) => { const a = t === 1 ? [tw] : t === 2 ? H : t === 3 ? mine : []; return o && o.filter ? a.filter(o.filter) : a; } };
const go = h => { H = h; shots = []; W.towerRun(room); return shots; };
assert.deepStrictEqual(go([hc('d', 31, 1, { tough: 14, move: 14 }), hc('h', 32, 1, { heal: 7, move: 7 })]), [], 'drain tanks north of seal: hold fire');
assert.deepStrictEqual(go([hc('a', 30, 20, { attack: 10, move: 10 })]), ['a'], 'armed in base: fire');
assert.ok(room.memory.threat8 && room.memory.threat8.inBase, 'threat8 flags in-base threat for the defender spawn');
assert.deepStrictEqual(go([hc('c', 30, 1, { claim: 1, move: 1 })]), ['c'], 'claimer anywhere: fire');
tw.store.energy = 200;
assert.deepStrictEqual(go([hc('b', 30, 20, { tough: 14, move: 14 })]), [], 'unarmed in base, not dying in 2 ticks, tower < 400: keep reserve');
assert.deepStrictEqual(go([hc('b', 33, 30, { tough: 5, move: 5 })]), ['b'], 'unarmed in base dying within 2 ticks: fire even at low energy');
// 17:48 heal rule: a friendly < 60% is healed instead of attacking; >= 60% is not healed
tw.store.energy = 690; mine = [{ id: 'd', pos: P(29, 4), hits: 1400, hitsMax: 2200, body: body({ ranged_attack: 11, move: 11 }) }];
heals = []; assert.deepStrictEqual(go([hc('a', 30, 20, { attack: 10, move: 10 })]), ['a'], '64%: keep attacking'); assert.deepStrictEqual(heals, []);
mine[0].hits = 1200; heals = []; assert.deepStrictEqual(go([hc('a', 30, 20, { attack: 10, move: 10 })]), [], '<60%: no attack this tick'); assert.deepStrictEqual(heals, ['d'], 'heal the defender');
mine = [];
console.log('w47n8 tower ok');
// threat mode (14:23)
const TH = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'threat.js'));
Object.assign(global, { TOUGH: 'tough' }); Memory.ops = {}; Game.time = 100000;
assert.strictEqual(TH.on(), false, 'quiet by default'); assert.strictEqual(TH.wallTarget(10000), 10000);
const R = h => ({ name: 'W47N8', find: () => h });
TH.mark(R([{ owner: { username: 'BustJetter' }, pos: { y: 1 }, body: body({ tough: 14, move: 14 }) }]));
assert.strictEqual(TH.on(), false, 'TOUGH-only decoy -> no threat (Misaki 10-19)');
TH.mark(R([{ owner: { username: 'BustJetter' }, pos: { y: 1 }, body: body({ heal: 7, move: 7 }) }]));
assert.strictEqual(TH.on(), true, 'healer group -> threat'); assert.strictEqual(TH.wallTarget(10000), 100000); assert.strictEqual(TH.flee(), false, 'unarmed tanks do not trigger flee');
TH.mark(R([{ owner: { username: 'BustJetter' }, pos: { y: 5 }, body: body({ attack: 10, move: 10 }) }])); assert.strictEqual(TH.flee(), true, 'armed in north -> flee');
Game.time += 21; assert.strictEqual(TH.flee(), false, 'flee clears after 20 quiet ticks');
// 2026-11-19 02:17 patrol: FLEE_QUIET expiry is not "clear" if W47N7 FSM is still open (lost vision).
Memory.remote = { W47N7: { th: { st: 'THREAT' } } };
assert.strictEqual(TH.flee(), true, 'W47N7 THREAT holds flee after visual quiet');
Memory.remote.W47N7.th.st = 'DEFEND';
assert.strictEqual(TH.flee(), true, 'W47N7 DEFEND holds flee after visual quiet');
Memory.remote.W47N7.th.st = 'WAIT';
assert.strictEqual(TH.flee(), true, 'W47N7 WAIT holds flee after visual quiet');
Memory.remote.W47N7.th.st = 'SAFE';
assert.strictEqual(TH.flee(), false, 'W47N7 SAFE + visual quiet: resume');
Memory.remote = {};
Game.time += 1500; assert.strictEqual(TH.on(), false, 'threat reverts after 1500 quiet ticks');
// own creeps never count, even if a find() result includes them (14:27)
Memory.ops = {}; TH.mark(R([{ my: true, owner: { username: 'Misaki' }, pos: { y: 5 }, body: body({ attack: 10, ranged_attack: 5, work: 5, heal: 5, tough: 10, move: 10 }) }]));
assert.strictEqual(TH.on(), false, 'own armed creep -> no threat'); assert.strictEqual(TH.flee(), false, 'own armed creep -> no flee');
console.log('w47n8 threat ok');
// 18:06 cleared-threat rule: roster written while the border signal is fresh, dropped 60 t after it (no hostiles in room) -> no spawns
{ mine = []; Memory.ops = { w8invN: Game.time }; Game.time += 20; go([]); assert.ok(Memory.ops.w8roster, 'fresh border signal: roster');
  Game.time += 61; go([]); assert.strictEqual(Memory.ops.w8roster, undefined, 'signal > 60 t old, nothing in room: roster dropped');
  assert.strictEqual(room.memory.w8assess, undefined); console.log('w47n8 cleared threat ok'); }
