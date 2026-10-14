// Kiting vs a chasing melee NPC (docs/DEFENDER.md). Pure terrain math, no game state besides positions/fatigue.
// Small Invaders and our defender both move 1 tile/tick on plain and are stuck ~5 ticks on a swamp tile, so plain range is the
// wrong metric (2026-10-15: kited into swamp / the walled west-exit pocket and got caught). Time model (tick starts):
//   adj(m)   = first tick start at which the Invader can stand next to m (Dijkstra from it; leaving a swamp tile costs 5)
//   we sit on m for `dwell` tick starts (stay/plain 1, swamp 5); safe(m) = adj(m) > last tick we are on m (melee hits on tick start)
//   room(n)  = tiles reachable from n through safe tiles only (escape room; a dead end or swamp lock -> small)
//   a plain tile next to our exit tile counts as full room: one step leaves the room and NPCs never follow. In a walled exit
//   pocket (W45N8 west exit) we therefore fight next to the exit and leave when hurt instead of fleeing deeper into swamp.
// engage: among steps with enough room prefer range 3 to the target (shoot, never melee).
// flee: among steps with enough room the one closest (path ticks) to our exit, so a chaser behind us is outrun toward home;
//   if none has enough room, maximize room.
const D9 = [[0, 0], [0, -1], [1, -1], [1, 0], [1, 1], [0, 1], [-1, 1], [-1, 0], [-1, -1]];
const ROOM_OK = 25, ROOM_MAX = 60, MAX_T = 14; // "enough room" tiles; cap; search horizon in ticks
// bucket Dijkstra over tick costs: L[k] = tick we can leave k (entering costs its dwell), A[k] = tick start we arrive (d0 tile: 0)
function dijkstra(T, x0, y0, d0, ok, max = MAX_T) {
  const L = new Int16Array(2500).fill(32767), A = new Int16Array(2500).fill(32767), B = [], k0 = x0 * 50 + y0; let n = 0;
  L[k0] = d0; A[k0] = 0; B[d0] = [k0];
  for (let d = d0; d < B.length && d <= max; d++) for (const k of B[d] || []) {
    if (L[k] !== d) continue; n++; const x = (k / 50) | 0, y = k % 50;
    for (let i = 1; i <= 8; i++) { const nx = x + D9[i][0], ny = y + D9[i][1]; if (nx < 1 || ny < 1 || nx > 48 || ny > 48) continue;
      const tt = T.get(nx, ny); if (tt & TERRAIN_MASK_WALL) continue;
      const nk = nx * 50 + ny, nd = d + (tt & TERRAIN_MASK_SWAMP ? 5 : 1);
      if (nd < L[nk] && ok(nk, nd)) { L[nk] = nd; A[nk] = d + 1; (B[nd] = B[nd] || []).push(nk); } } }
  return { L, A, n };
}
// returns the direction to move (0 = stay); exit = [x, y] of the exit tile we leave by
function step(c, t, flee, exit) {
  const T = c.room.getTerrain(), mv = t.body.filter(p => p.type === MOVE && p.hits > 0).length || 1;
  const { A } = dijkstra(T, t.pos.x, t.pos.y, Math.ceil((t.fatigue || 0) / (2 * mv)), () => true);
  const adj = k => { const x = (k / 50) | 0, y = k % 50; let m = 32767; for (const [dx, dy] of D9) { const v = A[(x + dx) * 50 + y + dy]; if (v < m) m = v; } return m; };
  const H = flee && exit ? dijkstra(T, exit[0], exit[1], 0, () => true, 400).L : null;
  let best = 0, bs = -1e9;
  for (let k = 0; k <= 8; k++) {
    const x = c.pos.x + D9[k][0], y = c.pos.y + D9[k][1];
    if (x < 1 || x > 48 || y < 1 || y > 48 || T.get(x, y) & TERRAIN_MASK_WALL) continue;
    const dwell = k && T.get(x, y) & TERRAIN_MASK_SWAMP ? 5 : 1;
    const a = adj(x * 50 + y), r = Math.max(Math.abs(x - t.pos.x), Math.abs(y - t.pos.y));
    const room = exit && dwell === 1 && Math.max(Math.abs(x - exit[0]), Math.abs(y - exit[1])) <= 1 ? ROOM_MAX // haven: can leave next tick
      : dwell >= a ? 0 : Math.min(dijkstra(T, x, y, dwell, (nk, d) => d < adj(nk)).n, ROOM_MAX);
    const sc = !room ? (a - dwell) * 10 + r // caught either way: delay it (a swamp lock is the worst)
      : 1000 + (flee ? (room >= ROOM_OK ? 1000 - (H ? H[x * 50 + y] : 0) : 0) + room * 2 + r
      : Math.min(room, ROOM_OK) * 10 - Math.abs(r - 3) * 3 + (r <= 3 ? 5 : 0));
    if (sc > bs) { bs = sc; best = k; }
  }
  return best;
}
module.exports = { step };
