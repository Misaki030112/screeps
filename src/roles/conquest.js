// W47N8 conquest (docs/CONQUEST.md). MANUAL via Memory.ops.cq (tools/conquest.py); nothing spawns or moves until cq is set.
//   cq.cmd   'hold'    squad waits at W46N8 (3,20); breakers/workers wait at home too
//            'go'      squad enters W47N8: kill CLAIM creeps (reserver) first, then healers / armed, then the rest; patrols the north side
//            'retreat' everyone (squad, breakers, workers) home on the safe path; all conquest spawning stops (abort)
//   cq.spawn  true -> spawn the squad (cq.squadMax total, default 2)
//   cq.claim  true -> spawn breakers (2CLAIM2M: attackController on his reservation, claimController once it is gone; cq.breakers, default 3)
//                     then workers (5W5C5M, carry 250 from home, upgrade to RCL2, build spawn/ramparts/tower; cq.workers, default 4)
//   cq.autoSafe true -> workers activate safe mode in W47N8 when available (and re-activate when it ends). Default OFF:
//                     standing rule "never activate safe mode automatically" -> the owner must switch it on explicitly.
// Auto-retreat (before W47N8 is ours & in safe mode): any squad member < 70% hits, a hostile tower with energy,
// or armed hostile dps in the squad's room > total squad heal -> cmd 'retreat' (stays until a human sets a new cmd).
const ROOM = 'W47N8', HOME = 'W46N8', FORBID = new Set(['W47N9', 'W48N9', 'W48N8']);
const MIN_Y = 8, LOG_CAP = 200, HEAL_PER = 12, ATK_DMG = 30, RA_DMG = 10;
const HOLD_POS = { room: HOME, x: 3, y: 20 }, HOME_SAFE = { room: HOME, x: 28, y: 24 };
const PATROL = [[22, 10], [32, 10], [36, 12], [28, 14]];     // north side, y>=8
const CTRL = [15, 25], SPAWN_POS = [12, 26], TOWER_POS = [14, 28], WAIT_POS = [10, 24];
const SQUAD_BODY = () => [].concat(Array(6).fill(RANGED_ATTACK), Array(2).fill(HEAL), Array(8).fill(MOVE)); // 1800: 60 ranged dmg, 24 heal
const BREAKER_BODY = () => [CLAIM, CLAIM, CLAIM, MOVE, MOVE, MOVE];                                       // 1950, 3 reservation ticks/tick (RCL6 cap 2300)
const WORKER_BODY = () => [].concat(Array(5).fill(WORK), Array(5).fill(CARRY), Array(5).fill(MOVE));     // 1000, carries 250
const STORAGE_FLOOR = 3100; // keep the 1300 defender reserve (same gate as the probe)
const ROLES = ['cqsquad', 'cqbreaker', 'cqworker'];

const M = () => (Memory.ops = Memory.ops || {}, Memory.ops.cq = Memory.ops.cq || {});
function log(ev) { const P = M(); P.log = P.log || []; P.log.push(Object.assign({ t: Game.time }, ev)); if (P.log.length > LOG_CAP) P.log.splice(0, P.log.length - LOG_CAP); }
const act = (h, t) => h.body.filter(p => p.type === t && p.hits > 0).length;
const boostK = h => h.body.some(p => p.boost) ? 4 : 1;
const dps = h => (act(h, ATTACK) * ATK_DMG + act(h, RANGED_ATTACK) * RA_DMG) * boostK(h);
const armed = h => act(h, ATTACK) + act(h, RANGED_ATTACK) > 0;
const melee = h => act(h, ATTACK) > 0;
const rng = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
const AB = { move: 'M', work: 'W', carry: 'C', attack: 'A', ranged_attack: 'R', heal: 'H', claim: 'K', tough: 'T' };
const bodyStr = h => _.map(_.countBy(h.body, 'type'), (n, t) => n + (AB[t] || t)).join('');
const enemy = h => !h.owner || h.owner.username !== 'Source Keeper';

// ---- pure decisions (unit-tested) ----
// squad: [{hits,hitsMax,heal(active parts)}]; reason or null
function danger(squad, hostiles, towers) {
  for (const m of squad) if (m.hits < m.hitsMax * 0.7) return 'hits<70%';
  if (towers.some(t => (t.store ? t.store[RESOURCE_ENERGY] : t.energy) >= 10)) return 'hostile tower';
  const heal = squad.reduce((a, m) => a + m.heal * HEAL_PER, 0), d = hostiles.filter(armed).reduce((a, h) => a + dps(h), 0);
  if (d > heal) return `outgunned dps ${d} > heal ${heal}`;
  return null;
}
// CLAIM (reserver) > healers > armed (by dps) > haulers > miners > rest; then nearest, then lowest hits
function prio(h) { return act(h, CLAIM) ? 0 : act(h, HEAL) ? 1 : armed(h) ? 2 : act(h, CARRY) ? 3 : act(h, WORK) ? 4 : 5; }
function pickTarget(pos, hs, focusId) {
  const f = focusId && hs.find(h => h.id === focusId); if (f) return f;
  return _.sortBy(hs, h => prio(h) * 1e6 + (armed(h) ? -dps(h) : 0) * 1e3 + rng(pos, h.pos) * 1e4 + h.hits)[0];
}
// kite: stay at range 3 from melee, close to 3 from pure-ranged; step toward buddy when far
function kiteStep(me, target, buddy, hostiles) {
  if (!target) return null;
  const nearMelee = hostiles.filter(melee).filter(h => rng(me.pos, h.pos) <= 2);
  if (nearMelee.length) {
    // step away from the closest melee, prefer tiles that keep buddy in range 1-2
    let best = null, bestScore = -1e9;
    for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) {
      if (!dx && !dy) continue;
      const nx = me.pos.x + dx, ny = me.pos.y + dy;
      if (nx < 1 || nx > 48 || ny < MIN_Y || ny > 48) continue;
      const minMelee = Math.min(...nearMelee.map(h => Math.max(Math.abs(nx - h.pos.x), Math.abs(ny - h.pos.y))));
      const toBuddy = buddy ? Math.max(Math.abs(nx - buddy.pos.x), Math.abs(ny - buddy.pos.y)) : 1;
      const score = minMelee * 10 - Math.abs(toBuddy - 1) * 3;
      if (score > bestScore) { bestScore = score; best = { x: nx, y: ny }; }
    }
    return best;
  }
  const r = rng(me.pos, target.pos);
  if (r > 3) return { x: target.pos.x, y: target.pos.y, range: 3 };
  if (r < 3 && armed(target) && !melee(target)) return null; // already fine for pure RA
  if (buddy && rng(me.pos, buddy.pos) > 2) return { x: buddy.pos.x, y: buddy.pos.y, range: 1 };
  return null;
}
function matrixFor(rn, m) {
  if (FORBID.has(rn)) { for (let x = 0; x < 50; x++) for (let y = 0; y < 50; y++) m.set(x, y, 255); return m; }
  if (rn === ROOM) for (let x = 0; x < 50; x++) for (let y = 0; y < MIN_Y; y++) m.set(x, y, 255);
  return m;
}
function travel(c, rn, x, y, range = 1) {
  if (c.room.name === rn && c.pos.inRangeTo(x, y, range)) return true;
  c.moveTo(new RoomPosition(x, y, rn), { range, reusePath: 5, maxRooms: 4, costCallback: matrixFor, visualizePathStyle: undefined });
  return false;
}
function setCmd(cmd, why) { const P = M(); if (P.cmd !== cmd) { log({ ev: 'cmd', from: P.cmd, to: cmd, why }); P.cmd = cmd; } }
function ours() { return Game.rooms[ROOM] && Game.rooms[ROOM].controller && Game.rooms[ROOM].controller.my; }
function inSafe() { const r = Game.rooms[ROOM]; return r && r.controller && r.controller.my && r.controller.safeMode; }
function list(role) { return _.filter(Game.creeps, c => c.memory.role === role); }

// ---- combat helpers ----
function mutualHeal(c, buddy) {
  // heal the more-hurt of self / buddy; prefer other when both hurt so we don't waste a heal tick on full HP
  const candidates = [c];
  if (buddy && c.pos.inRangeTo(buddy, 1)) candidates.push(buddy);
  const need = candidates.filter(x => x.hits < x.hitsMax);
  if (!need.length) { if (c.hits < c.hitsMax) c.heal(c); return; }
  need.sort((a, b) => (a.hits / a.hitsMax) - (b.hits / b.hitsMax));
  c.heal(need[0]);
}
function shoot(c, hostiles, focus) {
  const inR = hostiles.filter(h => c.pos.inRangeTo(h, 3));
  if (!inR.length) return;
  if (inR.length >= 3) return c.rangedMassAttack();
  const t = (focus && c.pos.inRangeTo(focus, 3)) ? focus : pickTarget(c.pos, inR);
  if (t) c.rangedAttack(t);
}

// ---- roles ----
function runSquad(c) {
  const P = M(), cmd = P.cmd || 'hold';
  if (FORBID.has(c.room.name)) { log({ ev: 'forbidden', role: 'cqsquad', room: c.room.name }); return travel(c, ROOM, 30, 20, 3); }
  const hostiles = c.room.find(FIND_HOSTILE_CREEPS).filter(enemy);
  const towers = c.room.find(FIND_HOSTILE_STRUCTURES).filter(s => s.structureType === STRUCTURE_TOWER);
  // events
  P.seen = P.seen || {};
  for (const h of hostiles) if (!P.seen[h.id]) { P.seen[h.id] = Game.time; log({ ev: 'hostile', id: h.id, owner: h.owner && h.owner.username, name: h.name, body: bodyStr(h), boosted: h.body.some(p => p.boost) || undefined, pos: [h.pos.x, h.pos.y], room: c.room.name, ttl: h.ticksToLive }); }
  for (const id in P.seen) if (Game.time - P.seen[id] > 1500) delete P.seen[id];
  if (P.lastHits && P.lastHits[c.name] !== undefined && c.hits < P.lastHits[c.name]) log({ ev: 'damage', name: c.name, dmg: P.lastHits[c.name] - c.hits, hits: c.hits, pos: [c.pos.x, c.pos.y], room: c.room.name });
  P.lastHits = P.lastHits || {}; P.lastHits[c.name] = c.hits;
  if (P.tg && P.tg[c.name]) { const t = Game.getObjectById(P.tg[c.name].id); if (!t && P.tg[c.name].t === Game.time - 1 && P.tg[c.name].hits <= 60) log({ ev: 'kill', name: P.tg[c.name].name, body: P.tg[c.name].body }); if (!t) delete P.tg[c.name]; }

  const squad = list('cqsquad');
  // auto-retreat only before we own the room under safe mode (once ours+safe, stay and fight under SM)
  if (!inSafe() && cmd !== 'retreat') {
    const snap = squad.map(s => ({ hits: s.hits, hitsMax: s.hitsMax, heal: act(s, HEAL) }));
    const why = danger(snap, hostiles, towers);
    if (why) { log({ ev: 'auto-retreat', why, room: c.room.name, pos: [c.pos.x, c.pos.y] }); P.auto = { why, t: Game.time }; setCmd('retreat', why); }
  }
  const buddy = _.min(squad.filter(s => s.name !== c.name), s => rng(c.pos, s.pos));
  const bud = (buddy && buddy !== Infinity) ? buddy : null;

  if ((P.cmd || 'hold') === 'retreat') { shoot(c, hostiles); mutualHeal(c, bud); return travel(c, HOME_SAFE.room, HOME_SAFE.x, HOME_SAFE.y, 2); }
  if ((P.cmd || 'hold') === 'hold' || c.room.name !== ROOM) {
    mutualHeal(c, bud);
    // stick together: the lagging one catches up before we leave home
    if (bud && c.room.name === HOME && rng(c.pos, bud.pos) > 2) return travel(c, HOME, bud.pos.x, bud.pos.y, 1);
    if ((P.cmd || 'hold') === 'hold') return travel(c, HOLD_POS.room, HOLD_POS.x, HOLD_POS.y, 1);
    // go: walk into W47N8 together
    return travel(c, ROOM, PATROL[0][0], PATROL[0][1], 2);
  }
  // in W47N8 under 'go'
  const owner = P.owner || 'BustJetter';
  const targets = hostiles.filter(h => !h.owner || h.owner.username === owner || armed(h));
  const focusId = P.focus; // shared focus so both shoot the same target
  let target = targets.length ? pickTarget(c.pos, targets, focusId) : null;
  if (target) { P.focus = target.id; P.tg = P.tg || {}; P.tg[c.name] = { id: target.id, name: target.name, body: bodyStr(target), hits: target.hits, t: Game.time }; }
  else delete P.focus;
  shoot(c, hostiles, target);
  mutualHeal(c, bud);
  // keep buddy close
  if (bud && rng(c.pos, bud.pos) > 2 && (!target || rng(c.pos, target.pos) > 3)) return travel(c, ROOM, bud.pos.x, bud.pos.y, 1);
  if (target) {
    const step = kiteStep(c, target, bud, hostiles);
    if (step) {
      if (step.range !== undefined) return travel(c, ROOM, step.x, step.y, step.range);
      return c.move(c.pos.getDirectionTo(step.x, step.y));
    }
    return; // hold range
  }
  // patrol north side
  P.pi = P.pi || 0;
  const [px, py] = PATROL[P.pi % PATROL.length];
  if (c.pos.inRangeTo(px, py, 2)) P.pi++;
  travel(c, ROOM, px, py, 2);
}

function runBreaker(c) {
  const P = M(), cmd = P.cmd || 'hold';
  if (FORBID.has(c.room.name)) return travel(c, ROOM, CTRL[0], CTRL[1], 3);
  if (cmd === 'retreat') return travel(c, HOME_SAFE.room, HOME_SAFE.x, HOME_SAFE.y, 2);
  if (cmd === 'hold') return travel(c, HOLD_POS.room, HOLD_POS.x, HOLD_POS.y, 2);
  // go / claim phase
  if (c.room.name !== ROOM) return travel(c, ROOM, CTRL[0], CTRL[1], 1);
  const ctl = c.room.controller;
  if (!ctl) return;
  if (!c.pos.isNearTo(ctl)) return travel(c, ROOM, ctl.pos.x, ctl.pos.y, 1);
  if (ctl.my) { // already ours — idle near controller (workers handle upgrade)
    P.claimed = true; return;
  }
  if (ctl.reservation && ctl.reservation.username && ctl.reservation.username !== (Memory.username || c.owner.username)) {
    const r = c.attackController(ctl);
    if (r === OK) { P.broke = (P.broke || 0) + act(c, CLAIM); log({ ev: 'attackController', left: ctl.reservation.ticksToEnd, by: c.name }); }
    return;
  }
  // free -> claim
  const r = c.claimController(ctl);
  if (r === OK) { P.claimed = true; log({ ev: 'claimed', by: c.name }); }
  else if (r !== ERR_GCL_NOT_ENOUGH) log({ ev: 'claim-fail', code: r, by: c.name });
}

function runWorker(c) {
  const P = M(), cmd = P.cmd || 'hold';
  if (FORBID.has(c.room.name)) return travel(c, ROOM, WAIT_POS[0], WAIT_POS[1], 2);
  if (cmd === 'retreat') return travel(c, HOME_SAFE.room, HOME_SAFE.x, HOME_SAFE.y, 2);
  if (cmd === 'hold') return travel(c, HOLD_POS.room, HOLD_POS.x, HOLD_POS.y, 2);

  // fill at home storage first
  if (c.store[RESOURCE_ENERGY] === 0) {
    const st = Game.rooms[HOME] && Game.rooms[HOME].storage;
    if (!st || st.store[RESOURCE_ENERGY] < STORAGE_FLOOR + 250) return travel(c, HOME, HOLD_POS.x, HOLD_POS.y, 2);
    if (c.room.name !== HOME || !c.pos.isNearTo(st)) return travel(c, HOME, st.pos.x, st.pos.y, 1);
    c.withdraw(st, RESOURCE_ENERGY); return;
  }
  // go to W47N8
  if (c.room.name !== ROOM) return travel(c, ROOM, CTRL[0], CTRL[1], 3);
  const ctl = c.room.controller;
  if (!ctl) return;

  // if not ours yet: wait near controller (breakers claim)
  if (!ctl.my) return travel(c, ROOM, WAIT_POS[0], WAIT_POS[1], 2);

  // sign once
  if (!ctl.sign || ctl.sign.username !== c.owner.username) c.signController(ctl, 'Misaki');

  // upgrade to RCL2 (200) then keep upgrading for safe-mode charges
  if (ctl.level < 2 || (ctl.level === 2 && ctl.progress < 200)) {
    if (!c.pos.inRangeTo(ctl, 3)) return travel(c, ROOM, ctl.pos.x, ctl.pos.y, 3);
    c.upgradeController(ctl); return;
  }

  // autoSafe (opt-in): activate when available and not currently in SM
  if (P.autoSafe && ctl.safeModeAvailable > 0 && !ctl.safeMode && ctl.level >= 2) {
    const r = ctl.activateSafeMode();
    if (r === OK) log({ ev: 'safeMode', left: ctl.safeModeAvailable - 1, by: c.name });
    else log({ ev: 'safeMode-fail', code: r, by: c.name });
  }

  // build spawn then tower then ramparts around them + controller
  const sites = c.room.find(FIND_MY_CONSTRUCTION_SITES);
  if (!sites.length) {
    // place spawn if missing
    if (!c.room.find(FIND_MY_SPAWNS).length && !sites.some(s => s.structureType === STRUCTURE_SPAWN)) {
      c.room.createConstructionSite(SPAWN_POS[0], SPAWN_POS[1], STRUCTURE_SPAWN);
    } else if (ctl.level >= 3 && !c.room.find(FIND_MY_STRUCTURES, { filter: s => s.structureType === STRUCTURE_TOWER }).length) {
      c.room.createConstructionSite(TOWER_POS[0], TOWER_POS[1], STRUCTURE_TOWER);
    } else {
      // ramparts on spawn / tower / controller tiles
      for (const [x, y] of [SPAWN_POS, TOWER_POS, CTRL]) {
        const has = c.room.lookForAt(LOOK_STRUCTURES, x, y).some(s => s.structureType === STRUCTURE_RAMPART)
          || c.room.lookForAt(LOOK_CONSTRUCTION_SITES, x, y).some(s => s.structureType === STRUCTURE_RAMPART);
        if (!has) c.room.createConstructionSite(x, y, STRUCTURE_RAMPART);
      }
    }
  }
  const site = c.pos.findClosestByRange(FIND_MY_CONSTRUCTION_SITES);
  if (site) {
    if (!c.pos.inRangeTo(site, 3)) return travel(c, ROOM, site.pos.x, site.pos.y, 3);
    c.build(site); return;
  }
  // otherwise keep upgrading (charges + RCL3)
  if (!c.pos.inRangeTo(ctl, 3)) return travel(c, ROOM, ctl.pos.x, ctl.pos.y, 3);
  c.upgradeController(ctl);
}

function run(c) {
  const P = M();
  P.status = P.status || {};
  P.status[c.memory.role] = P.status[c.memory.role] || {};
  P.status[c.memory.role][c.name] = { room: c.room.name, pos: [c.pos.x, c.pos.y], hits: c.hits, hitsMax: c.hitsMax, ttl: c.ticksToLive, store: c.store.getUsedCapacity(), t: Game.time };
  P.cmd = P.cmd || 'hold';
  if (c.memory.role === 'cqsquad') return runSquad(c);
  if (c.memory.role === 'cqbreaker') return runBreaker(c);
  if (c.memory.role === 'cqworker') return runWorker(c);
}

// ---- spawn gate (called from managers/spawn.js) ----
function wantSpawn(room) {
  if (!(Memory.ops && Memory.ops.cq && Memory.ops.cq.armed === true)) return null; // INERT until Misaki's go (Memory.ops.cq.armed)
  const P = M();
  if ((P.cmd || 'hold') === 'retreat') return null; // abort: no more conquest spawns
  if (!room.storage || room.storage.store[RESOURCE_ENERGY] < STORAGE_FLOOR) return null;
  const n = r => _.filter(Game.creeps, c => c.memory.role === r).length;
  if (P.spawn) {
    const max = P.squadMax || 2;
    if (n('cqsquad') < max) return { role: 'cqsquad', body: SQUAD_BODY(), mem: { role: 'cqsquad', home: HOME, born: Game.time } };
    // squad filled — clear the one-shot flag (replacements only if cq.respawn)
    if (!P.respawn) P.spawn = false;
  }
  if (P.claim) {
    const bMax = P.breakers || 3, wMax = P.workers || 4;
    if (n('cqbreaker') < bMax && !ours()) return { role: 'cqbreaker', body: BREAKER_BODY(), mem: { role: 'cqbreaker', home: HOME, born: Game.time } };
    // workers only after claimed OR when reservation nearly gone (<400 ticks) so they arrive with energy
    const ctl = Game.rooms[ROOM] && Game.rooms[ROOM].controller;
    const almost = ctl && ctl.reservation && ctl.reservation.ticksToEnd < 400;
    if (n('cqworker') < wMax && (ours() || almost || P.forceWorkers)) {
      return { role: 'cqworker', body: WORKER_BODY(), mem: { role: 'cqworker', home: HOME, born: Game.time } };
    }
    if (ours() && n('cqbreaker') === 0 && n('cqworker') >= wMax && !P.respawn) P.claim = false;
  }
  // replacement of dead squad members during an active 'go'
  if (P.respawn && (P.cmd || 'hold') === 'go' && n('cqsquad') < (P.squadMax || 2)) {
    return { role: 'cqsquad', body: SQUAD_BODY(), mem: { role: 'cqsquad', home: HOME, born: Game.time } };
  }
  return null;
}
function noteSpawned(name, role) { log({ ev: 'spawned', name, role }); }

module.exports = {
  run, danger, pickTarget, prio, dps, kiteStep, matrixFor, wantSpawn, noteSpawned,
  SQUAD_BODY, BREAKER_BODY, WORKER_BODY, PATROL, FORBID, ROOM, HOME, MIN_Y, STORAGE_FLOOR, ROLES,
};
