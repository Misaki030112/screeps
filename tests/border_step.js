// Border step-in (roles/remote.js inward): never step onto a tile another creep holds or is about to enter (bounce fix 2026-10-16)
const path = require('path'), assert = require('assert');
Object.assign(global, { TOP: 1, TOP_RIGHT: 2, RIGHT: 3, BOTTOM_RIGHT: 4, BOTTOM: 5, BOTTOM_LEFT: 6, LEFT: 7, TOP_LEFT: 8, _: require('lodash') });
const { inward } = require(path.join(__dirname, '..', 'src/roles/remote.js'));
const no = () => false, set = a => (x, y) => a.some(([p, q]) => p === x && q === y);
assert.strictEqual(inward(49, 21, no, no), LEFT, 'free: straight');
assert.strictEqual(inward(49, 21, no, set([[48, 21]])), TOP_LEFT, 'straight claimed by outbound hauler: diagonal');
assert.strictEqual(inward(49, 21, no, set([[48, 21], [48, 20]])), BOTTOM_LEFT, 'both claimed: other diagonal');
assert.strictEqual(inward(49, 21, set([[48, 20]]), set([[48, 21]])), BOTTOM_LEFT, 'wall skipped');
assert.strictEqual(inward(0, 21, no, set([[1, 21]])), TOP_RIGHT, 'left border');
assert.strictEqual(inward(20, 0, no, no), BOTTOM, 'top border');
assert.strictEqual(inward(20, 49, no, set([[20, 48]])), TOP_LEFT, 'bottom border');
assert.strictEqual(inward(49, 21, no, set([[48, 20], [48, 21], [48, 22]])), LEFT, 'all busy: straight (old behaviour)');
console.log('border_step ok 8');
