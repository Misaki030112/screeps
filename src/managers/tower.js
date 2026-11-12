// Towers: attack closest hostile, heal own creeps, repair planned roads/containers (<60%) and ramparts up to target.
// Off-plan leftovers (old v1 roads, 31,11 container) are left to decay. Repair target chosen every 10 ticks.
// Rampart top-up only while storage holds the defender reserve (threat.reserve): tower refills for the 16 RCL4 ramparts
// (~4k energy to 50k) competed with spawn refills and storage fell 1040 -> 200 (10-14 02:45), no 1300 for a defender. Below it only
// ramparts under RAMPART_FLOOR are repaired, so fresh ramparts (1 hit, decay 300/100t) never die.
const plan = require('../utils/plan'), rc = require('../utils/roomcache'), cmd = require('../utils/cmd');
const FIRE_FLOOR = 300; // keep for emergencies (docs/DEFENSE.md)
const RAMPART_TARGET = [0, 0, 0, 20000, 50000, 100000, 300000, 1000000, 3000000], RAMPART_FLOOR = 5000;
// New lab/factory covers stop at the RCL6 rampart target. The RCL7 room target is 1e6 and rampHW ratchets
// toward it (~865k live), which would pull a fresh 1-hit cover up with the rest of the room. Covers already
// well above 300k (the three built W46N8 labs, ~1M) stay on the room target. A repair tick cannot cross this gap.
const IND_RAMP = 300000, IND_LEGACY = 500000;
let indKeys = null;
function industryKeys() {
  if (indKeys) return indKeys;
  indKeys = new Set();
  const P = plan.get('W46N8'), rcl = P && P.raw && P.raw.rcl;
  if (!rcl) return indKeys;
  for (const lv of Object.values(rcl)) for (const t of ['lab', 'factory']) for (const [x, y] of (lv[t] || [])) indKeys.add(x * 50 + y);
  return indKeys;
}
function indType(t) { return t === 'lab' || t === 'factory'; }
// Cover of a lab/factory: the structure, its construction site, or a planned lab/factory tile (the rampart
// finishes in one energy, long before the 50k building, and decays 300 hits / 100t if nothing claims it).
function industryTile(room, x, y) {
  if (x == null || y == null) return false;
  if (industryKeys().has(x * 50 + y)) return true;
  if (!room || !room.lookForAt) return false;
  const hit = list => list && list.some(s => s && indType(s.structureType));
  if (hit(room.lookForAt(LOOK_STRUCTURES, x, y))) return true;
  if (typeof LOOK_CONSTRUCTION_SITES !== 'undefined' && hit(room.lookForAt(LOOK_CONSTRUCTION_SITES, x, y))) return true;
  return false;
}
// Hits cap for one rampart. Non-covers and legacy covers (already on the 1M path) use the RCL target.
function coverTarget(room, s, rclT) {
  if (!s || !s.pos || !industryTile(room, s.pos.x, s.pos.y)) return rclT;
  if ((s.hits || 0) >= IND_LEGACY) return rclT;
  return Math.min(rclT, IND_RAMP);
}
// Growth throttle: a rampart already above the previous RCL's target is only "growing" -> repair it every 5th tick (<= 2 e/t per
// tower). At RCL5, 2 towers x 10 e/t would pour ~10.6k energy (17 ramparts 50k->100k) into walls while tower/extension sites
// and upgraders need it (docs/RCL5.md). Fresh/damaged ramparts below the previous target still get full speed.
function growthPaused(s, rcl, time) {
  const prev = RAMPART_TARGET[Math.max(0, rcl - 1)];
  return s.structureType === STRUCTURE_RAMPART && prev > 0 && s.hits >= prev && time % 5 !== 0;
}
const PEACE_HEAL_E = 200; // 18:00 peacetime heal energy floor
// Road/container upkeep (<60%): planned tiles, plus at home the road-plan tiles (managers/roads isHomeTile: W45N8 haul leg
// 38,30->48,15, econ, wall trunks, w8link). Those were in no layout plan, so only builders repaired them, and builders are 0 while
// storage sits at the 15k floor: strategy review 10-20 11:4x found the shared W45N8/W45N7 haul leg at 34-52% (44,19 1700/5000,
// ~2 hits/t wear from 6 rhaulers) and 30,12/29,11/28,10 had already decayed out (Misaki 10-20: remote roads must never decay away).
function upkeep(P, roomName, s) {
  if (s.hits >= s.hitsMax * 0.6) return false;
  if (P.any[plan.key(s.pos.x, s.pos.y)]) return true;
  return s.structureType === STRUCTURE_ROAD && roomName === 'W46N8' && require('./roads').isHomeTile(s.pos.x, s.pos.y);
}
module.exports = { growthPaused, upkeep, coverTarget, IND_RAMP, IND_LEGACY, run(room) {
  const towers = rc.all(room, STRUCTURE_TOWER);
  if (!towers.length) return;
  if (room.memory.drain && Game.time % 100 === 0 && !room.find(FIND_HOSTILE_CREEPS).length) require('../utils/focus').track(room.memory.drain, [], Game.time);
  const hostiles = room.find(FIND_HOSTILE_CREEPS);
  const mem = room.memory;
  if (hostiles.length) { // focus fire (utils/focus): healer first when killable, never feed edge drainers
    const H = require('./home'), F = require('../utils/focus');
    const banned = F.track(mem.drain || (mem.drain = {}), hostiles, Game.time, mem.focus, mem.focusE);
    const hurting = H.hurting(room);
    let p = F.pick(towers.map(t => ({ pos: t.pos, energy: t.store[RESOURCE_ENERGY] })), hostiles, { prev: mem.focus, hurting, banned });
    // energy floor: a target that is not hurting us and not dying within 2 ticks is only shot by towers holding >= FLOOR
    const shooters = p && (hurting.has(p.h.id) || p.ttk <= 2) ? towers : towers.filter(t => t.store[RESOURCE_ENERGY] >= FIRE_FLOOR);
    if (p && !shooters.length) p = null;
    mem.focus = p ? p.h.id : undefined; mem.focusE = p ? shooters.length * 10 : 0;
    // 17:48 (Misaki): a friendly creep < 60% (no-HEAL first, lowest %) is healed instead of attacking this tick
    const hurt = F.healPick(room.find(FIND_MY_CREEPS), !F.hostileArmed(hostiles)); // 18:00: no armed/healing hostile -> heal to full
    // Peel commanded towers before any auto shot/heal so an order on a tower that is
    // not in `shooters` still runs (the others keep the focus plan).
    const auto = cmd.armed() ? towers.filter(t => !cmd.consumeTower(t)) : towers;
    const autoShoot = auto.length === towers.length ? shooters : shooters.filter(t => auto.includes(t));
    if (hurt) { for (const t of auto) t.heal(hurt); return; }
    if (p) { for (const t of autoShoot) t.attack(p.h); return; }
    // holding fire: repair only critical barriers (<2000) and keep >=500 for the next shot window
    const crit = !hurt && rc.all(room, STRUCTURE_RAMPART).concat(rc.all(room, STRUCTURE_WALL)).filter(s => s.hits < 2000)[0];
    for (const t of auto) { if (crit && t.store[RESOURCE_ENERGY] > 500) t.repair(crit); }
    return;
  }
  if (Game.time % 10 === 0) {
    const P = plan.get(room.name), st = room.storage;
    const funded = !st || st.store[RESOURCE_ENERGY] >= require('./threat').reserve(room.name);
    const lvl = room.controller.level, rclT = RAMPART_TARGET[lvl] || 0;
    // Per-rampart cap. Lab/factory covers use 300k unless already on the legacy 1M path (coverTarget).
    // Unfunded storage still only holds the floor, and v4 gate ramparts stay builder work (walls.js).
    const W = require('./walls');
    const capFor = s => {
      if (s.structureType !== STRUCTURE_RAMPART) return s.hitsMax;
      let t = coverTarget(room, s, rclT);
      if (!funded) t = Math.min(RAMPART_FLOOR, t);
      if (W.planned(P, s.pos.x, s.pos.y, STRUCTURE_RAMPART)) t = Math.min(RAMPART_FLOOR, t);
      return t;
    };
    const hurt = require('../utils/focus').healPick(room.find(FIND_MY_CREEPS), true); // 18:00 (Misaki): peacetime -> heal any damaged creep to full
    mem.towerHeal = hurt ? hurt.id : undefined;
    const rampKeep = s => plan.rampartWanted(P, room, s.pos.x, s.pos.y) || industryTile(room, s.pos.x, s.pos.y);
    const cand = rc.all(room, STRUCTURE_RAMPART).filter(s => s.hits < capFor(s) && rampKeep(s))
      .concat(rc.all(room, STRUCTURE_ROAD).concat(rc.all(room, STRUCTURE_CONTAINER)).filter(s => upkeep(P, room.name, s)));
    // Misaki 20:12: ramparts must never decay, independent of the storage reserve. Ratchet a high-water floor (>=150k, capped at
    // the RCL target) and let towers (energy > 600) top up any rampart below it; decay costs ~3 hits/t per rampart (tiny).
    // 11-12: a new lab/factory cover is not part of that ratchet. rampHW is already ~865k; folding a 1-hit cover into it
    // would repair the cover toward 1e6 once every other rampart is at the RCL target. Legacy covers (cap == rclT) stay in.
    const rs = rc.all(room, STRUCTURE_RAMPART);
    if (rs.length) {
      const grow = rs.filter(s => coverTarget(room, s, rclT) >= rclT);
      const pool = grow.length ? grow : rs;
      const mn = Math.min(...pool.map(s => s.hits));
      mem.rampHW = Math.min(rclT, Math.max(mem.rampHW || 0, 150000, mn));
      mem.rampFloorRep = cand.length ? undefined : (rs.filter(s => coverTarget(room, s, rclT) >= rclT && s.hits < mem.rampHW).sort((a, b) => a.hits - b.hits)[0] || {}).id;
    }
    mem.towerRep = cand.length ? _.min(cand, s => s.hits / capFor(s)).id : undefined;
  }
  const heal = mem.towerHeal && Game.getObjectById(mem.towerHeal);
  const rep = mem.towerRep && Game.getObjectById(mem.towerRep);
  const fl = mem.rampFloorRep && Game.getObjectById(mem.rampFloorRep);
  for (const t of towers) {
    if (cmd.armed() && cmd.consumeTower(t)) continue; // commander owns this tower; the others keep peace repair
    if (heal && heal.hits < heal.hitsMax && t.store[RESOURCE_ENERGY] >= PEACE_HEAL_E) t.heal(heal); // floor: keep a combat reserve
    else if (!rep && fl && fl.hits < (mem.rampHW || 0) && t.store[RESOURCE_ENERGY] > 600) t.repair(fl);
    else if (rep && t.store[RESOURCE_ENERGY] > 800 && !growthPaused(rep, room.controller.level, Game.time)) t.repair(rep); // keep ≥800 for combat (novice ends 2026-10-28)
  }
} };
