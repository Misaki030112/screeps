// Wall policy v4 phase (docs/DEFENSE_PLAN.md, layout.defense.policy.start; docs/RCL6.md R4). Single source of the wall phase:
//   off   rcl < 6 or no storage
//   bank  rcl >= 6, walls not started: spawn holds ONE upgrader so storage can reach START (storage never exceeded 2.3k
//         under supply-follows-demand, so `storage>=20000` was unreachable as written). ~11 e/t banked -> 20k in ~2k ticks.
//   build latched in room.memory.walls.started once storage >= START with no threat (or early: after novice end a hostile
//         PLAYER combat creep in the home room). Latched so a later dip below START never re-banks.
// Gate/wall sites + the hits-step budget read phase()==='build' (next roadmap step).
const START = 20000, NOVICE_END = Date.UTC(2026, 9, 27, 19, 33); // 2026-10-28 03:33 UTC+8
const COMBAT = ['attack', 'ranged_attack', 'work', 'claim'];
function playerCombat(room) {
  return room.find(FIND_HOSTILE_CREEPS).some(h => h.owner.username !== 'Invader' && h.body.some(p => COMBAT.includes(p.type) && p.hits > 0));
}
function phase(room) {
  const m = room.memory.walls;
  if (m && m.started) return 'build';
  if (room.controller.level < 6 || !room.storage) return 'off';
  const calm = !require('./threat').holding(room.name) && !room.find(FIND_HOSTILE_CREEPS).length;
  const early = Date.now() >= NOVICE_END && playerCombat(room);
  if ((room.storage.store[RESOURCE_ENERGY] >= START && calm) || early) {
    room.memory.walls = { started: Game.time, why: early ? 'player' : 'bank' };
    console.log(`WALLS start ${room.name} t=${Game.time} why=${room.memory.walls.why}`);
    return 'build';
  }
  return 'bank';
}
module.exports = { START, NOVICE_END, phase };
