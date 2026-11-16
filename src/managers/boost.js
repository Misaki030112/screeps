// Default KO boost for kite-bodied ranged attackers spawned at home (W46N8).
// Dormant until a new kite is standing in W46N8. Does not set Memory.ops.labs and does not
// start W47 reactions. Core busters (ATTACK, no RANGED_ATTACK) and melee w8guards are skipped.
// A 19 RA kite needs 570 KO and 380 energy. The lab is filled toward KO>=900 when the colony has it.
// Lab energy is not taken from storage while storage is under STOR_SAFE (20k); the creep leaves
// unboosted instead of dipping the 15k floor. A lab that already holds the energy can still boost.
const HOME = 'W46N8';
const KO = 'KO';
const PART_KO = 30;
const PART_E = 20;
const KO_FILL = 900;
const STOR_SAFE = 20000;
const KITE_ROLES = { defender: 1, guard: 1, rdef: 1, w8defender: 1, w8guard: 1 };
const E = () => (typeof RESOURCE_ENERGY !== 'undefined' ? RESOURCE_ENERGY : 'energy');
const RA = () => (typeof RANGED_ATTACK !== 'undefined' ? RANGED_ATTACK : 'ranged_attack');
const ATK = () => (typeof ATTACK !== 'undefined' ? ATTACK : 'attack');
function pType(p) { return typeof p === 'string' ? p : (p && p.type); }
function boosted(p) { return !!(p && typeof p === 'object' && p.boost); }
function pile(store, res) { return (store && store[res]) || 0; }
function isKite(c) {
  if (!c || !c.memory || !KITE_ROLES[c.memory.role]) return false;
  const body = c.body || [];
  let ra = 0, atk = 0;
  for (const p of body) {
    const t = pType(p);
    if (t === RA() && !boosted(p)) ra++;
    if (t === ATK()) atk++;
  }
  return ra > 0 && atk === 0;
}
function raNeed(c) {
  let n = 0;
  for (const p of (c.body || [])) if (pType(p) === RA() && !boosted(p)) n++;
  return n;
}
function labsOf(room) {
  if (!room || typeof room.find !== 'function' || typeof FIND_MY_STRUCTURES === 'undefined') return [];
  if (room._boostLabsT === Game.time && room._boostLabs) return room._boostLabs;
  const labs = room.find(FIND_MY_STRUCTURES).filter(s => s.structureType === (typeof STRUCTURE_LAB !== 'undefined' ? STRUCTURE_LAB : 'lab'));
  room._boostLabs = labs; room._boostLabsT = Game.time;
  return labs;
}
function colony(room, res) {
  let n = pile(room.terminal && room.terminal.store, res) + pile(room.storage && room.storage.store, res);
  for (const l of labsOf(room)) n += pile(l.store, res);
  return n;
}
function safeEnergy(room) {
  const storE = pile(room.storage && room.storage.store, E());
  const termE = pile(room.terminal && room.terminal.store, E());
  return { storE, termE, fromStor: Math.max(0, storE - STOR_SAFE) };
}
// A lab that is not an input of the home reaction pair. The reaction output is used only when
// every lab is in the pair, and reactions pause while a kite is waiting on it.
function pickLab(room, preferId) {
  const labs = labsOf(room);
  if (!labs.length) return null;
  let ro = null;
  try { ro = require('./labs').roles(labs); } catch (e) { ro = null; }
  const inputs = new Set();
  if (ro) { inputs.add(ro.ins[0].id); inputs.add(ro.ins[1].id); }
  const free = labs.filter(l => !inputs.has(l.id) && !(ro && l === ro.out));
  const prefer = preferId && labs.find(l => l.id === preferId && !inputs.has(l.id));
  if (prefer && free.some(l => l === prefer)) return { lab: prefer, pause: false };
  if (free.length) {
    free.sort((a, b) => pile(b.store, KO) - pile(a.store, KO));
    return { lab: free[0], pause: false };
  }
  if (prefer && ro && prefer === ro.out) return { lab: prefer, pause: true };
  if (ro) return { lab: ro.out, pause: true };
  return { lab: labs[0], pause: false };
}
function plan(room, c) {
  if (!isKite(c)) return { act: 'skip', why: 'body' };
  if (!c.room || c.room.name !== HOME) return { act: 'skip', why: 'away' };
  const parts = raNeed(c);
  if (!parts) return { act: 'done' };
  const pick = pickLab(room, c.memory && c.memory.bl);
  if (!pick) return { act: 'skip', why: 'nolab' };
  const needK = parts * PART_KO, needE = parts * PART_E;
  const totalK = colony(room, KO);
  if (totalK < needK) return { act: 'skip', why: 'ko', pick, needK, needE };
  const bar = totalK >= KO_FILL ? KO_FILL : needK;
  const labK = pile(pick.lab.store, KO), labE = pile(pick.lab.store, E());
  const energy = safeEnergy(room);
  if (labE + energy.fromStor + energy.termE < needE) return { act: 'skip', why: 'energy', pick, needK, needE, bar };
  if (labK >= bar && labE >= needE) return { act: 'ready', pick, needK, needE, bar };
  return { act: 'wait', pick, needK, needE, bar };
}
function waiters(room) {
  const creeps = (typeof Game !== 'undefined' && Game.creeps) || {};
  const out = [];
  for (const n in creeps) {
    const c = creeps[n];
    if (!c || !c.memory || c.spawning || c.memory.boosted || c.memory.noBoost) continue;
    if (!c.room || c.room.name !== (room && room.name)) continue;
    if (!isKite(c)) continue;
    out.push(c);
  }
  return out;
}
function blocksReaction(room) {
  for (const c of waiters(room)) {
    const p = plan(room, c);
    if ((p.act === 'wait' || p.act === 'ready') && p.pick && p.pick.pause) return true;
  }
  return false;
}
function haulTask(room) {
  if (!room) return null;
  for (const c of waiters(room)) {
    const p = plan(room, c);
    if (p.act !== 'wait' || !p.pick) continue;
    const lab = p.pick.lab;
    const labK = pile(lab.store, KO);
    if (labK < p.bar) {
      const want = p.bar - labK;
      const tK = pile(room.terminal && room.terminal.store, KO);
      if (tK > 0 && room.terminal) return { from: room.terminal.id, to: lab.id, res: KO, amt: Math.min(tK, want) };
      const sK = pile(room.storage && room.storage.store, KO);
      if (sK > 0 && room.storage) return { from: room.storage.id, to: lab.id, res: KO, amt: Math.min(sK, want) };
      for (const other of labsOf(room)) {
        if (other === lab) continue;
        const k = pile(other.store, KO);
        if (k > 0) return { from: other.id, to: lab.id, res: KO, amt: Math.min(k, want) };
      }
    }
    const labE = pile(lab.store, E());
    if (labE < p.needE) {
      const want = p.needE - labE;
      const energy = safeEnergy(room);
      if (energy.fromStor > 0 && room.storage) return { from: room.storage.id, to: lab.id, res: E(), amt: Math.min(energy.fromStor, want) };
      if (energy.termE > 0 && room.terminal) return { from: room.terminal.id, to: lab.id, res: E(), amt: Math.min(energy.termE, want) };
    }
  }
  return null;
}
// True while the creep must stay at home. False: leave (skipped, already boosted, or boost just landed).
function hold(c) {
  if (!c || !c.memory || c.spawning || c.memory.boosted || c.memory.noBoost) return false;
  if (!isKite(c)) { c.memory.noBoost = 1; return false; }
  const room = c.room;
  if (!room || room.name !== HOME) { c.memory.noBoost = 1; return false; }
  const p = plan(room, c);
  if (p.act === 'done') { c.memory.boosted = 1; return false; }
  if (p.act === 'skip' || !p.pick) { c.memory.noBoost = 1; return false; }
  const lab = p.pick.lab;
  c.memory.bl = lab.id;
  let there = false;
  try { there = require('../utils/move').to(c, lab.pos.x, lab.pos.y, 1); } catch (e) { there = false; }
  if (p.act === 'ready' && there && typeof lab.boostCreep === 'function') {
    const rv = lab.boostCreep(c);
    if (rv === 0) { c.memory.boosted = 1; return false; }
  }
  return true;
}
module.exports = {
  HOME, KO, PART_KO, PART_E, KO_FILL, STOR_SAFE, isKite, raNeed, pickLab, plan, haulTask, blocksReaction, hold,
};
