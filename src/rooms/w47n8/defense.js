// W47N8 defence doctrine (docs/DEFENSE_W47N8.md, Misaki 17:3x). Pure: no Game access; unit-tested in tests/w47n8_defense.js.
// Defensive only: never leaves W47N8, never safe mode (advice only, Misaki activates), never shoots north-of-seal drain tanks.
//  towerPick : one focus target for every tower. Eligible = claimer anywhere | anything inside the seal (y>3) | armed creep hurting us.
//              Only targets with net damage > 0 (tower dmg at range, TOUGH/boost-reduced, minus all heal reachable on it).
//              Priority healer > ranged > melee > other (Misaki 17:40), lowest hp; sticky on a target dying within 2 ticks.
//              Energy floor: a target that is not hurting us and not dying within 2 ticks is shot only by towers >= FLOOR.
//  sim       : tick model (same as tools/combat_sim.py) -> 'win' | 'lose' | 'stall'.
//  assess    : spawn border defenders ONLY when towers alone do not win AND towers + 2 defenders do (never feed an unwinnable fight);
//              advise safe mode (Memory flag only) when an armed force is inside the seal and nothing we have wins.
const F = require('../../utils/focus');
const SEAL_Y = 3, FLOOR = 400, MAX_T = 600;
const rng = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
const live = (c, t) => c.body.reduce((n, p) => n + (p.type === t && p.hits > 0 ? 1 : 0), 0);
const cls = c => (live(c, 'heal') ? 0 : live(c, 'ranged_attack') ? 1 : live(c, 'attack') ? 2 : 3); // Misaki 17:40: healers always first, then ranged, melee
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
  const best = ok.find(r => r.h.id === o.prev && r.ttk <= 2) || ok.sort((a, b) => a.cls - b.cls || a.h.hits - b.h.hits)[0];
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
  const defs = Array.isArray(def[0]) ? def : Array.from({ length: nDef }, () => def); // def: one body x nDef, or a list of bodies
  const en = enemy.map(mk), us = defs.map(b => mk({ body: b })), out = new Set();
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
// Border defender decision (pure; Misaki 17:36-17:38 simple rules). me: {pos, hits, hitsMax, hurt}, hs: hostiles in W47N8,
// o: {focus, towers:[pos], quiet, enemyX, idx}  -> { hurt, shoot, mass, move: 'flee'|'retreat'|'approach'|'post'|'recycle'|'hold', goal }
//  - HP rule: fight while >= 60%; below 60% retreat toward the nearest tower (towers heal); back to the wall at >= 90%
//  - target: the towers' focus when in range 3, else healer > ranged > melee, lowest hp; rangedMassAttack when >= 3 hostiles within 2
//  - station: the tile right behind the seal (y=4) of the segment nearest the enemy, spread by idx (POSTS); melee north of the seal
//    cannot reach y=4, so only melee INSIDE the seal makes us kite away; never shoots unarmed drain tanks north of the seal
//  - nothing hostile and no alert for RECYCLE ticks -> recycle
const COVER = 8, RECYCLE = 100;
const POSTS = { west: [[8, 4], [9, 4], [10, 4], [11, 4]], east: [[24, 4], [25, 4], [26, 4], [28, 4], [29, 4], [30, 4], [31, 4]] }; // y=4 open tiles (27,4 swamp)
function postTile(enemyX, idx = 0) {
  const ex = enemyX === undefined ? 29 : enemyX, seg = ex < 18 ? POSTS.west : POSTS.east;
  const t = seg.slice().sort((a, b) => Math.abs(a[0] - ex) - Math.abs(b[0] - ex));
  const [x, y] = t[Math.min(t.length - 1, idx * 2)]; return { x, y };
}
const dcls = cls;
function defPlan(me, hs, o = {}) {
  const hurt = me.hits < me.hitsMax * 0.6 ? true : me.hits >= me.hitsMax * 0.9 ? false : !!me.hurt;
  const elig = hs.filter(h => inBase(h) || armed(h) || live(h, 'heal'));
  const towers = o.towers || [], nearT = towers.length ? towers.reduce((a, t) => (rng(t, me.pos) < rng(a, me.pos) ? t : a)) : null;
  const inR = elig.filter(h => rng(h.pos, me.pos) <= 3);
  const f = o.focus && inR.find(h => h.id === o.focus);
  const shoot = f || inR.slice().sort((a, b) => dcls(a) - dcls(b) || a.hits - b.hits)[0] || null;
  const mass = elig.filter(h => rng(h.pos, me.pos) <= 2).length >= 3;
  const r = (move, goal) => ({ hurt, shoot, mass, move, goal });
  const melee = hs.find(h => inBase(h) && live(h, 'attack') && rng(h.pos, me.pos) <= 2);
  if (melee) return Object.assign(r('flee', null), { from: melee.pos });
  if (hurt && nearT) return r('retreat', nearT);
  if (!elig.length) return (o.quiet || 0) >= RECYCLE ? r('recycle', null) : r('post', postTile(o.enemyX, o.idx));
  const inside = elig.filter(h => inBase(h) && armed(h));
  if (inside.length) { const g = inside.sort((a, b) => dcls(a) - dcls(b) || a.hits - b.hits)[0]; return rng(g.pos, me.pos) > 3 ? r('approach', g.pos) : r('hold', null); }
  // enemy north of the seal: stand on the post behind the wall nearest them (shoots at range 3 from y=4)
  const ex = Math.round(elig.reduce((s, h) => s + h.pos.x, 0) / elig.length), p = postTile(ex, o.idx);
  return me.pos.x === p.x && me.pos.y === p.y ? r('hold', null) : r('post', p);
}
// ---- joint defence (Misaki 17:34): ONE planner for the W46N8 + W47N8 roster. Bodies: RA+MOVE only (towers heal on our ground).
const raBody = (e, max = 25) => { const k = Math.max(1, Math.min(max, Math.floor(e / 200))); return Array(k).fill('ranged_attack').concat(Array(k).fill('move')); };
// o: {force, towerR (ranges tower -> fight), homeOk, homeCap, w8Cap, inside}
// Misaki 17:45: home ALWAYS sends a baseline of 1 defender while a real (armed) threat is active and home itself is safe, win or lose.
// Local W47N8 defenders = fewest (0-2) that win (no losses) together with the baseline. A 2nd home defender only if the sim says it
// turns a loss into a win. Still unwinnable -> baseline only, no local spawns (never feed a lost fight); inside the seal -> advise safe mode.
function plan(o) {
  const fighters = o.force.filter(c => live(c, 'attack') + live(c, 'ranged_attack') > 0);
  if (!fighters.length) return { home: 0, w8: 0, win: true, why: 'unarmed', advise: '' };
  const hb = raBody(o.homeCap || 0), wb = raBody(o.w8Cap || 0, 12), base = o.homeOk ? 1 : 0;
  const wins = defs => { const r = defs.length ? sim(o.force, o.towerR, defs, 0, o) : sim(o.force, o.towerR, wb, 0, o); return r.result === 'win' && !r.lost; };
  for (let h = base; h <= (o.homeOk ? 2 : 0); h++)
    for (let n = 0; n <= 2; n++) if (wins(Array(h).fill(hb).concat(Array(n).fill(wb)))) return { home: h, w8: n, win: true, why: h > base ? 'extra home' : 'win', advise: '' };
  return { home: base, w8: 0, win: false, why: 'unwinnable', advise: o.inside ? 'safemode' : '' };
}
// ---- seal repair under fire (Misaki 17:36): walls an armed hostile can reach (RA 3 / ATTACK, WORK 1); lowest first
function repairPick(walls, hs) {
  const reach = h => (live(h, 'ranged_attack') ? 3 : live(h, 'attack') + live(h, 'work') ? 1 : 0);
  return walls.filter(w => hs.some(h => reach(h) && rng(w.pos, h.pos) <= reach(h))).sort((a, b) => a.hits - b.hits)[0] || null;
}
// stand within 3 of the wall, on our side (y > wall.y), as far as possible from enemy RA/melee; open(x,y) = walkable
function repairStand(wall, hs, open = () => true) {
  const en = hs.filter(armed); let best = null, bs = -1;
  for (let dx = -3; dx <= 3; dx++) for (let dy = 1; dy <= 3; dy++) { const x = wall.pos.x + dx, y = wall.pos.y + dy; if (!open(x, y)) continue;
    const d = en.length ? Math.min(...en.map(h => rng(h.pos, { x, y }))) : 9, sc = Math.min(d, 4) * 10 - Math.abs(dx);
    if (sc > bs) { bs = sc; best = { x, y }; } }
  return best;
}
// body summary {attack:n,...} (tools/north_watch.py) -> body list in the worst-case order (tough, move, work parts last)
function fromCounts(b) { const out = []; for (const t of ['tough', 'move', 'attack', 'ranged_attack', 'heal', 'work', 'claim', 'carry']) for (let i = 0; i < (b[t] | 0); i++) out.push({ type: t, hits: 100 }); return { body: out, hits: out.length * 100 }; }
module.exports = { towerPick, sim, assess, defPlan, postTile, POSTS, plan, raBody, repairPick, repairStand, COVER, RECYCLE, fromCounts, cls, armed, inBase, FLOOR, SEAL_Y };
