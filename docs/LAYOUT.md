# Base layouts

## Options considered
- **Overmind bunker** – fixed 13×13 stamp with ramparts around the perimeter; very defensible, needs a big open square.
- **Hivemind / dynamic planner** – scores candidate centres, places core, labs, extension clusters ("flowers"), then
  computes ramparts via **min-cut** between exits and core.
- **Checkerboard / diagonal road grid ("dt-style")** – buildings on one parity, roads on the other; roads connect
  diagonally so every structure touches a road. Fits irregular terrain well and is trivial to compute.

W46N8 has 25% swamp and a lot of walls around the spawn (spawn was already fixed at 35,28), so a 13×13 bunker does not
fit. We use a **checkerboard around the existing spawn + a 4×4 lab stamp**, with per-structure ramparts (min-cut later).

## Generator
`tools/plan_layout.py W46N8 35 28` →
- `data/layout_W46N8.json` (by RCL: structure type → [[x,y],…]; roads; ramparts)
- `src/layouts/W46N8.js` (same plan as a module for the bot)
- `docs/layout_W46N8.png` (render; number on tile = RCL it unlocks)

Steps: Dijkstra roads spawn→each source / controller / mineral (plain 2, swamp 10, road 1) with containers at the end,
source links next to containers, controller link within range 3; BFS over the road-parity grid from the spawn; nearest
building-parity tiles get core (storage, core link, tower, spawn 2, terminal, towers, spawn 3, factory, power spawn);
lab stamp = nearest open 4×4 (diagonal road, inputs at (1,2)/(2,1)); then 60 extensions by distance; nuker, observer.
Ramparts on spawns, towers, storage, terminal.

## W46N8 plan summary
60 extensions, 6 towers, 3 spawns, storage, terminal, 4 links, 10 labs, factory, power spawn, nuker, observer,
4 containers, extractor, ~123 road tiles, 11 ramparts. The bot places sites via `src/managers/layout.js`
(priority: spawn, extension, tower, container, storage, link, road, rampart, …; max 5 open sites).

Known limits: ramparts only on key structures (no perimeter min-cut yet); only 4 links (2 more can be added at RCL8).
