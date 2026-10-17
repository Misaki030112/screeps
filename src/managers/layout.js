// Layout v2: places construction sites from the plan per RCL and removes structures that conflict with it.
// Safety: never destroys spawns/towers/storage; destroys conflicting extensions only while at least MIN_EXT
// non-conflicting extensions are built (spawn energy capacity never drops below RCL2 level); nothing is
// destroyed while hostiles are present; conflicting extensions go one capacity step at a time (never below CAP_FLOOR). Runs every 25 ticks (or on RCL change).
const plan = require('../utils/plan');
const move = require('../utils/move');
const rc = require('../utils/roomcache');
const walls = require('./walls');
// Tower before extensions (Overmind BuildPriorities): with MAX_SITES 5, RCL5 tower 2 would otherwise wait for ~7 of 10 extensions.
const PRIORITY = ['spawn', 'tower', 'extension', 'container', 'storage', 'link', 'road', 'rampart', 'terminal', 'extractor', 'lab', 'factory', 'powerSpawn', 'nuker', 'observer'];
const MAX_SITES = 5, MIN_EXT = 5, CAP_FLOOR = 650;
const NEVER_DESTROY = new Set([STRUCTURE_SPAWN, STRUCTURE_TOWER, STRUCTURE_STORAGE, STRUCTURE_TERMINAL, STRUCTURE_CONTROLLER, STRUCTURE_RAMPART]);
const WALKABLE = new Set([STRUCTURE_ROAD, STRUCTURE_CONTAINER, STRUCTURE_RAMPART]);
// A container listed in layout.remove (removeAt <= rcl) whose energy has another sink: a link or storage within 1 tile.
function obsoleteContainer(room, P, rcl, structs) {
  return structs.find(s => {
    if (s.structureType !== STRUCTURE_CONTAINER) return false;
    const w = P.any[plan.key(s.pos.x, s.pos.y)];
    if (!w || w.type !== 'container' || !w.removeAt || rcl < w.removeAt) return false;
    return structs.some(o => (o.structureType === STRUCTURE_LINK || o.structureType === STRUCTURE_STORAGE) && o.pos.getRangeTo(s.pos) <= 1);
  });
}
module.exports = { obsoleteContainer, run(room) {
  const P = plan.get(room.name); if (!P) return;
  const rcl = room.controller.level, mem = room.memory;
  if (Game.time % 25 && mem.layoutRcl === rcl && !mem.layoutKick) return;
  mem.layoutRcl = rcl; delete mem.layoutKick;
  const structs = room.find(FIND_STRUCTURES), sites = room.find(FIND_MY_CONSTRUCTION_SITES);
  const hostile = room.find(FIND_HOSTILE_CREEPS).length > 0;
  const log = [];
  // ---- conflicts
  const blocked = new Set(); const conflictExt = [];
  let goodExt = 0;
  for (const s of structs) {
    const t = s.structureType; if (t === STRUCTURE_CONTROLLER || t === STRUCTURE_RAMPART) continue;
    const k = plan.key(s.pos.x, s.pos.y), want = P.any[k];
    let conflict = false;
    if (t === STRUCTURE_ROAD) conflict = !!(want && want.type !== 'road' && want.rcl <= rcl);
    else if (t === STRUCTURE_CONTAINER) conflict = !!(want && want.type !== 'container' && want.rcl <= rcl);
    else if (s.my) conflict = want ? want.type !== t : P.standing.has(k);
    if (!conflict) { if (t === STRUCTURE_EXTENSION) goodExt++; continue; }
    blocked.add(k);
    if (t === STRUCTURE_EXTENSION) conflictExt.push(s);
    else if (!NEVER_DESTROY.has(t) && !hostile && (t === STRUCTURE_ROAD || t === STRUCTURE_CONTAINER)) {
      if (s.destroy() === OK) log.push(`destroyed ${t} ${s.pos.x},${s.pos.y}`);
    } else if (NEVER_DESTROY.has(t)) log.push(`KEEP conflicting ${t} ${s.pos.x},${s.pos.y} (manual decision)`);
  }
  if (conflictExt.length && !hostile && goodExt >= MIN_EXT) {
    // Gradual swap: keep spawn capacity >= CAP_FLOOR (remote reserver CLAIM1+MOVE1 = 650), one v2 site per freed slot.
    // Order: extensions on planned standing spots first (queen/filler paths), then the emptiest.
    let spare = Math.floor((room.energyCapacityAvailable - CAP_FLOOR) / EXTENSION_ENERGY_CAPACITY[rcl]);
    conflictExt.sort((a, b) => (P.standing.has(plan.key(b.pos.x, b.pos.y)) - P.standing.has(plan.key(a.pos.x, a.pos.y))) || (a.store.energy - b.store.energy));
    for (const s of conflictExt) { if (spare <= 0) break; if (s.destroy() === OK) { spare--; log.push(`destroyed extension ${s.pos.x},${s.pos.y} (good ext ${goodExt}, cap ${room.energyCapacityAvailable})`); } }
  }
  // Storage before ramparts: 4 RCL4 rampart sites filled MAX_SITES and unlocked a 2nd hungry builder
  // (sites>3) while storage was only 11% done — one fed builder finishes storage faster (patrol 10-13 20:52).
  const hasStorage = structs.some(s => s.structureType === STRUCTURE_STORAGE);
  for (const s of sites) {
    const want = P.any[plan.key(s.pos.x, s.pos.y)];
    const ok = walls.planned(P, s.pos.x, s.pos.y, s.structureType) || (s.structureType === STRUCTURE_ROAD && require('./roads').isHomeTile(s.pos.x, s.pos.y)) || (s.structureType === STRUCTURE_RAMPART
      ? !!(hasStorage && P.ramparts[plan.key(s.pos.x, s.pos.y)])
      : want && want.type === s.structureType);
    if (!ok) { s.remove(); log.push(`removed site ${s.structureType} ${s.pos.x},${s.pos.y}`); }
  }
  // ---- placement (re-find sites: removals above leave the cached array stale)
  const sitesNow = room.find(FIND_MY_CONSTRUCTION_SITES);
  let budget = MAX_SITES - sitesNow.length;
  const have = new Set(structs.map(s => s.structureType + plan.key(s.pos.x, s.pos.y)).concat(sitesNow.map(s => s.structureType + plan.key(s.pos.x, s.pos.y))));
  const wanted = plan.upTo(room.name, rcl);
  const extSites = sitesNow.some(s => s.structureType === STRUCTURE_EXTENSION);
  const hasTower = structs.some(s => s.structureType === STRUCTURE_TOWER);
  for (const type of PRIORITY) {
    if (budget <= 0) break;
    if (type === 'road' && (extSites || hostile)) continue;
    if (type === 'rampart') {
      if (!hasTower || !hasStorage) continue; // after storage is up (see site cleanup above)
      for (const k in P.ramparts) {
        if (budget <= 0) break;
        if (P.ramparts[k] > rcl || have.has('rampart' + k)) continue;
        const x = Math.floor(k / 50), y = k % 50;
        if (!plan.rampartWanted(P, room, x, y)) continue; // rampart only over something (stand tiles only with STATIONARY_FILL)
        if (room.createConstructionSite(x, y, 'rampart') === OK) { budget--; log.push(`site rampart ${x},${y}`); }
      }
      continue;
    }
    for (const w of wanted) {
      if (budget <= 0) break;
      if (w.type !== type) continue;
      const k = plan.key(w.x, w.y);
      if (have.has(type + k) || blocked.has(k)) continue;
      if (w.removeAt && rcl >= w.removeAt) continue; // planned removal: do not rebuild
      let r = room.createConstructionSite(w.x, w.y, type);
      if (r === ERR_RCL_NOT_ENOUGH && type === 'container' && !hostile) { // limit hit: free a slot from the removal list only
        const old = obsoleteContainer(room, P, rcl, structs);
        if (old && old.destroy() === OK) { log.push(`destroyed obsolete container ${old.pos.x},${old.pos.y} for ${w.x},${w.y}`); continue; }
      }
      if (r === OK) { budget--; log.push(`site ${type} ${w.x},${w.y}`); }
    }
  }
  // v4 gates/trunks/walls once the wall phase is 'build' (managers/walls.js; no-op before)
  if (budget > 0) log.push(...walls.placeSites(room, budget));
  if (log.length) { console.log('LAYOUT ' + log.join('; ')); move.invalidate(room.name); rc.invalidate(room.name); mem.layoutKick = log.some(l => l.startsWith('destroyed')) ? 1 : undefined; }
} };
