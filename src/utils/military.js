// Military movement. Combat creeps recalculate a path every call. Nothing is read back from
// creep.memory._move (engine moveTo cache) or creep.memory._m (utils/move cache).
// A friendly civilian on the next tile is told to swap. The civilian's own move is replaced
// at the end of the tick (flush), and also at the start of its turn if the demand is already set.
// Military vs military is not forced: those creeps keep their own traffic rules.
const ROLES = {
  guard: 1, defender: 1,
  w8defender: 1, w8guard: 1, w8healer: 1,
  raid9: 1, cqsquad: 1, cqbreaker: 1, cqatk: 1, cqquad: 1,
};
function isMilitary(c) {
  const role = typeof c === 'string' ? c : c && c.memory && c.memory.role;
  return !!ROLES[role];
}
function fresh(c) {
  if (c && c.memory) { delete c.memory._move; delete c.memory._m; }
}
const DEMAND = { t: -1, map: {} };
function reset() {
  const t = typeof Game === 'undefined' ? 0 : Game.time;
  if (DEMAND.t !== t) { DEMAND.t = t; DEMAND.map = {}; }
}
// Ask a civilian to stand on (x, y) — the military creep's current tile — this tick.
function demandSwap(civ, x, y) {
  reset();
  if (!civ || !civ.my || civ.spawning || isMilitary(civ)) return false;
  const name = civ.name || civ.id;
  if (!name) return false;
  DEMAND.map[name] = { x, y, room: civ.room && civ.room.name, id: civ.id };
  return true;
}
function pullSwap(c, nx, ny) {
  reset();
  if (!c || !c.room || c.fatigue || nx == null || ny == null) return false;
  if (!c.room.lookForAt || typeof LOOK_CREEPS === 'undefined') return false;
  const list = c.room.lookForAt(LOOK_CREEPS, nx, ny) || [];
  const b = list[0];
  if (!b || b === c) return false;
  return demandSwap(b, c.pos.x, c.pos.y);
}
function issue(c, d) {
  if (!c || c.spawning || c.fatigue || !c.pos || !c.pos.getDirectionTo) return false;
  if (d.room && c.room && c.room.name !== d.room) return false;
  const dir = c.pos.getDirectionTo(d.x, d.y);
  if (!dir) return false;
  c.move(dir);
  return true;
}
// Civilian start-of-turn: a demand already recorded (military ran first) replaces this creep's move.
function block(c) {
  reset();
  if (!c || !c.name || isMilitary(c)) return false;
  const d = DEMAND.map[c.name];
  if (!d) return false;
  return issue(c, d);
}
// After every creep has run. Last move() wins, so a civilian that already pathed is pulled back.
function flush() {
  reset();
  if (typeof Game === 'undefined' || !Game.creeps) return;
  for (const name in DEMAND.map) {
    const d = DEMAND.map[name];
    const c = Game.creeps[name] || (d.id && Game.getObjectById && Game.getObjectById(d.id));
    if (!c || isMilitary(c)) continue;
    issue(c, d);
  }
}
// Fresh in-room step. Returns 'there' | 'moved' | 'wait' | 'no'.
// Does not store the path. An incomplete search is not followed (moveTo's nearest-tile fallback
// walked guards into the walled pocket).
function step(c, x, y, range, roomCallback) {
  fresh(c);
  const r = range || 0;
  if (!c || !c.pos) return 'no';
  if (Math.max(Math.abs(c.pos.x - x), Math.abs(c.pos.y - y)) <= r) return 'there';
  if (c.fatigue > 0) return 'wait';
  if (typeof PathFinder === 'undefined' || !PathFinder.search || typeof RoomPosition === 'undefined') return 'no';
  const res = PathFinder.search(c.pos, { pos: new RoomPosition(x, y, c.room.name), range: r }, {
    plainCost: 2, swampCost: 10, maxRooms: 1, maxOps: 2000,
    roomCallback: roomCallback || (rn => {
      try { return require('./move').matrix(rn, false); } catch (e) { return undefined; }
    }),
  });
  let n = res && res.path && res.path.length ? res.path[0] : null;
  // One tile out of range and the search gave nothing: step straight. This is geometry, not a cache.
  // An incomplete search that still returned a first step is followed; we do not jump to the
  // tile nearest the goal by range (that walked guards into the walled pocket).
  if (!n) {
    const dist = Math.max(Math.abs(c.pos.x - x), Math.abs(c.pos.y - y));
    if (dist - r !== 1 || !c.pos.getDirectionTo) return 'no';
    const dir0 = c.pos.getDirectionTo(x, y);
    const D = { 1: [0, -1], 2: [1, -1], 3: [1, 0], 4: [1, 1], 5: [0, 1], 6: [-1, 1], 7: [-1, 0], 8: [-1, -1] }[dir0];
    if (!D) return 'no';
    const nx = c.pos.x + D[0], ny = c.pos.y + D[1];
    if (nx <= 0 || ny <= 0 || nx >= 49 || ny >= 49) return 'no';
    let wall = false;
    try { wall = c.room.getTerrain().get(nx, ny) === (typeof TERRAIN_MASK_WALL !== 'undefined' ? TERRAIN_MASK_WALL : 1); } catch (e) { wall = false; }
    if (wall) return 'no';
    n = { x: nx, y: ny };
  }
  pullSwap(c, n.x, n.y);
  const dir = c.pos.getDirectionTo(n.x, n.y);
  if (dir) c.move(dir);
  return 'moved';
}
function posOf(target) {
  if (!target) return null;
  if (target.pos && target.pos.x != null) return { x: target.pos.x, y: target.pos.y, room: target.pos.roomName || (target.room && target.room.name) };
  if (target.x != null && target.y != null) return { x: target.x, y: target.y, room: target.roomName };
  return null;
}
// Same-room goals go through step() so a civilian on the next tile is swapped.
// Cross-room goals use the engine moveTo with the cache wiped and reusePath 0.
function moveTo(c, target, opts) {
  fresh(c);
  const o = Object.assign({}, opts || {});
  o.reusePath = 0;
  const p = posOf(target);
  const here = c && c.room && c.room.name;
  if (p && here && (!p.room || p.room === here) && typeof PathFinder !== 'undefined') {
    const cb = o.costCallback;
    const st = step(c, p.x, p.y, o.range == null ? 1 : o.range, cb ? (rn => {
      const m = typeof PathFinder.CostMatrix === 'function' ? new PathFinder.CostMatrix() : undefined;
      return cb(rn, m) || m;
    }) : undefined);
    if (st !== 'no') return typeof OK !== 'undefined' ? OK : 0;
  }
  return c.moveTo ? c.moveTo(target, o) : undefined;
}
module.exports = { ROLES, isMilitary, fresh, demandSwap, pullSwap, block, flush, step, moveTo, _demand: DEMAND };
