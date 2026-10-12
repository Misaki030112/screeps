// Places extension sites in a checkerboard ring around the first spawn.
module.exports = { run(room) {
  if (Game.time % 100) return;
  const spawn = room.find(FIND_MY_SPAWNS)[0]; if (!spawn) return;
  const max = CONTROLLER_STRUCTURES[STRUCTURE_EXTENSION][room.controller.level];
  const have = room.find(FIND_MY_STRUCTURES, { filter: { structureType: STRUCTURE_EXTENSION } }).length
    + room.find(FIND_MY_CONSTRUCTION_SITES, { filter: { structureType: STRUCTURE_EXTENSION } }).length;
  let need = max - have;
  for (let r = 2; r < 8 && need > 0; r++)
    for (let dx = -r; dx <= r && need > 0; dx++)
      for (let dy = -r; dy <= r && need > 0; dy++)
        if ((Math.abs(dx) === r || Math.abs(dy) === r) && (dx + dy) % 2 === 0)
          if (room.createConstructionSite(spawn.pos.x + dx, spawn.pos.y + dy, STRUCTURE_EXTENSION) === OK) need--;
} };
