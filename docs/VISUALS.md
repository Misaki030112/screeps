# In-game route overlay (`src/managers/visuals.js`)

Draws every tick with RoomVisual: remote haul routes and home trunks as thin (0.09) dashed lines, opacity 0.5, one colour per route, split per room so routes cross room edges. Legend (Chinese, route + length in tiles) sits in the top-left corner of W46N8.

| Route | Colour | Source |
|---|---|---|
| 外矿 W45N8 | #ffd400 yellow | `layouts/remote_routes.js` |
| 外矿 W45N7 | #ff66cc pink | `layouts/remote_routes.js` |
| 主干 TR / BR / TL / W / S | cyan / green / orange / purple / red | `layouts/W46N8.js` `defense.trunks` |

Overlapping stems get a small lateral offset per route (±0.18 tile) so each line stays visible.

- Toggle: `Memory.visuals = { routes: false }` (off) / `delete Memory.visuals` (on, default).
- Skipped when `Game.cpu.bucket < 2000`.
- Polylines cached in heap, rebuilt at most every 500 ticks or when a route length changes. CPU per tick: `Memory.visualsCpu`.
- Remote routes are regenerated with `python3 tools/road_plan.py && python3 tools/export_routes.py`.
- Test: `tests/visuals.js` (run by `scripts/check.js`).
