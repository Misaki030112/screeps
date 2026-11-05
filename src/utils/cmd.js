// Commander overlay (docs/COMMANDER.md). Red Alert style: while an order is live the
// unit obeys it; release / disarm / TTL hands the unit back to its role script.
// Peacetime cost is one falsy check (Memory.cmd absent or .on off). This module never
// writes Memory.ops, raidOrder, softCap, or role targets.
const DEFAULT_TTL = 200;
const OK = 0;

function time() { return (typeof Game !== 'undefined' && Game && Game.time) || 0; }
function root() {
  if (typeof Memory === 'undefined' || !Memory) return null;
  return Memory.cmd || null;
}
function armed() { const m = root(); return !!(m && m.on); }

// Live: explicitly on, and either sticky or still inside until / at+ttl.
function live(o, now) {
  if (!o || !o.on) return false;
  if (o.sticky) return true;
  const t = now == null ? time() : now;
  if (typeof o.until === 'number') return t < o.until;
  if (typeof o.ttl === 'number' && typeof o.at === 'number') return t < o.at + o.ttl;
  return false;
}
// Expired orders are deleted. Paused entries (on: 0) are kept so arm() can resume them.
function dead(o, now) {
  if (!o || o.sticky) return false;
  if (!o.on) return false;
  const t = now == null ? time() : now;
  if (typeof o.until === 'number') return t >= o.until;
  if (typeof o.ttl === 'number' && typeof o.at === 'number') return t >= o.at + o.ttl;
  return true;
}
let swept = -1, gen = 0;
function bump() { gen++; }
function sweep(now) {
  const m = root(); if (!m) return 0;
  const t = now == null ? time() : now;
  let n = 0;
  for (const slot of ['c', 's']) {
    const bag = m[slot]; if (!bag) continue;
    for (const k in bag) if (dead(bag[k], t)) { delete bag[k]; n++; }
  }
  return n;
}
function begin(now) {
  if (!armed()) return;
  const t = now == null ? time() : now;
  if (swept === t) return;
  swept = t; sweep(t);
}

function ensure() {
  if (typeof Memory === 'undefined' || !Memory) return null;
  const m = Memory.cmd || (Memory.cmd = { v: 1, on: 0, c: {}, s: {} });
  if (!m.c) m.c = {};
  if (!m.s) m.s = {};
  if (!m.v) m.v = 1;
  return m;
}
function copyOrder(src, now) {
  const o = { on: 1, at: now, by: src.by || 'cmd' };
  for (const k of ['duty', 'act', 'id', 'res', 'say', 'amount', 'range', 'in1', 'in2', 'name', 'role', 'heal', 'note', 'room']) {
    if (src[k] != null && src[k] !== '') o[k] = src[k];
  }
  if (src.pos) o.pos = { room: src.pos.room || src.pos.roomName, x: src.pos.x | 0, y: src.pos.y | 0 };
  if (src.fallback) o.fallback = 1;
  if (src.once) o.once = 1;
  if (src.allow) o.allow = 1;
  if (Array.isArray(src.body)) o.body = src.body.slice();
  if (src.mem && typeof src.mem === 'object') o.mem = src.mem;
  if (src.sticky) o.sticky = 1;
  else {
    const ttl = src.ttl > 0 ? src.ttl | 0 : DEFAULT_TTL;
    o.ttl = ttl;
    o.until = typeof src.until === 'number' ? src.until : now + ttl;
  }
  return o;
}
function issue(slot, key, order, now) {
  const m = ensure(); if (!m || !key) return null;
  const t = now == null ? time() : now;
  const o = copyOrder(order || {}, t);
  m.on = 1; m.at = t; m.by = o.by;
  m[slot][key] = o;
  swept = -1; // a new order must not be swept as if this tick already finished
  bump();
  return o;
}
function bagOrder(slot, key, now) {
  const m = root(); if (!m || !m.on) return null;
  const bag = m[slot]; if (!bag) return null;
  const o = bag[key]; if (!o) return null;
  const t = now == null ? time() : now;
  if (!live(o, t)) { if (dead(o, t)) delete bag[key]; return null; }
  return o;
}
function creepOrder(name, now) { return name ? bagOrder('c', name, now) : null; }
function structOrder(id, now) { return id ? bagOrder('s', id, now) : null; }

function releaseCreep(name) {
  const m = root(); if (!m || !m.c || !m.c[name]) return false;
  delete m.c[name];
  const mem = Memory.creeps && Memory.creeps[name];
  if (mem && mem._cmd) delete mem._cmd;
  bump();
  return true;
}
function releaseStruct(id) {
  const m = root(); if (!m || !m.s || !m.s[id]) return false;
  delete m.s[id]; bump(); return true;
}
function releaseAll() {
  const m = root(); if (!m) return 0;
  const n = Object.keys(m.c || {}).length + Object.keys(m.s || {}).length;
  m.c = {}; m.s = {};
  const creeps = Memory.creeps;
  if (creeps) for (const k in creeps) if (creeps[k] && creeps[k]._cmd) delete creeps[k]._cmd;
  bump();
  return n;
}
function disarm() { const m = root(); if (!m) return false; m.on = 0; bump(); return true; }
function arm() { const m = ensure(); if (!m) return false; m.on = 1; swept = -1; bump(); return true; }

function roomPos(x, y, room) {
  if (typeof RoomPosition === 'function') return new RoomPosition(x, y, room);
  return { x: x, y: y, roomName: room };
}
function dist(from, to) {
  if (!from || !to) return 999;
  const tx = to.pos || to;
  if (from.getRangeTo) {
    try { return from.getRangeTo(tx); } catch (e) { /* fall through */ }
  }
  if (from.x == null || tx.x == null) return 999;
  return Math.max(Math.abs(from.x - tx.x), Math.abs(from.y - tx.y));
}
function sameRoom(c, pos) {
  const room = pos && (pos.roomName || pos.room);
  return !room || !c.room || room === c.room.name;
}
function go(c, pos, range) {
  if (!pos || !c.moveTo) return false;
  const room = pos.roomName || pos.room;
  const dest = room && !sameRoom(c, pos) ? roomPos(pos.x, pos.y, room) : (pos.pos || pos);
  if (sameRoom(c, pos) && dist(c.pos, dest) <= range) return false;
  c.moveTo(dest, { range: range, reusePath: 8, maxRooms: room && !sameRoom(c, pos) ? 16 : 1 });
  return true;
}
function say(c, o) { if (o && o.say && c.say) c.say(String(o.say).slice(0, 10)); }
function obj(id) { return id && typeof Game !== 'undefined' && Game.getObjectById && Game.getObjectById(id); }
function finish(slot, key, o, code) { if (o.once && code === OK) { if (slot === 'c') releaseCreep(key); else releaseStruct(key); } }
function sideHeal(c, o) { if (o.heal === 'self' && c.heal && c.hits < c.hitsMax) c.heal(c); }

const RES = () => (typeof RESOURCE_ENERGY !== 'undefined' ? RESOURCE_ENERGY : 'energy');
const NEAR = { attack: 1, heal: 1, transfer: 1, withdraw: 1, pickup: 1, harvest: 1, repair: 1, build: 1, dismantle: 1, upgrade: 1 };
const RANGED = { rangedAttack: 3, rangedHeal: 3 };

function work(c, o, method, range) {
  const tgt = method === 'upgrade' && !o.id && c.room ? c.room.controller : obj(o.id);
  say(c, o);
  if (!tgt || typeof c[method] !== 'function') return !o.fallback;
  if (range > 0 && dist(c.pos, tgt.pos || tgt) > range) { go(c, tgt.pos || tgt, range); sideHeal(c, o); return true; }
  const res = o.res || RES();
  let code;
  if (method === 'transfer' || method === 'withdraw') code = o.amount != null ? c[method](tgt, res, o.amount) : c[method](tgt, res);
  else code = c[method](tgt);
  finish('c', c.name, o, code);
  sideHeal(c, o);
  return true;
}
function execCreep(c, o) {
  const act = o.act;
  if (act === 'idle' || act === 'say') { say(c, o); sideHeal(c, o); return true; }
  if (act === 'hold' || act === 'move') {
    say(c, o);
    const pos = o.pos || ((obj(o.id) || {}).pos);
    if (!pos) return !o.fallback;
    const r = o.range == null ? (act === 'hold' ? 0 : 1) : o.range;
    if (!go(c, pos, r) && o.once) releaseCreep(c.name);
    sideHeal(c, o);
    return true;
  }
  if (act === 'drop') {
    say(c, o);
    if (typeof c.drop !== 'function') return !o.fallback;
    finish('c', c.name, o, o.amount != null ? c.drop(o.res || RES(), o.amount) : c.drop(o.res || RES()));
    sideHeal(c, o); return true;
  }
  if (act === 'rangedMassAttack') {
    say(c, o);
    if (typeof c.rangedMassAttack !== 'function') return !o.fallback;
    finish('c', c.name, o, c.rangedMassAttack());
    sideHeal(c, o); return true;
  }
  if (act === 'recycle') {
    say(c, o);
    let sp = obj(o.id);
    if (!sp && c.room && c.room.find && typeof FIND_MY_SPAWNS !== 'undefined') sp = (c.room.find(FIND_MY_SPAWNS) || [])[0];
    if (!sp) return !o.fallback;
    if (dist(c.pos, sp.pos || sp) <= 1 && sp.recycleCreep) finish('c', c.name, o, sp.recycleCreep(c));
    else go(c, sp.pos || sp, 1);
    return true;
  }
  if (NEAR[act]) return work(c, o, act, NEAR[act]);
  if (RANGED[act]) return work(c, o, act, o.range == null ? RANGED[act] : o.range);
  say(c, o.say ? o : { say: '?' });
  return !o.fallback;
}

function consumeCreep(c) {
  if (!c || !armed()) {
    if (c && c.memory && c.memory._cmd) delete c.memory._cmd;
    return false;
  }
  const t = time();
  if (c._cmdTick === t && c._cmdGen === gen && c._cmdExec === t) return !!c._cmdHeld;
  c._cmdTick = t; c._cmdGen = gen;
  begin(t);
  const o = creepOrder(c.name, t);
  c._cmdOrder = o;
  if (!o || !o.act) {
    if (c.memory && c.memory._cmd) delete c.memory._cmd;
    c._cmdHeld = false; c._cmdExec = t; return false;
  }
  const held = execCreep(c, o) !== false;
  c._cmdHeld = held; c._cmdExec = t;
  // once/release may have deleted the order inside exec; do not leave _cmd behind.
  if (held && creepOrder(c.name, t) && c.memory) c.memory._cmd = 1;
  else if (c.memory && c.memory._cmd) delete c.memory._cmd;
  return held;
}

function consumeStruct(obj0, run) {
  if (!obj0 || !armed()) return false;
  const t = time();
  if (obj0._cmdTick === t && obj0._cmdGen === gen && obj0._cmdExec === t) return !!obj0._cmdHeld;
  obj0._cmdTick = t; obj0._cmdGen = gen; begin(t);
  const o = structOrder(obj0.id, t);
  if (!o) { obj0._cmdHeld = false; obj0._cmdExec = t; return false; }
  const held = run(o) !== false;
  obj0._cmdHeld = held; obj0._cmdExec = t;
  return held;
}
function consumeTower(tower) {
  return consumeStruct(tower, o => {
    if (o.act === 'idle' || o.act === 'hold') return true;
    if (o.act === 'attack' || o.act === 'heal' || o.act === 'repair') {
      const tgt = obj(o.id);
      if (!tgt || typeof tower[o.act] !== 'function') return !o.fallback;
      finish('s', tower.id, o, tower[o.act](tgt));
      return true;
    }
    return !o.fallback;
  });
}
function consumeLink(link) {
  return consumeStruct(link, o => {
    if (o.act === 'idle' || o.act === 'hold') return true;
    if (o.act === 'transfer') {
      const to = obj(o.id);
      if (!to || typeof link.transferEnergy !== 'function') return !o.fallback;
      if (link.cooldown) return true;
      finish('s', link.id, o, link.transferEnergy(to, o.amount));
      return true;
    }
    return !o.fallback;
  });
}
// Lab: idle/hold suppresses runReaction. act 'react' needs explicit in1+in2. Never sets Memory.ops.labs.
function consumeLab(lab) {
  return consumeStruct(lab, o => {
    if (o.act === 'react') {
      const a = obj(o.in1), b = obj(o.in2);
      if (a && b && typeof lab.runReaction === 'function') finish('s', lab.id, o, lab.runReaction(a, b));
      return true;
    }
    if (o.act === 'idle' || o.act === 'hold') return true;
    return !o.fallback;
  });
}
// Spawn: idle/hold/unknown suppresses the auto queue. act 'spawn' only fires with allow:1 and an explicit body.
// This module never invents a combat body, a claim, or a safe-mode activation.
function consumeSpawn(spawn) {
  return consumeStruct(spawn, o => {
    if (o.act === 'recycle') {
      const creep = obj(o.id);
      if (creep && dist(spawn.pos, creep.pos || creep) <= 1 && spawn.recycleCreep) finish('s', spawn.id, o, spawn.recycleCreep(creep));
      return true;
    }
    if (o.act === 'spawn') {
      if (o.allow && Array.isArray(o.body) && o.body.length && typeof spawn.spawnCreep === 'function') {
        const mem = o.mem || { role: o.role || 'hauler', v2: 1 };
        finish('s', spawn.id, o, spawn.spawnCreep(o.body, o.name || ('cmd' + time()), { memory: mem }));
      }
      return true;
    }
    if (o.act === 'idle' || o.act === 'hold') return true;
    return !o.fallback;
  });
}
// Any live structure order yields automation. Terminal.send is NOT executed in this phase
// (no market, no extra resource sends) — the terminal simply waits.
function blocks(struct) {
  if (!struct || struct.id == null || !armed()) return false;
  begin();
  return !!structOrder(struct.id);
}

// One peacetime check. Act wins; a duty the seam knows how to do runs next.
// Does not write role memory, raidOrder, or Memory.ops.
function yieldCreep(c) {
  if (!c || !armed()) return false;
  if (consumeCreep(c)) return true;
  return require('./intent').obey(c) === true;
}
// True while a live act or duty is addressed to this creep, even if this tick fell through
// to the role (advisory duties such as focus). raid9 uses this to skip raidOrder.
function suppressed(c) {
  if (!c || !armed()) return false;
  const o = creepOrder(c.name);
  return !!(o && (o.act || o.duty));
}

function setMany(names, order, now) {
  const out = [];
  const list = Array.isArray(names) ? names : [];
  for (let i = 0; i < list.length; i++) if (issue('c', list[i], order, now)) out.push(list[i]);
  return out;
}
function squadNames(spec) {
  const creeps = (typeof Game !== 'undefined' && Game && Game.creeps) || {};
  if (typeof spec === 'function') {
    const names = [];
    for (const n in creeps) if (creeps[n] && spec(creeps[n])) names.push(n);
    return names;
  }
  if (!spec || typeof spec !== 'object') return [];
  if (!spec.role && !spec.home && !spec.kind && !spec.room) return [];
  const names = [];
  for (const n in creeps) {
    const c = creeps[n];
    if (!c || !c.memory) continue;
    if (spec.role && c.memory.role !== spec.role) continue;
    if (spec.kind && c.memory.kind !== spec.kind) continue;
    if (spec.home && (c.memory.home || (c.room && c.room.name)) !== spec.home) continue;
    if (spec.room && (!c.room || c.room.name !== spec.room)) continue;
    names.push(n);
  }
  return names;
}
function setSquad(spec, order, now) { return setMany(squadNames(spec), order, now); }
function releaseMany(names) {
  let n = 0;
  const list = Array.isArray(names) ? names : [];
  for (let i = 0; i < list.length; i++) if (releaseCreep(list[i])) n++;
  return n;
}

const OBS = () => (typeof STRUCTURE_OBSERVER !== 'undefined' ? STRUCTURE_OBSERVER : 'observer');
const NUK = () => (typeof STRUCTURE_NUKER !== 'undefined' ? STRUCTURE_NUKER : 'nuker');
const FAC = () => (typeof STRUCTURE_FACTORY !== 'undefined' ? STRUCTURE_FACTORY : 'factory');
const LAB = () => (typeof STRUCTURE_LAB !== 'undefined' ? STRUCTURE_LAB : 'lab');
const POW = () => (typeof STRUCTURE_POWER_SPAWN !== 'undefined' ? STRUCTURE_POWER_SPAWN : 'powerSpawn');

// observe(roomName). Target room is order.room, not a game object id.
function consumeObserver(obs) {
  return consumeStruct(obs, o => {
    if (o.act === 'idle' || o.act === 'hold') return true;
    if (o.act === 'observe') {
      const room = typeof o.room === 'string' ? o.room : null;
      if (!room || typeof obs.observe !== 'function') return !o.fallback;
      finish('s', obs.id, o, obs.observe(room));
      return true;
    }
    return !o.fallback;
  });
}
// launchNuke only with allow:1 and an explicit pos. Otherwise the nuker waits. Never picks a target.
function consumeNuker(nuker) {
  return consumeStruct(nuker, o => {
    if (o.act === 'idle' || o.act === 'hold') return true;
    if (o.act === 'launch') {
      if (!(o.allow && o.pos && typeof nuker.launchNuke === 'function')) return true;
      const pos = roomPos(o.pos.x, o.pos.y, o.pos.room || o.pos.roomName);
      finish('s', nuker.id, o, nuker.launchNuke(pos));
      return true;
    }
    return !o.fallback;
  });
}
// Factory production is not implemented. produce/idle/hold own the tick and call nothing.
function consumeFactory(fac) {
  return consumeStruct(fac, () => true);
}
// Power spawn processing is not implemented. Do not call processPower.
function consumePower(ps) {
  return consumeStruct(ps, () => true);
}
// Structures with no manager (observer, nuker, factory, labs outside the reaction) still
// obey while Memory.cmd is armed. Tower/link/spawn managers consume first; the per-tick
// cache makes a second pass a no-op. Not called when the overlay is off.
function runHeldStructures() {
  if (!armed()) return 0;
  begin();
  const bag = root().s;
  if (!bag) return 0;
  const t = time();
  let n = 0;
  for (const id in bag) {
    if (!live(bag[id], t)) continue;
    const s = obj(id);
    if (!s) continue;
    const k = s.structureType;
    let held = false;
    if (k === OBS()) held = consumeObserver(s);
    else if (k === NUK()) held = consumeNuker(s);
    else if (k === FAC()) held = consumeFactory(s);
    else if (k === POW()) held = consumePower(s);
    else if (k === LAB()) held = consumeLab(s);
    if (held) n++;
  }
  return n;
}

const api = {
  DEFAULT_TTL, OK, armed, live, dead, sweep, begin,
  creepOrder, structOrder,
  setCreep: (name, order, now) => issue('c', name, order, now),
  setStruct: (id, order, now) => issue('s', id, order, now),
  setMany, setSquad, squadNames, releaseMany,
  releaseCreep, releaseStruct, releaseAll, disarm, arm,
  yieldCreep, suppressed,
  consumeCreep, consumeTower, consumeLink, consumeLab, consumeSpawn, blocks,
  consumeObserver, consumeNuker, consumeFactory, consumePower, runHeldStructures,
};
if (typeof global !== 'undefined') global.CMD = api;
module.exports = api;
