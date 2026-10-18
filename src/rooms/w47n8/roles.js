// W47N8 roles (w8miner / w8hauler / w8upgrader / w8builder). Simple, room-local; no safe mode anywhere.
const C = require('./config');
const go = (c, x, y, r = 1) => c.moveTo(new RoomPosition(x, y, C.ROOM), { range: r, reusePath: 10, maxRooms: 1 });
const E = 'energy';
const isHub = s => s.pos.x === C.HUB_CONT[0] && s.pos.y === C.HUB_CONT[1];
function home(c) { if (c.room.name !== C.ROOM) { c.moveTo(new RoomPosition(C.SPAWN[0], C.SPAWN[1], C.ROOM), { reusePath: 20 }); return false; } return true; }
function getEnergy(c) {
  const drop = c.pos.findClosestByRange(FIND_DROPPED_RESOURCES, { filter: r => r.resourceType === E && r.amount >= 50 });
  const cont = c.pos.findClosestByRange(FIND_STRUCTURES, { filter: s => s.structureType === STRUCTURE_CONTAINER && s.store[E] >= 100
    && !((s.pos.x === C.CTL_CONT[0] && s.pos.y === C.CTL_CONT[1] || isHub(s)) && c.memory.role === 'w8hauler') });
  const t = [drop, cont].filter(Boolean).sort((a, b) => c.pos.getRangeTo(a) - c.pos.getRangeTo(b))[0];
  if (t) { if (!c.pos.isNearTo(t)) go(c, t.pos.x, t.pos.y); else if (t.amount !== undefined) c.pickup(t); else c.withdraw(t, E); return true; }
  const src = c.pos.findClosestByRange(FIND_SOURCES_ACTIVE);
  if (src && c.getActiveBodyparts(WORK)) { if (!c.pos.isNearTo(src)) go(c, src.pos.x, src.pos.y); else c.harvest(src); return true; }
  return false;
}
// hauler pickup (18:05): sticky target scored by usable amount / (range+10), minus what other w8haulers already claimed,
// so haulers also clear the far south source (11,43: 2k energy piled while all 3 w8haulers circled the north source).
function haulPick(c) {
  const room = Game.rooms[C.ROOM], free = c.store.getFreeCapacity(), amt = o => (o.amount !== undefined ? o.amount : o.store[E]);
  let t = c.memory.pt && Game.getObjectById(c.memory.pt);
  if (!t || amt(t) < 50) {
    const claimed = {};
    for (const h of room.find(FIND_MY_CREEPS, { filter: x => x.memory.role === 'w8hauler' && x.id !== c.id && x.memory.pt && !x.memory.w }))
      claimed[h.memory.pt] = (claimed[h.memory.pt] || 0) + h.store.getFreeCapacity();
    const cands = room.find(FIND_DROPPED_RESOURCES, { filter: r => r.resourceType === E && r.amount >= 50 }).concat(room.find(FIND_STRUCTURES,
      { filter: s => s.structureType === STRUCTURE_CONTAINER && s.store[E] >= 100 && !(s.pos.x === C.CTL_CONT[0] && s.pos.y === C.CTL_CONT[1]) && !isHub(s) }));
    let bs = 0; t = null;
    // 18:20: score by the whole unclaimed pile, not min(free, pile): capped by a 150-250 free store every pile scored the same and
    // the nearest (north, drained by 10 workers) always won, so 10,43 grew 1574->2011 and decayed ~2 e/t
    for (const o of cands) { const left = amt(o) - (claimed[o.id] || 0), sc = left / (c.pos.getRangeTo(o) + 10); if (Math.min(free, left) >= 50 && sc > bs) { bs = sc; t = o; } }
    c.memory.pt = t ? t.id : undefined;
  }
  if (!t) return false;
  // Misaki rule: deliver once over half full rather than walking to another pile
  if (!c.pos.isNearTo(t) && c.store[E] * 2 >= c.store.getCapacity()) { delete c.memory.pt; return false; }
  if (!c.pos.isNearTo(t)) go(c, t.pos.x, t.pos.y); else { if (t.amount !== undefined) c.pickup(t); else c.withdraw(t, E); delete c.memory.pt; }
  return true;
}
function toggle(c) {
  if (c.memory.w && c.store[E] === 0) { c.memory.w = false; delete c.memory.sk; delete c.memory.ft; }
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
// container sink after spawn/extensions/tower: while hub sites (non-wall) exist, the emptier of hub/ctl container; else ctl first
// sticky per load (memory.sk, cleared when empty) so a hauler never flips between the two mid-walk
function sink(room, c) {
  const free = s => (s && s.store.getFreeCapacity(E) > 0 ? s : null), was = free(c.memory.sk && Game.getObjectById(c.memory.sk));
  if (was) return was;
  const ctl = free(ctlCont()), hub = free(hubCont());
  const t = hub && room.find(FIND_MY_CONSTRUCTION_SITES, { filter: s => s.structureType !== STRUCTURE_WALL }).length && (!ctl || hub.store[E] < ctl.store[E]) ? hub : ctl || hub;
  c.memory.sk = t ? t.id : undefined; return t;
}
// 02:45 fill target sticky per trip (memory.ft) and one creep per extension: with a fresh closest-free pick every tick, Spawn2
// draining the TEMP_EXT ring by the spawn turned loaded w8hauler/w8rhauler around mid-walk to the hub strips (22,11 -> 16,10).
function fillTarget(c, tower) {
  const t0 = c.memory.ft && Game.getObjectById(c.memory.ft);
  if (t0 && t0.store && t0.store.getFreeCapacity(E) > 0) return t0;
  const taken = new Set();
  for (const o of c.room.find(FIND_MY_CREEPS)) if (o.id !== c.id && o.memory.ft) taken.add(o.memory.ft);
  const t = c.pos.findClosestByRange(FIND_MY_STRUCTURES, { filter: s => s.store && s.store.getFreeCapacity(E) > 0 && (s.structureType === STRUCTURE_SPAWN
    || (s.structureType === STRUCTURE_EXTENSION && !taken.has(s.id)) || (tower && s.structureType === STRUCTURE_TOWER && s.store.getFreeCapacity(E) > 200)) });
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
function wallJob(room, c) {
  const tgt = C.WALL_TARGET[room.controller.level] || 0;
  const ws = room.find(FIND_STRUCTURES, { filter: s => s.structureType === STRUCTURE_WALL && s.hits < tgt && C.SEAL.some(([x, y]) => s.pos.x === x && s.pos.y === y) });
  if (!ws.length) { if (c) delete c.memory.wt; return null; }
  const lo = _.min(ws, s => s.hits).hits;
  if (!c) return ws.find(s => s.hits === lo);
  const cur = c.memory.wt && ws.find(s => s.id === c.memory.wt);
  if (cur && cur.hits < lo + 500) return cur;
  const t = c.pos.findClosestByRange(ws.filter(s => s.hits < lo + 300));
  c.memory.wt = t.id; return t;
}
// ---- W47N7 remote (only while reserved by us) ----
const RM = C.REMOTE;
const LAY = require('./layout');
// w8filler: owns one v3b strip; refills from hub storage, walks its 1-tile-wide strip road, parks at the strip's filler stand
function fillerRun(c) {
  if (!home(c)) return;
  const S = LAY.STRIPS[c.memory.si | 0], st = c.room.storage;
  if (!S) return;
  if (c.store[E] === 0) { if (st) { if (!c.pos.isNearTo(st)) go(c, st.pos.x, st.pos.y); else c.withdraw(st, E); } return; }
  let t = c.memory.ft && Game.getObjectById(c.memory.ft);
  if (!t || t.store.getFreeCapacity(E) === 0) {
    const need = [];
    for (const [x, y] of S.ext) { const e = c.room.lookForAt(LOOK_STRUCTURES, x, y).find(s => s.structureType === STRUCTURE_EXTENSION); if (e && e.store.getFreeCapacity(E) > 0) need.push(e); }
    t = c.pos.findClosestByRange(need); c.memory.ft = t ? t.id : undefined;
  }
  if (!t) { if (c.store.getFreeCapacity(E) > 0 && st) { if (!c.pos.isNearTo(st)) go(c, st.pos.x, st.pos.y); else c.withdraw(st, E); return; } return go(c, S.fill[0], S.fill[1], 0); }
  if (!c.pos.isNearTo(t)) go(c, t.pos.x, t.pos.y); else { c.transfer(t, E); c.memory.ft = undefined; }
}
function rgo(c, x, y, r) { return c.moveTo(new RoomPosition(x, y, RM.room), { range: r, reusePath: 20 }); }
const R = {
  w8miner(c) {
    if (!home(c)) return;
    const S = C.SOURCES[c.memory.si | 0], [x, y] = S.stand;
    const src = Game.rooms[C.ROOM].lookForAt(LOOK_SOURCES, S.src[0], S.src[1])[0];
    // 22:05: learn the walk on first reaching the source (any adjacent tile). Measuring on the stand tile counted the overlap
    // spent harvesting beside the old miner, so the lead crept up every cycle (si1 146->157, replacement ~94 ticks early).
    if (src && !c.memory.arr && c.pos.isNearTo(src)) { c.memory.arr = Game.time; const o = Memory.ops = Memory.ops || {}; (o.w8lead = o.w8lead || {})[c.memory.si | 0] = Game.time - (c.memory.born || Game.time) - 3 * c.body.length; }
    if (c.pos.x !== x || c.pos.y !== y) {
      // stand taken (e.g. a cqminer from home still mining): harvest from any tile next to the source
      if (Game.rooms[C.ROOM].lookForAt(LOOK_CREEPS, x, y).length && src) return c.pos.isNearTo(src) ? c.harvest(src) : go(c, src.pos.x, src.pos.y, 1);
      c.memory.wk = 1; return go(c, x, y, 0);
    }
    const cont = c.pos.lookFor(LOOK_STRUCTURES).find(s => s.structureType === STRUCTURE_CONTAINER);
    if (cont && cont.hits < cont.hitsMax * 0.5 && c.store[E] > 0) return c.repair(cont);
    if (src) c.harvest(src);
  },
  w8hauler(c) {
    if (!home(c)) return; toggle(c);
    if (!c.memory.w) { if (!haulPick(c) && c.store[E] > 0) c.memory.w = true; return; }
    const room8 = Game.rooms[C.ROOM];
    const fed = hubFeed(room8) && room8.find(FIND_MY_CREEPS, { filter: x => x.memory.role === 'w8builder' && x.store.getFreeCapacity(E) >= 50 && nearHub(x, 8) })
      .sort((a, b) => a.store[E] - b.store[E])[0];
    const t = fillTarget(c, true) || fed || sink(room8, c) || room8.storage;
    // nothing to fill: hand it to the emptiest w8upgrader/w8builder; never drop on the ground (Misaki rule), else wait
    const k = t || Game.rooms[C.ROOM].find(FIND_MY_CREEPS, { filter: x => (x.memory.role === 'w8upgrader' || x.memory.role === 'w8builder')
      && x.store.getFreeCapacity(E) > 0 }).sort((a, b) => a.store[E] - b.store[E])[0];
    if (!k) return c.pos.inRangeTo(C.CTL[0], C.CTL[1], 4) || go(c, C.CTL[0], C.CTL[1], 4);
    if (k.structureType === STRUCTURE_CONTAINER && k.pos.x === C.CTL_CONT[0] && k.pos.y === C.CTL_CONT[1] && !c.pos.isNearTo(k)) {
      // unload from a reserved tile (never the 13,25 dead end); both taken: wait within 2 (a range-0 path to an occupied tile wandered off)
      const room = Game.rooms[C.ROOM], f = C.CTL_HAUL.find(([x, y]) => !room.lookForAt(LOOK_CREEPS, x, y).length);
      if (f) go(c, f[0], f[1], 0); else if (!c.pos.inRangeTo(k, 2)) go(c, k.pos.x, k.pos.y, 2);
      return;
    }
    if (!c.pos.isNearTo(k)) go(c, k.pos.x, k.pos.y); else { c.transfer(k, E); delete c.memory.ft; }
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
        if (c.store[E] && c.pos.inRangeTo(ctl, 3)) c.upgradeController(ctl);
        if (c.pos.x !== x || c.pos.y !== y) { if (c.store[E] || cont.store[E]) return go(c, x, y, 0); }
        else { if (c.store[E] < 2 * c.getActiveBodyparts(WORK) && cont.store[E]) c.withdraw(cont, E); /* CPU 21:20: refill only when ~2 ticks left (0.2/intent) */ if (c.store[E] || cont.store[E]) return; }
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
  w8filler(c) { fillerRun(c); },
  w8rminer(c) {
    const S = RM.sources[c.memory.si | 0], [x, y] = S.stand;
    if (c.room.name !== RM.room) return rgo(c, x, y, 0);
    const src = c.room.lookForAt(LOOK_SOURCES, S.src[0], S.src[1])[0];
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
    toggle(c);
    // one-off sign of W47N7 with home's text (22:21): only while it differs, one hauler at a time, then back to work
    if (c.room.name === RM.room && c.room.controller) {
      const SG = require('../../utils/sign'), ct = c.room.controller;
      if (SG.needs(ct, c.owner.username) && (c.memory.signer || !_.some(Game.creeps, x => x.memory.signer && x.memory.role === 'w8rhauler'))) {
        c.memory.signer = 1;
        if (c.pos.isNearTo(ct)) c.signController(ct, SG.SIGN); else return rgo(c, ct.pos.x, ct.pos.y, 1);
        return;
      } else if (c.memory.signer) delete c.memory.signer;
    }
    if (!c.memory.w) {
      if (c.room.name !== RM.room) return rgo(c, 25, 25, 20);
      const amt = o => (o.amount !== undefined ? o.amount : o.store[E]);
      const t = c.pos.findClosestByRange(c.room.find(FIND_DROPPED_RESOURCES, { filter: r => r.resourceType === E && r.amount >= 100 })
        .concat(c.room.find(FIND_STRUCTURES, { filter: s => s.structureType === STRUCTURE_CONTAINER && s.store[E] >= 200 })));
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
    if (!home(c)) return;
    const room = Game.rooms[C.ROOM];
    const t = fillTarget(c, false) || sink(room, c) || room.storage;
    if (!t) return go(c, C.CTL[0], C.CTL[1], 3);
    if (!c.pos.isNearTo(t)) go(c, t.pos.x, t.pos.y); else { c.transfer(t, E); delete c.memory.ft; }
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
    const all = c.room.find(FIND_MY_CONSTRUCTION_SITES);
    // north seal walls first (1 energy each, Misaki 17:08), x8-11 before x24-31; then the spawn/extension sites
    const seal = all.filter(s => s.structureType === STRUCTURE_WALL).sort((a, b) => (a.pos.x <= 11 ? 0 : 1) - (b.pos.x <= 11 ? 0 : 1));
    const site = seal[0] || c.pos.findClosestByRange(all);
    if (site) { if (!c.pos.inRangeTo(site, 3)) go(c, site.pos.x, site.pos.y, 3); else c.build(site); return; }
    // 19:31: urgent road/container repair (<10%; container 11,43 at 18% = 2k ticks of decay left pulled the builder off the walls) -> seal walls to WALL_TARGET[rcl], lowest first -> maintenance (<60%).
    // With maintenance first the lone 2W builder spent 180 ticks on container 26,11 (87k/250k) + 22 roads and no wall left 1 hit.
    const rr = f => c.pos.findClosestByRange(FIND_STRUCTURES, { filter: s => (s.structureType === STRUCTURE_CONTAINER || s.structureType === STRUCTURE_ROAD) && s.hits < s.hitsMax * f });
    const rep = rr(0.1) || wallJob(c.room, c) || rr(0.6);
    if (rep) {
      if (c.pos.inRangeTo(rep, 3)) { c.repair(rep); return; }
      if (c.store[E] < 20 && c.pos.getRangeTo(rep) > 6) { c.memory.w = false; getEnergy(c); return; } // don't walk a near-empty load across the room
      go(c, rep.pos.x, rep.pos.y, 3); return;
    }
    R.w8upgrader(c);
  },
};
// main.js dispatches roles[role].run(c): wrap (bare functions crashed every w8 creep with 'run is not a function')
module.exports = Object.fromEntries(Object.entries(R).map(([k, f]) => [k, { run: f }]));
