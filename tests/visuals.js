// visuals: per-room segments, legend, toggle + bucket gate.
const assert = require('assert'); const calls = [];
global.Game = { time: 1, cpu: { bucket: 10000 } }; global.Memory = {};
global.RoomVisual = function (r) { this.poly = (p, s) => calls.push(['poly', r, p.length, s.stroke]); this.text = () => calls.push(['text', r]); this.line = () => {}; };
const v = require('../src/managers/visuals');
v.run(); const rooms = new Set(calls.filter(c => c[0] === 'poly').map(c => c[1]));
assert(rooms.has('W46N8') && rooms.has('W45N8') && rooms.has('W45N7'), 'segments in all 3 rooms');
assert.strictEqual(new Set(calls.filter(c => c[0] === 'poly').map(c => c[3])).size, v.STYLE.length, 'distinct colours');
calls.length = 0; Memory.visuals = { routes: false }; v.run(); assert.strictEqual(calls.length, 0, 'toggle off');
Memory.visuals = {}; Game.cpu.bucket = 1500; v.run(); assert.strictEqual(calls.length, 0, 'low bucket');
console.log('visuals ok', v.build().legend.map(l => l.label + ' ' + l.len).join(' | '));
