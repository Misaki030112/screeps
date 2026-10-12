// Spawn priorities: emergency harvester -> 1 miner per source -> haulers -> upgraders -> builders.
function worker(energy) {           // WORK/CARRY/MOVE sets, leftover >=100 adds a WORK
  const parts = []; let e = energy;
  while (e >= 200 && parts.length < 15) { parts.push(WORK, CARRY, MOVE); e -= 200; }
  if (e >= 100 && parts.length && parts.length < 15) parts.unshift(WORK);
  return parts.length ? parts : [WORK, CARRY, MOVE];
}
function miner(energy) {            // up to 5 WORK (saturates a 3000-energy source), 1 MOVE per 2 WORK
  const w = Math.min(5, Math.floor((energy - 50) / 100)); const parts = Array(Math.max(1, w)).fill(WORK);
  const m = Math.max(1, Math.min(3, Math.floor((energy - w * 100) / 50))); return parts.concat(Array(m).fill(MOVE));
}
function hauler(energy) {           // CARRY/MOVE pairs, max 10 pairs
  const n = Math.max(1, Math.min(10, Math.floor(energy / 100))); return Array(n).fill(CARRY).concat(Array(n).fill(MOVE));
}
module.exports = { run(spawn) {
  if (spawn.spawning) return;
  const room = spawn.room, cap = room.energyCapacityAvailable, avail = room.energyAvailable;
  const mine = _.filter(Game.creeps, c => c.room.name === room.name || c.memory.home === room.name);
  const count = _.countBy(mine, c => c.memory.role);
  const sources = room.find(FIND_SOURCES);
  const sites = room.find(FIND_MY_CONSTRUCTION_SITES).length;
  const spawnIt = (body, role, mem = {}) => spawn.spawnCreep(body, role + Game.time, { memory: Object.assign({ role, home: room.name }, mem) });
  // 1) emergency: nothing moves energy to the spawn
  if (!(count.harvester || 0) && !(count.hauler || 0)) return spawnIt(worker(Math.max(200, avail)), 'harvester');
  // 2) one miner per source; pre-spawn the replacement so it arrives as the old one dies
  //    (lead = measured travel time recorded by the miner on arrival + spawn time of the body)
  const lead = c => (c.memory.travel || 100) + c.body.length * 3;
  for (const s of sources) {
    if (!mine.some(c => c.memory.role === 'miner' && c.memory.sourceId === s.id && (c.ticksToLive || 1500) > lead(c))) {
      if (avail < Math.min(cap, 550)) return;
      return spawnIt(miner(Math.min(cap, 550)), 'miner', { sourceId: s.id });
    }
  }
  // haulers scale with the energy backlog sitting in source containers (hauling is the bottleneck while far sources fill up)
  const ctl = room.controller;
  const contBacklog = _.sum(room.find(FIND_STRUCTURES, { filter: s => s.structureType === STRUCTURE_CONTAINER && !(ctl && s.pos.inRangeTo(ctl, 3)) }),
    s => s.store[RESOURCE_ENERGY]);
  const dropBacklog = _.sum(room.find(FIND_DROPPED_RESOURCES, { filter: r => r.resourceType === RESOURCE_ENERGY }), r => r.amount);
  const backlog = contBacklog + dropBacklog;
  // extra upgraders soak up a source-container backlog (energy sink is the bottleneck once spawn/extensions are full)
  // Keep 1 builder when sites=0 for container/road upkeep and so RCL-up tower sites start without waiting a full spawn cycle.
  const T = { hauler: Math.min(6, 2 + Math.floor(backlog / 700)), upgrader: Math.min(6, (sites ? 2 : 4) + Math.floor(backlog / 1500)), builder: sites ? (backlog >= 1500 ? 3 : 2) : 1, harvester: 0 };
  for (const role of ['hauler', 'upgrader', 'builder']) {
    if ((count[role] || 0) < T[role]) {
      const e = role === 'hauler' && !(count.hauler) ? Math.max(200, avail) : cap;
      if (avail < e) return;
      return spawnIt(role === 'hauler' ? hauler(Math.min(e, 600)) : worker(e), role);
    }
  }
} };
