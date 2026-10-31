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
- Wall STEPS[7]=300k then STEPS next=1M; **08:4x peacetime `stepHeld` holds at HOLD_STEP_RCL7=300k** so fundSpend does not auto-open 1M. Resume via threat/siege or `Memory.defense.pushBarrier=true`.
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

## 2026-10-30 08:4x — post-300k STEP at RCL7 (hold vs auto 1M)

**Question:** when home walls min lands on STEPS[7]=300k, should fundSpend immediately open the next STEP (1M)?

**Answer: NO (peacetime).** Hold at 300k until colony RCL7 / soft ramps / minerals progress, or Misaki/`Memory.defense.pushBarrier` resumes.

### Why
- Next STEP is **1M**. Lifting 41 walls × ~(1M−300k)/100 ≈ **~287k e** — would crush home upgrade for days while W47N8 still needs ~34 h to RCL7 and storage sits ~13–15k.
- Roadmap already ordered **walls→300k → colony RCL7 → minerals → barriers 1M**. Auto-open contradicts that.
- **Overmind:** `barrierHits[7]=1M` but `fortifyDutyThreshold=500k` storage before routine fortify. We lack 500k storage; holding the step is the equivalent gate (cheaper than waiting for a storage threshold we will not hit under supply-follows-demand + reserveE 15k).

### Code (`src/managers/walls.js`)
- `HOLD_STEP_RCL7 = 300000`; RCL≥7 peacetime `stepHeld` when `tgt > HOLD_STEP_RCL7`.
- Escape: `threat(room)` / siege, or `Memory.defense.pushBarrier` truthy.
- RCL<7 still holds at `HOLD_STEP` 100k (unchanged).
- Tests: `tests/walls_barriers.js` case "RCL7 peacetime hold at 300k".

### Reprioritise
Unchanged order; **1M is now explicit opt-in** (pushBarrier or later strategy when storage/colony ready), not an automatic fundSpend consequence of finishing 300k.

## Post-300k energy reallocation (strategy 11:4x, 2026-10-30 ~11:45 Asia/Hong_Kong)

**Question.** Once peacetime walls hit `HOLD_STEP_RCL7` (300k) and `stepHeld` flips true, how does energy leave wall builders and return to storage / upgrade / colony RCL7 / minerals — without starving the 15k defense floor?

**Live context (tick ~83954890).** Home RCL7 walls min ~262k climbing (~+10k / 30 min → ~1.8–2 h to 300k). `fundSpend=true`, `stepHeld=false`, storage ~14k under reserveE 15k, fund ~35.5k. Colony W47N8 ~32 h to RCL7. Remotes SAFE. Hostiles 0. Deploy `2ff5c0d`.

### Exit criteria (already coded — no flip flag)

| Condition | Effect |
|-----------|--------|
| `stepHeld` (RCL≥7, peacetime, all barriers ≥300k, no `pushBarrier` / threat) | `fundSpend` → **false** same tick (`walls.js`) |
| `wantBuilder` / `repairJob` | Off while held (unless threat / push) |
| `reserved` (fund) | 0 while held → queen `storageFloor` = `reserveE` (15k) |
| Builders | Starve out / recycle; no new wall builders |
| Income | Banks into storage toward ≥15k (no builder drain) |
| Upgraders | `defLowUpgraders(held=true)` restores target when `storage ≥ reserveE − UP_DIP` (13k) |

So the "exit" is automatic: reaching the hold **is** the exit. No Memory flag, no manual Misaki action. Tests: `tests/walls_barriers.js` ("post-300k fundSpend exit"), `tests/spawn_upgraders.js` (held + UP_DIP).

### Recovery sequence (expected after first 300k tick)

1. **0–~30 min:** builders die off; storage climbs from dip (~9–14k) toward 15k at net surplus (~8–12 e/t typical peacetime with remotes).
2. **storage ≥13k:** upgrader count returns (ferry still stops at 15k floor — upgraders eat ctl container/link, not storage below floor).
3. **storage ≥15k stable:** `defLow` clears; normal spawn mix; home surplus feeds colony claim/upgrade pipeline.
4. **Do not open 1M** unless Misaki sets `Memory.rooms.W46N8.walls.pushBarrier` or a real threat — peacetime hold stays (08:4x).

Rough ETA from live climb: wall min 262k→300k ≈ **~12:00–14:00 Asia/Hong_Kong 2026-10-30** (rate-dependent). Recovery banking ≈ **30–90 min** after hold if storage lands under 13k; often shorter when fundSpend already kept stor near 13–15k.

### Post-hold energy priority (reallocation order)

Once fundSpend is off and storage has recovered past the floor:

1. **Defense floor** — keep storage ≥15k; towers/safe-mode cushion untouched.
2. **Home upgrade** — resume full upgrader set (RCL7→8 is long; don't idle for walls).
3. **Colony W47N8 RCL6→7** — still the critical path (~32 h); home surplus / remote O support colony, not a new wall STEP.
4. **Colony soft ramparts** — raise spawn/tower/storage soft ramps from ~20–50k toward a staging band (candidate for a later review; Overmind-style barrier staging) **before** day-of RCL7 tower3/spawn2.
5. **Mineral / boost pipeline** — extractor→container→miner body, then labs; keep `RCL7_INDUSTRY=false` / BOOST gate until walls held **and** storage healthy (see `MINERAL_DEFENSE_ROADMAP.md`).
6. **Optional 1M walls** — only via `pushBarrier` or threat; not automatic.

### Overmind / TooAngel notes

- **Overmind** `fortifyDutyThreshold` (~500k) / `barrierHits[7]=1M`: workers fortify when barriers are below threshold; above it they leave fortify duty. Same shape as our hold: past the peacetime target, energy returns to upgrade/economy. We hold earlier (300k) by Misaki choice; Overmind's higher bar is a reference, not a reason to auto-climb.
- **TooAngel**: dedicated repairers top walls continuously — we deliberately **don't** (fund + STEP + hold) so storage can recover. Continuous repairers would fight the post-300k reallocation.

### What we did not change

- No code behavior change beyond documenting the exit comment on `fundSpend`.
- No auto-push to 1M; no mineral enable; soft-rampart HP raise deferred to **14:4x** (see below).
- Observability: patrol / model already expose `wmin`, `fundSpend`, storage; watch for `stepHeld` equivalent = walls min ≥300k + no job.

## 2026-10-30 14:4x — colony soft-ramp staging (topic A)

**Question:** before W47N8 RCL7 day-of (tower3+spawn2), should we raise soft KEY ramparts (spawn/tower/storage) from ~20–50k toward an Overmind-style barrier band, and to what target without starving upgrade?

**Answer: YES — stage to 100k (not 500k).** Peacetime + storage≥5k; spawn/gate always; seal/GATE stay 300k.

### Why 100k not Overmind 500k
- Overmind `barrierHits[6]=500k` / `[7]=1M` with `fortifyDutyThreshold=500k` storage. Colony storage is ~0–3k; home ~15k under/around reserveE. A 500k soft target would burn tens of k e into ramps while ~560k e still sit on the RCL7 controller.
- Hits cost: energy = hits/100. Spawn 20k→100k ≈800e; tower+storage ~50k→100k ≈1k e; **~1.8k e total** — a few minutes of surplus, not a multi-hour diversion.
- Defense: 100k soft cover survives small Invader/probe pressure until towers engage; seal + GATE@29,3 already ≥300k handle the north line. BustJetter post-novice threat is seal/towers, not soft-ramp HP at 500k.
- TooAngel continuous repairers would fight upgrade — we keep soft raise **gated** and hold-map never ratchets (decay-offset only above the soft floor).

### Code (`src/rooms/w47n8/config.js`, `index.js` rampHold)
- `GATE_TOWER` 20k→**100000** (spawn-slot + gate critical floor, always).
- `SOFT_RAMP=100000`, `SOFT_MIN=5000` (→**0** at 17:4x).
- Soft path: peacetime (`!TH.on()` at 14:4x → `!TH.localOn()` at 17:4x) + storage≥SOFT_MIN → raise lowest non-gate KEY soft ramp below SOFT_RAMP.
- Observability: `Memory.ops.w8soft = { t, tgt, spawn, tower, stor, gate, storE, why }` (why/storE added 17:4x).
- Tests: `tests/w47n8_no_rampart.js` soft staging; `w47n8_spawn_move.js` adjusted for GATE_TOWER band.

### Reprioritise
Soft ramps move **ahead of** day-of RCL7 placement in the post-hold sequence (still after walls hold + storage recover). Day-of order unchanged: tower3@22,7 + spawn2@33,30 + 10 ext + spur; factory OFF (`RCL7_INDUSTRY=false`).

## 2026-10-30 17:4x — soft-ramp stuck ~49k (follow-up)

**Question:** why are W47N8 soft KEY ramparts (tower/storage) still ~49k three hours after 14:4x staged them to 100k, while spawn already hit GATE_TOWER? Will soft finish before RCL7 day-of (~25 h)?

**Answer: two gates blocked the soft path; fix both. Soft finishes in minutes after deploy — well before RCL7.**

### Root cause
1. **`SOFT_MIN=5000` never trips.** Upgrade-first economy keeps colony storage ~0–3k (live ~2.4k). Soft raise required `storE >= SOFT_MIN`, so tower/storage never climbed; spawn/gate still did via unconditional `GATE_TOWER`.
2. **`!TH.on()` treated neighbor staging as wartime.** `TH.on()` ORs `w8threat` with `w8threatN`. BustJetter armed groups in own W48N9 refresh `w8threatN` every north_watch scan → soft path stayed off even if storage briefly cleared 5k. Seal walls already ≥300k; towers still prioritize attack/heal over repair.

### Cost / ETA
Hits remaining ≈ (100k−49k)×2 KEY ≈ 102k hits ≈ **~1k e**. Towers repair only when E>600 and not fighting — ~minutes of divert, negligible vs ~503k e left on the RCL7 controller (~25 h at ~23 e/t).

### Code
- `config.SOFT_MIN` **5000→0**.
- `threat.localOn()` — in-room / W47N7 `w8threat` only (not `w8threatN`).
- `rampHold` soft peacetime = `!TH.localOn()`; observability `Memory.ops.w8soft.{storE,why}` (`ok`/`stor`/`threat`/`off`).
- Hold map still never ratchets up; GATE_TOWER path unchanged.

### What we did not change
- No flip of `RCL6_MINERALS` / `RCL7_INDUSTRY` / `STATIONARY_FILL`.
- Seal/GATE stay 300k; no Overmind 500k soft band; defend-only W47N9.

## 2026-10-30 20:4x — W47N8 RCL7 day-of: pre-bank vs reactive siteRem

**Question:** Should W47N8 pre-bank ~50k energy in storage before RCL7 so day-of spawn2+tower3+10ext finish without starving upgraders, or keep upgrade-first and let `siteRem` spawn builders reactively?

**Answer: NO pre-bank. Stay upgrade-first; reactive `siteRem≥3k → ≤4 builders` + 2 upgraders already covers day-of.**

### Evidence
1. **Bill is ~50k, not ~153k.** Spur roads already live (patrol roads 139). Day-of = spawn2@33,30 (15k) + tower3@22,7 (5k) + 10×ext (30k). Factory still gated (`RCL7_INDUSTRY=false`).
2. **Existing spawn path is reactive.** `spawnRun`: when sites exist, upgraders stay at **2** (not zeroed); builders scale `siteRem≥3000→4 / ≥1200→2 / else 1`. First-tick sites (spawn+tower) ≈20k → 4 builders immediately; after those stand, 10 ext sites keep the same cohort.
3. **Throughput math.** Colony harvest ~30 e/t gross; 4×~6W builders ≈20–23 e/t build while 2 upgraders keep ~10–12 e/t on the controller. Full 50k ≈ **2–3 h** wall; first batch spawn+tower alone ≈ **15–20 min**. Pre-banking 50k at ~3 e/t surplus would delay RCL7 itself by **~1–2 h** — worse than the build dip.
4. **Overmind / TooAngel.** Overmind fortifyDutyThreshold gates *walls* on storage, not RCL structure batches. TooAngel `checkForBuilder` spawns builders when construction sites exist — reactive, no RCL day-of bank. Same pattern we already run.
5. **Live (t~83962645):** soft-ramp COMPLETE (`w8soft.why=ok` ≥100k); home walls HOLD 300001 fundSpend EXIT; W47N8 need ~438k ≈ **~21 h** @~23 e/t; colony stor ~0–3k (upgrade-first, expected). Spurs DONE.

### Observability
`Memory.ops.w8day` (layoutRun every 20 t): `{rcl,need,siteRem,builders,upgraders,storE,bill,missSpawn,missTower,missExt,why}` with `why∈{upgrade,near,dayof,done}`. Patrol/strategy can watch bill↓ without guessing.

### What we did not change
- No pre-bank threshold; no flip of `RCL6_MINERALS` / `RCL7_INDUSTRY` / `HUB_LINK` / `STATIONARY_FILL`.
- Day-of order unchanged: spawn2 + tower3 first, then 10 ext; minerals after stor≥20k (`MINERAL_DEFENSE_ROADMAP` §B).
- Defend-only W47N9; no claim/attack/credits/SM.


## 2026-10-31 05:4x — W47N8 day-of energy crash (stor~1–3k)

**Question:** Will reactive day-of with stor~1–3k empty towers or crash spawn energy?

**Answer: NO.** Confirm 20:4x no-pre-bank. Spawn/eAvail protected by filler+hauler priority; residual risk is **north tower** while `hubNeedy` blocks filler — haulers still cover `free>200`. Detail: `docs/PLAN_W47N8.md` "Day-of energy crash risk".

### Also closed (02:4x next-open)
Home upgrade sustained ≥20 after remotes SAFE? **YES** on short/SAFE windows (24h hourly: SAFE hours 20–22 e/t ≈ live_comp; core hours 15–17). Binding constraint = W45N7 Invader core frequency, not transport. No code lever beyond finishing cores (already engaging).

### Shipped
- `w8day.{towerMinE,eAvail,eCap}` + `tests/w47n8_dayobs.js`. Deploy this run.
- No gate flips; no fill-priority change; no pre-bank.

## 2026-10-31 08:4x — post-RCL7 first-hours: leanBank → stor≥20k

**Question:** After W47N8 day-of (spawn2+tower3+10ext ≈50k) finishes, how do we get colony storage from ~2–3k → **20k** for lean KO without flipping gates — and do we need to throttle **home** upgrade for the colony day-of bill?

**Answer: Auto leanBank on colony after day-of (default ON, opt-out `Memory.ops.w8leanBank=false`). Do NOT throttle home. Do NOT flip `RCL6_MINERALS`.**

### Live proof (24h postgres + Memory.ops, Asia/Hong_Kong 08:4x)
- Colony stor stuck **0.5–3k** under full upgrade for ~24h (surplus upgrader rule scales WORK with stor → net≈0).
- Natural stor→20k under 3 upgraders ≈ **never**; with 1×10W upgrader, net ~15–25 e/t → **~0.8–1.3 h** from 2.5k.
- Home and colony economies are **independent** (no terminal energy send yet); home throttle would not fund colony day-of. Home CPU fine; keep home upgrade.

### Sequence (refined checklist; gates stay false)
1. **RCL7 tick** → reactive day-of (20:4x / 05:4x): spawn2@33,30 + tower3@22,7 first, then 10 ext. Watch `w8day.towerMinE`. ~2–3 h.
2. **`w8day.why=done`** + storE < 20k → **`leanBank` ON**: `energyBank` throttles upgrader spawn (keep ≤1 if ticksToDowngrade≥20k else 1 for downgrade), recycles surplus via `Memory.ops.w8recycle`, parks idle builders, pauses non-urgent road repair (same as move-banking).
3. **`w8day.phase=bank20`** until storE≥20000 → **`phase=ready`**, leanBank off, full upgrade resumes. Cushion sits ready for lean KO.
4. Flip **`RCL6_MINERALS`** only after checklist in `MINERAL_DEFENSE_ROADMAP` §5.6 (still needs **w8mminer/send** — not this run).

### Observability
`Memory.ops.w8day` adds: `phase` (`upgrade|near|dayof|bank20|ready`), `bankLeft`, `bankEta` (ticks @~20 e/t while leanBank, else −1), `leanBank` 0/1.

### Overmind / TooAngel
Overmind `storageBuffer` ~100k before industry; TooAngel banks via fewer upgraders when building. We use a tighter **20k** colony cushion and an explicit post-dayof throttle (not a pre-RCL bank — that remains rejected by 20:4x).

### Shipped
- `leanBank` / `energyBank` / `leanBankRecycle` / `dayofMiss` in `src/rooms/w47n8/index.js`; roles use `energyBank` for repair pause + park.
- tests: `w47n8_dayobs` phase/bank/recycle/opt-out; `w47n8_move_bank` spawn throttle + park.
- **No gate flips. No home throttle. Opt-out: `Memory.ops.w8leanBank=false`.**


## 2026-10-31 11:4x — lean KO code: w8mminer + haul (send still open)
Closes the 08:4x "still needs w8mminer/send" half: colony now has dormant miner + haul-to-terminal. Flip still waits RCL7 + leanBank ready + **`terminal.send`** (next slice) + Misaki propose. Detail: `docs/MINERAL_DEFENSE_ROADMAP.md` §5.9. ETA RCL7 slipped to **~18:00–18:15 Asia/Hong_Kong**.

## 2026-10-31 14:4x — lean KO send shipped (dormant)
Closes 11:4x remaining code gap: `mineralSend` + `termFuel` behind `RCL6_MINERALS=false`. Flip still waits RCL7 + day-of + leanBank ready + Misaki propose. Detail: `docs/MINERAL_DEFENSE_ROADMAP.md` §5.10. Live ETA RCL7 **~17:20–18:00 Asia/Hong_Kong** (need~57k).


## 2026-10-31 17:4x — day-of north tower ≥600 (topic B residual)

**Question:** Live day-of after RCL7@83981380 — does north tower stay ≥600 under builder drain, or need filler ignore `hubNeedy` @towerE<500?

**Answer: Do not change hubNeedy.** North towers (24,8 + new 22,7) are served by `northFeed@600`, not the hub filler. Live ~33 min in: towerMinE 860, eA full, stor 0. Detail: `docs/PLAN_W47N8.md` 17:4x.

### Shipped
- `w8day.{towerHubE,towerNorthE,nf}` + `tests/w47n8_dayobs.js`. Deploy this run. **Gates stay false.**

### Sequence after this
1. Finish day-of (~2–3 h) watching `towerNorthE`/`nf`.
2. leanBank → stor≥20k (~1 h).
3. **Propose** flip `RCL6_MINERALS` only (code ready). No wait for ext wave beyond day-of done.

## 2026-10-31 20:4x — leanBank arms on day-crit (not 50ext)

**Question:** Why is `leanBank` still 0 after spawn2+tower3 DONE while ext~40/50? Does post-RCL banking wait for the full extension flood?

**Answer: Bug/mismatch — arm leanBank as soon as day-crit (spawn2+tower3) is live. Do NOT wait for 50ext. Gates stay false.**

### Live proof (Asia/Hong_Kong ~20:47, t~83984600)
- `w8day`: missSpawn=0 missTower=0 **missExt=10** why=**dayof** phase=dayof leanBank=**0** storE=0 bankEta=-1 siteRem~15.8k; builders4 upgraders3; towerMinE~600 (north=600 hub=920 nf=0).
- Home: stor~14k UNDER floor15k; remotes W45N8/W45N7 SAFE post core clear; deploy was 1cba10f.

### Research
- Overmind `UpgradeSite.storageBuffer` ≈100k before scaling upgraders — surplus-driven upgrade, not "finish every extension then bank."
- TooAngel cuts upgrader pressure while construction sinks energy — same shape as mid-ext leanBank.
- Our own `dayCrit` already prioritises spawn+tower over ext flood (19:1x); leanBank requiring `missExt===0` undid that.

### Fix
1. `leanBank(room)`: require only `!missSpawn && !missTower` (+ RCL7 + stor<20k + !gate + opt-out).
2. `w8day.why`: `dayof` only while day-crit missing; else `done` → `phase` bank20/ready from storE.
3. `bankEta`: `ceil((bankLeft + siteRem) / 20)` while leanBank (sites still sink first).
4. Builders keep working sites; surplus upgraders recycle; idle builders park once sites clear.

### Shipped
- `src/rooms/w47n8/index.js` leanBank + dayObs; tests mid-ext; docs §5.8/§5.12. **No gate flips. No home throttle.**

## 2026-10-31 23:4x — flipReady + post-flip leanBank hold

**Question:** When bank20 completes, is the lean KO flip checklist clear? Does flipping `RCL6_MINERALS` disarm leanBank too early?

**Answer:** Ship `w8min.flipReady` (propose-only). Keep leanBank through `phase=minBuild` until terminal+minCont exist after a future flip. **Do not flip in this run.** See `docs/MINERAL_DEFENSE_ROADMAP.md` §5.13.
