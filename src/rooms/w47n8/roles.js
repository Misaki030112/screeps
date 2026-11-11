// W47N8 roles (w8miner / w8hauler / w8upgrader / w8builder). Simple, room-local; no safe mode anywhere.
const C = require('./config');
const CMV = require('../../utils/combatmove');
// 11-11 patrol (w8builder84200485): vanilla moveTo searched with creeps as walls; with creeps on the 1-wide x=38 / 31,2x trunks the
// search to container 37,44 went INCOMPLETE (3 steps to the south-edge dead end 33,48 instead of the real 84) and the builder shuttled
// 31,48 <-> 17,33 / 8,23 for ~300 t carrying 66 energy. In W47N8 the search ignores creeps; one creep-aware search only when stuck
// (utils/combatmove, same rule as the w8 combat roles since #35).
const go = (c, x, y, r = 1) => (c.room.name === C.ROOM ? CMV.to(c, x, y, r, undefined, 10)
  : c.moveTo(new RoomPosition(x, y, C.ROOM), { range: r, reusePath: 10, maxRooms: 1 }));
const E = 'energy';
const FM = require('./fillmeter');
const F = require('./fill');
const isFill = s => s && (s.structureType === STRUCTURE_EXTENSION || s.structureType === STRUCTURE_SPAWN);
const fillXfer = (c, s) => { const a = Math.min(c.store[E], s.store.getFreeCapacity(E)); if (c.transfer(s, E) === 0) FM.xfer(c, a); };
const isHub = s => s.pos.x === C.HUB_CONT[0] && s.pos.y === C.HUB_CONT[1];
// 10-20 09:4x (Misaki "W47N7 的搬运不走 road"): native cross-room moveTo treats creeps as walls on every repath, so 4 rhaulers on the
// 1-wide W47N7 road routed around each other onto plain (15C1W8M loaded = half speed off road; live samples 24,15 26,25 25,21 30,32).
// W47N7 legs now use move.to (road matrix, creeps ignored, swap/shove when blocked) via the fixed N exit 18,0 <-> W47N8 18,49.
const MV = require('../../utils/move');
const EX7 = [18, 0], EX8 = [18, 49], ND = { noDetour: true };
function onBorder(c) { return c.pos.x === 0 || c.pos.x === 49 || c.pos.y === 0 || c.pos.y === 49; }
function rmove(c, room, x, y, r) {
  const R7 = C.REMOTE.room;
  if (c.room.name === room) {
    if (onBorder(c)) { delete c.memory._m; return c.move(c.pos.y === 0 ? BOTTOM : c.pos.y === 49 ? TOP : c.pos.x === 0 ? RIGHT : LEFT); }
    return MV.to(c, x, y, r, ND);
  }
  const ex = c.room.name === R7 && room === C.ROOM ? EX7 : c.room.name === C.ROOM && room === R7 ? EX8 : null;
  if (!ex) return c.moveTo(new RoomPosition(x, y, room), { range: r, reusePath: 20 });
  if (c.pos.x === ex[0] && c.pos.y === ex[1]) { delete c.memory._m; return c.move(ex[1] === 0 ? TOP : BOTTOM); }
  return MV.to(c, ex[0], ex[1], 0, ND);
}
// 10-21 04:0x (2room patrol): home-sent joint defender w8defender83770598 took ~335 t (was ~35 t) from W46N8 spawn to W47N8:
// native cross-room moveTo (creeps = walls, reusePath 20) flipped routes, 46,17 <-> 16,29, then ~175 t outside our tracked rooms
// via the W45N8 side. Same fix as the W47N7 leg: move.to to the fixed W46N8 west exit 0,23 (enters W47N8 at 49,23).
const EXH = [0, 23], HOME_R = 'W46N8';
function home(c) {
  if (c.room.name === C.ROOM) return true;
  if (c.room.name === C.REMOTE.room) rmove(c, C.ROOM, C.SPAWN[0], C.SPAWN[1], 1);
  else if (c.room.name === HOME_R) MV.to(c, EXH[0], EXH[1], 0, ND);
  else c.moveTo(new RoomPosition(C.SPAWN[0], C.SPAWN[1], C.ROOM), { reusePath: 20 });
  return false;
}
function getEnergy(c) {
  const drop = c.pos.findClosestByRange(FIND_DROPPED_RESOURCES, { filter: r => r.resourceType === E && r.amount >= 50 });
  const cont = c.pos.findClosestByRange(FIND_STRUCTURES, { filter: s => s.structureType === STRUCTURE_CONTAINER && s.store[E] >= 100
    && !((s.pos.x === C.CTL_CONT[0] && s.pos.y === C.CTL_CONT[1] || isHub(s)) && c.memory.role === 'w8hauler') });
  // 13:00 storage 35,32 finished (2026-10-19): haulers only top it up once ctl/hub conts are full, so builders/upgraders may draw
  // from it (>= 300) instead of letting the surplus sit while they walk to source containers
  // 17:4x: with a w8filler alive the storage first holds its buffer (one hub refill + 200); spenders take only what is above it + 300
  // 10-31 19:1x: during RCL7 day-of (miss spawn2/tower3) builders may draw at >=300 even below the filler buffer — ea was full
  // while stor~1k and 4 builders walked west every load; spawn/tower sites crawled ~1 e/t for hours.
  let floor = F.alive(c.room) ? F.reserve(c.room) + 300 : 300;
  // Use Memory.ops.w8day (dayObs) — avoid require('./index') cycle
  const w8d = Memory.ops && Memory.ops.w8day;
  if (c.memory.role === 'w8builder' && w8d && (w8d.missSpawn || w8d.missTower)) floor = 300;
  const st = c.room.storage && c.memory.role !== 'w8hauler' && c.room.storage.store[E] >= floor ? c.room.storage : null;
  const t = [drop, cont, st].filter(Boolean).sort((a, b) => c.pos.getRangeTo(a) - c.pos.getRangeTo(b))[0];
  if (t) { if (!c.pos.isNearTo(t)) go(c, t.pos.x, t.pos.y); else if (t.amount !== undefined) c.pickup(t); else c.withdraw(t, E); return true; }
  const src = c.pos.findClosestByRange(FIND_SOURCES_ACTIVE);
  if (src && c.getActiveBodyparts(WORK)) { if (!c.pos.isNearTo(src)) go(c, src.pos.x, src.pos.y); else c.harvest(src); return true; }
  return false;
}
// hauler pickup (18:05): sticky target scored by usable amount / (range+10), minus what other w8haulers already claimed,
// so haulers also clear the far south source (11,43: 2k energy piled while all 3 w8haulers circled the north source).
// 03:40 hub cont sat full 2000 with no sites near it (b8b6b31 stopped refilling it, but nothing ever drained it) while the ctl cont was
// at 737 and the upgrader surplus rule counted that hub energy: w8haulers may pick from the hub (half score) only while no hub sites
// need it and the ctl cont has >= 400 free, so a hub load always has somewhere else to go (sink() falls back to ctl first)
function hubSpare(room) {
  if (hubSites(room)) return false;
  if (F.alive(room) && F.stock(room) < F.reserve(room)) return false; // 17:4x: hub container is the filler's buffer
  const k = ctlCont(); return !!k && k.store.getFreeCapacity(E) >= 400;
}
// 19:5x strategy review (RCL5 tower 24,8, Misaki 18:06 "ample energy supply"): tower 2 sits 2 tiles from source A's container 26,11
// but ~23 road tiles from storage, and once link 26,12 ships source A to the controller nothing stocks 26,11 any more. While a tower
// within 4 of the source-A stand is below NORTH_FEED the miner skips the link, so harvest overflows into 26,11 (~10 e/t = that tower
// firing every tick), haulers score 26,11 x3 and fillTarget's nearest pick carries it the 2 tiles. Above the line source A goes back to
// the ctl link. Dormant until tower 24,8 + link 26,12 exist (RCL5). The hub filler no longer walks there (fill.js TOWER_R).
const NORTH_FEED = 600;
let nfT = -1, nfV = null;
function northFeed(room) {
  if (nfT === Game.time) return nfV; nfT = Game.time;
  const [x, y] = C.SOURCES[0].stand;
  return (nfV = (room && room.find(FIND_MY_STRUCTURES, { filter: s => s.structureType === STRUCTURE_TOWER && s.pos.inRangeTo(x, y, 4) && s.store[E] < NORTH_FEED })[0]) || null);
}
function haulPick(c) {
  const room = Game.rooms[C.ROOM], free = c.store.getFreeCapacity(), amt = o => (o.amount !== undefined ? o.amount : o.store[E]);
  let t = c.memory.pt && Game.getObjectById(c.memory.pt);
  if (!t || amt(t) < 50) {
    const claimed = {};
    for (const h of room.find(FIND_MY_CREEPS, { filter: x => x.memory.role === 'w8hauler' && x.id !== c.id && x.memory.pt && !x.memory.w }))
      claimed[h.memory.pt] = (claimed[h.memory.pt] || 0) + h.store.getFreeCapacity();
    const cands = room.find(FIND_DROPPED_RESOURCES, { filter: r => r.resourceType === E && r.amount >= 50 }).concat(room.find(FIND_TOMBSTONES, { filter: t => t.store[E] >= 50 }), room.find(FIND_RUINS, { filter: t => t.store[E] >= 50 }), room.find(FIND_STRUCTURES,
      { filter: s => s.structureType === STRUCTURE_CONTAINER && s.store[E] >= 100 && !(s.pos.x === C.CTL_CONT[0] && s.pos.y === C.CTL_CONT[1]) && (!isHub(s) || hubSpare(room)) }));
    let bs = 0; t = null;
    // 04:05: ground piles score x2 (they decay 1+/tick): 241 sat on road 29,35 losing 1/t while haulers chose 780-1110 source conts
    // 18:20: score by the whole unclaimed pile, not min(free, pile): capped by a 150-250 free store every pile scored the same and
    // the nearest (north, drained by 10 workers) always won, so 10,43 grew 1574->2011 and decayed ~2 e/t
    const nf = northFeed(room), A = C.SOURCES[0].stand, isA = o => o.pos.x === A[0] && o.pos.y === A[1];
    for (const o of cands) { const left = amt(o) - (claimed[o.id] || 0), sc = (o.structureType ? (isHub(o) ? 0.5 : nf && isA(o) ? 3 : 1) : 2) * left / (c.pos.getRangeTo(o) + 10); if (Math.min(free, left) >= 50 && sc > bs) { bs = sc; t = o; } }
    c.memory.pt = t ? t.id : undefined;
  }
  // Wartime: if no source/drop pile, drain storage into empty extensions (Misaki 2026-11-04 unlimited war supply).
  if (!t) {
    let war = false; try { war = require('../../roles/raid9').pauseCivilians(); } catch (e) { war = false; }
    if (war && room.storage && (room.storage.store[E] || 0) > 0 && room.energyAvailable < room.energyCapacityAvailable) {
      t = room.storage; c.memory.pt = t.id;
    }
  }
  if (!t) return false;
  // Misaki rule: deliver once over half full rather than walking to another pile
  if (!c.pos.isNearTo(t) && c.store[E] * 2 >= c.store.getCapacity()) { delete c.memory.pt; return false; }
  if (!c.pos.isNearTo(t)) go(c, t.pos.x, t.pos.y); else { if (t.amount !== undefined) c.pickup(t); else c.withdraw(t, E); delete c.memory.pt; }
  return true;
}
function toggle(c) {
  if (c.memory.w && c.store[E] === 0) { c.memory.w = false; delete c.memory.sk; delete c.memory.ft; delete c.memory.fm; }
  if (!c.memory.w && c.store.getFreeCapacity() === 0) c.memory.w = true;
}
const ctlCont = () => Game.rooms[C.ROOM].lookForAt(LOOK_STRUCTURES, C.CTL_CONT[0], C.CTL_CONT[1]).find(s => s.structureType === STRUCTURE_CONTAINER);
const hubCont = () => Game.rooms[C.ROOM].lookForAt(LOOK_STRUCTURES, C.HUB_CONT[0], C.HUB_CONT[1]).find(s => s.structureType === STRUCTURE_CONTAINER);
// 22:50 hub feed: until the hub container (a 5000-energy site itself) stands, haulers hand energy straight to builders working
// the hub sites (builders were still walking ~25 tiles per 100 energy; ext 31,36 gained 150 in 55 ticks). Cached per tick.
let feedT = -1, feedOn = false;
function hubFeed(room) {
  if (feedT === Game.time) return feedOn; feedT = Game.time;
  const [hx, hy] = C.HUB_CONT, hub = new RoomPosition(hx, hy, C.ROOM);
  feedOn = !hubCont() && room.find(FIND_MY_CONSTRUCTION_SITES, { filter: s => s.structureType !== STRUCTURE_WALL && s.pos.inRangeTo(hub, 5) }).length > 0;
  return feedOn;
}
const nearHub = (c, r) => c.pos.inRangeTo(C.HUB_CONT[0], C.HUB_CONT[1], r);
const hubSites = room => room.find(FIND_MY_CONSTRUCTION_SITES, { filter: s => s.structureType !== STRUCTURE_WALL && s.pos.inRangeTo(C.HUB_CONT[0], C.HUB_CONT[1], 5) }).length > 0;
// container sink after spawn/extensions/tower: while hub sites (non-wall) exist, the emptier of hub/ctl container; else ctl first
// sticky per load (memory.sk, cleared when empty) so a hauler never flips between the two mid-walk
function sink(room, c) {
  const free = s => (s && s.store.getFreeCapacity(E) > 0 ? s : null);
  // 02:3x (2room-eval) the filler buffer counts loads already committed to storage, and a storage commitment ends once the buffer is
  // met: t83749490-547 four haulers chose storage at 648 < 950, kept walking there by stickiness (storage 648 -> 2752) while the ctl
  // cont sat at 0 and 40 WORK upgraded nothing for 57+ ticks (same at t83749050-100)
  const inbound = () => room.find(FIND_MY_CREEPS, { filter: o => o.id !== c.id && o.memory.sk === room.storage.id }).reduce((a, o) => a + o.store[E], 0);
  const bufLow = () => room.storage && F.alive(room) && F.stock(room) + inbound() < F.reserve(room);
  let was = free(c.memory.sk && Game.getObjectById(c.memory.sk));
  // 08:4x/20:4x: keep sticky storage while rebuild/soft-band (stor <LEAN_SOFT + ctl≥1200) even if filler buffer is met.
  // 20:4x extends below LEAN_ARM — post-gate soft-cap alone never parked energy while ctl had free capacity.
  // 08:4x 2026-11-02: park through LEAN_SOFT (25k), not just LEAN_STOR (20k). HMAX=3 overflow stopped at 20k while
  // soft-cap held nUp≤2 until 25k → WORK-bound deadlock (ctl/hub full, stor flat ~20k, upg~55% ideal).
  // 20:4x 11-03 strategy: soft-band is STRICT se<LEAN_SOFT — do NOT follow softE hysteresis.
  // softE (clear@25k / re-arm@22k) only gates softCap2/nUp. Coupling park to softE left [ARM,SOFT)
  // after a clear with nUp3 + park OFF → stor bled 25k→22k (seal correctly parked via softThin).
  // Overmind keeps logistics filling storageBuffer while upgrade battery is saturated; we park when
  // ctl≥1200 and stor still under the soft floor.
  const softFloor = (se) => (se || 0) < 25000; // LEAN_SOFT strict (nUp hysteresis is index softE only)
  const holdBand = () => {
    // Wartime: never soft-band park (Misaki 2026-11-04 drain storage→ext).
    try { if (require('../../roles/raid9').pauseCivilians()) return false; } catch (e) { /* ok */ }
    if (!room.storage) return false;
    const se = room.storage.store[E] || 0;
    const ctlS = ctlCont();
    const ctlE = ctlS ? (ctlS.store[E] || 0) : 0;
    return softFloor(se) && ctlE >= 1200;
  };
  if (was && room.storage && was.id === room.storage.id && !bufLow() && !holdBand()) was = null;
  // 11:4x 11-04 strategy: soft-band must PREEMPT sticky ctl/hub. Post-clear (stor just dipped under
  // LEAN_SOFT) haulers still carried sk=ctl from the ≥25k feed window; line above only releases
  // sticky STORAGE when holdBand drops — never breaks sticky ctl/hub when holdBand rises. Live
  // 11:31 clear@25.1k → 11:32 stor23.6k ctl1920 (holdBand true) still bled →21k because sk stuck
  // on ctl. Overmind logistics retargets to storageBuffer whenever under buffer; TooAngel parks
  // upgrade when thin — we keep nUp hysteresis and only retarget the sink.
  if (was && room.storage && was.id !== room.storage.id && holdBand() && free(room.storage)) was = null;
  if (was) return was;
  // 17:4x filler buffer: while a w8filler lives, storage below one hub refill (+200) comes before the ctl/hub containers
  if (room.storage && free(room.storage) && bufLow()) { c.memory.sk = room.storage.id; return room.storage; }
  // 08:4x/20:4x/20:4x-11-03 soft-band storage park — STRICT se<LEAN_SOFT and ctl ≥1200:
  // park hauler surplus so cushion can climb/hold the soft floor (25k). softE hysteresis stays on
  // softCap2/nUp only — park must still refill storage in the post-clear [ARM,SOFT) band.
  // Threat softCap (TH.localOn) does NOT force park here (predicate is energy floor, not softE).
  // Overmind keeps logistics topping storageBuffer while upgrade battery is saturated.
  // Wartime (pauseCivilians): never soft-park into storage — keep surplus on the fill path (Misaki 2026-11-04).
  let warRefill = false; try { warRefill = require('../../roles/raid9').pauseCivilians(); } catch (e) { warRefill = false; }
  if (!warRefill && room.storage && free(room.storage)) {
    const se = room.storage.store[E] || 0;
    const ctlS = ctlCont();
    const ctlE = ctlS ? (ctlS.store[E] || 0) : 0;
    if (softFloor(se) && ctlE >= 1200) { c.memory.sk = room.storage.id; return room.storage; }
  }
  const ctl = free(ctlCont()), hub = free(hubCont());
  // 03:20 hub only while sites near the hub need it: any road site anywhere sent rhaulers to the hub (864 -> 2000 full in ~290t)
  // while the ctl cont fell 1024 -> 652 and the upgraders starved
  const t = hub && hubSites(room) && (!ctl || hub.store[E] < ctl.store[E]) ? hub : ctl || hub;
  c.memory.sk = t ? t.id : undefined; return t;
}
// 02:45 fill target sticky per trip (memory.ft) and one creep per extension: with a fresh closest-free pick every tick, Spawn2
// draining the TEMP_EXT ring by the spawn turned loaded w8hauler/w8rhauler around mid-walk to the hub strips (22,11 -> 16,10).
const lastE = s => (s.structureType === STRUCTURE_SPAWN && s.pos.x === C.SPAWN[0] && s.pos.y === C.SPAWN[1]) || (s.structureType === STRUCTURE_EXTENSION && LAYT.some(([x, y]) => s.pos.x === x && s.pos.y === y));
const LAYT = require('./layout').TEMP_EXT;
function fillTarget(c, tower, rng = 99) {
  const t0 = c.memory.ft && Game.getObjectById(c.memory.ft);
  if (t0 && t0.store && t0.store.getFreeCapacity(E) > 0) return t0;
  const taken = new Set();
  for (const o of c.room.find(FIND_MY_CREEPS)) if (o.id !== c.id && o.memory.ft) taken.add(o.memory.ft);
  // 03:00 once a trip has committed to a container sink (memory.sk), only divert to a fill target within 5 tiles: a loaded
  // w8hauler flipped 4x in 60 ticks between ctl cont 13,26 and hub ext 32,36 as Spawn2 drained/others refilled extensions
  const lim = Math.min(rng, c.memory.sk ? 5 : 99), fa = F.alive(c.room); // 17:5x alive, not active: a starved filler is fed via storage (haulers filling the hub themselves kept storage at 0 and the filler empty)
  // Wartime: haulers may assist hub duty while spawn energy is short (filler alone cannot keep up with fat raid bodies).
  let warHub = false; try { warHub = require('../../roles/raid9').pauseCivilians() && c.room.energyAvailable < c.room.energyCapacityAvailable; } catch (e) { warHub = false; }
  const cand = c.room.find(FIND_MY_STRUCTURES, { filter: s => s.store && s.store.getFreeCapacity(E) > 0 && c.pos.inRangeTo(s, lim) && (s.structureType === STRUCTURE_SPAWN
    || (s.structureType === STRUCTURE_EXTENSION && !taken.has(s.id)) || (tower && s.structureType === STRUCTURE_TOWER && s.store.getFreeCapacity(E) > 200))
    && !(fa && !warHub && F.isDuty(c.room, s)) }); // 17:4x: hub extensions/spawns are the w8filler's while it works (haulers: Spawn2 cluster + tower); warHub opens hub
  // 14:57 (Misaki): hub extensions/spawns/tower first, Spawn2 + its 5 temp extensions last (spawning drains them last too)
  const hub = cand.filter(s => !lastE(s)), t = c.pos.findClosestByRange(hub.length ? hub : cand);
  c.memory.ft = t ? t.id : undefined; return t;
}
const onTile = (c, tiles) => tiles.some(([x, y]) => c.pos.x === x && c.pos.y === y);
// sticky tile claim (memory[key] = index): keep my claim unless another creep claims it; a new claim needs a tile nobody stands on or claims
function pickTile(c, tiles, key) {
  const claimed = new Set(), stood = new Set();
  for (const o of Game.rooms[C.ROOM].find(FIND_MY_CREEPS)) if (o.id !== c.id) { stood.add(o.pos.x + ',' + o.pos.y); if (o.memory[key] !== undefined && tiles[o.memory[key]]) claimed.add(String(tiles[o.memory[key]])); }
  const me = c.memory[key];
  if (me !== undefined && tiles[me] && !claimed.has(String(tiles[me]))) return me;
  return tiles.findIndex(t => !claimed.has(String(t)) && !stood.has(String(t)));
}
// 20:55: plain 'lowest first' made both builders ping-pong between the x8-11 and x24-31 groups (16+ tiles) every time one
// repair lifted a wall past the others (walls within 200 hits), even walking over with 2 energy left. Now: sticky per-creep
// target kept until it is 500 above the weakest; new picks are the closest wall within 500 of the weakest.
function wallJob(room, c, cap) {
  // 11-02 17:4x/21:xx: planTarget may be w8seal=1M, but deep raise above STAGE3 only when stor >= sealMinE (default LEAN_SOFT=25k).
  // 11-03 02:4x: sealDeepOk also parks while softCap2 / sticky w8sealPark (Misaki rejected raising sealMinE to 35k).
  // Otherwise a live maintenance builder kept burning the bank into seal→1M while softCap2 / KEY catch-up needed the energy.
  let plan = TH.planTarget(room.controller.level, C.WALL_TARGET[room.controller.level] || 0);
  const storE = room.storage && room.storage.store ? (room.storage.store[E] || 0) : 0;
  if (!TH.sealDeepOk(storE)) plan = Math.min(plan, TH.STAGE3);
  const tgt = Math.min(cap === undefined ? Infinity : cap, TH.wallTarget(plan));
  // 17:15: seal walls only. Core ramparts (14:09) are no longer raised by builders (Misaki: development first, as in home).
  const ws = room.find(FIND_STRUCTURES, { filter: s => (s.structureType === STRUCTURE_WALL || (s.structureType === STRUCTURE_RAMPART && (C.GATE || []).some(([x, y]) => s.pos.x === x && s.pos.y === y))) && s.hits < tgt && C.SEAL.some(([x, y]) => s.pos.x === x && s.pos.y === y) });
  if (!ws.length) { if (c) delete c.memory.wt; return null; }
  const lo = _.min(ws, s => s.hits).hits;
  if (!c) return ws.find(s => s.hits === lo);
  // 14:42 (2026-10-19): a fixed 500-hit band made 5-6 WORK builders (500-600 hits/tick) switch walls every tick: 4 builders (22 WORK,
  // ~2200 hits/t possible) raised the 15 seal walls/core ramparts only ~140 hits/t (t83739446..479) while walking. Band scales with target.
  const band = Math.max(500, Math.floor(tgt / 10));
  const cur = c.memory.wt && ws.find(s => s.id === c.memory.wt);
  if (cur && cur.hits < lo + band) return cur;
  const t = c.pos.findClosestByRange(ws.filter(s => s.hits < lo + band * 0.6));
  c.memory.wt = t.id; return t;
}
// ---- W47N7 remote (only while reserved by us) ----
const RM = C.REMOTE;
const LAY = require('./layout');
const TH = require('./threat');
const ROADSET = new Set(require('./roads').ROADS.concat(require('../../layouts/w8link').W47N8).map(([x, y]) => x * 50 + y)); // deprecated roads are never repaired (09:13)
// 15:55 (Misaki "路断了"): W47N7 haul roads were never in any plan/repair list (laid by the old conquest builders), so 20 of ~39
// decayed to 30-570 hits and the rest vanished. remote_roads.js = shortest path cont -> N exit (tools/w47n7_roads.py).
// rminer places missing sites (<=3 open, every 50t); loaded rhaulers with a WORK part build/repair in passing (no detour).
const RROADS = require('./remote_roads').ROADS, RRSET = new Set(RROADS.map(([x, y]) => x * 50 + y));
let rrT = 0;
function rroadSites(room) {
  if (Game.time % 50 || !room || rrT === Game.time) return; rrT = Game.time; // any rminer in W47N7, once per tick
  let open = room.find(FIND_MY_CONSTRUCTION_SITES).length;
  for (const [x, y] of RROADS) {
    if (open >= 3) return;
    if (room.lookForAt(LOOK_STRUCTURES, x, y).some(s => s.structureType === STRUCTURE_ROAD) || room.lookForAt(LOOK_CONSTRUCTION_SITES, x, y).length) continue;
    if (room.createConstructionSite(x, y, STRUCTURE_ROAD) === OK) open++;
  }
}
function rroadWork(c) {
  if (c.room.name !== RM.room || !c.store[E] || !c.getActiveBodyparts(WORK)) return;
  const site = c.pos.findInRange(FIND_MY_CONSTRUCTION_SITES, 3, { filter: s => s.structureType === STRUCTURE_ROAD })[0];
  if (site) return c.build(site);
  // 15:2x patrol: underfoot-only repair lost to decay on swamp tiles (19,16 at 4200/25000: one 100-hit pass per trip < 500/1000t
  // swamp decay). Also top up the lowest planned road within range 3 below 50% (repair reaches 3 tiles, still no detour).
  const r = c.pos.lookFor(LOOK_STRUCTURES).find(s => s.structureType === STRUCTURE_ROAD && s.hits < s.hitsMax * 0.8)
    || _.min(c.pos.findInRange(FIND_STRUCTURES, 3, { filter: s => s.structureType === STRUCTURE_ROAD && s.hits < s.hitsMax * 0.5 && RRSET.has(s.pos.x * 50 + s.pos.y) }), s => s.hits / s.hitsMax);
  if (r && r !== Infinity) c.repair(r);
}
function rgo(c, x, y, r) { return rmove(c, RM.room, x, y, r); }
const go8 = (c, x, y, r = 1) => rmove(c, C.ROOM, x, y, r); // rhauler legs inside W47N8 too (same 1-wide trunk, 14,35-38 plain lane seen live)
// 11:4x strategy: lean KO haul (Overmind ExtractorOverlord pattern — mine→container→hauler→terminal).
// Dormant while RCL6_MINERALS false. Empty w8hauler drains mineral container (>= MIN_RUN or near-full) into terminal.
// 14:4x: terminal.send (index.mineralSend) + termFuel energy buffer complete the lean KO path once gate flips.
// terminal.send W47N8→W46N8 is a later slice; do NOT add it here.
const MIN_RUN = 500; // colony haulers are smaller than home (~400 carry vs ~800)
function mineralRun(c) {
  if (!C.RCL6_MINERALS) return false;
  const room = Game.rooms[C.ROOM]; if (!room) return false;
  const term = room.terminal; if (!term) return false;
  const held = Object.keys(c.store).find(r => r !== E && c.store[r] > 0);
  if (held) {
    if (c.pos.isNearTo(term)) c.transfer(term, held); else go8(c, term.pos.x, term.pos.y);
    return true;
  }
  if (c.store[E] > 0 || c.memory.w) return false;
  const [mx, my] = C.MINERAL_CONT || [37, 44];
  const k = room.lookForAt(LOOK_STRUCTURES, mx, my).find(s => s.structureType === STRUCTURE_CONTAINER);
  if (!k) { delete c.memory.mr; return false; }
  const r = Object.keys(k.store).find(t => t !== E && k.store[t] > 0);
  if (!r) { delete c.memory.mr; return false; }
  if (!c.memory.mr && k.store[r] < Math.min(MIN_RUN, c.store.getCapacity()) && k.store.getFreeCapacity() > 200) return false;
  c.memory.mr = 1;
  if (c.pos.isNearTo(k)) { c.withdraw(k, r); delete c.memory.mr; } else go8(c, mx, my);
  return true;
}
// 14:4x: park energy in terminal for send fees when K (or other mineral) is waiting. Overmind keeps
// transfer-cost buffer in the terminal; adjacent send ~33e/1k. Dormant while gate false.
// 11:4x 2026-11-01: post-minBuild stor often ~2–8k — old stor≥2000 floor blocked first fees; drop to 500 while mineral waits.
const TERM_E_FLOOR = 1000;
const TERM_FUEL_STOR = 500; // was 2000; 500 still leaves spawn/tower headroom under lean soft-cap
function termFuel(c) {
  if (!C.RCL6_MINERALS) return false;
  const room = Game.rooms[C.ROOM]; if (!room || !room.terminal || !room.storage) return false;
  const term = room.terminal, st = room.storage;
  if ((term.store[E] || 0) >= TERM_E_FLOOR) return false;
  const waiting = Object.keys(term.store).some(r => r !== E && (term.store[r] || 0) >= 100);
  if (!waiting) return false;
  if (Object.keys(c.store).some(r => r !== E && c.store[r] > 0)) return false;
  if (c.store[E] > 0) {
    if (c.pos.isNearTo(term)) c.transfer(term, E); else go8(c, term.pos.x, term.pos.y);
    return true;
  }
  if (c.memory.w) return false;
  if ((st.store[E] || 0) < TERM_FUEL_STOR) return false;
  if (c.pos.isNearTo(st)) c.withdraw(st, E); else go8(c, st.pos.x, st.pos.y);
  return true;
}

// Invader loot (2026-11-10, W47N8 30,2): haulPick / rhauler piles scored and withdrew energy only,
// so GO/KO/ZH/UH in the tombstone were left to decay. Reuse utils/salvage (minerals weighted,
// sticky until empty, dump to storage). mineralRun still delivers held minerals to the terminal
// when the RCL6 gate is on; salvage.dump is the fallback. Pick decaying loot before starting a
// mineral-container run or walking an empty rhauler out to W47N7.
const S = require('../../utils/salvage');
function holdingLoot(c) { return Object.keys(c.store).some(k => k !== E && c.store[k] > 0); }
function lootDump(c) {
  if (!holdingLoot(c)) return false;
  if (c.memory.role === 'w8hauler' && mineralRun(c)) return true;
  return S.dump(c);
}
function lootPick(c) {
  if (c.memory.w) return false;
  if (c.store.getFreeCapacity && c.store.getFreeCapacity() < S.WORTH) return false;
  const sv = S.pick(c); if (!sv) return false;
  delete c.memory.pt; delete c.memory.mr;
  if (c.pos.isNearTo(sv)) S.take(c, sv);
  else if (c.room.name === C.ROOM) go8(c, sv.pos.x, sv.pos.y);
  else rmove(c, c.room.name, sv.pos.x, sv.pos.y, 1);
  return true;
}
const R = {
  w8miner(c) {
    if (!home(c)) return;
    const S = C.SOURCES[c.memory.si | 0], [x, y] = S.stand;
    const src = Game.rooms[C.ROOM].lookForAt(LOOK_SOURCES, S.src[0], S.src[1])[0];
    // 22:05: learn the walk on first reaching the source (any adjacent tile). Measuring on the stand tile counted the overlap
    // spent harvesting beside the old miner, so the lead crept up every cycle (si1 146->157, replacement ~94 ticks early).
    // 11-10 patrol: a lost si0 miner arrived after a 1400-tick east-of-wall detour and wrote
    // w8lead[0]≈1378. Existing si0 miners then had TTL < lead, so they were not 'live' and a
    // third miner spawned. Same cap as w8rlead: only record a real walk, not a detour.
    if (src && !c.memory.arr && c.pos.isNearTo(src)) {
      c.memory.arr = Game.time;
      const t = Game.time - (c.memory.born || Game.time) - 3 * c.body.length;
      if (t > 0 && t <= 300) { const o = Memory.ops = Memory.ops || {}; (o.w8lead = o.w8lead || {})[c.memory.si | 0] = t; }
    }
    if (c.pos.x !== x || c.pos.y !== y) {
      // stand taken (e.g. a cqminer from home still mining): harvest from any tile next to the source
      if (Game.rooms[C.ROOM].lookForAt(LOOK_CREEPS, x, y).length && src) return c.pos.isNearTo(src) ? c.harvest(src) : MV.to(c, src.pos.x, src.pos.y, 1);
      // 11-10 patrol: native go() reusePath 10 expires during 6W1C1M fatigue (~8 t/tile). moveTo then
      // treats the wait as stuck and backtracks. si0 miner born 84177534 oscillated in the 35,11 pocket
      // east of the terrain wall for ~1200 t and never reached stand 26,11 (source A sat at 3000).
      // MV.to keeps the path across fatigue, ignores creeps, swaps when blocked.
      c.memory.wk = 1; return MV.to(c, x, y, 0);
    }
    const cont = c.pos.lookFor(LOOK_STRUCTURES).find(s => s.structureType === STRUCTURE_CONTAINER);
    if (cont && cont.hits < cont.hitsMax * 0.5 && c.store[E] > 0) return c.repair(cont);
    // RCL5: source link beside the stand; harvest overflow lands in the container under me
    // 19:5x: north tower low -> skip the link, overflow into the container under me for the haulers (northFeed above)
    const feed = S.link && cont && cont.store[E] < 1500 && northFeed(c.room);
    if (S.link && !feed && c.store.getCapacity() && c.store.getFreeCapacity() <= 2 * c.getActiveBodyparts(WORK)) {
      const lk = c.room.lookForAt(LOOK_STRUCTURES, S.link[0], S.link[1]).find(s => s.structureType === STRUCTURE_LINK);
      if (lk && lk.store.getFreeCapacity(E) > 0) c.transfer(lk, E);
    }
    if (src) c.harvest(src);
  },
  // 11:4x strategy: dormant mineral miner (home mminer pattern). Stands on MINERAL_CONT; harvest when extractor off CD.
  // No CARRY — output drops into the container underfoot. Spawned only while RCL6_MINERALS + extractor + minCont.
  w8mminer(c) {
    if (!home(c)) return;
    const [x, y] = C.MINERAL_CONT || [37, 44];
    if (c.pos.x !== x || c.pos.y !== y) return MV.to(c, x, y, 0);
    const m = c.memory.min ? Game.getObjectById(c.memory.min) : c.pos.findInRange(FIND_MINERALS, 1)[0];
    if (!m) return; c.memory.min = m.id;
    const ex = m.pos.lookFor(LOOK_STRUCTURES).find(s => s.structureType === STRUCTURE_EXTRACTOR);
    if (ex && !ex.cooldown && m.mineralAmount > 0) c.harvest(m);
  },
  w8hauler(c) {
    if (!home(c)) return;
    if (lootDump(c)) return;
    if (lootPick(c)) return;
    if (mineralRun(c)) return;
    if (termFuel(c)) return;
    toggle(c);
    if (!c.memory.w) { if (!haulPick(c) && c.store[E] > 0) c.memory.w = true; return; }
    const room8 = Game.rooms[C.ROOM];
    // CPU 13:10: the builder scan only runs when no fill target (same result as before, evaluated lazily)
    const fed = () => hubFeed(room8) && room8.find(FIND_MY_CREEPS, { filter: x => x.memory.role === 'w8builder' && x.store.getFreeCapacity(E) >= 50 && nearHub(x, 8) })
      .sort((a, b) => a.store[E] - b.store[E])[0];
    const t = fillTarget(c, true) || fed() || sink(room8, c) || room8.storage;
    // nothing to fill: hand it to the emptiest w8upgrader/w8builder; never drop on the ground (Misaki rule), else wait
    const k = t || Game.rooms[C.ROOM].find(FIND_MY_CREEPS, { filter: x => (x.memory.role === 'w8upgrader' || x.memory.role === 'w8builder')
      && x.store.getFreeCapacity(E) > 0 }).sort((a, b) => a.store[E] - b.store[E])[0];
    if (!k) return c.pos.inRangeTo(C.CTL[0], C.CTL[1], 4) || go8(c, C.CTL[0], C.CTL[1], 4);
    if (k.structureType === STRUCTURE_CONTAINER && k.pos.x === C.CTL_CONT[0] && k.pos.y === C.CTL_CONT[1] && !c.pos.isNearTo(k)) {
      // unload from a reserved tile (never the 13,25 dead end); both taken: wait within 2 (a range-0 path to an occupied tile wandered off)
      const room = Game.rooms[C.ROOM], f = C.CTL_HAUL.find(([x, y]) => !room.lookForAt(LOOK_CREEPS, x, y).length);
      if (f) go8(c, f[0], f[1], 0); else if (!c.pos.inRangeTo(k, 2)) go8(c, k.pos.x, k.pos.y, 2);
      return;
    }
    if (!c.pos.isNearTo(k)) { if (isFill(k)) FM.walk(c); go8(c, k.pos.x, k.pos.y); } else { if (isFill(k)) fillXfer(c, k); else c.transfer(k, E); delete c.memory.ft; }
  },
  w8upgrader(c) {
    if (!home(c)) return;
    const ctl = Game.rooms[C.ROOM].controller, cont = ctlCont();
    // sign like home (22:19): one upgrader walks over only while the sign differs; cheap string compare otherwise
    const SG = require('../../utils/sign');
    if (SG.needs(ctl, c.owner.username) && !_.some(Game.creeps, x => x.memory.signer && x.name !== c.name)) {
      c.memory.signer = 1;
      if (c.pos.isNearTo(ctl)) c.signController(ctl, SG.SIGN); else return go(c, ctl.pos.x, ctl.pos.y, 1);
    } else if (c.memory.signer) delete c.memory.signer;
    // stand beside the ctl container: upgrade and refill in the same tick, never leave (19:08 jam fix)
    if (cont && c.memory.role === 'w8upgrader') {
      const i = pickTile(c, C.UPG_STAND, 'st');
      if (i >= 0) {
        c.memory.st = i; const [x, y] = C.UPG_STAND[i];
        // 11:38 strategy: one standee repairs ctl cont <50% (Overmind UpgradeSite battery) before upgrade — miners already
        // do source/minCont <50%; without this the battery rot to ~25% while builders chase roads (same findClosest pool).
        if (c.store[E] && cont.hits < cont.hitsMax * 0.5 && c.pos.inRangeTo(cont, 3)) {
          const standees = _.filter(Game.creeps, x => x.memory && x.memory.role === 'w8upgrader' && x.store[E] > 0 && x.pos.inRangeTo(cont, 3));
          if (standees.length && _.min(standees, x => x.name).name === c.name) c.repair(cont);
          else if (c.pos.inRangeTo(ctl, 3)) c.upgradeController(ctl);
        } else if (c.store[E] && c.pos.inRangeTo(ctl, 3)) c.upgradeController(ctl);
        // 11:30: 9W1C2M upgraders left the stands whenever the ctl cont ran dry and walked ~20 tiles toward the piles (1 tile/3t) to fetch
        // 50 energy, missing the refill by ~30 ticks; a 1-CARRY upgrader waits at its stand instead
        const stay = c.store.getCapacity() <= 50;
        if (c.pos.x !== x || c.pos.y !== y) { if (c.store[E] || cont.store[E] || stay) return go(c, x, y, 0); }
        else { const lk = c.room.lookForAt(LOOK_STRUCTURES, C.CTL_LINK[0], C.CTL_LINK[1]).find(s => s.structureType === STRUCTURE_LINK && s.store[E] > 0 && c.pos.isNearTo(s));
          if (c.store[E] < 2 * c.getActiveBodyparts(WORK) && (lk || cont.store[E])) c.withdraw(lk || cont, E); /* CPU 21:20: refill only when ~2 ticks left (0.2/intent) */ if (c.store[E] || cont.store[E] || stay) return; }
        // container empty and I'm empty: fall through and fetch from the piles
      } else delete c.memory.st;
    }
    toggle(c);
    if (!c.memory.w) getEnergy(c);
    else {
      if (c.pos.inRangeTo(ctl, 3)) c.upgradeController(ctl);
      const j = pickTile(c, C.UPG_EXTRA, 'xs'); // park off the hauler tiles and corridors
      if (j >= 0) { c.memory.xs = j; if (!onTile(c, [C.UPG_EXTRA[j]])) go(c, C.UPG_EXTRA[j][0], C.UPG_EXTRA[j][1], 0); }
      else if (!c.pos.inRangeTo(ctl, 3)) go(c, ctl.pos.x, ctl.pos.y, 3);
    }
  },
  w8filler(c) { F.run(c); },
  // in-room defender (14:09): ranged-only, never leaves W47N8, never goes north of the seal (y<5); idles beside Spawn2.
  // 14:46 (Misaki): border ranged defender. Attacks intruders inside W47N8 only (never leaves: home() + no exit/seal-north tiles),
  // kites melee, self/ally heal when it has HEAL. Spawned only on an invasion move (TH.invasion) or an armed hostile in the base.
  w8defender(c) {
    // doctrine (src/rooms/w47n8/defense.js defPlan, docs/DEFENSE_W47N8.md): station right behind the seal nearest the enemy, shoot the
    // towers' focus (healer > ranged > melee), retreat to a tower below 60% hp, back at 90%; quiet: idle, no recycle (18:04).
    // memory.jd 'W46N8' = joint-defence creep sent by home (same role, counted in the joint roster)
    if (!home(c)) return;
    const D = require('./defense');
    const cb = (rn, m) => { if (rn !== C.ROOM) return false; for (let i = 0; i < 50; i++) { for (let y = 0; y <= 3; y++) m.set(i, y, 255); m.set(0, i, 255); m.set(49, i, 255); m.set(i, 49, 255); } return m; };
    const mv = (pos, r) => CMV.to(c, pos.x, pos.y, r, cb, 3); // creeps ignored, detour only when stuck (utils/combatmove)
    const room = c.room, hs = room.find(FIND_HOSTILE_CREEPS).filter(x => !x.my), mem = c.memory;
    if (hs.length || TH.invasion()) mem.seen = Game.time;
    const towers = room.find(FIND_MY_STRUCTURES, { filter: s => s.structureType === STRUCTURE_TOWER }).map(t => t.pos);
    const th = room.memory.threat8, idx = _.filter(Game.creeps, x => x.memory.role === 'w8defender').map(x => x.name).sort().indexOf(c.name);
    const p = D.defPlan({ pos: c.pos, hits: c.hits, hitsMax: c.hitsMax, hurt: mem.hurt }, hs,
      { focus: th && th.id, towers, quiet: Game.time - (mem.seen || mem.born || Game.time), enemyX: hs.length ? undefined : TH.invasion() ? Memory.ops && Memory.ops.w8invNx : undefined, idx: Math.max(0, idx), n: _.filter(Game.creeps, x => x.memory.role === 'w8defender' && x.room.name === C.ROOM).length,
        avoid: room.find(FIND_MY_CREEPS, { filter: x => x.memory.role === 'w8builder' && x.pos.y <= 6 }).map(x => x.pos),
        healer: (room.find(FIND_MY_CREEPS, { filter: x => x.memory.role === 'w8healer' && x.getActiveBodyparts(HEAL) > 0 })[0] || {}).pos });
    mem.hurt = p.hurt;
    if (p.mass) c.rangedMassAttack(); else if (p.shoot) c.rangedAttack(p.shoot);
    if (c.body.some(b => b.type === HEAL && b.hits > 0)) { // 17:59: HEAL parts heal every tick (heal() + rangedAttack same tick; rangedHeal only when not shooting)
      const fr = room.find(FIND_MY_CREEPS, { filter: x => x.hits < x.hitsMax || x.id === c.id }), a = D.healAct(c, fr, hs, !!(p.mass || p.shoot));
      if (a) { const t = Game.getObjectById(a.id); if (t) a.act === 'heal' ? c.heal(t) : c.rangedHeal(t); } }
    if (p.move === 'flee') { const away = PathFinder.search(c.pos, { pos: new RoomPosition(p.from.x, p.from.y, C.ROOM), range: 4 }, { flee: true, maxRooms: 1, roomCallback: rn => cb(rn, new PathFinder.CostMatrix()) }).path[0]; if (away) c.move(c.pos.getDirectionTo(away)); return; }
    if (p.move === 'retreat') { const rr = p.toHealer ? 1 : 2; return c.pos.inRangeTo(p.goal.x, p.goal.y, rr) || mv(p.goal, rr); }
    if (p.move === 'approach') return mv(p.goal, 3);
    if (p.move === 'post') return mv(p.goal, 0);
  },
  // 18:04 (Misaki) dedicated healer (HEAL+MOVE) in a joint roster of >= 4 defenders: behind the defenders, heals the most-hurt (heal at 1,
  // rangedHeal at 3), HP rule 60/90 like defenders, never crosses the seal. 10-20 07:31 (Misaki): waits at a safe spot >= 4 tiles inside
  // the seal (HIDLE, y=8, off road), goes out only to heal a hurt friendly from a tile out of enemy reach, then walks back.
  // 10-20 15:25 (Misaki) melee gate guard (defense.guardPlan): stands on gate rampart 29,3, hits what comes adjacent, sallies only at
  // catchable targets near the gate (dismantlers/melee/slow), HP rule 60/90, never leaves W47N8 (exit row blocked)
  w8guard(c) {
    if (!home(c)) return;
    const D = require('./defense'), room = c.room, hs = room.find(FIND_HOSTILE_CREEPS).filter(x => !x.my), mem = c.memory;
    const cb = (rn, m) => { if (rn !== C.ROOM) return false; for (let i = 0; i < 50; i++) { m.set(i, 0, 255); m.set(0, i, 255); m.set(49, i, 255); m.set(i, 49, 255); } return m; };
    const towers = room.find(FIND_MY_STRUCTURES, { filter: s => s.structureType === STRUCTURE_TOWER }).map(t => t.pos), th = room.memory.threat8;
    const p = D.guardPlan({ pos: c.pos, hits: c.hits, hitsMax: c.hitsMax, hurt: mem.hurt }, hs, { focus: th && th.id, towers,
      healer: (room.find(FIND_MY_CREEPS, { filter: x => x.memory.role === 'w8healer' && x.getActiveBodyparts(HEAL) > 0 })[0] || {}).pos });
    mem.hurt = p.hurt;
    if (p.hit) c.attack(p.hit);
    const mv = (pos, r) => CMV.to(c, pos.x, pos.y, r, cb, 2); // creeps ignored, detour only when stuck (utils/combatmove)
    if (p.move === 'retreat') return c.pos.inRangeTo(p.goal.x, p.goal.y, 1) || mv(p.goal, 1);
    if (p.move === 'approach' || p.move === 'sally') return mv(p.goal, 1);
    if (p.move === 'post') return mv(p.goal, 0);
  },
  w8healer(c) {
    if (!home(c)) return;
    const D = require('./defense'), room = c.room, hs = room.find(FIND_HOSTILE_CREEPS).filter(x => !x.my), mem = c.memory;
    const cb = (rn, m) => { if (rn !== C.ROOM) return false; for (let i = 0; i < 50; i++) { for (let y = 0; y <= 4; y++) m.set(i, y, 255); m.set(0, i, 255); m.set(49, i, 255); m.set(i, 49, 255); } return m; };
    const mv = (pos, r) => CMV.to(c, pos.x, pos.y, r, cb, 3); // creeps ignored, detour only when stuck (utils/combatmove)
    const defs = room.find(FIND_MY_CREEPS, { filter: x => x.memory.role === 'w8defender' });
    const towers = room.find(FIND_MY_STRUCTURES, { filter: s => s.structureType === STRUCTURE_TOWER }).map(t => t.pos);
    const idx = _.filter(Game.creeps, x => x.memory.role === 'w8healer').map(x => x.name).sort().indexOf(c.name);
    const tr = room.getTerrain(), open = (x, y) => !(tr.get(x, y) & TERRAIN_MASK_WALL) && !room.lookForAt(LOOK_STRUCTURES, x, y).some(s => s.structureType === STRUCTURE_ROAD || (s.structureType !== STRUCTURE_RAMPART && s.structureType !== STRUCTURE_CONTAINER)) && !room.lookForAt(LOOK_CREEPS, x, y).some(k => k.id !== c.id);
    const dmgd = room.find(FIND_MY_CREEPS, { filter: x => x.memory.role !== 'w8defender' && x.id !== c.id && x.hits < x.hitsMax }); // any hurt friendly
    const p = D.healPlan({ id: c.id, pos: c.pos, hits: c.hits, hitsMax: c.hitsMax, hurt: mem.hurt }, defs.concat(dmgd), hs, { towers, idx: Math.max(0, idx), open });
    mem.hurt = p.hurt;
    if (p.heal) { const t = Game.getObjectById(p.heal.id); if (t) p.heal.act === 'heal' ? c.heal(t) : c.rangedHeal(t); }
    if (p.move === 'flee') { const away = PathFinder.search(c.pos, { pos: new RoomPosition(p.from.x, p.from.y, C.ROOM), range: 4 }, { flee: true, maxRooms: 1, roomCallback: rn => cb(rn, new PathFinder.CostMatrix()) }).path[0]; if (away) c.move(c.pos.getDirectionTo(away)); return; }
    if (p.move === 'retreat') return c.pos.inRangeTo(p.goal.x, p.goal.y, 2) || mv(p.goal, 2);
    if (p.move === 'post') return mv(p.goal, 0);
  },
  w8rminer(c) {
    // 14:23: armed hostiles in W47N7 / W47N8 north -> hold inside the W47N8 base (loaded haulers still unload there), resume when clear
    if (TH.flee() && (c.memory.role === 'w8rminer' || !c.store[E] || c.room.name !== C.ROOM)) {
      if (c.room.name !== C.ROOM || !c.pos.inRangeTo(C.SPAWN[0], C.SPAWN[1], 5)) c.moveTo(new RoomPosition(C.SPAWN[0], C.SPAWN[1], C.ROOM), { range: 4, reusePath: 20 });
      return;
    }
    const S = RM.sources[c.memory.si | 0], [x, y] = S.stand;
    if (c.room.name !== RM.room) return rgo(c, x, y, 0);
    rroadSites(c.room);
    const src = c.room.lookForAt(LOOK_SOURCES, S.src[0], S.src[1])[0];
    // 10-19 21:4x: learn the walk (spawn end -> beside the source) for the replacement lead in index.js rmLead8
    if (src && !c.memory.arr && c.pos.isNearTo(src)) { c.memory.arr = Game.time; const t = Game.time - (c.memory.born || Game.time) - 3 * c.body.length; if (t > 0 && t <= 300) { const o = Memory.ops = Memory.ops || {}; (o.w8rlead = o.w8rlead || {})[c.memory.si | 0] = t; } } // > 300 = already on station at deploy, not a walk
    if (c.pos.x !== x || c.pos.y !== y) {
      // stand taken (e.g. a BustJetter creep; passive, never attack): mine from any tile next to the source
      if (c.room.lookForAt(LOOK_CREEPS, x, y).length && src) return c.pos.isNearTo(src) ? c.harvest(src) : rgo(c, src.pos.x, src.pos.y, 1);
      return rgo(c, x, y, 0);
    }
    const cont = c.pos.lookFor(LOOK_STRUCTURES).find(s => s.structureType === STRUCTURE_CONTAINER);
    if (!cont) {
      const site = c.pos.lookFor(LOOK_CONSTRUCTION_SITES)[0];
      if (!site) c.room.createConstructionSite(x, y, STRUCTURE_CONTAINER);
      else if (c.store[E] >= c.getActiveBodyparts(WORK) * 5) return c.build(site);
    } else if (cont.hits < cont.hitsMax * 0.5 && c.store[E] > 0) return c.repair(cont);
    if (src) c.harvest(src);
  },
  w8rhauler(c) {
    // 14:23: armed hostiles in W47N7 / W47N8 north -> hold inside the W47N8 base (loaded haulers still unload there), resume when clear
    if (TH.flee() && (c.memory.role === 'w8rminer' || !c.store[E] || c.room.name !== C.ROOM)) {
      if (c.room.name !== C.ROOM || !c.pos.inRangeTo(C.SPAWN[0], C.SPAWN[1], 5)) c.moveTo(new RoomPosition(C.SPAWN[0], C.SPAWN[1], C.ROOM), { range: 4, reusePath: 20 });
      return;
    }
    toggle(c);
    if (holdingLoot(c)) { if (!home(c)) return; if (lootDump(c)) return; }
    // one-off sign of W47N7 with home's text (22:21): only while it differs, one hauler at a time, then back to work
    if (c.room.name === RM.room && c.room.controller) {
      const SG = require('../../utils/sign'), ct = c.room.controller;
      if (SG.needs(ct, c.owner.username) && (c.memory.signer || !_.some(Game.creeps, x => x.memory.signer && x.memory.role === 'w8rhauler'))) {
        c.memory.signer = 1;
        if (c.pos.isNearTo(ct)) c.signController(ct, SG.SIGN); else return rgo(c, ct.pos.x, ct.pos.y, 1);
        return;
      } else if (c.memory.signer) delete c.memory.signer;
    }
    // 10:15: w8rhauler ttl15 sat loaded at W47N7 23,15 (picked 500 at 18,17 with ~20 ttl left, dies before the hub ~50 tiles away).
    // Under 90 ttl: carry what I have home, never start a new pickup (energy stays in the container for the next hauler).
    if (!c.memory.w && c.ticksToLive < 90) { if (c.store[E] > 0) c.memory.w = true; else { c.suicide(); return; } }
    if (!c.memory.w) {
      if (lootPick(c)) return;
      // 17:45: W47N7 over-hauled (75 CARRY, conts 120/520, rhaulers waiting) while W47N8 source B cont 11,43 hit 1826/2000 (local haulers
      // busy refilling extensions). The rhauler exit path passes beside 11,43 (12,42): when W47N7 holds < 800, take a load there -> ctl.
      if (c.room.name === C.ROOM) {
        const l7 = Memory.ops && Memory.ops.w8lo7, B = C.SOURCES[1].stand;
        if (l7 && Game.time - l7.t < 50 && l7.v < 800 && c.pos.inRangeTo(B[0], B[1], 4)) {
          const kb = c.room.lookForAt(LOOK_STRUCTURES, B[0], B[1]).find(s => s.structureType === STRUCTURE_CONTAINER && s.store[E] >= 500);
          if (kb) return c.pos.isNearTo(kb) ? c.withdraw(kb, E) : go8(c, B[0], B[1]);
        }
      }
      if (c.room.name !== RM.room) return rgo(c, 25, 25, 20);
      const amt = o => (o.amount !== undefined ? o.amount : o.store[E]);
      // 03:30: closest-first starved the south source (31,34 at 2000+2k drop while north 18,17 had 400-600 and ate every empty rhauler from the N exit)
      const piles = c.room.find(FIND_DROPPED_RESOURCES, { filter: r => r.resourceType === E && r.amount >= 100 })
        .concat(c.room.find(FIND_STRUCTURES, { filter: s => s.structureType === STRUCTURE_CONTAINER && s.store[E] >= 200 }));
      Memory.ops = Memory.ops || {}; if (!Memory.ops.w8lo7 || Memory.ops.w8lo7.t !== Game.time) Memory.ops.w8lo7 = { t: Game.time, v: _.sum(c.room.find(FIND_STRUCTURES, { filter: s => s.structureType === STRUCTURE_CONTAINER }), s => s.store[E]) + _.sum(c.room.find(FIND_DROPPED_RESOURCES), r => r.amount) };
      const closest = c.pos.findClosestByRange(piles);
      const fullest = piles.length ? _.max(piles, amt) : null;
      const t = (fullest && closest && amt(fullest) >= amt(closest) + 500) ? fullest : closest;
      if (!t) {
        if (c.store[E] > 0) { c.memory.w = true; return; }
        // 21:10: nothing >=200 yet: wait within 2 of the fullest container instead of idling on the north edge (19,0-19,2)
        const w = _.max(c.room.find(FIND_STRUCTURES, { filter: s => s.structureType === STRUCTURE_CONTAINER }), s => s.store[E]);
        if (w && w.pos && !c.pos.inRangeTo(w, 2)) rgo(c, w.pos.x, w.pos.y, 2);
        return;
      }
      if (!c.pos.isNearTo(t)) return rgo(c, t.pos.x, t.pos.y, 1);
      return t.amount !== undefined ? c.pickup(t) : c.withdraw(t, E);
    }
    rroadWork(c);
    if (!home(c)) return;
    const room = Game.rooms[C.ROOM];
    // 15:10 model: 700-carry rhaulers spent 24-143 ticks per trip inside W47N8 filling single 50-energy extensions across the hub and
    // flipping ctl <-> hub (w8rhauler83738293 t8492-8568), and a range-3 limit still chained strip to strip (t83739964-40016). Now they
    // never detour for extensions: top up one adjacent extension/spawn in passing (transfer + move same tick) and walk on to ctl/hub
    // cont -> storage. Full fill duty only when spawn energy < 300 or no local w8hauler (extensions are the w8haulers' job).
    let warLow = false; try { warLow = require('../../roles/raid9').pauseCivilians(); } catch (e) { warLow = false; }
    const low = warLow ? room.energyAvailable < room.energyCapacityAvailable : (room.energyAvailable < 300 || !room.find(FIND_MY_CREEPS, { filter: x => x.memory.role === 'w8hauler' }).length);
    if (!low) delete c.memory.ft;
    const t = (low && fillTarget(c, false)) || sink(room, c) || room.storage;
    if (t && !low && !c.pos.isNearTo(t)) {
      const adj = c.pos.findInRange(FIND_MY_STRUCTURES, 1, { filter: s => (s.structureType === STRUCTURE_EXTENSION || s.structureType === STRUCTURE_SPAWN) && s.store.getFreeCapacity(E) > 0 })[0];
      if (adj) fillXfer(c, adj);
    }
    if (!t) return go8(c, C.CTL[0], C.CTL[1], 3);
    if (!c.pos.isNearTo(t)) { if (isFill(t)) FM.walk(c); go8(c, t.pos.x, t.pos.y); } else { if (isFill(t)) fillXfer(c, t); else c.transfer(t, E); delete c.memory.ft; }
  },
  w8builder(c) {
    if (!home(c)) return; toggle(c);
    // hub feed: at the hub sites, build with whatever I hold; when empty wait (<=40 ticks) for a hauler instead of walking off
    if (!c.memory.w && hubFeed(c.room) && nearHub(c, 8)) {
      if (c.store[E] > 0) c.memory.w = true;
      else if ((c.memory.fw = (c.memory.fw || 0) + 1) <= 40) return;
    }
    if (c.store[E] > 0) delete c.memory.fw;
    if (!c.memory.w) { getEnergy(c); return; }
    // 17:36 (Misaki): seal walls under attack -> repair the lowest attacked segment from behind it, as far from enemy range as possible
    { const hs = c.room.find(FIND_HOSTILE_CREEPS).filter(x => !x.my), D = require('./defense');
      if (hs.some(D.armed)) { const ws = c.room.find(FIND_STRUCTURES, { filter: s => (s.structureType === STRUCTURE_WALL || s.structureType === STRUCTURE_RAMPART) && s.pos.y === 3 }), w = D.repairPick(ws, hs);
        if (w) { const ter = c.room.getTerrain(), st = D.repairStand(w, hs, (x, y) => ter.get(x, y) !== TERRAIN_MASK_WALL);
          if (st && (c.pos.x !== st.x || c.pos.y !== st.y)) go(c, st.x, st.y, 0); if (c.pos.inRangeTo(w, 3)) c.repair(w); return; } } }
    const all = c.room.find(FIND_MY_CONSTRUCTION_SITES);
    // north seal walls first (1 energy each, Misaki 17:08), x8-11 before x24-31; then the spawn/extension sites
    const seal = all.filter(s => s.structureType === STRUCTURE_WALL || (s.structureType === STRUCTURE_RAMPART && (C.GATE || []).some(([x, y]) => s.pos.x === x && s.pos.y === y))).sort((a, b) => (a.pos.x <= 11 ? 0 : 1) - (b.pos.x <= 11 ? 0 : 1));
    // 14:23 threat mode: seal walls to 50k before other sites (seal wall sites still first)
    const tj = !seal[0] && TH.on() && wallJob(c.room, c, TH.urgentTarget()); // 06:3x: only up to the 50k floor ahead of sites (tower 24,8 first at RCL5)
    if (tj) { if (!c.pos.inRangeTo(tj, 3)) go(c, tj.pos.x, tj.pos.y, 3); else c.repair(tj); return; }
    // 18:1x spawn move: the new spawn site goes first; forced prep: idle builders wait loaded beside the new slot
    const mvb = Memory.ops && Memory.ops.w8move, sp8 = all.find(s => s.structureType === STRUCTURE_SPAWN);
    if (!sp8 && !seal[0] && mvb && mvb.force && mvb.phase === 'prep') { const [nx, ny] = require('./layout').ORDER.spawn[0];
      if (c.store[E] < c.store.getCapacity() / 2) { c.memory.w = false; getEnergy(c); return; }
      if (!c.pos.inRangeTo(nx, ny, 2)) go(c, nx, ny, 2); return; }
    // 20:1x ext-phase relocation: new hub extension sites right after the spawn/seal sites
    const ex8 = mvb && mvb.phase === 'ext' && c.pos.findClosestByRange(all.filter(s => s.structureType === STRUCTURE_EXTENSION));
    // 10-31 19:1x: tower3@22,7 after spawn (not closest — hub ext sites stole focus once spawn finished)
    const tw8 = all.find(s => s.structureType === STRUCTURE_TOWER);
    const site = sp8 || seal[0] || tw8 || ex8 || c.pos.findClosestByRange(all);
    if (site) { if (!c.pos.inRangeTo(site, 3)) go(c, site.pos.x, site.pos.y, 3); else c.build(site); return; }
    // 19:31: urgent road/container repair (<10%; container 11,43 at 18% = 2k ticks of decay left pulled the builder off the walls) -> seal walls to WALL_TARGET[rcl], lowest first -> maintenance (<60%).
    // With maintenance first the lone 2W builder spent 180 ticks on container 26,11 (87k/250k) + 22 roads and no wall left 1 hit.
    // 11:38 strategy: Overmind WorkerOverlord repairs owned containers <50% *before* paving/fortify; RoadLogistics critical=25%/repair=90%.
    // Old rr() pooled containers+roads by distance — ~140 roads <50% starved ctl/hub/minCont at ~23–25% (~1.3h to death). Split pools.
    // 14:4x: after contMinPct hit ≥50%, softCap clear re-armed sealRaise and the lone builder stuck on deep seal@~542k while roadCrit=38
    // (roads 10–25%). Overmind parks fortifyDuty until assets>~500k and keeps RoadLogistics critical=25% as its own paver duty —
    // put roadNeed(0.25) *before* wallJob (deep seal); STAGE3/KEY already DONE; under-attack seal path above stays first.
    const contNeed = f => c.pos.findClosestByRange(FIND_STRUCTURES, { filter: s => s.structureType === STRUCTURE_CONTAINER && s.hits < s.hitsMax * f });
    const roadNeed = f => c.pos.findClosestByRange(FIND_STRUCTURES, { filter: s => s.structureType === STRUCTURE_ROAD && ROADSET.has(s.pos.x * 50 + s.pos.y) && s.hits < s.hitsMax * f });
    // CPU 13:10: sticky repair target, rescanned every 15 ticks or when done (was 2-3 FIND_STRUCTURES scans per builder per tick)
    // 11:38: also break sticky when a container sits under the 50% band (do not finish a mid road while battery dies)
    // 14:4x: also break sticky fortify when a kept road is under critical 25% (do not finish seal→1M while roadCrit drains)
    let rep = c.memory.rj && Game.getObjectById(c.memory.rj);
    const contUrgent = contNeed(0.5);
    const mvp = require('./index').energyBank(c.room); // 15:5x+08:4x: road/container upkeep paused while banking/leanBank (only <10% urgent)
    const roadCritNeed = mvp ? null : roadNeed(0.25);
    if (!rep || Game.time >= (c.memory.rjt || 0)
      || (contUrgent && rep.structureType !== STRUCTURE_CONTAINER)
      || (roadCritNeed && (rep.structureType === STRUCTURE_WALL || rep.structureType === STRUCTURE_RAMPART))
      || rep.hits >= (rep.structureType === STRUCTURE_WALL || rep.structureType === STRUCTURE_RAMPART ? TH.wallTarget(TH.planTarget(c.room.controller.level, C.WALL_TARGET[c.room.controller.level] || 0)) : rep.hitsMax * 0.95)) {
      // urgent any <10% → containers <50% → roads critical 25% → seal wallJob → roads maint 60% (mvp: skip mid-band roads; containers+wallJob still run)
      rep = contNeed(0.1) || roadNeed(0.1) || contUrgent || roadCritNeed || wallJob(c.room, c) || (mvp ? null : roadNeed(0.6));
      c.memory.rj = rep ? rep.id : undefined; c.memory.rjt = Game.time + 15;
    }
    if (rep) {
      if (c.pos.inRangeTo(rep, 3)) { c.repair(rep); return; }
      if (c.store[E] < 20 && c.pos.getRangeTo(rep) > 6) { c.memory.w = false; getEnergy(c); return; } // don't walk a near-empty load across the room
      go(c, rep.pos.x, rep.pos.y, 3); return;
    }
    // 10-20 14:4x strategy review: while the spawn move banks (Memory.ops.w8move prep, MOVE_E 16k in storage) an idle builder parks
    // instead of falling back to w8upgrader, which refilled from storage (3 x 6W = 18 e/t, about the whole W47N8 surplus once the north
    // line reached the 100k stage-1 cap), so the bank would never fill while the builders lived.
    const mv = Memory.ops && Memory.ops.w8move;
    if ((mv && mv.phase === 'prep' && require('./index').banking(c.room)) || require('./index').leanBank(c.room)) {
      const j = pickTile(c, C.UPG_EXTRA, 'xs');
      if (j >= 0) { c.memory.xs = j; if (!onTile(c, [C.UPG_EXTRA[j]])) go(c, C.UPG_EXTRA[j][0], C.UPG_EXTRA[j][1], 0); }
      return;
    }
    R.w8upgrader(c);
  },
};
// main.js dispatches roles[role].run(c): wrap (bare functions crashed every w8 creep with 'run is not a function')
// 17:20 retire surplus creeps now instead of waiting out their TTL: Memory.ops.w8recycle = [names] -> walk to Spawn2 and recycle
// (returns up to body cost x ttl/1500 as a tombstone, which w8haulers collect)
function recycled(c) {
  const L = Memory.ops && Memory.ops.w8recycle; if (!L || !L.includes(c.name)) return false;
  const sp = Game.spawns.Spawn2; if (!sp) return false;
  if (c.store[E] && c.room.name === C.ROOM) { const cc = ctlCont(); if (cc && c.pos.isNearTo(cc)) { c.transfer(cc, E); return true; } }
  if (c.pos.isNearTo(sp)) { sp.recycleCreep(c); Memory.ops.w8recycle = L.filter(n => n !== c.name && Game.creeps[n]); } else c.moveTo(sp, { range: 1, reusePath: 10 });
  return true;
}
// Commander act/duty beats w8recycle and the role body (docs/COMMANDER.md). Unarmed: one check.
const cmd = require('../../utils/cmd');
module.exports = Object.fromEntries(Object.entries(R).map(([k, f]) => [k, { run(c) {
  if (cmd.yieldCreep(c)) return;
  return recycled(c) || f(c);
} }]));
Object.defineProperty(module.exports, '_fill', { value: fillTarget, enumerable: false }); // tests only
Object.defineProperty(module.exports, '_northFeed', { value: northFeed, enumerable: false }); // tests only
Object.defineProperty(module.exports, '_sink', { value: sink, enumerable: false }); // tests only
Object.defineProperty(module.exports, '_haulPick', { value: haulPick, enumerable: false }); // tests only
Object.defineProperty(module.exports, '_wallJob', { value: wallJob, enumerable: false }); // tests only
Object.defineProperty(module.exports, '_rmove', { value: rmove, enumerable: false }); // tests only
Object.defineProperty(module.exports, '_home', { value: home, enumerable: false }); // tests only
Object.defineProperty(module.exports, '_mineralRun', { value: mineralRun, enumerable: false }); // tests only
Object.defineProperty(module.exports, '_lootPick', { value: lootPick, enumerable: false });
Object.defineProperty(module.exports, '_lootDump', { value: lootDump, enumerable: false });
Object.defineProperty(module.exports, '_termFuel', { value: termFuel, enumerable: false }); // tests only
