// In-room move for W47N8 creeps (combat roles with their own cost matrix; since 11-11 also the roles.js `go` helper)
// (no exit tiles, no seal rows). Patrol 2026-11-11: vanilla moveTo searches with creeps as obstacles. A hauler in the
// 1-wide 27,17 / 28,19 corridor made that search INCOMPLETE, and moveTo then walks to the tile nearest BY RANGE to the goal:
// the walled NE pocket 35,10 (range 6 from the guard hold 29,5, real path 56). w8guard84199224 oscillated 35,10 <-> 46,21 for
// ~900 t and never reached its hold; w8defender84199225 did the same for ~400 t before it got through.
// Search ignores creeps (like utils/move); only after STUCK ticks without moving (fatigue excluded) one creep-aware search
// routes around a real blocker.
const STUCK = 3;
function militaryTo(c, x, y, range, costCallback) {
  const mil = require('./military');
  const cb = costCallback ? (rn => {
    const m = new PathFinder.CostMatrix();
    return costCallback(rn, m) || m;
  }) : undefined;
  const st = mil.step(c, x, y, range, cb);
  // 'moved' is a successful step this tick. 'wait' is fatigue. 'no' is a blocked or empty search.
  if (st === 'there' || st === 'moved') return OK;
  if (st === 'wait') return typeof ERR_TIRED !== 'undefined' ? ERR_TIRED : -11;
  return typeof ERR_NO_PATH !== 'undefined' ? ERR_NO_PATH : -2;
}
function to(c, x, y, range, costCallback, reusePath) {
  // Combat roles recalculate every tick and swap civilians. Haulers/builders keep the stuck-3 cache below.
  if (c && c.memory && require('./military').isMilitary(c) && typeof PathFinder !== 'undefined') return militaryTo(c, x, y, range, costCallback);
  const m = c.memory, here = c.pos.x * 50 + c.pos.y, t = Game.time;
  if (c.pos.inRangeTo(x, y, range)) { m.cm = { p: here, n: 0, t }; return OK; }
  if (m.cm && m.cm.p === here && m.cm.t === t - 1 && !c.fatigue) m.cm.n++; else m.cm = { p: here, n: 0 };
  m.cm.t = t;
  const around = m.cm.n >= STUCK;
  if (around) { delete m._move; m.cm.n = 0; }
  return c.moveTo(x, y, { range, maxRooms: 1, reusePath: around ? 0 : reusePath, costCallback, ignoreCreeps: !around });
}
module.exports = { to, STUCK };
