// Cached movement: one PathFinder search per destination, path stored compactly in creep memory
// (one char per tile), re-searched only if the creep leaves the path or is stuck for 2 ticks.
const CM = {};   // heap: roomName -> {t, m}
const enc = p => String.fromCharCode(p.x * 50 + p.y + 192);
function matrix(roomName, avoidCreeps) {
  const room = Game.rooms[roomName]; if (!room) return undefined;
  let e = CM[roomName];
  if (!e || Game.time - e.t > 100 || (e.dirtyAt && Game.time >= e.dirtyAt)) {
    const m = new PathFinder.CostMatrix();
    for (const s of room.find(FIND_STRUCTURES)) {
      if (s.structureType === STRUCTURE_ROAD) { if (m.get(s.pos.x, s.pos.y) === 0) m.set(s.pos.x, s.pos.y, 1); }
      else if (s.structureType !== STRUCTURE_CONTAINER && !(s.structureType === STRUCTURE_RAMPART && s.my)) m.set(s.pos.x, s.pos.y, 255);
    }
    for (const s of room.find(FIND_MY_CONSTRUCTION_SITES))
      if (![STRUCTURE_ROAD, STRUCTURE_CONTAINER, STRUCTURE_RAMPART].includes(s.structureType)) m.set(s.pos.x, s.pos.y, 255);
    // stationary creep tiles are expensive so traffic routes around them
    const P = require('./plan').get(roomName);
    if (P) for (const k of P.standing) { const x = Math.floor(k / 50), y = k % 50; if (m.get(x, y) < 255) m.set(x, y, 20); }
    e = CM[roomName] = { t: Game.time, m };
  }
  if (!avoidCreeps) return e.m;
  const m2 = e.m.clone();
  for (const c of room.find(FIND_CREEPS)) m2.set(c.pos.x, c.pos.y, 255);
  return m2;
}
module.exports = {
  // new sites/structures only appear in find() next tick, so rebuild next tick
  invalidate(roomName) { if (CM[roomName]) CM[roomName].dirtyAt = Game.time + 1; },
  // returns true when in range (arrived)
  to(c, x, y, range = 0) {
    if (Math.max(Math.abs(c.pos.x - x), Math.abs(c.pos.y - y)) <= range) { delete c.memory._m; return true; }
    if (c.fatigue > 0) return false;
    const k = `${x},${y},${range}`;
    let m = c.memory._m;
    const here = enc(c.pos);
    let i = m && m.k === k ? m.p.indexOf(here) : -1;
    if (m && m.k === k && m.l === here) m.s = (m.s || 0) + 1; else if (m) m.s = 0;
    if (!m || m.k !== k || (i < 0 && m.l !== here) || m.s >= 2) {
      const stuck = m && m.s >= 2;
      const r = PathFinder.search(c.pos, { pos: new RoomPosition(x, y, c.room.name), range },
        { plainCost: 2, swampCost: 10, maxRooms: 1, roomCallback: rn => matrix(rn, stuck) });
      m = c.memory._m = { k, p: here + r.path.map(enc).join(''), s: 0 };
      i = 0;
    }
    if (i < 0) i = m.p.indexOf(m.l);
    const nxt = m.p.charCodeAt(i + 1);
    m.l = here;
    if (!nxt) { delete c.memory._m; return false; }
    const v = nxt - 192, nx = Math.floor(v / 50), ny = v % 50;
    c.move(c.pos.getDirectionTo(nx, ny));
    return false;
  },
};
