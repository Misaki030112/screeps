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
function wantSpawn() {
  const P = M(); if (!P.on) return null; seen();
  if (_.some(Game.creeps, c => c.memory.role === 'reserve7' && (c.spawning || c.ticksToLive > LEAD))) return null;
  const left = (P.endTime || 0) - Game.time;
  const ours = P.by === 'Misaki';
  if (ours ? left < 2500 : left < LEAD) return { role: 'reserve7', body: [CLAIM, CLAIM, MOVE, MOVE], mem: { role: 'reserve7', home: 'W46N8', v2: 1, born: Game.time } };
  return null;
}
function run(c) {
  seen();
  if (c.room.name !== ROOM || !c.pos.isNearTo(CTL[0], CTL[1])) return c.moveTo(new RoomPosition(CTL[0], CTL[1], ROOM), { range: 1, reusePath: 20 });
  const ctl = c.room.controller, res = ctl.reservation;
  if (res && res.username !== c.owner.username) return; // wait: foreign reservation still active (no attackController)
  c.reserveController(ctl);
}
module.exports = { run, wantSpawn, ROOM };
