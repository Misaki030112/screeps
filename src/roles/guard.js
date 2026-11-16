// Home guard (docs/DEFENSE.md "Home defense"): ranged defender spawned while player combat creeps are in W46N8.
// Never leaves the room; fights only inside tower cover (<= SAFE of a tower); focuses the towers' target (healer first);
// kites melee; retreats to the spawn below 60% hp (towers heal it); recycles 100 ticks after the room is clear.
const move = require('../utils/move'), H = require('../managers/home'), F = require('../utils/focus');
const SAFE = 15;
module.exports = { run(c) {
  if (require('../utils/cmd').yieldCreep(c)) return; // Memory.cmd off => one check (docs/COMMANDER.md)
  if (require('../managers/boost').hold(c)) return;
  const room = c.room, home = Game.rooms[c.memory.home];
  if (c.hits < c.hitsMax) c.heal(c);
  if (room.name !== c.memory.home) { const sp = home && home.find(FIND_MY_SPAWNS)[0]; return require('../utils/military').moveTo(c, sp ? sp.pos : new RoomPosition(25, 25, c.memory.home), { range: 2 }); }
  const hs = H.hostiles(room), towers = room.find(FIND_MY_STRUCTURES).filter(s => s.structureType === STRUCTURE_TOWER);
  const sp = room.find(FIND_MY_SPAWNS)[0];
  if (hs.length) c.memory.lastSeen = Game.time;
  if (c.hits < c.hitsMax * 0.6) c.memory.hurt = true; else if (c.hits >= c.hitsMax * 0.95) c.memory.hurt = false;
  const covered = p => towers.some(t => t.pos.inRangeTo(p, SAFE));
  // target: towers' focus if in reach, else best focus pick among creeps within range 3
  let t = room.memory.focus && Game.getObjectById(room.memory.focus);
  const inR = hs.filter(h => c.pos.inRangeTo(h, 3));
  if (!t || !c.pos.inRangeTo(t, 3)) { const p = F.pick(towers.map(x => ({ pos: x.pos, energy: x.store[RESOURCE_ENERGY] })), inR); t = p ? p.h : c.pos.findClosestByRange(inR); }
  if (t && c.pos.inRangeTo(t, 3)) { if (inR.length >= 3 && inR.some(h => c.pos.inRangeTo(h, 1))) c.rangedMassAttack(); else c.rangedAttack(t); }
  if (c.memory.hurt) return sp && move.to(c, sp.pos.x, sp.pos.y, 1);
  // Threat already gone at birth, or cleared: stay for the full TTL. Do not recycle early.
  if (!hs.length) return sp && move.to(c, sp.pos.x, sp.pos.y, 3);
  const melee = hs.find(h => h.body.some(p => p.type === ATTACK && p.hits > 0) && c.pos.inRangeTo(h, 2));
  if (melee) {
    const r = PathFinder.search(c.pos, { pos: melee.pos, range: 3 }, { flee: true, maxRooms: 1 });
    if (r.path.length) {
      require('../utils/military').pullSwap(c, r.path[0].x, r.path[0].y);
      return c.move(c.pos.getDirectionTo(r.path[0]));
    }
  }
  // approach the chosen target only while staying in tower cover and off the exit strip
  const goal = (room.memory.focus && Game.getObjectById(room.memory.focus)) || c.pos.findClosestByRange(hs);
  if (goal && !c.pos.inRangeTo(goal, 3) && covered(goal.pos) && goal.pos.x > 2 && goal.pos.x < 47 && goal.pos.y > 2 && goal.pos.y < 47) return require('../utils/military').moveTo(c, goal, { range: 3, maxRooms: 1 });
  if (!covered(c.pos) && sp) return move.to(c, sp.pos.x, sp.pos.y, 3);
} };
