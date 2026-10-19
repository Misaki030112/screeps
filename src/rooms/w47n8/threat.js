// W47N8 threat state (Misaki 14:23). Defensive only: no attacks, never safe mode.
//   mark(): every tick from W47N8 (+ W47N7 when visible). Armed (ATTACK/RANGED_ATTACK/WORK) or HEAL hostiles (TOUGH-only decoys ignored)
//           -> Memory.ops.w8threat = tick. Armed hostiles in W47N7 or W47N8 north (y<=10) -> Memory.ops.w8flee = tick.
//   tools/north_watch.py also sets Memory.ops.w8threatN when W47N9 holds an armed/drain group or W48N9 (BustJetter army room) >=2 armed (no in-game vision there).
//   on(): any of those within the last 1500 ticks -> seal walls to >=50k ahead of upgrading (ramparts excluded 17:15) (auto-reverts when quiet).
//   flee(): armed hostiles seen in the last 20 ticks -> W47N7 remote creeps hold inside the W47N8 base.
const WINDOW = 1500, FLEE_QUIET = 20, FLOOR = 50000;
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
// invasion(): armed hostiles in W47N8 within 50 ticks, or north_watch saw >=2 armed in W47N9 (border room) within 300 ticks
function invasion() { const o = M(); return (o.w8inv > 0 && Game.time - o.w8inv < 50) || (o.w8invN > 0 && Game.time - o.w8invN < 300); }
function flee() { const t = M().w8flee || 0; return t > 0 && Game.time - t < FLEE_QUIET; }
// effective seal wall target: plan target, raised to 50k while threatened
function wallTarget(base) { return on() ? Math.max(base, FLOOR) : base; }
// 10-20 06:3x strategy review: the part of the seal-wall raise that goes AHEAD of upgrading and construction sites. Only the threat
// floor (Misaki 14:23); the per-RCL target above it (100k at RCL5, 300k RCL6...) stays a surplus job (Misaki 19:18). Without this cap,
// RCL5 under the W47N9 camp would have queued ~600k hits (~6k energy, ~400 t) of wall repair before tower 24,8 with 1-2 upgraders,
// and RCL6 (300k) ~3M hits (~30k energy, hours of 1-2 upgraders) while the camp keeps threat mode on.
function urgentTarget() { return on() ? FLOOR : 0; }
module.exports = { mark, on, flee, invasion, wallTarget, urgentTarget, WINDOW, FLOOR };
