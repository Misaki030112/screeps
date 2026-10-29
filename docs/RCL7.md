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

## 2026-10-30 02:4x — STATIONARY_FILL readiness at home RCL7 (keep queens)

**Question:** flip `plan.STATIONARY_FILL` to true now that home is RCL7 with 4 links?

**Answer: NO.** Keep dual-queen regime through walls→300k and W47N8 RCL7. Re-evaluate at RCL8 (links l5/l6) or after an explicit hybrid design (manager + keep queens).

### Live (t83947497, Asia/Hong_Kong 02:50)
- `STATIONARY_FILL=false`; dual queens; 1 home hauler; manager 0; fillers 0.
- Links (LINK_PLAN A): hub 37,29 (799), ctl 30,31 (776), srcA 30,11 (800), **l4 stamp-B 32,34 (0)** — unused under queens.
- Storage ~11k (fundSpend FLOOR 5k / reserveE 15k tug); walls.fund ~42.9k; wall min ~197k → 300k.

### What enabling does today (`spawn.targets` + `plan.js`)
| Effect | Detail |
|---|---|
| `fillersOn` | `STATIONARY_FILL && rcl>=5 && links>=2` → **true** |
| Queens | `T.queen = 0` — both queens recycled; **storage→ctl ferry dies** unless manager+ctl link path already carries it |
| Fillers | `T.filler = 4` — assigned to first 4 `positions.fillers` (stamp **A** only: 34,25/34,27/36,25/36,27) |
| Manager | `T.manager = 1` at 36,30 |
| Hauler | with 4 links + flag on → `T.hauler = 0` (mineral run disappears) |
| Link plan | drops LINK_PLAN override; uses v2 json links (35,26 / 30,11 / 30,31 / …) — **site churn risk** vs live hub/ctl coords |
| Stamp containers | RCL7 K-tile 30,27 would re-enter the plan |

### Gaps vs a working stationary network
1. **Coverage:** 12 filler stand tiles across stamps A/B/C; code only spawns **4** (stamp A). Stamps B/C (20+ extensions + tower 2 / spawn 2) lose queen service with nothing to replace it — same G1–G3 failure mode as docs/RCL5.md.
2. **Stamp links incomplete until RCL8:** LINK_PLAN puts stamp-C link **l5 30,25** and stamp-A link **l6 35,26** at RCL8. Live l4@32,34 is stamp B only and sits at E=0 under queens.
3. **Ferry:** queens are still the only reliable storage→ctl path under fundSpend / defLow. Manager alone does not inherit the queen standby ferry.
4. **Overmind / TooAngel:** Hatchery keeps **mobile queens** (QueenOverlord) through mid-game; bunker “manager” is RCL8 logistics, not a drop-in for killing queens at first RCL7. Stationary fast-fillers appear in bunker designs with **per-stamp** link+container pairs and enough CARRY bodies — we have neither the body count nor the link set yet.
5. **Stand-tile ramparts:** DEFENSE_PLAN 10-15 left 13 empty stands decaying while flag off. Re-eval at RCL7: **still leave decaying** (flag stays off). Revisit only when STATIONARY_FILL actually turns on.

### Preconditions to flip (checklist — all required)
- [ ] `T.filler` covers all served stamps (or hybrid: keep ≥1 queen for B/C + ferry)
- [ ] Stamp A + C filler links live (RCL8 l5/l6) **or** redesigned LINK_PLAN that does not thrash hub/ctl
- [ ] Manager (or equivalent) proven to replace storage→ctl ferry under fundSpend / reserveE
- [ ] Mineral hauler path preserved (or mminer→terminal transfer coded) so `T.hauler` can go 0 safely
- [ ] Gate test + sim: spawn refill ≥90%, upgrade not collapsing to ~10 e/t, no link site thrash
- [ ] Misaki not required for the flip once checklist green (standing “continue roadmap”); still **propose** if hybrid changes spawn economy materially

### Reprioritise (unchanged order, stationary deferred)
1. Home walls min → **300k** (fundSpend; ETA ~12–18 h Asia/Hong_Kong from ~02:50)
2. W47N8 RCL7 (~**2026-10-31 21:45** Asia/Hong_Kong at ~22 e/t) → tower3@22,7 + spawn2@33,30; factory OFF
3. Lab ramparts → raise toward RCL targets (sites already placed 23:4x; live ~423k covering 3 labs)
4. Colony storage ≥20k → minerals + K send; then KO≥900 → boost
5. Barriers →1M; **then** STATIONARY_FILL / hybrid at RCL8
