# RCL6 readiness (strategy review 2026-10-15 14:40 UTC+8)

**Why this topic.** W46N8 is RCL5 203.6k/1.215M and upgrading ~21/t (06:00–14:00 avg 17–23/t; 4.07 s/tick), so RCL6 lands
about **10-17 ~21:00 – 10-18 early morning UTC+8** (~1.01M left, ~48k ticks). The RCL5 switch-over (review 10-14) showed that what
the code does on the level-up night matters more than another model pass; the RCL5 build phase still cost ~8 h at 4–10/t
(10-14 22:00 – 10-15 06:00, 6 fixes overnight). RCL6 is also the start gate of the approved wall plan (v4) before novice ends 10-28 03:33.

## What the as-built code would do at RCL6

| # | Trigger | Behaviour | Effect |
|---|---|---|---|
| R1 | layout plan rcl6 | Places 10 ext (30k) + link 30,11 (5k), then **terminal 35,31 (100k)**, **3 labs (150k)**, extractor 40,24 (5k) (mineral container 39,24 would be a 6th container, refused by the RCL limit) | ~295k of build energy; **~260k for structures that do nothing**: no mineral-miner role, no lab/boost code, no market code |
| R2 | `spawn.targets` `T.upgrader = sites ? 1 : 2` | While any site exists only 1 base upgrader (+extras only with storage surplus, which never builds up) | Upgrading falls to ~10–12/t for the whole luxury build: 260k at ~21 e/t ≈ 12k ticks ≈ **14 h of upgrading lost; RCL7 ~14 h later** |
| R3 | `T.builder = sites>3 && cap>=1300 ? 2 : 1` | 2 builders for the 5-site terminal/lab queue | Same drain, plus 2 builder bodies upkeep |
| R4 | wall policy start `rcl>=6 && storage>=20000` (DEFENSE_PLAN v4, not coded yet) | Storage has **never exceeded 2.3k** (48h max; avg 135–1556 per 4h): supply-follows-demand spawns a 3rd upgrader at floor+1000 | As written the walls **never start** before 10-28 unless storage is allowed to bank |
| R5 | `T.hauler = rcl>=6 && links>=3 ? 1 : …` | Miner A now fills link 30,11 → ctl link; the lone home hauler keeps waiting on container A (only link-full overflow) | ~0.7 e/t upkeep for little work — patrol to measure (`idle_by_reason`) and drop to 0 if idle > 70% |

## Mineral economics (why the terminal/labs can wait)
- Mineral **O (oxygen), density 2: 35,000 per 50,000-tick regen**. A 10W extractor miner (1 per WORK per 5 ticks) empties it in ~17.5k
  ticks → ~0.5 O/t average.
- Market shard3 (read-only, 10-15): O avg 23.6–29.2 cr/day (5 days), best buy 32.0; energy avg 14–21 cr. 0.5 O/t ≈ 13 cr/t ≈ **0.9 e/t
  equivalent**, before terminal transfer energy (`amount × (1 − e^(−dist/30))`, ~60% of the amount for a 30-room deal) and miner upkeep.
- Payback of terminal + extractor + container (110k) at < 1 e/t equivalent: **> 100k ticks (≈ 5 days)** — and only if Misaki allows
  market selling. Labs need a 2nd mineral (bought = spending credits) before they can make anything.
- Overmind/TooAngel build terminal/labs at RCL6 because they run many rooms and a market module; for one energy-bound room with a
  defence deadline it is the wrong order.

## Shipped in this review (no-op until RCL6)
- **`plan.RCL6_MINERALS = false`** (`src/utils/plan.js`): terminal, labs, extractor and the mineral container are removed from the plan, so
  RCL6 builds only **source-A link 30,11 + 10 extensions (~35k, ~2 h)**. One switch turns the block back on.
- Test `tests/rcl6_gate.js` (in `scripts/check.js`).

## Plan for the RCL6 night (patrol watchpoints)
1. First RCL6 sites: extensions (5 at a time) then link 30,11. Expected dip ≈ 2 h, then upgrade ≥ 21/t; source A's 10/t now arrives
   by link (no A-hauler walk; link loss 3%).
2. Miner A transfers into link 30,11 (`miner.sink` refresh ≤ 100 ticks); `links.run` sends A → ctl link when < 400, else → hub.
3. Queen reaches the new extensions 30–34,35–36 and 32,26–27 (stamp-B style direct stops); spawn should be full again within ~300 ticks.
4. Home hauler: see R5.
5. **Walls (R4):** implement the v4 wall policy code before RCL6, and make its start reachable: after the RCL6 core build is done, hold
   upgrader extras until storage ≥ 20k (banking, not loss: ≈ 1k ticks of upgrade shifted), then walls draw per the approved budget table.
   Step 1 (all 38 barriers → 100k) ≈ 43k energy, step 2 (→ 300k) ≈ +76k; both fit well before 10-28.

## Decisions for Misaki (proposal)
- Minerals/market: keep terminal/extractor/labs off until (a) walls step 2 is done and (b) she decides whether to sell O on the market
  (earns credits; any credit *spending* stays her call). Recommended: revisit after 10-28.

## 2026-10-17 update — roads before walls (Misaki 17:40 UTC+8)
Walls are now LOW priority. After the core build the road plan runs first (docs/ROADS.md: home trunks → W45N8 → done; W45N7 road dropped 17:47);
`walls.phase()` returns `'roads'` until `Memory.roads.phase === 'done'`, so the R4 banking rule ("one upgrader until storage 20k") and
barrier sites start only after the roads. Emergency wall starts are unchanged. Watchpoint 5 above now applies after the road plan.

**Build hold (2026-10-17 21:00):** during the road plan no upgrader at all (`walls.noUpgrade`, docs/ROADS.md), safety upgrader
if `ticksToDowngrade < 20000`. After roads the R4 banking rule (1 upgrader until storage 20k) applies unchanged.
