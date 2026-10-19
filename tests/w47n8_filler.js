// W47N8 hub filler (fill.js, Misaki 17:3x "spawn must never wait for energy"): strip routes, sweep rule, hauler hand-off,
// storage buffer, spawn rule, and a tick simulation on real terrain + the live 17:23 structures (fatigue modelled).
// Prints refill times; asserts refill bounds. node tests/w47n8_filler.js [--quiet]
const assert = require('assert'), fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..');
const T = fs.readFileSync(path.join(ROOT, 'data/terrain_W47N8.txt'), 'utf8').trim();
const SNAP = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/w47n8_fill_snapshot.json'))).s.map(r => r.split(' '));
const quiet = process.argv.includes('--quiet'), say = (...a) => quiet || console.log(...a);
Object.assign(global, { _: require('lodash'), FIND_MY_STRUCTURES: 10, FIND_STRUCTURES: 5, FIND_MY_CREEPS: 3, FIND_MY_CONSTRUCTION_SITES: 1, FIND_DROPPED_RESOURCES: 6,
  FIND_TOMBSTONES: 7, FIND_RUINS: 8, FIND_SOURCES_ACTIVE: 9, FIND_MY_SPAWNS: 2, FIND_HOSTILE_CREEPS: 4,
  STRUCTURE_EXTENSION: 'extension', STRUCTURE_SPAWN: 'spawn', STRUCTURE_TOWER: 'tower', STRUCTURE_ROAD: 'road', STRUCTURE_RAMPART: 'rampart', STRUCTURE_CONTAINER: 'container',
  STRUCTURE_STORAGE: 'storage', STRUCTURE_WALL: 'constructedWall', STRUCTURE_LINK: 'link', RESOURCE_ENERGY: 'energy', LOOK_STRUCTURES: 'ls', LOOK_CREEPS: 'lcr', LOOK_SOURCES: 'lso',
  LOOK_CONSTRUCTION_SITES: 'lc', OK: 0, ERR_NOT_IN_RANGE: -9, WORK: 'work', CARRY: 'carry', MOVE: 'move', ATTACK: 'attack', RANGED_ATTACK: 'ranged_attack', HEAL: 'heal', CLAIM: 'claim', TOUGH: 'tough',
  BODYPART_COST: { work: 100, carry: 50, move: 50 }, Memory: { ops: {} }, Game: { time: 1, rooms: {}, creeps: {}, getObjectById: id => OBJ[id] } });
const F = require(path.join(ROOT, 'src/rooms/w47n8/fill.js')), L = require(path.join(ROOT, 'src/rooms/w47n8/layout.js'));
const sum = (a, f) => a.reduce((t, x) => t + f(x), 0), K = (x, y) => x * 50 + y, cheb = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
// ---------- static route checks
assert.strictEqual(F.ROUTES.length, 4);
F.ROUTES.forEach((R, i) => {
  R.road.forEach((p, j) => j && assert.strictEqual(Math.max(Math.abs(p[0] - R.road[j - 1][0]), Math.abs(p[1] - R.road[j - 1][1])), 1, 'strip road contiguous'));
  for (const e of L.STRIPS[i].ext) assert.ok(R.ext[K(e[0], e[1])], 'every strip extension touches its road ' + e);
});
assert.deepStrictEqual(F.ENTRY(), [0, 1, 1, 1], 'entries: B1 north 38,30, B2 east 32,35, B3 south 31,28, B4 east 28,25');
// ---------- mini engine (terrain, obstacles, roads, fatigue, one move + one transfer/withdraw per tick)
let OBJ = {}, nid = 0;
class RoomPosition { constructor(x, y, r) { this.x = x; this.y = y; this.roomName = r || 'W47N8'; }
  getRangeTo(a, b) { const p = typeof a === 'number' ? { x: a, y: b } : (a.pos || a); return cheb(this, p); }
  inRangeTo(a, b, c) { return typeof a === 'number' ? cheb(this, { x: a, y: b }) <= c : cheb(this, a.pos || a) <= b; }
  isNearTo(a, b) { return this.getRangeTo(a, b) <= 1; }
  getDirectionTo(x, y) { const dx = Math.sign(x - this.x), dy = Math.sign(y - this.y); return { '0,-1': 1, '1,-1': 2, '1,0': 3, '1,1': 4, '0,1': 5, '-1,1': 6, '-1,0': 7, '-1,-1': 8 }[dx + ',' + dy]; }
  findClosestByRange(a) { return _.minBy(a, o => this.getRangeTo(o)); }
  findInRange(t, r, o) { return room.find(t, o).filter(x => this.getRangeTo(x) <= r); } }
global.RoomPosition = RoomPosition;
const DIRS = { 1: [0, -1], 2: [1, -1], 3: [1, 0], 4: [1, 1], 5: [0, 1], 6: [-1, 1], 7: [-1, 0], 8: [-1, -1] };
const OBST = new Set(['spawn', 'extension', 'tower', 'storage', 'link', 'constructedWall']);
const st = (cap, e) => { const s = { energy: e }; Object.defineProperties(s, { getFreeCapacity: { value: () => cap - s.energy }, getCapacity: { value: () => cap } }); return s; };
const CAPS = { spawn: 300, extension: 50, tower: 1000, container: 2000, storage: 1e6 };
const mkS = (t, x, y, e = 0, cap) => { const s = { id: 's' + nid++, structureType: t, my: true, pos: new RoomPosition(x, y), hits: 1, hitsMax: 1 }; if (CAPS[t]) s.store = st(cap || CAPS[t], Math.min(e, cap || CAPS[t])); OBJ[s.id] = s; return s; };
let room, creeps = [];
function build(extCap, extTiles) {
  OBJ = {}; creeps = []; const map = { ext: 'extension', spa: 'spawn', tow: 'tower', sto: 'storage', con: 'container', roa: 'road', lin: 'link' };
  for (const [t, x, y] of SNAP) if (map[t] && !(extTiles && t === 'ext')) mkS(map[t], +x, +y, 0, t === 'ext' ? extCap : undefined);
  if (extTiles) { for (const [x, y] of L.TEMP_EXT) mkS('extension', x, y, 0, extCap); for (const [x, y] of extTiles) mkS('extension', x, y, 0, extCap); }
  const all = () => Object.values(OBJ);
  room = { name: 'W47N8', controller: { level: 4, my: true },
    get energyAvailable() { return sum(all().filter(s => s.structureType === 'extension' || s.structureType === 'spawn'), s => s.store.energy); },
    get energyCapacityAvailable() { return sum(all().filter(s => s.structureType === 'extension' || s.structureType === 'spawn'), s => s.store.getCapacity()); },
    find: (t, o) => (t === 10 || t === 5 ? all().filter(s => s.structureType) : t === 3 ? creeps : []).filter((o && o.filter) || (() => true)),
    lookForAt: (k, x, y) => (k === 'ls' ? all().filter(s => s.structureType && s.pos.x === x && s.pos.y === y) : k === 'lcr' ? creeps.filter(c => c.pos.x === x && c.pos.y === y) : []) };
  room.storage = all().find(s => s.structureType === 'storage');
  Game.rooms.W47N8 = room;
}
const walk = (x, y) => x > 0 && y > 0 && x < 49 && y < 49 && !(+T[y * 50 + x] & 1) && !Object.values(OBJ).some(s => s.structureType && OBST.has(s.structureType) && s.pos.x === x && s.pos.y === y);
const tcost = (x, y) => (Object.values(OBJ).some(s => s.structureType === 'road' && s.pos.x === x && s.pos.y === y) ? 1 : +T[y * 50 + x] & 2 ? 10 : 2);
function route(from, to, r) { // Dijkstra with road 1 / plain 2 / swamp 10
  const dist = new Map([[K(from.x, from.y), 0]]), prev = new Map(), q = [[0, from.x, from.y]];
  while (q.length) { q.sort((a, b) => a[0] - b[0]); const [d, x, y] = q.shift(); if (cheb({ x, y }, to) <= r) { const out = []; let k = K(x, y); while (prev.has(k)) { out.unshift(k); k = prev.get(k); } return out; }
    if (d > dist.get(K(x, y))) continue;
    for (const [dx, dy] of Object.values(DIRS)) { const nx = x + dx, ny = y + dy, nk = K(nx, ny); if (!walk(nx, ny)) continue; const nd = d + tcost(nx, ny); if (nd < (dist.has(nk) ? dist.get(nk) : 1e9)) { dist.set(nk, nd); prev.set(nk, K(x, y)); q.push([nd, nx, ny]); } } }
  return [];
}
function mkCreep(role, body, x, y, mem = {}) {
  const c = { id: 'c' + nid++, name: role + nid, memory: Object.assign({ role, home: 'W47N8' }, mem), body: body.map(type => ({ type, hits: 100 })), pos: new RoomPosition(x, y), fatigue: 0, ticksToLive: 1400, my: true,
    get room() { return room; }, spawning: false, moved: 0, xfer: 0, acts: 0,
    getActiveBodyparts: t => body.filter(p => p === t).length };
  c.store = st(50 * body.filter(p => p === 'carry').length, 0);
  c.move = d => { if (c.fatigue > 0 || c._mv) return -11; c._mv = DIRS[d]; return 0; };
  c.moveTo = (p, o = {}) => { if (c.fatigue > 0) return -11; const pp = p.pos || p, P = route(c.pos, pp, o.range === undefined ? 1 : o.range); if (!P.length) return 0; const k = P[0]; c._mv = [Math.floor(k / 50) - c.pos.x, k % 50 - c.pos.y]; return 0; };
  c.transfer = (s, r) => { if (c._act || !c.pos.isNearTo(s)) return -9; const a = Math.min(c.store.energy, s.store.getFreeCapacity()); if (a <= 0) return -8; c._act = () => { c.store.energy -= a; s.store.energy += a; }; c.xfer++; return 0; };
  c.withdraw = (s, r) => { if (c._act || !c.pos.isNearTo(s)) return -9; const a = Math.min(s.store.energy, c.store.getFreeCapacity()); if (a <= 0) return -6; c._act = () => { s.store.energy -= a; c.store.energy += a; }; return 0; };
  creeps.push(c); return c;
}
function step() {
  for (const c of creeps) { c._mv = null; c._act = null; F.run(c); }
  for (const c of creeps) { if (c._act) c._act(); }
  for (const c of creeps) {
    if (c._mv) { const nx = c.pos.x + c._mv[0], ny = c.pos.y + c._mv[1]; if (walk(nx, ny) && !creeps.some(o => o !== c && o.pos.x === nx && o.pos.y === ny)) {
      c.pos = new RoomPosition(nx, ny); c.moved++; const loaded = Math.ceil(c.store.energy / 50), heavy = Math.min(loaded, c.getActiveBodyparts('carry'));
      c.fatigue += tcost(nx, ny) * heavy; } }
    c.fatigue = Math.max(0, c.fatigue - 2 * c.getActiveBodyparts('move'));
  }
  Game.time++;
}
const dutyAll = () => Object.values(OBJ).filter(s => (s.structureType === 'extension' || s.structureType === 'spawn') && F.isDuty(room, s));
const hubFull = () => dutyAll().every(s => s.store.getFreeCapacity() === 0);
// drain like Spawn2's energyOrder (hub nearest core 34,33 first)
function drain(n) { const o = dutyAll().sort((a, b) => cheb(a.pos, { x: 34, y: 33 }) - cheb(b.pos, { x: 34, y: 33 })); for (const s of o) { const a = Math.min(n, s.store.energy); s.store.energy -= a; n -= a; } }
function fillAll() { for (const s of dutyAll()) s.store.energy = s.store.getCapacity(); }
function settle(f) { for (let i = 0; i < 80 && !(hubFull() && f.pos.x === F.POST[0] && f.pos.y === F.POST[1] && f.store.getFreeCapacity() === 0); i++) step(); }
const TRACES = [];
function refill(f, n, lim) {
  drain(n); const t0 = Game.time, x0 = f.xfer, m0 = f.moved;
  const tr = [[f.pos.x, f.pos.y, f.store.energy]];
  while (!hubFull()) { step(); tr.push([f.pos.x, f.pos.y, f.store.energy, f.xfer - x0]); assert.ok(Game.time - t0 < lim, `refill of ${n} not done in ${lim} ticks (filler at ${f.pos.x},${f.pos.y} e${f.store.energy} fs ${f.memory.fs})`); }
  if (process.env.FILL_TRACE) TRACES.push({ n, tr });
  return { t: Game.time - t0, xfer: f.xfer - x0, moves: f.moved - m0 };
}
// ---------- (A) live RCL4 hub: 16 hub-duty extensions (800) + tower, storage 3000
build(50); room.storage.store.energy = 3000;
DUTY_RESET();
function DUTY_RESET() { Game.time += 100; } // duty cache refresh (25 ticks)
fillAll();
const body = F.body(1300, room); assert.deepStrictEqual(_.countBy(body), { carry: 12, move: 6 }, 'RCL4 body 12C6M (75% of 750 hub energy)');
const f = mkCreep('w8filler', body, 34, 32);
settle(f);
assert.deepStrictEqual([f.pos.x, f.pos.y, f.store.energy], [34, 32, 600], 'idles full on POST 34,32');
const R4 = {};
for (const n of [150, 300, 600, 800]) { R4[n] = refill(f, n, n <= 300 ? 25 : 70); settle(f); }
say('RCL4 live hub (15 ext, 750):', JSON.stringify(R4));
assert.ok(R4[800].t <= 60, 'full 800 hub refill within 60 ticks: ' + R4[800].t);
// every tick of a sweep either transfers or moves (no dead ticks except refill): xfer = energy/50
assert.strictEqual(R4[800].xfer, 15, 'one transfer per extension (15 hub ext live)');
// ---------- (B) full v3b RCL6 (40 ext incl. 5 temp; 35 hub) and RCL8 (60 ext x 200): sweep scales
for (const [nm, cap, cnt, lim] of [['RCL6', 50, 35, 120], ['RCL8', 200, 55, 400]]) {
  build(cap, L.ORDER.extension.slice(0, cnt)); room.storage.store.energy = 50000; DUTY_RESET(); fillAll();
  const b = F.body(nm === 'RCL8' ? 12900 : 2300, room), g = mkCreep('w8filler', b, 34, 32); settle(g);
  const tot = sum(dutyAll(), s => s.store.getCapacity()), r = refill(g, tot, lim);
  say(nm, 'hub', tot, 'body', JSON.stringify(_.countBy(b)), 'full refill', JSON.stringify(r));
}
// ---------- (C) hauler hand-off + storage buffer (roles.js integration)
build(50); room.storage.store.energy = 3000; DUTY_RESET(); fillAll();
const ff = mkCreep('w8filler', body, 34, 32); ff.store.energy = 600;
assert.ok(F.active(room) && F.alive(room), 'filler active');
Game.time++; room.storage.store.energy = 0; assert.ok(F.active(room), 'loaded filler stays active with storage empty');
Game.time++; ff.store.energy = 0; assert.ok(!F.active(room) && F.alive(room), 'empty filler + empty buffer: haulers take the hub back');
assert.strictEqual(F.reserve(room), 950, 'reserve = hub 750 + 200');
// haulers: hub duty is the filler's while it works; Spawn2 cluster (+ tower) stays theirs; hub comes back when the filler is idle-empty
const RL = require(path.join(ROOT, 'src/rooms/w47n8/roles.js'));
for (const s of Object.values(OBJ)) if (s.store && (s.structureType === 'extension' || s.structureType === 'spawn')) s.store.energy = 0;
const hc = () => ({ id: 'h' + nid++, memory: { role: 'w8hauler' }, room, pos: new RoomPosition(30, 30) });
Game.time++; ff.store.energy = 600; room.storage.store.energy = 3000;
const t1 = RL._fill(hc(), false);
assert.ok(t1 && !F.isDuty(room, t1), 'filler active: hauler picks the Spawn2 cluster, not hub ' + JSON.stringify(t1 && t1.pos));
Game.time++; ff.store.energy = 0; room.storage.store.energy = 0;
const t2 = RL._fill(hc(), false);
assert.ok(t2 && F.isDuty(room, t2), 'filler starved: hauler fills the hub again');
// ---------- (D) spawn rule
creeps = []; DUTY_RESET();
assert.ok(F.want(room, []), 'want a filler (15 hub ext, storage built)');
assert.ok(!F.want(room, [{ memory: { role: 'w8filler' }, ticksToLive: 500 }]), 'one live filler is enough at 750');
assert.ok(F.want(room, [{ memory: { role: 'w8filler' }, ticksToLive: 80 }]), 'replacement ahead of death (lead 3*18+40=94)');
const noSt = room.storage; room.storage = null; assert.ok(!F.want(room, []), 'no storage, no filler'); room.storage = noSt;
if (process.env.FILL_TRACE) fs.writeFileSync(process.env.FILL_TRACE, JSON.stringify({ R4, traces: TRACES.slice(0, 4) }));
console.log('w47n8 filler ok' + (quiet ? '' : ' (' + JSON.stringify(R4[800]) + ' for 800)'));
