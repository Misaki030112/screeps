# W46N8 Layout v2 — final RCL1–8 plan (LIVE since 2026-10-13; see LIVE section)

Files: `data/layout_W46N8_v2.json` (every structure by RCL, removals, fixed creep positions, routes),
`docs/layout_W46N8_v2.png` (final RCL8 plan), `docs/layout_W46N8_v2_rcl.png` (per-RCL strip),
`data/layout_compare.json` (candidate comparison). Generator: `tools/plan_v2.py` → `tools/export_v2.py` → `tools/render_v2.py`.

## Design in plain words
- **Hub (core stamp).** One stationary *manager* creep stands on **(36,30)** and touches, without moving:
  storage (37,31), terminal (35,31), hub link (37,29), factory (35,30), power spawn (36,29), spawn 3 (35,29) and
  2 extensions (37,30), (36,31). Before RCL8 the spawn-3 tile is the manager's entrance; at RCL8 spawn 3 spawns the
  replacement manager directly onto (36,30).
- **Source B is "free".** Its miner stands on **(38,32)**, which is next to both the source and the storage, so from
  RCL4 it transfers straight into storage — no hauler and no link for that source.
- **3 fast-filler stamps (5×5).** Each has 4 stationary filler creeps, a link in the middle, a container on one edge
  (entrance and buffer; containers are walkable) and a spawn on the opposite edge. Every extension/spawn in the stamp
  touches a filler, so refilling needs **zero walking and zero searching**: fillers take from the centre link /
  container and fill their fixed neighbours.
  - A (x33–37, y24–28) contains the existing Spawn1 (35,28); RCL2–4 extensions are all here.
  - B (x30–34, y32–36) with spawn 2 (30,34), built RCL5–6.
  - C (x28–32, y23–27), built RCL7–8.
  Bottom fillers are spawned in place by the stamp's spawn (`directions`); top fillers walk in over the container.
- **Links (6):** fillerA (35,26) + hub (37,29) at RCL5, source A (30,11) at RCL6, controller (30,30) at RCL7,
  fillerB (32,34) + fillerC (30,25) at RCL8. Source A link → controller/filler links; manager tops up filler links
  from storage via the hub link. After RCL7 there is no mining hauler at all.
- **Upgraders** stand still on (31,29) [controller container], (31,30), (31,31), (30,29): all within range 3 of
  the controller and next to the controller link (30,30).
- **Roads: 30 tiles in total** (v1 had 116). One trunk from the storage door (36,32) north along x=38 to source A,
  short spurs to the controller spot, filler entrances, mineral and labs. The same tiles serve every RCL; only
  haulers (until links), builders and walking-in of new stationary creeps use them.
- **Labs**: 4×4 stamp (33–36, 20–23) on the trunk, inputs (33,22)/(34,21) reach all 8 others.
  **Towers** (32,30),(32,31),(36,33),(37,33),(35,34),(36,34); **nuker** (38,23); **observer** (33,31);
  **mineral** container (39,24) + extractor (40,24).
- **Ramparts (27):** spawns, towers, storage, terminal, factory, power spawn, nuker, the manager tile and all filler
  tiles. (A full min-cut perimeter can be added later; not needed while the core is this compact.)
- **Containers never exceed 5** at any RCL (src B container removed at RCL4, src A at RCL6, controller at RCL7).

## Candidates compared (`tools/compare_layouts.py`)
| | v1 checkerboard (live) | **v2 hub + fast-filler (chosen)** | Bunker 13×13 / 11×11 |
|---|---|---|---|
| Road tiles | 116 | **30** | — |
| Walk to refill all 60 ext | ~69 tiles per full refill + `find` per tick | **0** (stationary fillers) | ~30 (bunker ring) |
| Storage→source B | n/a (hauler) | **0 (direct transfer)** | n/a |
| Storage→source A route | spawn→src 16 tiles (hauler) | 23 tiles (hauler only RCL2–5, link after) | — |
| Storage→controller | hauler / walking upgraders | 5 tiles, link from RCL7 | — |
| Fits with spawn at (35,28)? | yes | yes | **no** — 13×13 only at x10–24/y3–17, 11×11 only near (36,12); would need a new spawn |
| Est. CPU at RCL8 | 8–10 | **≈3** | ≈3–4 |

## Build order per RCL (from the JSON)
| RCL | New structures | Cumulative key counts |
|---|---|---|
| 1 | Spawn1 (exists) | — |
| 2 | 4 containers (src A 31,12; src B 38,32; controller 31,29; filler A 35,24), 5 ext (filler A), trunk roads (27) | ext 5 |
| 3 | 5 ext, tower 1 (36,33), ramparts spawn1+tower | ext 10, tower 1 |
| 4 | storage (37,31), 10 ext (filler A + 2 hub), ramparts on core; **remove src B container** | ext 20 |
| 5 | links: filler A + hub; filler B container; 10 ext (filler B); tower 2 | ext 30, links 2 |
| 6 | terminal, source A link, extractor + mineral container, 3 labs, 10 ext; remove src A container | ext 40, links 3, labs 3 |
| 7 | spawn 2 (30,34), factory, controller link, filler C container, 3 labs, tower 3, 10 ext; remove controller container | ext 50, spawns 2, links 4 |
| 8 | spawn 3 (hub), power spawn, filler B/C links, 4 labs, towers 4–6, nuker, observer, 10 ext | ext 60, spawns 3, links 6, labs 10, towers 6 |

## Roles (fixed positions, cached paths, no per-tick search)
All targets are positions/ids from the plan, resolved once and stored in memory. Moving creeps use a serialized path
stored in `Memory` (`Room.serializePath`, `moveByPath`), recomputed only on failure. Room-level checks such as
"is energy full?" run once per tick, not per creep.

| Role | Position / route | RCL2–4 (count × body) | RCL5–7 | RCL8 | CPU/tick each (est.) |
|---|---|---|---|---|---|
| miner A | (31,12) stand; container → link from RCL6 | 1 × WORK5 MOVE1–3 | 1 × WORK5 CARRY1 MOVE3 | same | 0.21 |
| miner B | (38,32) stand; container → storage from RCL4 | 1 × WORK5 MOVE1–3 | 1 × WORK5 CARRY1 MOVE3 | same | 0.21 |
| hauler A | route `srcA` (23 tiles) ↔ filler A container / storage | 2 × CARRY/MOVE | 1 until RCL6, then 0 | 0 | 0.25 moving, 0 waiting |
| filler | 4 tiles per stamp, never moves | 2 (A bottom) → 4 | 4–8 | 12 × CARRY4–6 MOVE1 | ~0.01 idle, 0.2 per transfer |
| manager | (36,30) | — | 1 × CARRY8–16 MOVE1 | 1 | 0.1–0.3 |
| upgrader | (31,29)/(31,30)/(31,31)/(30,29) | 2–4 × WORK-heavy | 2–3 | 1 × WORK15 (15/tick cap) | 0.21 |
| builder | cached paths to sites | 1–2 when sites exist | 1 | 0–1 | 0.3 while active |
| utility hauler | storage → towers, labs, nuker, B/C containers (until RCL8 links) | — | 1 | 1, mostly idle | 0.1 avg |
| mineral miner | (39,24) stand | — | 1 (RCL6+) | 1 | 0.05 (extractor cooldown) |

**CPU budget (20/tick):** RCL2–4 ≈ 2.5–3.5, RCL5–7 ≈ 3–4.5, RCL8 ≈ 2.5–3.5 (base memory/stats ≈ 0.5–0.8 included).
That leaves ~15 CPU for remote mining and a second room. (Assumes ~0.2 CPU per intent; measured today: 8 creeps on
the v1 search-based code use 1.4–2.8.)

## Migration from the live bot (needs approval)
- v1 extension sites at (36,25), (38,27), (38,29), (34,31) conflict with v2 (filler tile / trunk road / road) and
  would be removed; (36,31) is a v2 hub extension and stays.
- Existing neutral container (31,11) is replaced by (31,12); (38,32) is reused.
- Code: new `layout` manager reading v2 JSON (plus removals), new roles filler / manager / static upgrader,
  path cache util; spawn manager gets per-RCL role table above.

## LIVE since 2026-10-13 08:17 (UTC+8) — adjustments approved by Misaki
- Kept the existing tower **(36,29)** (it took the hub power-spawn slot; the manager can refill it from RCL5).
  Power spawn moved to **(36,33)** (RCL8). Towers by RCL: 3 (36,29) · 5 (37,33) · 7 (35,34) · 8 (36,34),(32,30),(32,31).
- Kept the controller container **(30,30)**: upgraders stand on (30,30),(31,30),(29,30),(31,31),(29,31);
  controller link **(30,31)** (RCL7); haulers deliver from (31,29)/(30,29)/(29,29).
- Pre-RCL5 there are no stationary fillers yet: one **queen** walks the fixed stops (filler tiles of stamp A + hub tile)
  and haulers help fill when the room is not full. Stationary fillers + manager switch on at RCL5 (links).
- Removed for v2: v1 roads (35,25),(33,26) immediately; v1 extensions (36,25),(38,27),(38,29),(34,31) are destroyed
  automatically **only after ≥5 non-conflicting extensions are built** (energy capacity never drops below 550).
  (36,31) stays (hub extension). Old off-plan roads are no longer repaired and will decay; container (31,11) is kept as
  a spare pickup until it decays.
- `tools/patch_v2_live.py` applies these adjustments to the planner output; images re-rendered.
