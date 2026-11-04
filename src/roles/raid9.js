// W47N9 wartime east-line assault (Misaki GO). Continuous field, not a 6-creep wave.
// Memory.ops.w47n9 is read every tick (flip knobs without redeploy). Per-creep
// Memory.creeps[name].raidOrder overrides that creep until clear or until.
// NEVER calls activateSafeMode. Arm/abort is manual: tools/raid9.py (do not arm from a cloud agent).
//
// Field max d:4 m:6 r:6 h:10. Squad mode (default): spawn balanced d+m+h (r optional).
// GO once a full squad (need.d/m/h, default 1/1/1) is on the W47N8 north lip or in W47N9.
// Enter together — do not trickle in alone. noOverrun (default) skips armed-parts flee.
// Entry only (38,49). Swamp (38,47) is not walked; path via (37,47) or (39,47).
// Pre-breach: max maxY43 dismantlers on y=43, and only on a seal whose dismantle dps
// beats minDps (default 1240, two towers repairing). A mouth that would be left with
// a single 24W (1200 dps) stays closed.
const MV = require('../utils/move');
const TARGET = 'W47N9', STAGE = 'W47N8', HOME = 'W46N8';
const ENTRY = { x: 38, y: 49 };
const SWAMP = { x: 38, y: 47 };
const MOUTH_DUAL = [{ x: 38, y: 42 }, { x: 39, y: 42 }];
const MOUTH_WIDE = [{ x: 37, y: 42 }, { x: 38, y: 42 }, { x: 39, y: 42 }, { x: 40, y: 42 }];
const TOWER_ORDER = [{ x: 39, y: 37 }, { x: 34, y: 28 }]; // T1 then T2; P.towerOrder replaces
const LANE = [37, 38, 39, 40];
const MAX = { d: 4, m: 6, r: 6, h: 10 };
const NEED = { d: 1, m: 1, r: 0, h: 1 }; // GO = one full squad (d+m+h) on the lip / in room
const MIN_DPS = 1240; // ~2 tower repair / tick. One 24W dismantles at 1200 and loses.
const DISMANTLE_HITS = 50; // per WORK per tick
const WORKS = 24;
const DPS_ONE = WORKS * DISMANTLE_HITS; // 1200
const PULL_SOFT = 0.70, PULL_HARD = 0.45;
const MAX_Y43 = 2;
const NEAR_EXIT = 3;
const EM_TICKS = 3, EM_COOL = 5;
const UP_SAFE = 20000; // match managers/walls.js — one upgrader if the controller is about to downgrade
const PREFER = { [HOME]: ['d', 'm', 'r', 'h'], [STAGE]: ['h', 'd', 'm', 'r'] };
const PRIO = ['fight', 'filler', 'towerRampart', 'tower', 'blocker', 'econ'];
const LADDER = ['breach', 'punch', 'inside_towers', 'inside_clean'];
const COST = { tough: 10, move: 50, work: 100, attack: 80, ranged_attack: 150, heal: 250, carry: 50 };
const SKIP = new Set(['road', 'container', 'controller', 'extractor', 'keeperLair', 'portal', 'source', 'mineral']);
const ND = { noDetour: true };
const GARRISON = [[30, 4], [31, 4], [30, 5], [31, 5], [32, 5], [29, 5]];
// RCL7 energyCapacityAvailable is 5300. 18H18M is 5400, so the spawned healer is the
// largest 1:1 body that fits the room cap (17H17M = 5100 at 5300). HEALER() is the spec body.
const rep = (n, p) => Array(Math.max(0, n)).fill(p);
const DISMANTLER = () => [].concat(rep(2, TOUGH), rep(WORKS, WORK), rep(WORKS, MOVE)); // 2T24W24M = 3620
const MELEE = () => [].concat(rep(2, TOUGH), rep(24, ATTACK), rep(24, MOVE));          // 2T24A24M = 3140
const RANGED = () => [].concat(rep(15, RANGED_ATTACK), rep(15, MOVE), [HEAL]);         // 15RA15M1H = 3250
const HEALER = () => [].concat(rep(18, HEAL), rep(18, MOVE));                          // 18H18M = 5400 spec
const costOf = body => (body || []).reduce((a, p) => a + (COST[p] || 0), 0);
function healBody(cap) {
  const limit = cap > 0 ? cap : 5300;
  let n = 18;
  while (n > 1 && n * 300 > limit) n--;
  return [].concat(rep(n, HEAL), rep(n, MOVE));
}
function bodyFor(kind, cap) {
  const limit = cap > 0 ? cap : 5300;
  if (kind === 'h') return healBody(limit);
  const fat = kind === 'd' ? DISMANTLER() : kind === 'm' ? MELEE() : kind === 'r' ? RANGED() : null;
  if (!fat || costOf(fat) > limit) return null;
  return fat;
}
const M = () => { const o = Memory.ops || (Memory.ops = {}); return o.w47n9 || (o.w47n9 = {}); };
const rng = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
const normPos = p => p ? { x: p.x | 0, y: p.y | 0 } : null;
const gSlotOf = k => GARRISON[(k | 0) % GARRISON.length];
const allRaid = () => _.filter(Game.creeps, x => x.memory && x.memory.role === 'raid9');
function raidActive(P) {
  return !!(P && P.on === true && !P.safe && !P.garrison && !P.flee && !(P.safeUntil && Game.time < P.safeUntil));
}
// Explicit pauseCivilians wins over `on`. Default: pause development while the assault is live.
function pauseCivilians() {
  if (typeof Memory === 'undefined' || !Memory || !Memory.ops) return false;
  const P = Memory.ops.w47n9;
  if (!P) return false;
  if (P.pauseCivilians === false) return false;
  if (P.pauseCivilians === true) return true;
  return P.on === true && !P.safe && !P.garrison && !P.flee && !(P.safeUntil && Game.time < P.safeUntil);
}
function upgraderKeep(room) {
  const ttl = room && room.controller && room.controller.ticksToDowngrade;
  return ttl && ttl < UP_SAFE ? 1 : 0;
}
function applyPause(T, room) {
  if (!T || !pauseCivilians()) return T;
  T.builder = 0;
  const keep = upgraderKeep(room);
  T.upgrader = keep ? Math.min(T.upgrader || 0, keep) : 0;
  return T;
}
// Colony soft-kill list: every builder, upgraders past the downgrade keep. Home builders use recycleCivilian.
function namesToRecycle(rows, keepUp) {
  const ups = (rows || []).filter(r => r && (r.role === 'w8upgrader' || r.role === 'upgrader') && !r.spawning)
    .sort((a, b) => (b.ttl | 0) - (a.ttl | 0));
  const bld = (rows || []).filter(r => r && (r.role === 'w8builder' || r.role === 'builder') && !r.spawning);
  const keep = Math.max(0, keepUp | 0);
  return ups.slice(keep).concat(bld).map(r => r.name).filter(Boolean);
}
function recycleCivilian(c) {
  if (!c || !c.memory || c.memory.role !== 'builder' || !pauseCivilians()) return false;
  const home = c.memory.home || (c.room && c.room.name);
  const mine = _.filter(Game.spawns, s => s.my);
  const sp = mine.filter(s => !home || s.pos.roomName === home)[0] || mine[0];
  if (!sp) return false;
  if (c.pos && c.pos.roomName === sp.pos.roomName && c.pos.isNearTo(sp)) sp.recycleCreep(c);
  else c.moveTo(sp, { range: 1, reusePath: 12 });
  return true;
}
function fieldCaps(P) {
  return {
    max: Object.assign({}, MAX, (P && P.max) || {}),
    need: Object.assign({}, NEED, (P && P.need) || {}),
  };
}
function wantKind(roomName, have, max, cap) {
  // Memory.ops.w47n9.preferHome / preferStage override hardcoded PREFER.
  const P = typeof Memory !== 'undefined' && Memory.ops && Memory.ops.w47n9;
  const key = roomName === HOME ? 'preferHome' : roomName === STAGE ? 'preferStage' : null;
  const order = (key && P && Array.isArray(P[key]) && P[key].length) ? P[key] : (PREFER[roomName] || PREFER[HOME]);
  // Squad mode (default ON): keep d/m/h within 1; on ties prefer m then d then h — never flood healers/work with 0 attack.
  // Set Memory.ops.w47n9.squad=false to fall back to prefer/alternate lists. Misaki 2026-11-04.
  if (!P || P.squad !== false) {
    const core = ['m', 'd', 'h'].filter(k => (max[k] || 0) > 0 && bodyFor(k, cap) && (have[k] || 0) < (max[k] || 0));
    if (core.length) {
      const rank = { m: 0, d: 1, h: 2 };
      core.sort((a, b) => {
        const ha = have[a] || 0, hb = have[b] || 0;
        if (ha !== hb) return ha - hb;
        return (rank[a] != null ? rank[a] : 9) - (rank[b] != null ? rank[b] : 9);
      });
      return core[0];
    }
    if ((max.r || 0) > 0 && bodyFor('r', cap) && (have.r || 0) < (max.r || 0)) return 'r';
    return null;
  }
  // alternate=true: interleave under-cap kinds from prefer list.
  if (P && P.alternate) {
    const pool = (order && order.length) ? order.slice() : ['d', 'm', 'r', 'h'];
    const atk = pool.filter(k => (have[k] || 0) < (max[k] || 0) && bodyFor(k, cap));
    if (atk.length === 1) return atk[0];
    if (atk.length > 1) {
      atk.sort((a, b) => (have[a] || 0) - (have[b] || 0));
      if ((have[atk[0]] || 0) < (have[atk[1]] || 0)) return atk[0];
      const last = P.lastKind;
      const nxt = atk.filter(k => k !== last);
      return (nxt.length ? nxt[0] : atk[0]);
    }
  }
  for (const k of order) {
    if ((have[k] || 0) >= (max[k] || 0)) continue;
    if (!bodyFor(k, cap)) continue;
    return k;
  }
  return null;
}
// Wartime storage floors (strategy 2026-11-02 14:4x): fat WAVE bodies must not starve queens/towers.
// Home 12k = emergency under reserveE 15k; colony 15k = LEAN_ARM. Missing storage → allow (tests / pre-storage).
// Override: Memory.ops.w47n9.storFloorHome / storFloorStage. Never auto safe-mode.
const WAR_STOR = { home: 12000, stage: 15000 };
function warFloor(room) {
  const P = Memory.ops && Memory.ops.w47n9;
  if (room && room.name === HOME) return (P && P.storFloorHome != null) ? P.storFloorHome : WAR_STOR.home;
  if (room && room.name === STAGE) return (P && P.storFloorStage != null) ? P.storFloorStage : WAR_STOR.stage;
  return WAR_STOR.stage;
}
function warStorOk(room) {
  if (!room || !room.storage || !room.storage.store) return true;
  return (room.storage.store.energy || 0) >= warFloor(room);
}
// avail < fat cost → {defer:true}. Caller spawns a due logistics creep instead of idling on this body.
// Spawn still banks once miners/haulers/fillers/remotes are met (that is the only way a 3620+ body builds).
function wantSpawn(room, avail) {
  const P = Memory.ops && Memory.ops.w47n9;
  if (!raidActive(P) || !room || (P && P.pauseSpawn)) return null;
  if (room.name !== HOME && room.name !== STAGE) return null;
  // Protect economy floors once storage exists (Overmind warSpawnCutoff / TooAngel underSiege pattern).
  if (!warStorOk(room)) return null;
  const { max } = fieldCaps(P);
  const cap = room.energyCapacityAvailable || 5300;
  const alive = allRaid();
  const have = _.countBy(alive, c => (c.memory && c.memory.kind) || 'm');
  const kind = wantKind(room.name, have, max, cap);
  if (!kind) return null;
  const body = bodyFor(kind, cap);
  const cost = costOf(body);
  const used = new Set(alive.filter(c => c.memory.kind === kind).map(c => c.memory.k | 0));
  let slot = 0; while (used.has(slot)) slot++;
  const mem = { role: 'raid9', home: room.name, k: slot, kind, born: Game.time };
  const haveE = avail != null ? avail : room.energyAvailable;
  if (haveE != null && haveE < cost) return { defer: true, role: 'raid9', body, mem, cost, kind };
  return { role: 'raid9', body, mem, cost, kind };
}
function noteSpawned(kind) {
  const P = M();
  P.n = (P.n | 0) + 1;
  if (kind === 'd' || kind === 'm' || kind === 'r' || kind === 'h') P.lastKind = kind;
}
function mouthsOf(P, phase) {
  const base = (P && P.mouths && P.mouths.length) ? P.mouths.map(normPos)
    : (phase === 'inside_towers' || phase === 'inside_clean' ? MOUTH_WIDE : MOUTH_DUAL).map(p => ({ x: p.x, y: p.y }));
  const f = P && P.focusSeal ? normPos(P.focusSeal) : null;
  if (!f) return base;
  return [f].concat(base.filter(m => m.x !== f.x || m.y !== f.y));
}
// Open a mouth only when `need` dismantlers can stand on it. Left-over singles stay in reserve.
function assignSeals(dCount, mouths, minDps, dpsOne, maxFront) {
  const dps = Math.max(1, dpsOne || DPS_ONE);
  const need = Math.max(1, Math.ceil((minDps == null ? MIN_DPS : minDps) / dps));
  const front = Math.max(0, Math.min(dCount | 0, maxFront == null ? MAX_Y43 : maxFront));
  const open = [];
  let left = front;
  for (const m of mouths || []) {
    if (left < need) break;
    open.push({ x: m.x, y: m.y, n: need });
    left -= need;
  }
  return { open, need, reserve: (dCount | 0) - open.reduce((a, m) => a + m.n, 0), front };
}
function frontSlots(mouth, n) {
  const xs = [mouth.x, mouth.x - 1, mouth.x + 1, mouth.x - 2, mouth.x + 2].filter(x => x >= 37 && x <= 40);
  const out = [];
  for (let i = 0; i < xs.length && out.length < n; i++) out.push({ x: xs[i], y: 43 });
  while (out.length < n) out.push({ x: mouth.x, y: 43 });
  return out;
}
function assignment(list, opt) {
  opt = opt || {};
  const maxY = opt.maxY43 == null ? MAX_Y43 : opt.maxY43;
  const asg = assignSeals(list.filter(c => c.kind === 'd').length, opt.mouths || MOUTH_DUAL, opt.minDps, opt.dps || DPS_ONE, maxY);
  const ds = list.filter(c => c.kind === 'd').sort((a, b) => (a.k | 0) - (b.k | 0));
  const out = {};
  let di = 0;
  for (const m of asg.open) {
    const slots = frontSlots(m, m.n);
    for (let s = 0; s < m.n && di < ds.length; s++, di++) out[ds[di].id] = { x: slots[s].x, y: 43, row: 'front', mouth: m };
  }
  for (; di < ds.length; di++) out[ds[di].id] = { x: LANE[di % 4], y: 45, row: 'reserve' };
  for (const c of list) {
    if (c.kind === 'd') continue;
    const x = LANE[(c.k | 0) % 4];
    if (c.kind === 'm') out[c.id] = { x, y: 44, row: 'melee' };
    else if (c.kind === 'r') out[c.id] = { x, y: 46, row: 'ranged' };
    else {
      // y47–48, never the swamp tile (38,47)
      let y = (c.k | 0) % 2 ? 48 : 47;
      if (x === SWAMP.x && y === SWAMP.y) y = 48;
      out[c.id] = { x, y, row: 'heal' };
    }
  }
  return { posts: out, seals: asg };
}
// On the swamp tile, or about to step onto it: sidestep to 37,47 or 39,47 (closer to the goal x).
function swampStep(from, goal) {
  if (!from || from.x !== SWAMP.x || from.y !== SWAMP.y) return null;
  const a = 37, b = 39;
  const pick = !goal ? a : (Math.abs(goal.x - a) <= Math.abs(goal.x - b) ? a : b);
  return { x: pick, y: 47 };
}
function stepOntoSwamp(from, goal) {
  if (!from || !goal) return false;
  const dx = Math.sign(goal.x - from.x), dy = Math.sign(goal.y - from.y);
  return from.x + dx === SWAMP.x && from.y + dy === SWAMP.y;
}
function pullMode(ratio, soft, hard) {
  if (ratio <= hard) return 'hard';
  if (ratio <= soft) return 'soft';
  return null;
}
function inApproach(c) {
  if (!c || !c.room || !c.pos || c.spawning) return false;
  if (c.room.name === TARGET) return true;
  return c.room.name === STAGE && c.pos.y <= NEAR_EXIT;
}
// Full squad on the lip / in room before GO. Defaults need 1d+1m+1h (r only if need.r>0).
// Prevents lone dismantlers/healers rushing the breach with no attack escort. Misaki 2026-11-04.
function assaultReady(creeps, need) {
  const nd = (need && need.d != null) ? need.d : NEED.d;
  const nm = (need && need.m != null) ? need.m : NEED.m;
  const nh = (need && need.h != null) ? need.h : NEED.h;
  const nr = (need && need.r != null) ? need.r : NEED.r;
  let d = 0, m = 0, h = 0, r = 0;
  for (const c of creeps || []) {
    if (!inApproach(c)) continue;
    const k = (c.memory && c.memory.kind) || 'm';
    if (k === 'd') d++;
    else if (k === 'm') m++;
    else if (k === 'h') h++;
    else if (k === 'r') r++;
  }
  return d >= nd && m >= nm && h >= nh && r >= nr;
}
function shouldRegroup(alive) {
  if (!alive || !alive.length) return true;
  for (const c of alive) {
    if (c.room && c.room.name === TARGET) return false;
    const k = (c.memory && c.memory.kind) || 'm';
    if ((k === 'd' || k === 'm' || k === 'r') && inApproach(c)) return false;
  }
  return true;
}
function syncGo(P, alive) {
  if (!raidActive(P)) return;
  const need = fieldCaps(P).need;
  if (P.go && shouldRegroup(alive)) delete P.go;
  else if (!P.go && assaultReady(alive, need)) P.go = Game.time;
}
function observe(world, mouths, ours) {
  const focus = (mouths && mouths[0]) || MOUTH_DUAL[0];
  const structs = (world && world.structs) || [];
  const sealUp = structs.some(s => (s.structureType === 'rampart' || s.structureType === 'constructedWall')
    && s.pos && s.pos.x === focus.x && s.pos.y === focus.y && (s.hits || 0) > 0);
  const towers = structs.filter(s => s.structureType === 'tower' && (s.hits == null || s.hits > 0));
  const inside = (ours || []).some(c => c && c.pos && c.pos.y < 42 && (c.room ? c.room.name === TARGET : c.inRoom !== false));
  let phase = 'breach';
  if (inside && !towers.length) phase = 'inside_clean';
  else if (inside) phase = 'inside_towers';
  else if (!sealUp) phase = 'punch';
  return { phase, sealUp, towers: towers.length, inside };
}
// Auto-advance only. Operator phase sticks until the world reaches a later ladder step.
// flee / garrison / safe (and an operator phase of fallback) hold fallback.
function syncPhase(P, obs) {
  if (!P) return 'breach';
  if (P.flee || P.garrison || P.safe || (P.safeUntil && Game.time < P.safeUntil)) { P.phase = 'fallback'; return P.phase; }
  if (P.phase === 'fallback') return 'fallback';
  const want = (obs && obs.phase) || 'breach';
  const cur = LADDER.indexOf(P.phase), nxt = LADDER.indexOf(want);
  if (cur < 0) P.phase = want;
  else if (nxt > cur) P.phase = want;
  return P.phase || 'breach';
}
function towerIndex(pos, order) {
  const list = order && order.length ? order : TOWER_ORDER;
  for (let i = 0; i < list.length; i++) {
    const t = list[i];
    if (t && (t.id && t.id === pos.id)) return i;
    if (t && t.x === pos.x && t.y === pos.y) return i;
  }
  return 50 + pos.x + pos.y;
}
function creepClass(h, towers) {
  if (!h) return 'econ';
  if (h.armed) return 'fight';
  const near = h.nearTower || (towers || []).some(t => rng(h.pos, t.pos || t) <= 1);
  return near ? 'filler' : 'econ';
}
function structClass(s, towers) {
  if (!s || SKIP.has(s.structureType)) return null;
  if (s.structureType === 'tower') return 'tower';
  const onTower = s.towerTile || (towers || []).some(t => t.pos && t.pos.x === s.pos.x && t.pos.y === s.pos.y)
    || (towers || []).some(t => t.x === s.pos.x && t.y === s.pos.y);
  if ((s.structureType === 'rampart' || s.structureType === 'constructedWall') && onTower) return 'towerRampart';
  if (s.structureType === 'rampart' || s.structureType === 'constructedWall') return 'blocker';
  return 'econ';
}
function candidates(me, w, opt) {
  const towers = (w.structs || []).filter(s => s.structureType === 'tower');
  const order = opt.towerOrder;
  const out = [];
  for (const h of w.creeps || []) {
    const cls = creepClass(h, towers);
    out.push({ id: h.id, pos: h.pos, cls, order: cls === 'fight' ? 0 : 1, hits: h.hits || 0 });
  }
  for (const s of w.structs || []) {
    const cls = structClass(s, towers);
    if (!cls) continue;
    out.push({ id: s.id, pos: s.pos, cls, order: cls === 'tower' ? towerIndex(s.pos, order) : 0, hits: s.hits || 0 });
  }
  return out;
}
function pickInside(me, w, opt) {
  opt = opt || {};
  const prio = (opt.prio && opt.prio.length) ? opt.prio : PRIO;
  const rank = cls => { const i = prio.indexOf(cls); return i < 0 ? 99 : i; };
  const cands = candidates(me, w, opt);
  if (!cands.length) return null;
  let best = 99;
  for (const c of cands) best = Math.min(best, rank(c.cls));
  if (opt.sticky) {
    const s = cands.find(c => c.id === opt.sticky);
    if (s && rank(s.cls) === best) return { id: s.id, pri: rank(s.cls), cls: s.cls };
  }
  const pool = cands.filter(c => rank(c.cls) === best);
  const t = _.min(pool, c => (c.order | 0) * 1e6 + rng(me, c.pos) * 1e3 + (c.hits | 0));
  return t && t.id ? { id: t.id, pri: rank(t.cls), cls: t.cls } : null;
}
function pickBreach(w, mouth) {
  if (!mouth) return null;
  const bars = (w.structs || []).filter(s => (s.structureType === 'rampart' || s.structureType === 'constructedWall')
    && s.pos && s.pos.x === mouth.x && s.pos.y === mouth.y && (s.hits || 0) > 0);
  if (!bars.length) return null;
  return { id: bars[0].id, pri: 0, cls: 'seal' };
}
function pickPunch(me, w, mouth, opt) {
  const on = (w.creeps || []).filter(h => h.pos && h.armed && mouth && h.pos.y === mouth.y && Math.abs(h.pos.x - mouth.x) <= 1);
  if (on.length) return { id: _.min(on, h => (h.hits | 0)).id, pri: 0, cls: 'fight' };
  const bar = pickBreach(w, mouth);
  if (bar) return bar;
  return pickInside(me, w, opt);
}
function pick(me, w, opt) {
  opt = opt || {};
  const phase = opt.phase || 'inside_towers';
  if (phase === 'breach') {
    // Seal first; once open (or gone) work 见什么拆什么 — smash fight/tower/blocker via inside prio.
    const seal = pickBreach(w, opt.mouth || MOUTH_DUAL[0]);
    if (seal) return seal;
    return pickInside(me, w, opt);
  }
  if (phase === 'punch') return pickPunch(me, w, opt.mouth || MOUTH_DUAL[0], opt);
  return pickInside(me, w, opt);
}
function shouldYield(pos, kind, mates, focus) {
  if (!focus || kind === 'd' || kind === 'm') return false;
  const my = rng(pos, focus);
  return (mates || []).some(m => {
    const k = (m.memory && m.memory.kind) || m.kind;
    const p = m.pos;
    return p && (k === 'd' || k === 'm') && rng(p, focus) > my;
  });
}
function manualOrder(c) {
  const o = c && c.memory && c.memory.raidOrder;
  if (!o) return null;
  if (o.clear || (o.until && Game.time > o.until)) { delete c.memory.raidOrder; return null; }
  return o;
}
function useMass(me, inR) {
  if (inR.length >= 3) return true;
  return _.sum(inR, h => { const r = rng(me, h.pos); return r <= 1 ? 10 : r === 2 ? 4 : 1; }) > 10;
}
const HEAL_URGENT = 0.6;
// Most-damaged each tick (no sticky lock). Includes self so hurt healers self-heal.
// Misaki 2026-11-04: rotate by ratio; never pin one id.
function healPlan(me, mates) {
  const hurt = [me].concat(mates || []).filter(x => x && x.hits < x.hitsMax);
  if (!hurt.length) return null;
  const t = hurt.reduce((a, x) => (x.hits / x.hitsMax < a.hits / a.hitsMax ? x : a));
  const r = t === me ? 0 : rng(me.pos, t.pos);
  return { id: t.id, ratio: t.hits / t.hitsMax, mode: r <= 1 ? 'heal' : r <= 3 ? 'ranged' : 'far', pos: t.pos };
}
// Full throughput: heal() on best adjacent (or self) AND rangedHeal() on best in 1-3.
// Separate intents — fire both every tick. Misaki 2026-11-04 furious.
function healDual(c, mates) {
  if (!c.getActiveBodyparts(HEAL)) return null;
  const hurt = [c].concat(mates || []).filter(x => x && x.hits < x.hitsMax)
    .sort((a, b) => a.hits / a.hitsMax - b.hits / b.hitsMax);
  if (!hurt.length) {
    // Pre-heal: top nearest front even when full squad.
    if (c.memory.kind === 'h') {
      const f = c.pos.findInRange(FIND_MY_CREEPS, 3).filter(x => x.memory && (x.memory.kind === 'd' || x.memory.kind === 'm'));
      const pf = f.length ? _.min(f, x => rng(c.pos, x.pos)) : null;
      if (pf) {
        if (c.pos.isNearTo(pf)) c.heal(pf);
        if (c.pos.inRangeTo(pf, 3)) c.rangedHeal(pf);
      }
    }
    return null;
  }
  const adj = hurt.find(x => x === c || c.pos.isNearTo(x));
  if (adj) c.heal(adj);
  else if (c.hits < c.hitsMax) c.heal(c);
  const ranged = hurt.find(x => x !== c && c.pos.inRangeTo(x, 3) && (!adj || x !== adj));
  if (ranged) c.rangedHeal(ranged);
  else if (!adj) {
    const only = hurt.find(x => x !== c && c.pos.inRangeTo(x, 3));
    if (only) c.rangedHeal(only);
  }
  return healPlan(c, mates);
}
function armedParts(creeps) {
  let n = 0;
  for (const h of creeps) n += (h.attack | 0) + (h.ranged | 0);
  return n;
}
// Only auto-flee when hostile ATTACK+RA parts are overwhelming AND noOverrun===false.
// Operator Memory.flee (abort) and enemy Safe Mode still garrison. Misaki 2026-11-04.
function overrun(room) {
  const P = typeof Memory !== 'undefined' && Memory.ops && Memory.ops.w47n9;
  if (!P || P.noOverrun !== false) return false; // default OFF unless explicitly noOverrun=false
  const min = (P.overrunMin != null) ? P.overrunMin : 40;
  return armedParts(room.find(FIND_HOSTILE_CREEPS).map(h => ({
    attack: h.getActiveBodyparts(ATTACK), ranged: h.getActiveBodyparts(RANGED_ATTACK),
  }))) >= min;
}
// Stale flee.why=overrun from older LIVE builds must not keep the squad in garrison when noOverrun is on.
function clearStaleOverrun(P) {
  if (!P || P.noOverrun === false) return false;
  if (!(P.flee && P.flee.why === 'overrun')) return false;
  delete P.flee;
  delete P.garrison;
  if (P.phase === 'fallback') P.phase = 'breach';
  return true;
}
function squad(c) { return c.room.find(FIND_MY_CREEPS).filter(x => x !== c && x.memory && x.memory.role === 'raid9'); }
function world(room) {
  const hc = room.find(FIND_HOSTILE_CREEPS);
  const towers = room.find(FIND_HOSTILE_STRUCTURES).filter(s => s.structureType === STRUCTURE_TOWER);
  const near = h => towers.some(t => h.pos.inRangeTo(t, 1));
  return {
    creeps: hc.map(h => ({
      id: h.id, pos: h.pos, energy: (h.store && h.store[RESOURCE_ENERGY]) || 0, hits: h.hits,
      armed: h.getActiveBodyparts(ATTACK) + h.getActiveBodyparts(RANGED_ATTACK) + h.getActiveBodyparts(HEAL) + h.getActiveBodyparts(WORK) > 0,
      nearTower: near(h),
    })),
    structs: room.find(FIND_HOSTILE_STRUCTURES).map(s => ({
      id: s.id, pos: s.pos, structureType: s.structureType, hits: s.hits,
      towerTile: towers.some(t => t.pos.x === s.pos.x && t.pos.y === s.pos.y),
    })),
    hc,
  };
}
// Same-tick friendly swap/pull. Screeps lets A enter B's tile when B moves out (or into A's)
// this tick — without this, raid creeps jam the mouth/tower lanes and healers never stick.
// Misaki 2026-11-04: "creep 可以互相交换位置的。不要傻傻的"
// Last move() wins per creep: if A swaps with B then B's later run() overwrites B.move,
// the swap dies. YIELD records the partner's required step so honorYield locks it in.
const OPP_DIR = { 1: 5, 2: 6, 3: 7, 4: 8, 5: 1, 6: 2, 7: 3, 8: 4 };
let yieldTick = -1;
const YIELD = Object.create(null); // creepId -> {x,y} they must step to this tick
function resetYield() {
  if (yieldTick === Game.time) return;
  for (const k in YIELD) delete YIELD[k];
  yieldTick = Game.time;
}
function honorYield(c) {
  resetYield();
  if (!c || c.fatigue) return false;
  const y = YIELD[c.id];
  if (!y) return false;
  const dir = c.pos.getDirectionTo(y.x, y.y);
  delete YIELD[c.id];
  if (!dir) return false;
  c.move(dir);
  return true;
}
function stepFriend(c, nx, ny) {
  resetYield();
  if (!c || c.fatigue || nx == null || ny == null) return false;
  if (nx < 0 || nx > 49 || ny < 0 || ny > 49) return false;
  if (c.room.getTerrain().get(nx, ny) === TERRAIN_MASK_WALL) return false;
  const dir = c.pos.getDirectionTo(nx, ny);
  if (!dir) return false;
  const b = c.room.lookForAt(LOOK_CREEPS, nx, ny)[0];
  if (!b) { c.move(dir); return true; }
  if (!b.my || b.fatigue) return false;
  // Mutual swap this tick: B must enter our tile even if B.run() has not finished / already ran.
  YIELD[b.id] = { x: c.pos.x, y: c.pos.y };
  b.move(OPP_DIR[dir]);
  c.move(dir);
  return true;
}
function go(c, x, y, range) {
  if (honorYield(c)) return false;
  if (c.fatigue) return false;
  const r = range || 0;
  if (c.room.name === TARGET) {
    const goal = { x, y };
    if (rng(c.pos, goal) <= r) return true;
    const off = swampStep(c.pos, goal);
    if (off) { stepFriend(c, off.x, off.y); return false; }
    if (stepOntoSwamp(c.pos, goal)) {
      const via = swampStep(SWAMP, goal);
      stepFriend(c, via.x, via.y);
      return false;
    }
    // Ignore creeps in PathFinder, then swap into the first step if a friend holds it.
    // Waiting for MV stuck≥2 is too slow at the breach.
    const res = PathFinder.search(c.pos, { pos: new RoomPosition(x, y, TARGET), range: r }, {
      plainCost: 2, swampCost: 5, maxRooms: 1, maxOps: 800,
      roomCallback(rn) {
        if (rn !== TARGET) return false;
        const room = Game.rooms[rn]; if (!room) return false;
        const m = new PathFinder.CostMatrix();
        m.set(SWAMP.x, SWAMP.y, 255);
        for (const s of room.find(FIND_STRUCTURES)) {
          if (s.structureType === STRUCTURE_ROAD) {
            if (m.get(s.pos.x, s.pos.y) === 0) m.set(s.pos.x, s.pos.y, 1);
          } else if (s.structureType !== STRUCTURE_CONTAINER
            && !(s.structureType === STRUCTURE_RAMPART && (s.my || s.isPublic))) {
            m.set(s.pos.x, s.pos.y, 255);
          }
        }
        return m;
      },
    });
    if (res.path && res.path.length) {
      const n = res.path[0];
      stepFriend(c, n.x, n.y);
      return false;
    }
    // Fallback: MV.to noDetour still swaps at stuck≥2 if PathFinder found nothing.
    return MV.to(c, x, y, r, ND);
  }
  return MV.to(c, x, y, r, ND);
}
function resolveTarget(c, spec) {
  if (!spec) return null;
  if (typeof spec === 'string') {
    if (spec === 'self') return c;
    return Game.getObjectById(spec);
  }
  const p = Array.isArray(spec) ? { x: spec[0], y: spec[1] } : spec;
  if (p.room && p.room !== c.room.name) return null;
  const at = [].concat(c.room.lookForAt(LOOK_CREEPS, p.x, p.y) || [], c.room.lookForAt(LOOK_STRUCTURES, p.x, p.y) || []);
  return at.find(o => o && !o.my) || null;
}
function applyOrder(c, o) {
  const healSpec = o.heal === 'lowest' ? null : o.heal;
  let healT = null;
  if (o.heal === 'self') healT = c;
  else if (o.heal === 'lowest') {
    const hp = c.getActiveBodyparts(HEAL) ? healPlan(c, squad(c)) : null;
    healT = hp && (hp.id === c.id ? c : Game.getObjectById(hp.id));
  } else if (healSpec) healT = resolveTarget(c, healSpec);
  if (c.getActiveBodyparts(HEAL)) {
    // No single-id lock: ordered heal=ID is one candidate; still dual-fire most-damaged.
    // heal=lowest / missing → pure rotate. Misaki 2026-11-04.
    if (o.heal && o.heal !== 'lowest' && healT && healT.hits < healT.hitsMax) {
      if (c.pos.isNearTo(healT) || healT === c) c.heal(healT);
      else if (c.pos.inRangeTo(healT, 3)) c.rangedHeal(healT);
      if (c.hits < c.hitsMax && healT !== c) c.heal(c);
    } else {
      healDual(c, squad(c));
    }
  }
  const atk = resolveTarget(c, o.attack);
  if (atk) {
    if (c.getActiveBodyparts(ATTACK) && c.pos.isNearTo(atk)) c.attack(atk);
    if (c.getActiveBodyparts(RANGED_ATTACK) && c.pos.inRangeTo(atk, 3)) c.rangedAttack(atk);
  }
  const dis = resolveTarget(c, o.dismantle);
  if (dis && c.getActiveBodyparts(WORK) && c.pos.isNearTo(dis)) c.dismantle(dis);
  if (honorYield(c)) return true;
  if (o.hold) return true;
  const mv = o.moveTo ? (Array.isArray(o.moveTo) ? { x: o.moveTo[0], y: o.moveTo[1] } : o.moveTo) : null;
  if (mv) {
    if (mv.room && mv.room !== c.room.name) c.moveTo(new RoomPosition(mv.x, mv.y, mv.room), { reusePath: 8, range: mv.range || 0 });
    else go(c, mv.x, mv.y, mv.range || 0);
    return true;
  }
  const chase = atk || dis;
  if (chase) {
    const r = c.getActiveBodyparts(RANGED_ATTACK) && !c.getActiveBodyparts(ATTACK) && !c.getActiveBodyparts(WORK) ? 3 : 1;
    if (!c.pos.inRangeTo(chase, r)) go(c, chase.pos.x, chase.pos.y, r);
  }
  return true;
}
function strike(c, t, w, hp) {
  const melee = c.getActiveBodyparts(ATTACK) > 0, work = c.getActiveBodyparts(WORK) > 0, ra = c.getActiveBodyparts(RANGED_ATTACK) > 0;
  // Prefer ordered/picked target; if none in reach, smash adjacent tower/rampart so assault keeps DPS up.
  if (work && t && c.pos.isNearTo(t)) c.dismantle(t);
  else if (work) {
    const adj = c.pos.findInRange(FIND_HOSTILE_STRUCTURES, 1).find(s =>
      s.structureType === STRUCTURE_TOWER || s.structureType === STRUCTURE_RAMPART || s.structureType === STRUCTURE_WALL);
    if (adj) c.dismantle(adj);
  }
  if (melee) {
    if (t && c.pos.isNearTo(t)) c.attack(t);
    else {
      const adjC = (w.hc || []).find(h => c.pos.isNearTo(h));
      const adjTw = c.pos.findInRange(FIND_HOSTILE_STRUCTURES, 1).find(s => s.structureType === STRUCTURE_TOWER);
      const adjS = adjTw || c.pos.findInRange(FIND_HOSTILE_STRUCTURES, 1).find(s => s.structureType !== STRUCTURE_CONTROLLER);
      const adj = adjC || adjS;
      if (adj) c.attack(adj);
    }
  }
  // Heal throughput: every tick heal() + rangedHeal() on current most-damaged (rotate, no lock).
  if (c.getActiveBodyparts(HEAL)) {
    const mates = c.room.find(FIND_MY_CREEPS).filter(x => x !== c && x.memory && x.memory.role === 'raid9');
    healDual(c, mates);
    if (!ra && c.memory.kind === 'h') return;
  }
  if (ra) {
    const inR = (w.hc || []).filter(h => c.pos.inRangeTo(h, 3));
    if (useMass(c.pos, inR)) c.rangedMassAttack();
    else if (t && c.pos.inRangeTo(t, 3)) c.rangedAttack(t);
    else if (inR.length) c.rangedAttack(_.min(inR, h => h.hits));
    else {
      const s = c.pos.findInRange(FIND_HOSTILE_STRUCTURES, 3).find(s => s.structureType !== STRUCTURE_CONTROLLER);
      if (s) c.rangedAttack(s);
    }
  }
}
let squadTick = -1;
function tickSquad(P, alive) {
  if (squadTick === Game.time) return;
  squadTick = Game.time;
  syncGo(P, alive);
  if (P.emBackAt && Game.time > P.emBackAt) delete P.emBack;
  if (P.phase === 'fallback' || P.flee || P.garrison || P.safe) { if (P.flee || P.garrison || P.safe) P.phase = 'fallback'; return; }
  const room = Game.rooms[TARGET];
  if (!room) { if (!P.phase) P.phase = 'breach'; return; }
  const mouths = mouthsOf(P, P.phase || 'breach');
  const ours = alive.filter(x => x.room && x.room.name === TARGET).map(x => ({ pos: x.pos, room: x.room }));
  syncPhase(P, observe(world(room), mouths, ours));
  // One update per tick so every healer sees the same 3-tick push and the same retreat.
  const soft = P.pullSoft == null ? PULL_SOFT : P.pullSoft, hard = P.pullHard == null ? PULL_HARD : P.pullHard;
  if ((P.phase || 'breach') === 'breach' && P.kite !== false) {
    const front = alive.filter(x => x.room && x.room.name === TARGET && (x.memory.kind === 'd' || x.memory.kind === 'm'));
    let worst = 1;
    for (const f of front) if (f.hitsMax) worst = Math.min(worst, f.hits / f.hitsMax);
    const healers = alive.filter(x => x.memory.kind === 'h' && x.room && x.room.name === TARGET)
      .sort((a, b) => (a.memory.k | 0) - (b.memory.k | 0));
    if (P.em && Game.time >= P.em.since + EM_TICKS) {
      P.emBack = P.em.ids; P.emBackAt = Game.time; P.emCool = Game.time + EM_COOL; delete P.em;
    } else if (!P.em && pullMode(worst, soft, hard) === 'hard' && healers.length && !(P.emCool && Game.time < P.emCool)) {
      P.em = { since: Game.time, ids: healers.slice(0, 2).map(h => h.name) };
    }
  }
}
function stageSlot(c) {
  const k = c.memory.k | 0, kind = c.memory.kind || 'm';
  const y = (kind === 'h' || kind === 'r') ? 2 : 1;
  return [[36, 37, 38, 39, 40, 41][k % 6], y];
}
function travel(c) {
  const slot = stageSlot(c);
  const b = c.pos.x === 0 || c.pos.x === 49 || c.pos.y === 0 || c.pos.y === 49;
  if (c.room.name === HOME) {
    if (c.pos.x === 0 && c.pos.y === 23) { delete c.memory._m; return c.move(LEFT); }
    if (b) { delete c.memory._m; return c.move(c.pos.x === 49 ? LEFT : c.pos.x === 0 ? RIGHT : c.pos.y === 0 ? BOTTOM : TOP); }
    return MV.to(c, 0, 23, 0);
  }
  if (c.room.name === STAGE) {
    if (b && c.pos.x === 49) { delete c.memory._m; return c.move(LEFT); }
    return MV.to(c, slot[0], slot[1], 0, ND);
  }
  return c.moveTo(new RoomPosition(slot[0], slot[1], STAGE), { reusePath: 10 });
}
function garrison(c) {
  const g = gSlotOf(c.memory.k);
  const hp = c.getActiveBodyparts(HEAL) ? healPlan(c, squad(c)) : null;
  const w = { hc: c.room.find(FIND_HOSTILE_CREEPS) };
  if (w.hc.length || hp || (c.getActiveBodyparts(HEAL) && c.hits < c.hitsMax)) strike(c, null, w, hp);
  if (honorYield(c)) return;
  if (c.room.name === TARGET) {
    if (c.pos.x === ENTRY.x && c.pos.y === ENTRY.y) return c.move(BOTTOM);
    return go(c, ENTRY.x, ENTRY.y, 0);
  }
  if (c.room.name !== STAGE) return travel(c);
  if (c.pos.x === g[0] && c.pos.y === g[1]) return;
  return MV.to(c, g[0], g[1], 0, ND);
}
function approach(c, P) {
  const hp = c.getActiveBodyparts(HEAL) ? healPlan(c, squad(c)) : null;
  const w = { hc: c.room.find(FIND_HOSTILE_CREEPS) };
  if (w.hc.length || hp || (c.getActiveBodyparts(HEAL) && c.hits < c.hitsMax)) strike(c, null, w, hp);
  if (honorYield(c)) return;
  if (P.go) {
    if (c.room.name === STAGE) {
      if (c.pos.x === ENTRY.x && c.pos.y === 0) return c.move(TOP);
      return MV.to(c, ENTRY.x, 0, 0, ND);
    }
    return travel(c);
  }
  return travel(c);
}
function fight(c, P) {
  const kind = c.memory.kind || 'm';
  const alive = allRaid().filter(x => x.room && x.room.name === TARGET);
  const mouths = mouthsOf(P, P.phase || 'breach');
  const opt = {
    mouths, minDps: P.minDps, maxY43: P.maxY43, dps: DPS_ONE,
  };
  const posts = assignment(alive.map(x => ({ id: x.id, kind: x.memory.kind || 'm', k: x.memory.k | 0 })), opt);
  const post = posts.posts[c.id] || { x: ENTRY.x, y: kind === 'h' ? 48 : 46, row: 'heal' };
  const mouth = post.mouth || posts.seals.open[0] || mouths[0] || MOUTH_DUAL[0];
  const w = world(c.room);
  const phase = P.phase || 'breach';
  const focusPos = (phase === 'breach' || phase === 'punch') ? mouth : (w.structs.find(s => s.structureType === 'tower') || {}).pos || mouth;
  const mates = squad(c);
  const hp = c.getActiveBodyparts(HEAL) ? healPlan(c, mates) : null;
  const pulls = { soft: P.pullSoft == null ? PULL_SOFT : P.pullSoft, hard: P.pullHard == null ? PULL_HARD : P.pullHard, kite: P.kite !== false };
  const front = alive.filter(x => x.memory.kind === 'd' || x.memory.kind === 'm');
  let worst = 1;
  for (const f of front) if (f.hitsMax) worst = Math.min(worst, f.hits / f.hitsMax);
  const mode = pulls.kite && phase === 'breach' ? pullMode(worst, pulls.soft, pulls.hard) : null;
  let chosen = pick(c.pos, w, {
    phase: phase === 'fallback' ? 'inside_clean' : phase,
    mouth, sticky: c.memory.sticky, prio: P.prio, towerOrder: P.towerOrder,
  });
  // Keep pushing assault: melee/dismantlers with no fight/seal target pile towers with the squad.
  // Misaki 2026-11-04.
  if ((kind === 'm' || kind === 'd') && !(chosen && (chosen.cls === 'fight' || chosen.cls === 'seal'))) {
    const towerFocus = pickInside(c.pos, w, {
      sticky: c.memory.sticky, towerOrder: P.towerOrder,
      prio: ['towerRampart', 'tower', 'blocker', 'fight', 'filler', 'econ'],
    });
    if (towerFocus) chosen = towerFocus;
  }
  if (chosen) c.memory.sticky = chosen.id; else delete c.memory.sticky;
  const t = chosen && Game.getObjectById(chosen.id);
  strike(c, t, w, hp);
  // Partner already demanded our tile: step into theirs, do not path elsewhere this tick.
  if (honorYield(c)) return;
  if (c.pos.x !== ENTRY.x && c.pos.y >= 49) return go(c, ENTRY.x, ENTRY.y, 0);
  let goal = { x: post.x, y: post.y };
  // Melee: escort dismantlers while seal/fight exists; else drive onto tower with squad.
  if (kind === 'm' && P.escort !== false) {
    if (t && chosen && (chosen.cls === 'tower' || chosen.cls === 'towerRampart')) {
      goal = { x: t.pos.x, y: t.pos.y };
      if (!c.pos.isNearTo(t)) return go(c, goal.x, goal.y, 1);
    } else {
      const ds = alive.filter(x => x.memory && x.memory.kind === 'd');
      if (ds.length) {
        const anchor = _.min(ds, x => rng(c.pos, x.pos));
        goal = { x: anchor.pos.x, y: Math.min(48, anchor.pos.y + (anchor.pos.y >= c.pos.y ? 0 : 1)) };
        if (t && c.pos.isNearTo(t)) { /* already striking */ }
        else if (rng(c.pos, goal) > 1) return go(c, goal.x, goal.y, 1);
      }
    }
  }
  if (phase === 'punch') {
    if (post.row === 'front' || post.row === 'melee') goal = { x: mouth.x, y: 41 };
    else if (post.row === 'reserve') goal = { x: mouth.x, y: 43 };
    else if (post.row === 'ranged') goal = { x: mouth.x, y: 44 };
    else goal = { x: mouth.x, y: 45 };
  } else if (phase === 'inside_towers' || phase === 'inside_clean') {
    if (shouldYield(c.pos, kind, mates, focusPos)) return go(c, c.pos.x, Math.min(48, c.pos.y + 2), 0);
    if (t) {
      const r = (kind === 'd' || kind === 'm') ? 1 : (kind === 'h' ? 2 : 3);
      goal = { x: t.pos.x, y: t.pos.y };
      if (kind === 'h') {
        const anchor = front.length ? _.min(front, x => rng(c.pos, x.pos)) : null;
        if (anchor) goal = { x: anchor.pos.x, y: Math.min(48, anchor.pos.y + 1) };
      }
      if (rng(c.pos, goal) <= r && kind !== 'h') return;
      if (hp && hp.mode === 'far' && hp.ratio < HEAL_URGENT) return go(c, hp.pos.x, hp.pos.y, 1);
      return go(c, goal.x, goal.y, kind === 'h' ? 1 : r);
    }
  }
  // Healers 贴身治疗: stand healGap (default 1) behind the most-hurt (else nearest) front creep.
  // Fall back to the heal row only when own HP < healerHold (default 0.6). Misaki 2026-11-04.
  if (kind === 'h' && (phase === 'breach' || phase === 'punch' || phase === 'inside_towers' || phase === 'inside_clean') && front.length && P.healFront !== false) {
    const hold = P.healerHold == null ? HEAL_URGENT : P.healerHold;
    if (c.hits / c.hitsMax >= hold) {
      const hurt = front.filter(x => x.hits < x.hitsMax);
      const anchor = hurt.length ? _.min(hurt, x => x.hits / x.hitsMax) : _.min(front, x => rng(c.pos, x.pos));
      // Adjacent (range 1): swap/pull onto a free neighbor of the tank, then heal/rangedHeal.
      // Exact healGap tile jammed the line when a melee already stood there.
      const gap = P.healGap == null ? 1 : P.healGap;
      return go(c, anchor.pos.x, anchor.pos.y, Math.max(1, gap));
    }
    return go(c, post.x, Math.max(post.y, 47), 0);
  }
  const emGo = P.em && P.em.ids && P.em.ids.indexOf(c.name) >= 0;
  const emBack = P.emBack && P.emBack.indexOf(c.name) >= 0;
  if (mode === 'hard' && (kind === 'd' || kind === 'm' || kind === 'r')) goal = { x: post.x, y: Math.min(48, c.pos.y + 1) };
  else if (mode === 'soft' && goal.y < c.pos.y && !emGo) goal = { x: goal.x, y: c.pos.y };
  // Named healers step to y44 for EM_TICKS even after the front ratio recovers, then leave together.
  if (emGo) goal = { x: mouth.x, y: 44 };
  else if (emBack) goal = { x: post.x, y: Math.max(post.y, 47) };
  // Breach line: dismantlers do not cross y43 until the hole opens. Emergency healers are allowed up to y44.
  if (phase === 'breach' && kind === 'd' && post.row === 'front' && !emGo) goal.y = Math.max(goal.y, 43);
  if (phase === 'breach' && (kind === 'm' || kind === 'r' || kind === 'h') && mode !== 'hard' && !emGo && !emBack) goal.y = Math.max(goal.y, post.y);
  return go(c, goal.x, goal.y, 0);
}
// War over (Memory.ops.w47n9.recycle === true): walk to the nearest own spawn and recycleCreep.
// Prefers a spawn in the current room, else the creep's home room. Heals self on the way.
function recycleSelf(c) {
  if (c.spawning) return;
  if (c.getActiveBodyparts(HEAL) && c.hits < c.hitsMax) c.heal(c);
  const mine = _.filter(Game.spawns, s => s.my);
  let sp = mine.filter(s => s.pos.roomName === c.room.name);
  if (!sp.length) sp = mine.filter(s => s.pos.roomName === c.memory.home);
  if (!sp.length) sp = mine;
  if (!sp.length) return;
  const t = sp.length > 1 ? (c.pos.findClosestByRange(sp) || sp[0]) : sp[0];
  if (c.pos.roomName === t.pos.roomName && c.pos.isNearTo(t)) return t.recycleCreep(c);
  return c.moveTo(t, { range: 1, reusePath: 10 });
}
function run(c) {
  const P = M();
  // forceGo FIRST — before raidOrder early-return, else resume never clears flee. Misaki 2026-11-04.
  if (P.forceGo) {
    delete P.flee; delete P.garrison; delete P.recycle; delete P.safe; delete P.safeUntil;
    if (P.phase === 'fallback') P.phase = 'breach';
    delete P.forceGo;
  }
  // noOverrun (default): drop stale overrun flees so Memory cannot keep us garrisoned.
  clearStaleOverrun(P);
  if (P.recycle === true) return recycleSelf(c);
  const order = manualOrder(c);
  if (order) return applyOrder(c, order);
  const tr = Game.rooms[TARGET];
  if (tr && tr.controller && tr.controller.safeMode) {
    P.safeUntil = Game.time + tr.controller.safeMode;
    P.safe = P.safe || Game.time;
    P.phase = 'fallback';
    P.garrison = true;
    return garrison(c);
  }
  // Opt-in only: overrun flee requires explicit noOverrun=false. Else only SM (above) or abort flee.
  if (P.noOverrun === false && c.room.name === TARGET && overrun(c.room)) {
    P.flee = P.flee || { t: Game.time, why: 'overrun' };
    P.garrison = true;
    P.phase = 'fallback';
    return garrison(c);
  }
  if (P.garrison || P.safe || P.flee || P.phase === 'fallback') return garrison(c);
  const alive = allRaid();
  tickSquad(P, alive);
  if (P.phase === 'fallback' || P.garrison || P.flee) return garrison(c);
  if (c.room.name !== TARGET) return approach(c, P);
  return fight(c, P);
}
module.exports = {
  TARGET, STAGE, HOME, ENTRY, SWAMP, MOUTH_DUAL, MOUTH_WIDE, TOWER_ORDER, MAX, NEED, MIN_DPS, DPS_ONE,
  PULL_SOFT, PULL_HARD, MAX_Y43, NEAR_EXIT, EM_TICKS, UP_SAFE, PRIO, LADDER, GARRISON,
  DISMANTLER, MELEE, RANGED, HEALER, healBody, bodyFor, costOf,
  raidActive, pauseCivilians, upgraderKeep, recycleSelf, applyPause, namesToRecycle, recycleCivilian,
  WAR_STOR, warFloor, warStorOk, fieldCaps, wantKind, wantSpawn, noteSpawned, mouthsOf, assignSeals, frontSlots, assignment,
  swampStep, stepOntoSwamp, stepFriend, honorYield, pullMode, inApproach, assaultReady, shouldRegroup, syncGo,
  observe, syncPhase, pick, pickInside, shouldYield, manualOrder, useMass, healPlan, healDual, armedParts, overrun, clearStaleOverrun,
  gSlotOf, run,
};
