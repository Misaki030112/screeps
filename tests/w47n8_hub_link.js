// Hub link tile (Misaki 2026-11-13): planned W47N8 hub link is 32,33, beside hub container 33,33.
// 33,34 is the plain road between that container and tower 33,35 and must not stay a link.
// A built link left at 33,34 is not destroyed here (ops does that) and blocks the new site,
// so layout never plans two hub links. Rampart and road may share 32,33; other structures do not.
const assert = require('assert'), path = require('path');
const d = path.join(__dirname, '..', 'src', 'rooms', 'w47n8');
const K = { LOOK_STRUCTURES: 'structure', LOOK_CONSTRUCTION_SITES: 'constructionSite', FIND_MY_SPAWNS: 112, FIND_MY_CONSTRUCTION_SITES: 114,
  FIND_MY_STRUCTURES: 108, OK: 0, ERR_RCL_NOT_ENOUGH: -14, RESOURCE_ENERGY: 'energy' };
const T = ['spawn', 'extension', 'road', 'wall', 'rampart', 'link', 'storage', 'tower', 'observer', 'powerSpawn', 'extractor', 'lab', 'terminal', 'container', 'nuker', 'factory'];
for (const t of T) K['STRUCTURE_' + (t === 'powerSpawn' ? 'POWER_SPAWN' : t.toUpperCase())] = t;
const CS = { spawn: [0, 1, 1, 1, 1, 1, 1, 2, 3], extension: [0, 0, 5, 10, 20, 30, 40, 50, 60], tower: [0, 0, 0, 1, 1, 2, 2, 3, 6], link: [0, 0, 0, 0, 0, 2, 3, 4, 6],
  storage: [0, 0, 0, 0, 1, 1, 1, 1, 1], container: Array(9).fill(5), road: Array(9).fill(2500), wall: [0, 0, 2500, 2500, 2500, 2500, 2500, 2500, 2500],
  rampart: [0, 0, 2500, 2500, 2500, 2500, 2500, 2500, 2500], terminal: [0, 0, 0, 0, 0, 0, 1, 1, 1], extractor: [0, 0, 0, 0, 0, 0, 1, 1, 1],
  lab: [0, 0, 0, 0, 0, 0, 3, 6, 10], factory: [0, 0, 0, 0, 0, 0, 0, 1, 1], powerSpawn: Array(8).fill(0).concat([1]), nuker: Array(8).fill(0).concat([1]), observer: Array(8).fill(0).concat([1]) };
Object.assign(global, K, { _: require('lodash'), CONTROLLER_STRUCTURES: CS, Memory: { ops: { w8layout: 'approved' } }, Game: { time: 20, rooms: {}, creeps: {} } });
const L = require(path.join(d, 'layout')), C = require(path.join(d, 'config')), W = require(path.join(d, 'index.js')), R = require(path.join(d, 'roads'));
const F = require(path.join(d, 'fill'));
const cheb = (a, b) => Math.max(Math.abs(a[0] - b[0]), Math.abs(a[1] - b[1]));

assert.deepStrictEqual(L.hubLinkPos(), [32, 33], 'planned hub link');
assert.deepStrictEqual(L.ORDER.link, [[32, 33]], 'ORDER.link is only 32,33');
assert.deepStrictEqual(L.RETIRED_HUB_LINK, [33, 34]);
for (const t of Object.keys(L.ORDER)) {
  assert.ok(!(L.ORDER[t] || []).some(([x, y]) => x === 33 && y === 34), '33,34 is not reserved as ' + t);
}
assert.ok(R.ROADS.some(([x, y]) => x === 33 && y === 34), '33,34 stays a planned road');
assert.ok(!R.ROADS.some(([x, y]) => x === 32 && y === 33), '32,33 is not a road tile');
assert.ok(L.ORDER.rampart.some(([x, y]) => x === 32 && y === 33), 'empty-slot rampart plan may share 32,33');
assert.strictEqual(cheb(L.hubLinkPos(), F.POST), 2, 'range 2 from filler POST 34,32');
assert.strictEqual(cheb(L.hubLinkPos(), L.ORDER.storage[0]), 3, 'range 3 from storage 35,32');
assert.deepStrictEqual(F.POST, [34, 32]);
assert.deepStrictEqual(C.HUB_CONT, [33, 33]);
assert.deepStrictEqual(C.CTL_LINK, [13, 25]);
assert.deepStrictEqual(C.SPAWN, [15, 18], 'spawn anchor unchanged');
assert.deepStrictEqual(L.ORDER.spawn.slice(0, 2), [[34, 30], [33, 30]]);
assert.deepStrictEqual(L.ORDER.storage[0], [35, 32]);
assert.deepStrictEqual(L.ORDER.terminal[0], [33, 32]);
assert.deepStrictEqual(L.ORDER.factory[0], [35, 30]);
assert.ok(L.ORDER.extension.some(([x, y]) => x === 32 && y === 34), 'extension 32,34 stays');
assert.strictEqual(C.HUB_LINK, true);
assert.strictEqual(C.RCL6_LABS, false);
assert.strictEqual(C.RCL7_INDUSTRY, false);
assert.strictEqual(C.RCL6_MINERALS, true);
assert.strictEqual(W.LEAN_ARM, 15000, '15k reserve unchanged');

function mkRoom(rcl, built) {
  const st = {}, sites = [];
  const add = (x, y, t) => (st[x * 50 + y] = st[x * 50 + y] || []).push({ structureType: t, pos: { x, y }, destroy() { this.destroyed = (this.destroyed || 0) + 1; return 0; } });
  for (const [x, y, t] of built) add(x, y, t);
  return { sites, controller: { level: rcl },
    find: (k, o) => { const a = k === FIND_MY_SPAWNS ? [{}] : k === FIND_MY_CONSTRUCTION_SITES ? sites : []; return o && o.filter ? a.filter(o.filter) : a; },
    lookForAt: (k, x, y) => k === LOOK_STRUCTURES ? (st[x * 50 + y] || []) : sites.filter(s => s.pos.x === x && s.pos.y === y),
    createConstructionSite(x, y, t) {
      const n = Object.values(st).flat().filter(s => s.structureType === t).length + sites.filter(s => s.structureType === t).length;
      if (n >= CS[t][rcl]) return ERR_RCL_NOT_ENOUGH;
      const site = { structureType: t, pos: { x, y }, remove() { const i = sites.indexOf(site); if (i >= 0) sites.splice(i, 1); } };
      sites.push(site); return OK; } };
}
const roads = R.ROADS.filter(([x, y]) => !R.MINERAL.some(([a, b]) => a === x && b === y)).concat(require('../src/layouts/w8link').W47N8);
const ready = [].concat(C.SEAL.map(([x, y]) => [x, y, 'wall']),
  [[34, 30, 'spawn'], [33, 30, 'spawn'], [35, 32, 'storage'], [33, 32, 'terminal'], [35, 30, 'factory'],
    [C.HUB_CONT[0], C.HUB_CONT[1], 'container'], [13, 26, 'container'], [37, 44, 'container'], [37, 45, 'extractor'],
    [33, 35, 'tower'], [24, 8, 'tower'], [22, 7, 'tower'],
    [C.CTL_LINK[0], C.CTL_LINK[1], 'link'], [C.SOURCES[0].link[0], C.SOURCES[0].link[1], 'link']],
  L.ORDER.extension.slice(0, 50).map(([x, y]) => [x, y, 'extension']),
  roads.map(([x, y]) => [x, y, 'road']));
const linkAt = (room, x, y) => room.sites.filter(s => s.structureType === 'link' && s.pos.x === x && s.pos.y === y);

{ const r = mkRoom(7, ready); W.layoutRun(r);
  assert.deepStrictEqual(linkAt(r, 32, 33).map(s => s.pos.x + ',' + s.pos.y), ['32,33'], 'sites the hub link at 32,33');
  assert.strictEqual(linkAt(r, 33, 34).length, 0, 'does not site a link at 33,34'); }

{ const r = mkRoom(7, ready); r.createConstructionSite(33, 34, 'link');
  assert.strictEqual(linkAt(r, 33, 34).length, 1);
  W.layoutRun(r);
  assert.strictEqual(linkAt(r, 33, 34).length, 0, 'drops the obsolete 33,34 link site');
  assert.strictEqual(linkAt(r, 32, 33).length, 1, 'sites 32,33 once the retired site is gone'); }

{ const r = mkRoom(7, ready.concat([[33, 34, 'link']])); W.layoutRun(r);
  const old = r.lookForAt(LOOK_STRUCTURES, 33, 34).find(s => s.structureType === 'link');
  assert.ok(old, 'retired structure still present');
  assert.strictEqual(old.destroyed || 0, 0, 'does not destroy the live 33,34 link');
  assert.strictEqual(linkAt(r, 32, 33).length, 0, 'does not site a second hub link while 33,34 stands');
  assert.strictEqual(linkAt(r, 33, 34).length, 0, 'does not refresh a link site at 33,34'); }

{ const r = mkRoom(7, ready.concat([[32, 33, 'extension']])); W.layoutRun(r);
  assert.strictEqual(linkAt(r, 32, 33).length, 0, 'does not site a link on an extension'); }
{ const r = mkRoom(7, ready.concat([[32, 33, 'rampart']])); W.layoutRun(r);
  assert.strictEqual(linkAt(r, 32, 33).length, 1, 'rampart may share the hub link tile'); }
{ const r = mkRoom(7, ready.concat([[32, 33, 'road']])); W.layoutRun(r);
  assert.strictEqual(linkAt(r, 32, 33).length, 1, 'road may share the hub link tile'); }

assert.strictEqual(W.hubLinkLive({ lookForAt: (k, x, y) => (x === 33 && y === 34 ? [{ structureType: 'link' }] : []) }), false, '33,34 is not hubLinkLive');
assert.strictEqual(W.hubLinkLive({ lookForAt: (k, x, y) => (x === 32 && y === 33 ? [{ structureType: 'link' }] : []) }), true, '32,33 is hubLinkLive');

let sentOld = 0, sentHub = 0;
const old = { structureType: 'link', cooldown: 0, store: { energy: 800, getFreeCapacity: () => 0 }, transferEnergy() { sentOld++; return 0; } };
const hub = { structureType: 'link', cooldown: 0, store: { energy: 400, getFreeCapacity: () => 400 }, transferEnergy() { sentHub++; return 0; } };
const ctl = { structureType: 'link', cooldown: 0, store: { energy: 0, getFreeCapacity: () => 800 } };
Game.rooms.W47N8 = { lookForAt: (k, x, y) => {
  if (x === 33 && y === 34) return [old];
  if (x === 32 && y === 33) return [hub];
  if (x === 13 && y === 25) return [ctl];
  return [];
}};
W.linkRun();
assert.strictEqual(sentOld, 0, 'linkRun does not send from 33,34');
assert.strictEqual(sentHub, 1, 'linkRun sends from 32,33 to the controller link');

console.log('w47n8 hub link 32,33 ok');
