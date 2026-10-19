// rminer pre-spawn lead = travel + 3*body + 10 (src/managers/spawn.js remoteSpawn). node tests/rminer_lead.js
const assert = require('assert'), fs = require('fs');
const s = fs.readFileSync(__dirname + '/../src/managers/spawn.js', 'utf8');
const m = s.match(/const rmLead = (\(C, c\) => [^;]+);/); assert(m, 'rmLead missing');
const C = {}; const rmLead = c => eval(m[1])(C, c);
const body = new Array(9);
assert.strictEqual(rmLead({ memory: { travel: 94 }, body }), 94 + 27 + 10); // new arrives 10t before old dies
assert.strictEqual(rmLead({ memory: {}, body }), 110 + 27 + 10);
assert.strictEqual(rmLead({ memory: { travel: 999 }, body }), 160 + 27 + 10); // capped
assert(fs.readFileSync(__dirname + '/../src/roles/remote.js', 'utf8').includes('c.memory.travel = t >= 0 && t <= 300'));
// rminers of every remote are checked before any remote's reserver/rhauler (W45N7 rminer queued behind W45N8, 10-19 18:50)
const body_ = s.slice(s.indexOf('function remoteSpawn'));
assert(body_.indexOf("role === 'rminer' && (c.spawning || c.ticksToLive > rmLead(C, c))") < body_.indexOf('remoteNext({'), 'rminer pre-pass must come first');
console.log('rminer_lead ok');
