// W47N8 defence doctrine (docs/DEFENSE_W47N8.md, Misaki 17:3x). Pure: no Game access; unit-tested in tests/w47n8_defense.js.
// Defensive only: never leaves W47N8, never safe mode (advice only, Misaki activates), never shoots north-of-seal drain tanks.
//  towerPick : one focus target for every tower. Eligible = claimer anywhere | anything inside the seal (y>3) | armed creep hurting us.
//              Only targets with net damage > 0 (tower dmg at range, TOUGH/boost-reduced, minus all heal reachable on it).
//              Priority healer > ranged > melee > other, then fastest kill; sticky on a target dying within 2 ticks.
//              Energy floor: a target that is not hurting us and not dying within 2 ticks is shot only by towers >= FLOOR.
//  sim       : tick model (same as tools/combat_sim.py) -> 'win' | 'lose' | 'stall'.
//  assess    : spawn border defenders ONLY when towers alone do not win AND towers + 2 defenders do (never feed an unwinnable fight);
//              advise safe mode (Memory flag only) when an armed force is inside the seal and nothing we have wins.
const F = require('../../utils/focus');
const SEAL_Y = 3, FLOOR = 400, MAX_T = 600;
const rng = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
const live = (c, t) => c.body.reduce((n, p) => n + (p.type === t && p.hits > 0 ? 1 : 0), 0);
const cls = c => (live(c, 'heal') ? 0 : live(c, 'ranged_attack') ? 1 : live(c, 'attack') ? 2 : 3);
const armed = c => live(c, 'attack') + live(c, 'ranged_attack') + live(c, 'work') > 0;
const inBase = c => c.pos.y > SEAL_Y;
// towers: [{pos, energy}], hostiles: [{id,pos,hits,body}], o: {prev, hurting:Set, banned:Set}
function towerPick(towers, hostiles, o = {}) {
  const tw = towers.filter(t => t.energy >= 10); if (!tw.length || !hostiles.length) return null;
  const hurting = o.hurting || new Set(), banned = o.banned || new Set();
  const rows = hostiles.map(h => { const raw = tw.reduce((s, t) => s + F.towerDmg(rng(t.pos, h.pos)), 0), net = F.effective(h, raw) - F.healOn(h, hostiles);
    const claim = live(h, 'claim') > 0, hurt = hurting.has(h.id);
    return { h, net, ttk: net > 0 ? h.hits / net : Infinity, cls: claim ? -1 : cls(h), claim, hurt,
      urgent: claim || hurt || (inBase(h) && armed(h)), elig: claim || inBase(h) || (hurt && armed(h)) }; });
  const ok = rows.filter(r => r.elig && r.net > 0 && !(banned.has(r.h.id) && !r.urgent && r.ttk > 2));
  const best = ok.find(r => r.h.id === o.prev && r.ttk <= 2) || ok.sort((a, b) => a.cls - b.cls || a.ttk - b.ttk)[0];
  if (!best) return null;
  const shooters = best.urgent || best.ttk <= 2 ? tw : tw.filter(t => t.energy >= FLOOR);
  return shooters.length ? Object.assign(best, { shooters }) : null;
}
// ---- combat model. enemy: [{body:[{type,hits,boost}], hits}] (real creeps work), towerR: [range per tower], def: body type list.
function mk(c) { const b = c.body.map(p => (typeof p === 'string' ? { type: p, hits: 100 } : { type: p.type, hits: p.hits, boost: p.boost }));
  return { body: b, hits: b.reduce((s, p) => s + p.hits, 0), max: b.length * 100 }; }
function hit(c, d) { c.hits -= d; let left = d; for (const p of c.body) { if (left <= 0) break; const a = Math.min(p.hits, left); p.hits -= a; left -= a; } }
function heal(c, g) { const add = Math.min(g, c.max - c.hits); c.hits += add; let left = add;
  for (let i = c.body.length - 1; i >= 0 && left > 0; i--) { const p = c.body[i], a = Math.min(100 - p.hits, left); p.hits += a; left -= a; } return add; }
function sim(enemy, towerR, def, nDef, o = {}) {
  const en = enemy.map(mk), us = Array.from({ length: nDef }, () => mk({ body: def })), out = new Set();
  let energy = (o.towerE === undefined ? 890 : o.towerE) * towerR.length, burnt = 0, mel = 0;
  const tw = towerR.reduce((s, r) => s + F.towerDmg(r), 0), up = o.meleeUptime || 0;
  for (let t = 1; t <= MAX_T; t++) {
    const E = en.filter(x => x.hits > 0), U = us.filter(x => x.hits > 0 && !out.has(x));
    if (!E.length) return { result: 'win', ticks: t, energy: burnt, lost: us.filter(x => x.hits <= 0).length };
    const hp = E.reduce((s, x) => s + F.healPow(x), 0), ra = U.reduce((s, x) => s + live(x, 'ranged_attack'), 0) * 10;
    const fire = energy >= 10 * towerR.length ? tw : 0;
    const tgt = E.slice().sort((a, b) => cls(a) - cls(b) || a.hits - b.hits).find(x => F.effective(x, fire + ra) - hp > 0);
    let ed = E.reduce((s, x) => s + live(x, 'ranged_attack'), 0) * 10; mel += up; if (mel >= 1) { mel -= 1; ed += E.reduce((s, x) => s + live(x, 'attack'), 0) * 30; }
    if (tgt) { if (fire) { energy -= 10 * towerR.length; burnt += 10 * towerR.length; } hit(tgt, Math.min(tgt.hits, F.effective(tgt, fire + ra))); }
    if (U.length && ed) { const v = U.reduce((a, b) => (b.hits < a.hits ? b : a)); hit(v, Math.min(v.hits, ed));
      for (const d of U) if (d.hits > 0) { heal(d, 12 * live(d, 'heal')); if (d.hits < 0.6 * d.max) out.add(d); } }
    let pool = hp; for (const x of E.filter(x => x.hits > 0).sort((a, b) => a.hits - a.max - (b.hits - b.max))) { if (pool <= 0) break; pool -= heal(x, pool); }
    const U2 = us.filter(x => x.hits > 0 && !out.has(x));
    if (!tgt && (!U2.length || !ed)) return { result: !U2.length && E.some(x => live(x, 'attack') + live(x, 'ranged_attack')) ? 'lose' : 'stall', ticks: t, energy: burnt, lost: us.filter(x => x.hits <= 0).length };
  }
  return { result: 'stall', ticks: MAX_T, energy: burnt, lost: 0 };
}
// force: hostile creeps (or {body} summaries), towerR: tower ranges to the fight, def: defender body for the current cap
// -> { spawn: bool, advise: '' | 'safemode', why }
function assess(force, towerR, def, o = {}) {
  const fighters = force.filter(c => live(c, 'attack') + live(c, 'ranged_attack') > 0);
  if (!fighters.length) return { spawn: false, advise: '', why: 'unarmed' };
  const alone = sim(force, towerR, def, 0, o);
  if (alone.result === 'win') return { spawn: false, advise: '', why: 'towers win', alone };
  const two = sim(force, towerR, def, 2, o);
  if (two.result === 'win' && two.lost === 0) return { spawn: true, advise: '', why: 'towers+2 win', two };
  return { spawn: false, advise: o.inside ? 'safemode' : '', why: 'unwinnable', two };
}
// Border defender decision (pure). me: {pos, hits, hitsMax, ra, hurt}, hs: hostiles in W47N8, o: {focus, win, towers:[pos], quiet}
// -> { hurt, shoot: creep|null, mass: bool, move: 'flee'|'retreat'|'approach'|'post'|'recycle'|'hold', goal, from }
//  - shoots the towers' focus when it is in range 3 (same target = focus fire), else pickDef (healer first, net > 0, mass when >=3 close)
//  - never shoots unarmed creeps north of the seal (drain tanks); keeps range >= 3 from melee; retreats below 60% to a tower (healed),
//    back at 95%; when the fight is not winnable (o.win false) stays inside tower cover (<= COVER of a tower) and only shoots what comes
//  - nothing hostile for RECYCLE ticks -> recycle at the spawn (no idle upkeep)
const COVER = 8, RECYCLE = 100;
function defPlan(me, hs, o = {}) {
  const hurt = me.hits < me.hitsMax * 0.6 ? true : me.hits >= me.hitsMax * 0.95 ? false : !!me.hurt;
  const elig = hs.filter(h => inBase(h) || armed(h) || live(h, 'heal'));
  const towers = o.towers || [], covered = p => towers.some(t => rng(t, p) <= COVER);
  const nearT = towers.length ? towers.reduce((a, t) => (rng(t, me.pos) < rng(a, me.pos) ? t : a)) : null;
  let shoot = null, mass = false;
  const f = o.focus && elig.find(h => h.id === o.focus && rng(h.pos, me.pos) <= 3);
  const pk = elig.length ? F.pickDef(me.pos, me.ra, elig, o.prev) : null;
  if (f) shoot = f; else if (pk && rng(pk.h.pos, me.pos) <= 3) { shoot = pk.h; mass = pk.mass; }
  const melee = hs.find(h => live(h, 'attack') && rng(h.pos, me.pos) <= 2);
  const r = (move, goal) => ({ hurt, shoot, mass, move, goal });
  if (melee) return Object.assign(r('flee', null), { from: melee.pos });
  if (hurt && nearT) return r('retreat', nearT);
  if (!elig.length) return (o.quiet || 0) >= RECYCLE ? r('recycle', null) : r('post', null);
  const goal = (o.focus && elig.find(h => h.id === o.focus)) || (pk && pk.h);
  if (!goal) return r('hold', null);
  if (o.win === false && !covered(goal.pos)) return covered(me.pos) || !nearT ? r('hold', null) : r('retreat', nearT);
  return rng(goal.pos, me.pos) > 3 ? r('approach', goal.pos) : r('hold', null);
}
// body summary {attack:n,...} (tools/north_watch.py) -> body list in the worst-case order (tough, move, work parts last)
function fromCounts(b) { const out = []; for (const t of ['tough', 'move', 'attack', 'ranged_attack', 'heal', 'work', 'claim', 'carry']) for (let i = 0; i < (b[t] | 0); i++) out.push({ type: t, hits: 100 }); return { body: out, hits: out.length * 100 }; }
module.exports = { towerPick, sim, assess, defPlan, COVER, RECYCLE, fromCounts, cls, armed, inBase, FLOOR, SEAL_Y };
