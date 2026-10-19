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
// 17:58: boosted melee. UH x2, UH2O x3, XUH2O x4 per ATTACK part; unboosted parts assume `def` (north stock has UH -> plan assumes UH)
const ATK_MULT = { UH: 2, UH2O: 3, XUH2O: 4 };
const atkPow = (c, def) => c.body.reduce((n, p) => n + (p.type === 'attack' && p.hits > 0 ? 30 * (ATK_MULT[p.boost || def] || 1) : 0), 0);
// 17:59 (Misaki): defenders with HEAL heal every tick besides shooting. me {pos,hits,hitsMax,id}, friends [{id,pos,hits,hitsMax}] (incl. me),
// shooting: rangedAttack/mass this tick. -> {act:'heal'|'rangedHeal', id} | null. heal() at 1 never conflicts with rangedAttack;
// rangedHeal does, so only when not shooting. Pre-heal self when armed hostiles within 4.
function healAct(me, friends, hs, shooting) {
  const pct = f => f.hits / f.hitsMax, hurt = friends.filter(f => f.hits < f.hitsMax);
  const adj = hurt.filter(f => rng(f.pos, me.pos) <= 1).sort((a, b) => pct(a) - pct(b))[0];
  if (adj) return { act: 'heal', id: adj.id };
  if (me.hits < me.hitsMax || hs.some(h => armed(h) && rng(h.pos, me.pos) <= 4)) return { act: 'heal', id: me.id };
  if (!shooting) { const far = hurt.filter(f => rng(f.pos, me.pos) <= 3).sort((a, b) => pct(a) - pct(b))[0]; if (far) return { act: 'rangedHeal', id: far.id }; }
  return null;
}
// 17:58 feints: armed groups on BOTH seal segments -> defenders split by wall threat (10/RA, 30/ATTACK, 50/WORK; >=1 each when n>=2).
// -> { x: target x for this defender, idx: index inside its group }
const SEG_X = 18;
function segSplit(elig, n, idx) {
  const w = h => 10 * live(h, 'ranged_attack') + 30 * live(h, 'attack') + 50 * live(h, 'work');
  const W = elig.filter(h => h.pos.x < SEG_X), E = elig.filter(h => h.pos.x >= SEG_X);
  const ww = W.reduce((s, h) => s + w(h), 0), we = E.reduce((s, h) => s + w(h), 0);
  const cx = g => Math.round(g.reduce((s, h) => s + h.pos.x, 0) / g.length);
  if (!ww || !we || n < 2) return null;
  const nw = Math.min(n - 1, Math.max(1, Math.round(n * ww / (ww + we))));
  return idx < n - nw ? { x: cx(E), idx } : { x: cx(W), idx: idx - (n - nw) };
}
const cls = c => (live(c, 'heal') ? 0 : live(c, 'ranged_attack') ? 1 : live(c, 'attack') ? 2 : 3); // Misaki 17:40: healers always first, then ranged, melee
const armed = c => live(c, 'attack') + live(c, 'ranged_attack') + live(c, 'work') > 0;
const inBase = c => c.pos.y > SEAL_Y;
// towers: [{pos, energy}], hostiles: [{id,pos,hits,body}], o: {prev, hurting:Set, banned:Set}
function towerPick(towers, hostiles, o = {}) {
  const tw = towers.filter(t => t.energy >= 10); if (!tw.length || !hostiles.length) return null;
  const hurting = o.hurting || new Set(), banned = o.banned || new Set();
  // 17:58: net counts COMBINED focused damage: towers + our RA within 3 (defenders shoot the tower focus). Tower-only net made a far
  // tower (150) hold fire forever vs 84-252 heal while defenders + tower together beat it. o.allies: [{pos, ra}] (live RA parts)
  const allies = o.allies || [], hurtIds = new Set([...hurting]);
  const rows = hostiles.map(h => { const raw = tw.reduce((s, t) => s + F.towerDmg(rng(t.pos, h.pos)), 0) + allies.reduce((s, a) => s + (rng(a.pos, h.pos) <= 3 ? 10 * a.ra : 0), 0), net = F.effective(h, raw) - F.healOn(h, hostiles);
    const claim = live(h, 'claim') > 0, hurt = hurting.has(h.id) || (live(h, 'heal') > 0 && hostiles.some(x => hurtIds.has(x.id) && rng(x.pos, h.pos) <= 3)); // healer backing an attacker counts as hurting us
    return { h, net, ttk: net > 0 ? h.hits / net : Infinity, cls: claim ? -1 : cls(h), claim, hurt,
      urgent: claim || hurt || (inBase(h) && armed(h)), elig: claim || inBase(h) || (hurt && (armed(h) || live(h, 'heal') > 0)) }; });
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
    let ed = E.reduce((s, x) => s + live(x, 'ranged_attack'), 0) * 10; mel += up; if (mel >= 1) { mel -= 1; ed += E.reduce((s, x) => s + atkPow(x, o.atkBoost), 0); }
    if (tgt) { if (fire) { energy -= 10 * towerR.length; burnt += 10 * towerR.length; } hit(tgt, Math.min(tgt.hits, F.effective(tgt, fire + ra))); }
    if (U.length && ed) { const v = U.reduce((a, b) => (b.hits < a.hits ? b : a)); hit(v, Math.min(v.hits, ed));
      // 18:04: all our HEAL (dedicated healer + self-heal parts) goes to the most-hurt defenders first (healer stands adjacent)
      let hp2 = U.reduce((s, d) => s + (d.hits > 0 ? 12 * live(d, 'heal') : 0), 0);
      for (const d of U.filter(d => d.hits > 0).sort((a, b) => a.hits / a.max - b.hits / b.max)) { if (hp2 <= 0) break; hp2 -= heal(d, hp2); }
      for (const d of U) if (d.hits > 0 && d.hits < 0.6 * d.max) out.add(d); }
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
//  - station (17:53): dynamic wall-back tile (y=4) nearest the focus target / enemy centroid, spread by idx, builders avoided; melee north of the seal
//    cannot reach y=4, so only melee INSIDE the seal makes us kite away; never shoots unarmed drain tanks north of the seal
//  - nothing hostile: idle by the north wall (18:04: never recycle; live out TTL, still respond if the enemy returns)
const COVER = 8, RECYCLE = 100;
const POSTS = { west: [[8, 4], [9, 4], [10, 4], [11, 4]], east: [[24, 4], [25, 4], [26, 4], [28, 4], [29, 4], [30, 4], [31, 4]] }; // cached wall-back tiles (y=4, inside the seal; 27,4 swamp)
const IDLE = [[28, 5], [29, 5], [25, 5], [30, 5], [26, 5], [31, 5], [24, 5], [27, 5]]; // 17:53: no hostiles -> near the east wall middle, plain, off roads
// dynamic station (Misaki 17:53): the wall-back tile nearest target x, defender idx takes the idx-th nearest (adjacent tiles, no
// stacking); tiles in `avoid` (builders repairing, other creeps) are skipped. Always y=4, i.e. inside the seal.
function postTile(tx, idx = 0, avoid = []) {
  const ex = tx === undefined ? 29 : tx, seg = ex < 18 ? POSTS.west : POSTS.east;
  const t = seg.filter(([x, y]) => !avoid.some(a => a.x === x && a.y === y)).sort((a, b) => Math.abs(a[0] - ex) - Math.abs(b[0] - ex) || a[0] - b[0]);
  const [x, y] = t.length ? t[Math.min(t.length - 1, idx)] : seg[0]; return { x, y };
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
  if (hurt && o.healer) return Object.assign(r('retreat', o.healer), { toHealer: true }); // 07:31: hurt defenders come to the healer
  if (hurt && nearT) return r('retreat', nearT);
  if (!elig.length) { // 18:04 (Misaki): no recycle when quiet; defenders live out their TTL idling off-road by the north wall
    if (o.enemyX === undefined) { const [x, y] = IDLE[Math.min(IDLE.length - 1, o.idx || 0)]; return me.pos.x === x && me.pos.y === y ? r('hold', null) : r('post', { x, y }); }
    const p = postTile(o.enemyX, o.idx, o.avoid); return me.pos.x === p.x && me.pos.y === p.y ? r('hold', null) : r('post', p); }
  const inside = elig.filter(h => inBase(h) && armed(h));
  if (inside.length) { const g = inside.sort((a, b) => dcls(a) - dcls(b) || a.hits - b.hits)[0]; return rng(g.pos, me.pos) > 3 ? r('approach', g.pos) : r('hold', null); }
  // enemy north of the seal: stand on the post behind the wall nearest them (shoots at range 3 from y=4)
  // shadow the enemy along the inner wall: focus target x (else the group centroid), re-picked every tick (11 cached tiles: cheap)
  const sp = o.n && segSplit(elig.filter(armed), o.n, o.idx || 0);
  const ft = o.focus && elig.find(h => h.id === o.focus), ex = ft ? ft.pos.x : Math.round(elig.reduce((s, h) => s + h.pos.x, 0) / elig.length);
  const p = sp ? postTile(sp.x, sp.idx, o.avoid) : postTile(ex, o.idx, o.avoid);
  return me.pos.x === p.x && me.pos.y === p.y ? r('hold', null) : r('post', p);
}
// ---- joint defence (Misaki 17:34): ONE planner for the W46N8 + W47N8 roster. Bodies: RA+MOVE only (towers heal on our ground).
// 18:04 dedicated healer: HEAL+MOVE pairs (300 e each)
const healBody = (e, max = 25) => { const k = Math.max(1, Math.min(max, Math.floor(e / 300))); return Array(k).fill('heal').concat(Array(k).fill('move')); };
// 10-20 07:31 (Misaki): the healer never stands by the walls. Enemy ranged can stand at y<=2 (north of the y=3 seal) and reach y<=5;
// safe spots are >= 4 tiles inside the seal (y >= SAFE_HY), plain, off roads/paths. It waits there, goes out only to heal a hurt
// friendly (rangedHeal from range 2-3, picking a tile outside every armed hostile's reach when one exists) and walks back afterwards.
const SAFE_HY = SEAL_Y + 4; // y >= 7
const HIDLE = [[21, 8], [20, 8], [19, 8], [22, 8]];
const hSafe = (t, hs) => t.y >= SAFE_HY - 1 && !hs.some(h => armed(h) && rng(h.pos, t) <= (live(h, 'attack') && !live(h, 'ranged_attack') ? 2 : 4)); // y>=6: out of reach from y<=2
// healer (pure). me {id,pos,hits,hitsMax,hurt}, defs: our combat defenders [{id,pos,hits,hitsMax}], hs: hostiles, o {towers:[pos], idx, open(x,y)}
// -> {hurt, heal:{act,id}|null, move:'flee'|'retreat'|'post'|'hold', goal}. HP rule 60/90 like defenders.
function healPlan(me, defs, hs, o = {}) {
  const hurt = me.hits < me.hitsMax * 0.6 ? true : me.hits >= me.hitsMax * 0.9 ? false : !!me.hurt;
  const all = defs.concat([me]), pct = f => f.hits / f.hitsMax, dmg = all.filter(f => f.hits < f.hitsMax);
  const adj = dmg.filter(f => rng(f.pos, me.pos) <= 1).sort((a, b) => pct(a) - pct(b))[0], far = dmg.filter(f => rng(f.pos, me.pos) <= 3).sort((a, b) => pct(a) - pct(b))[0];
  const heal = adj ? { act: 'heal', id: adj.id } : far ? { act: 'rangedHeal', id: far.id } : hs.some(h => armed(h) && rng(h.pos, me.pos) <= 4) ? { act: 'heal', id: me.id } : null;
  const r = (move, goal) => ({ hurt, heal, move, goal });
  const melee = hs.find(h => inBase(h) && live(h, 'attack') && rng(h.pos, me.pos) <= 2);
  if (melee) return Object.assign(r('flee', null), { from: melee.pos });
  const towers = o.towers || [], open = o.open || (() => true);
  if (hurt && towers.length) return r('retreat', towers.reduce((a, t) => (rng(t, me.pos) < rng(a, me.pos) ? t : a)));
  const [ix, iy] = HIDLE[Math.min(HIDLE.length - 1, o.idx || 0)], home = { x: ix, y: iy };
  const tgt = defs.filter(d => d.hits < d.hitsMax).sort((a, b) => pct(a) - pct(b))[0];
  if (!tgt) return rng(home, me.pos) === 0 ? r('hold', null) : r('post', home);
  // hurt friendly: already in heal range from a safe tile -> stay; else the safe tile within 3 of it nearest to us (prefer range 2-3)
  if (rng(tgt.pos, me.pos) <= 3 && hSafe(me.pos, hs)) return r('hold', null);
  let best = null, bs = Infinity;
  for (let dx = -3; dx <= 3; dx++) for (let dy = -3; dy <= 3; dy++) { const t = { x: tgt.pos.x + dx, y: tgt.pos.y + dy };
    if (t.x < 1 || t.x > 48 || t.y <= SEAL_Y || t.y > 48 || !open(t.x, t.y) || !hSafe(t, hs)) continue;
    const sc = rng(t, me.pos) * 10 + (rng(t, tgt.pos) <= 1 ? 5 : 0); if (sc < bs) { bs = sc; best = t; } }
  if (best) return rng(best, me.pos) === 0 ? r('hold', null) : r('post', best);
  // no safe tile reaches it: the defender comes back to us (defPlan retreat -> healer); wait at home
  return rng(home, me.pos) === 0 ? r('hold', null) : r('post', home);
}
const raBody = (e, max = 25) => { const k = Math.max(1, Math.min(max, Math.floor(e / 200))); return Array(k).fill('ranged_attack').concat(Array(k).fill('move')); };
// o: {force, towerR (ranges tower -> fight), homeOk, homeCap, w8Cap, inside}
// Misaki 17:45: home ALWAYS sends a baseline of 1 defender while a real (armed) threat is active and home itself is safe, win or lose.
// Local W47N8 defenders = fewest (0-4) that win (no losses) together with the baseline. Extra home defenders (up to 4 total) only if
// the sim says they turn a loss into a win (home iterated from the baseline upward, local 0-4 each). Still unwinnable -> baseline only, no local spawns (never feed a lost fight); inside the seal -> advise safe mode.
const MAXH = 4, MAXL = 4, HEAL_AT = 4; // Misaki 17:56: home max 4, W47N8 local max 4
function plan(o) {
  const fighters = o.force.filter(c => live(c, 'attack') + live(c, 'ranged_attack') > 0);
  if (!fighters.length) return { home: 0, w8: 0, win: true, why: 'unarmed', advise: '' };
  const hb = raBody(o.homeCap || 0), wb = raBody(o.w8Cap || 0, 12), base = o.homeOk ? 1 : 0;
  const wins = defs => { const r = defs.length ? sim(o.force, o.towerR, defs, 0, o) : sim(o.force, o.towerR, wb, 0, o); return r.result === 'win' && !r.lost; };
  // 18:04 (Misaki): a roster of >= 4 combat defenders always includes one dedicated healer (home at max cap if home is safe, else local),
  // counted in the sim
  const hh = o.homeOk ? healBody(o.homeCap || 0) : healBody(o.w8Cap || 0, 12), hl = o.homeOk ? 'home' : 'w8';
  for (let h = base; h <= (o.homeOk ? MAXH : 0); h++)
    for (let n = 0; n <= MAXL; n++) { const four = h + n >= HEAL_AT, defs = Array(h).fill(hb).concat(Array(n).fill(wb)).concat(four ? [hh] : []);
      if (wins(defs)) return { home: h, w8: n, hl: four ? hl : '', win: true, why: h > base ? 'extra home' : 'win', advise: '' }; }
  return { home: base, w8: 0, hl: '', win: false, why: 'unwinnable', advise: o.inside ? 'safemode' : '' };
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
module.exports = { SAFE_HY, hSafe, HEAL_AT, healBody, healPlan, HIDLE, MAXH, MAXL, healAct, segSplit, atkPow, towerPick, sim, assess, defPlan, postTile, POSTS, IDLE, plan, raBody, repairPick, repairStand, COVER, RECYCLE, fromCounts, cls, armed, inBase, FLOOR, SEAL_Y };
