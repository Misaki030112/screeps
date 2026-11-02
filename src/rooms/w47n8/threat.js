// W47N8 threat state (Misaki 14:23). Defensive only: no attacks, never safe mode.
//   mark(): every tick from W47N8 (+ W47N7 when visible). Armed (ATTACK/RANGED_ATTACK/WORK) or HEAL hostiles (TOUGH-only decoys ignored)
//           -> Memory.ops.w8threat = tick. Armed hostiles in W47N7 or W47N8 north (y<=10) -> Memory.ops.w8flee = tick.
//   tools/north_watch.py also sets Memory.ops.w8threatN when W47N9 holds an armed/drain group or W48N9 (BustJetter army room) >=2 armed (no in-game vision there).
//   on(): any of those within the last 1500 ticks -> seal walls to >=100k (10-20) ahead of upgrading (ramparts excluded 17:15) (auto-reverts when quiet).
//   flee(): armed hostiles seen in the last 20 ticks -> W47N7 remote creeps hold inside the W47N8 base.
const WINDOW = 1500, FLEE_QUIET = 20, FLOOR = 100000; // 10-20 14:0x Misaki: threat floor 50k -> 100k (W47N8 only)
const has = (c, ts) => c.body.some(p => ts.includes(p.type) && p.hits > 0);
const M = () => (Memory.ops = Memory.ops || {});
function mark(room) {
  if (!room) return;
  const hs = room.find(FIND_HOSTILE_CREEPS).filter(c => !c.my); if (!hs.length) return; /* hostile only: FIND_HOSTILE_CREEPS + explicit !my guard */
  const armed = hs.filter(c => has(c, [ATTACK, RANGED_ATTACK, WORK]));
  const drain = hs.filter(c => has(c, [HEAL])); // 10-20 06:2x: TOUGH-only decoys never count (Misaki: no influence on threat/defenders/towers); healers still do
  if (armed.length || drain.length) M().w8threat = Game.time;
  // 14:46 invasion move (Misaki): ATTACK/RANGED hostiles inside W47N8 -> w8inv (border ranged defenders spawn; see invasion())
  if (room.name === 'W47N8' && hs.some(c => has(c, [ATTACK, RANGED_ATTACK]))) M().w8inv = Game.time;
  const fl = hs.filter(c => has(c, [ATTACK, RANGED_ATTACK]) && (room.name !== 'W47N8' || c.pos.y <= 10));
  if (fl.length) M().w8flee = Game.time;
}
function on() { const o = M(), t = Math.max(o.w8threat || 0, o.w8threatN || 0); return t > 0 && Game.time - t < WINDOW; }
// 17:4x soft staging: local in-room/W47N7 threat only — neighbor staging (w8threatN) must not block soft raise
// (seal already at 300k; towers still prioritize attack/heal over repair).
function localOn() { const t = M().w8threat || 0; return t > 0 && Game.time - t < WINDOW; }
// invasion(): armed hostiles in W47N8 within 50 ticks, or north_watch saw >=2 armed in W47N9 (border room) within 300 ticks
function invasion() { const o = M(); return (o.w8inv > 0 && Game.time - o.w8inv < 50) || (o.w8invN > 0 && Game.time - o.w8invN < 300); }
function flee() { const t = M().w8flee || 0; return t > 0 && Game.time - t < FLEE_QUIET; }
// effective seal wall target: plan target, raised to the 100k floor while threatened
function wallTarget(base) { return on() ? Math.max(base, FLOOR) : base; }
// 10-20 06:3x strategy review: the part of the seal-wall raise that goes AHEAD of upgrading and construction sites. Only the threat
// floor (Misaki 14:23); the per-RCL target above it (100k at RCL5, 300k RCL6...) stays a surplus job (Misaki 19:18). Without this cap,
// RCL5 under the W47N9 camp would have queued ~600k hits (~6k energy, ~400 t) of wall repair before tower 24,8 with 1-2 upgraders,
// and RCL6 (300k) ~3M hits (~30k energy, hours of 1-2 upgraders) while the camp keeps threat mode on.
function urgentTarget() { return on() ? FLOOR : 0; }
// 10-20 14:0x Misaki: staged north line (11 walls + gate 29,3): 100k until the spawn move (Memory.ops.w8move) is done, then 300k
// from surplus; 500k later (after RCL6, not yet). Holds walls at 100k so storage can reach the 16k move trigger.
const STAGE1 = 100000, STAGE3 = 300000;
// 11-02 16:2x (Misaki t375u "加固城防，尤其面对他那一方"): post-W47N9-raid retaliation guard. Memory.defense knobs (absent = old behaviour):
//   w8seal      north seal walls + gate 29,3 cap above STAGE3 (clamped to WALL_TARGET[rcl]: 1M at RCL7). Builders raise lowest-first, so
//               the line climbs evenly 300k -> 1M.
//   w8sealMinE  colony storage needed to SPAWN a surplus wall builder AND for wallJob to aim above STAGE3 (default 35000 =
//               LEAN_SOFT+10k). Below it the spawn rule + wallJob see the old 300k cap, so the deep raise never starves softCap2 /
//               KEY catch-up / upgraders. 11-02 17:4x: was 5000→25000 (=LEAN_SOFT). 11-02 20:4x: raised again to 35000 —
//               Memory.defense.w8sealMinE=5000 (fortify knobs #23) overrode the code default and kept seal→1M draining
//               through softCap2; even sealMinE=LEAN_SOFT has zero hysteresis (seal starts the tick softCap clears → thrash).
//               Headroom above LEAN_SOFT lets nUp3 recover before deep seal. Override lower only for a deliberate early climb.
//   w8key       KEY rampart (spawn/tower/storage/terminal) soft target above SOFT_RAMP; w8keyMinE (default 8000) storage gate.
const D8 = () => (typeof Memory !== 'undefined' && Memory.defense) || {};
const num = (v, d) => (typeof v === 'number' && v >= 0 ? v : d);
function sealCap() { const v = num(D8().w8seal, 0); return v > STAGE3 ? v : STAGE3; }
function sealMinE() { return num(D8().w8sealMinE, 35000); }
function keyTarget() { return num(D8().w8key, 0); }
function keyMinE() { return num(D8().w8keyMinE, 8000); }
function planTarget(level, base) {
  if (level < 5) return base;
  const m = Memory.ops && Memory.ops.w8move;
  return (m && m.phase !== 'done') ? Math.min(base, STAGE1) : Math.max(STAGE3, Math.min(base, sealCap()));
}
module.exports = { sealCap, sealMinE, keyTarget, keyMinE, planTarget, STAGE1, STAGE3, mark, on, localOn, flee, invasion, wallTarget, urgentTarget, WINDOW, FLOOR };
