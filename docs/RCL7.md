# Home W46N8 RCL7 readiness (strategy review 2026-10-19 18:4x UTC+8)

## Timing
- 10-19 18:29: RCL6 401.4k / 3.645M. Tick ~4.3 s (83742481 at 18:11 -> 83742731 at 18:29).
- Remaining 3.24M: at 23.6 e/t (live since 18:11) ~137k ticks ~6.9 d -> **~10-26 afternoon**; at the 6 h average ~19-20 e/t -> **~10-27 evening**.
- **04:4x refresh (10-20):** 3.049M left; 6 h 21.9 e/t → **~10-27 01:00**, 24 h 18.7 → ~10-28 04:40. Realistic home ceiling ~23 e/t (docs/MODEL.md 04:4x). reserve7 moves to W47N8 at its RCL5 (bd442b2) → ~9-10 h earlier.
- Novice protection ends **10-28 03:33**. RCL7 lands 0.5-1.5 days before it, so whatever RCL7 builds competes with the last wall/defence push.

## What RCL7 would build as the plan stood (plan.upTo(7), rcl === 7)
| item | cost | used by code? |
|---|---|---|
| spawn 2 at 30,34 | 15k | yes (main.js runs spawnMgr per spawn) |
| tower 3 at 39,23 | 5k | yes |
| 10 extensions (stamp C) | 30k | yes; all 50 ext hold 100 at RCL7 -> cap 2300 -> 5600 |
| link 4 at 32,34 (stamp B 'L') | 5k | **no**: filler link, only fed with STATIONARY_FILL on |
| 3 labs 33,22 / 34,20 / 34,23 | 150k | **no**: no lab code; the 3 RCL6 labs are empty |
| factory 35,30 | 100k | **no**: no factory code |
| **total** | **305k** | 250k (82%) idle |

250k idle = ~12k ticks of upgrading at ~21 e/t (~14 h of RCL8 delay), and builders + spawn time pulled away right at novice end.

## Second problem found
`spawn.targets`: `T.hauler = 0` at RCL7 once 4 links exist. With STATIONARY_FILL off the 4th link (32,34) is never fed, so this only
removed the one home hauler, and the hauler is the only carrier of the mineral run (container 41,24 -> terminal, roles/hauler.js
mineralRun). Mineral mining would have stopped silently at RCL7 (mminer spawns only while the container has room).

## Shipped (dormant until RCL7)
- `plan.RCL7_INDUSTRY = false`: factory and labs 4-6 are not planned. RCL7 = spawn 2 + tower 3 + 10 ext + link (~55k).
- Home hauler stays 1 at RCL7 unless STATIONARY_FILL is on.
- `tests/rcl7_gate.js` (in scripts/check.js); fails on the old hauler rule.

## Watch at RCL7 (patrol)
- Spawn 2 at 30,34: two spawns run spawnMgr in the same tick. Confirm no duplicate spawns of the same role (the engine adds the new creep to Game.creeps as spawning, but verify live).
- Capacity 5600: bodies are capped (builder 11 sets = 2200, upgrader 12W, queen 1200), so the spawn does not wait for 5600, but the 2 queens (800 carry each) need ~7 trips to refill 5000 extension energy. Check refill time with fillmeter (Misaki: refill speed = reaction speed).
- Wall step 1M opens at RCL7 (walls.STEPS[7]); budget rules unchanged.
- Upgrader cap: RCL7 has no 15 e/t limit; 12W bodies x spots is still the limit.

## For Misaki (not urgent, before ~10-26)
- Keep factory/labs 4-6 off until there is code for them (recommended), or turn them on at RCL7 anyway.
- Link 4 (32,34) costs 5k and does nothing without stationary fillers; build it anyway (plan approved 10-15) or defer it with the industry block.

## 2026-10-20 08:4x strategy review: RCL7 -> novice-end window, and what happens to storage after RCL7
- **ETA refresh:** RCL6 661.4k / 3.645M at t83754824 (2.984M left). 12 h rate 10-19 18:00 -> 10-20 06:00 = 225.7k / 10210 t = **22.1 e/t**
  (851 t/h) -> **~10-26 23:00**; last 1-2 h ~20.6 e/t -> ~10-27 11:00. reserve7 leaves home at W47N8 RCL5 (~09:00 today, +1.3 e/t) and
  the home-sent w8defender stops once W47N8 tower 24,8 stands, so the faster end is more likely. **Window to novice end (10-28 03:33): ~16-28 h.**
- **Post-RCL7 bill before novice end:** spawn 2 + tower 3 + 10 ext + link ~55k (sites; layout PRIORITY spawn > tower > extension) and wall
  step 2 (300k, ~69k). ~124k at ~25 e/t of surplus = ~5000 t (~6 h). Fits the window with margin, so **Misaki's "step 2 after RCL7" rule holds**.
- **How the flip works (checked in code):** at RCL7 `walls.stepHeld` is false -> `queen.storageFloor` = reserve + `walls.reserved` = 1300 +
  min(fund 50k, storage) > storage, so the ctl ferry stops and storage banks; above reserveE + 2k (17k) builders spawn (1 + surplus/4k),
  `repairJob` targets 300k. Upgrading continues only on what reaches the ctl directly (link A, remote rhaulers).
- **Latent bug found and fixed (cd9c423, deployed t83754849):** step 2 spends the 50k fund down to 0 (69k needed, accrual 2.3 e/t). Once
  fund < ~13.7k the floor (1300 + fund) dropped under `Memory.defense.reserveE` (15k) and at fund 0 to 1300: the ferry would have emptied
  storage to ~1.3k in peacetime right around novice end, and `defLow` then blocked builders and upgrader replacements (oscillation).
  The floor is now `max(reserve + reserved, reserveE)`. No-op at RCL6 (held path already returns reserveE; live t83754855 floor 15000,
  held true, errors 0). `tests/queen_floor_rcl7.js` fails on the old code (2/6).
- **RCL7 patrol watch (added):** storage must stay >= 15k after the fund runs out; builders on step 2 while storage > 17k; tower 3 built
  in the first site batch.
