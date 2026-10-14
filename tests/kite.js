// Unit tests for src/utils/kite.js on real W45N8 terrain (2026-10-15 defender death: kited into swamp/walled exit pocket,
// then fled home through the melee). Directions only; tests/defender_duel.js runs the full fights.
// node tests/kite.js -> exits 1 on failure
const fs = require('fs'), path = require('path'), assert = require('assert');
const T = fs.readFileSync(path.join(__dirname, '..', 'data/terrain_W45N8.txt'), 'utf8');
const wall = (x, y) => x < 0 || y < 0 || x > 49 || y > 49 || T[y * 50 + x] === '1' || T[y * 50 + x] === '3', swamp = (x, y) => T[y * 50 + x] === '2';
Object.assign(global, { TERRAIN_MASK_WALL: 1, TERRAIN_MASK_SWAMP: 2, MOVE: 'move' });
const K = require(path.join(__dirname, '..', 'src/utils/kite.js'));
const D9 = [[0, 0], [0, -1], [1, -1], [1, 0], [1, 1], [0, 1], [-1, 1], [-1, 0], [-1, -1]], EXIT = [0, 14];
const room = { getTerrain: () => ({ get: (x, y) => wall(x, y) ? 1 : swamp(x, y) ? 2 : 0 }) };
const inv = (x, y, fatigue = 0) => ({ pos: { x, y }, fatigue, body: Array(5).fill({ type: 'move', hits: 100 }) }); // smallMelee: 5 MOVE
const to = (d, t, flee) => { const k = K.step({ pos: { x: d[0], y: d[1] }, room }, t, flee, EXIT); return [d[0] + D9[k][0], d[1] + D9[k][1]]; };
const rng = (a, p) => Math.max(Math.abs(a[0] - p.x), Math.abs(a[1] - p.y));
let n = 0; const ok = (name, cond, info) => { assert(cond, name + ' ' + JSON.stringify(info)); n++; };
// engage prefers range 3 (shoots every tick) and never steps inside 3 of a melee that chases
let t = inv(19, 9), p = to([15, 9], t, false); ok('engage from 4 -> range 3', rng(p, t.pos) === 3, p);
t = inv(18, 9); p = to([16, 9], t, false); ok('engage at 2 -> back to >=3', rng(p, t.pos) >= 3, p);
t = inv(18, 10); p = to([15, 9], t, false); ok('engage at 3 holds 3', rng(p, t.pos) === 3, p);
// swamp = 5-tick lock: never kite onto swamp while a chaser is close (scan every open tile at range 2/3 around (20,9))
let bad = [];
for (let x = 12; x <= 28; x++) for (let y = 4; y <= 11; y++) {
  if (wall(x, y) || swamp(x, y)) continue; t = inv(x, y);
  for (const [dx, dy] of [[2, 0], [-2, 0], [0, 2], [3, 1], [-3, -1], [2, 2]]) { const d = [x + dx, y + dy]; if (wall(...d) || swamp(...d)) continue;
    const q = to(d, t, false); if (swamp(...q)) bad.push([d, [x, y], q]); if (rng(q, t.pos) <= 1) bad.push(['melee', d, [x, y], q]); }
}
ok('open area: no swamp step / no step into melee while kiting', bad.length === 0, bad.slice(0, 5));
// flee: a hurt defender must step away from a melee between it and the exit, not toward the exit through it
t = inv(2, 13); p = to([3, 11], t, true); ok('flee past melee: away (range >=3)', rng(p, t.pos) >= 3, p);
t = inv(13, 10); p = to([15, 9], t, true); ok('flee open: away (range >=3)', rng(p, t.pos) >= 3, p);
// flee with the chaser behind (exit side clear): head toward the exit
t = inv(20, 9); p = to([17, 9], t, true); ok('flee toward exit when chaser behind', p[0] < 17 && rng(p, t.pos) >= 3, p);
// walled west-exit pocket: stay on a tile next to the exit (one step = out of the room) instead of fleeing north into swamp
t = inv(1, 16); p = to([1, 13], t, false); ok('pocket engage: stays next to exit', rng(p, { x: EXIT[0], y: EXIT[1] }) <= 1 && !swamp(...p), p);
t = inv(1, 14); p = to([1, 13], t, false); ok('pocket caught: no swamp escape', !swamp(...p) && rng(p, { x: EXIT[0], y: EXIT[1] }) <= 1, p);
// fatigued target (stuck in swamp): may hold range 3 without retreating further
t = inv(1, 16, 40); p = to([1, 13], t, false); ok('fatigued target: hold 3', rng(p, t.pos) === 3, p);
console.log(`kite tests passed (${n})`);
