// W47N8 roles (w8miner / w8hauler / w8upgrader / w8builder). Simple, room-local; no safe mode anywhere.
const C = require('./config');
const go = (c, x, y, r = 1) => c.moveTo(new RoomPosition(x, y, C.ROOM), { range: r, reusePath: 10, maxRooms: 1 });
const E = 'energy';
function home(c) { if (c.room.name !== C.ROOM) { c.moveTo(new RoomPosition(C.SPAWN[0], C.SPAWN[1], C.ROOM), { reusePath: 20 }); return false; } return true; }
function getEnergy(c) {
  const drop = c.pos.findClosestByRange(FIND_DROPPED_RESOURCES, { filter: r => r.resourceType === E && r.amount >= 50 });
  const cont = c.pos.findClosestByRange(FIND_STRUCTURES, { filter: s => s.structureType === STRUCTURE_CONTAINER && s.store[E] >= 100
    && !(s.pos.x === C.CTL_CONT[0] && s.pos.y === C.CTL_CONT[1] && c.memory.role === 'w8hauler') });
  const t = [drop, cont].filter(Boolean).sort((a, b) => c.pos.getRangeTo(a) - c.pos.getRangeTo(b))[0];
  if (t) { if (!c.pos.isNearTo(t)) go(c, t.pos.x, t.pos.y); else if (t.amount !== undefined) c.pickup(t); else c.withdraw(t, E); return true; }
  const src = c.pos.findClosestByRange(FIND_SOURCES_ACTIVE);
  if (src && c.getActiveBodyparts(WORK)) { if (!c.pos.isNearTo(src)) go(c, src.pos.x, src.pos.y); else c.harvest(src); return true; }
  return false;
}
function toggle(c) {
  if (c.memory.w && c.store[E] === 0) c.memory.w = false;
  if (!c.memory.w && c.store.getFreeCapacity() === 0) c.memory.w = true;
}
const R = {
  w8miner(c) {
    if (!home(c)) return;
    const S = C.SOURCES[c.memory.si | 0], [x, y] = S.stand;
    const src = Game.rooms[C.ROOM].lookForAt(LOOK_SOURCES, S.src[0], S.src[1])[0];
    if (c.pos.x !== x || c.pos.y !== y) {
      // stand taken (e.g. a cqminer from home still mining): harvest from any tile next to the source
      if (Game.rooms[C.ROOM].lookForAt(LOOK_CREEPS, x, y).length && src) return c.pos.isNearTo(src) ? c.harvest(src) : go(c, src.pos.x, src.pos.y, 1);
      return go(c, x, y, 0);
    }
    const cont = c.pos.lookFor(LOOK_STRUCTURES).find(s => s.structureType === STRUCTURE_CONTAINER);
    if (cont && cont.hits < cont.hitsMax * 0.5 && c.store[E] > 0) return c.repair(cont);
    if (src) c.harvest(src);
  },
  w8hauler(c) {
    if (!home(c)) return; toggle(c);
    if (!c.memory.w) { if (!getEnergy(c) && c.store[E] > 0) c.memory.w = true; return; }
    const t = c.pos.findClosestByRange(FIND_MY_STRUCTURES, { filter: s => (s.structureType === STRUCTURE_SPAWN || s.structureType === STRUCTURE_EXTENSION
      || (s.structureType === STRUCTURE_TOWER && s.store.getFreeCapacity(E) > 200)) && s.store.getFreeCapacity(E) > 0 })
      || (Game.rooms[C.ROOM].lookForAt(LOOK_STRUCTURES, C.CTL_CONT[0], C.CTL_CONT[1]).find(s => s.structureType === STRUCTURE_CONTAINER && s.store.getFreeCapacity(E) > 0))
      || Game.rooms[C.ROOM].storage;
    // nothing to fill: hand it to the emptiest w8upgrader/w8builder; never drop on the ground (Misaki rule), else wait
    const k = t || Game.rooms[C.ROOM].find(FIND_MY_CREEPS, { filter: x => (x.memory.role === 'w8upgrader' || x.memory.role === 'w8builder')
      && x.store.getFreeCapacity(E) > 0 }).sort((a, b) => a.store[E] - b.store[E])[0];
    if (!k) return c.pos.inRangeTo(C.CTL[0], C.CTL[1], 4) || go(c, C.CTL[0], C.CTL[1], 4);
    if (!c.pos.isNearTo(k)) go(c, k.pos.x, k.pos.y); else c.transfer(k, E);
  },
  w8upgrader(c) {
    if (!home(c)) return; toggle(c);
    if (!c.memory.w) { getEnergy(c); return; }
    const ctl = Game.rooms[C.ROOM].controller;
    if (!c.pos.inRangeTo(ctl, 3)) go(c, ctl.pos.x, ctl.pos.y, 3); else c.upgradeController(ctl);
  },
  w8builder(c) {
    if (!home(c)) return; toggle(c);
    if (!c.memory.w) { getEnergy(c); return; }
    const all = c.room.find(FIND_MY_CONSTRUCTION_SITES);
    // north seal walls first (1 energy each, Misaki 17:08), x8-11 before x24-31; then the spawn/extension sites
    const seal = all.filter(s => s.structureType === STRUCTURE_WALL).sort((a, b) => (a.pos.x <= 11 ? 0 : 1) - (b.pos.x <= 11 ? 0 : 1));
    const site = seal[0] || c.pos.findClosestByRange(all);
    if (site) { if (!c.pos.inRangeTo(site, 3)) go(c, site.pos.x, site.pos.y, 3); else c.build(site); return; }
    const rep = c.pos.findClosestByRange(FIND_STRUCTURES, { filter: s => (s.structureType === STRUCTURE_CONTAINER || s.structureType === STRUCTURE_ROAD) && s.hits < s.hitsMax * 0.6 });
    if (rep) { if (!c.pos.inRangeTo(rep, 3)) go(c, rep.pos.x, rep.pos.y, 3); else c.repair(rep); return; }
    R.w8upgrader(c);
  },
};
// main.js dispatches roles[role].run(c): wrap (bare functions crashed every w8 creep with 'run is not a function')
module.exports = Object.fromEntries(Object.entries(R).map(([k, f]) => [k, { run: f }]));
