// W47N8 drain-aware tower: hold fire on out-healed tanks north of the seal, shoot in-base armed creeps and claimers.
const assert = require('assert'), path = require('path');
global._ = require('lodash'); Object.assign(global, { FIND_MY_STRUCTURES: 1, FIND_HOSTILE_CREEPS: 2, FIND_MY_CREEPS: 3, FIND_STRUCTURES: 4, STRUCTURE_TOWER: 'tower', STRUCTURE_WALL: 'constructedWall', STRUCTURE_RAMPART: 'rampart',
  RESOURCE_ENERGY: 'energy', CLAIM: 'claim', ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack', WORK: 'work', HEAL: 'heal', TOUGH: 'tough', Memory: {}, Game: { time: 1, creeps: {}, rooms: {} } });
const W = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'index.js'));
let H;
const P = (x, y) => ({ x, y, getRangeTo: o => Math.max(Math.abs(x - (o.pos || o).x), Math.abs(y - (o.pos || o).y)),
  findInRange: (t, r) => t === 2 ? H.filter(h => Math.max(Math.abs(h.pos.x - x), Math.abs(h.pos.y - y)) <= r) : [] });
const body = o => Object.entries(o).flatMap(([t, n]) => Array(n).fill({ type: t, hits: 100 }));
let shots = []; const tw = { structureType: 'tower', pos: P(33, 35), store: { energy: 690 }, attack: x => shots.push(x.id), heal: () => {} };
const room = { memory: {}, find: (t, o) => { const a = t === 1 ? [tw] : t === 2 ? H : []; return o && o.filter ? a.filter(o.filter) : a; } };
const go = h => { H = h; shots = []; W.towerRun(room); return shots; };
assert.deepStrictEqual(go([{ id: 'd', pos: P(31, 1), body: body({ tough: 14, move: 14 }) }, { id: 'h', pos: P(32, 1), body: body({ heal: 7, move: 7 }) }]), [], 'drain tanks north of seal: hold fire');
assert.deepStrictEqual(go([{ id: 'a', pos: P(30, 20), body: body({ attack: 10, move: 10 }) }]), ['a'], 'armed in base: fire');
assert.ok(room.memory.threat8 && room.memory.threat8.inBase, 'threat8 flags in-base threat for the defender spawn');
assert.deepStrictEqual(go([{ id: 'c', pos: P(30, 1), body: body({ claim: 1, move: 1 }) }]), ['c'], 'claimer anywhere: fire');
tw.store.energy = 200;
assert.deepStrictEqual(go([{ id: 'b', pos: P(30, 20), body: body({ tough: 5, move: 5 }) }]), [], 'unarmed in base at low energy: keep reserve');
console.log('w47n8 tower ok');
// threat mode (14:23)
const TH = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'threat.js'));
Object.assign(global, { TOUGH: 'tough' }); Memory.ops = {}; Game.time = 100000;
assert.strictEqual(TH.on(), false, 'quiet by default'); assert.strictEqual(TH.wallTarget(10000), 10000);
const R = h => ({ name: 'W47N8', find: () => h });
TH.mark(R([{ owner: { username: 'BustJetter' }, pos: { y: 1 }, body: body({ tough: 14, move: 14 }) }]));
assert.strictEqual(TH.on(), true, 'drain group -> threat'); assert.strictEqual(TH.wallTarget(10000), 50000); assert.strictEqual(TH.flee(), false, 'unarmed tanks do not trigger flee');
TH.mark(R([{ owner: { username: 'BustJetter' }, pos: { y: 5 }, body: body({ attack: 10, move: 10 }) }])); assert.strictEqual(TH.flee(), true, 'armed in north -> flee');
Game.time += 21; assert.strictEqual(TH.flee(), false, 'flee clears after 20 quiet ticks');
Game.time += 1500; assert.strictEqual(TH.on(), false, 'threat reverts after 1500 quiet ticks');
console.log('w47n8 threat ok');
