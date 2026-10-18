// W47N8 conquest (docs/CONQUEST.md). MANUAL via Memory.ops.cq (tools/conquest.py); nothing spawns or moves until cq is set.
//   cq.cmd   'hold'    squad waits at W46N8 (3,20); breakers/workers wait at home too
//            'go'      squad enters W47N8: kill CLAIM creeps (reserver) first, then healers / armed, then the rest; patrols the north side
//            'retreat' everyone (squad, breakers, workers) home on the safe path; all conquest spawning stops (abort)
//   cq.spawn  true -> spawn the squad (cq.squadMax total, default 2)
//   cq.claim  true -> spawn breakers (3CLAIM3M: attackController then claimController; cq.breakers default 2) then workers+cqhaulers
//                     then workers (5W5C5M, carry 250 from home, upgrade to RCL2, build spawn/ramparts/tower; cq.workers, default 4)
//   cq.autoSafe true -> workers activate safe mode in W47N8 when available (and re-activate when it ends). Default OFF:
//                     standing rule "never activate safe mode automatically" -> the owner must switch it on explicitly.
// Retreat ONLY by Misaki's command (cmd='retreat'). danger() is kept as a pure helper for tests / console intel — never auto-fires.
const ROOM = 'W47N8', HOME = 'W46N8', FORBID = new Set(['W47N9', 'W48N9', 'W48N8']);
const MIN_Y = 8, LOG_CAP = 200, HEAL_PER = 12, ATK_DMG = 30, RA_DMG = 10;
const HOLD_POS = { room: HOME, x: 3, y: 20 }, HOME_SAFE = { room: HOME, x: 28, y: 24 };
const PATROL = [[22, 10], [32, 10], [36, 12], [28, 14]];     // north side, y>=8
const CTRL = [15, 25], SPAWN_POS = [15, 18], TOWER_POS = [14, 28], WAIT_POS = [10, 24];
const SQUAD_BODY = () => [].concat(Array(6).fill(RANGED_ATTACK), Array(2).fill(HEAL), Array(8).fill(MOVE)); // 1800: 60 ranged dmg, 24 heal
const BREAKER_BODY = () => [CLAIM, CLAIM, CLAIM, MOVE, MOVE, MOVE];                                       // 1950, 3 reservation ticks/tick (RCL6 cap 2300)
const WORKER_BODY = () => [].concat(Array(8).fill(WORK), Array(8).fill(CARRY), Array(8).fill(MOVE));     // 1600, carries 400 (Misaki 15:25 faster)
const MINER_BODY = () => [].concat(Array(6).fill(WORK), Array(3).fill(MOVE)); // 750, 12/tick on his containers
const SITE = [15, 18];
const MINER_SPOTS = [[26, 11], [11, 43]], MINER_SRC = [[27, 11], [11, 44]];
const STORAGE_FLOOR = 3100; // keep the 1300 defender reserve (same gate as the probe)
const ROLES = ['cqsquad', 'cqbreaker', 'cqworker', 'cqhauler', 'cqatk', 'cqrh', 'cqminer'];

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
  // Retreat ONLY by Misaki's command (cmd='retreat'). No automatic retreat triggers (2026-10-18).
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

function placeSpawn(room) {
  if (room.find(FIND_MY_SPAWNS).length || room.find(FIND_MY_CONSTRUCTION_SITES, { filter: x => x.structureType === STRUCTURE_SPAWN }).length) return;
  const r = room.createConstructionSite(SPAWN_POS[0], SPAWN_POS[1], STRUCTURE_SPAWN);
  const P = M(); if (P.spawnSiteRc !== r) { P.spawnSiteRc = r; log({ ev: 'spawnSite', rc: r, pos: SPAWN_POS }); }
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
  if (ctl.my) { // ours: place the spawn site at once (retry each tick until site/spawn exists), then idle
    P.claimed = true; placeSpawn(c.room); return;
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

// sticky energy pick (patrol 16:20: re-scoring every tick made fetchers oscillate 11,43 <-> 26,11). Keeps memory.tid until the
// target is gone/empty; new picks subtract the free capacity of creeps already heading there.
function stickyPick(c, pool) {
  const amt = o => o.amount !== undefined ? o.amount : o.store[RESOURCE_ENERGY];
  const cur = c.memory.tid && Game.getObjectById(c.memory.tid);
  if (cur && amt(cur) >= 50) return cur;
  const claimed = {};
  for (const n in Game.creeps) { const o = Game.creeps[n]; if (o !== c && o.memory.tid) claimed[o.memory.tid] = (claimed[o.memory.tid] || 0) + o.store.getFreeCapacity(); }
  const best = pool.length ? _.max(pool, o => amt(o) - (claimed[o.id] || 0) - 10 * (o.pos.roomName === c.pos.roomName ? c.pos.getRangeTo(o) : 50)) : null;
  c.memory.tid = best && best.id; return best;
}
function runWorker(c) {
  const P = M(), cmd = P.cmd || 'hold';
  if (FORBID.has(c.room.name)) return travel(c, ROOM, WAIT_POS[0], WAIT_POS[1], 2);
  if (cmd === 'retreat') return travel(c, HOME_SAFE.room, HOME_SAFE.x, HOME_SAFE.y, 2);
  if (cmd === 'hold') return travel(c, HOLD_POS.room, HOLD_POS.x, HOLD_POS.y, 2);

  // Fast RCL2 energy: prefer W47N8's own sources / his leftover containers, else haul from home storage.
  // pure builder (Misaki 15:26): never harvest or walk home; take energy dropped/delivered near the spawn site
  if (c.store[RESOURCE_ENERGY] === 0) {
    if (c.room.name !== ROOM) return travel(c, ROOM, SITE[0], SITE[1], 2);
    // Misaki 16:07: 2 oldest workers stay at the site (fed by haulers); the rest self-fetch anywhere in the room
    const wsAll = _.sortBy(_.filter(Game.creeps, x => x.memory.role === 'cqworker'), x => x.memory.born || 0);
    if (wsAll.findIndex(x => x.name === c.name) >= 2) {
      const pool = c.room.find(FIND_DROPPED_RESOURCES, { filter: r => r.resourceType === RESOURCE_ENERGY && r.amount >= 100 })
        .concat(c.room.find(FIND_STRUCTURES, { filter: s => s.structureType === STRUCTURE_CONTAINER && s.store[RESOURCE_ENERGY] >= 100 }));
      const best = stickyPick(c, pool);
      if (best && best.pos) {
        if (!c.pos.isNearTo(best)) return travel(c, ROOM, best.pos.x, best.pos.y, 1);
        if (best.amount !== undefined) c.pickup(best); else c.withdraw(best, RESOURCE_ENERGY); delete c.memory.tid; return;
      }
    }
    const drop = c.pos.findClosestByRange(FIND_DROPPED_RESOURCES, { filter: r => r.resourceType === RESOURCE_ENERGY && r.amount >= 20 && r.pos.inRangeTo(SITE[0], SITE[1], 6) });
    if (drop) { if (!c.pos.isNearTo(drop)) return travel(c, ROOM, drop.pos.x, drop.pos.y, 1); c.pickup(drop); return; }
    const tomb = c.pos.findClosestByRange(FIND_TOMBSTONES, { filter: t => t.store[RESOURCE_ENERGY] > 0 && t.pos.inRangeTo(SITE[0], SITE[1], 8) });
    if (tomb) { if (!c.pos.isNearTo(tomb)) return travel(c, ROOM, tomb.pos.x, tomb.pos.y, 1); c.withdraw(tomb, RESOURCE_ENERGY); return; }
    if (!c.pos.inRangeTo(SITE[0], SITE[1], 2)) return travel(c, ROOM, SITE[0], SITE[1], 2);
    return; // wait for carriers
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
  placeSpawn(c.room);
  if (ctl.level < 2) { // RCL2 first (200 energy), then everyone builds the spawn
    if (!c.pos.inRangeTo(ctl, 3)) return travel(c, ROOM, ctl.pos.x, ctl.pos.y, 3);
    c.upgradeController(ctl); return;
  }

  // downgrade guard (Misaki 16:02): one dedicated upgrader (oldest worker) from dg<8000 until dg>=9500 (hysteresis, no flapping);
  // everyone upgrades only in an emergency (<3000)
  const ws = _.sortBy(_.filter(Game.creeps, x => x.memory.role === 'cqworker' && x.room.name === ROOM), x => x.memory.born || 0);
  if (ctl.ticksToDowngrade < 8000) P.dgUp = 1; else if (ctl.ticksToDowngrade >= 9500) P.dgUp = 0;
  const up = ws[2] || ws[ws.length - 1]; // dedicated upgrader = a self-fetcher, not a site worker
  if ((P.dgUp && up && up.name === c.name) || ctl.ticksToDowngrade < 3000) {
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
  // spawn site first; never target sites whose build range lies inside the y<MIN_Y no-go rows (north seal walls at y=3:
  // unreachable for travel(), workers oscillated at y=8 holding energy). Those are left to the w8builders after the spawn.
  const site = sites.find(s => s.structureType === STRUCTURE_SPAWN)
    || c.pos.findClosestByRange(FIND_MY_CONSTRUCTION_SITES, { filter: s => s.pos.y + 3 >= MIN_Y });
  if (site) {
    if (!c.pos.inRangeTo(site, 3)) return travel(c, ROOM, site.pos.x, site.pos.y, 3);
    c.build(site); return;
  }
  // otherwise keep upgrading (charges + RCL3)
  if (!c.pos.inRangeTo(ctl, 3)) return travel(c, ROOM, ctl.pos.x, ctl.pos.y, 3);
  c.upgradeController(ctl);
}


// Dedicated home->W47N8 energy ferry (fast RCL2). Body 10C10M (1000). Withdraws home storage (>=floor+carry),
// dumps into W47N8 controller-adjacent container if present else drops next to controller for workers.
const HAULER_BODY = () => [].concat(Array(16).fill(CARRY), Array(16).fill(MOVE)); // 1600, 800 cap
// Continuous solo reinforcements (Misaki 14:35): walk to post 21,7, fight hostiles in range only (CLAIM/armed), no formation.
const REINF_POST = [21, 7], WAYPT = [30, 23]; // Misaki 14:42: route via 30,23
const ATK_BODY = () => [].concat(Array(12).fill(ATTACK), Array(12).fill(MOVE)); // 1560
const RH_BODY = () => [].concat(Array(4).fill(RANGED_ATTACK), Array(4).fill(HEAL), Array(8).fill(MOVE)); // 2000
function runReinf(c) {
  // Route: home -> W47N8 30,23 (r2) -> post 21,7. CLAIM hostiles: chase anywhere in room; else ignore harmless unless in range.
  const P = M(), cmd = P.cmd || 'hold';
  if (FORBID.has(c.room.name)) return travel(c, ROOM, WAYPT[0], WAYPT[1], 3);
  if (cmd === 'retreat') return travel(c, HOME_SAFE.room, HOME_SAFE.x, HOME_SAFE.y, 2);
  if (cmd === 'hold') return travel(c, HOLD_POS.room, HOLD_POS.x, HOLD_POS.y, 2);
  if (c.room.name !== ROOM) return travel(c, ROOM, WAYPT[0], WAYPT[1], 2);
  const hostiles = c.room.find(FIND_HOSTILE_CREEPS).filter(enemy);
  const claimers = hostiles.filter(h => act(h, CLAIM));
  if (claimers.length) {
    const t = pickTarget(c.pos, claimers);
    const inR = c.getActiveBodyparts(ATTACK) ? 1 : 3;
    if (c.pos.inRangeTo(t, inR)) {
      if (c.getActiveBodyparts(ATTACK)) c.attack(t); else c.rangedAttack(t);
    } else if (c.getActiveBodyparts(RANGED_ATTACK) && c.pos.inRangeTo(t, 3)) c.rangedAttack(t);
    if (c.getActiveBodyparts(HEAL) && c.hits < c.hitsMax) c.heal(c);
    if (!c.pos.inRangeTo(t, inR)) return travel(c, ROOM, t.pos.x, t.pos.y, inR);
    return;
  }
  // waypoint once per creep
  if (!c.memory.viaCtl) {
    if (c.pos.inRangeTo(WAYPT[0], WAYPT[1], 2)) c.memory.viaCtl = 1;
    else return travel(c, ROOM, WAYPT[0], WAYPT[1], 2);
  }
  // in-range only vs armed (not chase); heal self
  const inR = c.getActiveBodyparts(ATTACK) ? 1 : 3;
  const near = hostiles.filter(h => armed(h) && c.pos.inRangeTo(h, inR));
  if (near.length) {
    const t = pickTarget(c.pos, near);
    if (c.getActiveBodyparts(ATTACK)) c.attack(t);
    else { if (near.length >= 3) c.rangedMassAttack(); else c.rangedAttack(t); }
  } else {
    const soft = hostiles.filter(h => c.pos.inRangeTo(h, inR));
    if (soft.length) {
      const t = pickTarget(c.pos, soft);
      if (c.getActiveBodyparts(ATTACK)) c.attack(t); else c.rangedAttack(t);
    }
  }
  if (c.getActiveBodyparts(HEAL) && c.hits < c.hitsMax) c.heal(c);
  // melee chases armed hostiles near the post (leash 10 from 21,7), Misaki 14:56
  if (c.getActiveBodyparts(ATTACK) && !near.length) {
    const inLeash = hostiles.filter(h => h.pos.getRangeTo(REINF_POST[0], REINF_POST[1]) <= 10);
    const prey = inLeash.filter(armed).length ? inLeash.filter(armed) : inLeash; // armed first, else any enemy
    if (prey.length) { const t = c.pos.findClosestByRange(prey); return travel(c, ROOM, t.pos.x, t.pos.y, 1); }
  }
  if (!c.pos.inRangeTo(REINF_POST[0], REINF_POST[1], 3)) return travel(c, ROOM, REINF_POST[0], REINF_POST[1], 2);
}

// static miner on his leftover source containers until W47N8 has its own w8miners
function runMiner(c) {
  // memory.ms (not 'spot': main.js v2 migration deletes 'spot' on a creep's first tick -> every miner went north, spawn loop)
  const i = c.memory.ms != null ? c.memory.ms : (c.memory.spot || 0), [x, y] = MINER_SPOTS[i];
  // dedupe: one miner per spot; extras (younger ones, unless already on the tile) walk home and recycle
  const same = _.filter(Game.creeps, m => m.memory.role === 'cqminer' && (m.memory.ms != null ? m.memory.ms : 0) === i && !m.spawning);
  const fresh = same.filter(m => (m.ticksToLive || 1500) > 80), keeper = fresh.length ? _.max(fresh, m => m.memory.born || 0) : null; // youngest stays
  if (keeper && keeper.name !== c.name) {
    // surplus (Misaki 16:09): never walk home. One 6W miner already exceeds a source's 10/t, so an extra adds no income -> suicide.
    return c.suicide();
  }
  if (c.room.name !== ROOM) return travel(c, ROOM, x, y, 0);
  const src = c.room.lookForAt(LOOK_SOURCES, MINER_SRC[i][0], MINER_SRC[i][1])[0];
  if (c.pos.x === x && c.pos.y === y) { if (src) c.harvest(src); return; }
  // container tile taken (his creep / another miner): mine from any tile next to the source
  const blocked = c.room.lookForAt(LOOK_CREEPS, x, y).length > 0;
  if (blocked && src && c.pos.isNearTo(src)) return c.harvest(src);
  if (blocked && src) return travel(c, ROOM, src.pos.x, src.pos.y, 1);
  return travel(c, ROOM, x, y, 0);
}

// W47N8 ENERGY FLOW (Misaki 16:09):
//   cqminers on 26,11 / 11,43 -> containers -> cqhaulers -> site 15,18 (2 stationary cqworkers) ; self-fetch cqworkers take
//   containers/drops directly ; dg upgrader (a fetcher) upgrades 15,25 when dg<8000.
//   Home storage is a FALLBACK only: an EMPTY-ish (<50%) hauler with no in-room container>=300/drop>=150 fetches from W46N8.
//   No W47N8 role ever returns to W46N8 except that hauler case.
function runHauler(c) {
  const P = M(), cmd = P.cmd || 'hold';
  if (FORBID.has(c.room.name)) return travel(c, ROOM, WAIT_POS[0], WAIT_POS[1], 2);
  if (cmd === 'retreat') return travel(c, HOME_SAFE.room, HOME_SAFE.x, HOME_SAFE.y, 2);
  if (c.store[RESOURCE_ENERGY] === 0) c.memory.full = false;
  if (c.store[RESOURCE_ENERGY] >= c.store.getCapacity() / 2) c.memory.full = true; // >=50% -> deliver, never fetch more from home
  if (!c.memory.full) {
    // pure carrier (Misaki 15:26): W47N8 miner containers / drops first, else home storage
    const r8 = Game.rooms[ROOM];
    const conts = r8 ? r8.find(FIND_STRUCTURES, { filter: s => s.structureType === STRUCTURE_CONTAINER && s.store[RESOURCE_ENERGY] >= 300 && !s.pos.inRangeTo(SITE[0], SITE[1], 6) }) : [];
    const drops = r8 ? r8.find(FIND_DROPPED_RESOURCES, { filter: d => d.resourceType === RESOURCE_ENERGY && d.amount >= 150 && !d.pos.inRangeTo(SITE[0], SITE[1], 6) }) : [];
    if (c.store[RESOURCE_ENERGY] > 0 && !conts.length && !drops.length && c.room.name === ROOM) { c.memory.full = true; return; }
    const tgt = stickyPick(c, conts.length ? conts : drops); // sticky, containers first
    if (tgt && tgt.pos) {
      if (!c.pos.isNearTo(tgt)) return travel(c, ROOM, tgt.pos.x, tgt.pos.y, 1);
      if (tgt.amount !== undefined) c.pickup(tgt); else c.withdraw(tgt, RESOURCE_ENERGY); delete c.memory.tid; return;
    }
    const st = Game.rooms[HOME] && Game.rooms[HOME].storage;
    // home first (Misaki 16:25: home must not slip): fetch only above reserveE+5k (17:05: storage 25k->15k in 10 min, cqhaulers
    // would have pulled it to 3.6k while home builders/upgraders are gated below reserveE)
    const homeFloor = Math.max(STORAGE_FLOOR + 500, ((Memory.defense && Memory.defense.reserveE) || 0) + 5000);
    if (!st || st.store[RESOURCE_ENERGY] < homeFloor) return travel(c, ROOM, SITE[0], SITE[1], 3);
    if (c.room.name !== HOME || !c.pos.isNearTo(st)) return travel(c, HOME, st.pos.x, st.pos.y, 1);
    c.withdraw(st, RESOURCE_ENERGY); return;
  }
  // spawn built: fill Spawn2 / extensions first so the room can spawn its own w8 creeps (takeover), then feed builders
  const fill = c.room.name === ROOM && c.pos.findClosestByRange(FIND_MY_STRUCTURES, { filter: s => (s.structureType === STRUCTURE_SPAWN
    || s.structureType === STRUCTURE_EXTENSION) && s.store.getFreeCapacity(RESOURCE_ENERGY) > 0 });
  if (fill) { if (!c.pos.isNearTo(fill)) return travel(c, ROOM, fill.pos.x, fill.pos.y, 1); c.transfer(fill, RESOURCE_ENERGY); return; }
  if (c.room.name !== ROOM || !c.pos.inRangeTo(SITE[0], SITE[1], 2)) {
    // hand off to an empty builder on the way if adjacent
    return travel(c, ROOM, SITE[0], SITE[1], 2);
  }
  // never drop energy (Misaki 16:16): hand it to the hungriest builder (cqworker or w8builder: cqworkers die out after Spawn2) near the site; else wait
  const ws = c.room.find(FIND_MY_CREEPS, { filter: x => (x.memory.role === 'cqworker' || x.memory.role === 'w8builder') && x.store.getFreeCapacity(RESOURCE_ENERGY) > 0 && x.pos.inRangeTo(SITE[0], SITE[1], 6) });
  if (!ws.length) return;
  const w = _.max(ws, x => x.store.getFreeCapacity(RESOURCE_ENERGY) * 10 - c.pos.getRangeTo(x));
  if (!c.pos.isNearTo(w)) { travel(c, ROOM, w.pos.x, w.pos.y, 1); const n = c.pos.findInRange(ws, 1)[0]; if (n) c.transfer(n, RESOURCE_ENERGY); return; }
  c.transfer(w, RESOURCE_ENERGY);
}

function run(c) {
  const P = M();
  P.status = P.status || {};
  P.status[c.memory.role] = P.status[c.memory.role] || {};
  P.status[c.memory.role][c.name] = { room: c.room.name, pos: [c.pos.x, c.pos.y], hits: c.hits, hitsMax: c.hitsMax, ttl: c.ticksToLive, store: c.store.getUsedCapacity(), t: Game.time };
  P.cmd = P.cmd || 'hold';
  if (c.memory.role === 'cqsquad') return runSquad(c);
  if (c.memory.role === 'cqbreaker') return runBreaker(c);
  if (c.memory.role === 'cqminer') return runMiner(c);
  if (c.memory.role === 'cqworker') return runWorker(c);
  if (c.memory.role === 'cqhauler') return runHauler(c);
  if (c.memory.role === 'cqatk' || c.memory.role === 'cqrh') return runReinf(c);
}

// ---- spawn gate (called from managers/spawn.js) ----
// standing W47N8 melee guard (Misaki 16:06/16:30): always 1 cqatk. Prespawn when the youngest has < spawn(72t) + walk(~130t) + margin
// so the replacement reaches 24,8 before the old one dies. Called FIRST from managers/spawn.js (ahead of remotes) and in wantSpawn.
const GUARD_LEAD = 230;
function guardWant() {
  if (!(Memory.ops && Memory.ops.cq && Memory.ops.cq.armed === true) || !ours()) return null;
  const P = M(), gq = P.guard8 == null ? 1 : P.guard8;
  const gs = _.filter(Game.creeps, c => c.memory.role === 'cqatk' && (c.spawning || (c.ticksToLive || 1500) > GUARD_LEAD));
  return gs.length < gq ? { role: 'cqatk', body: ATK_BODY(), mem: { role: 'cqatk', g8: 1, v2: 1, home: HOME, born: Game.time } } : null;
}
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
    const bMax = P.breakers || 2, wMax = P.workers || 4;
    const ctl = Game.rooms[ROOM] && Game.rooms[ROOM].controller;
    const almost = ctl && ctl.reservation && ctl.reservation.ticksToEnd < 1200;
    // backup breaker if the living ones may expire before the reservation hits 0 (~7/tick)
    const brs = _.filter(Game.creeps, c => c.memory.role === 'cqbreaker');
    const need = ctl && ctl.reservation ? ctl.reservation.ticksToEnd / 7 + 40 : 0;
    const short = brs.length && _.max(brs.map(c => c.ticksToLive || 1500)) < need;
    if ((n('cqbreaker') < bMax || (short && n('cqbreaker') < bMax + 1)) && !ours()) return { role: 'cqbreaker', body: BREAKER_BODY(), mem: { role: 'cqbreaker', home: HOME, born: Game.time } };
    // pioneers before more reinforcements once the claim is near (Misaki 15:06)
    const self8 = require('../rooms/w47n8/index').selfSufficient(); // W47N8 runs itself -> no more pioneers/cqhaulers from home
    { const g = guardWant(); if (g) return g; }
    if (!self8 && ours()) {
      const ms = _.filter(Game.creeps, c => c.memory.role === 'cqminer');
      for (let i = 0; i < MINER_SPOTS.length; i++) if (!ms.some(c => (c.memory.ms != null ? c.memory.ms : -1) === i && (c.spawning || c.ticksToLive > 80)))
        return { role: 'cqminer', body: MINER_BODY(), mem: { role: 'cqminer', ms: i, v2: 1, home: HOME, born: Game.time } };
    }
    if (!self8 && n('cqworker') < wMax && (ours() || almost || P.forceWorkers)) {
      return { role: 'cqworker', body: WORKER_BODY(), mem: { role: 'cqworker', home: HOME, born: Game.time } };
    }
    const hMax = P.haulers || 2;
    if (!self8 && n('cqhauler') < hMax && (ours() || almost || P.forceWorkers)) {
      return { role: 'cqhauler', body: HAULER_BODY(), mem: { role: 'cqhauler', home: HOME, born: Game.time } };
    }
    // continuous solo reinf to post 21,7 (after at least one breaker out or already ours)
    if (P.reinf !== false && (n('cqbreaker') > 0 || ours() || P.forceReinf)) {
      const aMax = P.reinfAtk || 4, rMax = P.reinfRh || 4;
      // strict alternation (Misaki 14:45): fewer alive goes next, tie -> cqatk
      const na = n('cqatk'), nr = n('cqrh'), atkNext = na <= nr;
      if (atkNext && na < aMax) return { role: 'cqatk', body: ATK_BODY(), mem: { role: 'cqatk', home: HOME, born: Game.time } };
      if (nr < rMax) return { role: 'cqrh', body: RH_BODY(), mem: { role: 'cqrh', home: HOME, born: Game.time } };
      if (na < aMax) return { role: 'cqatk', body: ATK_BODY(), mem: { role: 'cqatk', home: HOME, born: Game.time } };
    }
  }
  // replacement of dead squad members during an active 'go'
  if (P.respawn && (P.cmd || 'hold') === 'go' && n('cqsquad') < (P.squadMax || 2)) {
    return { role: 'cqsquad', body: SQUAD_BODY(), mem: { role: 'cqsquad', home: HOME, born: Game.time } };
  }
  return null;
}
function noteSpawned(name, role) { log({ ev: 'spawned', name, role }); }

module.exports = {
  run, danger, pickTarget, prio, dps, kiteStep, matrixFor, wantSpawn, guardWant, noteSpawned,
  SQUAD_BODY, BREAKER_BODY, WORKER_BODY, HAULER_BODY, ATK_BODY, RH_BODY, PATROL, FORBID, ROOM, HOME, MIN_Y, STORAGE_FLOOR, ROLES,
};
