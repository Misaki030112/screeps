// Layout v2 accessors (data/layout_W46N8_v2.json, generated into src/layouts/W46N8.js). Heap-cached.
const PLANS = { W46N8: require('../layouts/W46N8') };
const cache = {};
// Link plan A (Misaki 10-14, docs/RCL5.md): the ONLY source of link positions while STATIONARY_FILL is off (overrides the v2
// json links). RCL5 hub (next to storage/manager tile) + controller; RCL6 source A -> ctl. Queen stays through RCL7.
const LINK_PLAN = { hub: [37, 29, 5], ctl: [30, 31, 5], srcA: [30, 11, 6] };
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
  const pos = p.positions;
  const standing = new Set([...pos.fillers, pos.manager, ...pos.upgraders, ...pos.miners].map(([x, y]) => key(x, y)));
  return { raw: p, any, ramparts, pos, standing, byRcl };
}
// RCL5+ fill network (links, stationary fillers, manager). OFF: the RCL2-4 regime continues at RCL5+ (queen fills every
// extension/tower incl. stamp B and ferries storage->ctl) and link sites are not placed. Turning it on as built would drop the
// queen with nothing to replace its storage->ctl ferry or fill stamp B / tower 2 (docs/RCL5.md, review 10-14): needs Misaki's
// link-plan decision + the missing roles first.
const STATIONARY_FILL = false;
// RCL6 mineral/market block (strategy review 10-15, docs/RCL6.md). OFF: terminal (100k), 3 labs (150k), extractor (5k) and the
// mineral container (5k) are not placed. As planned they would take ~260k of RCL6's ~295k build energy (~12k ticks of upgrading,
// RCL7 ~14 h later) and sit idle: no mineral-miner role, no lab/boost code, and selling O needs Misaki's market decision.
// RCL6 then builds only the source-A link + 10 extensions (~35k). Turn on after Misaki approves minerals/market.
const RCL6_MINERALS = false;
const DEFERRED = new Set(['terminal', 'extractor', 'lab']);
module.exports = {
  key, STATIONARY_FILL, LINK_PLAN, RCL6_MINERALS,
  get(name) { if (!(name in cache)) cache[name] = build(name); return cache[name]; },
  // wanted structures up to rcl: [{type,x,y,rcl}]
  upTo(name, rcl) { const P = this.get(name); return P ? Object.values(P.any).filter(s => s.rcl <= rcl) : []; },
};
