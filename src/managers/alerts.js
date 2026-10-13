// Attack detection (no automatic safe mode — user decision). Writes Memory.stats.alerts and logs "ALERT {json}"
// to the console so the box websocket listener picks it up within ~1 tick.
// Episode = room + hostile owner; ends after QUIET ticks with no hostile activity.
const QUIET = 50;
// WORK-only creeps (neighbour remote harvesters) are low severity unless structures lose hits (dismantle).
const DANGER = [ATTACK, RANGED_ATTACK, CLAIM, HEAL];
function bodySummary(c) { return _.countBy(c.body, p => p.type); }
module.exports = { run(room) {
  const mem = room.memory.alerts || (room.memory.alerts = { episodes: {}, hits: {} });
  const out = [];
  const hostiles = room.find(FIND_HOSTILE_CREEPS);
  // structure hit loss since last tick (own structures + roads/containers)
  const hitsNow = {}; let loss = 0; const damaged = [];
  const scan = Game.time % 5 === 0;  // structure hit-loss diff every 5 ticks (event log still covers every tick)
  if (scan) for (const s of room.find(FIND_STRUCTURES)) {
    if (!(s.my || s.structureType === STRUCTURE_ROAD || s.structureType === STRUCTURE_CONTAINER)) continue;
    hitsNow[s.id] = [s.hits, s.ticksToDecay];
    const prev = mem.hits[s.id];
    if (!Array.isArray(prev)) continue;
    // ignore natural decay (roads/containers/ramparts): ticksToDecay jumps back up when decay applies
    const decayed = prev[1] !== undefined && s.ticksToDecay !== undefined && s.ticksToDecay > prev[1];
    if (s.hits < prev[0] && !decayed) { loss += prev[0] - s.hits; damaged.push(s.structureType); }
  }
  // owned structures that vanished (destroyed)
  if (scan) for (const id in mem.hits) if (hitsNow[id] === undefined && !Game.getObjectById(id)) damaged.push('destroyed:' + id.slice(-4));
  if (scan) mem.hits = hitsNow;
  // event log attackers
  const evAttackers = {}; let evDamage = 0;
  for (const e of room.getEventLog()) {
    if (e.event !== EVENT_ATTACK) continue;
    const src = Game.getObjectById(e.objectId);
    if (src && src.owner && !src.my) { evAttackers[src.owner.username] = true; evDamage += e.data.damage; }
  }
  const byOwner = _.groupBy(hostiles, c => c.owner.username);
  for (const name in evAttackers) if (!byOwner[name]) byOwner[name] = [];
  for (const owner in byOwner) {
    const creeps = byOwner[owner];
    const parts = {}; for (const c of creeps) for (const p of c.body) if (p.hits > 0) parts[p.type] = (parts[p.type] || 0) + 1;
    const dangerous = DANGER.some(p => parts[p]) || evAttackers[owner] || (parts[WORK] && loss > 0);
    const sev = evAttackers[owner] || (loss > 0 && dangerous) ? 'high' : dangerous ? 'medium' : 'low';
    let ep = mem.episodes[owner];
    const isNew = !ep;
    if (!ep) ep = mem.episodes[owner] = { id: `${room.name}-${owner}-${Game.time}`, start: Game.time, sev: 'low', maxCreeps: 0, damage: 0 };
    const sevRank = { low: 0, medium: 1, high: 2 };
    const escalated = sevRank[sev] > sevRank[ep.sev];
    if (escalated) ep.sev = sev;
    ep.last = Game.time; ep.maxCreeps = Math.max(ep.maxCreeps, creeps.length); ep.damage += evDamage + (dangerous ? loss : 0);
    if (isNew || escalated || (sev === 'high' && Game.time % 10 === 0)) {
      out.push({ episode: ep.id, tick: Game.time, room: room.name, owner, severity: ep.sev, creeps: creeps.length,
        body: parts, bodies: creeps.slice(0, 5).map(bodySummary), structureHitLoss: loss, damaged: damaged.slice(0, 10),
        eventDamage: evDamage, totalDamage: ep.damage, positions: creeps.slice(0, 5).map(c => [c.pos.x, c.pos.y]) });
    }
  }
  if (!hostiles.length && loss > 0 && damaged.length) {
    // damage with no visible hostile (e.g. nuke / attacker left)
    out.push({ episode: `${room.name}-unknown-${Game.time}`, tick: Game.time, room: room.name, owner: 'unknown', severity: 'medium', structureHitLoss: loss, damaged: damaged.slice(0, 10) });
  }
  for (const owner in mem.episodes) {
    const ep = mem.episodes[owner];
    if (Game.time - ep.last > QUIET) { out.push({ episode: ep.id, tick: Game.time, room: room.name, owner, severity: ep.sev, ended: true, duration: ep.last - ep.start, totalDamage: ep.damage, maxCreeps: ep.maxCreeps }); delete mem.episodes[owner]; }
  }
  for (const a of out) console.log('ALERT ' + JSON.stringify(a));
  return out;
} };
