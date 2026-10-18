const path = require('path'), assert = require('assert');
Object.assign(global, { RESOURCE_ENERGY: 'energy', _: require('lodash') });
const W = require(path.join(__dirname, '..', 'src', 'managers', 'walls.js'));
global.Memory = { defense: { reserveE: 15000 } };
assert.strictEqual(W.defLow({ storage: { store: { energy: 3000 } } }), true); assert.strictEqual(W.defLow({ storage: { store: { energy: 16000 } } }), false);
assert.strictEqual(W.budgetE({ storage: { store: { energy: 3000 } }, memory: {} }), 0);
Memory.defense = {}; assert.strictEqual(W.defLow({ storage: { store: { energy: 3000 } } }), false); console.log('defense reserve ok');
