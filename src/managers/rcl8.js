// Home W46N8 at RCL8 — independent development (Misaki 2026-11-26 t514u "双房独立发展", t511u first principles).
// Measured 11:17-15:15 JST (ledger, 3393 t): income ~37 e/t; tower rampart repair 12.7, build 9.0 (power spawn/nuker/observer
// all at once), tower road/container 5.5, spawn ~15 net -> storage 11.7k -> 4.2k, under the 15k defence cushion.
// Priority with that income: (1) defence cushion + spawning, (2) GCL (1 x 15W, fed by source-A link first), (3) cheap useful
// RCL8 structures (observer), (4) everything else only from true surplus:
//   - power spawn / nuker sites stay placed (Misaki: auto-place, do not block) but builders and builder demand skip them until
//     storage has held OPT_ON (cleared below OPT_OFF). Power spawn has no power to burn (0 stock, GPL 0); a nuker needs
//     ghodium we cannot get without the market, and launching is an attack (not authorised).
//   - RCL8 rampart growth 1M -> 3M by towers only while storage >= GROW_ON (cleared below GROW_OFF); otherwise the RCL7
//     target 1M is kept (a 1M rampart already outlasts anything an NPC or a small player brings; 1M -> 3M = 20k energy each).
const OPT = { powerSpawn: 1, nuker: 1 };
const OPT_ON = 40000, OPT_OFF = 20000;
const GROW_ON = 60000, GROW_OFF = 40000;
const RAMP_RCL7 = 1000000;
const storE = room => (room && room.storage && room.storage.store && (room.storage.store.energy || 0)) || 0;
const lvl = room => (room && room.controller && room.controller.level) || 0;
function latch(room, key, on, off) {
  const mm = room.memory || (room.memory = {}), m = mm.rcl8 || (mm.rcl8 = {}), e = storE(room);
  if (m[key] && e < off) m[key] = 0; else if (!m[key] && e >= on) m[key] = 1;
  return !!m[key];
}
const optOpen = room => latch(room, 'opt', OPT_ON, OPT_OFF);
// A placed site the builders leave alone for now (not counted as builder demand either).
function deferSite(room, s) { return !!(s && OPT[s.structureType] && lvl(room) >= 8 && !optOpen(room)); }
// Tower rampart cap for the room at its level (tower.js); RCL8 grows past 1M only from surplus.
function rampTarget(room, rclT) { if (lvl(room) < 8 || rclT <= RAMP_RCL7) return rclT; return latch(room, 'grow', GROW_ON, GROW_OFF) ? rclT : RAMP_RCL7; }
module.exports = { OPT, OPT_ON, OPT_OFF, GROW_ON, GROW_OFF, RAMP_RCL7, optOpen, deferSite, rampTarget };
