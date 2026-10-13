// Layout v2 accessors (data/layout_W46N8_v2.json, generated into src/layouts/W46N8.js). Heap-cached.
const PLANS = { W46N8: require('../layouts/W46N8') };
const cache = {};
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
  const pos = p.positions;
  const standing = new Set([...pos.fillers, pos.manager, ...pos.upgraders, ...pos.miners].map(([x, y]) => key(x, y)));
  return { raw: p, any, ramparts, pos, standing, byRcl };
}
module.exports = {
  key,
  get(name) { if (!(name in cache)) cache[name] = build(name); return cache[name]; },
  // wanted structures up to rcl: [{type,x,y,rcl}]
  upTo(name, rcl) { const P = this.get(name); return P ? Object.values(P.any).filter(s => s.rcl <= rcl) : []; },
};
