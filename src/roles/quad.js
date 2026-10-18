// W47N8 2x2 quad (docs/CONQUEST_QUAD.md). INERT unless Memory.ops.cq.armed === true (spawn) — Misaki's explicit go only.
// Commands share Memory.ops.cq.cmd with roles/conquest.js: 'hold' (rally at home), 'go' (enter W47N8, kill reserver first,
// hold near the controller), 'retreat' (back to rally; stops conquest spawning).
// Formation: anchor = top-left cell; member idx k sits at anchor + OFF[k]. One decision per tick (first member to run):
//   1. regroup: any member off its cell (same room) -> members step to their cells, nobody advances
//   2. fatigue: any member fatigue > 0 -> wait (cohesion)
//   3. advance: PathFinder over a QUAD matrix (anchor tile valid only if all 4 cells walkable; cost = worst cell: road 1, plain 2,
//      swamp 10 -> swamps avoided), every member moves the same direction
//   4. squeeze: no 2x2 path (narrow pass / room exit) -> single file: leader paths to goal, k follows k-1's previous tile
// Combat every tick, independent of movement: shared focus (conquest.pickTarget: CLAIM/reserver first, then healers, armed by dps,
// haulers...), rangedMassAttack when >=3 hostiles in range 3; heal: most-hurt member in range 1 (else rangedHeal range 3),
// pre-heal self when hostiles within 5. Retreat triggers (conquest.danger + member lost after assembly) -> cmd 'retreat'.
const CQ = () => require('./conquest');
const OFF = [[0, 0], [1, 0], [0, 1], [1, 1]];
const RALLY = { room: 'W46N8', x: 9, y: 26 }, HOLD = { room: 'W47N8', x: 17, y: 23 };
const BODY = () => [].concat(Array(4).fill(RANGED_ATTACK), Array(9).fill(MOVE), Array(5).fill(HEAL)); // 2300: 4R5H9M
const M = () => (Memory.ops = Memory.ops || {}, Memory.ops.cq = Memory.ops.cq || {});
const members = () => _.sortBy(_.filter(Game.creeps, c => c.memory.role === 'cqquad'), c => c.memory.qi);
const rng = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));

// ---- pure helpers (unit-tested) ----
// terrain(x,y) -> 'wall'|'swamp'|'plain'; extra(x,y) -> cost override or undefined. Returns cost of anchoring at (x,y) or 255.
function anchorCost(x, y, terrain, extra) {
  let worst = 0;
  for (const [dx, dy] of OFF) {
    const cx = x + dx, cy = y + dy;
    if (cx < 1 || cy < 1 || cx > 48 || cy > 48) return 255;
    const e = extra ? extra(cx, cy) : undefined;
    const t = terrain(cx, cy);
    const c = e !== undefined ? e : t === 'wall' ? 255 : t === 'swamp' ? 10 : 2;
    if (c >= 255) return 255; worst = Math.max(worst, c);
  }
  return worst;
}
// anchor of a formed quad from member positions (idx -> pos); null if not in formation
function formedAnchor(pos) {
  const a = pos[0]; if (!a) return null;
  for (let k = 1; k < 4; k++) { const p = pos[k]; if (!p || p.roomName !== a.roomName || p.x !== a.x + OFF[k][0] || p.y !== a.y + OFF[k][1]) return null; }
  return { x: a.x, y: a.y, roomName: a.roomName };
}
// heal pick: most hurt (by ratio) within range 1 first, else within 3; returns [creep, 'heal'|'rangedHeal'] or null
function healPick(me, team) {
  const hurt = team.filter(m => m.hits < m.hitsMax).sort((a, b) => a.hits / a.hitsMax - b.hits / b.hitsMax);
  const r1 = hurt.find(m => rng(me.pos, m.pos) <= 1); if (r1) return [r1, 'heal'];
  const r3 = hurt.find(m => rng(me.pos, m.pos) <= 3); if (r3) return [r3, 'rangedHeal'];
  return null;
}

// ---- runtime ----
function quadMatrix(rn) {
  const room = Game.rooms[rn], T = Game.map.getRoomTerrain(rn), m = new PathFinder.CostMatrix();
  if (CQ().FORBID.has(rn)) { for (let x = 0; x < 50; x++) for (let y = 0; y < 50; y++) m.set(x, y, 255); return m; }
  const blk = {}, road = {};
  if (room) for (const s of room.find(FIND_STRUCTURES)) {
    if (s.structureType === STRUCTURE_ROAD) road[s.pos.x * 50 + s.pos.y] = 1;
    else if (s.structureType !== STRUCTURE_CONTAINER && !(s.structureType === STRUCTURE_RAMPART && s.my)) blk[s.pos.x * 50 + s.pos.y] = 1;
  }
  const terr = (x, y) => { const v = T.get(x, y); return v & TERRAIN_MASK_WALL ? 'wall' : v & TERRAIN_MASK_SWAMP ? 'swamp' : 'plain'; };
  const extra = (x, y) => blk[x * 50 + y] ? 255 : (rn === CQ().ROOM && y < CQ().MIN_Y) ? 255 : road[x * 50 + y] ? 1 : undefined;
  for (let x = 0; x < 50; x++) for (let y = 0; y < 50; y++) m.set(x, y, anchorCost(x, y, terr, extra));
  return m;
}
function goalFor(cmd, team, focus) {
  if (cmd === 'go') return focus ? { pos: focus.pos, range: 3 } : { pos: new RoomPosition(HOLD.x, HOLD.y, HOLD.room), range: 1 };
  return { pos: new RoomPosition(RALLY.x, RALLY.y, RALLY.room), range: 1 };
}
function decide(team) {
  const P = M(), Q = P.quad = P.quad || {};
  if (Q.t === Game.time) return Q; Q.t = Game.time;
  const cmd = P.cmd || 'hold', lead = team[0];
  // targets / focus (shared, reserver first)
  const room = lead.room, owner = P.owner || 'BustJetter';
  const hostiles = room.find(FIND_HOSTILE_CREEPS).filter(h => h.owner && h.owner.username !== 'Source Keeper');
  const targets = hostiles.filter(h => h.owner.username === owner || CQ().dps(h) > 0);
  const f = cmd === 'go' && targets.length ? CQ().pickTarget(lead.pos, targets, Q.focus) : null;
  Q.focus = f ? f.id : undefined;
  // retreat triggers (before W47N8 is ours and in safe mode)
  const r47 = Game.rooms[CQ().ROOM], safe = r47 && r47.controller && r47.controller.my && r47.controller.safeMode;
  if (!safe && cmd !== 'retreat') {
    const towers = room.find(FIND_HOSTILE_STRUCTURES).filter(s => s.structureType === STRUCTURE_TOWER);
    let why = CQ().danger(team.map(c => ({ hits: c.hits, hitsMax: c.hitsMax, heal: c.getActiveBodyparts(HEAL) })), hostiles, towers);
    if (!why && Q.assembled && team.length < 4) why = 'member lost';
    if (why) { P.cmd = 'retreat'; P.auto = { why, t: Game.time }; (P.log = P.log || []).push({ t: Game.time, ev: 'quad-retreat', why }); }
  }
  if (team.length >= 4) Q.assembled = 1;
  // movement plan
  const goal = goalFor(P.cmd || 'hold', team, f);
  const pos = {}; for (const c of team) pos[c.memory.qi] = c.pos;
  const anc = team.length === 4 ? formedAnchor(pos) : null;
  Q.moves = {}; Q.mode = 'wait';
  if (team.length < 4 && (P.cmd || 'hold') !== 'retreat') { Q.mode = 'assemble'; return Q; }
  if (team.some(c => c.fatigue > 0)) { Q.mode = 'fatigue'; return Q; }
  if (anc) {
    if (anc.roomName === goal.pos.roomName && rng(anc, goal.pos) <= goal.range) { Q.mode = 'there'; return Q; }
    const r = PathFinder.search(new RoomPosition(anc.x, anc.y, anc.roomName), { pos: goal.pos, range: goal.range },
      { maxRooms: 3, maxOps: 4000, roomCallback: quadMatrix, plainCost: 2, swampCost: 10 });
    if (!r.incomplete && r.path.length && r.path[0].roomName === anc.roomName) {
      const d = new RoomPosition(anc.x, anc.y, anc.roomName).getDirectionTo(r.path[0]);
      for (const c of team) Q.moves[c.name] = d; Q.mode = 'advance'; return Q;
    }
    Q.mode = 'squeeze';
  } else {
    // regroup if the leader's room has room for the formation around it, else squeeze
    const T = Game.map.getRoomTerrain(lead.pos.roomName), terr = (x, y) => { const v = T.get(x, y); return v & TERRAIN_MASK_WALL ? 'wall' : v & TERRAIN_MASK_SWAMP ? 'swamp' : 'plain'; };
    const allHere = team.every(c => c.pos.roomName === lead.pos.roomName);
    if (allHere && anchorCost(lead.pos.x, lead.pos.y, terr) < 255) { Q.mode = 'regroup'; Q.anchor = { x: lead.pos.x, y: lead.pos.y, room: lead.pos.roomName }; return Q; }
    Q.mode = 'squeeze';
  }
  Q.goal = { x: goal.pos.x, y: goal.pos.y, room: goal.pos.roomName, range: goal.range };
  return Q;
}
function fight(c, team, Q) {
  const hostiles = c.room.find(FIND_HOSTILE_CREEPS).filter(h => h.owner && h.owner.username !== 'Source Keeper');
  const inR = hostiles.filter(h => c.pos.inRangeTo(h, 3)), focus = Q.focus && Game.getObjectById(Q.focus);
  if (inR.length >= 3) c.rangedMassAttack();
  else if (focus && c.pos.inRangeTo(focus, 3)) c.rangedAttack(focus);
  else if (inR.length) c.rangedAttack(CQ().pickTarget(c.pos, inR));
  const h = healPick(c, team);
  if (h) c[h[1]](h[0]); else if (hostiles.some(x => c.pos.inRangeTo(x, 5))) c.heal(c);
}
function run(c) {
  const P = M(), team = members();
  if (c.memory.qi === undefined) { const used = new Set(team.map(m => m.memory.qi)); c.memory.qi = [0, 1, 2, 3].find(i => !used.has(i)); }
  const Q = decide(team);
  fight(c, team, Q);
  const k = c.memory.qi, cmd = P.cmd || 'hold';
  if (Q.mode === 'assemble') { const [dx, dy] = OFF[k] || [0, 0]; return c.moveTo(new RoomPosition(RALLY.x + dx, RALLY.y + dy, RALLY.room), { reusePath: 10 }); }
  if (Q.mode === 'advance') return c.move(Q.moves[c.name]);
  if (Q.mode === 'regroup' && Q.anchor) { const [dx, dy] = OFF[k]; return c.moveTo(new RoomPosition(Q.anchor.x + dx, Q.anchor.y + dy, Q.anchor.room), { reusePath: 0 }); }
  if (Q.mode === 'squeeze' && Q.goal) {
    // single file: leader to goal, each follower to the member ahead of it
    const ahead = team.filter(m => m.memory.qi < k).pop();
    if (!ahead) return c.moveTo(new RoomPosition(Q.goal.x, Q.goal.y, Q.goal.room), { range: Q.goal.range, reusePath: 5, costCallback: CQ().matrixFor });
    if (!c.pos.isNearTo(ahead)) return c.moveTo(ahead, { reusePath: 0, costCallback: CQ().matrixFor });
  }
}
// spawn gate: armed + quad.spawn; <4 members (replacement only with quad.respawn during 'go'); never during 'retreat'
function wantSpawn(room) {
  const P = Memory.ops && Memory.ops.cq; if (!P || P.armed !== true) return null;
  if ((P.cmd || 'hold') === 'retreat') return null;
  if (!room.storage || room.storage.store[RESOURCE_ENERGY] < (P.floor || 8000)) return null;
  const n = members().length, Q = P.quad || {};
  if (P.quadSpawn && n < 4 && (!Q.assembled || P.quadRespawn)) return { role: 'cqquad', body: BODY(), mem: { role: 'cqquad', home: 'W46N8', born: Game.time } };
  return null;
}
module.exports = { run, wantSpawn, anchorCost, formedAnchor, healPick, BODY, OFF, RALLY, HOLD };
