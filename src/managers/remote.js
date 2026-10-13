// Remote mining W45N8 (approved 2026-10-13). One source, reserved. docs/REMOTE_W45N8.md
// Safety: hostile combat creeps (or damage to our creeps) in W45N8 or W46N8 -> Memory.remote[R].pauseUntil = now+1500,
// remote creeps flee home and remote spawning stops. Logs ALERT lines (picked up by listener -> alerts.py).
const CFG = { W45N8: { home: 'W46N8', src: [14, 12], cont: [13, 11], ctl: [7, 36], exitHome: [49, 14], exitRemote: [0, 14],
  // swamp tiles on the ideal haul route (model.py pave list); home-side swamps live in layout RCL3 roads
  roads: [[2, 12]],
  // where fleeing remote creeps wait at home while paused: plain tiles off every fixed route/plan tile, near the exit route
  park: [46, 21] } };
const PAUSE = 1500, COMBAT = ['attack', 'ranged_attack'];
function mem(r) { return (Memory.remote = Memory.remote || {})[r] = Memory.remote[r] || { pauseUntil: 0 }; }
function paused(r) { return (mem(r).pauseUntil || 0) > Game.time; }
function placeRoads(r) {
  const C = CFG[r], room = Game.rooms[r]; if (!room || !C.roads) return;
  for (const [x, y] of C.roads) {
    if (room.lookForAt(LOOK_STRUCTURES, x, y).some(s => s.structureType === STRUCTURE_ROAD)) continue;
    if (room.lookForAt(LOOK_CONSTRUCTION_SITES, x, y).some(s => s.structureType === STRUCTURE_ROAD)) continue;
    room.createConstructionSite(x, y, STRUCTURE_ROAD);
  }
}
function check(r) {
  const C = CFG[r], m = mem(r);
  for (const rn of [r, C.home]) {
    const room = Game.rooms[rn]; if (!room) continue;
    const bad = room.find(FIND_HOSTILE_CREEPS).filter(h => h.body.some(p => COMBAT.includes(p.type) && p.hits > 0));
    const hurt = _.filter(Game.creeps, c => c.memory.remote === r && c.room.name === rn && c.hits < c.hitsMax);
    if (bad.length || hurt.length) {
      const fresh = !paused(r);
      // Invader-only: pause until they age out (+buffer), not a flat 1500 (saves resume time after short TTL left)
      const invOnly = bad.length > 0 && bad.every(h => h.owner.username === 'Invader') && !hurt.length;
      const ttl = invOnly ? Math.max(...bad.map(h => h.ticksToLive || 1500)) : PAUSE;
      const until = Game.time + (invOnly ? Math.min(PAUSE, ttl + 80) : PAUSE);
      m.pauseUntil = Math.max(m.pauseUntil || 0, until);
      if (fresh || Game.time % 50 === 0) {
        const owners = _.uniq(bad.map(h => h.owner.username));
        console.log('ALERT ' + JSON.stringify({ episode: `remote-${r}-${m.pauseStart = fresh ? Game.time : m.pauseStart}`, tick: Game.time, room: rn,
          owner: owners.join(',') || 'unknown', severity: hurt.length ? 'high' : 'medium', creeps: bad.length, remote: r, ourHurt: hurt.length,
          invOnly, pauseUntil: m.pauseUntil,
          action: `remote creeps fleeing home, remote spawning paused until ${m.pauseUntil}`, positions: bad.slice(0, 5).map(h => [h.pos.x, h.pos.y]) }));
      }
    }
  }
  const room = Game.rooms[r];
  if (room) {
    const ct = room.controller; m.res = ct && ct.reservation ? ct.reservation : null;
    const k = room.lookForAt(LOOK_STRUCTURES, C.cont[0], C.cont[1]).find(s => s.structureType === STRUCTURE_CONTAINER);
    m.cont = k ? { id: k.id, e: k.store[RESOURCE_ENERGY], hits: k.hits } : null; m.seen = Game.time;
    const src = room.lookForAt(LOOK_SOURCES, C.src[0], C.src[1])[0];
    if (src) m.invaderHarvested = src.invaderHarvested;
    if (!paused(r)) placeRoads(r);
  }
}
module.exports = { CFG, paused, mem, run() { for (const r in CFG) check(r); } };
