// Duel test for roles.defender (src/roles/remote.js) on real W45N8 terrain vs engine-accurate small Invader bodies.
// Invader AI simplified from engine invaders/findAttack.js: melee chases closest hostile & attacks adjacent; ranged part shoots ≤3.
// Usage: node tests/defender_duel.js  -> prints win rate, ticks, hp left per scenario; exits 1 on a failed expectation.
const fs = require('fs'), path = require('path'), vm = require('vm');
const ROOT = path.join(__dirname, '..');
const T = fs.readFileSync(path.join(ROOT, 'data/terrain_W45N8.txt'), 'utf8');
const wall = (x, y) => x < 0 || y < 0 || x > 49 || y > 49 || T[y * 50 + x] === '1' || T[y * 50 + x] === '3';
const swamp = (x, y) => T[y * 50 + x] === '2';
const DIRS = [[0, 0], [0, -1], [1, -1], [1, 0], [1, 1], [0, 1], [-1, 1], [-1, 0], [-1, -1]];
const rng = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
const BODY = {
  smallMelee: ['tough', 'tough', 'move', 'move', 'move', 'move', 'ranged_attack', 'work', 'attack', 'move'],
  smallRanged: ['tough', 'tough', 'move', 'move', 'move', 'move', 'ranged_attack', 'ranged_attack', 'ranged_attack', 'move'],
  smallHealer: ['move', 'move', 'move', 'move', 'heal', 'heal', 'heal', 'heal', 'heal', 'move'],
  defender: ['ranged_attack', 'ranged_attack', 'ranged_attack', 'ranged_attack', 'ranged_attack', 'move', 'move', 'move', 'move', 'move', 'move', 'heal'] };
class Pos { constructor(x, y, r = 'W45N8') { this.x = x; this.y = y; this.roomName = r; }
  getRangeTo(a) { return rng(this, a.pos || a); } inRangeTo(a, b, r) { return r === undefined ? rng(this, a.pos || a) <= b : rng(this, { x: a, y: b }) <= r; }
  getDirectionTo(a) { const p = a.pos || a, dx = Math.sign(p.x - this.x), dy = Math.sign(p.y - this.y); return DIRS.findIndex(d => d[0] === dx && d[1] === dy) || 1; }
  findClosestByRange(arr) { return arr.slice().sort((a, b) => rng(this, a.pos) - rng(this, b.pos))[0] || null; } }
function mk(type, x, y, owner, boosted) {
  const body = BODY[type].map(t => ({ type: t, hits: 100, boost: boosted }));
  return { name: type + x + y, type, pos: new Pos(x, y), owner: { username: owner }, body, hits: body.length * 100, hitsMax: body.length * 100, fatigue: 0, ticksToLive: 1500, memory: {}, intents: {} };
}
function damage(c, amt) { // tough boost GO: 0.7 taken; damage hits parts front-first
  for (const p of c.body) { if (amt <= 0) break; if (p.hits <= 0) continue; const mult = p.type === 'tough' && p.boost ? 0.7 : 1;
    const eff = Math.min(p.hits, amt * mult); p.hits -= eff; amt -= eff / mult; }
  c.hits = c.body.reduce((s, p) => s + p.hits, 0); }
const act = (c, t) => c.body.filter(p => p.type === t && p.hits > 0).length;
function stepTo(c, x, y, occ, range = 1) { // BFS on real terrain (swamp = 5), first step of shortest path to within range
  const dist = new Map(), prev = new Map(), k0 = c.pos.x * 50 + c.pos.y; dist.set(k0, 0); let q = [k0], goal = null;
  while (q.length && goal === null) { q.sort((a, b) => dist.get(a) - dist.get(b)); const k = q.shift(), cx = Math.floor(k / 50), cy = k % 50;
    if (rng({ x: cx, y: cy }, { x, y }) <= range) { goal = k; break; }
    for (let d = 1; d <= 8; d++) { const nx = cx + DIRS[d][0], ny = cy + DIRS[d][1], nk = nx * 50 + ny;
      if (((nx < 1 || ny < 1 || nx > 48 || ny > 48) && !(range === 0 && nx === x && ny === y)) || wall(nx, ny) || (occ(nx, ny) && rng({ x: nx, y: ny }, c.pos) === 1)) continue;
      const nd = dist.get(k) + (swamp(nx, ny) ? 5 : 1); if (!dist.has(nk) || nd < dist.get(nk)) { if (!dist.has(nk)) q.push(nk); dist.set(nk, nd); prev.set(nk, k); } } }
  if (goal === null || goal === k0) return; let k = goal; while (prev.get(k) !== k0) k = prev.get(k);
  c.intents.move = c.pos.getDirectionTo({ x: Math.floor(k / 50), y: k % 50 }); }
// opt (fixed-start scenarios): at = Invader start, d = defender start, hp / invHp = start hp fraction, still = Invader never moves
function scenario(name, invTypes, boosted, opt = {}) {
  const creeps = [];
  // Invaders spawn on a random exit tile of a non-home side (left side toward our W46N8 is excluded by the engine)
  const sides = ['top', 'right', 'bottom'].map(s => { const t = []; for (let i = 1; i < 49; i++) { const [x, y] = s === 'top' ? [i, 0] : s === 'bottom' ? [i, 49] : [49, i]; if (!wall(x, y)) t.push([x, y]); } return t; }).filter(t => t.length);
  const side = sides[Math.floor(rnd() * sides.length)]; const start = opt.at || side[Math.floor(rnd() * side.length)];
  invTypes.forEach((t, i) => creeps.push(mk(t, Math.min(48, Math.max(1, start[0] + i)), Math.min(48, Math.max(1, start[1])), 'Invader', boosted)));
  const [dx0, dy0] = opt.d || [1, 14], d = mk('defender', dx0, dy0, 'me'); if (opt.hp) damage(d, d.hitsMax * (1 - opt.hp));
  if (opt.invHp) creeps.forEach(v => damage(v, v.hitsMax * (1 - opt.invHp))); d.my = true; d.memory = { role: 'defender', remote: 'W45N8', born: 0 }; creeps.push(d);
  const mem = { pauseUntil: 1e9 };
  const occ = (x, y) => creeps.some(o => o.hits > 0 && o.pos.x === x && o.pos.y === y);
  const room = { name: 'W45N8', find: () => creeps.filter(o => o.hits > 0 && !o.my), getTerrain: () => ({ get: (x, y) => wall(x, y) ? 1 : swamp(x, y) ? 2 : 0 }) };
  d.room = room;
  Object.assign(d, { heal(t) { this.intents.heal = t; return 0; }, rangedAttack(t) { this.intents.ra = t; return 0; },
    move(k) { this.intents.move = k; return 0; }, moveTo(t, o) { stepTo(this, t.pos.x, t.pos.y, occ, o.range || 1); return 0; } });
  const G = { Game: { time: 0, spawns: {}, creeps: {} }, FIND_HOSTILE_CREEPS: 103, FIND_MY_SPAWNS: 112, ATTACK: 'attack', MOVE: 'move', RANGED_ATTACK: 'ranged_attack', HEAL: 'heal',
    TERRAIN_MASK_WALL: 1, TERRAIN_MASK_SWAMP: 2, ERR_NOT_IN_RANGE: -9, RIGHT: 3, LEFT: 7, TOP: 1, BOTTOM: 5, RESOURCE_ENERGY: 'energy' };
  const remoteMock = { CFG: { W45N8: { home: 'W46N8', src: [14, 12], cont: [13, 11], exitHome: [49, 14], exitRemote: [0, 14], park: [46, 21] } }, mem: () => mem, paused: () => true };
  // real FSM drives the defender: observation from the sim each tick (tests/threat_fsm.js covers step() in isolation)
  const TH = require(path.join(ROOT, 'src/managers/threat.js'));
  let th = { st: 'DEFEND', since: 0, def: d.name, seen: 0, last: [] };
  const threatMock = { S: TH.S, cfg: () => TH.DEF, state: () => th, noteRecycle() {} };
  const observe = () => ({ vis: true, players: 0, core: false, hurtNoInv: false, bucket: 10000, armed: true, def: d.hits > 0 ? 'out' : 'dead',
    inv: creeps.filter(c => !c.my && c.hits > 0).map(c => ({ x: c.pos.x, y: c.pos.y, ttl: 1400, heal: act(c, 'heal') > 0, ranged3: act(c, 'ranged_attack') >= 3 })) });
  const moveMock = { to(c, x, y, r) { if (rng(c.pos, { x, y }) > r) stepTo(c, x, y, occ, r); return rng(c.pos, { x, y }) <= r; } };
  const kiteMod = { exports: {} }; vm.runInNewContext(fs.readFileSync(path.join(ROOT, 'src/utils/kite.js'), 'utf8'), Object.assign({}, G, { module: kiteMod })); const kiteM = kiteMod.exports;
  const src = fs.readFileSync(path.join(ROOT, 'src/roles/remote.js'), 'utf8');
  const mod = { exports: {} };
  vm.runInNewContext(src, Object.assign(G, { module: mod, require: p => p.includes('utils/kite') ? kiteM : p.includes('managers/threat') ? threatMock : p.includes('managers/remote') ? remoteMock : p.includes('utils/move') ? moveMock : {} }));
  const role = mod.exports.defender.run;
  let t = 0, retreated = false, dmgTaken = 0, meleeHits = 0;
  for (; t < 400; t++) {
    G.Game.time = t; creeps.forEach(c => c.intents = {});
    const inv = creeps.filter(c => !c.my && c.hits > 0);
    if (!inv.length || d.hits <= 0) break;
    if (d.pos.x === 0 && (d.memory.recycle || d.memory.hurt)) { retreated = true; break; } // stepped onto the exit tile = crossed to W46N8 (Invaders never leave their room; tower heals)
    th = TH.step(th, observe(), TH.DEF, t + 1).s; th.def = d.name;
    role(d);
    if (process.env.TRACE === name && seed0 === +(process.env.RUN || 0)) console.log(t, 'D', d.pos.x, d.pos.y, d.hits, d.fatigue, d.memory.hurt ? 'H' : '', d.intents.move || '', '| I', inv.map(v => [v.pos.x, v.pos.y, v.hits, v.fatigue].join(',')).join(' '));
    for (const v of inv) { // NPC AI
      const r = rng(v.pos, d.pos);
      if (act(v, 'heal')) { const hurt = inv.filter(o => o.hits < o.hitsMax).sort((a, b) => a.hits - b.hits)[0] || inv.find(o => o !== v) || v; if (rng(v.pos, hurt.pos) > 1) stepTo(v, hurt.pos.x, hurt.pos.y, occ); v.intents.healT = hurt; }
      else { if (!opt.still && (act(v, 'attack') || r > 3)) stepTo(v, d.pos.x, d.pos.y, occ); else if (r < 3) { /* ranged-only flee to 3 */ const k = d.pos.getDirectionTo(v); const nx = v.pos.x + DIRS[k][0], ny = v.pos.y + DIRS[k][1]; if (!wall(nx, ny) && !occ(nx, ny)) v.intents.move = k; }
        if (r <= 1 && act(v, 'attack')) v.intents.att = 30 * act(v, 'attack') * (boosted ? 2 : 1);
        if (r <= 3) v.intents.ra = 10 * act(v, 'ranged_attack') * (boosted ? 2 : 1); }
    }
    // resolve damage then heal then movement (fatigue)
    if (d.intents.ra && d.intents.ra.hits > 0 && rng(d.pos, d.intents.ra.pos) <= 3) damage(d.intents.ra, 10 * act(d, 'ranged_attack'));
    for (const v of inv) { if (v.intents.att) meleeHits++; const x = (v.intents.att || 0) + (v.intents.ra || 0); if (x) { const h = d.hits; damage(d, x); dmgTaken += h - d.hits; } }
    for (const v of inv) if (v.intents.healT && v.intents.healT.hits > 0) { const tgt = v.intents.healT; const amt = (rng(v.pos, tgt.pos) <= 1 ? 12 : 4) * act(v, 'heal') * (boosted ? 2 : 1); tgt.hits = Math.min(tgt.hitsMax, tgt.hits + amt); let a = amt; for (const p of tgt.body.slice().reverse()) { const add = Math.min(100 - p.hits, a); p.hits += add; a -= add; } }
    if (d.intents.heal) { let a = 12 * act(d, 'heal'); for (const p of d.body.slice().reverse()) { const add = Math.min(100 - p.hits, a); p.hits += add; a -= add; } d.hits = d.body.reduce((s, p) => s + p.hits, 0); }
    for (const c of creeps) { if (c.hits <= 0) continue; // engine order: move needs fatigue 0 at tick start; fatigue drops at tick end
      if (c.intents.move && !c.fatigue) { const nx = c.pos.x + DIRS[c.intents.move][0], ny = c.pos.y + DIRS[c.intents.move][1];
        if (!wall(nx, ny) && !occ(nx, ny) && ((nx >= 1 && ny >= 1 && nx <= 48 && ny <= 48) || (c === d && nx === 0 && ny === 14))) { c.pos = new Pos(nx, ny); const heavy = c.body.filter(p => p.type !== 'move').length; c.fatigue = (swamp(nx, ny) ? 10 : 2) * heavy; } }
      c.fatigue = Math.max(0, c.fatigue - 2 * act(c, 'move')); }
  }
  const won = creeps.filter(c => !c.my).every(c => c.hits <= 0) && d.hits > 0;
  return { name, won, retreated: retreated || !!d.memory.recycle, ticks: t, hpLeft: d.hits, dmgTaken, meleeHits };
}
const results = [];
// 2026-10-15 incident (defender83647721 died): boosted smallMelee camping the west exit pocket at (1,17); defender enters on the exit tile
// 'exit camp*': the pocket is ringed by swamp (no kiting possible at equal speed): fight from the edge/exit-adjacent tiles, step out
// when hurt, never flee deeper (old code walked north into swamp, then home through the Invader). 'hurt*': a hurt defender must not
// walk home through the melee (zero melee hits). 'range 4': approach + chase must not collapse to melee (zero melee hits).
const CAMP = { at: [1, 17] }; let seed0 = 0; // seed0: run index (TRACE=<scenario> [RUN=i] prints that run per tick)
for (const [name, inv, boost, expect, opt, maxMelee] of [['smallMelee', ['smallMelee'], false, 'win', undefined, 0], ['smallMelee boosted', ['smallMelee'], true, 'win', undefined, 0],
  ['melee+ranged', ['smallMelee', 'smallRanged'], false, 'retreat'], ['melee+healer', ['smallMelee', 'smallHealer'], false, 'retreat'],
  ['exit camp boosted', ['smallMelee'], true, 'either', Object.assign({ d: [0, 14] }, CAMP), 8],
  ['exit camp boosted @x1', ['smallMelee'], true, 'either', Object.assign({ d: [1, 14] }, CAMP), 8],
  ['hurt flee past camp', ['smallMelee'], true, 'either', Object.assign({ d: [3, 11], hp: 0.58 }, CAMP), 0],
  // diag (not asserted): hurt in open terrain with the chaser between us and home. Equal speed + its chip (20) > our heal (12)
  // wears down the MOVE parts (front of the damage queue once RA is gone) -> caught. Not reachable when engage takes 0 melee hits.
  ['diag: hurt, melee between us & exit', ['smallMelee'], true, 'diag', { at: [13, 10], d: [15, 9], hp: 0.58 }],
  ['camp re-entry, Invader adjacent', ['smallMelee'], true, 'either', { at: [1, 15], d: [0, 14], invHp: 0.6 }, 8],
  ['melee not chasing (busy), range 6', ['smallMelee'], true, 'win', { at: [21, 9], d: [15, 9], still: true }, 0],
  ['healthy, melee at range 4', ['smallMelee'], true, 'win', { at: [19, 9], d: [15, 9] }, 0]]) {
  const runs = []; for (let i = 0; i < 20; i++) { seed0 = i; runs.push(scenario(name, inv, boost, opt)); }
  const wins = runs.filter(r => r.won).length, ret = runs.filter(r => r.retreated && !r.won).length, dead = runs.filter(r => r.hpLeft <= 0).length;
  const med = a => a.sort((x, y) => x - y)[a.length >> 1];
  const r = { name, expect, wins, retreats: ret, defenderDied: dead, medTicks: med(runs.map(r => r.ticks)), medHpLeft: med(runs.map(r => r.hpLeft)), medDmgTaken: med(runs.map(r => r.dmgTaken)), maxMeleeHits: Math.max(...runs.map(r => r.meleeHits)) };
  r.ok = expect === 'diag' || dead <= (opt ? 0 : 1) && (expect === 'win' ? wins + ret >= 19 && wins >= 14 : expect === 'either' ? wins + ret === 20 : ret >= 18)
    && (maxMelee === undefined || r.maxMeleeHits <= maxMelee); results.push(r);
}
console.table(results);
fs.writeFileSync(path.join(ROOT, 'metrics/defender_duel.json'), JSON.stringify(results, null, 1));
process.exit(results.every(r => r.ok) ? 0 : 1);
