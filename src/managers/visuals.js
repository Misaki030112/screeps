// Persistent in-game route overlay (RoomVisual). Toggle: Memory.visuals.routes (default true).
// Routes: remote haul paths (layouts/remote_routes) + home trunks (layouts/W46N8 defense.trunks).
// Per-room polylines are built once into heap and rebuilt every REBUILD ticks or when the plan signature changes.
const LAYOUT = require('../layouts/W46N8');
const REMOTE = require('../layouts/remote_routes');
const HOME = LAYOUT.room;
const REBUILD = 500, MIN_BUCKET = 2000;
// name (Chinese legend), colour, lateral offset so overlapping stems stay distinguishable
const STYLE = [
  { key: 'W45N8', label: '外矿 W45N8', color: '#ffd400', src: () => REMOTE.W45N8 },
  { key: 'W45N7', label: '外矿 W45N7', color: '#ff66cc', src: () => REMOTE.W45N7 },
  { key: 'TR', label: '主干 右上 TR', color: '#33ccff', src: () => trunk('TR') },
  { key: 'BR', label: '主干 右下 BR', color: '#66ff66', src: () => trunk('BR') },
  { key: 'TL', label: '主干 左上 TL', color: '#ff9933', src: () => trunk('TL') },
  { key: 'W', label: '主干 西 W', color: '#b388ff', src: () => trunk('W') },
  { key: 'S', label: '主干 南 S', color: '#ff4d4d', src: () => trunk('S') },
];
function trunk(k) { const t = LAYOUT.defense && LAYOUT.defense.trunks && LAYOUT.defense.trunks[k]; return t ? t.path.map(([x, y]) => [HOME, x, y]) : []; }
function sig() { return STYLE.map(s => s.key + ':' + s.src().length).join(','); }

// -> { rooms: {roomName: [{color, pts:[[x,y],...]}]}, legend: [{label,color,len}] }
function build() {
  const rooms = {}, legend = [];
  STYLE.forEach((s, i) => {
    const path = s.src(); if (!path.length) return;
    const off = (i - (STYLE.length - 1) / 2) * 0.06;
    let cur = null;
    for (const [r, x, y] of path) {
      if (!cur || cur.room !== r) { cur = { room: r, color: s.color, pts: [] }; (rooms[r] = rooms[r] || []).push(cur); }
      cur.pts.push([x + off, y + off]);
    }
    legend.push({ label: s.label, color: s.color, len: path.length });
  });
  return { rooms, legend, at: Game.time, sig: sig() };
}
let cache = null;
function get() {
  if (!cache || Game.time - cache.at >= REBUILD) { const s = sig(); if (!cache || cache.sig !== s) cache = build(); else cache.at = Game.time; }
  return cache;
}
function enabled() { const v = Memory.visuals; return !(v && v.routes === false); }

function run() {
  if (typeof RoomVisual === 'undefined' || !enabled() || Game.cpu.bucket < MIN_BUCKET) return;
  const c = get();
  const lineStyle = { width: 0.09, opacity: 0.5, lineStyle: 'dashed' };
  for (const r in c.rooms) {
    const v = new RoomVisual(r);
    for (const seg of c.rooms[r]) if (seg.pts.length > 1) v.poly(seg.pts, Object.assign({ stroke: seg.color }, lineStyle));
  }
  const v = new RoomVisual(HOME); let y = 1.2;
  v.text('路线图例 (格)', 0.6, y, { align: 'left', font: 0.5, color: '#dddddd', opacity: 0.7 });
  for (const l of c.legend) {
    y += 0.7;
    v.line(0.6, y - 0.15, 1.6, y - 0.15, { color: l.color, width: 0.09, opacity: 0.8, lineStyle: 'dashed' });
    v.text(l.label + ' ' + l.len, 1.8, y, { align: 'left', font: 0.45, color: l.color, opacity: 0.7 });
  }
}
module.exports = { run, build, STYLE };
