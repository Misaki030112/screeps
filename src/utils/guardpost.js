// Idle remote defender: a guard post off the haul lanes + a slow wander around it (W47N7 2026-10-31, Misaki:
// "rdef83982033 能不能别挡路，在这种位置驻守呢 27,19 ?? 并且有点活人感，四处巡逻"). rdef83982033 killed the Invader at
// 19,2 and then held the kill spot (memory.lk) forever at 18,1 — the tile next to the only exit 18,0, on the rhauler lane.
// Rules: never stop on a road / container / structure, next to a source, mineral, controller or container (miners and
// haulers work there), or within 1 of the room border (exit lanes). Swamp is avoided for stops (slow, looks stuck).
// Post per room: Memory.remote[r].post = [x, y] (no redeploy) > CFG/GUARD `post` > the room centre 25,25; if the wanted
// tile is not ok, the nearest ok tile. CPU: one bad-tile set per room per 100 ticks (heap), one move.to per idle tick.
const PATROL_R = 6, PAUSE = [6, 18], GIVEUP = 30;
const SETS = {}; // heap: room -> { t, bad:Set }
function badSet(room) {
  const e = SETS[room.name];
  if (e && Game.time - e.t < 100) return e.bad;
  const bad = new Set(), near = (x, y) => { for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) bad.add((x + dx) * 50 + y + dy); };
  for (const s of room.find(FIND_STRUCTURES) || []) {
    bad.add(s.pos.x * 50 + s.pos.y);
    if (s.structureType === STRUCTURE_CONTAINER || s.structureType === STRUCTURE_CONTROLLER) near(s.pos.x, s.pos.y);
  }
  for (const s of room.find(FIND_SOURCES) || []) near(s.pos.x, s.pos.y);
  for (const s of room.find(FIND_MINERALS) || []) near(s.pos.x, s.pos.y);
  for (const s of room.find(FIND_CONSTRUCTION_SITES) || []) bad.add(s.pos.x * 50 + s.pos.y);
  if (room.controller) near(room.controller.pos.x, room.controller.pos.y);
  SETS[room.name] = { t: Game.time, bad };
  return bad;
}
// pure: ok(x, y, terrainGet, bad) — a tile the idle defender may stop on
function ok(x, y, tget, bad) {
  return x >= 2 && x <= 47 && y >= 2 && y <= 47 && tget(x, y) === 0 && !bad.has(x * 50 + y);
}
// pure: nearest ok tile to [x, y] (itself first), ring search up to 12
function nearestOk(x, y, tget, bad) {
  if (ok(x, y, tget, bad)) return [x, y];
  for (let r = 1; r <= 12; r++) {
    let best = null, bd = 1e9;
    for (let dx = -r; dx <= r; dx++) for (let dy = -r; dy <= r; dy++) {
      if (Math.max(Math.abs(dx), Math.abs(dy)) !== r || !ok(x + dx, y + dy, tget, bad)) continue;
      const d = dx * dx + dy * dy; if (d < bd) { bd = d; best = [x + dx, y + dy]; }
    }
    if (best) return best;
  }
  return null;
}
// pure: random ok tile within R of post (rnd() in [0,1)), else the post
function waypoint(post, tget, bad, rnd, R = PATROL_R) {
  for (let i = 0; i < 12; i++) {
    const x = post[0] + Math.round((rnd() * 2 - 1) * R), y = post[1] + Math.round((rnd() * 2 - 1) * R);
    if (ok(x, y, tget, bad)) return [x, y];
  }
  return post;
}
function postFor(room, C) {
  const m = ((Memory.remote || {})[room.name] || {}).post;
  const want = (Array.isArray(m) && m.length === 2 && m) || (C && C.post) || [25, 25];
  const T = room.getTerrain(), tget = (x, y) => T.get(x, y);
  return nearestOk(want[0], want[1], tget, badSet(room)) || want;
}
const enc = (x, y) => String.fromCharCode(x * 50 + y + 192);
// an adjacent creep of ours whose cached path steps onto our tile next
function wanted(c) {
  const me = enc(c.pos.x, c.pos.y);
  return (c.pos.findInRange ? c.pos.findInRange(FIND_MY_CREEPS, 1) : []).some(o => {
    if (o === c || !o.memory || !o.memory._m || !o.memory._m.p) return false;
    const p = o.memory._m.p, i = p.indexOf(enc(o.pos.x, o.pos.y)); return i >= 0 && p[i + 1] === me;
  });
}
// hold [x, y] (e.g. the kill spot) but on the nearest ok tile; returns nothing
function hold(c, x, y, move) {
  const T = c.room.getTerrain(), tget = (a, b) => T.get(a, b), bad = badSet(c.room);
  const p = nearestOk(x, y, tget, bad) || [x, y];
  if (c.pos.x === p[0] && c.pos.y === p[1] && !wanted(c)) return;
  if (c.pos.x === p[0] && c.pos.y === p[1]) { const w = waypoint(p, tget, bad, Math.random, 2); return move.to(c, w[0], w[1], 0); }
  return move.to(c, p[0], p[1], 0);
}
// wander between ok tiles around the post with pauses. memory.gp = { x, y, u (deadline / pause end), a (arrived) }
function patrol(c, C, move) {
  const T = c.room.getTerrain(), tget = (a, b) => T.get(a, b), bad = badSet(c.room), post = postFor(c.room, C);
  let g = c.memory.gp;
  const at = g && c.pos.x === g.x && c.pos.y === g.y;
  if (!g || g.r !== c.room.name || Game.time >= g.u || (at && wanted(c))) {
    const w = (g || !ok(c.pos.x, c.pos.y, tget, bad)) ? waypoint(post, tget, bad, Math.random) : post;
    g = c.memory.gp = { x: w[0], y: w[1], r: c.room.name, u: Game.time + GIVEUP };
  }
  if (c.pos.x === g.x && c.pos.y === g.y) {
    if (!g.a) { g.a = 1; g.u = Game.time + PAUSE[0] + Math.floor(Math.random() * (PAUSE[1] - PAUSE[0])); }
    return;
  }
  // waypoint taken by another creep: pick another one now
  if (Math.max(Math.abs(c.pos.x - g.x), Math.abs(c.pos.y - g.y)) === 1 && (c.room.lookForAt(LOOK_CREEPS, g.x, g.y) || []).length) { g.u = Game.time; return; }
  move.to(c, g.x, g.y, 0);
}
module.exports = { ok, nearestOk, waypoint, postFor, badSet, hold, patrol, PATROL_R };
