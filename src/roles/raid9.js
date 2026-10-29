// W47N9 sustained assault (Misaki 2026-10-29): breach@(39,42) → towers → creeps → structures; force SM.
// Memory.ops.w47n9 = { on, n, go, safe, safeUntil, flee, garrison }.
// Continuous waves: while on && !safe/garrison/flee, keep WAVE living (2 melee + 2 ranged + 2 heal) from HOME and colony STAGE.
// go: ≥2 melee, or ≥2 melee+ranged, on the STAGE north lip or already in TARGET. Healers need not be on slots.
// Creeps already in TARGET stay. Clear go only when TARGET is empty and no melee/ranged remain on that lip.
// Do NOT auto-activate our safe mode. Manual abort: tools/raid9.py abort.
const MV = require('../utils/move');
const TARGET = 'W47N9', STAGE = 'W47N8', HOME = 'W46N8';
const WAVE = 6; // 2m + 2r + 2h
const NEED = { m: 2, r: 2, h: 2 };
// Staging near SE approach: north exits ~x38–41 → enter south of W47N9, push to breach 39,42
const RALLY = {
  m: [[38, 1], [39, 1]],
  r: [[38, 2], [39, 2]],
  h: [[40, 2], [41, 2]],
};
// North lip of STAGE: exit y=0, melee row y=1, ranged/heal row y=2, one-tile hold-back y=3. Any x.
const NEAR_EXIT = 3;
const LAUNCH = 2; // combat creeps (melee and/or ranged) on the lip or already in TARGET
const BREACH = { x: 39, y: 42 };
const MELEE = () => [].concat(Array(2).fill(TOUGH), Array(16).fill(ATTACK), Array(18).fill(MOVE)); // 2200
const RANGED = () => [].concat(Array(10).fill(RANGED_ATTACK), Array(11).fill(MOVE), [HEAL]);       // 2300
const HEALER = () => [].concat(Array(7).fill(HEAL), Array(7).fill(MOVE));                         // 2100 (colony RCL6 cap)
const BODY = { m: MELEE, r: RANGED, h: HEALER };
const ND = { noDetour: true };
const M = () => { const o = Memory.ops || (Memory.ops = {}); return o.w47n9 || (o.w47n9 = {}); };
const rng = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
const SKIP = new Set(['road', 'container', 'controller', 'constructedWall', 'rampart', 'extractor', 'keeperLair', 'portal', 'source', 'mineral']);
const isMelee = x => x.memory.kind === 'm';
const isHeal = x => x.memory.kind === 'h';
const slotOf = (k, kind) => {
  const row = RALLY[kind || 'm'] || RALLY.m;
  const idx = (k | 0) % row.length;
  return row[idx];
};
const allRaid = () => _.filter(Game.creeps, x => x.memory.role === 'raid9');
const raidActive = P => P && P.on === true && !P.safe && !P.garrison && !P.flee && !(P.safeUntil && Game.time < P.safeUntil);

// pure: world = { creeps:[{id,pos,energy,hits,armed}], structs:[{id,pos,structureType,hits}] }
// Priority (Misaki): (1) barrier near 39,42 (2) towers (3) hostile creeps (4) other structures
function pick(me, w) {
  const barriers = (w.structs || []).filter(s =>
    (s.structureType === 'rampart' || s.structureType === 'constructedWall')
    && rng(s.pos, BREACH) <= 2);
  if (barriers.length) return { id: _.min(barriers, s => rng(me, s.pos) * 1e6 + s.hits).id, pri: 1 };
  const towers = (w.structs || []).filter(s => s.structureType === 'tower');
  if (towers.length) return { id: _.min(towers, s => rng(me, s.pos)).id, pri: 2 };
  const creeps = w.creeps || [];
  if (creeps.length) {
    const armed = creeps.filter(h => h.armed);
    const pool = armed.length ? armed : creeps;
    return { id: _.min(pool, h => rng(me, h.pos) * 1e5 + h.hits).id, pri: 3 };
  }
  const st = (w.structs || []).filter(s => !SKIP.has(s.structureType));
  if (st.length) return { id: _.min(st, s => rng(me, s.pos) - (s.structureType === 'spawn' ? 5 : 0)).id, pri: 4 };
  return null;
}
function useMass(me, inR) {
  if (inR.length >= 3) return true;
  return _.sum(inR, h => { const r = rng(me, h.pos); return r <= 1 ? 10 : r === 2 ? 4 : 1; }) > 10;
}
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
      const adjS = c.pos.findInRange(FIND_HOSTILE_STRUCTURES, 1).find(s => s.structureType !== STRUCTURE_CONTROLLER);
      const adjC = w.hc.find(h => c.pos.isNearTo(h));
      // while breaching/towers: smash adjacent rampart/wall before peeling creeps
      const adj = (t && t.structureType && adjS) ? adjS : (adjC || adjS);
      if (adj) c.attack(adj);
    }
  }
  const hr = hp && c.getActiveBodyparts(HEAL) ? hp : null, ht = hr && (hr.id === c.id ? c : Game.getObjectById(hr.id));
  if (ht && hr.mode === 'heal') c.heal(ht);
  else if (ht && hr.mode === 'ranged' && (hr.ratio < HEAL_URGENT || !ra || isHeal(c))) { c.rangedHeal(ht); return; }
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
function creepSlot(c) { return slotOf(c.memory.k, c.memory.kind); }
function travel(c, slot) {
  const b = c.pos.x === 0 || c.pos.x === 49 || c.pos.y === 0 || c.pos.y === 49;
  if (c.room.name === HOME) {
    if (c.pos.x === 0 && c.pos.y === 23) { delete c.memory._m; return c.move(LEFT); }
    if (b) { delete c.memory._m; return c.move(c.pos.x === 49 ? LEFT : c.pos.x === 0 ? RIGHT : c.pos.y === 0 ? BOTTOM : TOP); }
    return MV.to(c, 0, 23, 0);
  }
  if (c.room.name === STAGE) {
    if (b && c.pos.x === 49) { delete c.memory._m; return c.move(LEFT); }
    // ranged + heal hold back until living melee are on front row
    if (!isMelee(c)) {
      const ml = allRaid().filter(isMelee);
      const ready = ml.length > 0 && ml.every(x => {
        const s = creepSlot(x);
        return x.room.name === STAGE && x.pos.x === s[0] && x.pos.y === s[1];
      });
      if (!ready && !(c.pos.x === slot[0] && c.pos.y === slot[1])) return MV.to(c, slot[0], Math.min(49, slot[1] + 1), 0, ND);
    }
    return MV.to(c, slot[0], slot[1], 0, ND);
  }
  return c.moveTo(new RoomPosition(slot[0], slot[1], STAGE), { reusePath: 10 });
}
const GARRISON = [[30, 4], [31, 4], [30, 5], [31, 5], [32, 5], [29, 5]];
const gSlotOf = k => GARRISON[(k | 0) % GARRISON.length];
function garrison(c) {
  const g = gSlotOf(c.memory.k);
  const hp = c.getActiveBodyparts(HEAL) ? healPlan(c, squad(c)) : null;
  const w = { hc: c.room.find(FIND_HOSTILE_CREEPS) };
  if (w.hc.length || hp) {
    const ra = c.getActiveBodyparts(RANGED_ATTACK) > 0;
    const t = w.hc.length ? _.min(w.hc.filter(h => c.pos.inRangeTo(h, ra ? 3 : 1)), h => h.hits) : null;
    strike(c, t && t.id ? t : null, w, hp);
  }
  if (c.room.name === TARGET) return c.pos.y === 49 ? c.move(BOTTOM) : MV.to(c, 39, 49, 0, ND);
  if (c.room.name !== STAGE) return travel(c, g);
  if (c.pos.x === g[0] && c.pos.y === g[1]) return;
  return MV.to(c, g[0], g[1], 0, ND);
}
function armedParts(creeps) {
  let n = 0;
  for (const h of creeps) n += (h.attack | 0) + (h.ranged | 0);
  return n;
}
// Sustained SM-burn (Misaki): do not flee on a single mid-size defender wave.
// Only auto-flee when hostile ATTACK+RA parts are overwhelming (~boosted squad).
function overrun(room) {
  return armedParts(room.find(FIND_HOSTILE_CREEPS).map(h => ({
    attack: h.getActiveBodyparts(ATTACK), ranged: h.getActiveBodyparts(RANGED_ATTACK),
  }))) >= 40;
}
// North lip of STAGE, or already inside TARGET. Exact rally slots are not required.
function inAssaultZone(c) {
  if (!c || !c.room || !c.pos) return false;
  if (c.room.name === TARGET) return true;
  return c.room.name === STAGE && c.pos.y <= NEAR_EXIT;
}
// Preferred pair is two melee. Any two of melee+ranged also launches. Healers never count.
function assaultReady(creeps) {
  let melee = 0, combat = 0;
  for (const c of creeps || []) {
    const k = (c.memory && c.memory.kind) || 'm';
    if ((k !== 'm' && k !== 'r') || !inAssaultZone(c)) continue;
    combat++;
    if (k === 'm') melee++;
  }
  if (melee >= LAUNCH) return true;
  return combat >= LAUNCH;
}
const combatKind = c => { const k = (c.memory && c.memory.kind) || 'm'; return k === 'm' || k === 'r'; };
// Fresh wave only: nobody left in TARGET, and no melee/ranged still on the lip.
// One death while others are in the room or combat is still staging does not clear go.
// Healers alone on the lip are not an assault force.
function shouldRegroup(alive) {
  if (!alive || !alive.length) return true;
  for (const c of alive) {
    if (c.room && c.room.name === TARGET) return false;
    if (combatKind(c) && inAssaultZone(c)) return false;
  }
  return true;
}
function syncGo(P, alive) {
  if (!raidActive(P)) return;
  if (P.go && shouldRegroup(alive)) delete P.go;
  else if (!P.go && assaultReady(alive)) P.go = Game.time;
}
function run(c) {
  const P = M(), kind = c.memory.kind || 'm', slot = creepSlot(c);
  if (P.garrison || P.safe || P.flee) return garrison(c);
  const tr = Game.rooms[TARGET];
  if (tr && tr.controller && tr.controller.safeMode) P.safeUntil = Game.time + tr.controller.safeMode;
  const sm = P.safeUntil && Game.time < P.safeUntil;
  if (sm) { P.safe = P.safe || Game.time; if (c.room.name === TARGET && (c.pos.y === 49)) return c.move(BOTTOM); return travel(c, slot); }
  if (c.room.name === TARGET && overrun(c.room)) {
    P.flee = P.flee || { t: Game.time, why: 'overrun' };
    P.garrison = true;
    if (c.pos.y === 49) return c.move(BOTTOM);
    return MV.to(c, 39, 49, 0, ND);
  }
  // Continuous waves replace the fallen. Creeps already in TARGET stay on the breach.
  const alive = allRaid();
  syncGo(P, alive);
  if (c.room.name === TARGET) {
    const w = world(c.room), p = pick(c.pos, w), t = p && Game.getObjectById(p.id);
    const hp = c.getActiveBodyparts(HEAL) ? healPlan(c, squad(c)) : null;
    const mlHere = alive.filter(isMelee).filter(x => x.room.name === TARGET);
    // Support (ranged/heal) must not stand closer to BREACH than melee — clear the lane.
    const yieldLane = () => {
      if (isMelee(c) || !mlHere.length) return false;
      const myD = rng(c.pos, BREACH);
      if (!_.some(mlHere, m => rng(m.pos, BREACH) > myD)) return false;
      delete c.memory._m;
      // step south (higher y = back toward entry) to let melee pass north
      c.moveTo(c.pos.x, Math.min(49, c.pos.y + 2), { reusePath: 0, maxRooms: 1, ignoreCreeps: true, swampCost: 5 });
      return true;
    };
    // dedicated healers: heal first, stay behind melee
    if (isHeal(c)) {
      if (hp && hp.mode === 'heal') { c.heal(hp.id === c.id ? c : Game.getObjectById(hp.id)); }
      else if (hp && hp.mode === 'ranged') { c.rangedHeal(Game.getObjectById(hp.id)); }
      else if (hp && hp.mode === 'far') return c.moveTo(hp.pos, { range: 1, reusePath: 2, maxRooms: 1 });
      if (yieldLane()) return;
      const anchor = mlHere.length ? _.min(mlHere, x => rng(c.pos, x.pos)) : null;
      if (anchor) {
        // prefer 1–2 tiles behind melee (farther from BREACH / higher y)
        const by = Math.min(49, Math.max(anchor.pos.y, anchor.pos.y + 1));
        if (!c.pos.inRangeTo(anchor.pos.x, by, 1)) return MV.to(c, anchor.pos.x, by, 1, ND);
        return;
      }
      if (!c.pos.inRangeTo(BREACH.x, BREACH.y, 4)) {
        delete c.memory._m;
        return c.moveTo(new RoomPosition(BREACH.x, BREACH.y, TARGET), { range: 4, reusePath: 5, maxRooms: 1, ignoreDestructibleStructures: true, ignoreCreeps: true });
      }
      return;
    }
    strike(c, t, w, hp);
    if (c.pos.y === 49) return c.move(TOP);
    if (hp && hp.mode === 'far' && hp.ratio < HEAL_URGENT && !(p && p.pri <= 2)) return c.moveTo(hp.pos, { range: 1, reusePath: 2, maxRooms: 1 });
    // ranged: shoot then yield if blocking melee
    if (!isMelee(c) && yieldLane()) return;
    if (!t) {
      delete c.memory._m;
      return c.moveTo(new RoomPosition(BREACH.x, BREACH.y, TARGET), { range: isMelee(c) ? 1 : 3, reusePath: 5, maxRooms: 1, ignoreDestructibleStructures: true, ignoreCreeps: true });
    }
    const r = isMelee(c) ? 1 : (p.pri === 1 || p.pri === 3 ? 3 : 2);
    if (c.pos.inRangeTo(t, r)) return;
    if (t.structureType) {
      // only hold on the pick target / breach barrier — not random adjacent ramparts
      const edge = c.pos.findInRange(FIND_HOSTILE_STRUCTURES, 1).find(s =>
        (s.structureType === STRUCTURE_RAMPART || s.structureType === STRUCTURE_WALL)
        && (s.id === t.id || rng(s.pos, BREACH) <= 2));
      if (edge) return;
      delete c.memory._m;
      c.moveTo(t, { range: r, reusePath: 5, maxRooms: 1, ignoreDestructibleStructures: true, ignoreCreeps: true, swampCost: 5 });
      return;
    }
    MV.to(c, t.pos.x, t.pos.y, r, ND);
    return;
  }
  const hp = c.getActiveBodyparts(HEAL) ? healPlan(c, squad(c)) : null;
  const w = { hc: c.room.find(FIND_HOSTILE_CREEPS) }; if (w.hc.length || hp) strike(c, null, w, hp);
  if (P.go) {
    if (c.room.name === STAGE) {
      if (c.pos.y === 0) return c.move(TOP);
      if (!isMelee(c) && _.some(allRaid(), x => isMelee(x) && x.room.name === STAGE)) return;
      const ex = exitX(c.room, slot[0]);
      if (MV.to(c, ex, 0, 0, ND)) return c.move(TOP);
      return;
    }
    return travel(c, slot);
  }
  travel(c, slot);
}
function wantSpawn(room) {
  const P = Memory.ops && Memory.ops.w47n9;
  if (!raidActive(P)) return null;
  if (room.name !== HOME && room.name !== STAGE) return null;
  const alive = allRaid();
  if (alive.length >= WAVE) return null;
  const have = _.countBy(alive, c => c.memory.kind || 'm');
  let kind = null;
  for (const k of ['m', 'r', 'h']) if ((have[k] || 0) < NEED[k]) { kind = k; break; }
  if (!kind) return null;
  const used = new Set(alive.filter(c => c.memory.kind === kind).map(c => c.memory.k | 0));
  let slot = 0; while (used.has(slot)) slot++;
  return { role: 'raid9', body: BODY[kind](), mem: { role: 'raid9', home: room.name, k: slot, kind, born: Game.time } };
}
function noteSpawned() { const P = M(); P.n = (P.n | 0) + 1; }
function pauseCivilians() {
  const P = Memory.ops && Memory.ops.w47n9;
  return !!(P && P.on === true && !P.safe && !P.garrison && !P.flee);
}
module.exports = {
  slotOf, gSlotOf, GARRISON, BREACH, WAVE, NEED, run, pick, useMass, healPlan, armedParts, overrun,
  wantSpawn, noteSpawned, pauseCivilians, MELEE, RANGED, HEALER, RALLY, raidActive,
  NEAR_EXIT, LAUNCH, inAssaultZone, assaultReady, shouldRegroup, syncGo,
};
