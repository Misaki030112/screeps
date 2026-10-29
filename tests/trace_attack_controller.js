// attackController / claimController must count as work in trace — else Invader reclaim looks queue_blocked.
const path = require('path'), assert = require('assert');
const creeps = {};
function Creep() {}
Creep.prototype.attackController = function () { return 0; };
Creep.prototype.claimController = function () { return 0; };
Creep.prototype.reserveController = function () { return 0; };
Creep.prototype.getActiveBodyparts = function () { return 2; };
Object.assign(global, {
  Game: { time: 18, creeps },
  RawMemory: { segments: {}, setActiveSegments() {} },
  Creep,
  WORK: 'work', CLAIM: 'claim',
  OK: 0, ERR_NOT_IN_RANGE: -9,
});
const t = require(path.join(__dirname, '..', 'src/utils/trace.js'));
t.wrap();
const c = {
  name: 'reserverTest', spawning: false, pos: { x: 7, y: 41 }, room: { name: 'W45N7' },
  memory: { role: 'reserver', remote: 'W45N7' },
  getActiveBodyparts(p) { return p === 'claim' ? 2 : 0; },
  attackController(...a) { return Creep.prototype.attackController.apply(this, a); },
};
creeps[c.name] = c;
assert.strictEqual(c.attackController({}), 0);
t.tick();
t.tick(); Game.time = 20; t.run();
const rows = JSON.parse(RawMemory.segments[90]).s.pop()[1];
const sc = rows.find(r => r[0] === 'reserverTest')[8];
assert.ok(sc.includes('w'), 'attackController should mark work, got ' + sc);
console.log('trace_attack_controller ok', sc);
