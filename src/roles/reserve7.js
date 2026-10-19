// W47N7 reservation (Misaki 17:13). Home reserver walks W46N8 -> W47N8 -> W47N7 (its only exits: N=W47N8, S=W47N6),
// waits next to the controller while BustJetter's reservation runs and reserves the tick it ends. NEVER attackController.
// Memory.ops.r7 = { on, endTime (foreign/our reservation end, seeded from the room-objects API, refreshed with vision) }.
const ROOM = 'W47N7', CTL = [38, 26], LEAD = 260; // spawn 12t + walk ~200t + margin
const M = () => { const o = Memory.ops || (Memory.ops = {}); return o.r7 || (o.r7 = {}); };
function seen() {
  const r = Game.rooms[ROOM]; if (!r || !r.controller) return;
  const res = r.controller.reservation;
  M().endTime = res ? Game.time + res.ticksToEnd : Game.time; M().by = res ? res.username : null;
}
// 10-20 04:4x strategy review (docs/MODEL.md "04:4x reserve7 owner"): holding W47N7 costs ~1.3 e/t (2C2M 1300 e per 600 t, minus a
// ~100-120 t walk from Spawn1 (PathFinder 102 tiles) vs ~75-80 t from Spawn2 (73 tiles)). Home was paying it for W47N8's remote while
// home RCL7 (3rd tower, wall step 2) lands ~10-27, right before novice end. Once W47N8 can pay it without draining its whole spawn
// energy (cap >= 1800, RCL5) Spawn2 spawns it; home stays the fallback when our reservation is under FALLBACK (Spawn2 busy/lost).
const W8 = 'W47N8', W8_CAP = 1800, FALLBACK = 1000;
function w8Ready() { const r = Game.rooms[W8]; return !!(r && r.controller && r.controller.my && r.energyCapacityAvailable >= W8_CAP && r.find(FIND_MY_SPAWNS).length); }
function wantSpawn(from = 'W46N8') {
  const P = M(); if (!P.on) return null; seen();
  if (_.some(Game.creeps, c => c.memory.role === 'reserve7' && (c.spawning || c.ticksToLive > LEAD))) return null;
  const left = (P.endTime || 0) - Game.time;
  const ours = P.by === 'Misaki';
  if (!(ours ? left < 2500 : left < LEAD)) return null;
  const w8 = w8Ready();
  if (from === W8 ? !w8 : w8 && !(ours && left < FALLBACK)) return null;
  return { role: 'reserve7', body: [CLAIM, CLAIM, MOVE, MOVE], mem: { role: 'reserve7', home: from, v2: 1, born: Game.time } };
}
function run(c) {
  seen();
  if (c.room.name !== ROOM || !c.pos.isNearTo(CTL[0], CTL[1])) return c.moveTo(new RoomPosition(CTL[0], CTL[1], ROOM), { range: 1, reusePath: 20 });
  const ctl = c.room.controller, res = ctl.reservation;
  if (res && res.username !== c.owner.username) return; // wait: foreign reservation still active (no attackController)
  c.reserveController(ctl);
  { const S = require('../utils/sign'); if (S.needs(ctl, c.owner.username) && c.pos.isNearTo(ctl)) c.signController(ctl, S.SIGN); } // same sign as home (22:19)
}
module.exports = { run, wantSpawn, w8Ready, ROOM, W8_CAP, FALLBACK };
