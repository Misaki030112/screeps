// Cheap per-creep instrumentation (heap only, no console). Every 5 ticks one window row per creep is pushed into a
// ring buffer kept in memory segment 90 ({s:[[tick,[row..]]..] last 60 windows = 300 ticks, a:[arrivals] last 100}).
// The box listener polls the segment every 60 s into metrics/ts.sqlite (positions come from the websocket, not from here).
// Per tick one state char per creep (tick(): w work, m move, s spawning, else idle reason set by role via why(c,ch) or role default):
//   e source_empty(legit) p waiting_pickup u waiting_feed f target_full q queue/blocked n no_task t parked_threat r renewing
// Row: [name, cpu(0.01ms over the 5-tick window), acts, work, repaths, stuckEvents, targetKey, repathReasons(chars, see move.js), stateCodes(5 chars, one per tick),
//       fails (wrapped intents returning an error other than ERR_NOT_IN_RANGE), maxTickCpu(0.01ms, worst single tick in the window)]; arrival: [tick,name,role,room:target,plannedLen,actualTicks]
const SEG = 90;
let ring = null;
const H = {}; let wrapped = false;
const h = n => H[n] || (H[n] = { cpu: 0, a: 0, w: 0, rp: 0, st: 0, rw: '', sc: '', ta: 0, f: 0, mx: 0 });
const DEF = { miner: 'e', rminer: 'e', mminer: 'e', hauler: 'p', rhauler: 'p', upgrader: 'u', builder: 'n', queen: 'f', filler: 'f', manager: 'f',
  // W47N8 roles fell through to 'q' so audits read e.g. upgrader waiting_feed as queue_blocked (strategy 10-21 11:4x)
  w8miner: 'e', w8rminer: 'e', w8mminer: 'e', w8hauler: 'p', w8rhauler: 'p', w8upgrader: 'u', w8builder: 'n', w8filler: 'f', w8defender: 't', w8guard: 't', w8healer: 't' };
const WHY = {}, POS = {};
const WORKF = { harvest: c => 2 * c.getActiveBodyparts(WORK), upgradeController: c => c.getActiveBodyparts(WORK), build: c => 5 * c.getActiveBodyparts(WORK),
  repair: c => c.getActiveBodyparts(WORK), transfer: c => c.store.getUsedCapacity(), withdraw: c => c.store.getFreeCapacity(), pickup: c => c.store.getFreeCapacity(),
  reserveController: c => c.getActiveBodyparts(CLAIM),
  // attackController must wrap too — else Invader reclaim (28d8443) looks like queue_blocked (patrol 05:5x)
  attackController: c => c.getActiveBodyparts(CLAIM), claimController: c => c.getActiveBodyparts(CLAIM), drop: () => 0 };
function wrap() {
  if (wrapped) return; wrapped = true;
  for (const f in WORKF) { const o = Creep.prototype[f]; if (!o) continue;
    Creep.prototype[f] = function (...a) { const r = o.apply(this, a); if (r === OK) { const e = h(this.name); e.a++; e.w += WORKF[f](this); } else if (r !== ERR_NOT_IN_RANGE) h(this.name).f++; return r; }; }
}
function load() { if (ring) return ring; const raw = RawMemory.segments[SEG]; try { ring = raw ? JSON.parse(raw) : null; } catch (e) { ring = null; } return ring || (ring = { s: [], a: [] }); }
module.exports = {
  wrap, repath(c, why) { const e = h(c.name); e.rp++; if (e.rw.length < 12) e.rw += why || '?'; }, stuck(c) { h(c.name).st++; },
  arrive(c, k, n, t) { if (n > 2) load().a.push([Game.time, c.name, c.memory.role, c.room.name + ':' + k, n, t]); },
  cpu(c, d) { const e = h(c.name); e.cpu += d; if (d > e.mx) e.mx = d; },
  why(c, ch) { WHY[c.name] = ch; },
  // once per tick after all creeps ran: ~0.005 ms/creep (no finds)
  tick() {
    for (const n in Game.creeps) { const c = Game.creeps[n], e = h(n), p = c.pos.x * 64 + c.pos.y + (c.room.name === c.memory.remote ? 4096 : 0);
      const ch = c.spawning ? 's' : e.a > e.ta ? 'w' : POS[n] !== undefined && POS[n] !== p ? 'm' : (WHY[n] || DEF[c.memory.role] || 'q');
      e.ta = e.a; POS[n] = p; if (e.sc.length < 5) e.sc += ch; }
    for (const n in WHY) delete WHY[n];
  },
  run() {
    RawMemory.setActiveSegments([SEG]);
    if (Game.time % 5) return;
    const R = load(), rows = [];
    for (const n in Game.creeps) { const e = h(n), m = Game.creeps[n].memory;
      rows.push([n, Math.round(e.cpu * 100), e.a, e.w, e.rp, e.st, m._m ? m._m.k : '', e.rw, e.sc, e.f, Math.round(e.mx * 100)]); H[n] = { cpu: 0, a: 0, w: 0, rp: 0, st: 0, rw: '', sc: '', ta: 0, f: 0, mx: 0 }; }
    for (const n in H) if (!Game.creeps[n]) { delete H[n]; delete POS[n]; }
    R.s.push([Game.time, rows]); if (R.s.length > 60) R.s.splice(0, R.s.length - 60); if (R.a.length > 100) R.a.splice(0, R.a.length - 100);
    if (Game.time % 10 === 0) { // segment hard limit 100 KB (17:00 notify at ~50 creeps x 60 windows): drop oldest windows until < 90 KB
      let js = JSON.stringify(R);
      while (js.length > 90000 && R.s.length > 12) { R.s.splice(0, Math.max(1, Math.ceil(R.s.length / 5))); js = JSON.stringify(R); }
      if (js.length > 90000) { R.a = R.a.slice(-20); js = JSON.stringify(R); }
      if (js.length <= 100000) RawMemory.segments[SEG] = js;
    }
  },
};
