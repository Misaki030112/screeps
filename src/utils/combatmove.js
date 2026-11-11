// In-room move for the W47N8 combat creeps (w8guard / w8defender / w8healer) that keeps each role's own cost matrix
// (no exit tiles, no seal rows). Patrol 2026-11-11: vanilla moveTo searches with creeps as obstacles. A hauler in the
// 1-wide 27,17 / 28,19 corridor made that search INCOMPLETE, and moveTo then walks to the tile nearest BY RANGE to the goal:
// the walled NE pocket 35,10 (range 6 from the guard hold 29,5, real path 56). w8guard84199224 oscillated 35,10 <-> 46,21 for
// ~900 t and never reached its hold; w8defender84199225 did the same for ~400 t before it got through.
// Search ignores creeps (like utils/move); only after STUCK ticks without moving (fatigue excluded) one creep-aware search
// routes around a real blocker.
const STUCK = 3;
function to(c, x, y, range, costCallback, reusePath) {
  const m = c.memory, here = c.pos.x * 50 + c.pos.y, t = Game.time;
  if (c.pos.inRangeTo(x, y, range)) { m.cm = { p: here, n: 0, t }; return OK; }
  if (m.cm && m.cm.p === here && m.cm.t === t - 1 && !c.fatigue) m.cm.n++; else m.cm = { p: here, n: 0 };
  m.cm.t = t;
  const around = m.cm.n >= STUCK;
  if (around) { delete m._move; m.cm.n = 0; }
  return c.moveTo(x, y, { range, maxRooms: 1, reusePath: around ? 0 : reusePath, costCallback, ignoreCreeps: !around });
}
module.exports = { to, STUCK };
