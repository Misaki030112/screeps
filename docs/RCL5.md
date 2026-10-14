# RCL5 transition readiness (strategy review 2026-10-14 14:40 UTC+8)

**Why this topic.** W46N8 is at RCL4 288.6k/405k and upgrading ~20/t (2h avg, 24/t when the ctl container is fed), so RCL5 lands
**tonight ~21:00–22:00 UTC+8** (116k left; ~4.0 s/tick measured over 24h). RCL5 is also the gate for both open strategy items:
tower #2 (defence before novice ends 2026-10-28 03:33) and the "revisit expansion after RCL5 + defence assessment" decision.
A code read-through of everything keyed on `rcl >= 5` found the RCL5 role switch-over would **cut upgrade speed roughly in half**
the moment two links exist. That is more actionable than more model math (economy is already at ~ideal 23.5/t when fed) or another layout benchmark.

## What the code did at RCL5 (before this review)

| # | Trigger | Behaviour | Effect |
|---|---|---|---|
| G1 | `rcl>=5 && links>=2` (`spawn.targets`) | `T.queen=0`, 4 stationary fillers on stamp **A** only | The queen is the **only** storage→ctl carrier (standby ferry, e7c3966/f0127a3). Without it, source B (miner→storage, 10/t) + remote (~8/t) only feed spawns; upgraders get source A's ~10/t → upgrade **~10/t instead of ~20–24/t**. |
| G2 | same | Stamp **B** gets its 10 RCL5 extensions (34,32…31,34), but no filler/queen serves stamp B | Spawn never full → home hauler (14C7M A→ctl) is diverted onto the fill route below 90% → ctl feed drops further; `lastFull` stale → bodies shrink after 300 ticks. |
| G3 | same | Tower 2 (37,33) touches neither the manager tile nor a stamp-A filler | Only filled by haulers when < 600 (below the ≥800 combat-reserve policy). |
| G4 | `storage && rcl>=5` | Manager (CARRY16 MOVE1, 850e) spawns at once and parks on 36,30 | 36,30 is also a queen stop → queen/manager tile contention (swap ladder) while both live. |
| G5 | layout `PRIORITY` | extension before tower | With `MAX_SITES=5`, tower 2 waits until ~7 of 10 extensions are built (~21k energy, several hours). Overmind builds **spawn → tower → extension** (`priorities_structures.ts`). |
| G6 | tower | 2 towers × repair whenever > 800 energy, rampart target 50k → 100k | 16+1 ramparts × +50k = ~850k hits ≈ **10.6k energy**, drained at up to **20 e/t** (both towers, queen tops them back to 900) right when RCL5 sites also need energy. RCL4 showed the same pattern (storage 1040→200, 10-14 02:45). |
| G7 | layout plan | "utility hauler" (storage→towers/B container) in LAYOUT_V2 role table was never implemented | Root of G2/G3. |

The design intent (docs/LAYOUT_V2.md) is right for RCL7–8, but the RCL5 slice of it is incomplete: one link pair (filler A + hub) can
feed stamp A only, and nothing replaces the queen's storage→ctl ferry until the controller link (planned RCL7).

## Shipped in this review (small, reversible)

1. **`plan.STATIONARY_FILL = false`** (one switch, `src/utils/plan.js`): while off, the RCL2–4 regime continues at RCL5+
   (queen stays, no fillers/manager) and **link sites are not placed** (saves 10k build energy and avoids building a link that
   the plan decision below might move). The queen already serves stamp B + tower 2 via its "visit directly" stops.
2. **Build order** `spawn → tower → extension → …` (Overmind order): tower 2 is the first RCL5 site.
3. **Rampart growth throttle** (`tower.js`): repairing a rampart that is already above the *previous* RCL's target ("growth") runs
   only on every 5th tick → ≤ 2 e/t per tower; below that (fresh/damaged ramparts, combat aftermath) full speed. 50k→100k still
   completes in ≈ 3 h with 2 towers, instead of competing with tower/extension sites at 20 e/t.

Tests: `tests/rcl5_gate.js` (spawn targets at RCL5 with 2 links, build order, throttle rule).

## Proposal for Misaki — RCL5–6 link plan (decision needed before `STATIONARY_FILL` is turned on)

| | A. **Controller link first** (recommended) | B. Original v2 (filler A + hub) | C. No links yet |
|---|---|---|---|
| RCL5 links | hub 37,29 + **controller 30,31** (already the planned RCL7 spot; touches all 5 upgrader spots) | filler A 35,26 + hub 37,29 | none |
| RCL6 (3rd link) | source A 30,11 → ctl link: retires the 14C7M A hauler | source A 30,11 | — |
| Fill network | queen through RCL6 (stamp A stops + direct visits); stationary fillers from RCL7 with the 4th link | fillers stamp A at RCL5; **still needs** stamp-B filler/utility hauler + a new storage→ctl carrier | queen |
| New code | manager on at RCL5 (feeds hub link via `linkWant`, already coded); queen drops the hub stop while a manager lives | utility hauler role, stamp-B fillers, ferry replacement (G1–G3, G7) | none |
| Upgrade effect | removes queen ferry dead-bands (≈ +0–2 e/t at RCL5); at RCL6 A's 10/t reaches upgraders with no walking (hauler upkeep −0.7 e/t) | ≈ neutral once all gaps are built; −50% if switched on as is | today's ~20–24/t |
| Cost | 2×5k links + manager 0.57 e/t; link loss 3% (~0.5 e/t) | same + extra roles | 0 |

Overmind's link order is the same as A: *upgrade site first, then mining sites by decreasing distance*
(`RoomPlanner.nextNeededLinkAnchor`). Note Overmind only builds an upgrade link when the controller is ≥ 10 tiles from storage
(`UpgradeSite.settings.minLinkDistance`); ours is 7, so at RCL5 alone A is a robustness gain, the real payoff is the RCL6 source-A → controller pair.
Nothing is demolished by any option (no links exist yet).

## Defence assessment at RCL5 (input for the "expand after RCL5" decision)

| Item | Now (10-14 14:40) | After RCL5 (proposed order) |
|---|---|---|
| Towers | 1 at 36,29, 1000/1000 | + 37,33 first site. Combined damage: spawn/storage/stamp B/source B **1200/t**, upgraders 1110, controller 990, east exit 480, source A 360, west exit 300 |
| Ramparts | 16 × 50–57k (target 50k ✓) | target 100k (Overmind `barrierHits[5]=1e5`, same as ours), growth throttled ≤ 4 e/t total |
| Safe mode | 3 available; never auto | unchanged — Misaki only |
| Threats 48h | BustJetter scout traffic only at home (106 low episodes, MOVE4 TOUGH4, 0 damage); Invaders: 4 W45N8 episodes (one 5-HEAL boosted group 04:56 → FSM WAIT, correct), 1 home Invader 10-13 17:29 | Fandalah (W44N8, east of the remote) **RCL5 → 6** since 10-13. Council players are the only player risk until 10-28; RCL8 neighbours (drtk712 W46N9, FungousCoast245 W46N7) can reach us only via W47N8/W45N8 (home has no N/S exits) after 10-28 |
| Remote defender | armed=true, defender body 5RA6M1H (1300) | unchanged; cap 1800 at RCL5 leaves the 1300 reserve easier to hold |

Expansion remains **shelved**: none of this changes the 10-25 deadline review (min-cut outer ramparts, safe-mode decision tree).

## Watchpoints for the patrol at/after RCL5
- First RCL5 sites = tower 37,33 + 4 extensions (no link sites). Queen T stays 1; no filler/manager spawned.
- Queen reaches stamp B extensions + tower 2 (direct stops); `idle_by_reason` queen `target_full` should drop (more work), hauler should not walk the fill route above 90%.
- Upgrade during the ~40k build (tower + 10 ext + container + road) falls to 1 base upgrader + storage-surplus extras — expected ≈ 2–3 h; afterwards back to ~20–24/t.
- Ramparts climb 50k→100k at ≤ 4 e/t; storage must not fall below the 1300 defender reserve because of towers.

## Decision record — link plan A (Misaki 2026-10-14 ~15:20 UTC+8: "哪种收益效率更高就用哪个")
Check against the table above: C keeps ~20–24/t with 0 cost but no RCL6 gain; B is ≈ neutral only after 4 extra roles and −50% as-is;
A is ≈ +0–2/t at RCL5 (no queen walk to ctl; −0.5/t link loss; no manager needed since the queen fills the hub) and +~10/t of
walk-free source-A delivery at RCL6 (A hauler retired, −0.7/t upkeep). **A has the highest net efficiency → adopted.**

Implemented:
- `plan.LINK_PLAN = { hub 37,29 @RCL5, ctl 30,31 @RCL5, srcA 30,11 @RCL6 }` — single source of link positions while
  `STATIONARY_FILL` is false (overrides the v2 json links 35,26 / 30,11@6 / 30,31@7). `STATIONARY_FILL` stays **false**: queen through RCL7, no fillers/manager.
- Build order unchanged by design: spawn → tower → extension → container → storage → **link** → road (tower 2 first, links
  after the 10 extensions; ~10k for 2 links).
- `links.js`: senders (source link, hub) transfer to the ctl link when it is < 400 and the sender holds ≥ 400.
- Queen standby: when both links exist and the ctl link is < 400, ferry storage surplus above the defender floor into the hub
  link (2 tiles from storage) instead of walking to the ctl container; falls back to the container if the hub is full.
- Upgraders: controller link first, then container (unchanged).
- Tests: `tests/rcl5_gate.js` (plan A positions, link transfer rules), `tests/queen_standby.js` (hub ferry, floor kept).

Expected: during the RCL5 build (~40k: tower, 10 ext, container, 2 links) upgrade ≈ base-upgrader level for ~2–3 h; afterwards
~24/t (2×12W cap) with fewer feed gaps; RCL6 + source-A link frees the A hauler.
