// W47N8 spawn-energy filler (Misaki 17:3x: "补能要贴合地形、智能补能、优先操作 ... 不要让 spawn 陷入能量等待").
// One w8filler (two once the hub holds > 2500) owns every hub-side spawn-energy structure. It idles FULL on POST (road 34,32,
// beside storage 35,32 and hub container 33,33), so a refill starts the tick the spawn draws energy.
// v3b strips are 3 wide (ext | road | ext): the filler walks the strip road from its hub-side end, one tile per tick, and
// transfers every tick to an adjacent needy extension. Each road tile touches up to 6 extensions (rows y-1..y+1 on both sides);
// it only stops while an extension it would leave behind (last road tile that touches it) still needs energy, and it turns
// back at the first tile that reaches the farthest needy one. Off-strip targets (hub ext 32,31, hub spawns, tower) are point
// stops. Spawn2 15,18 + its 5 temp extensions are the haulers' job; the filler goes there only when the spawn is waiting on
// energy and every hub structure is already full.
const C = require('./config'), L = require('./layout');
const E = 'energy', K = (x, y) => x * 50 + y, POST = [34, 32], TOWER_R = 8;
const cheb = (a, b) => Math.max(Math.abs(a[0] - b[0]), Math.abs(a[1] - b[1]));
const TEMP = new Set(L.TEMP_EXT.map(([x, y]) => K(x, y)));
const isS2 = s => s.structureType === STRUCTURE_SPAWN && s.pos.x === C.SPAWN[0] && s.pos.y === C.SPAWN[1];
// strip routes (static): road tiles in order; per extension the first/last road index touching it
const ROUTES = L.STRIPS.map(s => {
  const road = s.road.map(p => p.slice()), at = {};
  road.forEach(([x, y], i) => { at[K(x, y)] = i; });
  const ext = {};
  for (const e of s.ext) { const ix = road.map((r, i) => (cheb(r, e) <= 1 ? i : -1)).filter(i => i >= 0); if (ix.length) ext[K(e[0], e[1])] = [Math.min(...ix), Math.max(...ix)]; }
  return { road, at, ext };
});
const STRIP_OF = {}; ROUTES.forEach((r, i) => { for (const k in r.ext) STRIP_OF[k] = i; });
// entry end per strip: the end with the shorter walk from POST (PathFinder, refreshed every 1500 ticks; Chebyshev before that)
let entryT = -1e9, ENTRY = ROUTES.map(r => (cheb(r.road[0], POST) <= cheb(r.road[r.road.length - 1], POST) ? 0 : 1));
function entries(room) {
  if (Game.time - entryT < 1500 || typeof PathFinder === 'undefined' || !PathFinder.search) return ENTRY;
  entryT = Game.time;
  const from = new RoomPosition(POST[0], POST[1], C.ROOM), len = p => { const r = PathFinder.search(from, { pos: new RoomPosition(p[0], p[1], C.ROOM), range: 0 },
    { maxRooms: 1, plainCost: 2, swampCost: 10, roomCallback: () => obstacles(room) }); return r.incomplete ? 1e9 : r.cost; };
  ENTRY = ROUTES.map(r => (len(r.road[0]) <= len(r.road[r.road.length - 1]) ? 0 : 1));
  return ENTRY;
}
function obstacles(room) {
  const m = new PathFinder.CostMatrix();
  for (const s of room.find(FIND_STRUCTURES)) {
    if (s.structureType === STRUCTURE_ROAD) { if (!m.get(s.pos.x, s.pos.y)) m.set(s.pos.x, s.pos.y, 1); }
    else if (s.structureType !== STRUCTURE_CONTAINER && !(s.structureType === STRUCTURE_RAMPART && s.my)) m.set(s.pos.x, s.pos.y, 255);
  }
  return m;
}
// duty: hub-side extensions/spawns (+ towers), cached ids per room, rebuilt every 25 ticks
let dutyT = -1, DUTY = null;
function duty(room) {
  if (DUTY && Game.time - dutyT < 25 && DUTY.room === room.name) return DUTY;
  dutyT = Game.time;
  const D = { room: room.name, byKey: {}, strip: ROUTES.map(() => []), point: [], tower: [], cluster: [], cap: 0, n: 0 };
  for (const s of room.find(FIND_MY_STRUCTURES)) {
    const t = s.structureType, k = K(s.pos.x, s.pos.y);
    if (t === STRUCTURE_TOWER) { D.tower.push(s.id); D.byKey[k] = s.id; continue; }
    if (t !== STRUCTURE_EXTENSION && t !== STRUCTURE_SPAWN) continue;
    if (isS2(s) || TEMP.has(k)) { D.cluster.push(s.id); continue; }
    D.byKey[k] = s.id; D.cap += s.store.getCapacity ? s.store.getCapacity(E) : 50; D.n++;
    if (STRIP_OF[k] !== undefined && t === STRUCTURE_EXTENSION) D.strip[STRIP_OF[k]].push(s.id); else D.point.push(s.id);
  }
  DUTY = D; return D;
}
// hub duty (spawn/extensions the filler owns) still needs energy. 17:0x: towers wait only on these, not on Spawn2's far cluster
// (haulers' job), which kept energyAvailable < cap so towers were never topped up by the filler.
const hubNeedy = (room, D) => objs([].concat(...D.strip, D.point)).some(s => free(s) > 0);
const free = s => (s && s.store ? s.store.getFreeCapacity(E) : 0);
const needT = s => s.structureType === STRUCTURE_TOWER ? free(s) >= 300 : free(s) > 0;
const objs = ids => ids.map(id => Game.getObjectById(id)).filter(Boolean);
function source(room) {
  const st = room.storage, hc = room.lookForAt(LOOK_STRUCTURES, C.HUB_CONT[0], C.HUB_CONT[1]).find(s => s.structureType === STRUCTURE_CONTAINER);
  return [st, hc].filter(s => s && s.store[E] > 0); // 10-20 17:0x (Misaki): storage first, hub container only as fallback
}
const fillers = room => room.find(FIND_MY_CREEPS, { filter: c => c.memory.role === 'w8filler' });
// filler can do its job: alive (not spawning) and holding energy or with energy to draw (else haulers keep filling the hub)
let actT = -1, actV = false;
function active(room) {
  if (actT === Game.time) return actV; actT = Game.time; return (actV = active0(room));
}
function active0(room) {
  const fs = fillers(room).filter(c => !c.spawning);
  if (!fs.length) return false;
  return fs.some(c => c.store[E] >= 50) || source(room).reduce((a, s) => a + s.store[E], 0) >= 100;
}
const alive = room => fillers(room).some(c => !c.spawning);
const stock = room => source(room).reduce((a, s) => a + s.store[E], 0);
// storage + hub container buffer the filler draws from: one full hub refill + 200
const reserve = room => duty(room).cap + 200;
function body(e, room) {
  const k = Math.max(2, Math.min(12, Math.ceil((room ? duty(room).cap : 800) * 0.75 / 100), Math.floor(e / 150)));
  return Array(2 * k).fill(CARRY).concat(Array(k).fill(MOVE));
}
function want(room, cs) {
  if (!room.storage) return false;
  const D = duty(room); if (D.n < 6) return false;
  const k = D.cap > 2500 ? 2 : 1, lead = 3 * body(room.energyCapacityAvailable, room).length + 40;
  return cs.filter(c => c.memory.role === 'w8filler' && (c.spawning || c.ticksToLive > lead)).length < k;
}
// 10-21 03:3x patrol: vanilla moveTo treated the haulers parked on the 1-wide hub passage (32,29 / 33,33) as walls; the filler,
// holding 1050 with 29 of 30 extensions empty, walked strip 1 -> strip 2 entry 31,28 around the whole room (24,34 -> 16,32 ->
// 8,20 -> 24,14 -> 29,20, ~80 t vs 7 tiles) while the spawn sat at 150/1800. In-room moves now use move.to (road matrix, creeps
// ignored, swap/shove our own blocker from stuck 2), like the W47N8 haulers.
const MV = require('../../utils/move'), ND = { noDetour: true };
const go = (c, x, y, r) => (c.room.name === C.ROOM ? MV.to(c, x, y, r, ND) : c.moveTo(new RoomPosition(x, y, C.ROOM), { range: r, reusePath: 15, maxRooms: 1 }));
// leave index of an extension when sweeping strip i in direction d (0 = from road[0], 1 = from road[end])
const leave = (i, d, k) => { const a = ROUTES[i].ext[k]; return d ? -a[0] : a[1]; };
const reach = (i, d, k) => { const a = ROUTES[i].ext[k]; return d ? -a[1] : a[0]; };
function run(c) {
  if (c.room.name !== C.ROOM) return go(c, POST[0], POST[1], 0);
  const room = c.room, D = duty(room), m = c.memory, ent = entries(room);
  const others = fillers(room).filter(o => o.id !== c.id), taken = new Set(others.map(o => o.memory.fs).filter(x => x !== undefined));
  let held = c.store[E], did = false;
  const filled = {};
  const left = s => free(s) - (filled[s.id] || 0);
  // 1) transfer to the most urgent adjacent duty structure (the one I would leave behind first)
  if (held > 0) {
    let best = null, bs = 1e9;
    for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) {
      const k = K(c.pos.x + dx, c.pos.y + dy), id = D.byKey[k], s = id && Game.getObjectById(id);
      if (!s || !(s.structureType === STRUCTURE_TOWER ? free(s) >= 300 && !hubNeedy(room, D) : free(s) > 0)) continue;
      let sc = s.structureType === STRUCTURE_SPAWN ? -1e6 : s.structureType === STRUCTURE_TOWER ? 1e6 : 0;
      if (m.fs !== undefined && m.fs >= 0 && ROUTES[m.fs].ext[k]) sc += leave(m.fs, m.fd | 0, k) * 10;
      if (sc < bs) { bs = sc; best = s; }
    }
    if (best) { const a = Math.min(held, free(best)); if (c.transfer(best, E) === 0) { did = true; held -= a; filled[best.id] = a; require('./fillmeter').xfer(c, a); } }
  }
  if (c.ticksToLive < 15 && held > 0 && room.storage) { if (!did && c.pos.isNearTo(room.storage)) c.transfer(room.storage, E); else go(c, room.storage.pos.x, room.storage.pos.y, 1); return; }
  // 2) top up whenever beside the storage / hub container (withdraw and move can share a tick)
  const src = source(room).filter(s => c.pos.isNearTo(s))[0];
  if (!did && src && c.store.getFreeCapacity(E) > 0) { c.withdraw(src, E); delete m.fm; held = Math.min(c.store.getCapacity(), held + src.store[E]); }
  // 3) sweeping a strip
  if (m.fs !== undefined && m.fs >= 0) {
    const i = m.fs, d = m.fd | 0, R = ROUTES[i], needy = objs(D.strip[i]).filter(s => left(s) > 0);
    if (!needy.length || held <= 0) { delete m.fs; delete m.fr; }
    else {
      const idx = R.at[K(c.pos.x, c.pos.y)], pos = idx === undefined ? undefined : (d ? -idx : idx);
      if (pos === undefined) { const e = R.road[d ? R.road.length - 1 : 0]; return go(c, e[0], e[1], 0); }
      const kk = s => K(s.pos.x, s.pos.y), ahead = needy.filter(s => leave(i, d, kk(s)) >= pos);
      if (ahead.some(s => leave(i, d, kk(s)) === pos)) return; // one here would be left behind: stay (one transfer per tick)
      const far = ahead.length ? Math.max(...ahead.map(s => reach(i, d, kk(s)))) : -1e9;
      if (far > pos) { const n = R.road[d ? -(pos + 1) : pos + 1]; return c.move(c.pos.getDirectionTo(n[0], n[1])); }
      if (ahead.length) return; // the rest is beside me already: finish here (walking on reaches nothing new)
      if (ahead.length < needy.length) { m.fd = 1 - d; m.fr = (m.fr | 0) + 1; if (m.fr < 3) return run(c); } // drained behind me meanwhile: sweep back
      delete m.fs;
    }
  }
  if (m.fs === 'c') { // Spawn2 cluster backup
    const t = objs(D.cluster).filter(s => left(s) > 0).sort((a, b) => c.pos.getRangeTo(a) - c.pos.getRangeTo(b))[0];
    if (t && held > 0) { if (!c.pos.isNearTo(t)) { require('./fillmeter').walk(c); go(c, t.pos.x, t.pos.y, 1); } else if (!did) { const a = Math.min(held, free(t)); if (c.transfer(t, E) === 0) require('./fillmeter').xfer(c, a); } return; }
    delete m.fs;
  }
  // 4) next job: nearest needy strip entry or point; out of energy -> POST
  if (held < 50) {
    delete m.fs;
    // 17:5x fallback (patrol: storage 66 / hub 63 while source cont 26,11 held 1536): buffer empty -> fetch from the fullest container
    if (!source(room).length && room.energyAvailable < room.energyCapacityAvailable) {
      const k = room.find(FIND_STRUCTURES, { filter: s => s.structureType === STRUCTURE_CONTAINER && s.store[E] >= 300 && !(s.pos.x === C.CTL_CONT[0] && s.pos.y === C.CTL_CONT[1]) })
        .sort((a, b) => b.store[E] - a.store[E])[0];
      if (k) { if (c.pos.isNearTo(k)) c.withdraw(k, E); else go(c, k.pos.x, k.pos.y, 1); return; }
    }
    return c.pos.x === POST[0] && c.pos.y === POST[1] ? undefined : go(c, POST[0], POST[1], 0);
  }
  const jobs = [];
  ROUTES.forEach((R, i) => { if (taken.has(i)) return; const n = objs(D.strip[i]).filter(s => left(s) > 0); if (!n.length) return;
    const e = R.road[ent[i] ? R.road.length - 1 : 0]; jobs.push({ i, d: ent[i], cost: c.pos.getRangeTo(e[0], e[1]), e }); });
  for (const s of objs(D.point)) if (left(s) > 0) jobs.push({ p: s, cost: c.pos.getRangeTo(s) - 1 });
  // tower last: only with the spawn energy full. 19:5x: core towers only (<= TOWER_R of POST): RCL5 tower 24,8 is ~23 road tiles away
  // (~50 t round trip with the hub unattended); it is fed from source A's container 26,11 (roles.js northFeed)
  if (!jobs.length) for (const s of objs(D.tower)) if (free(s) >= 300 && cheb([s.pos.x, s.pos.y], POST) <= TOWER_R) jobs.push({ p: s, cost: c.pos.getRangeTo(s) });
  const j = jobs.reduce((a, x) => (!a || x.cost < a.cost ? x : a), null); // (no lodash: 3.10 in game, 4 in tests)
  if (j) {
    // short on energy for the job and beside the source: the withdraw above already ran; just go
    if (j.p) { if (!c.pos.isNearTo(j.p)) { require('./fillmeter').walk(c); go(c, j.p.pos.x, j.p.pos.y, 1); } return; }
    m.fs = j.i; m.fd = j.d; m.fr = 0; require('./fillmeter').walk(c);
    if (c.pos.x === j.e[0] && c.pos.y === j.e[1]) return; // already on the entry: next tick sweeps
    return go(c, j.e[0], j.e[1], 0);
  }
  // hub full: Spawn2 cluster only while the spawn waits on energy and no hauler is heading there
  const fm = Memory.ops && Memory.ops.w8fm, waiting = fm && fm.wc && Game.time - fm.wc[2] >= 3;
  // 10-20 17:0x (Misaki): the filler stays on the hub (it walked to 8,20 holding 850 while hub extensions were empty); Spawn2's
  // cluster is the haulers' job and energyOrder() draws it last
  if (C.FILL_CLUSTER && waiting && !others.some(o => o.memory.fs === 'c')) {
    const cl = objs(D.cluster).filter(s => free(s) > 0), claimed = new Set(room.find(FIND_MY_CREEPS, { filter: o => o.memory.ft }).map(o => o.memory.ft));
    if (cl.some(s => !claimed.has(s.id))) { m.fs = 'c'; return; }
  }
  // 23:4x strategy: idle hub-link ferry (dormant until HUB_LINK built). Mirror home queen.standby —
  // when hub duty is full and storage ≥ LEAN_SOFT, top the hub link so linkRun can push hub→ctl
  // whenever ctl battery dips (Overmind UpgradeSite requests when link <200 / battery <50%).
  // Hub link 33,34 is range-2 from POST 34,32 — one step to 33,33/34,33 then transfer.
  {
    const [hx, hy] = (L.ORDER.link && L.ORDER.link[0]) || [33, 34];
    const hubL = room.lookForAt(LOOK_STRUCTURES, hx, hy).find(s => s.structureType === STRUCTURE_LINK);
    const storE = room.storage && room.storage.store ? (room.storage.store[E] || 0) : 0;
    if (hubL && storE >= 25000) {
      const freeL = hubL.store.getFreeCapacity ? hubL.store.getFreeCapacity(E) : Math.max(0, 800 - (hubL.store[E] || 0));
      let bat = 0;
      const cc = room.lookForAt(LOOK_STRUCTURES, C.CTL_CONT[0], C.CTL_CONT[1]).find(s => s.structureType === STRUCTURE_CONTAINER);
      if (cc && cc.store) bat += cc.store[E] || 0;
      const [lx, ly] = C.CTL_LINK || [13, 25];
      const cl = room.lookForAt(LOOK_STRUCTURES, lx, ly).find(s => s.structureType === STRUCTURE_LINK);
      if (cl && cl.store) bat += cl.store[E] || 0;
      // Fill when ctl battery thin OR hub link empty enough to accept a full SEND (200+)
      if ((bat < 800 || (hubL.store[E] || 0) < 200) && freeL >= 100) {
        if (held > 0) {
          if (c.pos.isNearTo(hubL)) { c.transfer(hubL, E); return; }
          return go(c, hx, hy, 1);
        }
        // draw from storage at POST then walk to hub link
        if (room.storage && c.pos.isNearTo(room.storage) && c.store.getFreeCapacity(E) > 0) {
          c.withdraw(room.storage, E); return;
        }
        if (c.pos.x !== POST[0] || c.pos.y !== POST[1]) return go(c, POST[0], POST[1], 0);
      }
    }
  }
  // idle: refill to full at POST
  if (c.store.getFreeCapacity(E) > 0 && !src && source(room).length) return go(c, POST[0], POST[1], 0);
  if (c.pos.x !== POST[0] || c.pos.y !== POST[1]) go(c, POST[0], POST[1], 0);
}
module.exports = { run, want, body, active, alive, stock, reserve, duty, ROUTES, POST, ENTRY: () => ENTRY, isDuty: (room, s) => s.structureType !== STRUCTURE_TOWER && duty(room).byKey[K(s.pos.x, s.pos.y)] === s.id };
