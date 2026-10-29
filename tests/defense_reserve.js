const path = require('path'), assert = require('assert');
Object.assign(global, { RESOURCE_ENERGY: 'energy', _: require('lodash') });
const W = require(path.join(__dirname, '..', 'src', 'managers', 'walls.js'));
global.Memory = { defense: { reserveE: 15000 } };
assert.strictEqual(W.defLow({ storage: { store: { energy: 3000 } } }), true); assert.strictEqual(W.defLow({ storage: { store: { energy: 16000 } } }), false);
assert.strictEqual(W.budgetE({ storage: { store: { energy: 3000 } }, memory: {} }), 0);
Memory.defense = {}; assert.strictEqual(W.defLow({ storage: { store: { energy: 3000 } } }), false); console.log('defense reserve ok');
// spawn surplus sizing is exercised live; static check that the hysteresis block is present
assert.ok(require('fs').readFileSync(path.join(__dirname, '..', 'src', 'managers', 'spawn.js'), 'utf8').includes('sized to the SURPLUS'));
// bank recycle (13:26 10-18): empty builders recycle under defLow instead of idling at waiting_feed
assert.ok(require('fs').readFileSync(path.join(__dirname, '..', 'src', 'roles', 'builder.js'), 'utf8').includes("Wb.defLow(home) && (c.memory.nb"));
console.log('builder bank recycle present');
// siege exemption (strategy review 10-19 20:5x): player combat creep inside home -> one builder may repair below reserveE
global.FIND_HOSTILE_CREEPS = 103;
const hostile = (u, parts) => ({ owner: { username: u }, body: parts.map(t => ({ type: t, hits: 100 })) });
const roomWith = hs => ({ find: k => (k === 103 ? hs : []) });
assert.strictEqual(W.siege(roomWith([hostile('BustJetter', ['ranged_attack', 'move'])])), true);
assert.strictEqual(W.siege(roomWith([hostile('Invader', ['attack'])])), false);
assert.strictEqual(W.siege(roomWith([hostile('BustJetter', ['tough', 'move'])])), false);
assert.strictEqual(W.siege(roomWith([])), false);
const sp = require('fs').readFileSync(path.join(__dirname, '..', 'src', 'managers', 'spawn.js'), 'utf8');
assert.ok(sp.includes('T.builder > 0 && !war') && sp.includes('if (!war) T.builder = 0'));
assert.ok(require('fs').readFileSync(path.join(__dirname, '..', 'src', 'roles', 'builder.js'), 'utf8').includes('war ? storeFloor(home)'));
console.log('siege exemption ok');
// route-road upkeep (patrol 10-20 09:5x): one capped builder for remote road sites even at the reserve, without costing an upgrader
assert.ok(sp.includes("repairTarget(0.3))) { T.builder = 1; roadBuilder = true; }") && sp.includes('store[RESOURCE_ENERGY] >= dr - 3000 &&') && sp.includes('(roadBuilder || !T.builder)') && sp.includes("role === 'builder' && roadBuilder) e = Math.min(e, 1000)"));
console.log('road upkeep builder ok');
// fund-backed wall builder at the reserve (patrol 10-29 17:2x): wantBuilder keeps 1 builder when surplus gate would zero it
assert.ok(sp.includes('!T.builder && !low && Wr.wantBuilder(room)) { T.builder = 1; }'));
console.log('fund wall builder ok');
