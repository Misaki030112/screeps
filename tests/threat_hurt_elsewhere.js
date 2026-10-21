// sense(): damage taken outside the remote (e.g. NPC Invader in W45N8) must not flag hurtNoInv for W45N7.
const path = require('path'), assert = require('assert');
global._ = { some: (o, f) => Object.values(o).some(f), filter: (o, f) => Object.values(o).filter(f) };
Object.assign(global, { HEAL: 'heal', RANGED_ATTACK: 'ranged_attack', ATTACK: 'attack', CLAIM: 'claim', RESOURCE_ENERGY: 'energy', FIND_HOSTILE_CREEPS: 1, FIND_HOSTILE_STRUCTURES: 2, STRUCTURE_INVADER_CORE: 'invaderCore' });
global.Memory = { remote: {}, defense: {} };
const room = n => ({ name: n, find: () => [], memory: {} });
global.Game = { time: 100, cpu: { bucket: 10000 }, rooms: { W45N7: room('W45N7'), W46N8: room('W46N8'), W45N8: room('W45N8') }, creeps: {} };
const T = require(path.join(__dirname, '..', 'src/managers/threat.js'));
const c = { memory: { role: 'rhauler', remote: 'W45N7' }, hits: 1000, hitsMax: 1000, room: { name: 'W45N8' } };
Game.creeps.h = c;
const tick = (t, rn, hits) => { Game.time = t; c.room = { name: rn }; c.hits = hits; return T.sense('W45N7').hurtNoInv; };
assert.strictEqual(tick(100, 'W45N8', 1000), false);
assert.strictEqual(tick(101, 'W45N8', 700), false); // hit by Invader in W45N8
assert.strictEqual(tick(102, 'W45N7', 700), false); // enters W45N7 hurt: old damage, not a player
assert.strictEqual(tick(103, 'W45N7', 700), false);
assert.strictEqual(tick(104, 'W45N7', 600), true);  // real in-room drop, no Invader -> player
assert.strictEqual(tick(110, 'W45N7', 500), false); // stale sample (gap) is ignored
console.log('threat_hurt_elsewhere ok');
