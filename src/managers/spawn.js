// Spawn manager v2: per-RCL role table (docs/LAYOUT_V2.md). Counts come from Game.creeps (no room searches).
// Bodies are sized from energyCapacity; if the room has not been full for 300 ticks, sizes fall back to what is available.
const plan = require('../utils/plan'), rc = require('../utils/roomcache');
const rep = (n, p) => Array(Math.max(0, n)).fill(p);
// Birth side. The extension stamp around the spawn is closed except through its fill container, and the default order
// (TOP first) put new creeps on filler tile 36,27 inside it: they walked out through the queen ring, and
// upgrader83620552 (10W1C1M) needed 274 ticks from spawn to 31,30 (10-13 22:27). Born outside the stamp first;
// queen/fillers inside (any stamp tile counts as inside). All 8 directions stay in the list, so a blocked side falls back to the engine default.
const DXY = { 1: [0, -1], 2: [1, -1], 3: [1, 0], 4: [1, 1], 5: [0, 1], 6: [-1, 1], 7: [-1, 0], 8: [-1, -1] };
function birthDirs(spawn, role) {
  const P = plan.get(spawn.room.name); if (!P) return undefined;
  const inside = new Set([].concat(...Object.values(P.raw.stamps).map(st => Object.keys(st.tiles))).map(k => { const [x, y] = k.split(',').map(Number); return plan.key(x, y); }));
  const isIn = d => inside.has(plan.key(spawn.pos.x + DXY[d][0], spawn.pos.y + DXY[d][1]));
  const want = role === 'queen' || role === 'filler', all = [1, 2, 3, 4, 5, 6, 7, 8];
  const out = all.filter(d => isIn(d) === want);
  // remote creeps: outside tiles ordered by range to the remote's home exit (W45N8: exitHome 49,14 -> NE of spawn 35,28)
  const R = require('./remote').CFG, rc0 = REMOTE_ROLES.has(role) && Object.values(R).find(c => c.home === spawn.room.name);
  if (rc0) { const [ex, ey] = rc0.exitHome, d2 = d => { const dx = Math.abs(spawn.pos.x + DXY[d][0] - ex), dy = Math.abs(spawn.pos.y + DXY[d][1] - ey); return Math.max(dx, dy) * 100 + dx + dy; };
    out.sort((a, b) => d2(a) - d2(b)); }
  return out.concat(all.filter(d => isIn(d) !== want));
}
const REMOTE_ROLES = new Set(['rminer', 'rhauler', 'reserver', 'defender', 'rscout']);
const B = {
  // anti-Invader: 5 RANGED_ATTACK + 6 MOVE + 1 HEAL = 1300 (RCL4 full cap); 50 dmg/t at range 3, 12 hp/t self-heal
  defender: e => e >= 1300 ? [].concat(rep(5, RANGED_ATTACK), rep(6, MOVE), [HEAL]) : [].concat(rep(3, RANGED_ATTACK), rep(4, MOVE)),
  harvester: e => { const n = Math.max(1, Math.min(5, Math.floor(e / 200))); return [].concat(rep(n, WORK), rep(n, CARRY), rep(n, MOVE)); },
  miner: (e, carry) => { const c = carry ? 1 : 0; const w = Math.max(2, Math.min(5, Math.floor((e - 50 - c * 50) / 100)));
    const m = Math.max(1, Math.min(3, Math.floor((e - w * 100 - c * 50) / 50))); return [].concat(rep(w, WORK), rep(c, CARRY), rep(m, MOVE)); },
  hauler: e => { const n = Math.max(2, Math.min(8, Math.floor(e / 100))); return [].concat(rep(n, CARRY), rep(n, MOVE)); },
  // home hauler with storage: the A->ctl route is fully paved, so 2 CARRY : 1 MOVE still moves 1 tile/tick loaded
  roadHauler: (e, max = 8) => { const n = Math.max(1, Math.min(max, Math.floor(e / 150))); return [].concat(rep(2 * n, CARRY), rep(n, MOVE)); },
  queen: e => { const n = Math.max(2, Math.min(6, Math.floor(e / 150))); return [].concat(rep(2 * n, CARRY), rep(n, MOVE)); },
  // Upgraders walk once (spawn -> ctl spot, ~6 tiles) then sit, so 1 MOVE is enough. RCL4: 2x10W = 20 WORK was the binding
  // limit (1h upgrade ~19/t, ctl container 1000+ unused, storage parked at the ferry floor so the 3rd-upgrader gate never opened;
  // patrol 10-14 10:55). Cap 12 -> 12W1C1M = 1300 = RCL4 full cap, 2x12 = 24 WORK ~ model ideal 23.5.
  upgrader: (e, rcl) => { const w = Math.max(1, Math.min(rcl >= 8 ? 15 : 12, Math.floor((e - 100) / 100))); return [].concat(rep(w, WORK), [CARRY, MOVE]); },
  guard: e => { const n = Math.max(1, Math.min(6, Math.floor((e - 300) / 200))); return [].concat(rep(n, RANGED_ATTACK), rep(n + 1, MOVE), [HEAL]); },
  // builder cap 8W8C8M (1600e) at RCL6: 400 carry, fewer refill walks (was 5W5C5M)
  builder: e => { const n = Math.max(1, Math.min(11, Math.floor(e / 200))); return [].concat(rep(n, WORK), rep(n, CARRY), rep(n, MOVE)); },
  filler: e => [CARRY, CARRY, CARRY, MOVE],
  manager: e => [].concat(rep(Math.min(16, Math.floor((e - 50) / 50)), CARRY), [MOVE]),
};
function remoteSites() { let n = 0; try { for (const r of ['W45N8']) { const rm = typeof Game !== 'undefined' && Game.rooms && Game.rooms[r]; if (rm) n += rm.find(FIND_MY_CONSTRUCTION_SITES).filter(s => s.structureType === STRUCTURE_ROAD).length; } } catch (e) {} return n; }
function targets(room, count, backlog, ctlEnergy, sites) {
  const rcl = room.controller.level, P = plan.get(room.name);
  const st = !!room.storage, links = rc.all(room, STRUCTURE_LINK).length;
  const T = {};
  // With storage, miner B dumps adjacent (38,32→37,31) so only source A needs a hauler: 1×14C7M road hauler (see body note below).
  // Pre-storage keep 2 so both containers drain. Backlog can still add one extra.
  T.hauler = rcl >= 7 && links >= 4 ? 0 : (rcl >= 6 && links >= 3 ? 1 : (st ? Math.min(2, 1 + Math.floor(backlog / 1500)) : Math.min(4, 2 + Math.floor(backlog / 1500))));
  const fillersOn = plan.STATIONARY_FILL && rcl >= 5 && links >= 2; // off: queen regime at RCL5+ (docs/RCL5.md)
  T.queen = fillersOn ? 0 : 1;
  T.filler = fillersOn ? 4 : 0;
  T.manager = plan.STATIONARY_FILL && st && rcl >= 5 ? 1 : 0; // manager tile 36,30 is also a queen stop
  // Supply-follows-demand on the smoothed ctl container level (ctlEnergy = ~300-tick EMA): an empty container means upgraders
  // outnumber the feed. A snapshot rule (3 + level/700) spawned 4x7 WORK for ~11/t feed -> upgraders idle 55% waiting_feed (10-13 17:30).
  // With storage, the 3rd+ upgrader needs real surplus: storage SURPLUS above the queen's ferry floor (max(defender reserve, cap)).
  // Below that the queen still ferries storage->ctl, so a full ctl container is only a transient (e.g. a container A backlog drain).
  // Gate at the bare reserve (1300) spawned a 3rd 10W at ~08:00 10-14 while the ferry had not even started (floor+carry 1700):
  // waiting_feed 0-18% (2 upgraders, 07:30-07:59) -> 45-47% (3 upgraders, 08:00-08:14). (patrol 10-14 04:53 had the same: storage ~100.)
  const SURPLUS = 1000;
  const extra = Math.floor(ctlEnergy / 700);
  const allowExtra = !st || room.storage.store[RESOURCE_ENERGY] >= require('../roles/queen').storageFloor(room) + SURPLUS;
  T.upgrader = rcl >= 8 ? 1 : Math.min(P.pos.upgraders.length, (sites ? 1 : 2) + (allowExtra ? extra : 0));
  // RCL6+ wall banking (managers/walls.js): one upgrader until storage reaches the wall start (20k), then the latch releases it.
  if (rcl >= 6 && rcl < 8 && ['bank', 'roads'].includes(require('./walls').phase(room))) T.upgrader = Math.min(T.upgrader, 1);
  // Build hold (walls.noUpgrade): 0 upgraders during the road plan; falls back to the 1 minimal (700e) upgrader above
  // when ticksToDowngrade < walls.UP_SAFE. After roads: 'bank' keeps 1 upgrader until storage 20k (storage accumulates).
  if (require('./walls').noUpgrade(room)) T.upgrader = 0;
  // RCL4 extension push: 2 builders need ~40 e/t but net income ~22 -> spawn/ctl starve, builders no_task ~28%,
  // haulers wait on empty pickups (patrol 10-13 18:40). One fed builder finishes sites faster than two hungry ones.
  // Second builder only after cap>=1300 (20 ext, CLAIM2-ready) when the room can afford the extra demand.
  // With storage + sites=0 a lone builder cannot withdraw below threat.reserve, walks to source A / upgrades as a
  // hungry 5W, and keeps storage off the 1300 defender cushion (patrol 10-14 02:54 → 03:54, storage 1040→50→~100).
  T.builder = sites ? (sites > 3 && room.energyCapacityAvailable >= 1300 ? 2 : 1) : (st ? 0 : (rcl <= 4 ? 1 : 0));
  if (!T.builder && st && require('./walls').wantBuilder(room)) T.builder = 1; // wall-phase barrier repair (funded)
  // remote road sites (remote.CFG roads, not multi-hop) only count once nothing at home needs a builder (patrol 10-17 07:25:
  // W45N8 2,12 swamp site 0/1500 for days; loaded W45N8 rhaulers lose ~4t per trip on the 3,12 swamp, container overflows at 2000)
  if (!T.builder && st && require('../roles/builder').remoteRoadSite()) T.builder = 1;
  // RCL6 road plan (docs/ROADS.md): remote road phases get a 2nd builder once storage holds a cushion; route roads < 40% get one.
  if (st && rcl >= 6) { const RD = require('./roads');
    // build hold: the upgrader's ~6/t goes to builders; a 3rd builder once storage holds a cushion and >=3 sites are open
    if (T.builder === 2 && sites >= 3 && require('./walls').noUpgrade(room) && room.storage.store[RESOURCE_ENERGY] >= 3000) T.builder = 3;
    if (require('./walls').noUpgrade(room)) { // v2.1 build mode: spend storage down toward ~3k (Misaki 22:45); remote road sites count too
      const all = sites + remoteSites(), e = room.storage.store[RESOURCE_ENERGY];
      if (all >= 3 && T.builder < 2 && room.energyCapacityAvailable >= 1300) T.builder = 2; // >=3 so swamp7's 3 remote sites still bump (was >3 -> stuck at 1)
      if (T.builder >= 2 && all >= 4 && e >= 5000) T.builder = 4;
      if (T.builder >= 4 && all >= 8 && e >= 8000) T.builder = 5;
      if (T.builder >= 2 && T.builder < 3 && all >= 3 && e >= 3000) T.builder = 3; }
    if (T.builder === 1 && !sites && (/^W45N/.test(RD.phase()) || RD.phase() === 'swamp7' || remoteSites() > 0) && room.storage.store[RESOURCE_ENERGY] >= 5000 && room.energyCapacityAvailable >= 1300) T.builder = 2;
    if (!T.builder && RD.repairTarget(0.4)) T.builder = 1;
    // walls build phase: 1 builder (sites<=SITE_CAP 2) walking 35,24 -> 13-18,44 with 250 carry built ~3 e/t while the fund sat at
    // ~22k and storage 23k (patrol 10-18 02:12, Misaki: spend build-phase surplus on construction). 2nd builder while fund+storage >= 10k.
    { const W = require('./walls'), se = room.storage.store[RESOURCE_ENERGY], bp = W.phase(room) === 'build', f = bp ? (W.budgetE ? W.budgetE(room) : W.fund(room)) : 0;
      if (T.builder === 1 && bp && f >= 10000 && se >= 10000 && room.energyCapacityAvailable >= 1300) T.builder = 2;
      // v5 infra max (Misaki 02:2x): upgrade held in the wall phase, so its feed + storage down to ~5k go to builders: 3 builders
      // while fund and storage >= 8k, 4 while >= 15k. Spawn steady-state busy ~52% (02:20 live), room for it.
      // After the 100k hold lifts (07:5x 10-18) upgraders resume at 2 (feed-limited ~14-24 e/t) but these tiers were tied to
      // noUpgrade, so builders fell 6 -> 2 with storage 52k / budget 47k still rising (Misaki 02:21: walls first, spend storage
      // down to a reserve). Tiers now follow the wall budget alone for the whole build phase.
      if (T.builder >= 2 && bp && f >= 8000 && se >= 8000) T.builder = (f >= 15000 && se >= 15000) ? 4 : 3;
      // 4x 11W builders still left storage rising 24.2k -> 30.2k in ~300t (03:05-03:28, ~+20 e/t, builders work ~25% of ticks): 5th at >= 25k
      if (T.builder === 4 && bp && f >= 25000 && se >= 25000) T.builder = 5;
      // 5 builders (36-55 WORK, ~45% of ticks repairing) still left storage +12..27 e/t, 40.9k -> 46.7k (patrol 05:10); 6th at >= 40k
      if (T.builder === 5 && bp && f >= 40000 && se >= 40000) T.builder = 6; } }
  return T;
}
// Pre-spawn: a dying upgrader / home hauler / queen stops counting once its TTL is under spawn time + walk + margin,
// so the replacement is queued while the room is still full. Counting it to death let upgrader83631342 (died 83632876) go
// unreplaced 276 ticks: a remote reserver/rhauler/rminer wave took the 1300 first, 1x10W upgraded ~10/t (patrol 10-14 11:43).
// Same gap for the lone A->ctl hauler: hauler83634137 died ~83635697, the 21-part replacement spawned 63t, ctl container
// sat at 0 and 3 upgraders (36W) did ~3/t for ~90t (patrol 10-14 14:36). Miners/rhaulers/reservers have their own leads.
const PRESPAWN = new Set(['upgrader', 'hauler', 'queen']);
function retiring(c) { return PRESPAWN.has(c.memory.role) && !c.memory.remote && !c.spawning && c.ticksToLive <= c.body.length * 3 + 30; }
// Pure rule for remote hauler early-replace (exported for unit tests).
function rhaulerNeed(liveCount, allCount, target) {
  target = target === undefined ? 2 : target;
  return liveCount < target && allCount < target + 1;
}
// Remote mining (managers/remote.js): after home miners/queen/haulers, before fillers/upgraders/builders.
// CLAIM1 nets 0 reservation ticks; a low buffer never recovers unless two CLAIM1 overlap (+1/t) or we reach CLAIM2 at RCL4.
// CLAIM2 costs 1300: size the body from avail (not E=cap), else avail 650-1299 requests CLAIM2, returns
// ERR_NOT_ENOUGH_ENERGY and blocks rhauler/rminer (patrol 10-14 23:20: remotes dead, energy stuck ~1200 during RCL5 build).
function reserverBody(avail) { return avail >= 1300 ? [CLAIM, CLAIM, MOVE, MOVE] : [CLAIM, MOVE]; }
// lastFull must move during builds that rarely hit exact cap (extensions/builders siphon).
function nearFull(avail, cap) { return avail >= Math.max(0, cap - 100); }
// Pure remote spawn order. Producer (rminer) before carriers: a lone rhauler with no rminer earns 0
// (patrol 10-15 00:08: needRemote fired only on zero creeps, spawned 1 rhauler, then starving closed the gate; cont 10e, rminer 0).
// The remote is income, so it is NOT gated by home starving: that gate turned an RCL5 build drain into a remote blackout twice.
// CLAIM2 wait: with cap>=1300 and a comfortable buffer, skip (not block) the reserver until avail>=1300. A CLAIM1 spawned at
// avail 650-1299 while res was ~2900 (patrol 10-15 07:35: reserver83650835 1C1M) lets m.claim2 go stale after 1500t ->
// armed=false -> no defender AND queen storageFloor falls back to cap 1800, re-blocking the hub link ferry (05c2664).
const RES_WAIT = 1000;
// Spawn a reserver only below RES_SPAWN: 2 CLAIM add ~2×530 per life against decay 1/t, so one per ~1060t (~1.2/t) instead of
// back-to-back (8 per ~5000t ≈ 2.1/t holding ~4000, 10-15 data). 2000 still covers the longest Invader pause seen (~1700t).
const RES_SPAWN = 2000;
function remoteNext(s) {
  const waitClaim2 = (s.cap || 0) >= 1300 && s.avail < 1300 && s.res >= RES_WAIT;
  if (s.nRes < s.wantRes && s.res < RES_SPAWN && s.avail >= (s.claim2Only ? 1300 : 650) && !waitClaim2) return 'reserver'; // claim2Only: 600-TTL CLAIM1 on a 150-tile walk nets ~0
  if (s.rmLive < 1) return 'rminer';
  // RCL4 target is 2×8C8M. Early-replace at TTL≤120: both rhaulers born ~50t apart age out together and
  // would spawn 2 replacements on top of 2 dying → 4 creeps / ~1600e wipe (patrol 10-14 09:51: energy 1300→4).
  // Cap total (dying+new) at target+1 so only one overlap is in flight.
  if (rhaulerNeed(s.rhLive, s.rhAll, s.rhTarget)) return 'rhauler';
  // A 3rd was opportunistic on cont>1200 but left waiting_pickup idle while the container sat near empty
  // (patrol 10-14 03:55: 3 rhaulers, cont ~20e). Keep energy for home upgraders / storage reserve instead.
  return null;
}
// Bodies from cap (not starving E): a starving-sized 3C3M rhauler would count as live for 1500 ticks.
// Per-remote: C.lead (prespawn travel, W45N7 140), C.haulers (target, default 2), C.rhGap (min ticks between rhauler births: ages
// stay staggered so replacements never bunch), C.travel (rminer default travel). Ramp (multi-hop W45N7): rhaulers only once the
// container is >=60% built (before that the rminer spends all it mines on the build -> haulers would idle), and while the container
// is not built yet a new rhauler also needs storage >= the 1300 defender reserve (bootstrap: an Invader is likely, 169k harvested).
// Paved remote (docs/ROADS.md): 2C:1M road body (16C8M, 1200e, 800 carry) and C.pavedHaulers instead of C.haulers.
function rhPaved(r) { return require('./roads').paved(r); }
function rhTarget(C, m, storageE, paved) {
  const want = (m && m.haulers) || (paved && C.pavedHaulers) || C.haulers || 2; if (!C.via) return want; // m.haulers: console trial override (W45N7 5->4, 2026-10-17 23:50)
  if (m.cont) return want;
  if ((m.siteProg || 0) < 3000) return 0;
  return storageE >= 1300 ? Math.min(2, want) : 0;
}
function remoteSpawn(room, go, avail) {
  const remote = require('./remote'), cap = room.energyCapacityAvailable;
  for (const r in remote.CFG) {
    const C = remote.CFG[r];
    if (C.home !== room.name) continue;
    if (remote.paused(r)) continue; // also Memory.remotes[r].off; defender is spawned from the top of run() (threat.wantDefender)
    const m = remote.mem(r);
    const res = (m.res && m.res.ticksToEnd) || 0;
    const lead = C.lead || 0;
    const resLead = 150 + lead; // travel ~40 + spawn + margin (was 80; late spawn left ticksToEnd≈13); W45N7 +140 walk
    const mineR = role => _.filter(Game.creeps, c => c.memory.remote === r && c.memory.role === role);
    // rminer lead = measured travel + spawn time + 10 (fixed 120 arrived ~3t after the old one died: born+121 vs ttl 118, 10-15 data)
    const rmLead = c => Math.min(c.memory.travel || C.travel || 110, C.travel ? C.travel + 60 : 160) + c.body.length * 3 + 10;
    const live = role => mineR(role).filter(c => c.spawning || c.ticksToLive > (role === 'reserver' ? resLead : role === 'rminer' ? rmLead(c) : 120 + lead)).length;
    const rhAll = mineR('rhauler'), target = rhTarget(C, m, room.storage ? room.storage.store[RESOURCE_ENERGY] : 0, rhPaved(r));
    const gapOk = !C.rhGap || Game.time - (m.lastRh || 0) >= C.rhGap;
    const next = remoteNext({
      nRes: mineR('reserver').filter(c => c.spawning || (c.ticksToLive || 1500) > 30 + lead).length,
      wantRes: (res > 0 && res < 800 && !C.via) ? 2 : 1, // overlap rebuilds buffer while CLAIM1-only; W45N7 is CLAIM2-only (+1/t each), no 2nd 1300 up front
      res, avail, cap, rmLive: live('rminer'), rhLive: gapOk ? live('rhauler') : 99, rhAll: rhAll.length, rhTarget: target, claim2Only: !!C.via,
    });
    if (next === 'reserver') return go('reserver', reserverBody(avail), { remote: r });
    // rminer 6W: repair (50 hits/t container decay, 1 tick in 10 at 5W) blocks harvest in the same tick, so 5W harvested ~9/t
    // (R income 8.7 measured 10-15); 6W = 250 harvest + ~25 repair ticks per 300-tick regen -> full 10/t, +25t slack for handoffs.
    if (next === 'rminer') { const w = Math.min(6, Math.floor((Math.min(cap, 800) - 200) / 100)); return go('rminer', [].concat(rep(w, WORK), [CARRY], rep(3, MOVE)), { remote: r }); }
    if (next === 'rhauler') { const rv = go('rhauler', rhPaved(r) && cap >= 1200 ? B.roadHauler(Math.min(cap, C.rhE || 1200), 16) : B.hauler(Math.min(cap, 800)), { remote: r }); if (rv === OK) m.lastRh = Game.time; return rv; }
    // vision fallback (P4): no vision for 100+ ticks and no rminer/reserver alive or en route -> one 1-MOVE scout (50e)
    if (C.scout && !Game.rooms[r] && Game.time - (m.seen || 0) > 100 && !rhAll.length && !mineR('rminer').length && !mineR('reserver').length && !mineR('rscout').length)
      return go('rscout', [MOVE], { remote: r });
  }
}
// Energy to size a home body with. Starving (no near-full for 300t) shrinks bodies to what is available, except the upgrader:
// it sits 1500 ticks on one of 1-2 slots, so a 300e 2W upgrader caps upgrade at ~2/t for its whole life. It is the last home
// role before builders, so waiting for cap blocks nothing above it (patrol 10-15 00:50: RCL5 build drain, starving since
// 83643025, upgrader died unreplaced, the next spawn would have been sized to avail ~300).
// Same for the storage-era home hauler (source A -> ctl container): it does not refill the spawn (queen does, from storage),
// and a starving-sized 6C3M (300 carry / ~70t cycle = 4.3/t of source A's 10/t) starved the 12W upgrader for 1500 ticks
// while container A piled up (patrol 10-15 01:43).
// Same for a miner while another miner still works (the other source, or the predecessor it replaces): a starving-sized
// 4W1C2M on source A mines 8/t of 10/t for 1500 ticks (miner83645106, patrol 10-15 02:25). With no miner alive, recover small.
// RCL6 road/build mode (walls.phase 'roads', Misaki 2026-10-17: construction before upgrading): the one held upgrader is
// sized 6W1C1M (700e, ~6/t) instead of 12W. A 12W ate source A's whole 10/t while builders sat waiting_feed ~43% and storage
// fell under the 1300 reserve (patrol 10-17 19:40: upgrade 13.9/t vs build 5.9/t). Surplus ctl feed spills to storage -> builders.
const BUILD_UP_E = 700;
function bodyEnergy(role, E, cap, avail, haulerAlive, hasStorage, minerAlive, buildMode) {
  if (role === 'upgrader' && buildMode) return Math.min(cap, BUILD_UP_E);
  if (role === 'queen' && !haulerAlive) return Math.max(300, avail);
  // Builder: size to energyAvailable, not full cap. After roads→walls, lastFull kept resetting so starving never
  // shrank the body; 11W11C11M (2200) waited while avail sat ~1300–1600 and sites/gates sat idle >1k ticks
  // (patrol 2026-10-18 01:40). Spawn now with what we have; full-cap size when the spawn is actually full.
  // v5 floor (patrol 10-18 04:30): with storage wait for >= 70% of cap (8W at 2300). Patrol 04:50: starving set E=avail
  // (lastFull >300t ago while 5 builders drain extensions) and Math.min(E, floor) collapsed the floor — 5th builder
  // spawned 6W. Storage era ignores starving E (use cap); go() waits until avail >= floor. Pre-storage still uses E.
  if (role === 'builder') return Math.min(hasStorage ? cap : E, Math.max(hasStorage ? Math.floor(0.7 * cap) : 200, avail));
  const fromCap = role === 'upgrader' || (role === 'hauler' && hasStorage) || (role === 'miner' && minerAlive);
  return Math.min(fromCap ? cap : E, role === 'hauler' ? (hasStorage ? 1050 : 800) : role === 'queen' ? 600 : 3000);
}
// Spawn queue order. Base upgrader quota (1 with sites, else 2) jumps ahead of REMOTE so a remote
// rhauler wave cannot leave the room on a single 12W for hundreds of ticks (patrol 2026-10-16 16:42).
function spawnOrder(count, T, nSites) {
  const baseUp = Math.min(nSites ? 1 : 2, T.upgrader || 0);
  return (count.upgrader || 0) < baseUp
    ? ['queen', 'hauler', 'upgrader', 'REMOTE', 'filler', 'manager', 'builder']
    : ['queen', 'hauler', 'REMOTE', 'filler', 'manager', 'upgrader', 'builder'];
}
module.exports = { rhTarget, birthDirs, targets, rhaulerNeed, remoteNext, retiring, B, reserverBody, nearFull, bodyEnergy, spawnOrder, run(spawn) {
  if (spawn.spawning) return;
  const room = spawn.room, cap = room.energyCapacityAvailable, avail = room.energyAvailable, rcl = room.controller.level;
  if (nearFull(avail, cap)) room.memory.lastFull = Game.time; // cap-100: RCL5 build rarely hits exact cap
  const starving = Game.time - (room.memory.lastFull || Game.time) > 300;
  const E = starving ? Math.max(300, avail) : cap;
  const mine = _.filter(Game.creeps, c => c.memory.home === room.name || (!c.memory.home && c.room.name === room.name));
  const count = _.countBy(mine.filter(c => !retiring(c)), c => c.memory.role); // replacement targets
  const alive = _.countBy(mine, c => c.memory.role); // who can refill the spawn right now (retiring ones still work)
  const P = plan.get(room.name);
  const go = (role, body, mem = {}) => {
    const cost = _.sum(body, p => BODYPART_COST[p]);
    if (avail < cost) return ERR_NOT_ENOUGH_ENERGY;
    return spawn.spawnCreep(body, role + Game.time, { memory: Object.assign({ role, home: room.name }, mem), directions: birthDirs(spawn, role) });
  };
  // 1) emergency: nothing can refill the spawn
  if (!(alive.hauler || 0) && !(alive.queen || 0) && !(alive.harvester || 0) && !(alive.filler || 0))
    return go(count.miner ? 'hauler' : 'harvester', count.miner ? B.hauler(Math.max(200, avail)) : B.harvester(Math.max(200, avail)));
  // 1b) defender: top of the queue. While collecting the 1300, hold EVERYTHING except queen (refill) —
  // miners used to keep spawning and stretched the wait to ~31t (invader_W45N8_499, 2026-10-16).
  // Holding ends the tick noteSpawn sets th.def (wantDefender/holding go false → upgraders resume).
  const threat = require('./threat'), want = threat.wantDefender(room.name);
  if (want && rcl >= 4 && threat.armed(want)) {
    if (avail >= 1300) { const name = 'defender' + Game.time, rv = spawn.spawnCreep(B.defender(1300), name, { memory: { role: 'defender', home: room.name, remote: want, born: Game.time }, directions: birthDirs(spawn, 'defender') });
      if (rv === OK) threat.noteSpawn(want, name); return rv; }
    if (!(alive.queen || 0) && !(alive.filler || 0)) return go('queen', B.queen(Math.max(300, avail)));
    return ERR_BUSY; // reserve energyAvailable for the defender; home guards (off) never reach here while want is set
  }
  // 1c) home guards while player combat creeps are in the room (managers/home); queen first so towers stay fed
  const H = require('./home'), homeThreat = H.on('guards') && H.active(room); // guards + spawn hold behind Memory.defense.guards
  if (homeThreat) {
    if (!(alive.queen || 0) && !(alive.filler || 0)) return go('queen', B.queen(Math.max(300, avail)));
    if ((alive.guard || 0) < H.wantGuards(room)) { const b = B.guard(Math.max(500, Math.min(cap, avail))); // spawn now with what we have: towers carry the fight, speed matters
      return go('guard', b, { born: Game.time }); }
  }
  const hold = !!want || homeThreat || threat.energyHold(room.name); // energyHold: collect 1300 for a gated remote defender // threat: no upgraders/builders/remote spawns until clear
  // 2) miners (pre-spawned for travel time)
  // miner83614486 (10-13) arrived 115 ticks early and idled next to its predecessor: unmeasured travel defaulted to 100 (real ~30)
  const lead = c => Math.min(c.memory.travel || 40, 80) + c.body.length * 3;
  if (!room.memory.sources) room.memory.sources = room.find(FIND_SOURCES).map(s => s.id);
  for (const s of room.memory.sources.map(id => Game.getObjectById(id)).filter(Boolean)) {
    if (!mine.some(c => c.memory.role === 'miner' && c.memory.sourceId === s.id && (c.ticksToLive || 1500) > lead(c))) {
      const carry = rcl >= 4;
      return go('miner', B.miner(Math.min(bodyEnergy('miner', E, cap, avail, !!alive.hauler, !!room.storage, !!alive.miner), carry ? 800 : 650), carry), { sourceId: s.id });
    }
  }
  if (hold) { if (!(count.queen || 0) && !(count.filler || 0)) return go('queen', B.queen(Math.max(300, avail))); return ERR_BUSY; }
  // 2b) one-off manual probe (roles/probe.js): only when Memory.ops.probe.spawn === true and storage >= 3100 (1300 defender reserve kept)
  const PR = require('../roles/probe');
  if (PR.wantSpawn(room)) { const name = 'probe' + Game.time, b = PR.BODY();
    if (avail < _.sum(b, p => BODYPART_COST[p])) return ERR_NOT_ENOUGH_ENERGY;
    const rv = spawn.spawnCreep(b, name, { memory: { role: 'probe', home: room.name, born: Game.time }, directions: birthDirs(spawn, 'probe') });
    if (rv === OK) PR.noteSpawned(name); return rv; }
  // 2c) W47N8 conquest (roles/conquest.js): only when Memory.ops.cq.spawn/claim set; storage floor 3100
  const CQ = require('../roles/conquest');
  { const w = CQ.wantSpawn(room); if (w) {
    if (avail < _.sum(w.body, p => BODYPART_COST[p])) return ERR_NOT_ENOUGH_ENERGY;
    const name = w.role + Game.time;
    const rv = spawn.spawnCreep(w.body, name, { memory: w.mem, directions: birthDirs(spawn, w.role) });
    if (rv === OK) CQ.noteSpawned(name, w.role); return rv; } }
  const hp = require('../roles/hauler');
  const backlog = _.sum(hp.pickups(room), s => s.store[RESOURCE_ENERGY]);
  const [cx, cy] = P.pos.controllerContainer; const cc = rc.at(room, cx, cy, STRUCTURE_CONTAINER);
  const m = room.memory, ce = cc ? cc.store[RESOURCE_ENERGY] : 0;
  m.ctlEma = m.ctlEma === undefined ? ce : m.ctlEma + (ce - m.ctlEma) * Math.min(1, (Game.time - (m.ctlEmaT || Game.time)) / 300);
  m.ctlEma = Math.round(m.ctlEma); m.ctlEmaT = Game.time;
  const nSites = rc.sites(room).length;
  const T = targets(room, count, backlog, m.ctlEma, nSites);
  room.memory.roleTargets = T;
  for (const role of spawnOrder(count, T, nSites)) {
    if (role === 'REMOTE') { const r = remoteSpawn(room, go, avail); if (r !== undefined) return r; continue; }
    if ((count[role] || 0) >= T[role]) continue;
    const mem = {};
    if (role === 'filler') { const used = new Set(mine.filter(c => c.memory.role === 'filler').map(c => c.memory.spot.join())); mem.spot = P.pos.fillers.slice(0, 4).find(s => !used.has(s.join())); }
    // Home hauler: 8C8M pre-storage. With storage it hauls source A -> ctl container (27 tiles, measured cycle ~57-66t, not the
    // model's A->hub rt 28): 10/t x 66 = 660 carry -> one 14C7M road hauler (700, 1050e). 2x6C6M (600 carry) let
    // container A pile up to 1771/2000 (patrol 10-14 07:05) while upgraders sat waiting_feed ~50%.
    const buildMode = role === 'upgrader' && rcl >= 6 && rcl < 8 && require('./walls').phase(room) === 'roads';
    const e = bodyEnergy(role, E, cap, avail, !!alive.hauler, !!room.storage, undefined, buildMode);
    // v5 link era (RCL6, 3 links): source A ships via link 30,11, the home hauler only clears container overflow / drops.
    // 14C7M sat waiting_pickup 66% and moved empty 89% (motion audit 02:50) -> 6C3M (450e, 300 carry).
    const linkEra = role === 'hauler' && rcl >= 6 && rc.all(room, STRUCTURE_LINK).length >= 3;
    return go(role, role === 'hauler' && room.storage ? B.roadHauler(linkEra ? Math.min(e, 450) : e) : B[role](e, rcl), mem);
  }
} };
