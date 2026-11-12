// Home-room defense state (docs/DEFENSE.md "Home defense"). Never activates safe mode (Misaki does that herself).
//   hostiles(room): player/NPC creeps with live ATTACK/RANGED/HEAL/WORK parts in the room (cached per tick)
//   alert(room)   : room.memory.defAlert > Game.time — set from the console when a Council combat squad sits in an ADJACENT room
//                   (her approved early-wall trigger, 2026-10-16). Starts walls early; does not spawn anything by itself.
//   wantGuards    : guards to keep while hostiles are in the room, sized to the threat
// Switches (Misaki 2026-10-16): home earlyWalls/guards default OFF (BustJetter not worth slowing upgrade);
// remoteDefender default ON (W45N8 anti-NPC-Invader; Misaki 10:39 restore — do not wait out remotes).
// remotePatrol default ON (Misaki 10-16 W45N7): after a kill the remote defender patrols W45N8<->W45N7 until TTL instead of recycling.
// Override from console without deploy: Memory.defense = { earlyWalls: true, guards: true, remoteDefender: false, remotePatrol: false }
const FLAGS = { earlyWalls: false, guards: false, remoteDefender: true, remotePatrol: true }; // remoteDefender: W45N8 anti-Invader defender (threat.armed)
const on = k => { const m = typeof Memory !== 'undefined' && Memory.defense; return m && m[k] !== undefined ? !!m[k] : FLAGS[k]; };
const C = {}; const now = () => (typeof Game === 'undefined' ? 0 : Game.time); const COMBAT = ['attack', 'ranged_attack', 'heal', 'work'];
function hostiles(room) {
  const k = room.name; if (C[k] && C[k].t === now()) return C[k].h;
  const h = (room.find ? room.find(FIND_HOSTILE_CREEPS) || [] : []).filter(x => x.body.some(p => COMBAT.includes(p.type) && p.hits > 0));
  C[k] = { t: now(), h }; return h;
}
const players = room => hostiles(room).filter(h => h.owner.username !== 'Invader');
const alert = room => on('earlyWalls') && ((room.memory && room.memory.defAlert) || 0) > now();
const active = room => players(room).length > 0;
// Owned-room response. A creep with no ATTACK / RANGED_ATTACK / HEAL / WORK is a tourist and spawns nothing
// (2026-11-12 16:12 W47N8 was one unidentified hostile sample, no body, no damage — not a fight).
// HEAL and WORK count: a healer or a dismantler in our room is a combat threat. The old `guards` flag
// no longer suppresses this; Misaki's standing order is a spawn in every threatened owned room.
// Count is utils/squad.judge (same table as remote defenders), including NPC Invaders.
function specOf(h) {
  const n = t => h.body.filter(p => p.type === t && p.hits > 0).length;
  const ra = n('ranged_attack'), atk = n('attack'), heal = n('heal'), work = n('work');
  if (!ra && !atk && !heal && !work) return null;
  return { heal: heal > 0, ra, boosted: h.body.some(p => p.boost), attack: atk, work };
}
function wantGuards(room) {
  const specs = hostiles(room).map(specOf).filter(Boolean);
  if (!specs.length) return 0;
  return require('../utils/squad').judge(specs);
}
const combatNow = room => wantGuards(room) > 0;
// creeps that are damaging us (target of tower fire even when net<=0)
function hurting(room) {
  const s = new Set(), mine = room.find(FIND_MY_CREEPS).concat(room.find(FIND_MY_STRUCTURES));
  for (const h of hostiles(room)) {
    const r = h.body.some(p => p.type === 'ranged_attack' && p.hits > 0) ? 3 : 1;
    if (h.body.some(p => ['attack', 'ranged_attack', 'work'].includes(p.type) && p.hits > 0) && mine.some(m => h.pos.inRangeTo(m, r))) s.add(h.id);
  }
  return s;
}
// civilian safety: a hostile damage creep within `r` -> step away (PathFinder flee). true = moved
function flee(c, r = 5) {
  if (!c.room.controller || !c.room.controller.my) return false;
  const d = hostiles(c.room).filter(h => h.body.some(p => (p.type === 'attack' || p.type === 'ranged_attack') && p.hits > 0) && c.pos.inRangeTo(h, r));
  if (!d.length) return false;
  const res = PathFinder.search(c.pos, d.map(h => ({ pos: h.pos, range: r + 2 })), { flee: true, maxRooms: 1 });
  if (res.path.length) { c.move(c.pos.getDirectionTo(res.path[0])); return true; }
  return false;
}
module.exports = { FLAGS, on, hostiles, players, alert, active, wantGuards, combatNow, hurting, flee };
