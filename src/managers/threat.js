// Per-remote threat state machine (docs/DEFENDER.md §6). ONE pure decision function `step()`; everything else is I/O.
//   sense(r)  : Game -> observation o          (only place that looks at hostiles for remotes)
//   step(s,o) : (state, obs, cfg, t) -> {s, ev} (pure, unit-tested in tests/threat_fsm.js)
//   roles / spawn / remote manager only READ: state(r), holding(home), wantDefender(home), armed(r).
// States: SAFE -> THREAT (solo NPC Invader, defender requested) -> DEFEND (defender out) -> SAFE
//         any -> WAIT (wait-out: players, escalation, core, gate closed, timeouts, defender died) -> SAFE
const S = { SAFE: 'SAFE', THREAT: 'THREAT', DEFEND: 'DEFEND', WAIT: 'WAIT' };
const DEF = {
  minTtl: 300,        // solo Invader must have >= this TTL left to be worth 1300 energy
  readyTimeout: 200,  // THREAT: defender must be out of the spawn within this, else WAIT (wait-out)
  defendTimeout: 450, // DEFEND: whole fight incl. travel; else WAIT
  clearTicks: 10,     // vision with no Invader for this long = cleared
  waitBuffer: 80,     // WAIT on NPCs = last TTL + buffer
  playerPause: 1500,  // WAIT on players (never fight players)
  coreRecheck: 500,   // invader core: re-check (needs vision) — never auto-attacked
  maxPerDay: 4,       // defender spawns per 22k ticks (repeated waves cannot drain the economy)
  dayTicks: 22000,
  maxDeaths: 1,       // after a defender death in 1 day: wait-out only
  minBucket: 3000,    // CPU bucket guard
  reserve: 1300,      // storage emergency reserve (RCL4+ with storage) = defender cost
  stableTicks: 1500,  // RCL4 must have held (cap>=1300) this long
  hp: 0.6, hpBack: 0.95, // defender retreat / re-engage thresholds (role reads these)
};
const COMBAT = ['attack', 'ranged_attack', 'heal'];
const cfg = r => Object.assign({}, DEF, (require('./remote').CFG[r] || {}).threat || {});
// ---------- pure core ----------
function classify(o, c) {
  if (o.players > 0 || o.hurtNoInv) return 'player';
  if (o.core) return 'core';
  const inv = o.inv || [];
  if (!inv.length) return 'none';
  if (inv.length === 1 && !inv[0].heal && !inv[0].ranged3) return inv[0].ttl >= c.minTtl ? 'solo' : 'short';
  return 'invader'; // too many / healer / 3xRA / short TTL -> wait-out
}
const GATES = ['gate', 'cpu', 'budget', 'deaths']; // every reason gateReason() can return
function gateReason(o, c) { // why we may not spawn a defender now ('' = ok)
  if (!o.armed) return 'gate';
  if (o.bucket < c.minBucket) return 'cpu';
  if ((o.spawnsDay || 0) >= c.maxPerDay) return 'budget';
  if ((o.deathsDay || 0) >= c.maxDeaths) return 'deaths';
  return '';
}
function step(s, o, c, t) {
  s = s && s.st ? Object.assign({}, s) : { st: S.SAFE, since: t };
  const ev = [], go = (st, why, extra) => { ev.push(Object.assign({ ev: st === S.SAFE ? (s.st === S.WAIT ? 'resume' : s.st === S.DEFEND ? 'cleared' : 'cancel') : st.toLowerCase(), from: s.st, why }, extra || {}));
    s = Object.assign(s, { st, since: t, why }); };
  // no vision: carry last known invaders forward (TTL projected); vision always wins
  if (o.vis) { if ((o.inv || []).length) { s.last = o.inv; s.seen = t; delete s.gone; } else { s.last = null; s.gone = s.gone || t; } }
  else if (s.last) o = Object.assign({}, o, { inv: s.last.map(i => Object.assign({}, i, { ttl: i.ttl - (t - s.seen) })).filter(i => i.ttl > 0) });
  const k = classify(o, c), maxTtl = Math.max(0, ...(o.inv || []).map(i => i.ttl));
  const waitNpc = why => go(S.WAIT, why, { until: s.until = t + maxTtl + c.waitBuffer });
  if (k === 'player' && !(s.st === S.WAIT && s.why === 'player')) { go(S.WAIT, 'player', { until: s.until = t + c.playerPause }); return { s, ev }; }
  if (k === 'core' && !(s.st === S.WAIT && s.why === 'core')) { go(S.WAIT, 'core', { until: s.until = t + c.coreRecheck }); return { s, ev }; }
  switch (s.st) {
    case S.SAFE:
      if (k === 'solo') { const g = gateReason(o, c); if (g) waitNpc(g); else { s.inc = t; delete s.recycling; go(S.THREAT, 'solo', { inv: o.inv }); } }
      else if (k === 'invader') waitNpc('escalated');
      else if (k === 'short') waitNpc('short_ttl');
      break;
    case S.THREAT:
      if (k === 'none') go(S.SAFE, 'gone');
      else if (k !== 'solo') waitNpc(k === 'short' ? 'short_ttl' : 'escalated');
      else if (o.def === 'out') go(S.DEFEND, 'dispatched');
      else if (o.def !== 'spawning' && t - s.since > c.readyTimeout) waitNpc('timeout');
      break;
    case S.DEFEND:
      if (o.def === 'dead') waitNpc('defender_died');
      else if (o.def === 'none') waitNpc('defender_expired');
      else if (k === 'none' && o.vis && t - s.gone >= c.clearTicks) go(S.SAFE, 'killed');
      else if (k === 'invader') waitNpc('escalated');
      else if (t - s.since > c.defendTimeout) waitNpc('defend_timeout');
      break;
    case S.WAIT:
      if (s.why === 'core') { if (o.vis && !o.core) go(S.SAFE, 'core_gone'); else if (t >= s.until) s.until = t + c.coreRecheck; }
      // a spawn gate (gate/cpu/budget/deaths) cleared while a solo Invader is still here: arm and fight (do not wait out the whole TTL)
      else if (GATES.includes(s.why) && !gateReason(o, c) && k === 'solo') {
        delete s.until; s.inc = t; delete s.recycling; go(S.THREAT, 'solo', { inv: o.inv }); }
      else if (s.why !== 'player' && o.vis && k === 'none') go(S.SAFE, 'clear_seen');
      else if (t >= s.until) go(S.SAFE, 'timer');
      break;
  }
  if (s.st === S.SAFE) { delete s.inc; delete s.until; }
  return { s, ev };
}
// ---------- I/O adapter ----------
const mem = r => { const R = Memory.remote = Memory.remote || {}; R[r] = R[r] || {}; return R[r]; };
const hist = (m, key, c) => (m[key] = (m[key] || []).filter(x => Game.time - x < c.dayTicks));
function armed(r) { // code-level enable gate: flag AND RCL4 stable AND CLAIM2 reserver (patrol may flip only the flag)
  const R = require('./remote'), C = R.CFG[r], m = mem(r), home = Game.rooms[C.home];
  if (!(C.defend || m.defend) || !home || !home.controller) return false;
  const hm = home.memory, c = cfg(r);
  // RCL5+ already held RCL4 for >>stableTicks; seed the clock so a Memory wipe cannot disarm mid-raid
  if (home.controller.level >= 5) hm.rcl4Since = Math.min(hm.rcl4Since || Game.time, Game.time - c.stableTicks);
  else if (home.controller.level >= 4 && home.energyCapacityAvailable >= c.reserve) hm.rcl4Since = hm.rcl4Since || Game.time;
  else delete hm.rcl4Since;
  // Ready = recently near-full OR can pay for a defender now (RCL5 build keeps avail < cap-100 for long stretches → lastFull goes stale)
  const ready = Game.time - (hm.lastFull || 0) < 300 || home.energyAvailable >= c.reserve;
  const stable = hm.rcl4Since && Game.time - hm.rcl4Since >= c.stableTicks && ready;
  if (_.some(Game.creeps, x => x.memory.role === 'reserver' && x.memory.remote === r && x.getActiveBodyparts(CLAIM) >= 2)) m.claim2 = Game.time;
  return !!(stable && m.claim2 && Game.time - m.claim2 < 1500);
}
function body(h, t) { return h.body.some(p => p.type === t && p.hits > 0); }
function sense(r) {
  const R = require('./remote'), C = R.CFG[r], m = mem(r), room = Game.rooms[r], c = cfg(r), th = m.th || {};
  const o = { vis: !!room, inv: [], players: 0, core: false, hurtNoInv: false, bucket: Game.cpu.bucket, armed: armed(r) };
  for (const rn of [r, C.home]) {
    const rm = Game.rooms[rn]; if (!rm) continue;
    const hs = rm.find(FIND_HOSTILE_CREEPS); // never contains our own creeps (no false positives from own creeps)
    o.players += hs.filter(h => h.owner.username !== 'Invader' && h.body.some(p => COMBAT.includes(p.type) && p.hits > 0)).length;
    if (rn === r) {
      o.inv = hs.filter(h => h.owner.username === 'Invader' && h.body.some(p => COMBAT.includes(p.type) && p.hits > 0)).map(h => ({ x: h.pos.x, y: h.pos.y, ttl: h.ticksToLive || 1500,
        heal: body(h, HEAL), ranged3: h.getActiveBodyparts(RANGED_ATTACK) >= 3, hits: h.hits, boosted: h.body.some(p => p.boost) }));
      o.core = rm.find(FIND_HOSTILE_STRUCTURES).some(s => s.structureType === STRUCTURE_INVADER_CORE);
      // our creep hurt with no Invader visible => someone else (player) did it
      // our creep LOST hits this tick with no Invader visible => someone else (player) did it (old damage is ignored)
      for (const x of _.filter(Game.creeps, x => x.memory.remote === r && x.room.name === r)) { if (!o.inv.length && x.memory.role !== 'defender' && x.hits < (x.memory._h || x.hitsMax)) o.hurtNoInv = true; x.memory._h = x.hits; }
    }
  }
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
  if (s.st !== S.THREAT && s.st !== S.DEFEND) { if (s.def && !Game.creeps[s.def]) delete s.def; } // defender (if alive) reads state and recycles
  if ((o.def === 'dead' || o.def === 'none') && s.def && !Game.creeps[s.def]) { delete s.def; delete s.recycling; }
  m.th = s;
  return s;
}
const state = r => ((Memory.remote || {})[r] || {}).th || { st: S.SAFE };
const remotesOf = home => Object.keys(require('./remote').CFG).filter(r => require('./remote').CFG[r].home === home);
module.exports = { S, DEF, cfg, classify, step, sense, run, state, armed,
  // remote creeps stay home unless SAFE
  safe: r => state(r).st === S.SAFE,
  // first remote of this home that needs a defender spawned now
  wantDefender: home => remotesOf(home).find(r => state(r).st === S.THREAT && !state(r).def),
  // home is collecting energy for a defender: spawn holds non-critical roles, haulers fill extensions, upgraders/builders hold draw
  holding: home => remotesOf(home).some(r => state(r).st === S.THREAT && !state(r).def),
  // storage energy reserved for defence (builders must not go below it)
  reserve: home => remotesOf(home).some(r => ((Memory.remote || {})[r] || {}).armed) ? DEF.reserve : 0,
  // the defender tells the FSM it is recycling itself (so its disappearance is not counted as a death)
  noteRecycle(r, name) { const th = mem(r).th; if (th) th.recycling = name; },
  noteSpawn(r, name) { const m = mem(r); (m.defSpawns = m.defSpawns || []).push(Game.time); m.th.def = name;
    console.log('INCIDENT ' + JSON.stringify({ remote: r, tick: Game.time, inc: m.th.inc || null, state: m.th.st, ev: 'spawn_start', def: name, waited: Game.time - m.th.since })); },
};
