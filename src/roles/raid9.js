// One-off probing raid on BustJetter W47N9 (Misaki 2026-10-21 13:3x). Memory.ops.w47n9 = { on, n (spawned count), go (tick), done }.
// Spawn from HOME W46N8 (2 melee + 2 ranged, storage floor ignored), walk W46N8 west 0,23 -> W47N8 rally 30,1/31,1/30,2/31,2,
// all 4 present -> enter W47N9 together. One-shot: never respawned. NO retreat unless W47N9 controller.safeMode is active.
// Targets each tick: (1) hostile creeps carrying energy within 3 of a tower, (2) spawn, (3) structures (+ creeps near structures), rest.
const MV = require('../utils/move');
const TARGET = 'W47N9', STAGE = 'W47N8', HOME = 'W46N8';
const RALLY = [[30, 1], [31, 1], [30, 2], [31, 2]];
const MELEE = () => [].concat(Array(2).fill(TOUGH), Array(16).fill(ATTACK), Array(18).fill(MOVE)); // 2200
const RANGED = () => [].concat(Array(10).fill(RANGED_ATTACK), Array(11).fill(MOVE), [HEAL]);       // 2300
const KINDS = ['m', 'r', 'm', 'r'];
const M = () => { const o = Memory.ops || (Memory.ops = {}); return o.w47n9 || (o.w47n9 = {}); };
const rng = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
const SKIP = new Set(['road', 'container', 'controller', 'constructedWall', 'rampart', 'extractor', 'keeperLair', 'portal', 'source', 'mineral']);

// pure: world = { creeps:[{id,pos,energy,hits}], structs:[{id,pos,structureType,hits}] }; returns { id, pri } or null
function pick(me, w) {
  const towers = w.structs.filter(s => s.structureType === 'tower');
  const feeders = w.creeps.filter(h => h.energy > 0 && towers.some(t => rng(t.pos, h.pos) <= 3));
  if (feeders.length) return { id: _.min(feeders, h => rng(me, h.pos) * 1e5 + h.hits).id, pri: 1 };
  const sp = w.structs.filter(s => s.structureType === 'spawn');
  if (sp.length) return { id: _.min(sp, s => rng(me, s.pos)).id, pri: 2 };
  const st = w.structs.filter(s => !SKIP.has(s.structureType));
  const near = w.creeps.filter(h => st.some(s => rng(s.pos, h.pos) <= 2));
  // creeps near structures interfere (repair/refill), kill them when close; else nearest structure (towers first)
  const cNear = near.filter(h => rng(me, h.pos) <= 3);
  if (cNear.length) return { id: _.min(cNear, h => h.hits).id, pri: 3 };
  if (st.length) return { id: _.min(st, s => rng(me, s.pos) - (s.structureType === 'tower' ? 20 : 0)).id, pri: 3 };
  if (w.creeps.length) return { id: _.min(w.creeps, h => rng(me, h.pos)).id, pri: 4 };
  return null;
}
// pure: ranged choice given in-range enemies {pos} -> 'mass' when 3+ within 3 (or mass dmg beats single 10/part)
function useMass(me, inR) {
  if (inR.length >= 3) return true;
  return _.sum(inR, h => { const r = rng(me, h.pos); return r <= 1 ? 10 : r === 2 ? 4 : 1; }) > 10;
}
// pure: heal plan. me/mates = {id,pos,hits,hitsMax}; mates excludes me. Only damaged ones count; lowest hits ratio wins (self included).
// -> null | { id, ratio, mode: 'heal' (adjacent/self) | 'ranged' (range 2-3) | 'far' }
const HEAL_URGENT = 0.6;
function healPlan(me, mates) {
  const hurt = [me].concat(mates || []).filter(x => x.hits < x.hitsMax);
  if (!hurt.length) return null;
  const t = hurt.reduce((a, x) => x.hits / x.hitsMax < a.hits / a.hitsMax ? x : a), r = t === me ? 0 : rng(me.pos, t.pos);
  return { id: t.id, ratio: t.hits / t.hitsMax, mode: r <= 1 ? 'heal' : r <= 3 ? 'ranged' : 'far', pos: t.pos };
}
function squad(c) { return c.room.find(FIND_MY_CREEPS).filter(x => x !== c && x.memory.role === 'raid9'); }
function world(room) {
  const hc = room.find(FIND_HOSTILE_CREEPS);
  return {
    creeps: hc.map(h => ({ id: h.id, pos: h.pos, energy: (h.store && h.store[RESOURCE_ENERGY]) || 0, hits: h.hits })),
    structs: room.find(FIND_HOSTILE_STRUCTURES).map(s => ({ id: s.id, pos: s.pos, structureType: s.structureType, hits: s.hits })),
    hc,
  };
}
function strike(c, t, w, hp) {
  const melee = c.getActiveBodyparts(ATTACK) > 0, ra = c.getActiveBodyparts(RANGED_ATTACK) > 0;
  if (melee) {
    if (t && c.pos.isNearTo(t)) c.attack(t);
    else { // target of opportunity: adjacent creep, else adjacent non-road structure (incl. ramparts in the way)
      const adj = w.hc.find(h => c.pos.isNearTo(h)) || c.pos.findInRange(FIND_HOSTILE_STRUCTURES, 1).find(s => s.structureType !== STRUCTURE_CONTROLLER);
      if (adj) c.attack(adj);
    }
  }
  const hr = hp && c.getActiveBodyparts(HEAL) ? hp : null, ht = hr && (hr.id === c.id ? c : Game.getObjectById(hr.id));
  // heal() never blocks ranged attacks; rangedHeal does, so only spend the tick on it when the ally is badly hurt
  if (ht && hr.mode === 'heal') c.heal(ht);
  else if (ht && hr.mode === 'ranged' && (hr.ratio < HEAL_URGENT || !ra)) { c.rangedHeal(ht); return; }
  if (ra) {
    const inR = w.hc.filter(h => c.pos.inRangeTo(h, 3));
    if (useMass(c.pos, inR)) c.rangedMassAttack();
    else if (t && c.pos.inRangeTo(t, 3)) c.rangedAttack(t);
    else if (inR.length) c.rangedAttack(_.min(inR, h => h.hits));
    else { const s = c.pos.findInRange(FIND_HOSTILE_STRUCTURES, 3).find(s => s.structureType !== STRUCTURE_CONTROLLER); if (s) c.rangedAttack(s); }
  }
}
function travel(c, slot) {
  const b = c.pos.x === 0 || c.pos.x === 49 || c.pos.y === 0 || c.pos.y === 49;
  if (c.room.name === HOME) {
    if (c.pos.x === 0 && c.pos.y === 23) { delete c.memory._m; return c.move(LEFT); }
    if (b) { delete c.memory._m; return c.move(c.pos.x === 49 ? LEFT : c.pos.x === 0 ? RIGHT : c.pos.y === 0 ? BOTTOM : TOP); }
    return MV.to(c, 0, 23, 0);
  }
  if (c.room.name === STAGE) {
    if (b && c.pos.x === 49) { delete c.memory._m; return c.move(LEFT); }
    return MV.to(c, slot[0], slot[1], 0);
  }
  return c.moveTo(new RoomPosition(slot[0], slot[1], STAGE), { reusePath: 10 });
}
function run(c) {
  const P = M(), k = c.memory.k | 0, slot = RALLY[k % 4];
  const tr = Game.rooms[TARGET], sm = tr && tr.controller && tr.controller.safeMode;
  if (sm) { P.safe = Game.time; if (c.room.name === TARGET && (c.pos.y === 49)) return c.move(BOTTOM); return travel(c, slot); } // the only retreat
  if (c.room.name === TARGET) {
    const w = world(c.room), p = pick(c.pos, w), t = p && Game.getObjectById(p.id);
    const hp = c.getActiveBodyparts(HEAL) ? healPlan(c, squad(c)) : null;
    strike(c, t, w, hp);
    if (c.pos.y === 49) return c.move(TOP);
    // badly hurt ally out of reach and no feeder/spawn duty pinning us: go to them
    if (hp && hp.mode === 'far' && hp.ratio < HEAL_URGENT && !(p && p.pri <= 2)) return c.moveTo(hp.pos, { range: 1, reusePath: 2, maxRooms: 1 });
    if (!t) return;
    const r = c.getActiveBodyparts(ATTACK) ? 1 : (p.pri === 1 || p.pri === 4 ? 3 : 2);
    if (c.pos.inRangeTo(t, r)) return;
    const rv = c.moveTo(t, { range: r, reusePath: 3, maxRooms: 1 });
    if (rv === ERR_NO_PATH) c.moveTo(t, { range: r, reusePath: 3, maxRooms: 1, ignoreDestructibleStructures: true }); // walled in: walk into ramparts and hit them (opportunity)
    return;
  }
  // en route / staging: fight anything hostile adjacent/in range on the way, no chasing
  const hp = c.getActiveBodyparts(HEAL) ? healPlan(c, squad(c)) : null;
  const w = { hc: c.room.find(FIND_HOSTILE_CREEPS) }; if (w.hc.length || hp) strike(c, null, w, hp);
  if (P.go) {
    if (c.room.name === STAGE) { if (c.pos.y === 0) return c.move(TOP); return c.moveTo(new RoomPosition(30, 48, TARGET), { reusePath: 5 }); }
    return travel(c, slot);
  }
  travel(c, slot);
  // all alive raiders on their rally tiles -> go (once)
  const all = _.filter(Game.creeps, x => x.memory.role === 'raid9');
  if (all.length >= 4 && all.every(x => x.room.name === STAGE && x.pos.x === RALLY[(x.memory.k | 0) % 4][0] && x.pos.y === RALLY[(x.memory.k | 0) % 4][1])) P.go = Game.time;
}
// home spawn hook: only W46N8, only while ops.w47n9.on and fewer than 4 spawned in total (deaths are not replaced)
function wantSpawn(room) {
  const P = Memory.ops && Memory.ops.w47n9; if (!P || P.on !== true || room.name !== HOME) return null;
  const n = P.n | 0; if (n >= 4) return null;
  const kind = KINDS[n];
  return { role: 'raid9', body: kind === 'm' ? MELEE() : RANGED(), mem: { role: 'raid9', home: HOME, k: n, kind, born: Game.time } };
}
function noteSpawned() { const P = M(); P.n = (P.n | 0) + 1; }
module.exports = { run, pick, useMass, healPlan, wantSpawn, noteSpawned, MELEE, RANGED, RALLY };
