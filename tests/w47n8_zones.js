// 14:38 threat-mode wall zones: builders spread over W/E/R, prefer work in range, never count others' zones twice
const assert = require('assert'), path = require('path');
Object.assign(global, { _: require('lodash'), FIND_STRUCTURES: 5, FIND_MY_CREEPS: 3, STRUCTURE_WALL: 'constructedWall', STRUCTURE_RAMPART: 'rampart',
  ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack', WORK: 'work', HEAL: 'heal', TOUGH: 'tough', FIND_HOSTILE_CREEPS: 2,
  Memory: { ops: {} }, Game: { time: 1000, rooms: {} } });
const RL = require(path.join(__dirname, '..', 'src', 'rooms', 'w47n8', 'roles.js'));
const { zoneJob } = RL._t;
Memory.ops.w8threatN = 999; // threat on
const pos = (x, y) => ({ x, y, inRangeTo: (o, r) => Math.max(Math.abs(x - (o.pos || o).x), Math.abs(y - (o.pos || o).y)) <= r,
  findClosestByRange: a => _.min(a, o => Math.max(Math.abs(x - o.pos.x), Math.abs(y - o.pos.y))) });
const wall = (x, h) => ({ id: 'w' + x, structureType: 'constructedWall', hits: h, pos: pos(x, 3) });
const ram = (x, y, h) => ({ id: 'r' + x, structureType: 'rampart', my: true, hits: h, pos: pos(x, y) });
const S = [8, 9, 10, 11].map(x => wall(x, 10000)).concat([24, 25, 26, 27, 28, 29, 30, 31].map(x => wall(x, 10000)), [ram(15, 18, 10000), ram(33, 35, 10000), ram(35, 32, 10000)]);
const B = [];
const room = { controller: { level: 4 }, find: (t, o) => (t === 5 ? S : B).filter(o && o.filter || (() => true)) };
const mk = (id, x, y) => { const c = { id, memory: { role: 'w8builder' }, pos: pos(x, y) }; B.push(c); return c; };
const got = [];
for (let i = 0; i < 4; i++) { const c = mk('b' + i, 20, 10); zoneJob(room, c); got.push(c.memory.tz); }
assert.deepStrictEqual(got.slice().sort(), ['E', 'E', 'R', 'W'], 'deficit/(n+1): E 320k gets 2, W 160k and R 120k one each: ' + got);
// in-range preference: an E builder at 28,4 keeps repairing 29,3 (2k above the low) instead of walking to 24,3
const e = B[got.indexOf('E')]; e.pos = pos(28, 4); S.find(s => s.id === 'w29').hits = 9000; S.find(s => s.id === 'w24').hits = 7000;
for (const s of S) if (['w25', 'w26', 'w27', 'w28', 'w30', 'w31'].includes(s.id)) s.hits = 12000;
assert.strictEqual(zoneJob(room, e).id, 'w29', 'lowest in range 3 within 5k of the zone low');
S.find(s => s.id === 'w24').hits = 1000; assert.strictEqual(zoneJob(room, e).id, 'w24', 'zone low >5k below -> walk to it');
// own creeps are never hostiles here: zoneJob ignores non-builders
assert.ok(['W', 'E', 'R'].includes(e.memory.tz));
// done zone -> reassigned
for (const s of S) if (s.structureType === 'constructedWall' && s.pos.x <= 11) s.hits = 60000;
const w = B[got.indexOf('W')]; zoneJob(room, w); assert.notStrictEqual(w.memory.tz, 'W', 'finished W zone -> builder moves to another zone');
console.log('w47n8 zones ok');
