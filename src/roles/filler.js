// Filler (RCL5+): stands forever on a fixed stamp tile; takes from the stamp's centre link / container and fills
// its fixed neighbours. Idle (no intents) while the room is full.
const plan = require('../utils/plan'), move = require('../utils/move'), rc = require('../utils/roomcache');
const N8 = [[-1, -1], [0, -1], [1, -1], [-1, 0], [1, 0], [-1, 1], [0, 1], [1, 1]];
module.exports = { run(c) {
  if (require('../utils/cmd').yieldCreep(c)) return;
  const room = c.room, [x, y] = c.memory.spot;
  if (!move.to(c, x, y, 0)) return;
  if (!c.memory.n || Game.time % 200 === 0) {
    const n = { fill: [], src: [] };
    for (const [dx, dy] of N8) {
      const e = rc.get(room).at[(x + dx) * 50 + y + dy]; if (!e) continue;
      for (const t in e) { if (t === 'extension' || t === 'spawn' || t === 'tower') n.fill.push(e[t]); if (t === 'link' || t === 'container') n.src.push(e[t]); }
    }
    c.memory.n = n;
  }
  if (room.energyAvailable === room.energyCapacityAvailable && c.store.getFreeCapacity() === 0) return;
  const tgt = c.memory.n.fill.map(id => Game.getObjectById(id)).find(s => s && s.store.getFreeCapacity(RESOURCE_ENERGY) > 0);
  if (tgt && c.store[RESOURCE_ENERGY] > 0) { c.transfer(tgt, RESOURCE_ENERGY); return; }
  if (c.store.getFreeCapacity() > 0) { const s = c.memory.n.src.map(id => Game.getObjectById(id)).find(s => s && s.store[RESOURCE_ENERGY] > 0); if (s) c.withdraw(s, RESOURCE_ENERGY); }
} };
