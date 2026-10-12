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
req('main').loop();
if (!g.Memory.stats || g.Memory.stats.errors.length) throw new Error('smoke test failed: ' + JSON.stringify(g.Memory.stats));
console.log('checks passed:', Object.keys(mods).length, 'modules');
