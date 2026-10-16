// Remote mining W45N8 (approved 2026-10-13). One source, reserved. docs/REMOTE_W45N8.md
// Safety: hostile combat creeps (or damage to our creeps) in W45N8 or W46N8 -> Memory.remote[R].pauseUntil = now+1500,
// remote creeps flee home and remote spawning stops. Logs ALERT lines (picked up by listener -> alerts.py).
const CFG = { W45N8: { home: 'W46N8', src: [14, 12], cont: [13, 11], ctl: [7, 36], exitHome: [49, 14], exitRemote: [0, 14],
  // swamp tiles on the ideal haul route (model.py pave list); home-side swamps live in layout RCL3 roads
  roads: [[2, 12]],
  // where fleeing remote creeps wait at home while paused: plain tiles off every fixed route/plan tile, near the exit route
  park: [46, 21],
  // anti-Invader defender (docs/DEFENDER.md). Flag ON, but threat.armed() only arms it when RCL4 has been stable 1500 ticks
  // (cap>=1300, full within 300t) AND a CLAIM>=2 reserver is alive. Thresholds: threat.DEF, per-room override `threat: {...}`.
  defend: true } };
// Threat handling lives in ./threat (one state machine per remote). This file: config, bookkeeping, roads, ALERT lines.
const threat = require('./threat');
function mem(r) { return (Memory.remote = Memory.remote || {})[r] = Memory.remote[r] || {}; }
function paused(r, role) { return !threat.safe(r, role); } // role: rminer/rhauler may resume early (threat.EARLY)
function defendOn(r) { return threat.armed(r); }
function placeRoads(r) {
  const C = CFG[r], room = Game.rooms[r]; if (!room || !C.roads) return;
  for (const [x, y] of C.roads) {
    if (room.lookForAt(LOOK_STRUCTURES, x, y).some(s => s.structureType === STRUCTURE_ROAD)) continue;
    if (room.lookForAt(LOOK_CONSTRUCTION_SITES, x, y).some(s => s.structureType === STRUCTURE_ROAD)) continue;
    room.createConstructionSite(x, y, STRUCTURE_ROAD);
  }
}
function check(r) {
  const C = CFG[r], m = mem(r), was = threat.state(r).st, th = threat.run(r);
  if (th.st !== threat.S.SAFE && (was === threat.S.SAFE || Game.time % 50 === 0)) {
    if (was === threat.S.SAFE) m.pauseStart = Game.time;
    const inv = th.last || [];
    console.log('ALERT ' + JSON.stringify({ episode: `remote-${r}-${m.pauseStart}`, tick: Game.time, room: r, owner: th.why === 'player' ? 'player' : 'Invader',
      severity: th.why === 'player' ? 'high' : 'medium', creeps: inv.length, remote: r, state: th.st, why: th.why, invOnly: th.why !== 'player',
      action: th.st === 'THREAT' ? 'defender requested' : th.st === 'DEFEND' ? 'defender engaging' : `remote paused (${th.why})`, positions: inv.slice(0, 5).map(h => [h.x, h.y]) }));
  }
  if (th.st === threat.S.SAFE && was !== threat.S.SAFE) console.log('ALERT ' + JSON.stringify({ episode: `remote-${r}-${m.pauseStart}`, tick: Game.time, room: r, severity: 'low', remote: r, ended: true, action: 'remote resumed' }));
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
module.exports = { CFG, paused, mem, defendOn, run() { for (const r in CFG) check(r); } };
