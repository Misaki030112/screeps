// Per-remote threat state machine (docs/DEFENDER.md §6). ONE pure decision function `step()`; everything else is I/O.
//   sense(r)  : Game -> observation o          (only place that looks at hostiles for remotes)
//   step(s,o) : (state, obs, cfg, t) -> {s, ev} (pure, unit-tested in tests/threat_fsm.js)
//   roles / spawn / remote manager only READ: state(r), holding(home), wantDefender(home), armed(r).
// States: SAFE -> THREAT (solo NPC Invader, OR any combat hostile in a room we currently reserve) -> DEFEND -> SAFE
//         any -> WAIT (wait-out: players on the route/home, unreserved escalation, gate, timeouts, defender died) -> SAFE
// A room is "reserved" when its controller reservation is still ours (Memory.remote[r].res, projected from m.seen),
// Memory.ops.r7 says we hold W47N7, or Memory.ops.resRooms lists it.
// Invader cores and solo/guard Invaders in remotes we defend are fights, not wait-outs. WAIT only when a spawn gate fails
// (gate/cpu/deaths — not maxPerDay budget; Misaki: fight reserved-room enemies, do not pause mining and idle).
// Players outrank a core (the buster never targets a creep). W47N9 is never a target.
const S = { SAFE: 'SAFE', THREAT: 'THREAT', DEFEND: 'DEFEND', WAIT: 'WAIT' };
const DEF = {
  minTtl: 300,        // solo Invader must have >= this TTL left to be worth 1300 energy
  readyTimeout: 200,  // THREAT: defender must be out of the spawn within this, else WAIT (wait-out)
  defendTimeout: 450, // DEFEND: whole fight incl. travel; else WAIT
  clearTicks: 10,     // vision with no Invader for this long = cleared
  waitBuffer: 80,     // WAIT on NPCs = last TTL + buffer
  playerPause: 1500,  // WAIT on players (never fight players)
  coreRecheck: 500,   // legacy/blind core wait: look again (a live core with the gate open goes THREAT instead)
  coreDefendTimeout: 1000, // DEFEND on a core: travel + ceil(100000/300)=334 melee ticks; creep defendTimeout is too short
  maxPerDay: 4,       // defender spawns per 22k ticks (repeated waves cannot drain the economy)
  dayTicks: 22000,
  maxDeaths: 1,       // after a defender death in 1 day: wait-out only
  minBucket: 3000,    // CPU bucket guard
  reserve: 1300,      // storage emergency reserve (RCL4+ with storage) = defender cost
  stableTicks: 1500,  // RCL4 must have held (cap>=1300) this long
  hp: 0.6, hpBack: 0.95, // defender retreat / re-engage thresholds (role reads these)
};
const COMBAT = ['attack', 'ranged_attack', 'heal'];
function roomCfg(r) {
  const R = require('./remote');
  return (R.cfgFor && R.cfgFor(r)) || (R.CFG && R.CFG[r]) || null;
}
const cfg = r => Object.assign({}, DEF, (roomCfg(r) || {}).threat || {});
// ---------- pure core ----------
// 'guard' = combat hostiles inside a room we currently reserve (players, dismantlers, or an escalated Invader wave).
// Route/home players stay 'player' (do not march a remote defender into our own base or a blocked highway).
// Solo Invader is unchanged (ranged kite). A lone invader core is its own fight (melee buster).
// Players outrank a core: never deploy the buster into a player. Short-TTL Invaders stay a wait-out.
function classify(o, c) {
  const routeP = (o.players || 0) > (o.hereP || 0); // players counted outside the remote room itself
  if (routeP) return 'player';
  if (o.core && ((o.hereP || 0) > 0 || (o.players || 0) > 0)) return 'player';
  if (o.reserved && ((o.hereP || 0) > 0 || (o.work || 0) > 0)) return 'guard';
  if ((o.hurtNoInv && !o.core) || (o.players || 0) > 0) return 'player';
  const inv = o.inv || [];
  // combat creeps keep the solo/guard/escalated paths; the core is busted once they are gone
  if (o.core && !inv.length) return 'core';
  if (!inv.length) return 'none';
  if (inv.length === 1 && !inv[0].heal && !inv[0].ranged3) return inv[0].ttl >= c.minTtl ? 'solo' : 'short';
  return o.reserved ? 'guard' : 'invader'; // too many / healer / 3xRA: fight only while we still hold the room
}
const GATES = ['gate', 'cpu', 'budget', 'deaths']; // every reason gateReason() can return
function gateReason(o, c, k) { // why we may not spawn a defender now ('' = ok); k = classify() kind
  if (!o.armed) return 'gate';
  if (o.bucket < c.minBucket) return 'cpu';
  // Misaki: reserved remotes fight Invaders (solo/guard) and cores — do not WAIT/budget them out.
  // maxPerDay still caps a 2nd defender via request2(); unreserved escalated waves stay WAIT(escalated).
  if (k !== 'core' && k !== 'solo' && k !== 'guard' && (o.spawnsDay || 0) >= c.maxPerDay) return 'budget';
  if ((o.deathsDay || 0) >= c.maxDeaths) return 'deaths';
  return '';
}
function step(s, o, c, t) {
  s = s && s.st ? Object.assign({}, s) : { st: S.SAFE, since: t };
  const ev = [], go = (st, why, extra) => { ev.push(Object.assign({ ev: st === S.SAFE ? (s.st === S.WAIT ? 'resume' : s.st === S.DEFEND ? 'cleared' : 'cancel') : st.toLowerCase(), from: s.st, why }, extra || {}));
    s = Object.assign(s, { st, since: t, why }); };
  // no vision: carry last known invaders forward (TTL projected); vision always wins.
  // Reserved-room hostiles (players / dismantlers) are remembered for foeMemory ticks so civilians fleeing the room
  // do not cancel the guard before the defender arrives and restores vision.
  if (o.vis) {
    if ((o.inv || []).length) { s.last = o.inv; s.seen = t; delete s.gone; } else { s.last = null; s.gone = s.gone || t; }
    if ((o.hereP || 0) + (o.work || 0) > 0) { s.foes = (o.hereP || 0) + (o.work || 0); s.foeSeen = t; } else s.foes = 0;
    if (o.core && o.corePos) s.corePos = o.corePos.slice();
    else if (!o.core) delete s.corePos;
  } else {
    const extra = {};
    if (s.last) extra.inv = s.last.map(i => Object.assign({}, i, { ttl: i.ttl - (t - s.seen) })).filter(i => i.ttl > 0);
    if (s.foes && t - (s.foeSeen || 0) < (c.foeMemory || 200)) extra.hereP = Math.max(o.hereP || 0, s.foes);
    // core has no TTL: keep the fight alive while the buster travels (everyone else fled, so no vision)
    // also project through WAIT(gate/cpu/budget/deaths) so a core stuck on maxPerDay re-arms without needing fresh vision
    if (s.mission === 'core' && (s.st === S.THREAT || s.st === S.DEFEND || (s.st === S.WAIT && GATES.includes(s.why)))) { extra.core = true; if (s.corePos) extra.corePos = s.corePos; }
    if (extra.inv || extra.hereP || extra.core) o = Object.assign({}, o, extra);
  }
  const k = classify(o, c), maxTtl = Math.max(0, ...(o.inv || []).map(i => i.ttl));
  const waitNpc = why => go(S.WAIT, why, { until: s.until = t + maxTtl + c.waitBuffer });
  if (k === 'player' && !(s.st === S.WAIT && s.why === 'player')) { delete s.mission; go(S.WAIT, 'player', { until: s.until = t + c.playerPause }); return { s, ev }; }
  switch (s.st) {
    case S.SAFE:
      if (k === 'solo' || k === 'guard' || k === 'core') { const g = gateReason(o, c, k); if (g) { if (k === 'core') s.mission = 'core'; waitNpc(g); } else { s.inc = t; delete s.recycling; s.mission = k; go(S.THREAT, k, { inv: o.inv }); } }
      else if (k === 'invader') waitNpc('escalated');
      else if (k === 'short') waitNpc('short_ttl');
      break;
    case S.THREAT:
      if (k === 'none') go(S.SAFE, 'gone');
      else if (!o.armed) waitNpc('gate'); // disarmed mid-THREAT: wait out, any defender recycles
      else if (k !== 'solo' && k !== 'guard' && k !== 'core') waitNpc(k === 'short' ? 'short_ttl' : 'escalated');
      // solo/guard creep died but an Invader core remains: drop the kite, re-arm as a core buster mission
      else if (k === 'core' && s.mission !== 'core') {
        s.mission = 'core'; if (o.corePos) s.corePos = o.corePos.slice();
        delete s.def; delete s.def2; delete s.arrived; delete s.need2;
        go(S.THREAT, 'core');
      }
      else if (o.def === 'out') go(S.DEFEND, 'dispatched');
      else if (o.def !== 'spawning' && t - s.since > c.readyTimeout) waitNpc('timeout');
      break;
    case S.DEFEND:
      if (!o.armed && k !== 'none') waitNpc('gate');
      else if (o.def === 'dead') waitNpc('defender_died');
      else if (o.def === 'none') waitNpc('defender_expired');
      else if (k === 'none' && o.vis && t - s.gone >= c.clearTicks) go(S.SAFE, 'killed');
      else if (k === 'none' && !o.vis && !(o.inv || []).length && s.mission !== 'core') go(S.SAFE, 'gone'); // foe memory expired, nothing left to project
      // solo kite finished the creep but a core remains (W45N7@83983760: mission=solo DEFEND stuck while core@9,44 lived)
      else if (k === 'core' && s.mission !== 'core') {
        s.mission = 'core'; if (o.corePos) s.corePos = o.corePos.slice();
        delete s.def; delete s.def2; delete s.arrived; delete s.need2; delete s.early;
        go(S.THREAT, 'core');
      }
      else if (s.mission === 'core' && k !== 'core' && k !== 'none') waitNpc(k === 'short' ? 'short_ttl' : 'escalated'); // melee body does not duel creeps
      else if (k === 'invader') waitNpc('escalated');
      else if (k === 'core' && t - s.since > (c.coreDefendTimeout || 1000)) waitNpc('defend_timeout');
      else if (k !== 'guard' && k !== 'core' && t - s.since > c.defendTimeout) waitNpc('defend_timeout'); // a reserved-room guard stays while hostiles remain
      break;
    case S.WAIT:
      // legacy why=core (pre-buster): a visible core re-arms into THREAT the same tick; blind, keep the recheck
      // so a reserver/rminer looks again instead of pausing forever with no vision.
      if (s.why === 'core') {
        if (o.vis && o.core) { s.mission = 'core'; const g = gateReason(o, c, 'core'); if (g) { s.why = g; s.until = Math.max(s.until || 0, t + c.coreRecheck); } else s.why = 'gate'; }
        else if (!o.vis && t < (s.until || 0)) break;
        else { go(S.SAFE, o.vis ? 'core_gone' : 'core_recheck'); break; }
      }
      // a spawn gate (gate/cpu/budget/deaths) cleared while a solo, a guard, or a core is still needed
      if (s.st === S.WAIT && GATES.includes(s.why) && !gateReason(o, c, k) && (k === 'solo' || k === 'guard' || k === 'core')) {
        delete s.until; s.inc = t; delete s.recycling; s.mission = k; go(S.THREAT, k, { inv: o.inv }); }
      // player-on-the-route WAIT, or an escalated wait, becomes a guard once the hostiles are inside a room we reserve
      else if (k === 'guard' && !gateReason(o, c, k)) {
        delete s.until; s.inc = t; delete s.recycling; s.mission = 'guard'; go(S.THREAT, 'guard', { inv: o.inv }); }
      else if (s.why !== 'player' && o.vis && k === 'none') go(S.SAFE, 'clear_seen');
      else if (t >= s.until) go(S.SAFE, 'timer');
      break;
  }
  if (s.st === S.SAFE) { delete s.inc; delete s.until; delete s.foes; delete s.foeSeen; delete s.mission; delete s.corePos; }
  return { s, ev };
}
// resumeEarly (W45N8 review): in DEFEND with our defender in the room and the target <15% hp (or already dead, waiting
// clearTicks), rminer/rhauler go back early. Sticky until a target is back above 30% (healed) or the state leaves DEFEND.
const EARLY = { on: 0.15, off: 0.3, roles: ['rminer', 'rhauler'] };
function earlyNext(s, defIn) {
  // a core has no creep `last` entry; vacuous every() would resume miners the tick the buster arrives
  if (s.st !== S.DEFEND || !defIn || s.mission === 'core') return false;
  const inv = s.last || [], f = i => i.hitsMax ? i.hits / i.hitsMax : 1;
  if (inv.some(i => f(i) >= EARLY.off)) return false;
  return !!s.early || inv.every(i => f(i) < EARLY.on);
}
// ---------- I/O adapter ----------
const mem = r => { const R = Memory.remote = Memory.remote || {}; R[r] = R[r] || {}; return R[r]; };
const hist = (m, key, c) => (m[key] = (m[key] || []).filter(x => Game.time - x < c.dayTicks));
function ourName() {
  if (typeof Memory !== 'undefined' && Memory.username) return Memory.username;
  if (typeof Game === 'undefined' || !Game.creeps) return '';
  const id = Object.keys(Game.creeps)[0], c = id && Game.creeps[id];
  const name = c && c.owner && c.owner.username;
  if (name && typeof Memory !== 'undefined') Memory.username = name;
  return name || '';
}
// True while WE still hold this room's controller reservation (not merely a reserver walking there).
// Vision of a foreign reservation wins over a stale Memory.ops.r7 stamp.
function reservedByUs(r) {
  const who = ourName(); if (!who || r === 'W47N9') return false;
  const m = (Memory.remote || {})[r] || {}, res = m.res;
  if (res && res.username) {
    const left = (res.ticksToEnd | 0) - (Game.time - (m.seen != null ? m.seen : Game.time));
    if (left > 0) return res.username === who;
  }
  const p = Memory.ops && Memory.ops.r7;
  if (r === 'W47N7' && p && p.by === who && (p.endTime || 0) > Game.time) return true;
  const extra = Memory.ops && Memory.ops.resRooms && Memory.ops.resRooms[r];
  return !!(extra && extra.by === who && (extra.until || 0) > Game.time);
}
function armed(r) { // code-level enable gate: flag AND RCL4 stable AND (CLAIM2 reserver OR we still hold the reservation)
  const C = roomCfg(r); if (!C) return false;
  const m = mem(r), home = Game.rooms[C.home];
  m.needE = false;
  // remoteDefender (home.js FLAGS) defaults ON; Memory.defense.remoteDefender can force off without redeploy.
  if (!require('./home').on('remoteDefender')) return false;
  if (!(C.defend || m.defend) || !home || !home.controller) return false;
  const hm = home.memory, c = cfg(r);
  // RCL5+ already held RCL4 for >>stableTicks; seed the clock so a Memory wipe cannot disarm mid-raid
  if (home.controller.level >= 5) hm.rcl4Since = Math.min(hm.rcl4Since || Game.time, Game.time - c.stableTicks);
  else if (home.controller.level >= 4 && home.energyCapacityAvailable >= c.reserve) hm.rcl4Since = hm.rcl4Since || Game.time;
  else delete hm.rcl4Since;
  // Ready = recently near-full OR can pay for a defender now (RCL5 build / dual-remote spawn keeps avail < reserve
  // for long stretches → lastFull goes stale; storage holds the 1300 — queen/haulers can refill ext in <50t)
  const stor = home.storage && home.storage.store[RESOURCE_ENERGY] || 0;
  const ready = Game.time - (hm.lastFull || 0) < 300 || home.energyAvailable >= c.reserve || stor >= c.reserve;
  const stable = hm.rcl4Since && Game.time - hm.rcl4Since >= c.stableTicks && ready;
  if (_.some(Game.creeps, x => x.memory.role === 'reserver' && x.memory.remote === r && x.getActiveBodyparts(CLAIM) >= 2)) m.claim2 = Game.time;
  // A live reservation outlasts the reserver creep. Holding the room is enough; CLAIM2-within-1500t still counts on its own.
  const held = (!!m.claim2 && Game.time - m.claim2 < 1500) || reservedByUs(r);
  // A core in a room we are configured to defend still counts after it has eaten the reservation
  // (otherwise the bust can never start, and a mid-fight drop would abort it). W47N9 is never armed.
  const th = m.th || {};
  const coreJob = th.mission === 'core' && (th.st === S.THREAT || th.st === S.DEFEND || (th.st === S.WAIT && GATES.includes(th.why)));
  let coreHere = false;
  if (!held && !coreJob && (C.defend || m.defend) && r !== 'W47N9') {
    const rm = Game.rooms[r];
    if (rm && rm.find) coreHere = rm.find(FIND_HOSTILE_STRUCTURES).some(s => s && s.structureType === STRUCTURE_INVADER_CORE);
  }
  const keep = held || coreJob || coreHere;
  // only the energy readiness is missing (flag on, RCL ok, room held): spawn.js may hold to collect the 1300 (energyHold)
  m.needE = !ready && !!hm.rcl4Since && Game.time - hm.rcl4Since >= c.stableTicks && keep;
  return !!(stable && keep);
}
function body(h, t) { return h.body.some(p => p.type === t && p.hits > 0); }
function sense(r) {
  const C = roomCfg(r); if (!C) return { vis: false, inv: [], players: 0, hereP: 0, work: 0, reserved: false, core: false, hurtNoInv: false, bucket: Game.cpu.bucket, armed: false, def: 'none' };
  const m = mem(r), room = Game.rooms[r], c = cfg(r), th = m.th || {};
  const o = { vis: !!room, inv: [], players: 0, hereP: 0, work: 0, reserved: reservedByUs(r), core: false, hurtNoInv: false, bucket: Game.cpu.bucket, armed: armed(r) };
  // guardOnly (W47N7): hostiles in the colony room are that room's own defence. Counting them here would
  // WAIT-player the remote forever while BustJetter sits on the W47N8 seal.
  const scan = (C.guardOnly || C.dynamic) ? [r] : [r, C.home].concat(C.via || []);
  for (const rn of scan) { // via rooms (W45N7 through W45N8): players there block the route too
    const rm = Game.rooms[rn]; if (!rm) continue;
    const hs = rm.find(FIND_HOSTILE_CREEPS); // never contains our own creeps (no false positives from own creeps)
    const players = hs.filter(h => h.owner.username !== 'Invader' && h.body.some(p => COMBAT.includes(p.type) && p.hits > 0));
    o.players += players.length;
    if (rn === r) {
      o.hereP = players.length;
      o.work = hs.filter(h => h.body.some(p => p.type === 'work' && p.hits > 0) && !h.body.some(p => COMBAT.includes(p.type) && p.hits > 0)).length;
      o.inv = hs.filter(h => h.owner.username === 'Invader' && h.body.some(p => COMBAT.includes(p.type) && p.hits > 0)).map(h => ({ x: h.pos.x, y: h.pos.y, ttl: h.ticksToLive || 1500,
        heal: body(h, HEAL), ranged3: h.getActiveBodyparts(RANGED_ATTACK) >= 3, hits: h.hits, hitsMax: h.hitsMax, boosted: h.body.some(p => p.boost) }));
      const cores = rm.find(FIND_HOSTILE_STRUCTURES).filter(s => s.structureType === STRUCTURE_INVADER_CORE);
      o.core = cores.length > 0;
      if (o.core && cores[0].pos) o.corePos = [cores[0].pos.x, cores[0].pos.y];
      // our creep hurt with no Invader visible => someone else (player) did it
      // our creep LOST hits this tick with no Invader visible => someone else (player) did it (old damage is ignored)
    }
  }
  // hits sample refreshed every tick wherever the creep is; only a drop between two CONSECUTIVE ticks both spent
  // inside r counts (damage taken in W45N8 / en route was misread as a player attack in r and paused it 1500t)
  for (const x of _.filter(Game.creeps, x => x.memory.remote === r)) { const xm = x.memory, here = x.room.name === r;
    if (here && room && !o.inv.length && xm.role !== 'defender' && xm._hr === r && xm._ht === Game.time - 1 && x.hits < xm._h) o.hurtNoInv = true;
    xm._h = x.hits; xm._hr = x.room.name; xm._ht = Game.time; }
  const d = th.def && Game.creeps[th.def];
  o.def = !th.def ? 'none' : !d ? 'dead' : d.spawning ? 'spawning' : 'out';
  if (o.def === 'dead' && th.recycling === th.def) o.def = 'none'; // recycled by us, not killed
  o.defIn = !!(d && !d.spawning && d.room.name === r);
  o.spawnsDay = hist(m, 'defSpawns', c).length; o.deathsDay = hist(m, 'defDeaths', c).length;
  return o;
}
function incident(r, s, e, o) {
  const m = mem(r);
  if (e.ev === 'defender_died' || e.why === 'defender_died') (m.defDeaths = m.defDeaths || []).push(Game.time);
  console.log('INCIDENT ' + JSON.stringify(Object.assign({ remote: r, tick: Game.time, inc: s.inc || null, state: s.st,
    inv: (o.inv || []).length, invTtl: Math.max(0, ...(o.inv || []).map(i => i.ttl)), def: o.def, delivered: m.delivered || 0 }, e)));
}
function run(r) {
  const m = mem(r), c = cfg(r), o = sense(r);
  // one-off migration from the old pauseUntil scheme (pre-FSM wait-out still running): continue it as WAIT
  if (m.pauseUntil !== undefined) { if (m.pauseUntil > Game.time) m.th = { st: S.WAIT, since: Game.time, why: 'migrated', until: m.pauseUntil }; delete m.pauseUntil; delete m.invOnly; delete m.inv; }
  const prev = m.th || {};
  m.armed = o.armed;
  const { s, ev } = step(prev, o, c, Game.time);
  const startInc = prev.inc || s.inc;
  for (const e of ev) incident(r, Object.assign({}, s, { inc: startInc }), Object.assign(e, startInc ? { dur: Game.time - startInc } : {}), o);
  if (s.st === S.DEFEND && o.defIn && !s.arrived) { s.arrived = Game.time; incident(r, s, { ev: 'arrive', travel: Game.time - s.since }, o); }
  if (s.st !== S.DEFEND) delete s.arrived;
  s.early = earlyNext(s, o.defIn);
  if (s.st !== S.THREAT && s.st !== S.DEFEND) { if (s.def && !Game.creeps[s.def]) delete s.def; } // defender (if alive) reads state and recycles
  if ((o.def === 'dead' || o.def === 'none') && s.def && !Game.creeps[s.def]) { delete s.def; delete s.recycling; }
  if (s.def2 && !Game.creeps[s.def2]) delete s.def2;
  if (s.st !== S.DEFEND || (s.def && s.def2)) delete s.need2;
  if (!s.def && s.def2) { s.def = s.def2; delete s.def2; }
  // adopt a patrolling ranged defender instead of spawning a new one. A core needs ATTACK parts; do not adopt the kite body.
  if (s.st === S.THREAT && !s.def && s.mission !== 'core' && s.why !== 'core') { const p = adoptable(r); if (p) { s.def = p.name; p.memory.remote = r; p.memory.patrol = false;
    console.log('INCIDENT ' + JSON.stringify({ remote: r, tick: Game.time, inc: s.inc || null, state: s.st, ev: 'adopt', def: p.name, ttl: p.ticksToLive })); } }
  // Core missions need a melee buster. A leftover ranged kite body (prior solo/patrol) kept as th.def
  // flips THREAT→DEFEND via o.def==='out' and never spawns the buster — W45N7 core@83967273 sat at 100k
  // while defender83966149 (0 ATTACK) parked at the container for ~200t (patrol 2026-10-31 ~01:55).
  if ((s.st === S.THREAT || s.st === S.DEFEND) && s.mission === 'core' && s.def) {
    const d = Game.creeps[s.def];
    if (!d || !d.memory.core) {
      if (d) { d.memory.patrol = true; }
      const rejected = s.def;
      delete s.def; delete s.arrived; delete s.need2;
      if (s.def2 && Game.creeps[s.def2] && Game.creeps[s.def2].memory.core) { s.def = s.def2; delete s.def2; }
      else { delete s.def2; if (s.st === S.DEFEND) { s.st = S.THREAT; s.since = Game.time; s.why = 'need_buster'; } }
      console.log('INCIDENT ' + JSON.stringify({ remote: r, tick: Game.time, inc: s.inc || null, state: s.st, ev: 'reject_kite', def: rejected, ttl: d && d.ticksToLive }));
    }
  }
  m.th = s;
  return s;
}
// a live patrolling defender of the same home with enough TTL for a fight (travel + defendTimeout)
function adoptable(r) { const C = roomCfg(r); if (!C || C.guardOnly || C.dynamic) return undefined; // a west patrol must not be pulled across to W47N7
  return _.filter(Game.creeps, x => x.memory.role === 'defender' && x.memory.patrol && x.memory.home === C.home && !x.spawning && x.ticksToLive > 300)
    .sort((a, b) => b.ticksToLive - a.ticksToLive)[0]; }
const state = r => ((Memory.remote || {})[r] || {}).th || { st: S.SAFE };
function remotesOf(home) {
  const R = require('./remote');
  const names = Object.keys(R.CFG).filter(r => R.CFG[r].home === home);
  if (R.guardRooms) for (const r of R.guardRooms()) {
    const C = R.cfgFor && R.cfgFor(r);
    if (C && C.home === home && names.indexOf(r) < 0) names.push(r);
  }
  return names;
}
function coreMission(r) { const t = state(r); return t.mission === 'core' && (t.st === S.THREAT || t.st === S.DEFEND); }
module.exports = { S, DEF, cfg, classify, step, sense, run, state, armed, ourName, reservedByUs, roomCfg, coreMission,
  // remote creeps stay home unless SAFE
  safe: (r, role) => state(r).st === S.SAFE || (!!role && EARLY.roles.includes(role) && !!state(r).early),
  earlyNext, EARLY,
  // first remote of this home that needs a defender spawned now
  wantDefender: home => remotesOf(home).find(r => (state(r).st === S.THREAT && !state(r).def) || (state(r).st === S.DEFEND && state(r).need2 && !state(r).def2)),
  // defender could not win alone: ask for a 2nd one (2nd spawn still hits maxPerDay; cores/first fight exempt)
  request2(r) { const m = mem(r), th = m.th, c = cfg(r); if (!th || th.st !== S.DEFEND || th.need2 || th.def2) return;
    if (th.mission !== 'core' && hist(m, 'defSpawns', c).length >= c.maxPerDay) return; th.need2 = Game.time;
    console.log('INCIDENT ' + JSON.stringify({ remote: r, tick: Game.time, inc: th.inc || null, state: th.st, ev: 'need2', def: th.def })); },
  // home is collecting 1300 for a remote defender (clears once noteSpawn sets th.def): spawn holds all but queen,
  // haulers fill extensions to 100%, upgraders pause withdrawals (spawn/ext economy). Home guards use home.js, not this.
  holding: home => remotesOf(home).some(r => (state(r).st === S.THREAT && !state(r).def) || (state(r).st === S.DEFEND && state(r).need2 && !state(r).def2)) || module.exports.energyHold(home),
  // bootstrap reserve (W45N7 plan): a solo Invader is waited out ONLY because extensions are below 1300 -> hold spawns (queen still
  // refills) until energyAvailable reaches 1300; armed() then turns true and the FSM re-arms WAIT(gate) -> THREAT -> defender.
  energyHold: home => remotesOf(home).some(r => { const t = state(r), m = (Memory.remote || {})[r] || {};
    if (!(t.st === S.WAIT && t.why === 'gate' && m.needE)) return false;
    const solo = (t.last || []).length === 1 && !t.last[0].heal && !t.last[0].ranged3;
    return solo || (t.foes || 0) > 0 || t.mission === 'core'; // core bust uses the same 1300
  }),
  // storage energy reserved for defence (builders must not go below it)
  reserve: home => remotesOf(home).some(r => ((Memory.remote || {})[r] || {}).armed) ? DEF.reserve : 0,
  // the defender tells the FSM it is recycling itself (so its disappearance is not counted as a death)
  noteRecycle(r, name) { const th = mem(r).th; if (th) th.recycling = name; },
  noteSpawn(r, name) { const m = mem(r); (m.defSpawns = m.defSpawns || []).push(Game.time); if (m.th.def && Game.creeps[m.th.def]) m.th.def2 = name; else m.th.def = name;
    console.log('INCIDENT ' + JSON.stringify({ remote: r, tick: Game.time, inc: m.th.inc || null, state: m.th.st, ev: 'spawn_start', def: name, waited: Game.time - m.th.since })); },
};
