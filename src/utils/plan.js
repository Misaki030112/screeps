// Layout v2 accessors (data/layout_W46N8_v2.json, generated into src/layouts/W46N8.js). Heap-cached.
const PLANS = { W46N8: require('../layouts/W46N8') };
const cache = {};
// Link plan A (Misaki 10-14, docs/RCL5.md): the ONLY source of link positions while STATIONARY_FILL is off (overrides the v2
// json links). RCL5 hub (next to storage/manager tile) + controller; RCL6 source A -> ctl. Queen stays through RCL7.
// RCL7/8 (2026-10-15, final plan docs/final_layout_rcl8.png): 3 more links from the v2 slots -> 6 = CONTROLLER_STRUCTURES[8].
const LINK_PLAN = { hub: [37, 29, 5], ctl: [30, 31, 5], srcA: [30, 11, 6], l4: [32, 34, 7], l5: [30, 25, 8], l6: [35, 26, 8] };
const key = (x, y) => x * 50 + y;
function build(name) {
  const p = PLANS[name]; if (!p) return null;
  const byRcl = {}, any = {}, ramparts = {};
  for (let r = 1; r <= 8; r++) {
    const lv = p.rcl[r] || {};
    for (const t in lv) for (const [x, y] of lv[t]) {
      if (t === 'rampart') { ramparts[key(x, y)] = r; continue; }
      any[key(x, y)] = { type: t, rcl: r, x, y };
    }
  }
  if (!RCL6_MINERALS) { // terminal / extractor / labs + mineral container are not planned (not placed, not kept by the planner)
    const mm = p.positions.mineralMiner;
    for (const k in any) if (DEFERRED.has(any[k].type) || (mm && any[k].type === 'container' && any[k].x === mm[0] && any[k].y === mm[1])) delete any[k];
  }
  if (!STATIONARY_FILL) {
    for (const k in any) if (any[k].type === 'link') delete any[k];
    for (const n in LINK_PLAN) { const [x, y, r] = LINK_PLAN[n]; any[key(x, y)] = { type: 'link', rcl: r, x, y }; }
  }
  if (!STATIONARY_FILL) { // filler-stamp containers (stamp tile 'K') are only for stationary fillers; drop the ones not built yet (RCL7 30,27)
    for (const st in (p.stamps || {})) for (const t in p.stamps[st].tiles) {
      if (p.stamps[st].tiles[t] !== 'K') continue; const [x, y] = t.split(',').map(Number), a = any[key(x, y)];
      if (a && a.type === 'container' && a.rcl >= 7) delete any[key(x, y)];
    }
  }
  // Planned removals (layout.remove): kept in the plan (not conflicts) but marked; layout.js destroys one only when a planned
  // container cannot be placed for the container limit, and never re-places it once its removal RCL is reached.
  for (const r in (p.remove || {})) for (const rm of p.remove[r]) { const a = any[key(rm.pos[0], rm.pos[1])]; if (a && a.type === rm.type) a.removeAt = +r; }
  const pos = p.positions;
  const standing = new Set([...pos.fillers, pos.manager, ...pos.upgraders, ...pos.miners].map(([x, y]) => key(x, y)));
  return { raw: p, any, ramparts, pos, standing, byRcl };
}
// RCL5+ fill network (links, stationary fillers, manager). OFF: the RCL2-4 regime continues at RCL5+ (queen fills every
// extension/tower incl. stamp B and ferries storage->ctl) and link sites are not placed. Turning it on as built would drop the
// queen with nothing to replace its storage->ctl ferry or fill stamp B / tower 2 (docs/RCL5.md, review 10-14): needs Misaki's
// link-plan decision + the missing roles first.
const STATIONARY_FILL = false;
// Rampart worth building/repairing? Over a real structure (not road/rampart), an approved defense gate, or — only while
// STATIONARY_FILL is on — a filler/manager stand tile. Decision 2026-10-15 (Misaki, docs/DEFENSE_PLAN.md): the 13 empty
// stand-tile ramparts are no longer repaired (left to decay, not dismantled); re-evaluate at RCL7.
function rampartWanted(P, room, x, y) {
  if (room.lookForAt(LOOK_STRUCTURES, x, y).some(s => s.structureType !== STRUCTURE_ROAD && s.structureType !== STRUCTURE_RAMPART)) return true;
  const g = P && P.raw.defense && P.raw.defense.gates;
  if (g && Object.values(g).some(a => a.some(([gx, gy]) => gx === x && gy === y))) return true;
  return !!(STATIONARY_FILL && P && P.standing.has(key(x, y)));
}
// RCL6 mineral/market block (strategy review 10-15, docs/RCL6.md). OFF: terminal (100k), 3 labs (150k), extractor (5k) and the
// mineral container (5k) are not placed. As planned they would take ~260k of RCL6's ~295k build energy (~12k ticks of upgrading,
// RCL7 ~14 h later) and sit idle: no mineral-miner role, no lab/boost code, and selling O needs Misaki's market decision.
// RCL6 then builds only the source-A link + 10 extensions (~35k). Turn on after Misaki approves minerals/market.
const RCL6_MINERALS = true; // Misaki 2026-10-18 09:30: approved now (terminal, extractor + container 39,23, 3 labs)
const DEFERRED = new Set(['terminal', 'extractor', 'lab']);
module.exports = {
  key, STATIONARY_FILL, rampartWanted, LINK_PLAN, RCL6_MINERALS,
  get(name) { if (!(name in cache)) cache[name] = build(name); return cache[name]; },
  // wanted structures up to rcl: [{type,x,y,rcl}]
  upTo(name, rcl) { const P = this.get(name); return P ? Object.values(P.any).filter(s => s.rcl <= rcl) : []; },
};
