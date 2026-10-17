# RCL6 road plan v2 (Misaki approved 2026-10-17 22:33 UTC+8; deployed a839e9f + fix c907aae)

**v2 order = economic value** (tools/road_justify.py: Dijkstra on real terrain, 30-day cost = build + decay + wear + hauler time;
traffic from creep_ticks 24h; maps out/roads_v2_W46N8.png, out/roads_v2_W45N8.png):

| # | Phase | Tiles | Notes |
|---|---|---|---|
| 0 | core | 10 ext + link | done 21:50 |
| 1 | haul: storage 38,30 → 48,15 (W45N8 route home leg) | 16 | 12 already road; new 39,24 40,23 47,16 48,15 (1.2k). 40,23 = RCL8 tower → detour 38,24/37,23 at RCL8 |
| 2 | W45N8: 1,13 → 12,10 | 12 | rerouted onto the plain y9-11 band haulers walk (4,11 5,11 6,10 7,9 8,9 9,9 10,9); 0 new swamp (v1 had 4,10 5,9). 2,12 swamp already road. ~3.3k |
| 3 | econ: 35,26 36,25 34,25 35,31 | 4 | unroaded home tiles >=300 hauler/queen steps/day; 35,26 = RCL8 link |
| 4 | home: wall-gate trunks TR, S, W | 37 | 0 traffic, net negative economically; kept last by Misaki's decision |
| 5 | done → walls | | |

- Exit tiles (49,14 / W45N8 0,14) are NOT in the plan: createConstructionSite on room edges returns ERR_INVALID_TARGET (-7).
- No swamp-free path from storage to W45N8 exists (swamp belt ~x33-44,y20-27); all 6 swamps on the route were already road.
- Sites: BATCH 15 per room; replan every 50t, every 10t while a phase has no open sites. One-shot migrate (Memory.roads.v2):
  v1 phase 'home' → 'haul', 0-progress trunk sites removed.
- Builders: body cap 8W8C8M; build hold: 3rd at storage>=3000 & sites>=3, 4th at storage>=6000 & sites>=6.
- After phase W45N8 completes (paved('W45N8')), W45N8 haulers → 1x 16C8M.

---
# (v1, superseded) RCL6 road plan (Misaki 2026-10-17 17:40 UTC+8; W45N7 road dropped 17:47)

**17:47 decision:** only the short remote road (W45N8) is built. No W45N7 road phase; the W45N7-only home leg (45,18→49,21)
is dropped (the shared leg 38,30→45,18 stays as part of the W45N8 route). W45N7 haulers stay 5× 8C8M. After W45N8 → `done` → walls.

**Order after RCL6:** core build (10 extensions + source-A link 30,11) → roads → only then walls/ramparts. Walls are LOW priority.
Code: `src/managers/roads.js` (runs only at `controller.level >= 6`), state `Memory.roads = {phase, prog, log, bad}`.
`walls.phase()` returns `'roads'` (no banking, no upgrader hold, no barrier sites) until `Memory.roads.phase === 'done'`.
Emergency wall starts (approved earlyWalls threat trigger; post-novice player combat in home) still override.

Switches (console, no redeploy): `Memory.roads.off = true` pause site placement · `Memory.roads.skip = true` un-gate walls now ·
`Memory.roads.phase = '<phase>'` jump.

## Phases (live terrain + structures, 2026-10-17 UTC+8)

| # | Phase | Tiles | Already road | New | Swamp (new) | Build energy | Done when |
|---|---|---|---|---|---|---|---|
| 0 | core | 10 ext + link | – | 11 | – | ~35k | no non-road sites at home, 40 ext, 3 links |
| 1 | home: wall-gate trunks TR(6) W(26) S(9) + home leg of the W45N8 route (38,30 → 49,14) | 54 | 9 | 45 | 5 | 19.5k | every tile road |
| 2 | W45N8: route 0,14 → container 13,11 | 13 | 1 (2,12) | 12 | 2 | 6.0k | every tile road (needs vision) |
| 3 | done → walls (v4 policy: bank 20k, then barrier steps) | | | | | | |

Roads total **25.5k energy** (plus core 35k). Controller tile 30,30 (container) excluded; 40,23 (RCL8 tower) is road until RCL8.
Sites: ≤5 open road sites per room per phase, refreshed every 50 ticks. Home road sites are whitelisted in `layout.js`.

### Remote route (tools/road_plan.py → `src/layouts/remote_routes.js`, the fixed exit creeps use in `remote.CFG`)
- **W45N8**: storage 38,30 → exit **49,14 / 0,14** → container 13,11. Length **30** (home 17, W45N8 13); W45N8 swamps 3 (2,12 built).
- W45N7 (not paved): 67 tiles, exit 49,21 / 0,21 then 21,49 / 21,0, 18 swamps — would cost 36.6k + ~0.6 e/t upkeep for ≈0 net.

## Builders / repair
- Home sites: normal builder rule (1, or 2 when >3 sites and cap ≥1300). Note: open home sites keep the base upgrader quota at 1.
- Remote sites: 1 builder (refills from the W45N8 container, keeps 400); **2 builders** during the W45N8 phase when there are
  no home sites, storage ≥5k and cap ≥1300.
- Repair: builder repairs W45N8 route roads <50% (home trunks <80% via `repairables`); a builder is spawned when any remote route road <40%.
  Remote containers stay with the rminers (existing).

## Hauler change (`spawn.js`)
W45N8 only: when phase W45N8 is complete (`roads.paved('W45N8')`), rhauler body **16C8M (1200e, 800 carry, 2C:1M)** instead of
8C8M, target `pavedHaulers` 2 → **1** (model: 16C8M paved rt 64, need 0.8). Upkeep 1.07 → 0.80 e/t (−0.27); W45N8 road decay+wear
≈ +0.25 e/t → about break-even, −1 creep, no swamp fatigue on the short haul. **W45N7: unchanged, 5× 8C8M** (`paved('W45N7')` is always false).

## Patrol (state/next_iteration.json)
Each patrol: read `Memory.roads` (phase, prog road/site/open/unseen, bad), confirm sites exist in the current phase room, builder count,
storage trend, and that `walls.phase` is `roads`. Stuck >2 h in a phase (no prog change) → investigate (`bad` codes, vision, paused).

## Patrol checklist after RCL6 (every 15 min; source: state/next_iteration.json road_plan.each_patrol)
phase & prog vs last patrol · site count/locations (<=5/room, never W45N7) · builder count/state · queen/miners/haulers/remote creeps alive ·
energy not starved (storage >= 1300) · errors 0 · CPU · walls.phase === 'roads' until done · stall >2h -> investigate + tell Misaki.
2-hour briefing: one line with road phase, tiles built/total, sites, builders.

## Review 2026-10-17 (pre-RCL6)
- Fixed: invalid Memory.roads.phase (console typo) crashed run every 50t -> now reset to 'core' (re-checks, cheap).
- Changed: walls.phase 'roads' now also holds upgraders at 1 (as 'bank'), so road builders are not starved by upgraders.
- Added tests/roads_transition.js (RCL5->6 sim: gate, init, core->home->W45N8->done, batch, no vision, paused, off, RCL drop).
- Residual: home trunk tile 40,23 is under the RCL8 tower plan (road must be removed before that tower, RCL8 only).
- Changed (patrol 10-17 19:40): in walls.phase 'roads' the held upgrader is spawned 6W1C1M (700e, ~6/t) instead of 12W (spawn.bodyEnergy buildMode), so builders get the spare ~6/t. Measured before: upgrade 13.9/t, build 5.9/t, storage -4.2/t. Full size returns automatically when roads are done.

## Build hold — no upgrading during the road plan (Misaki 2026-10-17 21:00 "先停止升级，全力基建")
- `walls.noUpgrade(room)`: true while RCL6–7, `walls.phase === 'roads'` (core → home → W45N8), `ticksToDowngrade >= 20000`
  (`walls.UP_SAFE`) and `Memory.roads.upgrade` not set. Console override `Memory.roads.upgrade = 1` restores the 1×700e upgrader.
- While true: spawn target upgrader 0; the live upgrader spends what it carries, then recycles at the spawn; haulers skip the
  controller container (feed storage); queen does not ferry storage → controller/hub link; links do not send to the controller
  link; builders may draw from the controller container / link leftovers.
- Safety: timer < 20000 → hold off automatically → the 1 minimal (700e 6W1C1M) upgrader spawns until the timer is back up.
- Builders: 2 normally (sites > 3); a 3rd while the hold is on, ≥ 3 sites open and storage ≥ 3000.
- After `Memory.roads.phase === 'done'`: walls phase `bank` → 1 upgrader at normal size until storage reaches 20k
  (walls start), so storage accumulates; then normal supply-follows-demand upgraders. Tests: `tests/build_hold.js`.
