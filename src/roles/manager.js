// Manager (RCL5+ once storage + hub link exist): stands on the hub tile (36,30) and never moves.
// Hub link -> storage; storage -> tower / hub extensions / spawn3 / hub link (for filler links); terminal later.
const plan = require('../utils/plan'), move = require('../utils/move'), rc = require('../utils/roomcache');
const N8 = [[-1, -1], [0, -1], [1, -1], [-1, 0], [1, 0], [-1, 1], [0, 1], [1, 1]];
function pickFill(c, room) {
  const list = c.memory.n.fill.map(id => Game.getObjectById(id)).filter(s => s && s.store && s.store.getFreeCapacity(RESOURCE_ENERGY) > 0);
  let alert = false;
  try { alert = require('./queen').defenseFill(room); } catch (e) { alert = false; }
  if (!alert || list.length < 2) return list[0];
  const short = room.energyAvailable < room.energyCapacityAvailable;
  const rank = require('../utils/squad').fillRank;
  list.sort((a, b) => rank(true, short, a.structureType) - rank(true, short, b.structureType));
  return list[0];
}
module.exports = { run(c) {
  if (require('../utils/cmd').yieldCreep(c)) return;
  const room = c.room, P = plan.get(room.name), [x, y] = P.pos.manager;
  if (!move.to(c, x, y, 0)) return;
  if (!c.memory.n || Game.time % 200 === 0) {
    const n = { fill: [], link: null };
    for (const [dx, dy] of N8) { const e = rc.get(room).at[(x + dx) * 50 + y + dy]; if (!e) continue;
      for (const t in e) { if (t === 'extension' || t === 'spawn' || t === 'tower' || t === 'powerSpawn') n.fill.push(e[t]); if (t === 'link') n.link = e[t]; } }
    c.memory.n = n;
  }
  const st = room.storage; if (!st) return;
  const link = c.memory.n.link && Game.getObjectById(c.memory.n.link);
  if (c.store[RESOURCE_ENERGY] > 0) {
    const t = pickFill(c, room);
    if (t) { c.transfer(t, RESOURCE_ENERGY); return; }
    if (link && room.memory.linkWant && link.store.getFreeCapacity(RESOURCE_ENERGY) > 0) { c.transfer(link, RESOURCE_ENERGY); return; }
    c.transfer(st, RESOURCE_ENERGY); return;
  }
  if (link && link.store[RESOURCE_ENERGY] > 0 && !room.memory.linkWant) { c.withdraw(link, RESOURCE_ENERGY); return; }
  const need = c.memory.n.fill.some(id => { const s = Game.getObjectById(id); return s && s.store.getFreeCapacity(RESOURCE_ENERGY) > 0; });
  if ((need || room.memory.linkWant) && st.store[RESOURCE_ENERGY] > 0) c.withdraw(st, RESOURCE_ENERGY);
} };
