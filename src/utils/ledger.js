// Live energy ledger (docs/LEDGER.md). Cumulative counters in Memory.ledger = {t0, r:{room:{cat:energy}}, s:{srcId:[room,harvested,wastedAtRegen]}}.
// Read two snapshots and divide by the tick delta: tools/ledger.py. Cost ~0.01 ms/intent + ~0.02 ms/tick (sources only on regen tick).
// Categories: up upgrade, b build, rw rep wall, rr rep road, rc rep container, ro rep other, sp:<role> spawn body cost,
// rf:<role> recycle refund (estimate), tw/tr/th tower wall-or-rampart repair / road-or-other repair / attack+heal, dr dropped, lk link transfer loss (3%).
let done = false;
const add = (room, k, v) => { if (!v) return; const L = Memory.ledger || (Memory.ledger = { t0: Game.time, r: {}, s: {} }); const R = L.r[room] || (L.r[room] = {}); R[k] = (R[k] || 0) + v; };
const rcat = t => !t ? 'ro' : (t.structureType === STRUCTURE_WALL || t.structureType === STRUCTURE_RAMPART) ? 'w' : t.structureType === STRUCTURE_ROAD ? 'r' : t.structureType === STRUCTURE_CONTAINER ? 'c' : 'o';
const BC = { move: 50, work: 100, carry: 50, attack: 80, ranged_attack: 150, heal: 250, claim: 600, tough: 10 };
const home = c => c.memory.home || c.room.name;
function hook(C, f, fn) { if (typeof C === 'undefined' || !C) return; const P = C.prototype, o = P[f]; if (!o) return; P[f] = function (...a) { const pre = fn.pre ? fn.pre(this, a) : null; const r = o.apply(this, a); if (r === OK) try { fn.ok(this, a, pre); } catch (e) { /* never break intents */ } return r; }; }
function wrap() {
  if (done) return; done = true;
  hook(typeof Creep !== 'undefined' && Creep, 'harvest', { ok(c, [s]) { if (!s || s.energyCapacity === undefined) return; const L = Memory.ledger; if (!L) return;
    const e = L.s[s.id] || (L.s[s.id] = [s.room.name, 0, 0]); e[1] += Math.min(2 * c.getActiveBodyparts(WORK), s.energy); } });
  hook(typeof Creep !== 'undefined' && Creep, 'upgradeController', { ok(c) { add(c.room.name, 'up', Math.min(c.getActiveBodyparts(WORK), c.store[RESOURCE_ENERGY])); } });
  hook(typeof Creep !== 'undefined' && Creep, 'build', { ok(c, [s]) { add(home(c), 'b', Math.min(5 * c.getActiveBodyparts(WORK), c.store[RESOURCE_ENERGY], s.progressTotal - s.progress)); } });
  hook(typeof Creep !== 'undefined' && Creep, 'repair', { ok(c, [s]) { add(c.room.name === home(c) ? c.room.name : home(c), 'r' + rcat(s) + (c.room.name !== home(c) ? '@' + c.room.name : ''), Math.min(c.getActiveBodyparts(WORK), c.store[RESOURCE_ENERGY])); } });
  hook(typeof Creep !== 'undefined' && Creep, 'drop', { pre: (c, [res, n]) => res === RESOURCE_ENERGY ? (n || c.store[RESOURCE_ENERGY]) : 0, ok(c, a, n) { add(c.room.name, 'dr', n); } });
  hook(typeof StructureSpawn !== 'undefined' && StructureSpawn, 'spawnCreep', { ok(sp, [body, name, o]) { if (o && o.dryRun) return; add(sp.room.name, 'sp:' + ((o && o.memory && o.memory.role) || '?'), body.reduce((s, p) => s + BC[p], 0)); } });
  // rf:<role> recycle refund estimate (12h review 2026-11-10): sp:<role> is gross body cost, so floor-bank upgrader churn
  // (spawn at 16k, recycle young extras below 14.5k) looked like ~14 e/t. Engine drops body*ttl/lifetime (+carry) on recycle.
  hook(typeof StructureSpawn !== 'undefined' && StructureSpawn, 'recycleCreep', { pre: (sp, [c]) => c && c.body ? Math.floor(c.body.reduce((s, p) => s + BC[p.type], 0) * Math.min(1, (c.ticksToLive || 0) / (c.body.some(p => p.type === CLAIM) ? 600 : 1500))) : 0,
    ok(sp, [c], n) { add(sp.room.name, 'rf:' + ((c && c.memory && c.memory.role) || '?'), n); } });
  hook(typeof StructureTower !== 'undefined' && StructureTower, 'repair', { ok(t, [s]) { add(t.room.name, rcat(s) === 'w' ? 'tw' : 'tr', 10); } });
  hook(typeof StructureTower !== 'undefined' && StructureTower, 'attack', { ok(t) { add(t.room.name, 'th', 10); } });
  hook(typeof StructureTower !== 'undefined' && StructureTower, 'heal', { ok(t) { add(t.room.name, 'th', 10); } });
  hook(typeof StructureLink !== 'undefined' && StructureLink, 'transferEnergy', { ok(l, [to, n]) { add(l.room.name, 'lk', Math.ceil((n || l.store[RESOURCE_ENERGY]) * 0.03)); } });
}
const SRC = {};
function tick() { // waste: energy left in a source on its last tick before regeneration
  const L = Memory.ledger || (Memory.ledger = { t0: Game.time, r: {}, s: {} });
  for (const rn in Game.rooms) { const ids = SRC[rn] || (SRC[rn] = Game.rooms[rn].find(FIND_SOURCES).map(s => s.id));
    for (const id of ids) { const s = Game.getObjectById(id); if (s && s.ticksToRegeneration === 1) { const e = L.s[id] || (L.s[id] = [rn, 0, 0]); e[2] += s.energy; e[3] = (e[3] || 0) + 1; } } }
}
module.exports = { wrap, tick, reset() { Memory.ledger = { t0: Game.time, r: {}, s: {} }; } };
