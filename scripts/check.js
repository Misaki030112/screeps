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
if (!Object.keys(out.idle || {}).length) throw new Error('trace state codes missing in segment 90');
console.log('sim state codes per role (last 300 ticks):', JSON.stringify(out.idle));
// birth side: only queen/fillers may be born inside an extension stamp
const fill = new Set([].concat(...Object.values(require(path.join(__dirname, '..', 'src', 'layouts', 'W46N8.js')).stamps).map(st => Object.keys(st.tiles))));
// (first birth only: later ones may legitimately fall back inside while sim creeps still stand on the outside tiles)
const badBirth = (out.births || []).slice(0, 1).filter(([, role, x, y]) => !['queen', 'filler'].includes(role) && fill.has(`${x},${y}`));
if (badBirth.length) throw new Error('creeps born inside the stamp: ' + JSON.stringify(badBirth));
console.log('births:', JSON.stringify(out.births));
if (!out.log.some(l => l.startsWith('LAYOUT'))) throw new Error('layout manager did nothing in sim');
if (!(out.seg90 > 100 && out.seg90 < 90000)) throw new Error('trace segment 90 missing/too big: ' + out.seg90);
console.log(`checks passed: ${fs.readdirSync(DIST).length} modules; sim 600 ticks, 0 errors, energy ${out.energy}, ${out.creeps.length} creeps`);
// threat FSM unit tests (incl. the code-level enable gate armed()) + defender duel on real terrain driven by the real FSM
execSync('node ' + path.join(__dirname, '..', 'tests', 'threat_fsm.js'), { stdio: 'pipe' });
execSync('node ' + path.join(__dirname, '..', 'tests', 'defender_duel.js'), { stdio: 'pipe' });
execSync('node ' + path.join(__dirname, '..', 'tests', 'queen_standby.js'), { stdio: 'pipe' });
execSync('node ' + path.join(__dirname, '..', 'tests', 'spawn_upgraders.js'), { stdio: 'pipe' });
execSync('node ' + path.join(__dirname, '..', 'tests', 'builder_remote.js'), { stdio: 'pipe' });
execSync('node ' + path.join(__dirname, '..', 'tests', 'spawn_rhauler.js'), { stdio: 'pipe' });
execSync('node ' + path.join(__dirname, '..', 'tests', 'rcl5_gate.js'), { stdio: 'pipe' });
console.log('threat FSM tests + defender duel + queen standby + spawn upgraders + builder remote + spawn rhauler + rcl5 gate passed');
