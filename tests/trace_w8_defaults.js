// W47N8 roles get a real idle default (not 'q' queue_blocked) in the trace (strategy 2026-10-21 11:4x)
const path = require('path'), assert = require('assert');
const creeps = {};
Object.assign(global, { Game: { time: 18, creeps }, RawMemory: { segments: {}, setActiveSegments() {} } });
const t = require(path.join(__dirname, '..', 'src/utils/trace.js'));
const want = { w8upgrader: 'u', w8hauler: 'p', w8rhauler: 'p', w8miner: 'e', w8rminer: 'e', w8filler: 'f', w8builder: 'n', w8defender: 't', upgrader: 'u', zzz: 'q' };
for (const r in want) creeps['c_' + r] = { name: 'c_' + r, spawning: false, pos: { x: 5, y: 5 }, room: { name: 'W47N8' }, memory: { role: r } };
t.tick(); t.tick(); Game.time = 20; t.run();
const rows = JSON.parse(RawMemory.segments[90]).s.pop()[1];
for (const r in want) { const row = rows.find(x => x[0] === 'c_' + r); assert.strictEqual(row[8], want[r] + want[r], r); }
console.log('trace_w8_defaults ok', Object.keys(want).length);
