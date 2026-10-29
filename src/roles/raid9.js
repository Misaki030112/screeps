// W47N9 raid (Misaki 2026-10-21 probe; 2026-10-29 flatten-or-burn-SM). Memory.ops.w47n9 = { on, n, go, safe, safeUntil, flee, garrison }.
// Spawn from HOME W46N8 (2 melee + 2 ranged, storage floor ignored), walk W46N8 west 0,23 -> W47N8 rally 30,1/31,1/30,2/31,2,
// all 4 present -> enter W47N9 together (melee first). One-shot: never respawned.
// Retreat: (1) W47N9 safe mode, (2) overrun = hostile ATTACK+RA parts >=12, (3) last raider alive after n>=4, (4) manual abort/garrison.
// Targets each tick: (1) spawn (rampart on tile eats hits; siege path ignores destructibles), (2) feeders/armed after spawn dead, (3) structures (+ creeps near), rest.
// Misaki 10-29 live: hard-focus spawn rampart — no feeder/armed path diversions while spawn stands.
// Restart: replace Memory.ops.w47n9 with { on:true, n:0 } — leftover safe/garrison from a prior wave forces garrison.
const MV = require('../utils/move');
const TARGET = 'W47N9', STAGE = 'W47N8', HOME = 'W46N8';
const RALLY = [[30, 1], [31, 1], [30, 2], [31, 2]];
const MELEE = () => [].concat(Array(2).fill(TOUGH), Array(16).fill(ATTACK), Array(18).fill(MOVE)); // 2200
const RANGED = () => [].concat(Array(10).fill(RANGED_ATTACK), Array(11).fill(MOVE), [HEAL]);       // 2300
const KINDS = ['m', 'r', 'm', 'r'];
// formation (Misaki 14:1x): melee front row y=1 (nearest north exit), ranged behind y=2
const slotOf = k => (k | 0) % 2 === 0 ? RALLY[((k | 0) >> 1) % 2] : RALLY[2 + (((k | 0) >> 1) % 2)];
const isMelee = x => ((x.memory.k | 0) % 2) === 0;
const ND = { noDetour: true }; // swap through our own creeps, never deadlock
const M = () => { const o = Memory.ops || (Memory.ops = {}); return o.w47n9 || (o.w47n9 = {}); };
const rng = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
const SKIP = new Set(['road', 'container', 'controller', 'constructedWall', 'rampart', 'extractor', 'keeperLair', 'portal', 'source', 'mineral']);

// pure: world = { creeps:[{id,pos,energy,hits}], structs:[{id,pos,structureType,hits}] }; returns { id, pri } or null
function pick(me, w) {
  // primary assault: spawn — attack() on spawn damages covering rampart on the same tile.
  // Adjacent trash is peeled by strike() opportunity only — never divert path off spawn (Misaki 10-29).
  const sp = w.structs.filter(s => s.structureType === 'spawn');
  if (sp.length) return { id: _.min(sp, s => rng(me, s.pos)).id, pri: 1 };
  // only after spawn is gone: interrupt tower refill
  const towers = w.structs.filter(s => s.structureType === 'tower');
  const feeders = w.creeps.filter(h => h.energy > 0 && towers.some(t => rng(t.pos, h.pos) <= 3));
  if (feeders.length) return { id: _.min(feeders, h => rng(me, h.pos) * 1e5 + h.hits).id, pri: 2 };
  // armed left near us after spawn dead: peel before other structures
  const armed = w.creeps.filter(h => h.armed && rng(me, h.pos) <= 3);
  if (armed.length) return { id: _.min(armed, h => h.hits).id, pri: 2 };
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
    creeps: hc.map(h => ({ id: h.id, pos: h.pos, energy: (h.store && h.store[RESOURCE_ENERGY]) || 0, hits: h.hits, armed: h.getActiveBodyparts(ATTACK) + h.getActiveBodyparts(RANGED_ATTACK) > 0 })),
    structs: room.find(FIND_HOSTILE_STRUCTURES).map(s => ({ id: s.id, pos: s.pos, structureType: s.structureType, hits: s.hits })),
    hc,
  };
}
function strike(c, t, w, hp) {
  const melee = c.getActiveBodyparts(ATTACK) > 0, ra = c.getActiveBodyparts(RANGED_ATTACK) > 0;
  if (melee) {
    if (t && c.pos.isNearTo(t)) c.attack(t);
    else {
      // siege: when primary is a structure, smash adjacent rampart/wall BEFORE peeling creeps
      const adjS = c.pos.findInRange(FIND_HOSTILE_STRUCTURES, 1).find(s => s.structureType !== STRUCTURE_CONTROLLER);
      const adjC = w.hc.find(h => c.pos.isNearTo(h));
      const adj = (t && t.structureType && adjS) ? adjS : (adjC || adjS);
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
function exitX(room, x0) {
  const T = room.getTerrain(); let best = x0, bd = 99;
  for (let x = 1; x < 49; x++) if (!(T.get(x, 0) & TERRAIN_MASK_WALL) && Math.abs(x - x0) < bd) { bd = Math.abs(x - x0); best = x; }
  return best;
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
    // ranged hold 2 rows back until both melee stand on the front row, so they never block the melee path
    if (!isMelee(c)) {
      const ml = _.filter(Game.creeps, x => x.memory.role === 'raid9' && isMelee(x));
      const ready = ml.every(x => x.room.name === STAGE && x.pos.x === slotOf(x.memory.k)[0] && x.pos.y === slotOf(x.memory.k)[1]);
      if (!ready && !(c.pos.x === slot[0] && c.pos.y === slot[1])) return MV.to(c, slot[0], slot[1] + 2, 0, ND);
    }
    return MV.to(c, slot[0], slot[1], 0, ND);
  }
  return c.moveTo(new RoomPosition(slot[0], slot[1], STAGE), { reusePath: 10 });
}
// Misaki 10-21 14:3x: after W47N9 safe mode, garrison INSIDE the W47N8 north wall until old age; never re-enter W47N9.
// wall y=3, gate rampart 29,3 -> 29,4 -> road 28,4 stay free. melee hug the wall at 30,4/31,4, ranged one row behind 30,5/31,5 (shoot over the wall).
const GARRISON = [[30, 4], [31, 4], [30, 5], [31, 5]];
const gSlotOf = k => (k | 0) % 2 === 0 ? GARRISON[((k | 0) >> 1) % 2] : GARRISON[2 + (((k | 0) >> 1) % 2)];
function garrison(c) {
  const g = gSlotOf(c.memory.k);
  const hp = c.getActiveBodyparts(HEAL) ? healPlan(c, squad(c)) : null;
  const w = { hc: c.room.find(FIND_HOSTILE_CREEPS) };
  if (w.hc.length || hp) {
    const ra = c.getActiveBodyparts(RANGED_ATTACK) > 0;
    const t = w.hc.length ? _.min(w.hc.filter(h => c.pos.inRangeTo(h, ra ? 3 : 1)), h => h.hits) : null;
    strike(c, t && t.id ? t : null, w, hp);
  }
  if (c.room.name === TARGET) return c.pos.y === 49 ? c.move(BOTTOM) : MV.to(c, 30, 49, 0, ND);
  if (c.room.name !== STAGE) return travel(c, g);
  if (c.pos.x === g[0] && c.pos.y === g[1]) return;
  return MV.to(c, g[0], g[1], 0, ND);
}
// stop-loss: W48N9-style reinforce. Parts = ATTACK + RANGED_ATTACK on hostiles in room.
// >=12 (~two 6RA or one heavy melee) => flee to garrison. A lone 7H healer does NOT trip this.
function armedParts(creeps) {
  let n = 0;
  for (const h of creeps) n += (h.attack | 0) + (h.ranged | 0);
  return n;
}
function overrun(room) {
  return armedParts(room.find(FIND_HOSTILE_CREEPS).map(h => ({
    attack: h.getActiveBodyparts(ATTACK), ranged: h.getActiveBodyparts(RANGED_ATTACK),
  }))) >= 12;
}
function run(c) {
  const P = M(), k = c.memory.k | 0, slot = slotOf(k);
  if (P.garrison || P.safe || P.flee) return garrison(c); // SM burned, overrun flee, or manual abort
  const tr = Game.rooms[TARGET];
  if (tr && tr.controller && tr.controller.safeMode) P.safeUntil = Game.time + tr.controller.safeMode;
  // remembered: once we retreat we lose vision of W47N9, so never re-enter while its safe mode may still run (no border bounce)
  const sm = P.safeUntil && Game.time < P.safeUntil;
  if (sm) { P.safe = P.safe || Game.time; if (c.room.name === TARGET && (c.pos.y === 49)) return c.move(BOTTOM); return travel(c, slot); }
  // flank dump: leave before the squad is deleted; SM goal already failed/succeeded separately
  if (c.room.name === TARGET && overrun(c.room)) {
    P.flee = P.flee || { t: Game.time, why: 'overrun' };
    P.garrison = true;
    if (c.pos.y === 49) return c.move(BOTTOM);
    return MV.to(c, 30, 49, 0, ND);
  }
  // last creep standing with mates dead: fall back (one-shot op, no respawn)
  const alive = _.filter(Game.creeps, x => x.memory.role === 'raid9');
  if (c.room.name === TARGET && alive.length <= 1 && (P.n | 0) >= 4) {
    P.flee = P.flee || { t: Game.time, why: 'last' };
    P.garrison = true;
    if (c.pos.y === 49) return c.move(BOTTOM);
    return MV.to(c, 30, 49, 0, ND);
  }
  if (c.room.name === TARGET) {
    const w = world(c.room), p = pick(c.pos, w), t = p && Game.getObjectById(p.id);
    const hp = c.getActiveBodyparts(HEAL) ? healPlan(c, squad(c)) : null;
    strike(c, t, w, hp);
    if (c.pos.y === 49) return c.move(TOP);
    // badly hurt ally out of reach and no spawn/feeder duty pinning us: go to them
    if (hp && hp.mode === 'far' && hp.ratio < HEAL_URGENT && !(p && p.pri <= 2)) return c.moveTo(hp.pos, { range: 1, reusePath: 2, maxRooms: 1 });
    if (!t) return;
    const r = c.getActiveBodyparts(ATTACK) ? 1 : (p.pri === 1 || p.pri === 4 ? 3 : 2);
    if (c.pos.inRangeTo(t, r)) return;
    // siege structures: hold on adjacent rampart/wall and smash; else path ignoring destructibles
    // (walking onto enemy rampart always fails — must 强拆 the edge first). Creep chases still use MV.
    if (t.structureType) {
      const edge = c.pos.findInRange(FIND_HOSTILE_STRUCTURES, 1).find(s => s.structureType === STRUCTURE_RAMPART || s.structureType === STRUCTURE_WALL);
      if (edge) return;
      delete c.memory._m;
      c.moveTo(t, { range: r, reusePath: 5, maxRooms: 1, ignoreDestructibleStructures: true, ignoreCreeps: true, swampCost: 5 });
      return;
    }
    MV.to(c, t.pos.x, t.pos.y, r, ND); // our swap-capable mover: squad never deadlocks itself
    return;
  }
  // en route / staging: fight anything hostile adjacent/in range on the way, no chasing
  const hp = c.getActiveBodyparts(HEAL) ? healPlan(c, squad(c)) : null;
  const w = { hc: c.room.find(FIND_HOSTILE_CREEPS) }; if (w.hc.length || hp) strike(c, null, w, hp);
  if (P.go) {
    if (c.room.name === STAGE) {
      if (c.pos.y === 0) return c.move(TOP);
      // melee step in first; ranged follow once no melee is left in the staging room (1 tile behind)
      if (!isMelee(c) && _.some(Game.creeps, x => x.memory.role === 'raid9' && isMelee(x) && x.room.name === STAGE)) return;
      const ex = exitX(c.room, slot[0]); // rally x=30/31 on y=0 are walls: nearest open north exit tile
      if (MV.to(c, ex, 0, 0, ND)) return c.move(TOP);
      return;
    }
    return travel(c, slot);
  }
  travel(c, slot);
  // all alive raiders on their rally tiles -> go (once)
  const all = _.filter(Game.creeps, x => x.memory.role === 'raid9');
  if (all.length >= 4 && all.every(x => x.room.name === STAGE && x.pos.x === slotOf(x.memory.k)[0] && x.pos.y === slotOf(x.memory.k)[1])) P.go = Game.time;
}
// home spawn hook: only W46N8, only while ops.w47n9.on and fewer than 4 spawned in total (deaths are not replaced)
function wantSpawn(room) {
  const P = Memory.ops && Memory.ops.w47n9; if (!P || P.on !== true || room.name !== HOME) return null;
  const n = P.n | 0; if (n >= 4) return null;
  const kind = KINDS[n];
  return { role: 'raid9', body: kind === 'm' ? MELEE() : RANGED(), mem: { role: 'raid9', home: HOME, k: n, kind, born: Game.time } };
}
function noteSpawned() { const P = M(); P.n = (P.n | 0) + 1; }
module.exports = { slotOf, gSlotOf, GARRISON, run, pick, useMass, healPlan, armedParts, overrun, wantSpawn, noteSpawned, MELEE, RANGED, RALLY };
