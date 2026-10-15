// rminer pre-spawn lead = travel + 3*body + 10 (src/managers/spawn.js remoteSpawn). node tests/rminer_lead.js
const assert = require('assert'), fs = require('fs');
const s = fs.readFileSync(__dirname + '/../src/managers/spawn.js', 'utf8');
const m = s.match(/const rmLead = (c => [^;]+);/); assert(m, 'rmLead missing');
const rmLead = eval(m[1]);
const body = new Array(9);
assert.strictEqual(rmLead({ memory: { travel: 94 }, body }), 94 + 27 + 10); // new arrives 10t before old dies
assert.strictEqual(rmLead({ memory: {}, body }), 110 + 27 + 10);
assert.strictEqual(rmLead({ memory: { travel: 999 }, body }), 160 + 27 + 10); // capped
assert(fs.readFileSync(__dirname + '/../src/roles/remote.js', 'utf8').includes('c.memory.travel = t >= 0 && t <= 300'));
console.log('rminer_lead ok');
