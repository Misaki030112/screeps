// Lab scaffold (Misaki 2026-10-20 21:0x "开矿物线", boosts). DORMANT unless Memory.ops.labs = { W46N8: 'KO' } (compound to make).
// W46N8 labs 34,22 / 33,21 / 35,21 (plan rcl6) are all within range 2: the output is the lab in range 2 of both others.
// Reaction only: runReaction when both inputs hold >= 5 of their reagent. task(room) names the next terminal<->lab move for a
// carrier (not wired into any role yet: no reagents in stock; wire when Misaki buys the 2nd mineral). No market calls here.
const R = { KO: ['K', 'O'], LO: ['L', 'O'], UH: ['U', 'H'], OH: ['O', 'H'], ZO: ['Z', 'O'], UO: ['U', 'O'] };
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
module.exports = { R, cfg, roles, task, run(room) {
  const c = cfg(room); if (!c) return 0;
  const labs = room.find(FIND_MY_STRUCTURES).filter(s => s.structureType === STRUCTURE_LAB), ro = roles(labs); if (!ro) return 0;
  const [a, b] = ro.ins, [ra, rb] = R[c];
  if (ro.out.cooldown || amt(a, ra) < 5 || amt(b, rb) < 5) return 0;
  const k = kind(ro.out); if (k && k !== c) return 0;
  return ro.out.runReaction(a, b) === OK ? 1 : 0;
} };
