// Multi-tick simulation of the built bot against a snapshot of the live room (data/sim_snapshot.json).
// Not a full Screeps engine: movement ignores terrain/obstacles except structures, actions just move energy.
// Purpose: catch exceptions, check layout decisions and that every role acts. Usage: node scripts/sim.js [ticks]
const fs = require('fs'), path = require('path'), vm = require('vm');
const ROOT = path.join(__dirname, '..'), DIST = path.join(ROOT, 'dist');
const snap = JSON.parse(fs.readFileSync(process.env.SIM_SNAP || path.join(ROOT, 'data/sim_snapshot.json')));
const TICKS = +(process.argv[2] || 60);
const mods = {}; for (const f of fs.readdirSync(DIST)) mods[f.slice(0, -3)] = fs.readFileSync(path.join(DIST, f), 'utf8');
const C = { OK: 0, ERR_NOT_IN_RANGE: -9, ERR_NOT_ENOUGH_ENERGY: -6, ERR_INVALID_TARGET: -7, ERR_FULL: -8, ERR_RCL_NOT_ENOUGH: -14, ERR_NOT_ENOUGH_RESOURCES: -6,
  FIND_CREEPS: 101, FIND_MY_CREEPS: 102, FIND_HOSTILE_CREEPS: 103, FIND_SOURCES: 105, FIND_DROPPED_RESOURCES: 106, FIND_STRUCTURES: 107,
  FIND_MY_STRUCTURES: 108, FIND_CONSTRUCTION_SITES: 111, FIND_MY_CONSTRUCTION_SITES: 114, FIND_SOURCES_ACTIVE: 104, LOOK_RESOURCES: 'resource',
  RESOURCE_ENERGY: 'energy', WORK: 'work', CARRY: 'carry', MOVE: 'move', ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack', HEAL: 'heal', CLAIM: 'claim', TOUGH: 'tough',
  TOP: 1, RIGHT: 3, BOTTOM: 5, LEFT: 7, LOOK_SOURCES: 'source', LOOK_CREEPS: 'creep', FIND_CONSTRUCTION_SITES: 111, LOOK_STRUCTURES: 'structure', LOOK_CONSTRUCTION_SITES: 'constructionSite', BODYPART_COST: { work: 100, carry: 50, move: 50, attack: 80, ranged_attack: 150, heal: 250, claim: 600, tough: 10 }, EVENT_ATTACK: 1, TERRAIN_MASK_WALL: 1, TERRAIN_MASK_SWAMP: 2 };
for (const t of ['spawn', 'extension', 'road', 'wall', 'rampart', 'link', 'storage', 'tower', 'observer', 'powerSpawn', 'extractor', 'lab', 'terminal', 'container', 'nuker', 'factory', 'controller'])
  C['STRUCTURE_' + t.replace(/[A-Z]/g, m => '_' + m).toUpperCase()] = t;
C.EXTENSION_ENERGY_CAPACITY = { 0: 50, 1: 50, 2: 50, 3: 50, 4: 50, 5: 50, 6: 50, 7: 100, 8: 200 };
C.CONTROLLER_STRUCTURES = { extension: [0, 0, 5, 10, 20, 30, 40, 50, 60], tower: [0, 0, 0, 1, 1, 2, 2, 3, 6], container: [5, 5, 5, 5, 5, 5, 5, 5, 5], road: Array(9).fill(2500), rampart: [0, 0, 2500, 2500, 2500, 2500, 2500, 2500, 2500], storage: [0, 0, 0, 0, 1, 1, 1, 1, 1], link: [0, 0, 0, 0, 0, 2, 3, 4, 6], spawn: [0, 1, 1, 1, 1, 1, 1, 2, 3] };
const T = fs.readFileSync(path.join(ROOT, 'data/terrain_W46N8.txt'), 'utf8');
const isWall = (x, y) => T[y * 50 + x] === '1' || T[y * 50 + x] === '3';
let objs = {}; let nid = 1; const log = []; const errors = [];
const range = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
class RoomPosition { constructor(x, y, r) { this.x = x; this.y = y; this.roomName = r || 'W46N8'; }
  getRangeTo(a, b) { const p = typeof a === 'number' ? { x: a, y: b } : (a.pos || a); return range(this, p); }
  inRangeTo(a, b, c) { if (typeof a === 'number') return range(this, { x: a, y: b }) <= c; return range(this, a.pos || a) <= b; }
  isNearTo(a, b) { return this.getRangeTo(a, b) <= 1; }
  getDirectionTo(x, y) { if (typeof x !== 'number') { y = (x.pos || x).y; x = (x.pos || x).x; } const dx = Math.sign(x - this.x), dy = Math.sign(y - this.y);
    return { '0,-1': 1, '1,-1': 2, '1,0': 3, '1,1': 4, '0,1': 5, '-1,1': 6, '-1,0': 7, '-1,-1': 8 }[dx + ',' + dy] || 1; }
  findClosestByRange(arr) { return arr.slice().sort((a, b) => this.getRangeTo(a) - this.getRangeTo(b))[0] || null; }
  findInRange(type, r, o) { return room.find(type, o).filter(x => this.getRangeTo(x) <= r); }
  findClosestByPath(type, o) { return this.findClosestByRange(room.find(type, o)); } }
const DIRS = { 1: [0, -1], 2: [1, -1], 3: [1, 0], 4: [1, 1], 5: [0, 1], 6: [-1, 1], 7: [-1, 0], 8: [-1, -1] };
function store(cap, e = 0) { const s = { energy: e }; Object.defineProperty(s, 'getFreeCapacity', { value: () => cap - s.energy }); Object.defineProperty(s, 'getCapacity', { value: () => cap }); Object.defineProperty(s, 'getUsedCapacity', { value: () => s.energy }); return s; }
const CAP = { spawn: 300, extension: 50, tower: 1000, container: 2000, storage: 1e6, link: 800 };
const OBSTACLE = new Set(['spawn', 'extension', 'tower', 'storage', 'link', 'terminal', 'lab', 'factory', 'powerSpawn', 'nuker', 'observer', 'wall', 'extractor']);
function mkStruct(type, x, y, my, e = 0, extra = {}) {
  const s = Object.assign({ id: 's' + nid++, structureType: type, pos: new RoomPosition(x, y), my, hits: 1000, hitsMax: 5000, ticksToDecay: 500 }, extra);
  if (CAP[type]) s.store = store(CAP[type], e);
  s.destroy = () => { delete objs[s.id]; log.push(`DESTROY ${type} ${x},${y}`); return 0; };
  s.transferEnergy = t => { const a = s.store.energy; t.store.energy += a; s.store.energy = 0; s.cooldown = 3; return 0; };
  s.attack = s.heal = s.repair = () => 0;
  objs[s.id] = s; return s;
}
let room, sites = [];
const g = { console: { log: m => log.push(String(m)) }, Memory: { creeps: {} }, RoomPosition, Creep: function () {}, RawMemory: { segments: {}, setActiveSegments() {} } };
Object.assign(g, C);
g.PathFinder = { CostMatrix: class { constructor() { this.a = new Uint8Array(2500); } get(x, y) { return this.a[x * 50 + y]; } set(x, y, v) { this.a[x * 50 + y] = v; } clone() { const c = new g.PathFinder.CostMatrix(); c.a = this.a.slice(); return c; } },
  search(from, goal) { // BFS on terrain + obstacle structures
    const tgt = goal.pos, r = goal.range || 0, blocked = new Set(Object.values(objs).filter(o => o.structureType && OBSTACLE.has(o.structureType)).map(o => o.pos.x * 50 + o.pos.y));
    const prev = new Map([[from.x * 50 + from.y, -1]]); const q = [from.x * 50 + from.y]; let end = null;
    while (q.length) { const k = q.shift(), x = Math.floor(k / 50), y = k % 50; if (range({ x, y }, tgt) <= r) { end = k; break; }
      for (const [dx, dy] of Object.values(DIRS)) { const nx = x + dx, ny = y + dy, nk = nx * 50 + ny; if (nx < 1 || ny < 1 || nx > 48 || ny > 48 || prev.has(nk) || isWall(nx, ny)) continue;
        if (blocked.has(nk) && !(range({ x: nx, y: ny }, tgt) <= r && false)) continue; prev.set(nk, k); q.push(nk); } }
    const path = []; if (end !== null) { let k = end; while (prev.get(k) !== -1) { path.unshift(new RoomPosition(Math.floor(k / 50), k % 50)); k = prev.get(k); } }
    return { path, incomplete: end === null };
  } };
const lod = { countBy: (o, fn) => Object.values(o).reduce((a, x) => (a[fn(x)] = (a[fn(x)] || 0) + 1, a), {}), groupBy: (a, fn) => a.reduce((o, x) => ((o[fn(x)] = o[fn(x)] || []).push(x), o), {}),
  filter: (o, fn) => Object.values(o).filter(fn), some: (o, fn) => Object.values(o).some(fn), sum: (a, fn) => a.reduce((t, x) => t + (fn ? fn(x) : x), 0),
  max: (a, fn) => a.reduce((b, x) => (b === undefined || fn(x) > fn(b) ? x : b), undefined), min: (a, fn) => a.reduce((b, x) => (b === undefined || fn(x) < fn(b) ? x : b), undefined) };
g._ = lod;
// --- build room from snapshot
const ctlObj = snap.objects.find(o => o.type === 'controller');
room = { name: 'W46N8', memory: {}, get storage() { return Object.values(objs).find(o => o.structureType === 'storage'); },
  controller: { id: ctlObj._id, my: true, level: ctlObj.level, progress: ctlObj.progress, progressTotal: 135000, pos: new RoomPosition(ctlObj.x, ctlObj.y), safeModeAvailable: 2, structureType: 'controller' },
  get energyAvailable() { return Object.values(objs).filter(o => o.structureType === 'spawn' || o.structureType === 'extension').reduce((t, o) => t + o.store.energy, 0); },
  get energyCapacityAvailable() { return Object.values(objs).filter(o => o.structureType === 'spawn' || o.structureType === 'extension').reduce((t, o) => t + CAP[o.structureType], 0); },
  getEventLog: () => [], getTerrain: () => ({ get: (x, y) => isWall(x, y) ? 1 : 0 }), lookForAtArea: () => [], lookForAt: (t, x, y) => Object.values(objs).filter(o => o.body && o.pos.x === x && o.pos.y === y),
  find(type, opts) { let r;
    const all = Object.values(objs);
    switch (type) {
      case C.FIND_STRUCTURES: r = all.filter(o => o.structureType); break;
      case C.FIND_MY_STRUCTURES: r = all.filter(o => o.structureType && o.my); break;
      case C.FIND_SOURCES: case C.FIND_SOURCES_ACTIVE: r = all.filter(o => o.isSource); break;
      case C.FIND_MY_CONSTRUCTION_SITES: case C.FIND_CONSTRUCTION_SITES: r = sites.slice(); break;
      case C.FIND_HOSTILE_CREEPS: r = []; break;
      case C.FIND_MY_CREEPS: case C.FIND_CREEPS: r = Object.values(g.Game.creeps); break;
      default: r = [];
    }
    if (opts && opts.filter) r = typeof opts.filter === 'function' ? r.filter(opts.filter) : r.filter(o => Object.entries(opts.filter).every(([k, v]) => o[k] === v));
    return r; },
  createConstructionSite(x, y, type) {
    if (Object.values(objs).some(o => o.structureType && o.pos.x === x && o.pos.y === y && o.structureType !== 'rampart' && type !== 'rampart' && !(o.structureType === 'road' && type === 'road' && false))) return C.ERR_INVALID_TARGET;
    const lim = C.CONTROLLER_STRUCTURES[type]; const n = Object.values(objs).filter(o => o.structureType === type).length + sites.filter(s => s.structureType === type).length;
    if (lim && n >= lim[room.controller.level]) return C.ERR_RCL_NOT_ENOUGH;
    const s = { id: 'c' + nid++, structureType: type, pos: new RoomPosition(x, y), progress: 0, progressTotal: type === 'extension' ? 3000 : 300, my: true, remove() { sites = sites.filter(z => z !== s); log.push(`REMOVE site ${type} ${x},${y}`); return 0; } };
    sites.push(s); return 0; } };
for (const o of snap.objects) {
  if (['road', 'container', 'spawn', 'extension', 'tower', 'rampart', 'storage', 'link'].includes(o.type)) {
    const s = mkStruct(o.type, o.x, o.y, o.user === snap.uid, (o.store || {}).energy || 0, { hits: o.hits || 1000, name: o.name });
    if (o.type === 'spawn') { s.spawning = null; s.room = room; s.spawnCreep = (body, name, opt) => { const cost = body.reduce((t, p) => t + C.BODYPART_COST[p], 0); if (room.energyAvailable < cost) return C.ERR_NOT_ENOUGH_ENERGY;
      let left = cost; for (const e of Object.values(objs).filter(o => o.structureType === 'spawn' || o.structureType === 'extension')) { const d = Math.min(left, e.store.energy); e.store.energy -= d; left -= d; }
      mkCreep(name, body, s.pos.x, s.pos.y + 1, opt.memory); log.push(`SPAWN ${name} ${body.length}`); return 0; }; g.Game_spawns = g.Game_spawns || {}; g.Game_spawns[o.name] = s; }
  } else if (o.type === 'source') { objs[o._id] = { id: o._id, isSource: true, pos: new RoomPosition(o.x, o.y), energy: 3000, energyCapacity: 3000 }; }
}
function mkCreep(name, body, x, y, memory) {
  const c = { id: 'k' + nid++, name, body: body.map(t => ({ type: t, hits: 100 })), pos: new RoomPosition(x, y), memory, fatigue: 0, ticksToLive: 1400, my: true, hits: 100, hitsMax: 100,
    store: store(body.filter(b => b === 'carry').length * 50), acts: 0,
    getActiveBodyparts: t => body.filter(b => b === t).length,
    move(d) { const [dx, dy] = DIRS[d]; const nx = c.pos.x + dx, ny = c.pos.y + dy; if (isWall(nx, ny) || Object.values(objs).some(o => o.structureType && OBSTACLE.has(o.structureType) && o.pos.x === nx && o.pos.y === ny)) return -2; c.pos = new RoomPosition(nx, ny); c.acts++; return 0; },
    moveTo(t) { const p = t.pos || t; return c.move(c.pos.getDirectionTo(p.x, p.y)); },
    transfer(t, r, a) { if (range(c.pos, t.pos) > 1) return C.ERR_NOT_IN_RANGE; const n = Math.min(c.store.energy, t.store.getFreeCapacity('energy')); t.store.energy += n; c.store.energy -= n; c.acts++; return 0; },
    withdraw(t) { if (range(c.pos, t.pos) > 1) return C.ERR_NOT_IN_RANGE; const n = Math.min(t.store.energy, c.store.getFreeCapacity()); t.store.energy -= n; c.store.energy += n; c.acts++; return 0; },
    pickup() { return 0; }, drop() { c.store.energy = 0; return 0; },
    harvest(s) { if (range(c.pos, s.pos) > 1) return C.ERR_NOT_IN_RANGE; const n = c.getActiveBodyparts('work') * 2; const cont = Object.values(objs).find(o => o.structureType === 'container' && o.pos.x === c.pos.x && o.pos.y === c.pos.y);
      if (c.store.getFreeCapacity() > 0) c.store.energy = Math.min(c.store.getCapacity(), c.store.energy + n); else if (cont) cont.store.energy = Math.min(2000, cont.store.energy + n); c.acts++; return 0; },
    upgradeController(ctl) { if (range(c.pos, ctl.pos) > 3) return C.ERR_NOT_IN_RANGE; const n = Math.min(c.store.energy, c.getActiveBodyparts('work')); c.store.energy -= n; ctl.progress += n; c.acts++; return 0; },
    build(s) { if (range(c.pos, s.pos) > 3) return C.ERR_NOT_IN_RANGE; const n = Math.min(c.store.energy, c.getActiveBodyparts('work') * 5); c.store.energy -= n; s.progress += n; c.acts++;
      if (s.progress >= s.progressTotal) { sites = sites.filter(z => z !== s); mkStruct(s.structureType, s.pos.x, s.pos.y, true); log.push(`BUILT ${s.structureType} ${s.pos.x},${s.pos.y}`); } return 0; },
    repair(s) { if (range(c.pos, s.pos) > 3) return C.ERR_NOT_IN_RANGE; c.acts++; return 0; },
    dismantle(s) { if (range(c.pos, s.pos) > 1) return C.ERR_NOT_IN_RANGE; const n = c.getActiveBodyparts('work') * 50; s.hits = Math.max(0, (s.hits || 0) - n); c.acts++;
      if (s.hits <= 0) { delete objs[s.id]; log.push(`DISMANTLE ${s.structureType} ${s.pos.x},${s.pos.y}`); } return 0; } };
  Object.defineProperty(c, 'room', { get: () => room });
  g.Game.creeps[name] = c; objs[c.id] = c; g.Memory.creeps[name] = memory; return c;
}
g.Game = { time: 83607700, creeps: {}, spawns: {}, rooms: { W46N8: room }, gcl: { level: 2, progress: 0, progressTotal: 1 }, cpu: { bucket: 10000, getUsed: () => 0 }, getObjectById: id => objs[id] || sites.find(s => s.id === id) || (id === room.controller.id ? room.controller : null) };
g.Game.spawns = g.Game_spawns;
// creeps from snapshot
for (const o of snap.objects.filter(o => o.type === 'creep' && o.user === snap.uid)) {
  const mem = snap.creepMem[o.name] || { role: 'hauler' };
  const body = o.body.map(b => b.type);
  const c = mkCreep(o.name, body, o.x, o.y, mem); c.store.energy = (o.store || {}).energy || 0; c.ticksToLive = o.ageTime ? o.ageTime - g.Game.time : 800;
}
// fill extensions partially, containers
const cache = {};
function req(n) { if (cache[n]) return cache[n].exports; if (!(n in mods)) throw new Error('missing module ' + n);
  const m = cache[n] = { exports: {} }; vm.runInNewContext(`(function(module,exports,require){${mods[n]}\n})`, g)(m, m.exports, req); return m.exports; }
const main = req('main');
const startPos = Object.fromEntries(Object.values(g.Game.creeps).map(c => [c.name, c.pos.x + ',' + c.pos.y]));
for (let t = 0; t < TICKS; t++) {
  g.Game.time++;
  for (const s of Object.values(objs)) if (s.cooldown) s.cooldown--;
  try { main.loop(); } catch (e) { errors.push(e.stack); break; }
  for (const c of Object.values(g.Game.creeps)) { c.fatigue = 0; c.ticksToLive--; }
  // sources regen not modelled; refill containers a bit to emulate miners
}
const errs = (g.Memory.stats && g.Memory.stats.errors) || [];
const out = { ticks: TICKS, errors: errs.concat(errors), creeps: Object.values(g.Game.creeps).map(c => ({ n: c.name, role: c.memory.role, from: startPos[c.name], to: c.pos.x + ',' + c.pos.y, acts: c.acts, e: c.store.energy })),
  sites: sites.map(s => `${s.structureType} ${s.pos.x},${s.pos.y}`), log: log.filter(l => /LAYOUT|DESTROY|REMOVE|SPAWN|BUILT|ERR|CS |STUCK|^DBG/.test(l)).slice(-400),
  mem: Object.fromEntries(Object.values(g.Game.creeps).map(c => [c.name, c.memory])), prog: sites.map(s => s.progress), energy: `${room.energyAvailable}/${room.energyCapacityAvailable}`, ctlProgress: room.controller.progress, seg90: (g.RawMemory.segments[90] || '').length,
  repaths: (() => { const R = JSON.parse(g.RawMemory.segments[90] || '{"s":[]}'), o = {}; for (const [, rows] of R.s) for (const r of rows) { const role = r[0].replace(/[0-9]/g, ''); o[role] = (o[role] || 0) + r[4]; for (const ch of (r[7] || '')) o[role + ':' + ch] = (o[role + ':' + ch] || 0) + 1; } return o; })() };
console.log(JSON.stringify(out, null, 1));
if (out.errors.length) process.exit(1);
