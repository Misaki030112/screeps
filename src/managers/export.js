// RCL8 energy export W46N8 -> W47N8 (2026-11-26, Misaki t511u "遵循第一性原理，好好规划 RCL8").
// First principles: home is RCL8, so its controller only feeds GCL (cap 15 e/t). The same energy upgraded in W47N8 (RCL7,
// 3.15M to go) counts the same for GCL *and* brings W47's RCL8 (3rd spawn, 6 towers, 60 ext) closer. A terminal send between the
// two adjacent rooms costs ceil(amt * (1 - exp(-1/30))) ≈ 3.3% (165 per 5000) — not a market order, no credits.
// While on (home RCL8, colony < RCL8, both terminals): home keeps no 15 W upgrader (spawn.js homeUpgrade8: a guard upgrader only
// when ticksToDowngrade < GUARD_TTD), the home hauler moves storage energy above EXPORT_KEEP into the home terminal
// (manager tile 36,30 touches storage, terminal and hub link), and this module sends BATCH to W47N8 when the terminal holds
// BATCH + fee. W47's filler moves terminal energy above fill.TERM_KEEP into storage, where W47's upgrader rules see it.
// Off: Memory.ops.export === false (console), home threat (remote defence holding, home alert, hostiles in home), colony RCL8,
// colony storage+terminal energy >= COLONY_FULL. Off returns the home rules to 1 upgrader at RCL8 once the colony is RCL8.
const HOME = 'W46N8', COLONY = 'W47N8', E = 'energy';
const EXPORT_ON = 20000;   // hauler starts filling the terminal only while home storage >= 20k (15k reserveE + 5k builder band)
const EXPORT_KEEP = 18000; // and never takes storage below 18k
const TERM_TARGET = 6000;  // home terminal energy the hauler tops up to (one batch + fee + slack)
const BATCH = 5000;
const COLONY_FULL = 150000;
const GUARD_TTD = 100000;  // RCL8 downgrade timer is 200k; a guard upgrader restores +100 per upgrading tick
const om = () => (Memory.ops = Memory.ops || {});
function rooms() { const R = (typeof Game !== 'undefined' && Game.rooms) || {}; return { home: R[HOME], col: R[COLONY] }; }
// Structural switch: home exports instead of upgrading. Threat does not flip it (the guard upgrader keeps the controller safe).
function exporting() {
  if (typeof Memory !== 'undefined' && Memory.ops && Memory.ops.export === false) return false;
  const { home, col } = rooms();
  if (!home || !home.controller || !home.controller.my || home.controller.level < 8 || !home.terminal || !home.storage) return false;
  if (!col || !col.controller || !col.controller.my || col.controller.level >= 8 || !col.terminal || !col.storage) return false;
  return true;
}
function homeThreat(home) {
  try { if (require('./threat').holding(HOME)) return 'remoteHold'; } catch (e) { /* threat optional in tests */ }
  try { if (require('./home').alert(home)) return 'alert'; } catch (e) { /* ok */ }
  if (typeof FIND_HOSTILE_CREEPS !== 'undefined' && home.find(FIND_HOSTILE_CREEPS).length) return 'hostiles';
  return null;
}
function colonyE(col) { return (col.storage.store[E] || 0) + (col.terminal.store[E] || 0); }
// Live flow gate (hauler fill + send). Returns null when energy may move, else a short reason.
function blocked() {
  if (!exporting()) return 'off';
  const { home, col } = rooms();
  const th = homeThreat(home); if (th) return th;
  if (colonyE(col) >= COLONY_FULL) return 'colonyFull';
  return null;
}
// Home RCL8 upgrader target (spawn.js). Exporting: 0, or 1 guard while the downgrade timer is under GUARD_TTD.
function homeUpgrade8(room) {
  if (!exporting()) return 1;
  return (room.controller.ticksToDowngrade || 0) < GUARD_TTD ? 1 : 0;
}
function fee(amt) {
  if (Game.market && Game.market.calcTransactionCost) return Game.market.calcTransactionCost(amt, HOME, COLONY);
  return Math.ceil(amt * (1 - Math.exp(-1 / 30)));
}
// Energy the home hauler should move storage -> terminal now (0 = nothing).
function fillAmount(room) {
  if (!room || room.name !== HOME || blocked()) return 0;
  const st = room.storage, t = room.terminal, se = st.store[E] || 0, te = t.store[E] || 0;
  if (se < EXPORT_ON) return 0;
  return Math.max(0, Math.min(se - EXPORT_KEEP, TERM_TARGET - te, t.store.getFreeCapacity(E)));
}
function run() {
  if (Game.time % 5) return;
  const m = om(), x = (m.exportStat = m.exportStat || { sent: 0, fee: 0, n: 0 });
  const why = blocked(); x.why = why || 'ok'; x.t = Game.time;
  if (why) return;
  const { home, col } = rooms(), t = home.terminal;
  if (t.cooldown) return;
  const f = fee(BATCH), te = t.store[E] || 0;
  if (te < BATCH + f) return;
  if (col.terminal.store.getFreeCapacity() < BATCH + 10000) { x.why = 'colTermFull'; return; }
  const r = t.send(E, BATCH, COLONY, 'rcl8 export');
  if (r === OK) { x.sent += BATCH; x.fee += f; x.n++; x.last = Game.time; } else x.why = 'err' + r;
}
module.exports = { HOME, COLONY, EXPORT_ON, EXPORT_KEEP, TERM_TARGET, BATCH, COLONY_FULL, GUARD_TTD, exporting, blocked, homeUpgrade8, fillAmount, fee, run };
