// Build + syntax check + load smoke test with a mocked Game (one tick).
const { execSync } = require('child_process'), fs = require('fs'), path = require('path'), vm = require('vm');
execSync('node ' + path.join(__dirname, 'build.js'), { stdio: 'inherit' });
const DIST = path.join(__dirname, '..', 'dist');
for (const f of fs.readdirSync(DIST)) execSync(`node --check ${path.join(DIST, f)}`);
const mods = {}; for (const f of fs.readdirSync(DIST)) mods[f.slice(0, -3)] = fs.readFileSync(path.join(DIST, f), 'utf8');
const cache = {};
const g = { console, Memory: {}, _: { countBy: (o, fn) => Object.values(o).reduce((a, x) => (a[fn(x)] = (a[fn(x)] || 0) + 1, a), {}) },
  Game: { time: 1, creeps: {}, spawns: {}, rooms: {}, gcl: { level: 1, progress: 0, progressTotal: 1 }, cpu: { bucket: 10000, getUsed: () => 0 } } };
function req(n) { if (cache[n]) return cache[n].exports; if (!(n in mods)) throw new Error('missing module ' + n);
  const m = cache[n] = { exports: {} }; vm.runInNewContext(`(function(module,exports,require){${mods[n]}\n})`, g)(m, m.exports, req); return m.exports; }
// mock one owned RCL3 room so managers execute
const consts = { FIND_MY_CONSTRUCTION_SITES: 1, FIND_HOSTILE_CREEPS: 2, FIND_MY_STRUCTURES: 3, FIND_MY_CREEPS: 4, FIND_STRUCTURES: 5, FIND_SOURCES: 6,
  STRUCTURE_TOWER: 'tower', STRUCTURE_EXTENSION: 'extension', STRUCTURE_RAMPART: 'rampart', STRUCTURE_ROAD: 'road', STRUCTURE_CONTAINER: 'container', OK: 0 };
Object.assign(g, consts);
let sites = 0;
g.Game.rooms.W46N8 = { name: 'W46N8', memory: {}, controller: { my: true, level: 3, progress: 0, progressTotal: 1 }, energyAvailable: 300, energyCapacityAvailable: 300,
  find: () => [], createConstructionSite: () => (sites++, 0) };
req('main').loop();
if (sites !== 5) throw new Error('layout manager placed ' + sites + ' sites, expected 5');
if (!g.Memory.stats || g.Memory.stats.errors.length) throw new Error('smoke test failed: ' + JSON.stringify(g.Memory.stats));
console.log('checks passed:', Object.keys(mods).length, 'modules');
