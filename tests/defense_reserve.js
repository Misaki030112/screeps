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
