// In-game route overlay (RoomVisual). Shows the routes creeps ACTUALLY walk, derived from live positions.
// Toggles: Memory.visuals.routes (default on), Memory.visuals.planned (default off: old planned roads/trunks).
// Recording (every tick, heap, ~0.003 ms/creep, no finds):
//   - remote haul: each rhauler's full loaded trip (first tick carrying energy -> empty at home), positions across rooms;
//     the latest completed trip per remote is that route.
//   - home: every movement leg of home roles (one leg = one move.js target key _m.k, from start tile to arrival), grouped by
//     role + unordered {previous target, target}; the latest leg per group is its route. Busiest groups (trips x length) shown.
// Drawing: snapshot rebuilt every REFRESH ticks, drawn every tick; skipped when bucket < 2000. Heap only (global reset clears it).
// Memory.routesLive (written on refresh): [{key,label,color,len,n,age,pts:'room:x,y;..'}] for console/box verification.
const LAYOUT = require('../layouts/W46N8');
const HOME = LAYOUT.room;
const REFRESH = 50, MIN_BUCKET = 2000, MAX_AGE = 1500, MIN_LEN = 4, MAX_HOME = 6, MAX_PTS = 300;
const HOME_ROLES = { hauler: '运输', queen: '女王', filler: '填充', manager: '管家', upgrader: '升级', builder: '建造', miner: '矿工', harvester: '采集' };
const NAMES = { source: '能量源', controller: '控制器', storage: '仓库', container: '容器', spawn: '出生点', extension: '扩展',
  link: '链接', tower: '塔', terminal: '终端', mineral: '矿物', road: '路' };
const PALETTE_R = ['#ffd400', '#ff66cc', '#ffffff'];
const PALETTE_H = ['#33ccff', '#66ff66', '#ff9933', '#b388ff', '#ff4d4d', '#00e6b8'];
const L = {};  // creep -> {k, prev, pts}  (home legs)
const T = {};  // creep -> pts             (remote loaded trips)
const G = {};  // group key -> {pts, n, t, label, remote}
let snap = null;

const same = (a, b) => a && a[0] === b[0] && a[1] === b[1] && a[2] === b[2];
function push(pts, c) { const p = [c.room.name, c.pos.x, c.pos.y]; if (!same(pts[pts.length - 1], p) && pts.length < MAX_PTS) pts.push(p); }
function save(key, pts, label, remote) { const g = G[key] || (G[key] = { n: 0 }); g.pts = pts; g.n++; g.t = Game.time; g.label = label; g.remote = remote; }
const KN = {};
function nameAt(k) { // "x,y,range" in HOME -> Chinese name of what sits there
  if (KN[k]) return KN[k];
  const [x, y] = k.split(',').map(Number), room = Game.rooms[HOME]; let n = `(${x},${y})`;
  if (room && room.lookForAt) {
    const s = room.lookForAt('source', x, y)[0] ? 'source' : room.lookForAt('mineral', x, y)[0] ? 'mineral'
      : ((room.lookForAt('structure', x, y).find(o => o.structureType !== 'road' && o.structureType !== 'rampart') || {}).structureType);
    if (s && NAMES[s]) n = NAMES[s] + (['source', 'container', 'link', 'extension'].includes(s) ? `(${x},${y})` : '');
  }
  return (KN[k] = n);
}
function record() {
  for (const n in Game.creeps) {
    const c = Game.creeps[n]; if (c.spawning) continue; const role = c.memory.role;
    if (role === 'rhauler' && c.memory.remote) {
      const loaded = c.store.getUsedCapacity() > 0;
      if (loaded) { if (!T[n]) T[n] = []; push(T[n], c); }
      else if (T[n]) { const p = T[n]; delete T[n];
        if (p.length >= MIN_LEN && p.some(q => q[0] === HOME) && p.some(q => q[0] === c.memory.remote)) save('R:' + c.memory.remote, p, '外矿 ' + c.memory.remote, true); }
    } else if (HOME_ROLES[role] && c.room.name === HOME) {
      const k = c.memory._m ? c.memory._m.k : null; let l = L[n];
      if (!l) l = L[n] = { k, prev: null, pts: [] };
      if (k !== l.k) {
        if (l.k && l.pts.length >= MIN_LEN) { const ends = [l.prev || 'start', l.k].sort();
          save('H:' + role + ':' + ends.join('|'), l.pts, HOME_ROLES[role] + ' ' + ends.map(e => e === 'start' ? '出发点' : nameAt(e)).join('↔'), false); }
        if (l.k) l.prev = l.k; l.k = k; l.pts = [];
      }
      if (k) push(l.pts, c);
    }
  }
  if (Game.time % 100 === 0) { for (const n in L) if (!Game.creeps[n]) delete L[n]; for (const n in T) if (!Game.creeps[n]) delete T[n]; }
}
function build() {
  const live = Object.keys(G).filter(k => { if (Game.time - G[k].t > MAX_AGE) { delete G[k]; return false; } return true; });
  const rem = live.filter(k => G[k].remote).sort();
  const home = live.filter(k => !G[k].remote).sort((a, b) => G[b].n * G[b].pts.length - G[a].n * G[a].pts.length || (a < b ? -1 : 1)).slice(0, MAX_HOME);
  const rooms = {}, legend = [], out = [], all = rem.concat(home);
  all.forEach((k, i) => {
    const g = G[k], color = g.remote ? PALETTE_R[rem.indexOf(k) % PALETTE_R.length] : PALETTE_H[home.indexOf(k) % PALETTE_H.length];
    const off = (i - (all.length - 1) / 2) * 0.05; let cur = null;
    for (const [r, x, y] of g.pts) {
      if (!cur || cur.room !== r) { cur = { room: r, color, pts: [] }; (rooms[r] = rooms[r] || []).push(cur); }
      cur.pts.push([x + off, y + off]);
    }
    legend.push({ label: g.label, color, len: g.pts.length - 1 });
    out.push({ key: k, label: g.label, color, len: g.pts.length - 1, n: g.n, age: Game.time - g.t, pts: g.pts.map(p => p.join(':')).join(';') });
  });
  Memory.routesLive = out;
  return { rooms, legend, at: Game.time };
}
// ---- optional planned overlay (off by default) ----
function planned() {
  const R = require('../layouts/remote_routes'), tr = (LAYOUT.defense && LAYOUT.defense.trunks) || {};
  const paths = [R.W45N8, R.W45N7].concat(Object.keys(tr).map(k => tr[k].path.map(([x, y]) => [HOME, x, y])));
  const by = {}; for (const p of paths) if (p) { let cur = null; for (const [r, x, y] of p) { if (!cur || cur.r !== r) { cur = { r, pts: [] }; (by[r] = by[r] || []).push(cur); } cur.pts.push([x, y]); } }
  for (const r in by) { const v = new RoomVisual(r); for (const s of by[r]) if (s.pts.length > 1) v.poly(s.pts, { stroke: '#888888', width: 0.06, opacity: 0.3, lineStyle: 'dotted' }); }
}
function run() {
  record();
  const V = Memory.visuals || {};
  if (typeof RoomVisual === 'undefined' || Game.cpu.bucket < MIN_BUCKET) return;
  if (V.planned === true) planned();
  if (V.routes === false) return;
  if (!snap || Game.time - snap.at >= REFRESH) snap = build();
  const st = { width: 0.09, opacity: 0.5, lineStyle: 'dashed' };
  for (const r in snap.rooms) { const v = new RoomVisual(r);
    for (const s of snap.rooms[r]) if (s.pts.length > 1) v.poly(s.pts, Object.assign({ stroke: s.color }, st)); }
  const v = new RoomVisual(HOME); let y = 1.2;
  v.text('实际路线 (格, 每' + REFRESH + 't刷新)', 0.6, y, { align: 'left', font: 0.5, color: '#dddddd', opacity: 0.7 });
  if (!snap.legend.length) v.text('采集中…', 0.6, y + 0.7, { align: 'left', font: 0.45, color: '#aaaaaa', opacity: 0.7 });
  for (const l of snap.legend) { y += 0.7;
    v.line(0.6, y - 0.15, 1.6, y - 0.15, { color: l.color, width: 0.09, opacity: 0.8, lineStyle: 'dashed' });
    v.text(l.label + ' ' + l.len, 1.8, y, { align: 'left', font: 0.45, color: l.color, opacity: 0.7 }); }
}
module.exports = { run, record, build, _G: G, _reset() { for (const o of [L, T, G]) for (const k in o) delete o[k]; snap = null; } };
