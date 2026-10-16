// node tests/home_defense.js : early wall start on the approved threat trigger, west-first site order, guard body
const path = require('path'), assert = require('assert'); const src = p => path.join(__dirname, '..', 'src', p);
const L4 = require('lodash'); global._ = Object.assign({}, L4, { min: (a, f) => f ? L4.minBy(a, f) : L4.min(a) });
Object.assign(global, { OK: 0, RESOURCE_ENERGY: 'energy', STRUCTURE_RAMPART: 'rampart', STRUCTURE_WALL: 'constructedWall', STRUCTURE_ROAD: 'road', FIND_HOSTILE_CREEPS: 103, LOOK_CONSTRUCTION_SITES: 'constructionSite',
  RANGED_ATTACK: 'ranged_attack', MOVE: 'move', HEAL: 'heal', WORK: 'work', CARRY: 'carry', CLAIM: 'claim', ATTACK: 'attack', Game: { time: 1000 }, FIND_MY_CONSTRUCTION_SITES: 114, STRUCTURE_WALL: 'constructedWall', Memory: {} });
require.cache[require.resolve(src('managers/threat.js'))] = { loaded: true, exports: { holding: () => false, reserve: () => 1300 } };
require.cache[require.resolve(src('utils/roomcache.js'))] = { loaded: true, exports: { at: () => null, sites: () => [], all: () => [] } };
console.log = (l => (...a) => { if (!String(a[0]).startsWith('WALLS')) l(...a); })(console.log);
const W = require(src('managers/walls.js')), H = require(src('managers/home.js'));
const room = (mem, hs = []) => { const made = []; return { name: 'W46N8', made, memory: mem, controller: { level: 5 }, storage: { store: { energy: 900 } }, find: () => hs,
  lookForAt: () => [], createConstructionSite: (x, y, t) => { made.push(`${t} ${x},${y}`); return 0; } }; };
// default OFF (Misaki 2026-10-16 09:51): alert/squad does not start walls, no guards
let r = room({ defAlert: 2000 }); assert.strictEqual(W.phase(r), 'off', 'early walls off by default');
assert.strictEqual(H.wantGuards(room({}, [{ owner: { username: 'B' }, body: Array(8).fill({ type: 'ranged_attack', hits: 100 }) }])), 0, 'guards off by default');
// switching off after an early start: latch cleared, unbuilt planned sites removed, progressed ones kept
let removed = []; const site = (x, y, t, p) => ({ pos: { x, y }, structureType: t, progress: p, progressTotal: 1000, remove() { removed.push(`${x},${y}`); return 0; } });
r = room({ walls: { started: 1, why: 'threat' }, defAlert: 5000 }); r.find = t => t === 114 ? [site(6, 28, 'rampart', 0), site(6, 24, 'constructedWall', 500), site(30, 30, 'rampart', 0)] : [];
assert.strictEqual(W.phase(r), 'off'); assert.ok(!r.memory.walls && !r.memory.defAlert); assert.deepStrictEqual(removed, ['6,28'], 'only unbuilt planned barrier sites');
Memory.defense = { earlyWalls: true, guards: true };
r = room({}); assert.strictEqual(W.phase(r), 'off', 'calm RCL5 stays off');
r = room({ defAlert: 2000 }); assert.strictEqual(W.phase(r), 'build'); assert.strictEqual(r.memory.walls.why, 'threat'); assert.strictEqual(r.memory.walls.fund, 0);
W.placeSites(r, 5); assert.deepStrictEqual(r.made, ['rampart 6,28', 'constructedWall 6,24'], 'west gate then west wall first');
const sq = { owner: { username: 'BustJetter' }, pos: { x: 10, y: 25 }, body: Array(8).fill({ type: 'ranged_attack', hits: 100 }) };
Game.time++; r = room({}, [sq]); assert.strictEqual(W.phase(r), 'build', 'squad inside starts walls'); assert.strictEqual(H.wantGuards(r), 1);
Game.time++; const r2 = room({}, [sq, Object.assign({}, sq, { body: Array(9).fill({ type: 'ranged_attack', hits: 100 }) })]); assert.strictEqual(H.wantGuards(r2), 2);
Game.time++; assert.strictEqual(H.wantGuards(room({}, [{ owner: { username: 'X' }, body: [{ type: 'tough', hits: 100 }] }])), 0, 'scouts: no guard');
console.log('home defense ok');
