// visuals: routes derived from simulated creep movement (remote loaded trip across rooms + home legs), toggle, bucket gate.
const assert = require('assert'); const calls = [];
global.Game = { time: 1, cpu: { bucket: 10000 }, creeps: {}, rooms: {} }; global.Memory = {};
global.RoomVisual = function (r) { this.poly = (p, s) => calls.push(['poly', r, p.length, s.stroke, s.lineStyle]); this.text = () => calls.push(['text', r]); this.line = () => {}; };
const v = require('../src/managers/visuals');
const mk = (name, role, extra) => (Game.creeps[name] = Object.assign({ name, spawning: false, memory: { role }, pos: { x: 0, y: 0 }, room: { name: 'W46N8' }, store: { e: 0, getUsedCapacity() { return this.e; } } }, extra || {}));
const rh = mk('rh', 'rhauler'); rh.memory.remote = 'W45N8'; const hh = mk('hh', 'hauler');
const trip = [['W45N8', 20, 10], ['W45N8', 21, 11], ['W45N8', 49, 12], ['W46N8', 0, 12], ['W46N8', 1, 13], ['W46N8', 30, 28]];
hh.memory._m = { k: '30,28,1' }; const leg = [[10, 10], [11, 11], [12, 12], [13, 13], [14, 14]];
for (let i = 0; i < 8; i++) {
  Game.time++; rh.store.e = i < trip.length ? 100 : 0;
  if (i < trip.length) { rh.room = { name: trip[i][0] }; rh.pos = { x: trip[i][1], y: trip[i][2] }; }
  if (i < leg.length) hh.pos = { x: leg[i][0], y: leg[i][1] }; else delete hh.memory._m;
  v.record();
}
const out = v.build();
assert.deepStrictEqual(out.legend.map(l => l.label + ' ' + l.len), ['外矿 W45N8 5', '运输 (30,28)↔出发点 4']);
assert(out.rooms.W45N8 && out.rooms.W46N8, 'remote route split per room');
assert.strictEqual(Memory.routesLive[0].pts.split(';')[0], 'W45N8:20:10', 'pts are the real positions');
Game.time += 100; v.run(); const polys = calls.filter(c => c[0] === 'poly');
assert(polys.length >= 3 && polys.every(p => p[4] === 'dashed') && new Set(polys.map(p => p[3])).size === 2, 'dashed, distinct colours');
calls.length = 0; Memory.visuals = { routes: false }; v.run(); assert.strictEqual(calls.length, 0, 'toggle off');
Memory.visuals = {}; Game.cpu.bucket = 1500; v.run(); assert.strictEqual(calls.length, 0, 'low bucket');
console.log('visuals ok', out.legend.map(l => l.label + ' ' + l.len).join(' | '));
