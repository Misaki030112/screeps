// Priority / intent seam (docs/COMMANDER.md). rank() is pure: the same signals always
// produce the same ordered duties. Live creeps are not steered unless a commander
// duty order is addressed to them (why: 'cmd'). Memory.cmd.steer only stamps an
// advisory c._duty for this tick — it does not change peacetime scripts.
// No Memory.ops / raidOrder / softCap writes. No room.find on the hot path.
const cmd = require('./cmd');

const MIL = {
  guard: 1, defender: 1, w8defender: 1, w8guard: 1, w8healer: 1, raid9: 1, probe: 1,
  cqsquad: 1, cqbreaker: 1, cqworker: 1, cqhauler: 1, cqatk: 1, cqminer: 1, cqrh: 1, cqquad: 1,
};
function family(role) { return MIL[role] ? 'mil' : 'econ'; }

// Base weights. rank() then adds realtime modifiers and drops duties whose `when` is false.
const CATALOG = {
  econ: [
    { duty: 'flee', w: 100, when: s => s.threat >= 3 && !s.combatBody },
    { duty: 'fillSpawn', w: 90, when: s => s.spawnPressure },
    { duty: 'fillTower', w: 80, when: s => s.threat >= 1 || s.remoteDefense },
    { duty: 'bank', w: 70, when: s => s.floor === 'crash' || s.floor === 'under' || (s.softCap && s.floor === 'band') },
    { duty: 'haul', w: 50, when: () => true },
    { duty: 'repair', w: 40, when: s => s.repairDebt && !s.war && s.floor !== 'crash' },
    { duty: 'lab', w: 25, when: s => s.labs && !s.spawnPressure && !s.war && s.floor !== 'crash' && s.floor !== 'under' },
    { duty: 'upgrade', w: 10, when: s => !s.softCap && !s.war && !s.bucketLow && s.floor === 'ok' },
  ],
  mil: [
    { duty: 'kite', w: 100, when: s => s.hurt },
    { duty: 'focus', w: 90, when: s => s.threat >= 2 || s.war },
    { duty: 'hold', w: 70, when: s => s.remoteDefense || s.threat === 1 },
    { duty: 'idle', w: 10, when: s => s.threat === 0 && !s.war && !s.remoteDefense },
  ],
};

function rank(role, signals) {
  const s = signals || {};
  const rows = CATALOG[family(role)] || CATALOG.econ;
  const out = [];
  for (let i = 0; i < rows.length; i++) {
    const row = rows[i];
    if (!row.when(s)) continue;
    let w = row.w;
    if (row.duty === 'fillSpawn' && s.spawnHot) w += 20;
    if (row.duty === 'fillTower' && s.threat >= 2) w += 15;
    if (row.duty === 'fillTower' && s.remoteDefense) w += 10;
    if (row.duty === 'bank' && s.floor === 'crash') w += 20;
    if (row.duty === 'bank' && s.softCap) w += 10;
    if (row.duty === 'focus' && (s.war || s.threat >= 3)) w += 10;
    if (row.duty === 'hold' && s.remoteDefense && s.threat < 2) w += 15;
    out.push({ duty: row.duty, w: w, why: row.duty, i: i });
  }
  out.sort((a, b) => b.w - a.w || a.i - b.i);
  return out;
}
function pick(role, signals) {
  const rows = rank(role, signals);
  return rows[0] || { duty: family(role) === 'mil' ? 'idle' : 'haul', w: 0, why: 'default', i: 99 };
}

function energy(store) {
  if (!store) return 0;
  if (typeof RESOURCE_ENERGY !== 'undefined' && store[RESOURCE_ENERGY]) return store[RESOURCE_ENERGY];
  return store.energy || 0;
}
function warOn(ops, now) {
  const P = ops && ops.w47n9; if (!P) return false;
  if (P.pauseCivilians === false) return false;
  if (P.pauseCivilians === true) return true;
  return P.on === true && !P.safe && !P.garrison && !P.flee && !(P.safeUntil && now < P.safeUntil);
}
function threatLevel(room, ops, now) {
  if (!room) return 0;
  const mem = room.memory || {};
  const th = mem.threat8;
  if (th && th.inBase && now - (th.t || 0) < 5) return 3;
  if (mem.focus) return 2;
  if (th && now - (th.t || 0) < 5) return 2;
  if (typeof ops.w8threat === 'number' && now - ops.w8threat < 1500) return 2;
  if (ops.w8roster && now - (ops.w8roster.t || 0) < 20) return 1;
  if (typeof ops.w8invN === 'number' && now - ops.w8invN < 60) return 1;
  return 0;
}
function remoteDefense(ops, remote, now) {
  if (ops.w8roster && now - (ops.w8roster.t || 0) < 20) return true;
  if (!remote) return false;
  for (const k in remote) {
    const st = remote[k] && remote[k].th && remote[k].th.st;
    if (st === 'DEFEND' || st === 'THREAT') return true;
  }
  return false;
}
function floorOf(room) {
  if (!room || !room.storage || !room.storage.store) return 'ok';
  const stor = energy(room.storage.store);
  if (stor < 5000) return 'crash';
  if (stor < 15000) return 'under';
  if (stor < 25000) return 'band';
  return 'ok';
}
let roomTick = -1, roomName = '', roomBase = null;
function roomSignals(room) {
  const now = (typeof Game !== 'undefined' && Game && Game.time) || 0;
  const name = (room && room.name) || '';
  if (roomTick === now && roomName === name && roomBase) return roomBase;
  const ops = (typeof Memory !== 'undefined' && Memory && Memory.ops) || {};
  const day = ops.w8day || {};
  const cap = (room && room.energyCapacityAvailable) || 0;
  const avail = (room && room.energyAvailable) || 0;
  const ratio = cap > 0 ? avail / cap : 1;
  const remote = (typeof Memory !== 'undefined' && Memory && Memory.remote) || null;
  roomTick = now; roomName = name;
  roomBase = {
    threat: threatLevel(room, ops, now),
    war: warOn(ops, now),
    softCap: !!(day.softCap2 || day.threatSoft),
    floor: floorOf(room),
    spawnPressure: cap > 0 && ratio < 0.5,
    spawnHot: cap > 0 && ratio < 0.25,
    remoteDefense: remoteDefense(ops, remote, now),
    labs: !!(ops.labs && typeof ops.labs === 'object' && Object.keys(ops.labs).length),
    repairDebt: (day.contLow > 0) || (day.roadCrit > 0),
    bucketLow: typeof Game !== 'undefined' && Game && Game.cpu && Game.cpu.bucket < 2000,
  };
  return roomBase;
}
function signals(c) {
  const base = roomSignals(c && c.room);
  const s = Object.assign({}, base);
  const hits = c && c.hits, max = (c && c.hitsMax) || hits || 1;
  s.hurt = !!(hits && max && hits < max * 0.6);
  let combat = false;
  if (c && c.getActiveBodyparts) {
    try {
      const g = p => c.getActiveBodyparts(p) || 0;
      combat = g(typeof ATTACK !== 'undefined' ? ATTACK : 'attack') + g(typeof RANGED_ATTACK !== 'undefined' ? RANGED_ATTACK : 'ranged_attack') + g(typeof HEAL !== 'undefined' ? HEAL : 'heal') > 0;
    } catch (e) { combat = false; }
  }
  s.combatBody = combat;
  return s;
}

function stamp(c) {
  if (!c || !cmd.armed()) return null;
  const t = (typeof Game !== 'undefined' && Game && Game.time) || 0;
  if (c._dutyTick === t && c._dutyWhy) return c._duty || null;
  const o = cmd.creepOrder(c.name);
  if (o && o.duty) { c._duty = o.duty; c._dutyWhy = 'cmd'; c._dutyTick = t; return o.duty; }
  const m = (typeof Memory !== 'undefined' && Memory && Memory.cmd) || {};
  if (!m.steer) { c._dutyTick = t; return null; }
  const top = pick(c.memory && c.memory.role, signals(c));
  c._duty = top.duty; c._dutyWhy = 'steer'; c._dutyTick = t;
  return top.duty;
}

const E = () => (typeof RESOURCE_ENERGY !== 'undefined' ? RESOURCE_ENERGY : 'energy');
function carry(c) { return energy(c && c.store); }
function near(c, obj) {
  if (!c || !c.pos || !obj) return false;
  const p = obj.pos || obj;
  if (c.pos.isNearTo) return c.pos.isNearTo(obj.pos ? obj : p);
  if (c.pos.getRangeTo) return c.pos.getRangeTo(p) <= 1;
  return Math.max(Math.abs(c.pos.x - p.x), Math.abs(c.pos.y - p.y)) <= 1;
}
function step(c, obj, range) {
  if (!c.moveTo) return;
  const dest = obj.pos || obj;
  c.moveTo(dest, { range: range == null ? 1 : range, reusePath: 8, maxRooms: 1 });
}
function closest(c, list) {
  if (!list || !list.length) return null;
  if (c.pos && c.pos.findClosestByRange) return c.pos.findClosestByRange(list);
  return list[0];
}
function deliver(c, dest) {
  if (!dest) return false;
  if (near(c, dest)) { if (c.transfer) c.transfer(dest, E()); }
  else step(c, dest, 1);
  return true;
}
function structs(c, pred) {
  if (!c.room || !c.room.find || typeof FIND_MY_STRUCTURES === 'undefined') return [];
  const all = c.room.find(FIND_MY_STRUCTURES) || [];
  return all.filter(pred);
}
function runDuty(c, o) {
  const duty = (o && o.duty) || c._duty;
  if (duty === 'idle') { if (o && o.say && c.say) c.say(String(o.say).slice(0, 10)); return true; }
  if (duty === 'hold' || duty === 'kite' || duty === 'flee') {
    const pos = o && o.pos;
    if (pos && c.moveTo) {
      const room = pos.room || pos.roomName;
      const dest = room && c.room && room !== c.room.name && typeof RoomPosition === 'function'
        ? new RoomPosition(pos.x, pos.y, room) : pos;
      const here = !room || !c.room || room === c.room.name;
      const r = o.range == null ? (duty === 'flee' ? 3 : 0) : o.range;
      if (!(here && c.pos && c.pos.getRangeTo && c.pos.getRangeTo(dest) <= r)) c.moveTo(dest, { range: r, reusePath: 8, maxRooms: here ? 1 : 16 });
      return true;
    }
    if (duty === 'flee' || duty === 'kite') {
      let sp = null;
      if (c.room && c.room.find && typeof FIND_MY_SPAWNS !== 'undefined') sp = (c.room.find(FIND_MY_SPAWNS) || [])[0];
      if (sp) { step(c, sp, 3); return true; }
    }
    if (duty === 'hold') return true;
    return false;
  }
  if (!carry(c)) return false; // let the role script pick up; the duty order is still live next tick
  if (duty === 'fillSpawn') {
    const tgt = o && o.id && typeof Game !== 'undefined' && Game.getObjectById && Game.getObjectById(o.id);
    const SPAWN = typeof STRUCTURE_SPAWN !== 'undefined' ? STRUCTURE_SPAWN : 'spawn';
    const EXT = typeof STRUCTURE_EXTENSION !== 'undefined' ? STRUCTURE_EXTENSION : 'extension';
    const dest = tgt || closest(c, structs(c, s => (s.structureType === SPAWN || s.structureType === EXT) && s.store && s.store.getFreeCapacity && s.store.getFreeCapacity(E()) > 0));
    return deliver(c, dest);
  }
  if (duty === 'fillTower') {
    const tgt = o && o.id && typeof Game !== 'undefined' && Game.getObjectById && Game.getObjectById(o.id);
    const TOWER = typeof STRUCTURE_TOWER !== 'undefined' ? STRUCTURE_TOWER : 'tower';
    const dest = tgt || closest(c, structs(c, s => s.structureType === TOWER && s.store && energy(s.store) < 900 && s.store.getFreeCapacity && s.store.getFreeCapacity(E()) > 0));
    return deliver(c, dest);
  }
  if (duty === 'bank') {
    const st = c.room && c.room.storage;
    return deliver(c, st);
  }
  // focus / haul / repair / lab / upgrade: the role script already knows how. Duty is advisory.
  return false;
}
function obey(c) {
  if (!c || !cmd.armed()) return false;
  if (!c._dutyWhy) stamp(c);
  if (c._dutyWhy !== 'cmd') return false;
  const t = (typeof Game !== 'undefined' && Game && Game.time) || 0;
  if (c._dutyRan === t) return !!c._dutyHeld;
  c._dutyRan = t;
  const o = cmd.creepOrder(c.name) || { duty: c._duty };
  if (o.act) { c._dutyHeld = false; return false; } // concrete act belongs to cmd.consumeCreep
  c._dutyHeld = runDuty(c, o) === true;
  return c._dutyHeld;
}

function resetCache() { roomTick = -1; roomName = ''; roomBase = null; }
module.exports = {
  MIL, CATALOG, family, rank, pick, signals, roomSignals, stamp, obey, runDuty,
  warOn, threatLevel, floorOf, resetCache,
};
