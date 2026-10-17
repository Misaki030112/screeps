// Movement (simple by design): one cached path per creep+target, serialized one char per tile in memory (_m).
// Fallback ladder when the creep does not change position (fatigue excluded):
//   stuck 2  -> repath once treating creeps as obstacles (kept only if not much costlier than the blocked path;
//               an INCOMPLETE creep-avoiding path = goal walled in by creeps -> keep the old path and swap at stuck 4.
//               10-16: W45N7 rminer orbited 700t around 4 rhaulers boxing in the container, never reaching s=4)
//   stuck 4  -> swap with / push our own non-stationary blocker
//   stuck 8  -> step to any free neighbour tile, repath (reported to trace)
//   stuck 30 -> console "STUCK" report once (box audit flags it). No automatic recycling.
// Paths are invalidated only when the room's structure/site set changes (version bump) — no timed expiry.
// Cheap shortcuts (no PathFinder): one step from the goal range -> step straight at it if the tile is passable;
// range-0 goal held by our own stationary creep (old miner/upgrader before it dies) -> wait adjacent, no repath/shove.
// Every search is traced with a reason: n=new target, v=version bump, o=off path, s=stuck2, x=stuck8, z=stuck30.
const CM = {};   // heap: roomName -> {v, m}
const VER = {};  // heap: roomName -> {v, n}  structure+site count signature
const enc = p => String.fromCharCode(p.x * 50 + p.y + 192);
const dec = ch => { const v = ch - 192; return [Math.floor(v / 50), v % 50]; };
const trace = require('./trace');
const OPP = { 1: 5, 2: 6, 3: 7, 4: 8, 5: 1, 6: 2, 7: 3, 8: 4 };
const DXY = { 1: [0, -1], 2: [1, -1], 3: [1, 0], 4: [1, 1], 5: [0, 1], 6: [-1, 1], 7: [-1, 0], 8: [-1, -1] };
function version(room) {
  let e = VER[room.name];
  if (!e || e.t !== Game.time) {
    const n = room.find(FIND_STRUCTURES).length * 1000 + room.find(FIND_CONSTRUCTION_SITES).length;
    if (!e) e = VER[room.name] = { v: 1, n, t: Game.time }; else { if (e.n !== n) { e.v++; e.n = n; } e.t = Game.time; }
  }
  return e.v;
}
function matrix(roomName, avoidCreeps) {
  const room = Game.rooms[roomName]; if (!room) return undefined;
  const v = version(room);
  let e = CM[roomName];
  if (!e || e.v !== v) {
    const m = new PathFinder.CostMatrix();
    for (const s of room.find(FIND_STRUCTURES)) {
      if (s.structureType === STRUCTURE_ROAD) { if (m.get(s.pos.x, s.pos.y) === 0) m.set(s.pos.x, s.pos.y, 1); }
      else if (s.structureType !== STRUCTURE_CONTAINER && !(s.structureType === STRUCTURE_RAMPART && (s.my || s.isPublic))) m.set(s.pos.x, s.pos.y, 255);
    }
    // foreign construction sites are trampled (destroyed) when stepped on: never path over them (W45N7 22,15 BustJetter's container)
    for (const s of room.find(FIND_HOSTILE_CONSTRUCTION_SITES)) m.set(s.pos.x, s.pos.y, 255);
    for (const s of room.find(FIND_MY_CONSTRUCTION_SITES))
      if (![STRUCTURE_ROAD, STRUCTURE_CONTAINER, STRUCTURE_RAMPART].includes(s.structureType)) m.set(s.pos.x, s.pos.y, 255);
    // fixed spots (fillers/miners/upgraders/manager) are expensive so traffic yields to them
    const P = require('./plan').get(roomName);
    if (P) for (const k of P.standing) { const x = Math.floor(k / 50), y = k % 50; if (m.get(x, y) < 255) m.set(x, y, 20); }
    // v5: exit tiles cost 50 so a ranged goal (repair range 3) never ends ON an exit (live 03:00: builder repairing NE wall 47,11
    // from 49,14 = W45N8 exit -> gets bounced into W45N8 and back). Range-0 exit walks (hop) still reach them.
    for (let i = 0; i < 50; i++) for (const [x, y] of [[0, i], [49, i], [i, 0], [i, 49]]) if (m.get(x, y) < 50) m.set(x, y, 50);
    e = CM[roomName] = { v, m };
  }
  if (!avoidCreeps) return e.m;
  const m2 = e.m.clone();
  for (const c of room.find(FIND_CREEPS)) m2.set(c.pos.x, c.pos.y, 255);
  return m2;
}
function search(c, x, y, range, avoid, why) {
  const r = PathFinder.search(c.pos, { pos: new RoomPosition(x, y, c.room.name), range },
    { plainCost: 2, swampCost: 10, maxRooms: 1, maxOps: 2000, roomCallback: rn => matrix(rn, avoid) });
  trace.repath(c, why);
  return [enc(c.pos) + r.path.map(enc).join(''), r.incomplete ? Infinity : r.cost];
}
// cost of the rest of a cached path (same costs as search, creeps ignored)
function restCost(room, p, i) {
  const m = matrix(room.name, false), T = room.getTerrain(); let cost = 0;
  for (let j = i + 1; j < p.length; j++) { const [x, y] = dec(p.charCodeAt(j)); cost += (m && m.get(x, y)) || (T.get(x, y) & TERRAIN_MASK_SWAMP ? 10 : 2); }
  return cost;
}
const DETOUR = 12; // stuck-2 path may cost at most this much more than the blocked rest; else wait for the stuck-4 swap
function stationary(o) { const P = require('./plan').get(o.room.name); return !!(P && P.standing.has(o.pos.x * 50 + o.pos.y)) && ['miner', 'filler', 'manager', 'upgrader', 'rminer'].includes(o.memory && o.memory.role); }
// costCallback for raw creep.moveTo calls (defender etc.): same foreign-site protection
function foreignSites(rn, m) { const room = Game.rooms[rn]; if (room) for (const s of room.find(FIND_HOSTILE_CONSTRUCTION_SITES)) m.set(s.pos.x, s.pos.y, 255); return m; }
module.exports = {
  foreignSites,
  invalidate(roomName) { const e = VER[roomName]; if (e) e.n = -1; },
  // returns true when in range (arrived)
  to(c, x, y, range = 0) {
    const k = `${x},${y},${range}`;
    let m = c.memory._m;
    if (Math.max(Math.abs(c.pos.x - x), Math.abs(c.pos.y - y)) <= range) {
      if (m && m.k === k && m.t0 !== undefined) trace.arrive(c, k, m.n, Game.time - m.t0);
      delete c.memory._m; return true;
    }
    if (c.fatigue > 0) return false;
    const dist = Math.max(Math.abs(c.pos.x - x), Math.abs(c.pos.y - y));
    if (range === 0 && dist === 1) { // goal tile held by our own stationary creep: wait here (it will die/leave)
      const b = c.room.lookForAt(LOOK_CREEPS, x, y)[0];
      if (b && b.my && stationary(b)) { if (m && m.k === k) { m.s = 0; m.l = enc(c.pos); } return false; }
    }
    const here = enc(c.pos), v = version(c.room);
    if (m && m.k === k) m.s = m.l === here ? (m.s || 0) + 1 : 0;
    const s = m && m.k === k ? m.s : 0;
    let i = m && m.k === k ? m.p.indexOf(here) : -1;
    if (!m || m.k !== k || m.v !== v || (i < 0 && m.l !== here) || s === 2 || s === 8 || s >= 30 && s % 30 === 0) {
      const keep = m && m.k === k ? m : null;
      const why = !keep ? 'n' : s === 2 ? 's' : s === 8 ? 'x' : s >= 30 ? 'z' : m.v !== v ? 'v' : 'o';
      if (s === 8) { trace.stuck(c); const d = 1 + (Game.time % 8); c.move(d); }
      if (s === 30) console.log(`STUCK ${c.name} ${c.memory.role} ${c.room.name} ${c.pos.x},${c.pos.y} -> ${k}`);
      let p = null;
      if (why === 'n' && dist - range === 1) { // one step away: straight step if passable (no search)
        const dir = c.pos.getDirectionTo(x, y), D = DXY[dir], nx = c.pos.x + D[0], ny = c.pos.y + D[1];
        const cm = matrix(c.room.name, false);
        if (nx > 0 && nx < 49 && ny > 0 && ny < 49 && c.room.getTerrain().get(nx, ny) !== TERRAIN_MASK_WALL && (!cm || cm.get(nx, ny) < 255))
          p = here + enc({ x: nx, y: ny });
      }
      let cost = 0;
      if (!p) [p, cost] = search(c, x, y, range, s >= 2, why);
      // A creep parked on the trunk (builder on 37,32) made the stuck-2 path a ~50-tick swamp detour that stayed cached
      // for the whole trip (patrol 10-15 02:53). Keep the old path instead; stuck 4 swaps/pushes our own blocker.
      if (why === 's' && i >= 0 && cost > restCost(c.room, keep.p, i) + DETOUR) { keep.l = here; return false; }
      m = c.memory._m = { k, p, s, v, n: keep ? keep.n : undefined, t0: keep ? keep.t0 : Game.time };
      if (m.n === undefined) m.n = m.p.length - 1;
      if (s === 8) { m.l = here; return false; }
      i = 0;
    }
    if (i < 0) i = m.p.indexOf(m.l);
    const nxt = m.p.charCodeAt(i + 1);
    m.l = here;
    if (!nxt) { delete c.memory._m; return false; }
    const [nx, ny] = dec(nxt), dir = c.pos.getDirectionTo(nx, ny);
    if (s >= 4 && s < 8) { // swap with our own moving creep
      const b = c.room.lookForAt(LOOK_CREEPS, nx, ny)[0];
      if (b && b.my && !stationary(b) && !b.fatigue) b.move(OPP[dir]);
    }
    c.move(dir);
    return false;
  },
};
