// Build + syntax check + multi-tick simulation against the live-room snapshot (scripts/sim.js).
// Fails on any exception/caught error, or if creeps stop acting.
const { execSync } = require('child_process'), fs = require('fs'), path = require('path');
execSync('node ' + path.join(__dirname, 'build.js'), { stdio: 'inherit' });
const DIST = path.join(__dirname, '..', 'dist');
for (const f of fs.readdirSync(DIST)) execSync(`node --check ${path.join(DIST, f)}`);
const out = JSON.parse(execSync(`node ${path.join(__dirname, 'sim.js')} 600`, { maxBuffer: 1 << 26 }).toString());
if (out.errors.length) throw new Error('sim errors: ' + out.errors.slice(0, 3).join('\n'));
const idle = out.creeps.filter(c => c.acts < 50 && c.from);
if (idle.length > 2) throw new Error('too many idle creeps in sim: ' + JSON.stringify(idle));
if (!out.log.some(l => l.startsWith('LAYOUT'))) throw new Error('layout manager did nothing in sim');
console.log(`checks passed: ${fs.readdirSync(DIST).length} modules; sim 600 ticks, 0 errors, energy ${out.energy}, ${out.creeps.length} creeps`);
