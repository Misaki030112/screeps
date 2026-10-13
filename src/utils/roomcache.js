// Per-room structure cache refreshed every 20 ticks (or when invalidated). Roles read ids from here instead of find().
const C = {};
module.exports = {
  invalidate(name) { if (C[name]) C[name].t = Math.min(C[name].t, Game.time + 1 - 20); }, // rebuild next tick
  get(room) {
    let c = C[room.name];
    if (!c || Game.time - c.t >= 20) {
      const by = {};
      for (const s of room.find(FIND_STRUCTURES)) (by[s.structureType] || (by[s.structureType] = [])).push(s.id);
      const at = {};
      for (const t in by) for (const id of by[t]) { const s = Game.getObjectById(id); at[s.pos.x * 50 + s.pos.y] = at[s.pos.x * 50 + s.pos.y] || {}; at[s.pos.x * 50 + s.pos.y][t] = id; }
      c = C[room.name] = { t: Game.time, by, at, sites: room.find(FIND_MY_CONSTRUCTION_SITES).map(s => s.id) };
    }
    return c;
  },
  // structure of type at (x,y) or null
  at(room, x, y, type) { const c = this.get(room); const e = c.at[x * 50 + y]; return e && e[type] ? Game.getObjectById(e[type]) : null; },
  all(room, type) { return (this.get(room).by[type] || []).map(id => Game.getObjectById(id)).filter(Boolean); },
  sites(room) { return this.get(room).sites.map(id => Game.getObjectById(id)).filter(Boolean); },
};
