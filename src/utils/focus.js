// Tower/defender focus-fire (docs/DEFENSE.md "Home defense"). Pure: no Game access, unit-tested in tests/focus.js.
// net(t) = tower damage at range (TOUGH/boost-reduced) - max heal all hostile healers can put on t next tick (self 12/HEAL,
// adjacent 12, range 2-3 4; boosted HEAL x2..4). Healer first if net>0; else highest net / fastest kill; never fire at net<=0
// (anti-drain: edge tanks bounce out and heal) unless the target is hurting us. Sticky on the previous target near death.
const TOUGH_MULT = { '': 1, GO: 0.7, GHO2: 0.5, XGHO2: 0.3 }, HEAL_MULT = { '': 1, LO: 2, LHO2: 3, XLHO2: 4 };
function towerDmg(r) { return r <= 5 ? 600 : r >= 20 ? 150 : 600 - (r - 5) * 30; }
const rng = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
function healPow(h) { let s = 0; for (const p of h.body) if (p.type === 'heal' && p.hits > 0) s += 12 * (HEAL_MULT[p.boost || ''] || 1); return s; }
// damage after TOUGH absorbs (body order: front parts take damage first)
function effective(h, raw) {
  let left = raw, dealt = 0;
  for (const p of h.body) { if (left <= 0) break; if (p.hits <= 0) continue;
    const m = p.type === 'tough' ? (TOUGH_MULT[p.boost || ''] || 1) : 1, absorb = Math.min(p.hits, left * m);
    dealt += absorb; left -= absorb / m; }
  return dealt + Math.max(0, left);
}
function healOn(t, hostiles) {
  let s = 0; for (const h of hostiles) { const p = healPow(h); if (!p) continue; const r = rng(h.pos, t.pos);
    s += h === t || r <= 1 ? p : r <= 3 ? p / 3 : 0; } return s;
}
// towers: [{pos, energy}], hostiles: [{id,pos,hits,body}], o: {prev, hurting:Set(id), minE}
function pick(towers, hostiles, o = {}) {
  const minE = o.minE === undefined ? 10 : o.minE, armed = towers.filter(t => t.energy >= minE);
  if (!armed.length || !hostiles.length) return null;
  const rows = hostiles.map(h => { const raw = armed.reduce((s, t) => s + towerDmg(rng(t.pos, h.pos)), 0);
    const net = effective(h, raw) - healOn(h, hostiles); return { h, net, ttk: net > 0 ? h.hits / net : Infinity, healer: healPow(h) > 0,
      edge: h.pos.x <= 1 || h.pos.y <= 1 || h.pos.x >= 48 || h.pos.y >= 48 }; });
  const prev = o.prev && rows.find(r => r.h.id === o.prev && r.net > 0 && r.ttk <= 2);
  if (prev) return prev;
  // anti-drain (Misaki 10-16): shoot edge-sitters by default; only creeps with an OBSERVED drain pattern (o.banned, see track())
  // are skipped while they sit on the exit strip, unless dead within 2 ticks or hurting us
  const hurting = o.hurting || new Set(), banned = o.banned || new Set();
  const ok = rows.filter(r => r.net > 0 && !(banned.has(r.h.id) && r.edge && r.ttk > 2 && !hurting.has(r.h.id)));
  const healers = ok.filter(r => r.healer);
  const best = (healers.length ? healers : ok).sort((a, b) => a.ttk - b.ttk)[0];
  if (best) return best;
  const hurt = rows.filter(r => o.hurting && o.hurting.has(r.h.id)).sort((a, b) => b.net - a.net)[0];
  return hurt || null; // hold fire
}
// Drain-pattern tracker. mem: {id: {hits, max, dmg, cyc, spent, seen, ban}}. present: hostiles now in room; shotId/energy: what we
// fired last tick. A cycle = we knocked it to <=70%, then it recovered to >=90% (healed on the strip or out of room). >=2 cycles, or >=1000
// tower energy spent with hits recovered -> ban for BAN ticks. Returns Set of banned ids.
const BAN = 1500;
function track(mem, present, time, shotId, spent) {
  const out = new Set();
  for (const h of present) {
    const max = h.hitsMax || h.body.length * 100, r = mem[h.id] || (mem[h.id] = { hits: h.hits, max, dmg: false, cyc: 0, spent: 0 });
    if (shotId === h.id) r.spent += spent || 0;
    // a cycle needs a REAL knock-down (<=70%) then recovery to >=90%: a 5000hp tank tickled to 94% and healed is not a drain (10-16 dpefwd3)
    if (h.hits < r.hits - 0.5) { r.dmg = true; r.low = Math.min(r.low === undefined ? h.hits : r.low, h.hits); }
    else if (r.dmg && h.hits >= max * 0.9) { if (r.low <= max * 0.7) r.cyc++; r.dmg = false; r.low = undefined; }
    r.hits = h.hits; r.max = max; r.seen = time;
    if (!r.ban && (r.cyc >= 2 || (r.spent >= 1000 && h.hits >= max * 0.9))) r.ban = time + BAN;
    if (r.ban && time >= r.ban) { r.ban = 0; r.cyc = 0; r.spent = 0; }
    if (r.ban) out.add(h.id);
  }
  for (const id in mem) if (time - mem[id].seen > BAN) delete mem[id];
  return out;
}
module.exports = { track, BAN, towerDmg, effective, healOn, healPow, pick };
