// Build + syntax check + load smoke test with a mocked Game (one tick).
const { execSync } = require('child_process'), fs = require('fs'), path = require('path'), vm = require('vm');
execSync('node ' + path.join(__dirname, 'build.js'), { stdio: 'inherit' });
const DIST = path.join(__dirname, '..', 'dist');
for (const f of fs.readdirSync(DIST)) execSync(`node --check ${path.join(DIST, f)}`);
const mods = {}; for (const f of fs.readdirSync(DIST)) mods[f.slice(0, -3)] = fs.readFileSync(path.join(DIST, f), 'utf8');
const cache = {};
const g = { console, Memory: {}, _: { groupBy: (a, fn) => a.reduce((o, x) => ((o[fn(x)] = o[fn(x)] || []).push(x), o), {}), countBy: (o, fn) => Object.values(o).reduce((a, x) => (a[fn(x)] = (a[fn(x)] || 0) + 1, a), {}) },
  Game: { getObjectById: () => null, time: 1, creeps: {}, spawns: {}, rooms: {}, gcl: { level: 1, progress: 0, progressTotal: 1 }, cpu: { bucket: 10000, getUsed: () => 0 } } };
function req(n) { if (cache[n]) return cache[n].exports; if (!(n in mods)) throw new Error('missing module ' + n);
  const m = cache[n] = { exports: {} }; vm.runInNewContext(`(function(module,exports,require){${mods[n]}\n})`, g)(m, m.exports, req); return m.exports; }
// mock one owned RCL3 room so managers execute
const consts = { FIND_MY_CONSTRUCTION_SITES: 1, FIND_HOSTILE_CREEPS: 2, FIND_MY_STRUCTURES: 3, FIND_MY_CREEPS: 4, FIND_STRUCTURES: 5, FIND_SOURCES: 6, FIND_DROPPED_RESOURCES: 7,
  STRUCTURE_TOWER: 'tower', STRUCTURE_EXTENSION: 'extension', STRUCTURE_RAMPART: 'rampart', STRUCTURE_ROAD: 'road', STRUCTURE_CONTAINER: 'container', OK: 0, ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack', WORK: 'work', CLAIM: 'claim', HEAL: 'heal', EVENT_ATTACK: 1 };
Object.assign(g, consts);
let sites = 0;
g.Game.rooms.W46N8 = { name: 'W46N8', memory: {}, controller: { my: true, level: 3, progress: 0, progressTotal: 1 }, energyAvailable: 300, energyCapacityAvailable: 300,
  getEventLog: () => [], find: t => t === 2 ? [{ owner: { username: 'nb' }, body: [{ type: 'work', hits: 100 }, { type: 'move', hits: 100 }], pos: { x: 1, y: 1 } }] : [], createConstructionSite: () => (sites++, 0) };
const logs = []; const ol = g.console.log; g.console = { log: m => logs.push(m) };
let spawned = [];
g.Game.spawns.Spawn1 = { spawning: null, room: g.Game.rooms.W46N8, spawnCreep: (b, n, o) => (spawned.push([b, o.memory]), 0) };
g.FIND_MY_CONSTRUCTION_SITES = 1; g.FIND_SOURCES = 6; g.WORK = 'work'; g.CARRY = 'carry'; g.MOVE = 'move';
g._.filter = (o, fn) => Object.values(o).filter(fn);
req('main').loop();
g.console = console;
if (spawned.length !== 1 || spawned[0][1].role !== 'harvester') throw new Error('spawn test failed ' + JSON.stringify(spawned));
// 2nd scenario: one hauler alive, no backlog -> spawner tops haulers up to 2
g._.sum = (a, fn) => a.reduce((t, x) => t + fn(x), 0); g.RESOURCE_ENERGY = 'energy';
const room2 = Object.assign({}, g.Game.rooms.W46N8, { find: () => [] });
g.Game.creeps = { h1: { room: room2, memory: { role: 'hauler', home: 'W46N8' }, body: [] } };
spawned = []; req('managers.spawn').run(Object.assign({}, g.Game.spawns.Spawn1, { room: room2 }));
g.Game.creeps = {};
if (spawned.length !== 1 || spawned[0][1].role !== 'hauler' || spawned[0][0].length !== 6) throw new Error('hauler spawn test failed ' + JSON.stringify(spawned));
const al = logs.filter(l => l.startsWith('ALERT ')).map(l => JSON.parse(l.slice(6)));
if (al.length !== 1 || al[0].severity !== 'low') throw new Error('alert test failed ' + JSON.stringify(logs));
if (sites !== 5) throw new Error('layout manager placed ' + sites + ' sites, expected 5');
if (!g.Memory.stats || g.Memory.stats.errors.length) throw new Error('smoke test failed: ' + JSON.stringify(g.Memory.stats));
console.log('checks passed:', Object.keys(mods).length, 'modules');
