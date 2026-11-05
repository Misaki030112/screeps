// One-off armed probe into W47N8 (BustJetter's reserved remote; plan /workspace/probe_w47n8_plan_cn.md, docs/PROBE.md).
// MANUALLY commanded via Memory.ops.probe.cmd (tools/probe.py), switchable any tick:
//   observe  roam the waypoint loop in W47N8 (never y<8, never W47N9/W48N9)
//   hold     stay at Memory.ops.probe.pos = {room,x,y} (default: our west exit side, W46N8 3,20)
//   steal    withdraw from W47N8 containers (south (11,43) first), carry home to our storage, repeat
//   attack   kill creeps of Memory.ops.probe.owner (default BustJetter) in W47N8: healers/fighters, then haulers/miners/reserver
//   retreat  full speed to W46N8, healing
//   guard    become the remote defender (roles/remote.js) patrolling W45N8+W45N7 until TTL
// Safety override (any cmd except guard): armed hostile out-damaging our heal, hits < 70%, or a hostile tower with energy -> retreat.
const ROOM = 'W47N8', HOME = 'W46N8', FORBID = new Set(['W47N9', 'W48N9', 'W48N8']);
const MIN_Y = 8, LOG_CAP = 200, HEAL_PER = 12;
const HOME_POS = { room: HOME, x: 3, y: 20 };
// [x, y, dwell] — (19,24)/(15,40) from the plan are walls; nearest open tiles used instead
const WAYPOINTS = [[47, 20, 0], [40, 16, 5], [29, 14, 5], [11, 24, 3], [12, 40, 5], [20, 35, 0], [30, 35, 0], [40, 30, 0], [46, 24, 0]];
const CONTAINERS = [[11, 43], [26, 11]];
const ATK_DMG = 30, RA_DMG = 10;
const BODY = () => [].concat(Array(4).fill(RANGED_ATTACK), Array(3).fill(HEAL), [CARRY], Array(8).fill(MOVE)); // 1800

const M = () => (Memory.ops = Memory.ops || {}, Memory.ops.probe = Memory.ops.probe || {});
function log(ev) { const P = M(); P.log = P.log || []; P.log.push(Object.assign({ t: Game.time }, ev)); if (P.log.length > LOG_CAP) P.log.splice(0, P.log.length - LOG_CAP); }
const act = (h, t) => h.body.filter(p => p.type === t && p.hits > 0).length;
const AB = { move: 'M', work: 'W', carry: 'C', attack: 'A', ranged_attack: 'R', heal: 'H', claim: 'K', tough: 'T' };
const bodyStr = h => _.map(_.countBy(h.body, 'type'), (n, t) => n + (AB[t] || t)).join('');
// damage per tick a hostile can deal to us (no boosts counted; boosted parts x4 noted in log)
function dps(h) { const boost = h.body.some(p => p.boost) ? 4 : 1; return (act(h, ATTACK) * ATK_DMG + act(h, RANGED_ATTACK) * RA_DMG) * boost; }
const armed = h => act(h, ATTACK) + act(h, RANGED_ATTACK) > 0;
// pure decision (unit-tested): reason string or null
function danger(me, hostiles, towers) {
  if (me.hits < me.hitsMax * 0.7) return 'hits<70%';
  if (towers.some(t => (t.store ? t.store[RESOURCE_ENERGY] : t.energy) >= 10)) return 'hostile tower';
  const heal = me.heal * HEAL_PER, d = hostiles.filter(armed).reduce((a, h) => a + dps(h), 0);
  if (d > heal) return `outgunned dps ${d} > heal ${heal}`;
  return null;
}
// pure target choice (unit-tested): healers > fighters > haulers > miners > reserver/claim > rest, then nearest, then lowest hits
function prio(h) { return act(h, HEAL) ? 0 : armed(h) ? 1 : act(h, CARRY) ? 2 : act(h, WORK) ? 3 : act(h, CLAIM) ? 4 : 5; }
function pickTarget(pos, hs) {
  const r = h => Math.max(Math.abs(h.pos.x - pos.x), Math.abs(h.pos.y - pos.y));
  return _.sortBy(hs, h => prio(h) * 1e6 + r(h) * 1e4 + h.hits)[0];
}
function matrixFor(rn, m) {
  if (FORBID.has(rn)) { for (let x = 0; x < 50; x++) for (let y = 0; y < 50; y++) m.set(x, y, 255); return m; }
  if (rn === ROOM) for (let x = 0; x < 50; x++) for (let y = 0; y < MIN_Y; y++) m.set(x, y, 255);
  return m;
}
function travel(c, rn, x, y, range = 1) {
  if (c.room.name === rn && c.pos.inRangeTo(x, y, range)) return true;
  c.moveTo(new RoomPosition(x, y, rn), { range, reusePath: 5, maxRooms: 3, costCallback: matrixFor, visualizePathStyle: undefined });
  return false;
}
function setCmd(cmd, why) { const P = M(); if (P.cmd !== cmd) { log({ ev: 'cmd', from: P.cmd, to: cmd, why }); P.cmd = cmd; } }

function run(c) {
  if (require('../utils/cmd').yieldCreep(c)) return;
  const P = M(), cmd = P.cmd || 'hold';
  P.name = c.name;
  // forbidden room (should never happen): step back south immediately
  if (FORBID.has(c.room.name)) { log({ ev: 'forbidden', room: c.room.name }); return travel(c, ROOM, 30, 20, 3); }
  const owner = P.owner || 'BustJetter';
  const hostiles = c.room.find(FIND_HOSTILE_CREEPS), towers = c.room.find(FIND_HOSTILE_STRUCTURES).filter(s => s.structureType === STRUCTURE_TOWER);
  // events: new hostiles, damage, cmd
  P.seen = P.seen || {};
  for (const h of hostiles) if (!P.seen[h.id]) { P.seen[h.id] = Game.time; log({ ev: 'hostile', id: h.id, owner: h.owner.username, name: h.name, body: bodyStr(h), boosted: h.body.some(p => p.boost) || undefined, pos: [h.pos.x, h.pos.y], room: c.room.name, ttl: h.ticksToLive }); }
  for (const id in P.seen) if (Game.time - P.seen[id] > 1500) delete P.seen[id];
  if (P.lastHits !== undefined && c.hits < P.lastHits) log({ ev: 'damage', dmg: P.lastHits - c.hits, hits: c.hits, pos: [c.pos.x, c.pos.y], room: c.room.name, near: hostiles.filter(armed).map(h => h.name) });
  P.lastHits = c.hits;
  if (P.tg) { const t = Game.getObjectById(P.tg.id); if (!t && P.tg.t === Game.time - 1 && P.tg.hits <= 60) log({ ev: 'kill', name: P.tg.name, body: P.tg.body }); if (!t) delete P.tg; }
  if (cmd !== P.lastCmd) { log({ ev: 'cmd', to: cmd }); P.lastCmd = cmd; }
  P.status = { room: c.room.name, pos: [c.pos.x, c.pos.y], hits: c.hits, hitsMax: c.hitsMax, cmd, ttl: c.ticksToLive, store: c.store.getUsedCapacity(), hostiles: hostiles.length, t: Game.time };
  if (cmd === 'guard') return toGuard(c);
  // self-heal every tick (cheap pre-heal when armed hostiles are near)
  if (c.hits < c.hitsMax || hostiles.some(h => armed(h) && c.pos.inRangeTo(h, 5))) c.heal(c);
  const why = danger({ hits: c.hits, hitsMax: c.hitsMax, heal: act(c, HEAL) }, hostiles.filter(h => h.owner.username !== 'Source Keeper'), towers);
  if (why && cmd !== 'retreat') { log({ ev: 'auto-retreat', why, room: c.room.name, pos: [c.pos.x, c.pos.y] }); P.auto = { why, t: Game.time }; setCmd('retreat', why); }
  const shoot = () => { const inR = hostiles.filter(h => c.pos.inRangeTo(h, 3) && (cmd === 'attack' || armed(h))); if (!inR.length) return; if (inR.length >= 2) c.rangedMassAttack(); else c.rangedAttack(inR[0]); };
  switch (P.cmd) {
    case 'retreat': shoot(); travel(c, HOME, 28, 24, 2); return; // inside tower cover
    case 'observe': return observe(c);
    case 'steal': return steal(c);
    case 'attack': return attack(c, hostiles.filter(h => h.owner.username === owner));
    default: { const p = P.pos && P.pos.x !== undefined ? Object.assign({ room: ROOM }, P.pos) : HOME_POS; return travel(c, p.room, p.x, p.y, 0); }
  }
}
function observe(c) {
  const P = M(); let i = (P.wi || 0) % WAYPOINTS.length; const [x, y, dwell] = WAYPOINTS[i];
  if (c.room.name === ROOM && c.pos.inRangeTo(x, y, 1)) {
    P.ww = P.ww || Game.time;
    if (Game.time - P.ww >= dwell) { P.wi = i + 1; delete P.ww; if (P.wi % WAYPOINTS.length === 0) log({ ev: 'loop-done' }); }
    return;
  }
  delete P.ww; travel(c, ROOM, x, y, 1);
}
function steal(c) {
  const P = M();
  if (c.store.getFreeCapacity() === 0) { const st = Game.rooms[HOME] && Game.rooms[HOME].storage; if (!st) return travel(c, HOME, 28, 24, 2);
    if (c.room.name === HOME && c.pos.isNearTo(st)) { const res = Object.keys(c.store)[0]; const n = c.store[res]; if (c.transfer(st, res) === OK) log({ ev: 'delivered', res, n }); return; }
    return travel(c, HOME, st.pos.x, st.pos.y, 1); }
  const pts = P.from ? [P.from] : CONTAINERS;
  if (c.room.name !== ROOM) return travel(c, ROOM, pts[0][0], pts[0][1], 1);
  const conts = pts.map(([x, y]) => c.room.lookForAt(LOOK_STRUCTURES, x, y).find(s => s.structureType === STRUCTURE_CONTAINER)).filter(s => s && s.store.getUsedCapacity() > 0);
  if (!conts.length) { if (c.store.getUsedCapacity()) { const st = Game.rooms[HOME].storage; return st && c.room.name === HOME && c.pos.isNearTo(st) ? c.transfer(st, Object.keys(c.store)[0]) : travel(c, HOME, st ? st.pos.x : 28, st ? st.pos.y : 24, 1); } log({ ev: 'steal-empty' }); setCmd('hold', 'containers empty'); P.pos = { room: ROOM, x: 40, y: 20 }; return; }
  const t = conts[0];
  if (!c.pos.isNearTo(t)) return travel(c, ROOM, t.pos.x, t.pos.y, 1);
  const res = t.store[RESOURCE_ENERGY] > 0 ? RESOURCE_ENERGY : Object.keys(t.store).find(r => t.store[r] > 0);
  const n = Math.min(t.store[res], c.store.getFreeCapacity());
  if (c.withdraw(t, res) === OK) { log({ ev: 'withdraw', res, n, from: [t.pos.x, t.pos.y] }); P.stolen = (P.stolen || 0) + n; }
}
function attack(c, targets) {
  const P = M();
  if (c.room.name !== ROOM) return travel(c, ROOM, 40, 20, 2);
  if (!targets.length) return travel(c, ROOM, 30, 30, 5) && undefined; // central lookout
  const t = pickTarget(c.pos, targets), r = c.pos.getRangeTo(t), near = targets.filter(h => c.pos.inRangeTo(h, 3));
  if (near.length >= 2) c.rangedMassAttack(); else if (r <= 3) c.rangedAttack(t); else if (near.length) c.rangedAttack(near[0]);
  P.tg = { id: t.id, name: t.name, body: bodyStr(t), hits: t.hits, t: Game.time };
  if (act(t, ATTACK) && r < 3) { // kite: step away from melee, keep range 3 (never toward y<MIN_Y)
    const res = PathFinder.search(c.pos, [{ pos: t.pos, range: 3 }], { flee: true, maxRooms: 1, roomCallback: rn => matrixFor(rn, new PathFinder.CostMatrix()) });
    if (res.path.length) c.move(c.pos.getDirectionTo(res.path[0]));
    return;
  }
  const want = armed(t) ? 3 : 1; // unarmed: close in so mass attack does full 10
  if (r > want) travel(c, ROOM, t.pos.x, t.pos.y, want);
}
function toGuard(c) {
  log({ ev: 'guard', ttl: c.ticksToLive });
  c.memory.role = 'defender'; c.memory.remote = 'W45N8'; c.memory.born = c.memory.born || Game.time; c.memory.probe = 1;
  M().guarded = Game.time;
}
// spawn hook (managers/spawn.js): once, only when Memory.ops.probe.spawn===true and storage >= 3100 (keeps the 1300 defender reserve)
function wantSpawn(room, alive) {
  const P = Memory.ops && Memory.ops.probe;
  if (!P || P.spawn !== true || P.spawned) return false;
  if (_.some(Game.creeps, c => c.memory.role === 'probe')) return false;
  return !!(room.storage && room.storage.store[RESOURCE_ENERGY] >= 3100);
}
function noteSpawned(name) { const P = M(); P.spawned = name; P.spawn = false; P.cmd = P.cmd || 'hold'; log({ ev: 'spawned', name }); }
module.exports = { run, danger, pickTarget, prio, dps, wantSpawn, noteSpawned, BODY, WAYPOINTS, matrixFor, FORBID };
