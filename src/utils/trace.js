// Cheap per-creep instrumentation (heap only, no console). Every 5 ticks one window row per creep is pushed into a
// ring buffer kept in memory segment 90 ({s:[[tick,[row..]]..] last 60 windows = 300 ticks, a:[arrivals] last 100}).
// The box listener polls the segment every 60 s into metrics/ts.sqlite (positions come from the websocket, not from here).
// Row: [name, cpu(0.01ms over the 5-tick window), acts, work, repaths, stuckEvents, targetKey, repathReasons(chars, see move.js)]; arrival: [tick,name,role,room:target,plannedLen,actualTicks]
const SEG = 90;
let ring = null;
const H = {}; let wrapped = false;
const h = n => H[n] || (H[n] = { cpu: 0, a: 0, w: 0, rp: 0, st: 0, rw: '' });
const WORKF = { harvest: c => 2 * c.getActiveBodyparts(WORK), upgradeController: c => c.getActiveBodyparts(WORK), build: c => 5 * c.getActiveBodyparts(WORK),
  repair: c => c.getActiveBodyparts(WORK), transfer: c => c.store.getUsedCapacity(), withdraw: c => c.store.getFreeCapacity(), pickup: c => c.store.getFreeCapacity(),
  reserveController: c => c.getActiveBodyparts(CLAIM), drop: () => 0 };
function wrap() {
  if (wrapped) return; wrapped = true;
  for (const f in WORKF) { const o = Creep.prototype[f]; if (!o) continue;
    Creep.prototype[f] = function (...a) { const r = o.apply(this, a); if (r === OK) { const e = h(this.name); e.a++; e.w += WORKF[f](this); } return r; }; }
}
function load() { if (ring) return ring; const raw = RawMemory.segments[SEG]; try { ring = raw ? JSON.parse(raw) : null; } catch (e) { ring = null; } return ring || (ring = { s: [], a: [] }); }
module.exports = {
  wrap, repath(c, why) { const e = h(c.name); e.rp++; if (e.rw.length < 12) e.rw += why || '?'; }, stuck(c) { h(c.name).st++; },
  arrive(c, k, n, t) { if (n > 2) load().a.push([Game.time, c.name, c.memory.role, c.room.name + ':' + k, n, t]); },
  cpu(c, d) { h(c.name).cpu += d; },
  run() {
    RawMemory.setActiveSegments([SEG]);
    if (Game.time % 5) return;
    const R = load(), rows = [];
    for (const n in Game.creeps) { const e = h(n), m = Game.creeps[n].memory;
      rows.push([n, Math.round(e.cpu * 100), e.a, e.w, e.rp, e.st, m._m ? m._m.k : '', e.rw]); H[n] = { cpu: 0, a: 0, w: 0, rp: 0, st: 0, rw: '' }; }
    for (const n in H) if (!Game.creeps[n]) delete H[n];
    R.s.push([Game.time, rows]); if (R.s.length > 60) R.s.splice(0, R.s.length - 60); if (R.a.length > 100) R.a.splice(0, R.a.length - 100);
    if (Game.time % 10 === 0) RawMemory.segments[SEG] = JSON.stringify(R);
  },
};
