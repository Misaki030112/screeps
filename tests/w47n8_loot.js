// W47 haulers must loot Invader mineral tombstones, not just energy (live 2026-11-10 W47N8 30,2).
// node tests/w47n8_loot.js
const assert = require('assert'), path = require('path');
Object.assign(global, {
  STRUCTURE_CONTAINER: 'container', STRUCTURE_EXTRACTOR: 'extractor', STRUCTURE_TERMINAL: 'terminal',
  STRUCTURE_SPAWN: 'spawn', STRUCTURE_EXTENSION: 'extension', STRUCTURE_TOWER: 'tower', STRUCTURE_STORAGE: 'storage',
  STRUCTURE_LINK: 'link', STRUCTURE_ROAD: 'road', STRUCTURE_WALL: 'constructedWall', STRUCTURE_RAMPART: 'rampart',
  STRUCTURE_LAB: 'lab', LOOK_STRUCTURES: 'structure', LOOK_CREEPS: 'creep', LOOK_SOURCES: 'source',
  LOOK_CONSTRUCTION_SITES: 'constructionSite',
  FIND_MINERALS: 116, FIND_MY_STRUCTURES: 108, FIND_MY_CREEPS: 106, FIND_HOSTILE_CREEPS: 103,
  FIND_DROPPED_RESOURCES: 105, FIND_STRUCTURES: 107, FIND_SOURCES_ACTIVE: 104, FIND_MY_SPAWNS: 112,
  FIND_MY_CONSTRUCTION_SITES: 114, FIND_CONSTRUCTION_SITES: 115, FIND_TOMBSTONES: 118, FIND_RUINS: 123, RESOURCE_ENERGY: 'energy',
  WORK: 'work', MOVE: 'move', CARRY: 'carry', ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack',
  HEAL: 'heal', TOUGH: 'tough', CLAIM: 'claim', TERRAIN_MASK_WALL: 1,
  BODYPART_COST: { work: 100, move: 50, carry: 50, attack: 80, ranged_attack: 150, heal: 250, tough: 10, claim: 600 },
  OK: 0, ERR_NOT_ENOUGH_ENERGY: -6,
  _: require('lodash'), Memory: { ops: {} },
  Game: { time: 80, rooms: {}, creeps: {}, getObjectById: id => OBJ[id] },
  RoomPosition: function (x, y, r) { this.x = x; this.y = y; this.roomName = r || 'W47N8'; },
});
const d = path.join(__dirname, '..', 'src', 'rooms', 'w47n8');
const C = require(path.join(d, 'config'));
const RL = require(path.join(d, 'roles.js'));
const MV = require(path.join(__dirname, '..', 'src', 'utils', 'move.js'));
MV.to = (c, x, y, r) => { if (c.moveTo) c.moveTo({ x, y, range: r }); return Math.max(Math.abs(c.pos.x - x), Math.abs(c.pos.y - y)) <= (r || 0); };

const cheb = (a, b) => Math.max(Math.abs(a.x - (b.pos || b).x), Math.abs(a.y - (b.pos || b).y));
const pos = (x, y, rn) => {
  const p = { x, y, roomName: rn || 'W47N8' };
  p.getRangeTo = o => cheb(p, o.pos || o);
  p.isNearTo = o => cheb(p, o.pos || o) <= 1;
  p.inRangeTo = (o, r) => cheb(p, o.pos || o) <= r;
  return p;
};
let OBJ = {};
function storeOf(map, cap) {
  const s = Object.assign({}, map);
  const used = () => Object.keys(s).filter(k => typeof s[k] === 'number').reduce((a, k) => a + s[k], 0);
  Object.defineProperties(s, {
    getCapacity: { value: () => cap },
    getUsedCapacity: { value: used },
    getFreeCapacity: { value: () => cap - used() },
  });
  return s;
}
const stor = { my: true, id: 'stor', structureType: 'storage', pos: pos(35, 32), store: storeOf({ energy: 8000 }, 1e6) };
const term = { my: true, id: 'term', structureType: 'terminal', pos: pos(35, 33), store: storeOf({}, 3e5) };
const tomb = {
  id: 'tomb302', pos: pos(30, 2), ticksToDecay: 160,
  store: storeOf({ energy: 582, GO: 95, KO: 17, ZH: 23, UH: 11 }, 2000),
};
OBJ = { stor, term, tomb302: tomb };
const room = {
  name: 'W47N8', storage: stor, terminal: term, controller: { level: 7, my: true },
  energyAvailable: 1200, energyCapacityAvailable: 1300,
  find: (t) => {
    if (t === FIND_TOMBSTONES) return [tomb];
    if (t === FIND_DROPPED_RESOURCES || t === FIND_RUINS || t === FIND_HOSTILE_CREEPS) return [];
    if (t === FIND_MY_CREEPS) return Object.values(Game.creeps);
    if (t === FIND_STRUCTURES || t === FIND_MY_STRUCTURES) return [stor, term];
    return [];
  },
  lookForAt: () => [],
};
Game.rooms.W47N8 = room;

function creep(role, x, y, cap, extra) {
  const c = {
    id: 'c' + role + x + y, name: role + x + y, memory: Object.assign({ role, home: 'W47N8' }, extra && extra.memory),
    pos: pos(x, y), room, ticksToLive: 1000, got: [], moved: [],
    store: storeOf((extra && extra.store) || {}, cap),
    withdraw(o, k) { this.got.push(['w', k]); return 0; },
    pickup(o) { this.got.push(['p', o.id]); return 0; },
    transfer(o, k) { this.got.push(['t', o.id, k]); return 0; },
    moveTo(p) { this.moved.push([p.x, p.y]); return 0; },
    getActiveBodyparts: () => 0,
  };
  Game.creeps[c.name] = c;
  OBJ[c.id] = c;
  return c;
}

// haulPick itself still ignores a minerals-only view: energy filter would skip a 0-energy mineral tomb.
// The role hook uses salvage, which must pick this live pile and walk there.
Game.time++;
const h = creep('w8hauler', 22, 34, 500);
assert.strictEqual(RL._lootPick(h), true, 'empty hauler picks the Invader tombstone');
assert.strictEqual(h.memory.salv, 'tomb302');
assert.ok(h.moved.length && h.moved[0][0] === 30 && h.moved[0][1] === 2, 'walks toward 30,2: ' + JSON.stringify(h.moved));

Game.time++;
const near = creep('w8hauler', 30, 3, 750);
assert.strictEqual(RL._lootPick(near), true);
assert.deepStrictEqual(near.got, [['w', 'energy']], 'energy withdrawn first');
assert.strictEqual(near.memory.salv, 'tomb302', 'stays on the tomb until empty (not one withdraw and leave)');

Game.creeps = {}; Game.time++;
const loaded = creep('w8hauler', 35, 32, 500, { store: { GO: 95 } });
assert.strictEqual(RL._lootDump(loaded), true, 'held minerals dump');
assert.deepStrictEqual(loaded.got, [['t', 'term', 'GO']], 'mineralRun delivers GO to the terminal');

// empty rhauler in W47N8 must loot instead of walking out to W47N7
Game.creeps = {}; Game.time++;
const rh = creep('w8rhauler', 31, 26, 750);
assert.strictEqual(RL._lootPick(rh), true, 'empty rhauler in home also loots');
assert.strictEqual(rh.memory.salv, 'tomb302');
assert.ok(rh.moved.length && rh.moved[0][1] === 2, 'rhauler walks north to 30,2, not to the remote: ' + JSON.stringify(rh.moved));

// energy delivery (w=true) is not interrupted for a new loot walk
Game.creeps = {}; Game.time++;
const busy = creep('w8hauler', 22, 34, 500, { memory: { w: true }, store: { energy: 500 } });
busy.store.getFreeCapacity = () => 0;
assert.strictEqual(RL._lootPick(busy), false, 'loaded energy delivery is not diverted');

console.log('w47n8 loot ok');
