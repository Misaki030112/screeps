// W47N8 spawn-energy meter (Misaki 17:2x "spawn must never wait for energy"). Memory.ops.w8fm, a few hundred bytes.
// Per spawn tick: sp = spawning, w = idle with a creep wanted but energy short (waiting), i = idle, nothing wanted.
// Refill: energy delivered into spawn/extensions (dAvail + spent), ticks below cap, episodes empty-ish -> full (last 12).
// Fill transfers by role: n transfers, e energy, trips (loads that made >= 1 fill), walk = ticks a creep held a fill target.
// Reset: Memory.ops.w8fm = undefined (starts a new window).
const M = () => { const o = (Memory.ops = Memory.ops || {}); return (o.w8fm = o.w8fm || { t0: Game.time, n: 0, sp: 0, w: 0, i: 0, low: 0, del: 0, ep: [], ws: [], x: {} }); };
let lastT = -1, waitT = -1;
function tick(spawn) {
  if (lastT === Game.time) return; lastT = Game.time;
  const m = M(), r = spawn.room, a = r.energyAvailable, cap = r.energyCapacityAvailable;
  m.n++;
  if (spawn.spawning) m.sp++;
  if (m.pa !== undefined) { const d = a - m.pa + (m.ps || 0); if (d > 0) m.del += d; }
  m.pa = a; m.ps = 0;
  if (a < cap) { m.low++; if (!m.cur) m.cur = [Game.time, cap - a]; else m.cur[1] = Math.max(m.cur[1], cap - a); }
  else if (m.cur) { m.ep.push([m.cur[0], m.cur[1], Game.time - m.cur[0]]); if (m.ep.length > 12) m.ep.shift(); delete m.cur; }
}
// called by spawnRun when it wants `role` but energy < cost (after tick() this tick)
function wait(role, cost, avail) {
  const m = M(); if (waitT === Game.time) return; waitT = Game.time;
  m.w++;
  if (!m.wc) m.wc = [role, cost, Game.time];
}
// called by spawnRun after a successful spawnCreep (also closes the open wait episode)
function spent(cost) {
  const m = M(); m.ps = (m.ps || 0) + cost;
  if (m.wc) { m.ws.push([m.wc[0], m.wc[1], Game.time - m.wc[2]]); if (m.ws.length > 12) m.ws.shift(); delete m.wc; }
}
function idle() { const m = M(); m.i++; if (m.wc) { delete m.wc; } }
// fill transfer accounting (role-level): amt actually moved; trip flag kept on the creep memory (fm)
function xfer(c, amt) {
  const m = M(), k = c.memory.role, x = (m.x[k] = m.x[k] || [0, 0, 0, 0]);
  x[0]++; x[1] += amt; if (!c.memory.fm) { c.memory.fm = 1; x[2]++; }
}
function walk(c) { const m = M(), k = c.memory.role, x = (m.x[k] = m.x[k] || [0, 0, 0, 0]); x[3]++; }
module.exports = { tick, wait, spent, idle, xfer, walk };
