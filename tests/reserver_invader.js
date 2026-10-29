// 05:4x strategy: after Invader-core kill, residual Invader reservation blocks harvest (ERR_NOT_OWNER).
// Reserver must attackController on Invader only; never on a player (diplomacy / reserve7 same rule).
const path = require('path'), assert = require('assert'), ROOT = path.join(__dirname, '..');
const { reserverAct } = require(path.join(ROOT, 'src/roles/remote.js'));
assert.strictEqual(reserverAct({ ours: 'Misaki', resUser: null }), 'reserve', 'unreserved');
assert.strictEqual(reserverAct({ ours: 'Misaki', resUser: undefined }), 'reserve', 'no reservation');
assert.strictEqual(reserverAct({ ours: 'Misaki', resUser: 'Misaki' }), 'reserve', 'ours');
assert.strictEqual(reserverAct({ ours: 'Misaki', resUser: 'Invader' }), 'attackInvader', 'Invader');
assert.strictEqual(reserverAct({ ours: 'Misaki', resUser: 'BustJetter' }), 'wait', 'player');
assert.strictEqual(reserverAct({ ours: 'Misaki', resUser: 'fhl' }), 'wait', 'abandoned-owner name still wait');
console.log('reserver_invader tests passed');
