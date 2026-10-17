# RCL6 road plan (Misaki 2026-10-17 17:40 UTC+8)

**Order after RCL6:** core build (10 extensions + source-A link 30,11) → roads → only then walls/ramparts. Walls are LOW priority.
Code: `src/managers/roads.js` (runs only at `controller.level >= 6`), state `Memory.roads = {phase, prog, log, bad}`.
`walls.phase()` returns `'roads'` (no banking, no upgrader hold, no barrier sites) until `Memory.roads.phase === 'done'`.
Emergency wall starts (approved earlyWalls threat trigger; post-novice player combat in home) still override.

Switches (console, no redeploy): `Memory.roads.off = true` pause site placement · `Memory.roads.skip = true` un-gate walls now ·
`Memory.roads.phase = '<phase>'` jump.

## Phases (live terrain + structures, 2026-10-17 17:5x UTC+8)

| # | Phase | Tiles | Already road | New | Swamp (new) | Build energy | Done when |
|---|---|---|---|---|---|---|---|
| 0 | core | 10 ext + link | – | 11 | – | ~35k | no non-road sites at home, 40 ext, 3 links |
| 1 | home: wall-gate trunks TR(6) W(26) S(9) + home leg of both haul routes (38,30→49,14 / 49,21) | 58 | 9 | 49 | 5 | 20.7k | every tile road |
| 2 | W45N8: route 0,14 → container 13,11 | 13 | 1 (2,12) | 12 | 2 | 6.0k | every tile road (needs vision) |
| 3 | W45N7: W45N8 0,21 → 21,49 leg + W45N7 21,0 → container 21,15 | 50 | 0 | 50 | 18 | 36.6k | every tile road |
| 4 | done → walls (v4 policy: bank 20k, then barrier steps) | | | | | | |

Total roads ≈ **63k energy** (plus core 35k). Controller tile 30,30 (container) is excluded; 40,23 (RCL8 tower) is kept as road until RCL8.
Sites: ≤5 open road sites per room per phase, refreshed every 50 ticks. Home road sites are whitelisted in `layout.js`.

### Remote routes (tools/road_plan.py → `src/layouts/remote_routes.js`, matches the fixed exits creeps use in `remote.CFG`)
- **W45N8**: storage 38,30 → exit **49,14 / 0,14** → container 13,11. Length **30** (home 17, W45N8 13). Swamps: W45N8 2,12 (built) + 2 more.
- **W45N7**: storage 38,30 → exit **49,21 / 0,21** → W45N8 south → exit **21,49 / 21,0** → container 21,15. Length **67**
  (home 17, W45N8 34 with 15 swamp, W45N7 16 with 3 swamp). Never touches BustJetter's site 22,15.

## Builders / repair
- Home sites: normal builder rule (1, or 2 when >3 sites and cap ≥1300). Note: open home sites keep the base upgrader quota at 1.
- Remote sites: 1 builder (refills from the W45N8 / W45N7 container, keeps 400); **2 builders** during W45N8/W45N7 phases when there are
  no home sites, storage ≥5k and cap ≥1300. W45N7 sites are reached via the fixed exits (`remote.route` + `exitTile`).
- Repair: builder repairs route roads <50% (home trunks <80% via `repairables`); a builder is spawned when any remote route road <40%.
  Remote containers stay with the rminers (existing).

## Hauler change (`spawn.js`)
When a remote's phase is complete (`roads.paved(r)`): rhauler body **16C8M (1200e, 800 carry, 2C:1M = 1 tile/t loaded on road)**
instead of 8C8M (800e, 400 carry), and target `pavedHaulers`: W45N8 2→**1**, W45N7 5→**3** (patrol may cut to 2 if the container stays low).

Model (metrics/road_plan.json): W45N8 8C8M today rt 72 → 16C8M paved rt 64, haulers needed 1.8 → 0.8.
W45N7 8C8M today rt 210 (need 5.25) → 16C8M paved rt 138 (need 1.73).

| | today | paved | Δ |
|---|---|---|---|
| hauler upkeep W45N8 | 2×800/1500 = 1.07 e/t | 1×1200 = 0.80 | −0.27 |
| hauler upkeep W45N7 | 5×800 = 2.67 e/t | 3×1200 = 2.40 (2 → 1.60) | −0.27 (−1.07) |
| road decay (all 121 tiles) | 0 | ≈ 0.25 e/t | +0.25 |
| road wear (1 hit / body part / step) | 0 | ≈ 0.7–0.9 e/t | +0.8 |
| net | | | **≈ −0.3 … +0.3 e/t**, −4 creeps (CPU ~−0.5) |

**Honest read:** remote throughput is already capped by the sources (each ~9–10 e/t delivered), so roads do not add income; they
cut hauler bodies/creeps and roughly pay their own upkeep. The 42.6k for remote roads does not pay back in energy; benefits are fewer
creeps/CPU, faster flee/return from remotes, and no swamp fatigue. Phase 1 (home trunks, 20.7k) is needed for the wall build anyway.
Time at ~10–20 e/t spare: phase 1 ~1.5–2.5 h, phase 2 ~0.5 h, phase 3 ~3–4 h (+ walking).

## Patrol (state/next_iteration.json)
Each patrol: read `Memory.roads` (phase, prog road/site/open/unseen, bad), confirm sites exist in the current phase room, builder count,
storage trend, and that `walls.phase` is `roads`. Stuck >2 h in a phase (no prog change) → investigate (`bad` codes, vision, paused).
