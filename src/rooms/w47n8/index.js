// W47N8 room module: spawn manager + layout + tower. Runs ONLY for W47N8; home W46N8 code never sees it.
// Never activates safe mode (Misaki does it manually).
const C = require('./config');
const rep = (n, p) => Array(n).fill(p);
const FM = require('./fillmeter');
const FL = require('./fill');
function mine() { return _.filter(Game.creeps, c => c.memory.home === C.ROOM); }
function bodyFor(role, e) {
  // 17:34 (Misaki joint defence): RA+MOVE only, no HEAL (towers heal on our ground; HP rule 60%/90% in defense.defPlan)
  if (role === 'w8defender') return require('./defense').raBody(e, 25); // RCL7 5600 → 25 RA + 25 MOVE
  if (role === 'w8guard') return require('./defense').meleeBody(e); // 10-20 15:25 melee gate guard, sized to cap
  if (role === 'w8healer') return require('./defense').healBody(e, 25); // 18:04 local healer, full cap (18H18M at 5600)
  if (role === 'w8filler') return FL.body(e, Game.rooms[C.ROOM]); // 17:4x 2C:1M, carry ~75% of the hub spawn energy (fill.js)
  if (role === 'w8rminer') { // 20:22: old formula priced 4W1C3M=600 at cap 550, so it never spawned; now the biggest that fits, trimming MOVE first
    // 10-19 21:4x (strategy review, port of home rmBody): 6W. Reserved-room containers decay 5000/100t = 50 hits/t; repair shares the
    // harvest pipeline (repair blocks harvest that tick), so 5W (10/t, no slack) repaired 1 tick in 10 and mined ~9/t; R2 31,34 had
    // 900 left at ttr 32 (t83745419). 6W = 250 harvest + ~25 repair ticks per 300 -> full 10/t, +25t slack for handoffs.
    // MOVE = ceil(W/2): the empty CARRY weighs nothing, so 6W1C3M (800) still walks 1 tile/t on road.
    for (let w = 6; w >= 2; w--) for (let m = Math.ceil(w / 2); m >= Math.ceil((w + 1) / 3); m--)
      if (100 * w + 50 + 50 * m <= e) return rep(w, WORK).concat([CARRY], rep(m, MOVE));
    return [WORK, WORK, CARRY, MOVE];
  }
  // 02:35: W47N7 routes are road almost end to end (18,17->ctl 45 tiles/43 road, 31,34->59/56), so 2C:1M keeps full speed loaded:
  // 10C5M=750 carries 500 vs 8C8M=800 carrying 400 at cap 800
  if (role === 'w8rhauler') { if (e < 450) { const n = Math.max(2, Math.floor(e / 100)); return rep(n, CARRY).concat(rep(n, MOVE)); }
    // 15:55: 1 WORK (replaces 1 CARRY, still 2 heavy:1 MOVE) so loaded rhaulers build/repair the W47N7 road in passing
    const k = Math.min(8, Math.floor((e - 50) / 150)); return rep(2 * k - 1, CARRY).concat([WORK], rep(k, MOVE)); }
  // 17:20: 6W (12/t vs regen 10/t): a 5W miner needs every tick of the 300-tick regen, so walk-in, container repair and replacement gaps
  // were lost for good (local miners 85% working, 1 h). 6W catches up; +0.07 e/t upkeep. +1 CARRY at RCL5 to feed the source link.
  if (role === 'w8miner') { const w = Math.max(2, Math.min(6, Math.floor((e - 50) / 100))), cy = linkAt(C.SOURCES[0].link) && e >= 750 ? 1 : 0;
    return rep(Math.min(w, Math.floor((e - 50 - 50 * cy) / 100)), WORK).concat(rep(cy, CARRY), [MOVE]); }
  // 11:4x strategy: dormant w8mminer (same body as home mminer). Only spawned while RCL6_MINERALS + extractor + minCont.
  if (role === 'w8mminer') { const n = Math.max(2, Math.min(12, Math.floor((e - 150) / 100))); return rep(n, WORK).concat(rep(3, MOVE)); }
  // 15:10 model: local routes are paved end to end (A->ctl 25/25 road, B->ctl 16/16, hub legs 1 unpaved tile), so 2C:1M keeps full
  // speed loaded on road: 10C5M = 750 carries the same 500 as 10C10M = 1000 (-0.5 e/t upkeep over 3 haulers). Below 450: 1:1.
  if (role === 'w8hauler') { if (e < 450) { const n = Math.max(2, Math.floor(e / 100)); return rep(n, CARRY).concat(rep(n, MOVE)); }
    const k = Math.min(5, Math.floor(e / 150)); return rep(2 * k, CARRY).concat(rep(k, MOVE)); }
  // 18:58: upgraders sit beside the ctl container 13,26 (1750/2000 full, spawn idle at 550/550): WORK-heavy 4W1C2M instead of 2W2C2M
  if (role === 'w8upgrader' && e >= 550) { const w = Math.min(10, Math.floor((e - 150) / 100)); return rep(w, WORK).concat([CARRY, MOVE, MOVE]); }
  const n = Math.max(1, Math.min(6, Math.floor(e / 200))); return rep(n, WORK).concat(rep(n, CARRY), rep(n, MOVE)); // upgrader/builder
}
// energy lying on the ground or in source containers (ctl/hub containers excluded)
// typeof guards: unit tests often stub only a subset of FIND_* constants
const looseE = room => {
  let n = 0;
  if (typeof FIND_DROPPED_RESOURCES !== 'undefined')
    n += _.sum(room.find(FIND_DROPPED_RESOURCES, { filter: r => r.resourceType === RESOURCE_ENERGY }), r => r.amount);
  if (typeof FIND_STRUCTURES !== 'undefined')
    n += _.sum(room.find(FIND_STRUCTURES, { filter: s => s.structureType === STRUCTURE_CONTAINER
      && !(s.pos.x === C.CTL_CONT[0] && s.pos.y === C.CTL_CONT[1])
      && !(s.pos.x === C.HUB_CONT[0] && s.pos.y === C.HUB_CONT[1]) }), s => (s.store && s.store[RESOURCE_ENERGY]) || 0);
  return n;
};
const siteRem = room => _.sum(room.find(FIND_MY_CONSTRUCTION_SITES), s => s.progressTotal - s.progress);
// 14:57 (Misaki): spawn energy from hub-area extensions (nearest the core first) and hub spawns, Spawn2 + its 5 temp extensions last
function energyOrder(room) {
  const [cx, cy] = L.CORE, all = room.find(FIND_MY_STRUCTURES, { filter: s => s.structureType === STRUCTURE_EXTENSION || s.structureType === STRUCTURE_SPAWN });
  const last = s => (s.structureType === STRUCTURE_SPAWN && s.pos.x === C.SPAWN[0] && s.pos.y === C.SPAWN[1]) || (s.structureType === STRUCTURE_EXTENSION && isTemp(s));
  const d = s => Math.max(Math.abs(s.pos.x - cx), Math.abs(s.pos.y - cy));
  return all.filter(s => !last(s)).sort((a, b) => d(a) - d(b)).concat(all.filter(last).sort((a, b) => (a.structureType === STRUCTURE_SPAWN ? 0 : 1) - (b.structureType === STRUCTURE_SPAWN ? 0 : 1)));
}
// 10-19 22:4x patrol: + 60 queue margin. First live replacement at 18,17 was ordered at old TTL 43 (lead 140): Spawn2 was busy with
// 2 hauler-floor spawns (45t each) + a local miner from TTL 140 on, so the source sat unmined ~77 ticks. Overlap costs ~0.5 e/t-tick.
const rmLead8 = (i, c) => Math.min(180, Math.max(40, (Memory.ops && Memory.ops.w8rlead && Memory.ops.w8rlead[i]) || 90)) + 3 * ((c && c.body) || []).length + 20 + 60;
// 11-10: one planning pass per room per tick, plus an idle/wait throttle (home IDLE_EVERY).
// Hostiles and a live commander order skip the throttle. A second idle spawn does not
// repeat the find cascade; it still runs when the first spawn actually started a creep.
const IDLE_EVERY = 4;
function spawnForce(room) {
  if (typeof FIND_HOSTILE_CREEPS !== 'undefined') {
    try { if (room.find(FIND_HOSTILE_CREEPS).length) return true; } catch (e) { /* test stubs */ }
  }
  try { const cmd = require('../../utils/cmd'); if (cmd.armed && cmd.armed()) return true; } catch (e) { /* ok */ }
  // A reserved-room threat (W47N7) is not a hostile in W47N8. Do not idle-skip the tick it arrives.
  try {
    const t = require('../../managers/threat');
    if (t.wantDefender(room.name) || t.holding(room.name) || t.energyHold(room.name)) return true;
  } catch (e) { /* ok */ }
  return false;
}
function spawnGate(spawn) {
  const room = spawn.room;
  const o = (Memory.ops = Memory.ops || {});
  const mem = (o.w8sg = o.w8sg || {});
  const stor = room.storage && room.storage.store ? (room.storage.store[RESOURCE_ENERGY] || 0) : 0;
  upBankTick(stor); // every tick, even while the cascade is throttled (streak must not skip)
  let g = room._sg;
  if (!g || g.t !== Game.time) {
    const force = spawnForce(room);
    const canPay = mem.waitCost > 0 && (room.energyAvailable || 0) >= mem.waitCost;
    const throttled = !force && mem.ne > Game.time && !canPay;
    g = room._sg = { t: Game.time, throttled, planned: 0, spawned: 0, passes: 0, who: '', mem, force };
    mem.passes = 0; mem.skipTick = 0;
  }
  return g;
}
function spawnRun(spawn) {
  FM.tick(spawn); // 17:3x spawn-energy meter (Memory.ops.w8fm)
  const room = spawn.room;
  const g = spawnGate(spawn);
  const sid = spawn.name || spawn.id || '';
  if (g.throttled) { g.mem.skipTick++; return; }
  // Commander owns this spawn before we count it as the room's planning pass.
  if (!spawn.spawning && require('../../utils/cmd').consumeSpawn(spawn)) return;
  if (!spawn.spawning && sid && g.planned && !g.spawned && g.who && g.who !== sid) { g.mem.skipTick++; return; }
  if (!spawn.spawning) {
    if (sid) g.who = g.who || sid;
    g.planned = 1; g.passes++; g.mem.passes = g.passes;
  }
  const markSpawn = () => { g.spawned++; if (sid) { g.mem.waitCost = 0; g.mem.ne = 0; } };
  const markIdle = () => { if (sid) { g.mem.waitCost = 0; g.mem.ne = Game.time + IDLE_EVERY; } FM.idle(); };
  const markWait = (role, cost, avail) => { if (sid) { g.mem.waitCost = cost; g.mem.ne = Game.time + IDLE_EVERY; } FM.wait(role, cost, avail); };
  // Census is per pass. A second idle spawn returns above and never gets here. A pass that
  // actually starts a creep reads Game.creeps again so the sibling sees that body (plus pending).
  const cs = mine(), n = r => cs.filter(c => c.memory.role === r).length;
  const sites = room.find(FIND_MY_CONSTRUCTION_SITES).length;
  const storPark = room.storage ? (room.storage.store[RESOURCE_ENERGY] || 0) : 0;
  TH.updateSealPark(storPark, cs.filter(c => c.memory.role === 'w8upgrader' && (c.spawning || !(c.ticksToLive <= 3 * (c.body || []).length + 60))).length
    + require('../../managers/spawn').pendingSpawn(room, 'w8upgrader'), sites);
  // 17:5x (patrol: 2 upgraders died within 40 ticks, upgrade fell to ~10 e/t): upgraders count only while they outlive a replacement
  // (spawn 3/part + ~60 ticks Spawn2 -> ctl stands), so the next one is queued before the old one dies.
  // Same-tick intents (home overshoot, 2026-11-10): the other idle spawn's spawnCreep is not in Game.creeps yet.
  const nUp = () => cs.filter(c => c.memory.role === 'w8upgrader' && (c.spawning || !(c.ticksToLive <= 3 * (c.body || []).length + 60))).length
    + require('../../managers/spawn').pendingSpawn(room, 'w8upgrader');
  if (spawn.spawning) return;
  const cap = room.energyCapacityAvailable, avail = room.energyAvailable;
  let want = null, mem = {};
  const raidPause = require('../../roles/raid9').pauseCivilians();
  // 0) defender (Misaki 14:09): only when an armed hostile is inside the sealed base (towerRun sets threat8.inBase); max 2
  const th = room.memory && room.memory.threat8;
  // 14:46 (Misaki): also on an invasion move (armed hostiles entering W47N8, or an armed group at the W47N9 border); max 2, stays in W47N8
  // 17:3x doctrine (docs/DEFENSE_W47N8.md): only when towerRun's assessment says towers alone lose AND towers + 2 defenders win;
  // never feed an unwinnable fight (Memory.ops.w8adv advises safe mode instead). Memory.ops.w8defOld = 1 restores the old trigger.
  // 17:34 joint defence: Memory.ops.w8roster (assessRun -> defense.plan) = local defenders + 1 home defender (src W46N8, spawned by home)
  const ro = Memory.ops && Memory.ops.w8roster, dOld = Memory.ops && Memory.ops.w8defOld, fresh = ro && Game.time - ro.t < 20;
  const local = cs.filter(c => (c.memory.role === 'w8defender' || c.memory.role === 'w8guard') && !c.memory.jd).length;
  const lg = cs.filter(c => c.memory.role === 'w8guard').length;
  const dGo = dOld ? ((th && th.inBase && Game.time - th.t < 5) || TH.invasion()) && local < 2 : !!(fresh && local < Math.min(D.MAXL, ro.w8)); // 17:56: up to 4 local
  // 10-20 07:4x (2room eval): the hub filler died while Spawn2 made 2 local defenders (threat outside the room) and its replacement
  // waited ~70 t behind them. Refill speed is defence reaction speed (Misaki 10-19), so a due filler goes first unless armed hostiles
  // are inside the base (same idea as home 'queen first' before joint defence).
  const inBase = !!(th && th.inBase && Game.time - th.t < 5);
  // Combat hostiles in this room (ATTACK / RA / HEAL / WORK). A TOUGH/MOVE scout does not count.
  // HEAL is included: defense.armed() leaves healers out so towers ignore drain tanks, but an owned
  // room still spawns. Count is the same squad table as remotes. The roster can ask for more, not fewer.
  const Df = require('./defense');
  const foes = room.find(FIND_HOSTILE_CREEPS).filter(h => Df.respond(h));
  const specN = foes.length ? require('../../utils/squad').judge(foes.map(Df.toSpec)) : 0;
  const n9t = (Memory.ops || {}).w8n9a || 0;
  const fmv = Memory.ops && Memory.ops.w8move && Memory.ops.w8move.force && ['prep', 'build'].includes(Memory.ops.w8move.phase);
  const border = fmv || (n9t > 0 && Game.time - n9t < 60);
  const owe = Math.max(specN, border ? 1 : 0, dGo ? Math.min(Df.MAXL, ro.w8 | 0) : 0);
  // A second spawn this tick does not see the creep the first one just queued.
  // The counter is per tick; leaving it set would double-count the creep once it exists.
  if (room._defPendT !== Game.time) { room._defPend = 0; room._defPendT = Game.time; }
  const pending = room._defPend || 0;
  if (local + pending < owe) {
    // The spec/border minimum is a gate guard. Further roster bodies follow w8m, then ranged.
    const role = local + pending < Math.max(specN, border ? 1 : 0) ? 'w8guard'
      : (!dOld && lg < (ro.w8m | 0) ? 'w8guard' : 'w8defender');
    const body = bodyFor(role, cap);
    const cost = _.sum(body, p => BODYPART_COST[p]);
    if (avail >= cost) { want = role; room._defPend = pending + 1; }
    else if (!cs.some(c => c.memory.role === 'w8filler' || c.memory.role === 'w8hauler')) want = 'w8filler';
    else { markWait(role, cost, avail); return; }
  }
  if (!want && !inBase && FL.want(room, cs)) want = 'w8filler';
  // 18:04: roster >= 4 combat defenders -> one dedicated healer; local only when home can't send it (ro.hl 'w8')
  if (!want && !dOld && fresh && ro.hl === 'w8' && !_.some(Game.creeps, c => c.memory.role === 'w8healer')) want = 'w8healer';
  // Reserved remote of this colony (W47N7, plus any other room we currently reserve next door).
  // Same `defender` role / threat FSM as W45N8. Local seal defence above still wins. Never W47N9.
  if (!want && room.controller && room.controller.level >= 4 && room.name) {
    const TG = require('../../managers/threat'), SP = require('../../managers/spawn');
    const planD = SP.planDefender(room);
    if (planD && (planD.remote || planD.hold)) {
      if (planD.remote && avail >= planD.cost) {
        const name = 'rdef' + Game.time;
        const mem = { role: 'defender', home: room.name, remote: planD.remote, born: Game.time, squad: 1, v2: 1 };
        if (planD.core) mem.core = 1;
        const rv = spawn.spawnCreep(planD.body, name, { memory: mem, energyStructures: energyOrder(room) });
        if (rv === OK) { TG.noteSpawn(planD.remote, name); FM.spent(planD.cost); markSpawn(); return; }
      } else if (planD.hold) {
        if (!cs.some(c => c.memory.role === 'w8filler' || c.memory.role === 'w8hauler')) want = 'w8filler';
        else { markWait('defender', planD.cost || 1300, avail); return; }
      }
    }
  }
  // 1) miners per source: keep >=5 WORK (10 e/t) on each source. Replace at TTL<60; and since the first w8miners were 2 WORK
  // (cap 300) and would run at 40% for ~1000 ticks, add a bigger one once cap allows (17:25), counting any cqminer still there.
  // Always walk every source (even after want is set) so a surplus si0 miner still gets recycled this tick.
  for (let i = 0; i < C.SOURCES.length; i++) {
    // 20:20: replace at TTL < walk time + spawn time (learned per source by w8miner on arrival). TTL<60 left source 11,44 unmined
    // ~150 ticks (5W1M walks 5-25 ticks/tile; spawn->11,43 took ~170 ticks), regen wasted at 3000/3000.
    const S = C.SOURCES[i];
    // 11-10 patrol: ignore a poisoned w8lead (>300, e.g. a 1400-tick detour arrival) and fall back to the range estimate.
    const learned = Memory.ops && Memory.ops.w8lead && Memory.ops.w8lead[i];
    const walk = (learned > 0 && learned <= 300) ? learned : 5 * spawn.pos.getRangeTo(S.stand[0], S.stand[1]);
    const lead = Math.max(60, walk + 3 * 6 + 10);
    // 11-10 patrol: a si0 miner can walk the long east-of-wall detour from hub spawns 33-34,30 for
    // hundreds of ticks without arr; TTL still > lead so it blocked a replacement while source A sat
    // unmined. Count as live only if spawning, arrived, or still within lead+80 of birth (or no born).
    const live = cs.filter(c => {
      if (c.memory.role !== 'w8miner' || (c.memory.si | 0) !== i) return false;
      if (!(c.spawning || c.ticksToLive > lead)) return false;
      if (c.spawning || c.memory.arr) return true;
      const born = c.memory.born;
      if (!born) return true;
      return (Game.time - born) <= lead + 80;
    });
    const cq = room.find(FIND_MY_CREEPS, { filter: c => c.memory.role === 'cqminer' && c.ticksToLive > 60 && c.pos.inRangeTo(S.src[0], S.src[1], 1) });
    const works = _.sum(live.concat(cq), c => c.getActiveBodyparts(WORK) || _.filter(c.body, p => p.type === WORK).length);
    const add = bodyFor('w8miner', cap).filter(p => p === WORK).length;
    // Enough WORK already on this source: recycle extras (keep stand / higher WORK / earlier arr).
    const arrived = live.filter(c => c.memory.arr && !c.spawning);
    if (arrived.length > 1 && works >= 5) {
      const [sx, sy] = S.stand;
      const workOf = c => c.getActiveBodyparts(WORK) || _.filter(c.body, p => p.type === WORK).length;
      const onStand = c => c.pos && c.pos.x === sx && c.pos.y === sy ? 1 : 0;
      const named = c => c.name || (Object.keys(Game.creeps).find(n => Game.creeps[n] === c));
      arrived.sort((a, b) => onStand(b) - onStand(a) || workOf(b) - workOf(a) || (a.memory.arr || 0) - (b.memory.arr || 0));
      const o = Memory.ops = Memory.ops || {};
      const L = o.w8recycle || [];
      for (const c of arrived.slice(1)) { const n = named(c); if (n && !L.includes(n)) L.push(n); }
      o.w8recycle = L;
    }
    if (!want && (!live.length || (works < 5 && live.length < 2 && add > (live[0] ? live[0].getActiveBodyparts(WORK) : 0)))) { want = 'w8miner'; mem.si = i; }
  }
  // 2) haulers 2, 3) upgraders 2 (3 when no sites), 4) builders while sites
  // 04:47: base 3 (was 2): with 2 haulers and 0 sites RCL3 fell ~22 -> ~7.5 e/t (t83731005..1169), ctl cont 0-114 while source conts
  // rose to 633/1000; the surplus 3rd only spawned after loose passed 1200, so the ctl ran dry every cycle
  // 17:15: count only haulers that outlive a replacement (15-part body 45t spawn + ~30t walk): the 5-hauler cohort aged out together
  // to 2 (one at TTL 155) before the floor fired; ctl cont 13,26 at 0 with 3 upgraders empty while 11,43 rose to 1450 (t83741650)
  // 10-29 patrol: with A→ctl links (Memory.ops.w8model.links) local CARRY need ~9; floor 3 kept 30 CARRY idle. Drop to 2 when links.
  const hFloor = (Memory.ops && Memory.ops.w8model && Memory.ops.w8model.links) ? 2 : 3;
  if (!want && cs.filter(c => c.memory.role === 'w8hauler' && (c.spawning || c.ticksToLive > 75)).length < hFloor) want = 'w8hauler';
  // 17:4x (Misaki: spawn must never wait for energy): hub filler right after miners + the hauler floor, replaced ahead of death (fill.js)
  if (!want && FL.want(room, cs)) want = 'w8filler';
  // Raid spawn is after miners/haulers/filler/rminers/rhaulers (logistics stay ahead of the fat body).
  // 10-20 03:4x (w8patrol): rminer replacements sat behind the 3rd upgrader (after a defender + 2-hauler burst): W47N7 src 18,17 unmined
  // from t83750522 with the other rminer at TTL 123 < lead. Income before sinks: W47N7 rminers come right after the filler.
  // 10:40: rhaulers sat last in the queue, so with 4 builders + 6 sites on the single Spawn2 all 6 (spawned in one burst at RCL3) aged out
  // together: 0 alive t~83735970-6045 while W47N7 conts hit 2000/2000 + ~1.2k dropped. Keep a floor of 2 ahead of builders/surplus.
  const r7m = Memory.ops && Memory.ops.r7, ours7 = r7m && r7m.by === 'Misaki' && (r7m.endTime || 0) > Game.time + 200;
  const R7 = Game.rooms[C.REMOTE.room], lo7 = R7 ? looseE(R7) : 0;
  // 10:57: floor 2 still left W47N7 at 2000/2000 conts + 2936 dropped (lo7 ~6.9k, ~3 e/t decaying) behind 4 builders; 2 sources ~20 e/t need
  // ~3-4 x 700-carry rhaulers (round trip ~100-120t), so floor 4 while lo7 > 3000
  // 11:12: lo7 kept rising 6.9k -> 7.3k (conts 2000/2000 + 3292 dropped) while 3 builders and 2 upgraders sat queue_blocked (energy-starved,
  // local conts 140/530): remote haul is the income bottleneck, so floor 6 above 5k (each 14C7M rhauler ~6 e/t over a ~110t round trip)
  // 14:05: rminer replacement sat in step 7 behind builders/surplus: W47N7 ran on 1 rminer (one source unmined) while Spawn2 made a 4th
  // w8builder t83738940, and the rhauler floor (lo7 ~5.0k -> 6) would have spawned 2 more rhaulers first. A source is ~10 e/t; mine it first.
  // 10-19 21:4x: lead = learned walk (Memory.ops.w8rlead, set on first reaching the source) + spawn time + 20 (fixed 100 < R2 ~70 walk +
  // 30 spawn + queue behind upgraders/filler at the single Spawn2; overlap is free: the newcomer mines from a tile beside the stand)
  for (let i = 0; ours7 && i < C.REMOTE.sources.length && !want; i++)
    if (!cs.some(c => c.memory.role === 'w8rminer' && (c.memory.si | 0) === i && (c.spawning || c.ticksToLive > rmLead8(i, c)))) { want = 'w8rminer'; mem.si = i; }
  // 10-20 04:4x: W47N7 reservation from Spawn2 once cap >= 1800 (roles/reserve7.js: ~60 t walk vs ~200 from home; home is the fallback)
  let body7 = null;
  if (!want) { const w7 = require('../../roles/reserve7').wantSpawn(C.ROOM); if (w7) { want = 'reserve7'; body7 = w7.body; mem = w7.mem; } }
  // Remote carry math is shared by the crash bootstrap here and the normal floor after upgraders.
  const wm = (Memory.ops && Memory.ops.w8model) || {}, rNeed = wm.rcarry || 55;
  const rCarry = (ttl) => cs.filter(c => c.memory.role === 'w8rhauler' && (c.spawning || c.ticksToLive > ttl)).reduce((a, c) => a + c.body.filter(p => p.type === CARRY).length, 0);
  const rhaulShort = ours7 && lo7 > 1000 && n('w8rminer') && rCarry(150) < rNeed * (lo7 > 3000 ? 1 : 0.6);
  // 11-13 01:1x (live ~84229650): stor ~0–500, avail ~458/5600, W47N7 conts 2000/2000, zero w8rhauler,
  // spawn waited on w8mminer 12W3M=1350. 'starving' is only "no local hauler or no miner", so two w8haulers
  // kept the body on cap and the rhauler floor (below upgraders) never ran. While stor is under the lean
  // emergency line, stranded remote energy is income and comes before the mineral miner and other sinks.
  // At/above LEAN_ARM the 17:4x order stands: one mminer still precedes surplus upgraders.
  if (!want && storPark < LEAN_ARM && rhaulShort) want = 'w8rhauler';
  // 17:4x strategy 2026-11-01: elevate w8mminer after economy floors, BEFORE soft/surplus upgraders.
  // Overmind ownedRoom.mineral=520 < upgrading.upgrade=600 — mineral start must not wait behind soft-cap ≤2.
  // Still behind miners/haulers/filler/rminer/reserve7/defense. Dormant while gate false or minCont missing.
  if (!want && C.RCL6_MINERALS && !raidPause) {
    const [mx, my] = C.MINERAL_CONT || [37, 44];
    const k = room.lookForAt(LOOK_STRUCTURES, mx, my).find(s => s.structureType === STRUCTURE_CONTAINER);
    const ex = room.find(FIND_MY_STRUCTURES, { filter: s => s.structureType === STRUCTURE_EXTRACTOR })[0];
    const min = (typeof FIND_MINERALS !== 'undefined' ? room.find(FIND_MINERALS) : [])[0];
    if (k && ex && min && min.mineralAmount > 0 && k.store.getFreeCapacity() > 400
      && !cs.some(c => c.memory.role === 'w8mminer' && (c.spawning || c.ticksToLive > 50))) want = 'w8mminer';
  }
  // 14:23 threat mode: seal walls to 50k ahead of upgrading; 1 upgrader keeps the controller safe (2 if downgrade < 10k)
  const thr = TH.on(), wtgt = TH.wallTarget(TH.planTarget((room.controller || {}).level || 0, C.WALL_TARGET[(room.controller || {}).level] || 0));
  // 15:45 hysteresis: core ramparts decay 300/100t, so a strict '< 50k' gate re-entered wall mode (1-2 upgraders, +builders) ~100 ticks
  // after every top-up. Wall mode starts below 90% of target; builders still repair to the full target (wallJob).
  // 17:15: seal walls only (ramparts no longer part of the wall raise)
  const wallsLow = thr && room.find(FIND_STRUCTURES, { filter: s => (s.structureType === STRUCTURE_WALL || (s.structureType === STRUCTURE_RAMPART && isGate(s.pos.x, s.pos.y))) && C.SEAL.some(([x, y]) => s.pos.x === x && s.pos.y === y) && s.hits < Math.min(wtgt, TH.urgentTarget()) * 0.9 }).length > 0; // 06:3x: threat floor only, RCL target from surplus
  // 15:10 model: under the wall raise 1 upgrader (10 WORK of ~30 e/t net) left ~8k idle in containers (ctl/hub 1.5k+1.6k, W47N8 sources
  // 2.3k, W47N7 2.8k) while builders spent ~13 e/t; a 2nd upgrader while >3000 sits in local piles + ctl/hub conts (stock covers the gap)
  const stock8 = () => looseE(room) + _.sum([C.CTL_CONT, C.HUB_CONT], ([x, y]) => _.sum(room.lookForAt(LOOK_STRUCTURES, x, y).filter(s => s.structureType === STRUCTURE_CONTAINER), s => s.store[RESOURCE_ENERGY]));
  // 10-20 14:4x strategy review: moveReady needs a builder with TTL >= 700, but with 0 sites and the north line at the stage-1 cap
  // nothing spawns one, so the move could stall on 'ttl' after the bank fills. Queue one once storage is within 3k of MOVE_E.
  const mv8 = Memory.ops && Memory.ops.w8move;
  if (!want && mv8 && mv8.phase === 'prep' && room.storage && bankE(room) >= MOVE_E - 3000
    && !raidPause && !cs.some(c => c.memory.role === 'w8builder' && (c.spawning || c.ticksToLive >= 700))) want = 'w8builder';
  if (!want && wallsLow && nUp() < upCapN(room, raidPause ? require('../../roles/raid9').upgraderKeep(room) : (room.controller.ticksToDowngrade < 10000 || stock8() > 3000 ? 2 : 1))) want = 'w8upgrader';
  else if (!want && !raidPause && wallsLow && n('w8builder') < 3) want = 'w8builder';
  else if (!want && !wallsLow && nUp() < upCapN(room, raidPause ? require('../../roles/raid9').upgraderKeep(room) : upgTarget(room))) want = 'w8upgrader'; // 15:5x move bank // 11-04 leanBank bands // 11-10: peacetime 2 until 40k/500 sticky, then 3; threatSoft stays ≤2. 11-12: sites cap at 1 (upgTarget)
  // 14:55 model-driven (tools/model_w8.py -> Memory.ops.w8model): remote fleet sized by CARRY need = sum 10 x (rt x 1.1 + 4) / 50 over
  // both W47N7 sources (~52 at 14:55) instead of loose-pile thresholds (live 88 CARRY: rhaulers 82% moving/12% blocked, +1.8 e/t upkeep).
  // Floor (ahead of builders): 60% of need; full need + a backlog term (+16 CARRY per 2000 loose above 3000) in step 7.
  // wm / rNeed / rCarry live above the mineral miner (crash bootstrap shares them).
  // 15:55 model: local CARRY need = lcarry (~20, source->ctl) + ~10 for extension refills (spawn upkeep ~10 e/t over ~45t hub trips) = ~30
  // = 3 x 10C5M. The loose-pile surplus rule had grown it to 5-6 haulers (50-60 CARRY): the piles were sink-bound (ctl cont 2000 full,
  // 1-2 upgraders under the wall rule), so extra haulers only cost upkeep. Max 4 (one spare for stock/storage moves).
  // 10-29 patrol: with A→ctl links + w8filler, local need ~9 CARRY (1x10C); floor 2. Pre-link keeps old 3–4.
  // 11-02 02:4x strategy: soft-cap ≤2 (LEAN_SOFT) saturates ctl cont → source conts fill → src_A harvest soft (~2 e/t).
  // HMAX=2 also blocked the loose>1200 surplus rule from spawning a 3rd hauler, so piles never drained into rebuild-band storage.
  // Cap 3 under links so overflow can park into storage without lifting the upgrader soft-cap (floor stays 2 via hFloor).
  // 11-04 08:4x: link-era HMAX=3 + Math.min(..., loose>2000?4:3) still capped at 3 — the "4th when >2k" comment was dead.
  // SoftCap+leanBank parks nUp≤2 while B (south, no link) + A-overflow pile to looseE~3–5k; 3×10C cannot clear into storage.
  // Overmind transporters size off mining e/t×distance independent of storageBuffer; TooAngel keeps logistics warm while upgrade parks.
  // Dynamic: links → 3 steady / 4 while loose>2000 (overflow valve). Floor stays 2.
  const looseNow = looseE(room);
  const HMAX = wm.links ? (looseNow > 2000 ? 4 : 3) : Math.max(3, Math.min(4, Math.ceil(((wm.lcarry || 20) + 10) / 10) + 1));
  if (!want && rhaulShort) want = 'w8rhauler';
  // 12:00: local loose ~2.9k (source conts 1090/2000) with hub 0 while spawn waited on a 1000-cost 4th builder (have 3). Surplus
  // haulers sit behind builders in the queue (same trap as the rhauler floor): floor up to 5 haulers ahead of the 4th builder
  // while piles > 2500 so energy reaches hub/builders before more WORK.
  if (!want && sites && looseE(room) > 2500 && n('w8hauler') < HMAX) want = 'w8hauler';
  // 04:10: size by remaining build work, not site count: 3 cheap road sites (~900 left) brought a 4th builder while the ctl cont sat at 0,
  // wbuilder idle 0.69 (6h) and 4 upgraders energy-starved
  else if (!want && !raidPause && sites && n('w8builder') < (siteRem(room) >= 3000 ? 4 : siteRem(room) >= 1200 ? 2 : 1)) want = 'w8builder'; // 17:20: 1 for a small backlog (2 road sites ~480 kept 3x 6W builders, 2.4 e/t upkeep) // 17:05: Spawn2 sat idle at 300/300 with 5 ext sites
  // 5) hauler surplus only. The upgrader surplus that jumped to 4–6 the tick stor crossed LEAN_SOFT
  // is gone (11-10): that rule spent a thin 25k bank (25.4k→16k and 25.7k→14.7k the same day) for ~+2.7 e/t
  // the feed could not support. Peacetime count is upgTarget — 2 until the 40k/500 latch, then a steady 3.
  if (!want && !raidPause) {
    const loose = looseE(room);
    if (loose > 1200 && n('w8hauler') < Math.min(HMAX, loose > 2000 ? 4 : 3)) want = 'w8hauler'; // 18:20: 4th when >2k piles (far south source)
  }
  // 6) wall builder from surplus (19:18): 1 builder while a seal wall is below target and spawn is full
  // 19:31: 2 while >1500 loose energy piles (2.8k at 19:30 with the ctl container full and upgraders at the WORK cap)
  // 11-03 02:4x: soft-gate — deep seal only while sealDeepOk; edge band (stor < sealMinE+SEAL_EDGE) caps at 1 builder; parked still allows 1 for STAGE3 floor
  {
    const storS = room.storage ? (room.storage.store[RESOURCE_ENERGY] || 0) : 0;
    const deep = TH.sealDeepOk(storS);
    const tgt = deep ? wtgt : Math.min(wtgt, TH.STAGE3);
    const edgeFat = deep && storS >= TH.sealMinE() + TH.SEAL_EDGE;
    const maxB = deep ? (looseE(room) > 1500 && edgeFat ? 2 : 1) : 1;
    if (!want && !raidPause && room.energyAvailable === cap && n('w8builder') < maxB) {
      // 11-02 (Misaki t375u): raise above STAGE3 only while sealDeepOk (softCap2 + sticky park + sealMinE)
      if (room.find(FIND_STRUCTURES, { filter: s => s.structureType === STRUCTURE_WALL && s.hits < tgt && C.SEAL.some(([x, y]) => s.pos.x === x && s.pos.y === y) }).length) want = 'w8builder';
    }
  }
  // 10-21 11:2x patrol: with 0 sites and the seal at cap no builder spawned, so nothing repaired the kept roads.js network (27 of 116
  // below 30%, link road 14,35/15,34 at 300 hits, about 3k ticks from vanishing). 1 maintenance builder while a kept road/container is critical.
  // 11:38 strategy: Overmind owns containers <50%; spawn earlier for container debt.
  // 14:4x: road maint threshold 20%→25% (= RoadLogistics criticalThreshold / w8day.roadCrit) so softCap-clear seal does not starve 10–25% roads.
  // 11-04 14:4x strategy (post-abort): builders recycled to 0; contMinPct slid 46→38 (contLow=3) while softCap/leanBank rebuilt
  // stor 0→22k. Old gate energyAvailable===cap + Game.time%50 left Spawn2 idle for long stretches at eAvail 3–5k/5600
  // (fillers topping towers/ext while soft-band parks). Overmind WorkerOverlord sizes repair from containers <50% /
  // RoadLogistics critical independent of fortifyDutyThreshold/storageBuffer — repair duty is not "wait for full spawn".
  // Split: container debt arms at energyAvailable≥200 (min builder body) with no %50 throttle; roadCrit-only keeps
  // full-cap + %50 (optional polish, not crash).
  // 11-05 20:2x 12h strategy: post-W47N9 war drain, contMinPct slid 20→12 / roadCrit~62 with only 1 maint builder
  // (motion working~14% — losing to container decay 50 hits/t × N). Overmind sizes workers from repairTicks up to
  // MAX_WORKERS=5; fortifyDutyThreshold=500k is a separate gate. Allow a 2nd builder when ≥3 containers sit <50%
  // so reclaim beats decay under softCap (still caps at 2 — not a seal/fortify burst).
  if (!want && !raidPause) {
    const contDebtN = room.find(FIND_STRUCTURES, { filter: s =>
      s.structureType === STRUCTURE_CONTAINER && s.hits < s.hitsMax * 0.5 }).length;
    const nB = n('w8builder');
    if (contDebtN > 0 && nB < 1 && room.energyAvailable >= 200) want = 'w8builder';
    else if (contDebtN >= 3 && nB < 2 && room.energyAvailable >= 200) want = 'w8builder';
    else if (!nB && room.energyAvailable === cap && Game.time % 50 === 0) {
      const keep = new Set(require('./roads').ROADS.map(([x, y]) => x * 50 + y));
      if (room.find(FIND_STRUCTURES, { filter: s =>
        s.structureType === STRUCTURE_ROAD && keep.has(s.pos.x * 50 + s.pos.y) && s.hits < s.hitsMax * 0.25
      }).length) want = 'w8builder';
    }
  }
  // 7) W47N7 remote (after all local roles): only while home's reserve7 holds the reservation for us
  if (!want && ours7) {
    // 02:16: 3 rhaulers fell behind 2 reserved sources (~20 e/t): W47N7 had 31,34 full 2000 + 5871 dropped, 18,17 at 1138.
    // +1 per 1500 loose above 1500 in W47N7 (max 6), same idea as the local hauler surplus rule
    // looseE already counts drops + containers (CTL/HUB excludes are W47N8 coords, so both W47N7 conts count)
    // 02:35: max 6 -> 8: with 5 alive the pile kept growing (6175 -> 6229 dropped + conts 1978/2000 by t83729299); round trips ~90-120 ticks
    // at 400 carry = ~3.6 e/t each, below the 2 sources' ~20 e/t plus decay
    // 18:05: need x1.0 (model rcarry already carries the 1.1 congestion factor; x1.1 kept 75 CARRY vs 56 with W47N7 conts empty)
    if (!want && n('w8rhauler') < 8 && rCarry(100) < rNeed + 16 * Math.floor(Math.max(0, lo7 - 3000) / 2000)) want = 'w8rhauler';
  }
  // Wartime raid after miners/haulers/fillers/rminers/rhaulers. A short logistics creep already set `want`
  // and spawns small. defer banks the partial pile instead of dropping it into an upgrader/builder.
  if (!want) {
    const RD = require('../../roles/raid9'), w = RD.wantSpawn(room, avail);
    if (w && w.defer) { markWait('raid9', w.cost, avail); return; }
    if (w) {
      const rv = spawn.spawnCreep(w.body, 'raid9_' + room.name + Game.time, { memory: w.mem, energyStructures: energyOrder(room) });
      if (rv === OK) { RD.noteSpawned(w.kind); FM.spent(w.cost); markSpawn(); return; }
    }
  }
  if (!want) { markIdle(); return; }
  // emergency: nothing alive that refills -> spawn with what we have
  const starving = !n('w8hauler') || !n('w8miner');
  // Combat bodies are never shrunk to energyAvailable. Collection fills the pile; the body waits.
  const combatSpawn = want === 'w8guard' || want === 'w8defender' || want === 'w8healer';
  let e = combatSpawn ? cap : (starving ? Math.max(200, avail) : cap);
  // A cap rhauler is 15C1W8M=1250. The crash above is not 'starving' (local miners and haulers
  // are alive), so e stayed at cap and 458 energy could never start the haul. Pay a road body instead.
  if (want === 'w8rhauler' && storPark < LEAN_ARM) e = rhaulBudget(cap, avail, storPark, n('w8rhauler'));
  const body = body7 || bodyFor(want, e), cost = _.sum(body, p => BODYPART_COST[p]);
  if (avail < cost) { markWait(want, cost, avail); return; }
  const born = want + Game.time;
  const rv = spawn.spawnCreep(body, born, { memory: Object.assign({ role: want, home: C.ROOM, born: Game.time, v2: 1 }, mem), energyStructures: energyOrder(room) });
  if (rv === OK) {
    if (want === 'w8upgrader') require('../../managers/spawn').notePendingSpawn(room, want, born);
    FM.spent(cost);
    markSpawn();
  }
}
const isGate = (x, y) => (C.GATE || []).some(([a, b]) => a === x && b === y);
function placeSeal(room) {
  for (const [x, y] of C.SEAL) {
    if (isGate(x, y)) { // rampart gate (13:30): never re-wall; rampart site only once the old wall is gone
      const st = room.lookForAt(LOOK_STRUCTURES, x, y);
      if (!st.some(s => s.structureType === STRUCTURE_WALL || s.structureType === STRUCTURE_RAMPART) && !room.lookForAt(LOOK_CONSTRUCTION_SITES, x, y).length) room.createConstructionSite(x, y, STRUCTURE_RAMPART);
      continue;
    }
    if (room.lookForAt(LOOK_STRUCTURES, x, y).some(s => s.structureType === STRUCTURE_WALL)) continue;
    if (room.lookForAt(LOOK_CONSTRUCTION_SITES, x, y).length) continue;
    room.createConstructionSite(x, y, STRUCTURE_WALL);
  }
}
const L = require('./layout');
const TH = require('./threat'); // v3b (approved 20:11): ORDER per type nearest-core first; STRIPS with filler stand
const PRIO = ['spawn', 'tower', 'extension', 'container', 'storage', 'link', 'terminal', 'extractor', 'lab', 'factory', 'powerSpawn', 'nuker', 'observer', 'road']; // no 'rampart' (17:15, see layoutRun)
// 10-31 (Misaki): KEY structures (tower/spawn/storage/terminal) may keep/get a rampart site — tower 24,8 was naked while 33,35 had ~100k.
// Empty planned slots still get no rampart (old 17:15 rule). Soft staging (SOFT_RAMP) raises KEY covers to ~100k.
const KEY = ['spawn', 'storage', 'tower', 'terminal'];
// 11-12: lab/factory covers are not KEY (placeKeyRamps must not auto-place them) but a parent-placed
// rampart site on that tile has to survive, and the built cover has to be held at 300k (see rampHold).
const IND_RAMP = 300000;
function indAt(room, x, y) {
  if (!room || !room.lookForAt || x == null) return false;
  const hit = list => list && list.some(s => s && (s.structureType === 'lab' || s.structureType === 'factory'));
  if (hit(room.lookForAt(LOOK_STRUCTURES, x, y))) return true;
  if (typeof LOOK_CONSTRUCTION_SITES !== 'undefined' && hit(room.lookForAt(LOOK_CONSTRUCTION_SITES, x, y))) return true;
  return false;
}
const keepRamp = (room, x, y) => isGate(x, y) || (x === L.ORDER.spawn[0][0] && y === L.ORDER.spawn[0][1])
  || room.lookForAt(LOOK_STRUCTURES, x, y).some(s => KEY.includes(s.structureType))
  || indAt(room, x, y);
function placeKeyRamps(room) {
  for (const s of room.find(FIND_MY_STRUCTURES, { filter: s => KEY.includes(s.structureType) })) {
    const { x, y } = s.pos;
    if (room.lookForAt(LOOK_STRUCTURES, x, y).some(o => o.structureType === STRUCTURE_RAMPART)) continue;
    if (room.lookForAt(LOOK_CONSTRUCTION_SITES, x, y).length) continue;
    room.createConstructionSite(x, y, STRUCTURE_RAMPART);
  }
}
const isTemp = s => L.TEMP_EXT.some(([x, y]) => s.pos.x === x && s.pos.y === y);
function swapTemp(room, minE = 50000) {
  const hub = room.lookForAt(LOOK_STRUCTURES, L.ORDER.spawn[0][0], L.ORDER.spawn[0][1]).some(s => s.structureType === STRUCTURE_SPAWN && s.my);
  if (!hub || !room.storage || room.storage.store[RESOURCE_ENERGY] <= minE || room.energyAvailable < room.energyCapacityAvailable) return null;
  if (room.find(FIND_MY_CONSTRUCTION_SITES, { filter: s => s.structureType === STRUCTURE_EXTENSION }).length || room.find(FIND_MY_CONSTRUCTION_SITES).length >= 5) return null;
  const temp = L.TEMP_EXT.map(([x, y]) => room.lookForAt(LOOK_STRUCTURES, x, y).find(s => s.structureType === STRUCTURE_EXTENSION)).find(Boolean);
  if (!temp) return null;
  const tr = room.getTerrain(), slot = L.ORDER.extension.find(([x, y]) => !room.lookForAt(LOOK_STRUCTURES, x, y).some(s => s.structureType === STRUCTURE_EXTENSION));
  if (!slot || (tr.get(slot[0], slot[1]) & 1) || room.lookForAt(LOOK_STRUCTURES, slot[0], slot[1]).some(s => s.structureType !== STRUCTURE_RAMPART)) return null;
  if (temp.destroy() !== OK) return null;
  (Memory.ops = Memory.ops || {}).w8swap = { from: [temp.pos.x, temp.pos.y], to: slot, t: Game.time };
  return slot;
}
// 10-20 13:39 (Misaki order): relocate Spawn2 15,18 -> 34,30 (was 32,32, see layout.js) (RCL5 allows 1 spawn: destroy, then build 15k site), then swap the
// 5 temp extensions by Spawn2 into v3b ORDER slots one at a time. Memory.ops.w8move.phase: prep -> build -> ext -> done.
// prep only fires when it is safe: no hostiles/threat mode, storage >= MOVE_E (whole spawn bill banked), spawn idle and full, both
// miners + 2 haulers TTL >= 500, a builder TTL >= 700 (nobody needs a spawn during the ~300-500 t build). While in prep the room banks
// (upgraders capped at 1). Abort = set phase 'hold' (prep never resumes on its own once held).
// 10-20 15:5x (Misaki: move ASAP): bank 16k -> 9k in storage + hub container. The 15k site is built from the bank plus live income
// (W47N8 + W47N7 ~20-25 e/t keeps flowing through haulers while no spawn exists): ~6k / 22 e/t ~ 280 t extra build time.
const MOVE_E = 9000, N9_QUIET = 150; // ~one north_watch scan (10 min ~ 140 t)
const bankE = room => (room.storage ? room.storage.store[RESOURCE_ENERGY] : 0) + _.sum(room.lookForAt(LOOK_STRUCTURES, C.HUB_CONT[0], C.HUB_CONT[1]).filter(s => s.structureType === STRUCTURE_CONTAINER), s => s.store[RESOURCE_ENERGY]);
function moveReady(room) {
  const sp = room.find(FIND_MY_SPAWNS)[0], cs = mine(), ttl = (r, t) => cs.filter(c => c.memory.role === r && c.ticksToLive >= t).length;
  const why = [];
  if (!sp || sp.pos.x !== C.SPAWN[0] || sp.pos.y !== C.SPAWN[1]) why.push('spawn');
  if (sp && sp.spawning) why.push('spawning');
  // 10-20 14:0x (Misaki ordered the move today): TH.on() never clears while W48N9 holds >=2 armed (north_watch refreshes w8threatN), so
  // gate only on real proximity: hostiles in W47N8, invasion(), or armed creeps in W47N9 (north_watch w8n9a) within N9_QUIET ticks.
  // 10-20 18:1x (Misaki order: move at 19:30 despite the W47N9 border): Memory.ops.w8move.force = 1 skips ONLY the W47N9 (w8n9a) check.
  // Forced moves additionally need: north line >= 100k, both towers >= 700, a builder within 3 of the new slot, a w8guard alive.
  const n9 = (Memory.ops || {}).w8n9a || 0, mv = (Memory.ops || {}).w8move || {}, force = !!mv.force;
  if (room.find(FIND_HOSTILE_CREEPS).length || TH.invasion() || (!force && n9 > 0 && Game.time - n9 < N9_QUIET)) why.push('threat');
  if (force) {
    const [nx, ny] = L.ORDER.spawn[0];
    if (room.find(FIND_STRUCTURES, { filter: s => (s.structureType === STRUCTURE_WALL || s.structureType === STRUCTURE_RAMPART) && C.SEAL.some(([x, y]) => s.pos.x === x && s.pos.y === y) && s.hits < 100000 }).length) why.push('walls');
    if (room.find(FIND_MY_STRUCTURES, { filter: s => s.structureType === STRUCTURE_TOWER && s.store[RESOURCE_ENERGY] < 700 }).length) why.push('towers');
    if (!cs.some(c => c.memory.role === 'w8builder' && !c.spawning && c.pos.inRangeTo(nx, ny, 3) && c.store[RESOURCE_ENERGY] > 0)) why.push('builderpos');
    if (!cs.some(c => c.memory.role === 'w8guard')) why.push('guard');
  }
  if (!room.storage || bankE(room) < MOVE_E) why.push('storage');
  if (room.energyAvailable < room.energyCapacityAvailable) why.push('energy');
  if (ttl('w8miner', 500) < 2 || ttl('w8hauler', 500) < 2 || ttl('w8builder', 700) < 1) why.push('ttl');
  return why;
}
function moveRun(room) {
  const o = (Memory.ops = Memory.ops || {}), m = o.w8move; if (!m || room.controller.level < 5) return;
  const [nx, ny] = L.ORDER.spawn[0], sp = room.find(FIND_MY_SPAWNS);
  // 18:1x: forced move, armed hostile inside W47N8 before the destroy -> hold (Misaki restarts it: phase 'prep')
  if (m.phase === 'prep' && m.force && room.find(FIND_HOSTILE_CREEPS).some(h => D.armed(h))) { m.phase = 'hold'; m.held = Game.time; m.why = ['armed-in-room']; return; }
  if (m.phase === 'prep') { // 15:5x: rampart over the new slot first (1 hit site, builders finish it fast); the spawn site may sit on a rampart
    const ramp = room.lookForAt(LOOK_STRUCTURES, nx, ny).some(s => s.structureType === STRUCTURE_RAMPART);
    if (!ramp && !room.lookForAt(LOOK_CONSTRUCTION_SITES, nx, ny).length) room.createConstructionSite(nx, ny, STRUCTURE_RAMPART);
    m.why = moveReady(room); if (!ramp) m.why.push('rampart'); if (m.why.length) return;
    const old = sp[0]; if (old.destroy() === OK) { m.phase = 'build'; m.t0 = Game.time; } return; }
  if (m.phase === 'build') {
    if (sp.some(s => s.pos.x === nx && s.pos.y === ny)) { m.phase = 'ext'; m.t1 = Game.time; return; }
    if (!sp.length && !room.lookForAt(LOOK_CONSTRUCTION_SITES, nx, ny).some(s => s.structureType === STRUCTURE_SPAWN)) m.site = room.createConstructionSite(nx, ny, STRUCTURE_SPAWN, 'Spawn2');
    return;
  }
  if (m.phase === 'ext') { if (!L.TEMP_EXT.some(([x, y]) => room.lookForAt(LOOK_STRUCTURES, x, y).some(s => s.structureType === STRUCTURE_EXTENSION))) { m.phase = 'done'; m.t2 = Game.time; } else extBatch(room, m); }
}
// 10-20 20:1x (Misaki: "move the whole base, not just the spawn"): ext phase no longer waits for storage > 3500 and one-at-a-time swaps.
// The remaining west extensions (TEMP_EXT, farthest from storage first) are destroyed in one batch of <= EXT_BATCH and their
// replacements are placed right away in the next unbuilt ORDER.extension slots near storage (sites are built from live income).
// Guards: no hostile in room, capacity after the batch >= EXT_CAP_MIN (filler/guard/miner bodies fit), and no
// extension site still pending (next batch waits for the previous one). 50 e of stored energy per destroyed extension is lost.
const EXT_BATCH = 5, EXT_CAP_MIN = 1300;
function extBatch(room, m) {
  const sp = room.find(FIND_MY_SPAWNS)[0];
  if (!sp || room.find(FIND_HOSTILE_CREEPS).length) return 0; // spawning is fine: its energy is already paid
  if (room.find(FIND_MY_CONSTRUCTION_SITES, { filter: s => s.structureType === STRUCTURE_EXTENSION }).length) return 0;
  const [sx, sy] = L.ORDER.storage[0], d = p => Math.max(Math.abs(p.x - sx), Math.abs(p.y - sy));
  const temp = L.TEMP_EXT.map(([x, y]) => room.lookForAt(LOOK_STRUCTURES, x, y).find(s => s.structureType === STRUCTURE_EXTENSION)).filter(Boolean).sort((a, b) => d(b.pos) - d(a.pos));
  const tr = room.getTerrain(), free = L.ORDER.extension.filter(([x, y]) => !(tr.get(x, y) & 1) && !room.lookForAt(LOOK_STRUCTURES, x, y).length && !room.lookForAt(LOOK_CONSTRUCTION_SITES, x, y).length);
  let n = Math.min(EXT_BATCH, temp.length, free.length, Math.floor((room.energyCapacityAvailable - EXT_CAP_MIN) / 50));
  if (n <= 0) return 0;
  let done = 0;
  for (let i = 0; i < n; i++) if (temp[i].destroy() === OK) { room.createConstructionSite(free[i][0], free[i][1], STRUCTURE_EXTENSION); done++; }
  m.batch = { n: done, t: Game.time, to: free.slice(0, done) };
  return done;
}
// 10-20 17:0x (Misaki: storage 20k+ idle): banking only holds MOVE_E + 2k; above that upgraders/builders/repairs run as normal
const BANK_HOLD = MOVE_E + 2000, banking = room => moving() && bankE(room) < BANK_HOLD;
const moving = () => { const m = Memory.ops && Memory.ops.w8move; return !!m && (m.phase === 'prep' || m.phase === 'build'); };
const LEAN_STOR = 20000;
// 02:4x 2026-11-01 strategy: hysteresis re-arm + soft-cap. Disarm at 20k; re-arm only below 15k so a brief dip
// (remote DEFEND / soft drain) does not thrash ready↔bank20. Soft-cap ≤2 upgraders while stor < 25k (Overmind
// storageBuffer scales WORK off surplus; we keep a tighter cushion but stop dumping it into ctl).
const LEAN_ARM = 15000;
// Crash rhauler budget. Cap body at RCL7 is 15C1W8M = 1250, which an empty bank cannot pay.
// bodyFor below 450 is the 1:1 shape (2C2M at 200). Pass at least 450 so the first hauler is the
// road body k>=2 (3C1W2M = 350) — the largest shape avail ~458 can start. Once any rhauler is
// alive, wait for k>=4 (7C1W4M = 650) instead of filling the carry quota with more 3C creeps.
// A tick that can already pay the cap body still gets that body.
function rhaulBudget(cap, avail, storE, haveRh) {
  if ((storE || 0) >= LEAN_ARM) return cap;
  const full = _.sum(bodyFor('w8rhauler', cap), p => BODYPART_COST[p]);
  if (avail >= full) return cap;
  return Math.max(haveRh ? 650 : 450, Math.min(avail || 0, cap));
}
const LEAN_SOFT = 25000;
// 08:4x 2026-11-03 strategy: softCap energy hysteresis. Clear at LEAN_SOFT; re-arm only below
// LEAN_SOFT_ARM. Live 23.4↔25.5k thrash recycled nUp 3→2 every boundary cross (seal soft-gate
// parks seal only — softCap itself had zero hysteresis). Mirror leanBank 15/20k; do NOT raise
// LEAN_SOFT (Misaki rejected sealMinE 35k / accepted 25k edge). softThin/sealDeepOk stay STRICT
// <LEAN_SOFT so seal still waits for a true ≥25k clear.
const LEAN_SOFT_ARM = 22000;
// 11-10: upgrader latch, separate from LEAN_SOFT / seal. Hold keep=2 until storage has stayed
// >= 40k for 500 consecutive ticks, then a steady 3. Re-arm to 2 below 30k. A brief cross of
// the 25k seal line must not spawn 4–6, and must not sit at 3 on that thin edge either.
const UP_STICKY = 40000;
const UP_STICKY_T = 500;
const UP_REARM = 30000;
function upBankTick(storE) {
  const o = (Memory.ops = Memory.ops || {});
  const s = (o.w8up = o.w8up || { on: 0, since: 0 });
  const e = storE || 0;
  if (e < UP_REARM) { s.on = 0; s.since = 0; return false; }
  if (s.on) return true;
  if (e >= UP_STICKY) {
    if (!s.since) s.since = Game.time;
    if (Game.time - s.since >= UP_STICKY_T) { s.on = 1; return true; }
    return false;
  }
  s.since = 0;
  return false;
}
// 11-12: while any construction site is up, RCL7 keep is 1 (home spawn.js already cuts to 1 on nSites).
// Sites gone → the previous keep (2 until the 40k/500 latch, then 3; threatSoft stays ≤2; leanBank bands unchanged).
// Does not lift softCap or the latch. Below RCL7 the old target is left alone.
function upCapN(room, keep) {
  if (!room || !room.controller || room.controller.level < 7) return keep;
  if (!room.find || typeof FIND_MY_CONSTRUCTION_SITES === 'undefined') return keep;
  return room.find(FIND_MY_CONSTRUCTION_SITES).length ? Math.min(keep, 1) : keep;
}
// Peacetime w8upgrader target. leanBank / day-of miss stay as they were. threatSoft caps at 2
// even after the sticky bank. Never 4–6. Open sites cap the result at 1 (upCapN).
function upgTarget(room) {
  const se = room.storage && room.storage.store ? (room.storage.store[RESOURCE_ENERGY] || 0) : 0;
  let t;
  if (energyBank(room)) t = se < LEAN_ARM ? (room.controller.ticksToDowngrade < 20000 ? 1 : 0) : 2;
  else {
    const m = dayofMiss(room);
    if (m.missSpawn || m.missTower) t = 1;
    else if (threatSoft()) t = 2;
    else t = upBankTick(se) ? 3 : 2;
  }
  return upCapN(room, t);
}
// 11:4x 2026-11-02 (Misaki): reversible ≤2 w8upgrader soft-cap while threat soft is on.
// threatSoft = TH.localOn() — Memory.ops.w8threat within TH.WINDOW (1500). Same predicate as
// rampHold's w8soft.why==='threat' (soft-ramp raise blocked; towers keep energy for combat,
// repair only above 600). Seal walls already above the 100k urgent floor leave wallsLow false,
// so the peacetime rule was lifting base nUp to 3 and surplus to 4×10W (WORK40) as soon as
// stor≥LEAN_SOFT. That starved the ctl (waiting_feed) and dropped 2h upgrade (~46.7%).
// Neighbor staging w8threatN (TH.on() but not localOn) does NOT hold the cap — the W47N9 camp
// is chronic and must not pin upgraders. When the local window expires, softCap2 falls back to
// energy hysteresis (08:4x) and base/surplus resume. Home W46N8 upgraders do not use this.
function threatSoft() { return TH.localOn(); }
// Energy half of softCap2 — sticky via w8day.softE so hauler park (roles.js) can follow without
// threatSoft forcing a park during combat drain in the [ARM,SOFT) band.
function softEnergyCap(storE) {
  const e = storE || 0;
  if (e >= LEAN_SOFT) return false; // clear
  const was = !!(Memory.ops && Memory.ops.w8day && Memory.ops.w8day.softE);
  if (!was && e >= LEAN_SOFT_ARM) return false; // hysteresis hold
  return true; // below ARM, or was on and still below SOFT
}
function softCap2(storE) { return threatSoft() || softEnergyCap(storE); }
// 11:4x strategy 2026-11-02: peacetime overshoot after softCap lift.
// Overmind UpgradeSite scales WORK off storageBuffer (~100k) AND requests battery input at
// upgradePowerNeeded (battery kept ≥50%). TooAngel co-locates storage beside the upgrader so
// feed is not the bottleneck. We park at LEAN_SOFT 25k (tighter), then the surplus rule counted
// stor-2000 → 4×10W=WORK40 the tick softCap2 cleared, while A→ctl link + haulers only deliver
// ~8 e/t to ctl (hub ~18) → waiting_feed ~30%, 2h upgrade stuck ~53%. Gate surplus on ctl battery.
const FEED_MIN = 800; // surplus nUp>base needs ctl cont+link ≥ this (hold-band uses 1200; 800 = link almost full)
function ctlBattery(room) {
  let e = 0;
  const cont = room.lookForAt(LOOK_STRUCTURES, C.CTL_CONT[0], C.CTL_CONT[1]).find(s => s.structureType === STRUCTURE_CONTAINER);
  if (cont && cont.store) e += cont.store[RESOURCE_ENERGY] || 0;
  const [lx, ly] = C.CTL_LINK || [13, 25];
  const link = room.lookForAt(LOOK_STRUCTURES, lx, ly).find(s => s.structureType === STRUCTURE_LINK);
  if (link && link.store) e += link.store[RESOURCE_ENERGY] || 0;
  return e;
}
// 11-03 05:4x strategy: upgCeil/recycle must wait for hub link STRUCTURE, not just config.HUB_LINK.
// Flipping the flag places a 5k site; raising ceil on the flag alone recreates 14:4x waiting_feed before
// ferry+linkRun can feed ctl. Screeps link cooldown = getRangeTo (hub 32,33→ctl 13,25 = 19) → ~42 e/t
// gross / ~41 net after 3% — enough for WORK40+ once live. Matches w8day.hubReady.
// A link still standing at retired 33,34 is not this structure.
function hubLinkLive(room) {
  if (!C.HUB_LINK || !room) return false;
  const [hx, hy] = L.hubLinkPos();
  return !!room.lookForAt(LOOK_STRUCTURES, hx, hy).find(s => s.structureType === STRUCTURE_LINK);
}
// 08:4x 2026-10-31 strategy: after RCL7 day-crit (spawn2+tower3), throttle upgrade so storage can reach 20k for lean KO.
// 20:4x: day-crit ≠ 50ext — arm leanBank while the 10ext wave is still building (builders keep sites; upgraders throttle).
// Opt-out: Memory.ops.w8leanBank === false. Does NOT flip RCL6_MINERALS / RCL6_LABS. See docs/RCL7.md "08:4x".
function dayofMiss(room) {
  const has = (typ, x, y) => room.lookForAt(LOOK_STRUCTURES, x, y).some(s => s.structureType === typ);
  const [sx, sy] = L.ORDER.spawn[1], [tx, ty] = L.ORDER.tower[2];
  const nExt = room.find(FIND_MY_STRUCTURES, { filter: s => s.structureType === STRUCTURE_EXTENSION }).length;
  return { missSpawn: !has(STRUCTURE_SPAWN, sx, sy), missTower: !has(STRUCTURE_TOWER, tx, ty),
    missExt: Math.max(0, 50 - nExt) };
}
// 23:4x 2026-10-31 strategy: after gate flip, keep leanBank until terminal + mineral container stand
// (~110k lean KO build). Otherwise `if (RCL6_MINERALS) return false` would disarm on flip and full
// upgrade would starve the terminal/minCont sites as soon as stor dipped below 20k.
function leanMinBuild(room) {
  if (!C.RCL6_MINERALS) return false;
  if (!room.terminal) return true;
  const [mx, my] = C.MINERAL_CONT || [37, 44];
  return !room.lookForAt(LOOK_STRUCTURES, mx, my).some(s => s.structureType === STRUCTURE_CONTAINER);
}
function leanBank(room) {
  // 20:4x 2026-10-31: arm after day-crit (spawn2+tower3) — do NOT wait for 50ext.
  // 17:4x already said flip/bank need not wait on the ext wave; §5.8 "50ext齐" was a doc/code mismatch.
  // 23:4x: stay armed while lean KO logistics structures are still missing after the gate flip.
  // 02:4x 2026-11-01: hysteresis — once disarmed (leanBank was 0), stay off until stor < LEAN_ARM (15k).
  // Live proof 00:14→01:25: ready@23k → 4 upgraders → dn20@~19.9k → re-arm → W47N7 DEFEND drained to ~1.7k.
  // 20:4x 2026-11-01 strategy: post-minBuild must NOT permanently disable leanBank while RCL6_MINERALS.
  // Soft-cap ≤2 alone left colony stor~3–5k (ctl-first sink feeds 2 upgraders; hold-band only [15k,20k)).
  // Overmind storageBuffer is gate-agnostic — keep our 15/20k hysteresis after logistics stand.
  const o = Memory.ops || {};
  if (o.w8leanBank === false) return false;
  if (!room.controller || room.controller.level < 7) return false;
  const minBuild = leanMinBuild(room);
  const storE = room.storage && room.storage.store ? (room.storage.store[RESOURCE_ENERGY] || 0) : 0;
  // Pre-flip / post-flip rebuild: bank until 20k. minBuild: keep throttle until structs exist (sites need the energy).
  if (!minBuild && storE >= LEAN_STOR) return false;
  // Hysteresis hold: after ready, do not re-arm on a shallow dip above LEAN_ARM (pre- or post-gate).
  const wasLean = !!(o.w8day && o.w8day.leanBank);
  if (!minBuild && !wasLean && storE >= LEAN_ARM) return false;
  const m = dayofMiss(room);
  return !(m.missSpawn || m.missTower);
}
const energyBank = room => banking(room) || leanBank(room);
function leanUpKeep(storE) {
  // 05:4x 11-04 strategy: banded leanBank upgrader ceiling after defense re-arm.
  // Emergency stor < LEAN_ARM → ≤1 (crash recovery). Rebuild [ARM, STOR) while leanBank sticky → ≤2
  // (= softCap parity). soft-band + sealPark already protect the climb; hard 0/1 through 15→20k froze
  // W47 at ~8 e/t for hours post-Invader. Overmind scales WORK above storageBuffer (never dual-stack
  // 0/1 then ≤2); TooAngel parks when thin but keeps a floor. Recycle floor is always ≥1 under bank.
  return (storE || 0) < LEAN_ARM ? 1 : 2;
}
function leanBankRecycle(room) {
  // 02:4x: keep ≤1 under leanBank; keep ≤2 while cushion thin (stor < LEAN_SOFT) even after ready.
  // 05:4x 11-01: soft-cap must survive RCL6_MINERALS flip — Overmind storageBuffer is gate-agnostic; post-minBuild stor can be ≪25k.
  // 05:4x 11-04: leanBank keep is BANDED — <LEAN_ARM →1, [ARM,STOR) →2 (softCap parity); was hard ≤1 entire bank.
  // 11:4x: softCap2 also recycles back to ≤2 while threat soft is on, even after stor≥LEAN_SOFT (4×10W waiting_feed).
  // 11:4x strategy: peacetime feed-starve — if softCap2 off but ctl battery thin, trim surplus above base 3 (keep stands saturable).
  // 05:4x: !hubLinkLive (not mere !HUB_LINK) — flag-on + 5k site still keeps ≤3 until structure stands.
  // 17:4x 11-04: soft-band surplus trim — softCap2 hysteresis hold leaves softCap2 OFF in [ARM,SOFT) so the ≤2
  // recycle does not fire, but hub+fat ctl also skips the feed-gate ≤3 trim → live nUp=4 drains soft-band.
  // Keep base-3 hysteresis (08:4x intent); only recycle surplus above 3 while stor < LEAN_SOFT.
  // 17:2x patrol: reconcile each tick (prune dead; release kept upgraders). Prior append-only left stale names on
  // Memory.ops.w8recycle so a kept stand worker kept walking to Spawn2 after the surplus died → upgrade flat.
  const o = (Memory.ops = Memory.ops || {});
  const prune = L => (L || []).filter(n => Game.creeps[n]);
  const nonUp = L => prune(L).filter(n => {
    const c = Game.creeps[n];
    return c && c.memory && c.memory.role !== 'w8upgrader';
  });
  const banking = leanBank(room);
  const storE = room.storage && room.storage.store ? (room.storage.store[RESOURCE_ENERGY] || 0) : 0;
  let keep = Infinity;
  // 11-10: RCL7 peacetime keep is 2 until the 40k/500 latch, then 3. threatSoft stays at 2.
  // The old soft-band trim (keep 3 in [22k,25k)) and the 4–6 surplus path are both gone,
  // so a 25k clear cannot leave four upgraders walking to Spawn2.
  if (banking) keep = leanUpKeep(storE);
  else if (room.controller && room.controller.level >= 7) keep = (threatSoft() || !upBankTick(storE)) ? 2 : 3;
  else { o.w8recycle = nonUp(o.w8recycle); return; }
  keep = upCapN(room, keep); // 11-12: open sites trim to 1; the 40k latch is restored once they finish
  const ups = [];
  for (const n in Game.creeps) {
    const c = Game.creeps[n];
    if (!c || !c.memory || c.memory.role !== 'w8upgrader' || c.spawning) continue;
    if (!(c.memory.home === room.name || (c.room && c.room.name === room.name))) continue;
    if (!c.name) c.name = n;
    ups.push(c);
  }
  ups.sort((a, b) => (b.ticksToLive || 0) - (a.ticksToLive || 0));
  const drop = ups.slice(keep).map(c => c.name).filter(Boolean);
  o.w8recycle = nonUp(o.w8recycle).concat(drop);
}
// W47N9 wartime: recycle colony upgraders (keep one if the controller is near downgrade) and every builder.
// Miners, haulers, fillers, and the W47N7 remote are not on this list.
function raidSoftKill(room) {
  const RD = require('../../roles/raid9');
  if (!RD.pauseCivilians()) return;
  const rows = [];
  for (const n in Game.creeps) {
    const c = Game.creeps[n];
    if (!c || !c.memory) continue;
    const role = c.memory.role;
    if (role !== 'w8upgrader' && role !== 'w8builder') continue;
    if (!(c.memory.home === room.name || (c.room && c.room.name === room.name))) continue;
    rows.push({ name: c.name || n, role, ttl: c.ticksToLive || 0, spawning: !!c.spawning });
  }
  const drop = RD.namesToRecycle(rows, RD.upgraderKeep(room));
  if (!drop.length) return;
  const o = (Memory.ops = Memory.ops || {});
  const L = o.w8recycle || [];
  for (const name of drop) if (name && !L.includes(name)) L.push(name);
  o.w8recycle = L;
}

// 14:4x strategy: dormant terminal.send K W47N8→W46N8 (lean KO). Overmind TerminalNetwork pattern —
// surplus at colony, deficit at home labs; TERMINAL_MIN_SEND=100, COOLDOWN=10; adjacent ~ceil(amt*(1-e^(-1/30))).
// 11:4x 2026-11-01: first-K pacing — thin-stor batch + homeFree/fee obs (post-minBuild stor often ≪15k).
// Gate false → no live send. termFuel (roles) parks energy for fees when gate flips.
const HOME_ROOM = 'W46N8';
const SEND_BATCH = 5000;      // full cushion / Overmind-ish chunk
const SEND_BATCH_THIN = 1000; // post-minBuild / lean recovery: ~33e fee adjacent vs ~165e for 5k
const TERM_MIN_SEND = 100;
function sendCost(amt, from, to) {
  if (typeof Game !== 'undefined' && Game.market && Game.market.calcTransactionCost)
    return Game.market.calcTransactionCost(amt, from, to);
  const range = (typeof Game !== 'undefined' && Game.map && Game.map.getRoomLinearDistance)
    ? Game.map.getRoomLinearDistance(from, to, true) : 1;
  return Math.ceil(amt * (1 - Math.exp(-range / 30)));
}
function mineralSend(room) {
  const o = (Memory.ops = Memory.ops || {});
  const w = o.w8min = o.w8min || {};
  w.sendOk = 1;
  const storE = room.storage && room.storage.store ? (room.storage.store[RESOURCE_ENERGY] || 0) : 0;
  const batchMax = (storE > 0 && storE < LEAN_ARM) ? SEND_BATCH_THIN : SEND_BATCH;
  w.batch = batchMax;
  if (!C.RCL6_MINERALS) { w.sendWhy = 'gate'; return; }
  const term = room.terminal;
  if (!term) { w.sendWhy = 'noTerm'; return; }
  // A live commander order yields the terminal. Phase 1 does not call terminal.send (no market, no extra sends).
  if (require('../../utils/cmd').blocks(term)) { w.sendWhy = 'cmd'; return; }
  if (term.cooldown > 0) { w.sendWhy = 'cd'; w.cd = term.cooldown; return; }
  const K = (typeof RESOURCE_KEANIUM !== 'undefined') ? RESOURCE_KEANIUM : 'K';
  const k = term.store[K] || 0;
  if (k < TERM_MIN_SEND) { w.sendWhy = 'noK'; w.cd = 0; return; }
  const home = Game.rooms[HOME_ROOM];
  const hTerm = home && home.terminal;
  if (!hTerm) { w.sendWhy = 'noHome'; return; }
  const free = hTerm.store.getFreeCapacity
    ? hTerm.store.getFreeCapacity()
    : Math.max(0, (hTerm.storeCapacity || 300000) - _.sum(hTerm.store));
  w.homeFree = free;
  if (free < TERM_MIN_SEND) { w.sendWhy = 'homeFull'; return; }
  let amount = Math.min(k, batchMax, free);
  let cost = sendCost(amount, room.name, HOME_ROOM);
  const e = term.store[(typeof RESOURCE_ENERGY !== 'undefined') ? RESOURCE_ENERGY : 'energy'] || 0;
  while (amount >= TERM_MIN_SEND && e < cost) {
    amount = Math.floor(amount / 2);
    cost = sendCost(amount, room.name, HOME_ROOM);
  }
  w.fee = cost;
  if (amount < TERM_MIN_SEND) { w.sendWhy = 'noE'; w.needE = sendCost(TERM_MIN_SEND, room.name, HOME_ROOM); return; }
  const r = term.send(K, amount, HOME_ROOM);
  if (r === OK) {
    w.sendWhy = 'sent'; w.lastSend = Game.time; w.lastAmt = amount; w.needE = 0; w.cd = 0; w.fee = cost;
  } else {
    w.sendWhy = 'err' + r;
  }
}
// 20:4x strategy: day-of readiness observability. Spurs already live →
// remaining bill ≈ missing spawn2@33,30 + tower3@22,7 + (50−nExt)×3k. Reactive siteRem≥3k → ≤4 builders;
// no pre-bank (see docs/RCL7.md "20:4x"). 08:4x adds phase bank20/ready + leanBank.
function dayObs(room) {
  const o = (Memory.ops = Memory.ops || {});
  const rcl = room.controller.level;
  const need = Math.max(0, (room.controller.progressTotal || 0) - (room.controller.progress || 0));
  const sites = room.find(FIND_MY_CONSTRUCTION_SITES);
  const siteRemV = _.sum(sites, s => (s.progressTotal || 0) - (s.progress || 0));
  // Game.creeps (not FIND_MY_CREEPS) so layout unit stubs without that constant still run
  const inRoom = c => c.memory && (c.memory.home === room.name || (c.room && c.room.name === room.name) || (c.pos && c.pos.roomName === room.name));
  const builders = _.filter(Game.creeps, c => inRoom(c) && c.memory.role === 'w8builder').length;
  const upgraders = _.filter(Game.creeps, c => inRoom(c) && c.memory.role === 'w8upgrader').length;
  const storE = room.storage && room.storage.store ? (room.storage.store[RESOURCE_ENERGY] || 0) : 0;
  const has = (typ, x, y) => room.lookForAt(LOOK_STRUCTURES, x, y).some(s => s.structureType === typ);
  const [sx, sy] = L.ORDER.spawn[1], [tx, ty] = L.ORDER.tower[2];
  const miss = dayofMiss(room);
  const missSpawn = miss.missSpawn, missTower = miss.missTower, missExt = miss.missExt;
  let bill = siteRemV;
  if (missSpawn && !sites.some(s => s.structureType === STRUCTURE_SPAWN && s.pos.x === sx && s.pos.y === sy)) bill += 15000;
  if (missTower && !sites.some(s => s.structureType === STRUCTURE_TOWER && s.pos.x === tx && s.pos.y === ty)) bill += 5000;
  const extSites = sites.filter(s => s.structureType === STRUCTURE_EXTENSION).length;
  bill += Math.max(0, missExt - extSites) * 3000;
  // 05:4x strategy: day-of energy crash watch (docs/PLAN_W47N8.md / docs/RCL7.md).
  // 17:4x: north towers (inRange 4 of source-A stand) are fed by northFeed@600, NOT filler/hubNeedy —
  // split towerHubE/towerNorthE/nf so patrol can tell which path dipped. Filler hubNeedy only affects hub tower.
  const towers = room.find(FIND_MY_STRUCTURES, { filter: s => s.structureType === STRUCTURE_TOWER });
  const towerMinE = towers.length ? Math.min(...towers.map(t => (t.store && t.store[RESOURCE_ENERGY]) || 0)) : -1;
  const [ax, ay] = (C.SOURCES[0] && C.SOURCES[0].stand) || [26, 11];
  let towerNorthE = -1, towerHubE = -1;
  for (const t of towers) {
    const e = (t.store && t.store[RESOURCE_ENERGY]) || 0;
    if (t.pos.inRangeTo(ax, ay, 4)) towerNorthE = towerNorthE < 0 ? e : Math.min(towerNorthE, e);
    else towerHubE = towerHubE < 0 ? e : Math.min(towerHubE, e);
  }
  const nf = towerNorthE >= 0 && towerNorthE < 600 ? 1 : 0;
  const eAvail = room.energyAvailable || 0, eCap = room.energyCapacityAvailable || 0;
  let why = 'upgrade';
  // 20:4x: why=dayof only while day-crit (spawn2/tower3) missing. Ext wave + sites tracked via missExt/siteRem;
  // after crit done we enter bank20/ready even mid-ext so leanBank can arm (17:4x intent).
  if (rcl >= 7) why = (missSpawn || missTower) ? 'dayof' : 'done';
  else if (need < 80000) why = 'near';
  // 08:4x/20:4x: phase splits post-daycrit into bank20 (stor<20k) vs ready (≥20k cushion for lean KO).
  // 23:4x: minBuild while gate on but terminal/minCont still missing (post-flip lean KO construction).
  let phase = why;
  const minBuild = leanMinBuild(room);
  if (why === 'done') {
    if (minBuild) phase = 'minBuild';
    else if (storE >= LEAN_STOR) phase = 'ready'; // cushion filled (pre- or post-gate)
    else if (storE >= LEAN_ARM && !leanBank(room)) phase = 'ready'; // 02:4x hysteresis hold (15–20k)
    else phase = 'bank20'; // 20:4x: post-gate rebuild also uses bank20 (not forced ready by minerals)
  }
  // 20:4x: bankLeft honest post-gate too (was zeroed by RCL6_MINERALS, hiding cushion debt).
  const bankLeft = minBuild ? 0 : Math.max(0, LEAN_STOR - storE);
  // ~20 e/t net while leanBank (≤1 upgrader). Mid-ext, sites still sink energy first → fold siteRem into ETA.
  // minBuild: ETA ≈ remaining mineral sites / 20 (stor cushion already spent into sites).
  const lb = leanBank(room);
  const bankEta = (!lb) ? (bankLeft <= 0 ? 0 : -1)
    : (minBuild ? Math.ceil((siteRemV || 1) / 20) : Math.ceil((bankLeft + siteRemV) / 20));
  // 02:4x obs: bankWhy explains ETA honesty (threat WINDOW / remote pause lie about +20 e/t).
  // 20:4x: drop unconditional bankWhy=gate — post-minBuild leanBank can re-arm; use bank/hold/off/ready.
  const warMode = require('../../roles/raid9').pauseCivilians();
  let bankWhy = 'ok';
  if (minBuild) bankWhy = 'minBuild';
  else if (warMode) bankWhy = 'war'; // 14:4x wartime: assault pause labels before softCap/threatSoft
  else if (lb) bankWhy = (typeof TH !== 'undefined' && TH.on && TH.on()) ? 'threat' : 'bank';
  else if (storE < LEAN_STOR) bankWhy = (storE >= LEAN_ARM) ? 'hold' : 'off';
  else if (softEnergyCap(storE)) bankWhy = 'soft'; // 08:4x 11-02/11-03: soft-cap energy half (hysteresis) — park to soft
  else if (threatSoft()) bankWhy = 'threatSoft'; // 11:4x: local threat holds ≤2 (even above LEAN_SOFT)
  else bankWhy = 'ready'; // includes softCap hysteresis hold in [SOFT_ARM, SOFT)
  // 08:4x: looseE (drops + source conts, excl ctl/hub) so patrol can see stranded energy vs stor20k shortfall
  const loose = looseE(room);
  const softLeft = Math.max(0, LEAN_SOFT - storE);
  // 11-03 02:4x: refresh sticky seal park from dayObs too (layoutRun every 20t) — spawnRun owns every-tick path
  TH.updateSealPark(storE, upgraders, sites.length);
  // 23:4x: hub link readiness (dormant until HUB_LINK + structure). Patrol sees energy + gate without flipping.
  // 05:4x: hubReady mirrors hubLinkLive — same predicate as upgCeil/recycle (structure, not flag alone).
  const [hlx, hly] = L.hubLinkPos();
  const hubLink = room.lookForAt(LOOK_STRUCTURES, hlx, hly).find(s => s.structureType === STRUCTURE_LINK);
  const hubLinkE = hubLink && hubLink.store ? (hubLink.store[RESOURCE_ENERGY] || 0) : -1;
  const hubReady = hubLinkLive(room) ? 1 : 0;
  // 11:38 strategy: container/road repair debt for patrol (Overmind <50% containers / road critical 25%)
  // Guard FIND_STRUCTURES like looseE — some unit stubs omit the constant (layout-only tests).
  const keepR = new Set(require('./roads').ROADS.map(([x, y]) => x * 50 + y));
  let contMinPct = 100, roadCrit = 0, contLow = 0;
  if (typeof FIND_STRUCTURES !== 'undefined') {
    for (const s of room.find(FIND_STRUCTURES, { filter: s => s.structureType === STRUCTURE_CONTAINER || (s.structureType === STRUCTURE_ROAD && keepR.has(s.pos.x * 50 + s.pos.y)) })) {
      if (s.structureType === STRUCTURE_CONTAINER) {
        const pct = Math.floor(100 * (s.hits || 0) / (s.hitsMax || 1));
        if (pct < contMinPct) contMinPct = pct;
        if (pct < 50) contLow++;
      } else if ((s.hits || 0) < (s.hitsMax || 0) * 0.25) roadCrit++;
    }
  }
    const upLatched = rcl >= 7 && upBankTick(storE);
    const upKeepN = upCapN(room, lb ? leanUpKeep(storE) : (rcl >= 7 ? ((threatSoft() || !upLatched) ? 2 : 3) : 0));
    o.w8day = { t: Game.time, rcl, need, siteRem: siteRemV, builders, upgraders, storE, bill,
    missSpawn: missSpawn ? 1 : 0, missTower: missTower ? 1 : 0, missExt, why, phase,
    bankLeft, bankEta, leanBank: lb ? 1 : 0, bankArm: LEAN_ARM, bankSoft: LEAN_SOFT, softArm: LEAN_SOFT_ARM, bankWhy, softLeft,
    threatSoft: threatSoft() ? 1 : 0,
    softE: softEnergyCap(storE) ? 1 : 0, // 08:4x 11-03: energy-half sticky for seal/softCap2, not the upgrader count
    // 20:4x 11-03: soft-band park is STRICT se<LEAN_SOFT (roles); obs diverges from softE in post-clear [ARM,SOFT)
    softBand: (storE < LEAN_SOFT && ctlBattery(room) >= 1200) ? 1 : 0,
    softCap2: softCap2(storE) ? 1 : 0, // 11:4x/08:4x-11-03: seal/energy half. Upgrader count uses upLatched.
    // 11-10: 1 emergency lean / 2 until 40k sticky (or threat) / 3 after the latch. Never 0 (surplus) or 4–6.
    upgKeep: upKeepN,
    upLatched: upLatched ? 1 : 0, upArm: UP_STICKY, upRearm: UP_REARM, upStickyT: UP_STICKY_T,
    warMode: warMode ? 1 : 0, // 14:4x: Memory.ops.w47n9 assault freeze
    ctlBat: ctlBattery(room), feedOk: ctlBattery(room) >= FEED_MIN ? 1 : 0, // 11:4x strategy: peacetime surplus needs feedOk
    sealMinE: TH.sealMinE(), // effective deep-seal gate (Memory override visible)
    sealRaise: (TH.sealDeepOk(storE) && (TH.sealCap() > TH.STAGE3)) ? 1 : 0, // 02:4x: soft-gate (softCap2 + sticky park)
    sealPark: TH.sealParked() ? 1 : 0,
    towerMinE, towerHubE, towerNorthE, nf, eAvail, eCap, looseE: loose,
    // 08:4x 11-04: effective local hauler cap (links: 3 steady / 4 while loose>2000)
    hMax: ((Memory.ops && Memory.ops.w8model && Memory.ops.w8model.links) ? (loose > 2000 ? 4 : 3) : 4),
    hubLinkE, hubReady, hubLink: C.HUB_LINK ? 1 : 0, // 23:4x strategy: HUB_LINK plumbing obs
    // 23:4x 11-03: hubPrime=1 when hub link holds ≥HUB_SEND(200) — patrol sees pre-warm during softCap bank
    hubPrime: (hubReady && hubLinkE >= 200) ? 1 : 0,
    // 11-10: effective ceiling is the keep (2, or 3 after the sticky bank). The old hub-live ceil of 6 is retired.
    // 11-12: upKeepN is already 1 while any construction site is open (upCapN).
    upgCeil: rcl >= 7 ? upKeepN : (siteRemV >= 3000 ? 2 : 3),
    feedBound: (!hubLinkLive(room) && !softCap2(storE) && !warMode && upgraders >= (siteRemV >= 3000 ? 2 : 3)) ? 1 : 0,
    contMinPct, contLow, roadCrit }; // 11:38: repair debt (containers <50% / roads <25%)
  leanBankRecycle(room);
  raidSoftKill(room);
  // 23:4x strategy: lean KO readiness (docs/MINERAL_DEFENSE_ROADMAP.md §5). Dormant report only — gates stay false.
  const [mx, my] = C.MINERAL_CONT || [37, 44];
  const hasTerm = !!room.terminal;
  const hasExt = room.find(FIND_MY_STRUCTURES, { filter: s => s.structureType === STRUCTURE_EXTRACTOR }).length > 0;
  const hasMinCont = has(STRUCTURE_CONTAINER, mx, my);
  const min = (typeof FIND_MINERALS !== 'undefined' ? room.find(FIND_MINERALS) : [])[0];
  const kAmt = min && min.mineralType === 'K' ? (min.mineralAmount || 0) : 0;
  const kTerm = hasTerm ? (room.terminal.store.K || 0) : 0;
  const miners = _.filter(Game.creeps, c => inRoom(c) && (c.memory.role === 'w8mminer' || c.memory.role === 'mminer')).length;
  const gaps = [];
  if (!C.RCL6_MINERALS) gaps.push('gate');
  if (!hasTerm) gaps.push('terminal');
  if (!hasExt) gaps.push('extractor');
  if (!hasMinCont) gaps.push('minCont');
  // 11:4x: w8mminer+haul shipped. 14:4x: terminal.send shipped (dormant). Miner gap only once gate on.
  if (C.RCL6_MINERALS && !miners) gaps.push('miner');
  if (rcl < 7) gaps.push('rcl');
  if (storE < 20000) gaps.push('stor20k');
  // no longer gap 'send' — code present; live readiness is sendWhy (gate/noK/noE/…)
  const prev = o.w8min || {};
  const termE = hasTerm ? (room.terminal.store[RESOURCE_ENERGY] || 0) : 0;
  // 23:4x strategy: flipReady = full §5.6 propose checklist (does NOT auto-flip).
  // Structural gaps (gate/terminal/minCont) are expected until Misaki flips — excluded from flipGaps.
  const FLIP_TOWER = 600, FLIP_HOME = 15000, HOME = 'W46N8';
  const flipGaps = [];
  if (missSpawn || missTower) flipGaps.push('daycrit');
  // 20:4x: once flipped, stor20k is a cushion gap (w8min.gaps), not a flip blocker — avoid flipGaps noise.
  if (!C.RCL6_MINERALS && storE < LEAN_STOR) flipGaps.push('stor20k');
  if (towerMinE >= 0 && towerMinE < FLIP_TOWER) flipGaps.push('towerE');
  const home = Game.rooms[HOME];
  const homeStor = (home && home.storage && home.storage.store)
    ? (home.storage.store[RESOURCE_ENERGY] || 0) : -1;
  if (homeStor >= 0 && homeStor < FLIP_HOME) flipGaps.push('homeStor');
  if (C.RCL6_MINERALS) flipGaps.push('already');
  const flipReady = flipGaps.length === 0 ? 1 : 0;
  o.w8min = { t: Game.time, rcl, storE, kAmt, kTerm, hasTerm: hasTerm ? 1 : 0, hasExt: hasExt ? 1 : 0,
    hasMinCont: hasMinCont ? 1 : 0, miners, minOk: C.RCL6_MINERALS ? 1 : 0, labsOk: C.RCL6_LABS ? 1 : 0,
    hasCode: 1, sendOk: 1, termE,
    sendWhy: prev.sendWhy || (C.RCL6_MINERALS ? 'idle' : 'gate'),
    lastSend: prev.lastSend || 0, lastAmt: prev.lastAmt || 0, needE: prev.needE || 0, cd: prev.cd || 0,
    // 11:4x first-K pacing obs (mineralSend refreshes every tick; dayObs preserves between)
    homeFree: prev.homeFree || 0, batch: prev.batch || SEND_BATCH, fee: prev.fee || 0,
    // 17:4x: minerPrio=1 means spawn elevates w8mminer ahead of soft/surplus upgraders (Overmind mineral<upgrade).
    minerPrio: 1,
    gaps: gaps.join(','), why: gaps.length ? gaps[0] : 'ready',
    flipReady, flipGaps: flipGaps.join(','), homeStor, minBuild: minBuild ? 1 : 0 };
}
// Home roads.maintain uses the same batch (managers/roads.js BATCH) on a 100t cadence.
const ROAD_BATCH = 15;
function roadExit(x, y) { return x === 0 || y === 0 || x === 49 || y === 49; }
// Kept network (roads.js ROADS + mineral trunk when the mineral gate is on + w8link). Exit tiles
// cannot take a site (live 18,49 → ERR_INVALID_TARGET). A container or rampart may share the tile;
// an existing construction site is left in place (do not remove it to pave).
function maintainRoads(room, tiles, dayCrit) {
  if (dayCrit || !tiles || !tiles.length || Game.time % 100) return;
  // Tower site still owns the queue (RCL5 tower-first). Day-crit spawn/tower is the dayCrit guard above.
  if (room.find(FIND_MY_CONSTRUCTION_SITES, { filter: s => s.structureType === STRUCTURE_TOWER }).length) return;
  let n = room.find(FIND_MY_CONSTRUCTION_SITES, { filter: s => s.structureType === STRUCTURE_ROAD }).length;
  if (n >= ROAD_BATCH) return;
  const seen = new Set();
  for (const [x, y] of tiles) {
    if (n >= ROAD_BATCH) return;
    const k = x * 50 + y; if (seen.has(k)) continue; seen.add(k);
    if (roadExit(x, y)) continue;
    const st = room.lookForAt(LOOK_STRUCTURES, x, y);
    if (st.some(s => s.structureType === STRUCTURE_ROAD)) continue;
    if (room.lookForAt(LOOK_CONSTRUCTION_SITES, x, y).length) continue;
    if (st.some(s => s.structureType !== STRUCTURE_CONTAINER && s.structureType !== STRUCTURE_RAMPART)) continue;
    if (room.createConstructionSite(x, y, STRUCTURE_ROAD) === OK) n++;
  }
}
// 2026-11-13 (Misaki): hub link is hubLinkPos() (32,33) only. 33,34 is the plain road between hub
// container 33,33 and tower 33,35. Drop a leftover link site there so builders cannot finish a second
// hub link. The built link is left for ops to destroy (rebuild is 5k). Until that structure is gone,
// do not site 32,33 — RCL7 has a spare link slot, and placing it early would leave two hub links.
// Rampart and road may share 32,33; any other structure blocks the site.
function dropRetiredHubLinkSite(room) {
  const p = L.RETIRED_HUB_LINK;
  if (!p || !room.find) return;
  for (const s of room.find(FIND_MY_CONSTRUCTION_SITES, { filter: s => s.structureType === STRUCTURE_LINK && s.pos && s.pos.x === p[0] && s.pos.y === p[1] }))
    if (typeof s.remove === 'function') s.remove();
}
function hubLinkSiteOk(room, x, y) {
  const p = L.RETIRED_HUB_LINK;
  if (p && room.lookForAt(LOOK_STRUCTURES, p[0], p[1]).some(s => s.structureType === STRUCTURE_LINK)) return false;
  if (p && room.lookForAt(LOOK_CONSTRUCTION_SITES, p[0], p[1]).some(s => s.structureType === STRUCTURE_LINK)) return false;
  return !room.lookForAt(LOOK_STRUCTURES, x, y).some(s =>
    s.structureType !== STRUCTURE_RAMPART && s.structureType !== STRUCTURE_ROAD && s.structureType !== STRUCTURE_LINK);
}
function layoutRun(room) {
  mineralSend(room); // every tick; dormant while RCL6_MINERALS false
  if (Game.time % 20) return;
  dayObs(room);
  if (room.controller.level >= 2) placeSeal(room);
  moveRun(room);
  if (moving() && Memory.ops.w8move.phase === 'build') return;
  if (!room.find(FIND_MY_SPAWNS).length) return;
  const rcl = room.controller.level, ok = Memory.ops && Memory.ops.w8layout === 'approved';
  if (rcl >= 3) { const [hx, hy] = C.HUB_CONT; if (!room.lookForAt(LOOK_STRUCTURES, hx, hy).some(s => s.structureType === STRUCTURE_CONTAINER) && !room.lookForAt(LOOK_CONSTRUCTION_SITES, hx, hy).length) room.createConstructionSite(hx, hy, STRUCTURE_CONTAINER); }
  // 14:57 (Misaki, was RCL8): temp-extension swap from RCL7 once hub spawn 32,32 stands and storage > 50k. One at a time, in TEMP_EXT
  // order, into the next unbuilt v3b ORDER.extension slot. Destroy only when: spawn energy full (spare), no extension site pending
  // (previous swap done), the replacement tile is clear and the site budget has room (this run's PRIO loop / the next places it).
  // Spawn2 is kept.
  if (ok && rcl >= 7) swapTemp(room);
  // 17:15 drop empty-slot rampart sites; 10-31 keep gate + spawn-slot + live KEY covers (tower 24,8 etc.)
  for (const s of room.find(FIND_MY_CONSTRUCTION_SITES, { filter: s => s.structureType === STRUCTURE_RAMPART && !keepRamp(room, s.pos.x, s.pos.y) })) s.remove();
  placeKeyRamps(room); // durable: any live KEY structure without a rampart gets a site (builders + soft raise to SOFT_RAMP)
  // 10-31 19:1x (Misaki RCL7 catch-up): while day-of still misses spawn2@33,30 or tower3@22,7, strip extension sites that
  // steal the 6-site budget and block tower re-queue, and never place new extensions. Live: 10 ext sites at rem0 sat with
  // tower@22,7 rem5000 for hours; sites>=6 early-return then could not re-place a missing tower.
  const dayMiss = rcl >= 7 ? dayofMiss(room) : { missSpawn: false, missTower: false, missExt: 0 };
  const dayCrit = !!(dayMiss.missSpawn || dayMiss.missTower);
  if (dayCrit) {
    for (const s of room.find(FIND_MY_CONSTRUCTION_SITES, { filter: s => s.structureType === STRUCTURE_EXTENSION })) s.remove();
  }
  dropRetiredHubLinkSite(room); // 33,34 link site is obsolete; do not let it hold a struct-site slot
  // Road sites are outside this budget. Counting them here let a decay re-site fill the 6 slots and
  // block the next spawn/tower/extension pass (10-31 tower re-queue). Labs still count: 6 of them used
  // to return before any road was placed (11-13 t84238893, 36 missing tiles).
  let structSites = room.find(FIND_MY_CONSTRUCTION_SITES, { filter: s => s.structureType !== STRUCTURE_RAMPART && s.structureType !== STRUCTURE_ROAD }).length;
  let roadSites = room.find(FIND_MY_CONSTRUCTION_SITES, { filter: s => s.structureType === STRUCTURE_ROAD }).length;
  // 03:05 west<->hub link road (missing from v3b plan): loaded 10C5M rhaulers sat 7-10 ticks on unroaded swamp 22,34 (fatigue 70)
  // between road 15,33 and strip road 24,35; queued ahead of the plan roads since every hub trip crosses it
  // 09:13 road audit: only the target network (roads.js: v3b spines + shared trunks + busy live roads) is placed
  // 10-20 03:4x strategy review (docs/PLAN_W47N8.md "RCL6 gate"): with RCL6_MINERALS off, terminal/extractor/mineral trunk stay
  // unplaced (no mineral miner / send code yet). 23:4x split: RCL6_LABS gates the 3 colony labs separately (lean KO uses home labs).
  // 10-29 20:4x (docs/PLAN_W47N8.md "RCL7 day-of"): RCL7 unlocks factory 35,30 (100k); with RCL7_INDUSTRY off it is not placed (same trap
  // as home plan.RCL7_INDUSTRY). RCL8 powerSpawn/nuker/observer stay gated with it. Day-of bill = spawn2 + tower3 + 10 ext + spur roads.
  const R8 = require('./roads'), minOk = !!C.RCL6_MINERALS, labsOk = !!C.RCL6_LABS, indOk = !!C.RCL7_INDUSTRY;
  const [mcx, mcy] = C.MINERAL_CONT || [37, 44];
  const baseCont = (L.ORDER.container || []).filter(([x, y]) => !(x === mcx && y === mcy));
  const cont = baseCont.concat(minOk ? [[mcx, mcy]] : []);
  // MINERAL tiles live in roads.MINERAL, not ROADS (w47n8_roads_v4 keeps them separate). Concat when minOk so trunk actually places.
  const baseRoads = R8.ROADS.filter(([x, y]) => !R8.MINERAL.some(([a, b]) => a === x && b === y));
  const roads = (rcl >= 6 && minOk ? baseRoads.concat(R8.MINERAL) : baseRoads).concat(require('../../layouts/w8link').W47N8);
  // 11-13: re-site decayed planned roads even when labs/factory/containers already hold the 6-site budget.
  // Cadence matches home maintain (every 100t, which is also a layout tick). Not while day-crit spawn/tower is open.
  const pave = () => { if (ok && rcl >= 3) maintainRoads(room, roads, dayCrit); };
  if (structSites >= 6 && !dayCrit) { pave(); return; }
  const O = ok ? Object.assign({}, L.ORDER, { container: cont, link: [C.CTL_LINK, C.SOURCES[0].link].concat(C.HUB_LINK ? L.ORDER.link : []), road: roads },
    minOk ? {} : { terminal: [], extractor: [] },
    labsOk ? {} : { lab: [] },
    indOk ? {} : { factory: [], powerSpawn: [], nuker: [], observer: [] }) : { extension: L.TEMP_EXT, container: L.ORDER.container };
  // 17:15: PRIO still has no rampart (empty-slot sites were the waste). 10-31: placeKeyRamps covers live KEY only (tower 24,8…).
  // Empty planned slots still dropped above; built KEY covers soft-raise to SOFT_RAMP via rampHold (~100k).
  // 17:5x strategy review: tower before everything except spawn, and nothing new is queued while a tower site stands. At RCL5 the
  // old order put 10 extensions (30k, ~2-3 h at W47N8's ~10-15 e/t build) ahead of tower 2 (5k); combat_sim F2/F3 (DEFENSE_W47N8.md)
  // says 2 towers alone beat the full BustJetter squad while 1 tower loses without defenders, so tower 2 is the defence step to rush.
  let towerSite = room.find(FIND_MY_CONSTRUCTION_SITES, { filter: s => s.structureType === STRUCTURE_TOWER }).length > 0;
  for (const t of PRIO) {
    // Hold extensions while a tower site stands (RCL5+) OR while RCL7 day-of still misses spawn2/tower3 structures.
    if (t === 'extension' && (towerSite || dayCrit)) return;
    if (t === 'road' && rcl < 3) continue;
    if (t === 'road' && dayCrit) continue; // day-of: keep site budget for spawn/tower only
    for (const [x, y] of (O[t] || [])) {
      if (t !== 'road' && structSites >= 6 && !(dayCrit && (t === 'spawn' || t === 'tower'))) { pave(); return; }
      if (t === 'road' && (structSites + roadSites) > 2) { pave(); return; } // trickle only while the queue is quiet; maintainRoads covers the rest
      if (t === 'road' && roadExit(x, y)) continue; // 18,49 and any other exit: createConstructionSite → ERR_INVALID_TARGET
      if (t === 'link' && L.ORDER.link && L.ORDER.link.some(([lx, ly]) => lx === x && ly === y) && !hubLinkSiteOk(room, x, y)) continue;
      if (room.lookForAt(LOOK_STRUCTURES, x, y).some(s => s.structureType === t)) continue;
      if (room.lookForAt(LOOK_CONSTRUCTION_SITES, x, y).length) continue;
      const r = room.createConstructionSite(x, y, t);
      if (r === OK) { if (t === 'road') roadSites++; else structSites++; if (t === 'tower') towerSite = true; } else if (r === ERR_RCL_NOT_ENOUGH) break; // next type
    }
  }
  pave();
}
// Drain-aware tower (Misaki 14:09 / 17:3x doctrine, docs/DEFENSE_W47N8.md): BustJetter TOUGH/MOVE tanks + healers sit at W47N8 y0-2,
// north of the seal walls, to burn tower energy. Target choice is ./defense towerPick: claimers anywhere, anything inside the seal
// (y>3), armed creeps hurting us; net damage > 0 only (tower dmg at range - reachable heal); healer > ranged > melee (lowest hp); one focus for
// all towers; non-urgent targets only from towers >= 400 energy; drain-pattern creeps (knocked down and healed back twice, or
// 1000 energy spent) are skipped unless urgent. Never safe mode (assessment only advises, Memory.ops.w8adv).
const PARTS = (c, t) => c.body.reduce((n, p) => n + (p.type === t && p.hits > 0 ? 1 : 0), 0);
const tdmg = r => (r <= 5 ? 600 : r >= 20 ? 150 : 600 - (r - 5) * 30);
// 17:20 (Misaki final rule): no new ramparts; built ones only offset decay. Memory.ops.w8hold[id] = hits first seen (ratchets down never,
// up never: a fresh rampart's hold is what it had). Tower tops up one rampart once it is HOLD_SLACK below its hold (300 hits/100t decay,
// ~0.03 e/t per rampart). Gone ramparts drop out of the map.
const HOLD_SLACK = 1000;
// 10-20 13:39 / 10-31: hold gate, KEY covers (spawn/storage/tower/terminal), and hub spawn slot. Empty-slot ramparts decay.
// placeKeyRamps (layoutRun) keeps live KEY structures covered; soft path raises them to SOFT_RAMP.
function rampNeeded(room, r) {
  if (!r.pos) return true;
  const { x, y } = r.pos;
  if (isGate(x, y) || (x === L.ORDER.spawn[0][0] && y === L.ORDER.spawn[0][1])) return true;
  if (indAt(room, x, y)) return true; // lab/factory cover: held at IND_RAMP, not left to decay
  return !room.lookForAt || room.lookForAt(LOOK_STRUCTURES, x, y).some(s => KEY.includes(s.structureType));
}
function rampHold(room) {
  const rs = room.find(FIND_MY_STRUCTURES, { filter: s => s.structureType === STRUCTURE_RAMPART }).filter(r => rampNeeded(room, r));
  const o = (Memory.ops = Memory.ops || {}), h = (o.w8hold = o.w8hold || {}), live = {};
  for (const r of rs) live[r.id] = h[r.id] === undefined ? r.hits : h[r.id];
  o.w8hold = live;
  // Observability (14:4x): soft-ramp mins for patrol/strategy — spawn/tower/storage/gate hits + staging target.
  const soft = (o.w8soft = { t: Game.time, tgt: C.SOFT_RAMP || 0 });
  for (const r of rs) {
    if (!r.pos) continue;
    const { x, y } = r.pos;
    if (isGate(x, y)) soft.gate = r.hits;
    else if (x === L.ORDER.spawn[0][0] && y === L.ORDER.spawn[0][1]) soft.spawn = r.hits;
    else if (room.lookForAt) {
      const st = room.lookForAt(LOOK_STRUCTURES, x, y);
      if (st.some(s => s.structureType === STRUCTURE_TOWER)) soft.tower = Math.min(soft.tower == null ? r.hits : soft.tower, r.hits);
      if (st.some(s => s.structureType === STRUCTURE_STORAGE)) soft.stor = r.hits;
    }
  }
  // 13:30 gate ramp-up; 10-20 16:5x patrol: also the spawn-slot rampart (L.ORDER.spawn[0]). It is built at 1 hit and its hold was 1,
  // so it decayed away every ~100 t (seen t83761858-862) and the relocated spawn would have stood uncovered.
  // 14:4x: GATE_TOWER=100k (=SOFT_RAMP) — spawn/gate critical floor, always (defense).
  const slot = (x, y) => x === L.ORDER.spawn[0][0] && y === L.ORDER.spawn[0][1];
  const g = rs.find(r => r.pos && (isGate(r.pos.x, r.pos.y) || slot(r.pos.x, r.pos.y)) && r.hits < (C.GATE_TOWER || 0)); if (g) return g;
  // 14:4x soft staging; 17:4x: SOFT_MIN=0 + peacetime = !TH.localOn() (not TH.on — w8threatN neighbor staging
  // was pinning soft at ~49k while spawn already hit GATE_TOWER). Hold map never ratchets up. Cost ~1k e remaining.
  const softMin = C.SOFT_MIN || 0;
  const storE = room.storage && room.storage.store ? (room.storage.store[RESOURCE_ENERGY] || 0) : 0;
  // 11-02 (Misaki t375u): Memory.defense.w8key lifts KEY covers above SOFT_RAMP while storage >= w8keyMinE (towers within KEY_REP_R only)
  const kt = TH.keyTarget(), softT = kt > (C.SOFT_RAMP || 0) && storE >= TH.keyMinE() ? kt : (C.SOFT_RAMP || 0);
  soft.tgt = softT; soft.storE = storE;
  soft.sealMinE = TH.sealMinE(); soft.sealCap = TH.sealCap();
  soft.sealRaise = (TH.sealDeepOk(storE) && TH.sealCap() > TH.STAGE3) ? 1 : 0; // 02:4x: soft-gate (softCap2 + sticky park)
  soft.sealPark = TH.sealParked() ? 1 : 0;
  const localThreat = TH.localOn();
  soft.why = softT <= 0 ? 'off' : localThreat ? 'threat' : (storE < softMin ? 'stor' : 'ok');
  // Lab/factory covers share the soft pass only up to IND_RAMP. w8key (and the RCL7 1M seal) must not
  // pull them further; a fresh 1-hit cover also has to be claimed here or the 300/100t decay deletes it.
  const softGoal = r => (r.pos && indAt(room, r.pos.x, r.pos.y)) ? Math.min(softT, IND_RAMP) : softT;
  if (softT > 0 && storE >= softMin && !localThreat) {
    const low = rs.filter(r => r.hits < softGoal(r) && r.pos && !isGate(r.pos.x, r.pos.y))
      .sort((a, b) => a.hits - b.hits)[0];
    if (low) return low;
  }
  const decayed = rs.find(r => r.hits < live[r.id] - HOLD_SLACK);
  if (decayed) return decayed;
  // Above SOFT_RAMP (or while threat skips the soft pass): finish the 300k floor, then stop.
  return rs.filter(r => r.pos && indAt(room, r.pos.x, r.pos.y) && r.hits < IND_RAMP).sort((a, b) => a.hits - b.hits)[0] || null;
}
// 17:20 RCL5 links (parent-approved plan): source A link 26,12 -> ctl link 13,25 (3% loss) replaces ~25-tile hauling of source A.
function linkAt(p) { const r = Game.rooms[C.ROOM]; return p && r && r.lookForAt(LOOK_STRUCTURES, p[0], p[1]).find(s => s.structureType === STRUCTURE_LINK); }
function linkRun() {
  // 20:5x patrol: require free>=400 deadlocked when ctl sat ~486 (free 314) — src link stayed full, A harvest looked soft.
  // Transfer any time sender has energy and ctl has free space (API caps to free). Keep >=50 src floor to avoid tiny dribbles.
  // 23:4x strategy: also hub→ctl when hub link exists (dormant until HUB_LINK built). Home managers/links.js pattern:
  // queen fills hub; hub pushes when ctl < CTL_LOW. Overmind UpgradeSite requests battery when <50%/link <200.
  const a = linkAt(C.SOURCES[0].link), k = linkAt(C.CTL_LINK);
  // Hub sender is 32,33 only. A link left at retired 33,34 does not send (and the filler does not fill it).
  const [hx, hy] = L.hubLinkPos();
  const h = linkAt([hx, hy]);
  const CTL_LOW = 400, HUB_SEND = 200; // home uses SEND=400; allow 200 so intermittent battery recovers sooner
  const cmd = require('../../utils/cmd'), cmdOn = cmd.armed();
  if (a && k && !a.cooldown && !(cmdOn && cmd.consumeLink(a))) {
    const have = a.store[RESOURCE_ENERGY] || 0, free = k.store.getFreeCapacity(RESOURCE_ENERGY) || 0;
    if (have >= 50 && free > 0) a.transferEnergy(k, Math.min(have, free));
  }
  // Hub→ctl independent of A (own cooldown). No-op while HUB_LINK=false (no structure). Prefer A first above.
  if (h && k && h !== a && !h.cooldown && !(cmdOn && cmd.consumeLink(h))) {
    const have = h.store[RESOURCE_ENERGY] || 0, ke = k.store[RESOURCE_ENERGY] || 0;
    const free = k.store.getFreeCapacity(RESOURCE_ENERGY) || 0;
    if (ke < CTL_LOW && have >= HUB_SEND && free > 0) h.transferEnergy(k, Math.min(have, free));
  }
}
const D = require('./defense'), F = require('../../utils/focus');
const KEY_REP_R = 10;
const SEAL_FIGHT = { x: 27, y: 3 }; // centre of the east seal: where a north squad has to break in
// 10-20 23:4x strategy review: the west seal (x 8-11) is the thin side, towers r32 + r13-16 (~460 dps vs ~750 east): the 21:45 W48N9
// group (28 HEAL) is held there by towers alone, ~36 HEAL is not. Border pre-assessment scores the segment nearest the announced group.
const SEAL_WEST = { x: 10, y: 3 }, sealAt = x => (typeof x === 'number' && x < 18 ? SEAL_WEST : SEAL_FIGHT);
// armed hostiles within reach (RA 3, ATTACK/WORK 1) of our creeps, our structures or the seal walls
function hurtingSet(room, hs) {
  const s = new Set(); hs = hs.filter(D.armed); if (!hs.length) return s; // drain tanks only: skip the structure scan (CPU)
  const ours = room.find(FIND_MY_CREEPS).concat(room.find(FIND_STRUCTURES, { filter: x => x.my || x.structureType === STRUCTURE_WALL }));
  for (const h of hs) { const r = PARTS(h, RANGED_ATTACK) ? 3 : PARTS(h, ATTACK) + PARTS(h, WORK) ? 1 : 0;
    if (r && ours.some(o => Math.max(Math.abs(o.pos.x - h.pos.x), Math.abs(o.pos.y - h.pos.y)) <= r)) s.add(h.id); }
  return s;
}
// every 5 ticks while an armed force is in W47N8 or announced at the W47N9 border: can towers / towers + 2 defenders win?
function assessRun(room, towers, hs) {
  const m = room.memory, o = (Memory.ops = Memory.ops || {});
  const inRoom = hs.filter(h => PARTS(h, ATTACK) + PARTS(h, RANGED_ATTACK) > 0), north = o.w8invN > 0 && Game.time - o.w8invN < 60; // 18:06: threat cleared = no armed hostile in W47N8 and no border signal for 60 t (~4 north_watch scans) -> roster dropped, no spawns/replacements (was 300: kept 5 defenders spawning after withdrawal)
  if (!inRoom.length && !north) { if (m.w8assess) delete m.w8assess; if (o.w8roster) delete o.w8roster; return; }
  if (m.w8assess && Game.time - m.w8assess.t < 10) return; // up to 5x5 sims (<=600 t each): cached 10 ticks
  let force, at;
  if (inRoom.length) { force = hs.filter(h => D.armed(h) || PARTS(h, HEAL)); at = inRoom.reduce((a, h) => (h.pos.y > a.pos.y ? h : a)).pos; }
  else if (Array.isArray(o.w8invNb) && o.w8invNb.length) { force = o.w8invNb.map(D.fromCounts); at = sealAt(o.w8invNx); }
  else force = [D.fromCounts({ ranged_attack: 8, move: 8 }), D.fromCounts({ ranged_attack: 6, move: 6 })], at = sealAt(o.w8invNx); // no body data: assume the 17:34 pair
  const inside = inRoom.some(h => h.pos.y > D.SEAL_Y);
  const tr = towers.map(t => Math.max(Math.abs(t.pos.x - at.x), Math.abs(t.pos.y - at.y)));
  // 17:34 joint planner (defense.plan): one place decides the W46N8 + W47N8 roster; home only if home itself is not threatened
  const hr = Game.rooms[HOME], homeOk = !!hr && !require('../../managers/home').active(hr);
  const r = D.plan({ force, towerR: tr, inside, homeOk, homeCap: hr ? hr.energyCapacityAvailable : 0, w8Cap: room.energyCapacityAvailable || 300,
    towerE: Math.min(...towers.map(t => t.store[RESOURCE_ENERGY])), atkBoost: o.w8uh > 0 ? 'UH' : '', meleeUptime: inside ? 1 : 0 }); // 17:58: UH stock north -> boosted melee; melee only reaches us inside the seal
  o.w8roster = { t: Game.time, home: r.home, w8: r.w8, w8m: r.w8m | 0, hl: r.hl || '', why: r.why };
  m.w8assess = { t: Game.time, spawn: r.w8 > 0, why: r.why, at: [at.x, at.y] };
  if (r.advise) o.w8adv = { t: Game.time, advise: r.advise, why: r.why, n: force.length }; // safe mode is Misaki's call (alerts relay it)
}
function towerRun(room) {
  TH.mark(room); TH.mark(Game.rooms[C.REMOTE.room]); linkRun();
  const towers = room.find(FIND_MY_STRUCTURES, { filter: s => s.structureType === STRUCTURE_TOWER });
  if (!towers.length) return;
  const h = room.find(FIND_HOSTILE_CREEPS).filter(x => !x.my);
  assessRun(room, towers, h);
  // 17:48 (Misaki): heal only creeps < 60% (no-HEAL creeps first, lowest %); a heal candidate beats attacking this tick
  const peace = !F.hostileArmed(h); // 18:00 (Misaki): no armed/healing hostile -> heal any damaged creep to full (floor 200 e)
  const hurt = F.healPick(room.find(FIND_MY_CREEPS), peace);
  let p = null;
  if (h.length) {
    const m = room.memory, hurting = hurtingSet(room, h);
    const banned = F.track(m.drain8 || (m.drain8 = {}), h, Game.time, m.threat8 && m.threat8.id, m.threat8 && m.threat8.e);
    p = D.towerPick(towers.map(t => ({ pos: t.pos, energy: t.store[RESOURCE_ENERGY], t })), h, { prev: m.threat8 && m.threat8.id, hurting, banned,
      allies: room.find(FIND_MY_CREEPS).map(c => ({ pos: c.pos, ra: (c.body || []).filter(b => b.type === RANGED_ATTACK && b.hits > 0).length })).filter(a => a.ra) });
  } else if (room.memory.drain8 && Game.time % 100 === 0) F.track(room.memory.drain8, [], Game.time);
  const inBaseThreat = !!p && p.h.pos.y > D.SEAL_Y && D.armed(p.h);
  room.memory.threat8 = p ? { t: Game.time, id: p.h.id, inBase: inBaseThreat, e: p.shooters.length * 10 } : undefined;
  const fire = new Set(p ? p.shooters.map(s => s.t) : []);
  const cmd = require('../../utils/cmd'), cmdOn = cmd.armed();
  for (const t of towers) {
    if (cmdOn && cmd.consumeTower(t)) continue; // this tower obeys Memory.cmd; the rest keep threat8 / repair
    if (hurt && (!peace || t.store[RESOURCE_ENERGY] >= 200)) t.heal(hurt);
    else if (fire.has(t)) t.attack(p.h);
    else if (t.store[RESOURCE_ENERGY] > 600) { // 17:20 hold/decay; 14:4x/17:4x soft staging to SOFT_RAMP (see rampHold)
      const r = rampHold(room);
      // 11-02: above GATE_TOWER (the KEY raise / high holds) only towers within KEY_REP_R repair: a r22 tower gets 200 hits per
      // 10 energy vs 800 at r<=5, so the far towers just burned energy. Every KEY/gate rampart has a tower within 10.
      if (r && (r.hits < (C.GATE_TOWER || 0) || !t.pos || !t.pos.getRangeTo || !r.pos || t.pos.getRangeTo(r) <= KEY_REP_R)) t.repair(r);
    }
  }
}
// 17:34 joint defence, home side: W46N8 spawn asks this. One RA+MOVE defender (max that fits home cap, no HEAL) for W47N8 when the
// planner wants it, home has no player combat creeps, and fewer home-sent defenders (memory.jd W46N8; not 'src', which main.js strips from creeps without v2) are alive/spawning.
// Overrides the home storage floor (defence). The creep runs the w8defender role (home: W47N8) and idles by the north wall until its TTL ends (18:04: no recycle).
const HOME = 'W46N8';
function homeWant(room) {
  // Wartime assault: do not bank a 5k joint w8defender ahead of raid9 melee (Misaki 2026-11-04 alternate spawn).
  try { if (require('../../roles/raid9').pauseCivilians()) return null; } catch (e) { /* ok */ }
  const ro = Memory.ops && Memory.ops.w8roster;
  if (room.name !== HOME || !ro || !ro.home || Game.time - ro.t > 20) return null;
  if (require('../../managers/home').active(room)) return null;
  const sent = _.filter(Game.creeps, c => c.memory.role === 'w8defender' && c.memory.jd === HOME).length;
  const mem = { home: C.ROOM, jd: HOME, born: Game.time, v2: 1 };
  if (sent < ro.home) return { role: 'w8defender', body: require('./defense').raBody(room.energyCapacityAvailable, 25), mem };
  // 18:04: roster >= 4 -> one dedicated healer from home at max cap (HEAL+MOVE)
  if (ro.hl === 'home' && !_.some(Game.creeps, c => c.memory.role === 'w8healer')) return { role: 'w8healer', body: require('./defense').healBody(room.energyCapacityAvailable, 25), mem };
  return null;
}
// self-sufficient = own spawn + a miner + a hauler alive (conquest.js stops sending cqworkers/cqhaulers)
function selfSufficient() {
  // 10-20 19:5x (Misaki: the spawn move is W47N8-only, no home support): our own planned move (old spawn destroyed by
  // moveRun, phase 'build') is not a lost room -> home must not send cqminers/cqworkers (it sent 2+5 = 9.5k e on 10-20)
  const mv = Memory.ops && Memory.ops.w8move; if (mv && mv.phase === 'build' && mv.t0) return true;
  const r = Game.rooms[C.ROOM]; if (!r || !r.find(FIND_MY_SPAWNS).length) return false;
  return mine().some(c => c.memory.role === 'w8miner'); // Spawn2 + its own miner -> home stops cq pioneers/haulers (guard stays)
}
module.exports = { sealAt, banking, BANK_HOLD, LEAN_STOR, LEAN_ARM, LEAN_SOFT, LEAN_SOFT_ARM, UP_STICKY, UP_STICKY_T, UP_REARM, IDLE_EVERY, FEED_MIN, threatSoft, softEnergyCap, softCap2, upBankTick, upgTarget, ctlBattery, hubLinkLive, leanBank, leanMinBuild, leanUpKeep, energyBank, dayofMiss, moveRun, moveReady, rampNeeded, homeWant, linkAt, linkRun, rampHold, dayObs, mineralSend, swapTemp, extBatch, energyOrder, ROOM: C.ROOM, spawnRun, layoutRun, towerRun, selfSufficient, bodyFor, rmLead8 };
