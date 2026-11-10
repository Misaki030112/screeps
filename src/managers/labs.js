// Lab scaffold (Misaki 2026-10-20 21:0x "开矿物线", boosts). DORMANT unless Memory.ops.labs = { W46N8: 'KO' } (compound to make).
// W46N8 labs 34,22 / 33,21 / 35,21 (plan rcl6) are all within range 2: the output is the lab in range 2 of both others.
// Reaction only: runReaction when both inputs hold >= 5 of their reagent. task(room) names the next terminal<->lab move;
// home hauler.labRun executes it (tests/labs_hauler.js). Strategy 14:4x review: propose Memory.ops.labs when labReady.propose=1
// (first K ≥ PROPOSE_K lands) — never auto-set. Lab energy fill / boostCreep wait KO≥900 (boost.js later).
const R = { KO: ['K', 'O'], LO: ['L', 'O'], UH: ['U', 'H'], OH: ['O', 'H'], ZO: ['Z', 'O'], UO: ['U', 'O'] };
// One input-lab fill / thin-batch size — enough for task() to start loading (≥100) and match SEND_BATCH_THIN.
const PROPOSE_K = 1000;
const PROPOSE_O = 1000;
// 23:4x strategy 2026-11-01: activation checklist floors (docs/MINERAL_DEFENSE_ROADMAP.md §5.21).
// Prefer nod only when home can spare a 1k K load without emptying terminal; reaction itself needs no lab energy.
const ACT_HOME_STOR = 15000;  // = reserveE / upgFeed.floor — keep upgrade pressure
const ACT_K_BUF = 3000;       // ≥1k load + ≥2k residual for continuous KO / thin-send jitter
const ACT_O_BUF = 3000;
// Dormant readyObs is a FIND_MY_STRUCTURES every tick (~0.10 CPU) while Memory.ops.labs is off.
// Rescan every READY_EVERY ticks (inside 10–50). Turning labs on scans immediately. Never starts a reaction.
const READY_EVERY = 20;
function cfg(room) { const o = typeof Memory !== 'undefined' && Memory.ops && Memory.ops.labs; return o && R[o[room.name]] ? o[room.name] : null; }
function roles(labs) {
  if (labs.length < 3) return null;
  const out = labs.find(l => labs.every(o => o === l || l.pos.getRangeTo(o) <= 2)); if (!out) return null;
  const ins = labs.filter(l => l !== out).sort((a, b) => a.pos.x - b.pos.x || a.pos.y - b.pos.y).slice(0, 2);
  return { out, ins };
}
const amt = (l, r) => (l.store && l.store[r]) || 0;
const kind = l => Object.keys(l.store || {}).find(k => k !== 'energy' && l.store[k] > 0);
function task(room, labs) {
  const c = cfg(room); if (!c || !room.terminal) return null; const ro = roles(labs); if (!ro) return null;
  for (let i = 0; i < 2; i++) { const l = ro.ins[i], need = R[c][i], k = kind(l);
    if (k && k !== need) return { from: l.id, to: room.terminal.id, res: k };            // wrong reagent: empty it
    if (amt(l, need) < 1000 && (room.terminal.store[need] || 0) >= 100) return { from: room.terminal.id, to: l.id, res: need }; }
  const k = kind(ro.out); if (k && amt(ro.out, k) >= 1000) return { from: ro.out.id, to: room.terminal.id, res: k };
  return null;
}
// 14:4x strategy 2026-11-01: home KO readiness obs for patrol propose (Overmind EvolutionChamber AcquiringMinerals —
// start once reagents present; we gate on Misaki Memory.ops.labs, so patrol needs a clear propose flag).
// 23:4x: also publish actOk/actGaps so strategy can tell "propose" (K landed) from "safe to nod now"
// (storage floor + terminal buffer). Reaction still needs no lab energy; boost waits KO≥900.
function readyObs(room) {
  if (!room || room.name !== 'W46N8') return;
  const ops0 = (typeof Memory !== 'undefined' && Memory && (Memory.ops = Memory.ops || {})) || null;
  const prev = ops0 && ops0.labReady;
  // Labs off: keep the last snapshot until READY_EVERY ticks have passed. No find on the skipped ticks.
  if (!cfg(room) && prev && typeof prev.t === 'number' && Game.time > prev.t && Game.time - prev.t < READY_EVERY) return;
  const term = room.terminal, stor = room.storage;
  const labs = room.find(FIND_MY_STRUCTURES).filter(s => s.structureType === STRUCTURE_LAB);
  const kTerm = (term && term.store && (term.store.K || 0)) || 0;
  const oTerm = (term && term.store && (term.store.O || 0)) || 0;
  const kStor = (stor && stor.store && (stor.store.K || 0)) || 0;
  const oStor = (stor && stor.store && (stor.store.O || 0)) || 0;
  const homeStor = (stor && stor.store && (stor.store.energy || 0)) || 0;
  const k = kTerm + kStor, o = oTerm + oStor;
  let koTerm = (term && term.store && (term.store.KO || 0)) || 0;
  let koLab = 0;
  for (const l of labs) koLab += (l.store && (l.store.KO || 0)) || 0;
  const mode = cfg(room);
  let why = 'ok', ready = 0, propose = 0;
  if (mode) why = 'active';
  else if (labs.length < 3) why = 'noLabs';
  else if (!term) why = 'noTerm';
  else if (k < PROPOSE_K) why = 'noK';
  else if (o < PROPOSE_O) why = 'noO';
  else { ready = 1; propose = 1; why = 'ready'; }
  // Activation checklist (independent of propose): Overmind starts AcquiringMinerals with reagents present
  // without pausing UpgradeSite; TooAngel keeps ~1k other minerals for reaction. We add a thin buffer so
  // the first 1k K lab load does not empty terminal while thin-send still jitters.
  const gaps = [];
  if (homeStor < ACT_HOME_STOR) gaps.push('homeStor');
  if (kTerm < ACT_K_BUF) gaps.push('kBuf');
  if (oTerm + oStor < ACT_O_BUF) gaps.push('oBuf');
  const actOk = gaps.length ? 0 : 1;
  const ops = (Memory.ops = Memory.ops || {});
  ops.labReady = {
    t: Game.time, mode: mode || null, kTerm, oTerm, k, o, labsN: labs.length,
    ready, propose, why, hasCode: 1, proposeK: PROPOSE_K,
    homeStor, koTerm, koLab, ko: koTerm + koLab,
    actOk, actGaps: gaps.join(',') || '',
    actHome: ACT_HOME_STOR, actK: ACT_K_BUF, actO: ACT_O_BUF,
  };
}
module.exports = { R, cfg, roles, task, PROPOSE_K, PROPOSE_O, ACT_HOME_STOR, ACT_K_BUF, ACT_O_BUF, READY_EVERY, readyObs, run(room) {
  readyObs(room);
  const c = cfg(room); if (!c) return 0;
  const labs = room.find(FIND_MY_STRUCTURES).filter(s => s.structureType === STRUCTURE_LAB), ro = roles(labs); if (!ro) return 0;
  const [a, b] = ro.ins, [ra, rb] = R[c];
  // Any lab with a live order yields. react on the output runs that reaction and skips auto.
  // An idle/hold on an input also skips auto. Does not write Memory.ops.labs.
  { const cmd = require('../utils/cmd'); if (cmd.armed()) {
    const oo = cmd.structOrder(ro.out.id);
    if (oo && oo.act === 'react') { cmd.consumeLab(ro.out); return 0; }
    if ((oo && cmd.consumeLab(ro.out)) || ro.ins.some(l => cmd.consumeLab(l))) return 0;
  } }
  if (ro.out.cooldown || amt(a, ra) < 5 || amt(b, rb) < 5) return 0;
  const k = kind(ro.out); if (k && k !== c) return 0;
  return ro.out.runReaction(a, b) === OK ? 1 : 0;
} };
