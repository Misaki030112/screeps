// Home towers keep the road-plan tiles alive (W45N8 haul leg etc.), not only layout-plan tiles. node tests/tower_route_roads.js
// Strategy review 2026-10-20 11:4x: haul leg 44,19..48,15 / 39,24 at 34-52% with no repairer; old filter (P.any only) skipped them.
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, { Memory: {}, _: require('lodash'), STRUCTURE_ROAD: 'road', STRUCTURE_CONTAINER: 'container', STRUCTURE_RAMPART: 'rampart', STRUCTURE_TOWER: 'tower', RESOURCE_ENERGY: 'energy' });
const plan = require(src('utils/plan.js')), T = require(src('managers/tower.js'));
const P = plan.get('W46N8');
const road = (x, y, hits) => ({ structureType: 'road', pos: { x, y }, hits, hitsMax: 5000 });
for (const [x, y] of [[44, 19], [45, 18], [46, 17], [47, 16], [48, 15], [39, 24]]) {
  assert.ok(!P.any[plan.key(x, y)], `${x},${y} is not a layout-plan tile (why the old filter skipped it)`);
  assert.ok(T.upkeep(P, 'W46N8', road(x, y, 1700)), `haul leg ${x},${y} at 34% is a tower repair candidate`);
  assert.ok(!T.upkeep(P, 'W46N8', road(x, y, 3100)), `haul leg ${x},${y} at 62% waits (60% rule)`);
}
assert.ok(!T.upkeep(P, 'W47N8', road(44, 19, 100)), 'home road-plan tiles never apply to another room');
assert.ok(!T.upkeep(P, 'W46N8', road(2, 2, 100)), 'off-plan leftover road still left to decay');
const k = Object.keys(P.any).map(Number).find(i => P.any[i].type === 'road'), px = Math.floor(k / 50), py = k % 50;
assert.ok(T.upkeep(P, 'W46N8', road(px, py, 1000)), 'layout-plan road still repaired');
console.log('tower route roads ok');
