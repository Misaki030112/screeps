# W47N8 energy-flow model (`tools/model_w8.py`)
Rerun every W47N8 patrol iteration: `.venv/bin/python tools/model_w8.py [--hours 6]` → stage table on stdout, `metrics/model_w47n8.json`,
`model_params` rows `w8.*` (ideal vs actual, Grafana), and `Memory.ops.w8model = {rcarry, lcarry, upw}` (read back), which the spawn rules use.

Model: real terrain + live objects for W47N8 + W47N7 (one grid, seam W47N8 y=49 ↔ W47N7 y=0), Dijkstra road 1 / plain 2 / swamp 10,
ticks/tile from the live hauler bodies. Per source 10/t (owned/reserved) − container decay (0.1 owned / 0.5 remote) − miner upkeep −
hauler upkeep (CARRY need = 10 × (round trip × 1.10 + 4) / 50, load split 75% ctl cont 13,26 / 25% hub 33,33). Shared: roads, ramparts
0.03/t each, builder-lite 1000/1500. Upgrade = net / (1 + upgrader upkeep 1150/1500/10). RCL5: 1800 cap, best of source-A link→ctl or hub→ctl link (3% loss).
reserve7 (2 CLAIM) is spawned and paid by home.

## 2026-11-15 20:2x — keep=2, 39332 closest yet to 40k latch; softCap off, tip in 22–25k hysteresis (plan holds)

12h window: W47 upgrade **18.97** e/t vs ideal ~30 (`tools/model_w8.py --hours 12` 18.97; 32.73%→34.51%, +194k). Forward RCL8 ≈ **18.45 d** (was 19.20 / 19.7 d). Stor avg 28.73k max **39332** min **22082**; **0% under 15k, 100% ≥20k, 86.8% ≥25k, 32.0% ≥30k, 0% ≥40k**. Two samples just under the 22k ARM (22082 @09:36, W47N7 core) then ≥22k the rest of the window. Live stor **~24.5–25.0k**, keep=2 phase=ready leanBank=0 softE=0 softCap2 **OFF** threatSoft **OFF** (18:28 leftover expired ~20:16; parked north-exit guards gone), softBand=1 softLeft=496, sealPark=1, upLatched=0. This is the designed [22k, 25k) hysteresis — not a phase exit. **39332 @18:20** is the **closest yet** to the 40k/500 t latch (morning official end 34965 / live 35385; earlier today 38466 @08:37) — longest ≥30k only **231 t**, not a latch. **contMinPct54 roadCrit0**. Do not unpark ceil/seal mid-band. keep=2 designed 20 e/t = 66.5% of the 30.08 ceiling, so short-soft upgrade ALERTs at that rate are expected. See `docs/RCL7.md` 20:2x.

## 2026-11-15 08:2x — keep=2, 35k closest yet to 40k latch; softCap on from threatSoft leftover (plan holds)

12h window: W47 upgrade **19.20** e/t vs ideal ~30 (`tools/model_w8.py --hours 12` 19.24; 31.00%→32.73%, +189k). Forward RCL8 ≈ **19.7 d** (was 19.36 / 20.0 d). Stor avg 26.2k max **35385** min **21653**; **0% under 15k, 100% ≥20k, 70.2% ≥25k, 0% ≥40k**. One sample below the 22k ARM (21653 @21:24, W47N7 core) then ≥22k the rest of the window. Live stor **~35.0–35.4k**, keep=2 phase=ready leanBank=0 softE=0 softLeft=0, softCap2 **ON** from threatSoft leftover after the 07:27 W47N7 core clear (parked w8guard/w8defender north-exit, ttl ~250) — known class, not a bank failure. Open ≥30k climb from 07:42 (~610 t at 08:25) is the **closest yet** to the 40k/500 t latch (prior 32.3k / last window 32.0k) — not a latch. Longest ≥25k stretch **1650 t** (02:07–04:10). **contMinPct50 roadCrit0**. Do not unpark ceil/seal mid leftover. keep=2 designed 20 e/t = 66.5% of the 30.08 ceiling, so short-soft upgrade ALERTs at that rate are expected. See `docs/RCL7.md` 08:2x.

## 2026-11-14 20:2x — keep=2, softCap sticky-cleared above 22k ARM, 40k latch waiting (plan holds)

12h window: W47 upgrade **19.36** e/t vs ideal ~30 (`tools/model.py` / ledger up 19.32; 29.28%→31.00%, +188k). Forward RCL8 ≈ **20.0 d** (was post-resume 16.09 / ~24.6 d). Stor avg 26.3k max **32038** min **22916**; **0% under 15k, 100% ≥20k, 83.1% ≥25k, 0% ≥40k**. Never crossed the 22k ARM, so softCap2 **sticky-cleared** (live softCap2=0 softE=0 threatSoft=0 leanBank=0 phase=ready upgKeep=2 upgCeil=2 sealPark=1). Longest single ≥25k stretch **330 t** — still a 23–32k camp, not a continuous 25k hold, and **not** a 40k latch (closest 32.0k). keep=2 is correct. **contMinPct53 roadCrit0**. Do not unpark ceil/seal mid-band. See `docs/RCL7.md` 20:2x.

## 2026-11-14 08:2x — sites done, keep=2, upgrade resumed; softCap thrashing 25k (plan holds)

12h window: W47 upgrade **5.25** e/t blended vs ideal **30.03** (`tools/model_w8.py --hours 12`; 28.81%→29.28%). Progress left 3150854 at **04:22:50**; sites first 0 at **04:25:03**; post-resume 3190 t **16.09 e/t** (model 3h 17.09 / 2h 16.68), forward RCL8 ≈ **24.6 d**. Stor avg 10.8k max **25486** min 0 (mid-window crash to 0 at 23:33–00:07 while sites were still up, then recovered); **69.1% under 15k, 20.8% ≥20k, 3.4% ≥25k, 0% ≥40k**. Longest ≥25k only **31 t** — softCap2 still ON, designed [22k, 25k) hysteresis, not a sticky clear. `f7328c4` keep returned to 2 once sites cleared (W47 siteRem **123709→0**; labsN **6**, factory done; a brief 1-site road blip 07:37–08:02 is already gone). Live stor 24733–25183, builders=1, upgraders=2×10W, leanBank=0, threatSoft leftover, phase=ready upgKeep=2 upgCeil=2. **contMinPct50 roadCrit 0–1**. After a sticky ≥25k clear, the 40k latch is the next keep step. Do not unpark ceil/seal mid-thrash. See `docs/RCL7.md` 08:2x.

## 2026-11-13 20:1x — keep=1 held; upgrade 0 all 12h while remaining lab sites build; rem 259k→124k (plan holds)

12h window: W47 upgrade **0.00** e/t vs ideal **30.03** (`tools/model_w8.py --hours 12`; 28.81% unchanged, progress still 3150854 since 17:24). **100% of samples under 15k**, max stor **8800**, **0% ≥20/25/40k**. `f7328c4` keep=1 while sites are open is held (W47 siteRem **259481→123709**; lab 29,38 completed this evening, live labs 3, factory done; remaining 28,37 at 28529, 27,40 at 3542, 28,38 still 0, plus minCont 37,44 0/5000). Live stor 5920, builders=4, upgraders=0, threatSoft off, phase=minBuild leanBank1 bankWhy=minBuild upgKeep=1 upgCeil=1. **contMinPct50 contLow0 roadCrit39** is repair debt under the thin bank and the mid-day #45 re-site wave (sites spiked to 41 @12:38 then drained), not a reason to unpark ceil/seal or revert keep=1. At the measured 17.29 e/t build, ~124k remaining is about **8–9 h**. After sites clear, keep returns to the 40k latch. See `docs/RCL7.md` 20:1x.

## 2026-11-13 08:2x — keep=1 held; upgrade 0 all 12h while remaining lab/factory sites build (plan holds)

12h window: W47 upgrade **0.00** e/t vs ideal **29.93** (`tools/model_w8.py --hours 12`; 28.81% unchanged, progress still 3150854 since 17:24). **100% of samples under 15k**, max stor **5760**, **0% ≥20/25/40k**. `f7328c4` keep=1 while sites are open is held (sites 7→6 after lab 27,38 finished; live siteRem **259481**, factory 66840/100000, lab 27,39 at 21000, lab 28,37 at 2829). Live stor 3494, builders=4, upgraders=0, threatSoft leftover WINDOW 1500 (w8threat=84234904), phase=bank20 leanBank1 upgKeep=1 upgCeil=1. **contMinPct6 contLow3 roadCrit29** is repair debt under the thin bank, not a reason to unpark ceil/seal or revert keep=1. At ~8 e/t build, ~259k remaining is about 1.5 days if the rate holds. After sites clear, keep returns to the 40k latch. See `docs/RCL7.md` 08:2x.

## 2026-11-12 20:1x — keep=1 while authorized sites are up; storage 0 after builders + Invader wave (plan holds)

12h window: W47 upgrade **11.84** e/t vs ideal **30.08** (`tools/model_w8.py --hours 12`; 27.76→28.81%, +115k ≈11.84 e/t, was 18.04). Progress flat at 3150854 since 17:24. **46.3% of samples under 15k**, **43.7% ≥20k**, **6.8% ≥25k** (longest 111 t, max **26276** — morning leftover, not a new sticky clear), **0% ≥40k**. Mid-day `f7328c4` drops keep to 1 while construction sites are open (11 sites, live siteRem **336100**); four builders then a 4-Invader W47N7 wave drained stor to **0** since 18:01 (under-15k streak from 16:16 still open). Live: stor 0, builders=0, emergency 1–2W miners, tiny hauler just spawned, threatSoft leftover WINDOW 1500, phase=bank20 leanBank1 upgKeep=1 upgCeil=1. **contMinPct44 contLow5 roadCrit1** is repair debt under the empty bank, not a reason to unpark ceil/seal or revert keep=1. After sites clear, keep returns to the 40k latch. See `docs/RCL7.md` 20:1x.

## 2026-11-12 08:1x — keep=2 held; softCap2 cleared into 22–25k hysteresis (plan holds)

12h window: W47 upgrade **18.04** e/t vs ideal **30.08** (`tools/model_w8.py --hours 12`; keep=2 / 20 WORK; 26.14→27.76%, +175k ≈18.04 e/t, was 16.99). **16.6% of samples ≥25k** (was 46.2% — last window's 32k peak is gone), **72.5% ≥20k**, max stor **26607** @08:04 (longest ≥25k **530 t**, 07:30–08:09); **0% ≥40k** — 40k/500t latch still waiting. That 530 t stretch **cleared softCap2**; live stor 23238 is the designed post-clear [22k, 25k) hysteresis (softLeft 1762, above ARM, softCap2=0 softE=0 softBand=1 phase=ready leanBank=0 upgKeep=2). sealPark still on (seal strict ≥25k). Two Invader bills (W47N7 + W45N7) were leave-alive and did not crash the bank. src_A "0.62 e/t" remains the known link-path accounting artefact. Not a reason to move the 40k latch or unpark ceil/seal mid-band. **contMinPct50 contLow0 roadCrit0**. See `docs/RCL7.md` 08:1x.

## 2026-11-11 20:2x — keep=2 delivered a 25–32k band, then leanBank rebuild (plan holds)

12h window: W47 upgrade **16.99** e/t vs ideal **30.08** (`tools/model_w8.py --hours 12`; keep=2; 24.62→26.14%, +166k ≈16.99 e/t, was 16.65). **46.2% of samples ≥25k** (was 18.4%), max stor **32259** @14:58–15:01 (longest ≥25k **980 t**); **0% ≥40k** — 40k/500t latch still waiting. Evening W45N7 + W47N7 Invader bills (two ×5200e defenders) plus mutual w8guard/w8defender bled storage to min **9478**; live 13.9k phase=bank20 leanBank1 upgKeep=1 (stor <15k) threatSoft leftover WINDOW 1500 from the W47N7 seen-tick — not a new bottleneck class and not a reason to move the 40k latch. **contMinPct56 contLow0 roadCrit0**. See `docs/RCL7.md` 20:2x.

## 2026-11-09 08:1x — leanBank rebuild after 21.3k peak (plan holds)

12h window: W47 upgrade **11.94** e/t vs ideal **30.08** (`tools/model_w8.py --hours 12`; WORK20 park; 19.34→20.40%, +116k ≈11.94 e/t). No 25k near-clear this window (peak stor **21275@23:00**); touched leanBank target **20057@00:00** then bled to min **10682** (04:00 hour); live stor 17329 softLeft 7671 / bankLeft 2671 phase=bank20 climbing again (upgKeep 2 after a brief keep=1 dip <15k). **contMinPct49 contLow1**; roadCrit 38→3 is the known mvp pause draining (not a new repair-debt class). Soft clear ≥25k remains the gate to ceil6. See `docs/RCL7.md` 08:1x.

## 2026-11-08 20:1x — leanBank rebuild after noon 22.3k peak (plan holds)

12h window: W47 upgrade **10.13** e/t vs ideal **30.08** (`tools/model_w8.py --hours 12`; WORK20 park; 18.42→19.34%, +101.5k ≈10.2 e/t). No 25k near-clear this window (peak stor **22280@12:51** tick 84141310); then bled to min **10524** (17:00 hour); live stor~15.2k softLeft~9.8k / bankLeft~4.8k phase=bank20 climbing again. **contMinPct48 contLow1**; roadCrit38 is the known mvp pause under softCap (not a new repair-debt class). Soft clear ≥25k remains the gate to ceil6. See `docs/RCL7.md` 20:1x.

## 2026-11-08 08:1x — leanBank rebuild after two near-clears (plan holds)

12h window: W47 upgrade ~12.1 e/t vs ideal ~30 (softCap+leanBank intentional; 17.31→18.42%). Near-cleared twice (stor max 25172@19:00 and **25391@21:00**) then bled; morning dip min~13.3k; live stor~18.3k softLeft~6.7k / bankLeft~1.7k phase=bank20 climbing again. **contMinPct50 contLow0** held; roadCrit24 is the known mvp pause under softCap (not a new repair-debt class). Soft clear ≥25k remains the gate to ceil6. See `docs/RCL7.md` 08:1x.

## 2026-11-07 20:2x — leanBank rebuild after near-clear thrash (plan holds)

12h window: W47 upgrade ~15 e/t vs ideal ~30 (softCap+leanBank intentional; model_w8 ~15.0/30 under WORK20 park). Hit near-clear ~19:28 (softLeft~78 / stor~25.2k) then bled to ~18–19k leanBank re-arm — softLeft~6.0k / bankLeft~1.0k phase=bank20 climbing. **contMinPct50 contLow0 roadCrit0** (repair DONE under softCap). Soft clear ≥25k remains the gate to ceil6. See `docs/RCL7.md` 20:2x.

## 2026-11-07 08:1x — leanBank climb vs softCap park (plan holds)

12h window: W47 upgrade ~12 e/t vs ideal ~30 (softCap+leanBank intentional; model_w8 ~10.2/30 under WORK20 park). softLeft 9→12→**8.4k** (overnight dip then rebuild); bankLeft~3.4k phase=bank20. Cont mid-band ~46–52 with **builders=2**; roadCrit≈1. Do not treat leanBank rebuild as a new bottleneck class — it is the softCap-bank path after a thrash dip. Soft clear ≥25k remains the gate to ceil6. See `docs/RCL7.md` 08:1x.

## 2026-11-06 20:1x — leanBank rebuild vs softCap park (plan holds)

12h window: W47 upgrade ~12 e/t vs ideal ~30 (softCap+leanBank intentional; model_w8 2h actual~6.7 under WORK20 park). Cont held ~48; **roadCrit 32→0**. Afternoon stor dip ~6.7k re-armed leanBank (phase=bank20); softLeft~9k climbing toward clear≥25k. Do not treat leanBank rebuild as a new bottleneck class — it is the softCap-bank path after a threat/thrash dip. See `docs/RCL7.md` 20:1x.

## 2026-11-06 08:1x — softCap park vs roadCrit (plan holds)

12h window: W47 upgrade ~8.9 e/t vs ideal ~30 (softCap intentional). Cont reclaim 12→~50 worked under 20:2x 2nd maint. Residual roadCrit~32 while softCap ON is expected: `energyBank`/`mvp` skips roadNeed(0.25/0.6) so soft-band can refill storage — roadCrit reclaim resumes after soft clear (≥25k). Model ideal still assumes healthy roads; do not treat mid-bank roadCrit as a spawn-gate bug. See `docs/RCL7.md` 08:1x.

## 2026-11-05 20:2x — post-war repairTicks vs 1 maint builder

Live softCap bank (~20k) with **contMinPct~12 / contLow4 / roadCrit~62**: container decay was beating one 6W builder. Overmind `repairTicks` would wishlist 2–5 workers; we raise maint max to 2 when `contDebtN≥3` (still under softCap — not a fortifyDuty burst). Expect contMinPct↑ then roadCrit↓ before soft clear unlocks deep seal.

## 2026-11-04 17:4x — soft-band surplus vs softCap hysteresis

Live thrash: clear@25.1k (15:57) → re-arm@22.7k (16:26) with nUp=4 while softBand ON. Model ideal ~30 assumes sustained WORK near ceil once soft clear holds; surplus WORK40 in the soft-band burns the cushion that soft-band haul is trying to refill. Soft-band surplus trim keeps WORK≤30 (base 3) until stor≥25k STRICT — matches Overmind scaling only above storageBuffer. See `docs/RCL7.md` 17:4x.

## 2026-11-04 14:4x — maint spawn vs softCap eAvail (post-abort)

Live anomaly after W47N9 abort: `contMinPct` 46→38 while softCap rebuilt stor and eAvail sat shy of `eCap`. Model income assumes containers healthy (miner stands / haul sinks). Maint now arms on container debt without full-cap gate (see `docs/RCL7.md` 14:4x). SoftCap/leanBank/hub numbers unchanged. Watch `w8day.contMinPct` / `contLow` climb under softCap bank.

## 2026-11-04 11:4x — soft-band sticky vs post-clear storage Δ

Live model window (~1560t @11:28): upgrade **15.36** vs ideal **30.08** (~51%); delivered hub 28.3 / ctl 1.4 (link-era attribution); waiting_feed ~0.39 averaged across softCap ON periods; stor~23–25k thrash. 3h room_stats: soft clears rare (2×) then storage Δ deeply negative for minutes while ctl still fat — haul sink sticky, not WORK/link capacity.

**Model implication:** soft-band park must retarget mid-load when `se` crosses under LEAN_SOFT; otherwise actual storage Δ after a clear stays negative even with holdBand true and HMAX/hubPrime healthy. See `docs/RCL7.md` 11:4x.

## 2026-11-04 05:4x — leanBank rebuild-band vs model upgrade

Live (c5334c8, ~05:45 Asia/Hong_Kong): W47 storage ~16–18k leanBank sticky + softCap ON; **nUp=1** → last3h ~8.7 e/t vs prior3h ~13.7 and model softCap-band target ~12–16 (2×10W under softCap≤2). Cause was leanBank hard keep=1 dual-stacked under softCap≤2 after Invader dip below LEAN_ARM — not a haul/link bottleneck (hubReady1 hubPrime1 feedOk; waiting_feed low).

**Model implication:** treat leanBank `[LEAN_ARM, LEAN_STOR)` as softCap-parity WORK (≤2), not a second upgrade freeze. Emergency `<LEAN_ARM` still 0/1. Soft clear ≥25k remains the gate to ceil6 / short≥70%. See `docs/RCL7.md` 05:4x.

## 2026-10-19 14:55 (6 h window, threat mode on for part of it; tick 4.20 s)
| stage | ideal | actual |
|---|---|---|
| mining A / B (local) | 10 / 10 | 10.0 / 9.6 (miners 93% working) |
| mining R1 / R2 (W47N7) | 10 / 10 | rminers 93% working; conts 1080 / 920 |
| round trip A / B / R1 / R2 | 48 / 38 / 99 / 132 t | — |
| local haul CARRY | 20.5 | 30 (3×10C10M; 80% moving, 11% blocked) |
| remote haul CARRY | 52 | 88 → 74 (14C7M/16C8M; 82% moving, 12% blocked) |
| net to sinks | 32.2 | upkeep live 12.7 (excl. reserve7) vs ideal ~6.8 |
| upgrade | 29.9 e/t (30 WORK) | 9.9 e/t (10–20 WORK, 41% queue_blocked) |
| build/repair | 0 (steady) | 13.4 e/t (seal walls + core ramparts to 50k, sites) |
| storage Δ | buffer | 0 (storage 316) |
| RCL5 ETA | 13.9 h | 42 h at 6 h rate |
| RCL5 ideal (links) | 30.3 e/t (link A→ctl) | — |

Balance: ~39 e/t mined ≈ 9.9 upgrade + 13.4 build + 12.7 upkeep + ~1.5 decay/carry-over. Upgraders are starved by allocation, not transport:
a third of income goes to walls/sites (threat-mode directive, temporary), and the fleet costs ~6 e/t more upkeep than ideal, mostly
oversized remote haulers (sized by loose-pile thresholds).

Fixes (0c590f1): remote haul fleet sized from model CARRY need (floor 60% ahead of builders, 110% + backlog term in step 7, max 8)
instead of loose thresholds; upgrader WORK cap = model `upw` (~30) instead of fixed 24 (applies when not in threat wall mode).
Next: local hauler 2C1M body on the fully paved local routes (−25% hauler upkeep); storage buffer once walls are done; RCL5 link A→ctl.

## 2026-10-19 15:10 bottleneck pass (allocation, not just upgrade)
6 h allocation (model `alloc` line, e/t): harvest 37.4 (miners 94%, rminers 93% working) = upgrade 9.9 + build/repair 13.1 + storage 0
+ upkeep 11.3 (excl. home-paid reserve7) + decay/stock/tower 3.2. Containers held ~9.6k idle stock (all 1.2-1.8k / 2000, W47N7 31,34 at 1790).
Findings:
- Sinks, not supply, bind: 1 upgrader (threat rule, walls < 50k) + 4 builders 64% walking. Walls 401k/750k hits at 15:05 -> done ~15:35.
- Remote haulers lost most of each trip inside W47N8: 24-143 ticks/trip filling single 50-energy extensions across the hub and
  flipping ctl <-> hub (w8rhauler83738293). Fix (0772f8b): no extension detours; one adjacent top-up in passing, fill duty only when spawn energy < 300 or no w8hauler -> ctl/hub cont -> storage.
  Measured after: in-room time per trip ~40-45 t (was 24-143, median ~70).
- Local hauler 10C10M on fully paved routes -> 10C5M (same 500 carry, -0.5 e/t upkeep).
- Upgrader count base was "2 while any site" (3 road sites ~700 left) and storage stock was invisible to it: base now by build backlog
  (>= 3000 -> 2, else 3), storage above 2k counts as stock, WORK cap = upw + 5 per 5k stored (max 40 = 4 stands x 10W).
Projected after walls: upkeep ~9.5, build ~1-2, upgrade ~24 e/t (30 with stock) -> RCL5 ~17-18 h (≈ 10-20 09:00-10:00 UTC+8).
RCL5 link proposal (needs approval, adds 2 tiles to v3b): ctl link 13,25 (dead-end tile beside stands 12,25/12,26/14,26) + source-A
link 26,12 (beside stand 26,11) -> model 30.3 e/t; v3b hub link 33,34 at RCL6.

### 16:15 after (18f621f, 0772f8b, 9c3162c, ab1a912)
- Walls/core ramparts reached 50k ~15:47; wall-mode gate now enters below 45k (rampart decay no longer flips it back).
- Upgrade: 20 e/t (2 upgraders) -> 40 e/t from t83740650 (4x10W) while the ~8k container stock drains; sustained ~25-27 e/t once
  stock is gone (4th upgrader not replaced unless storage >= 5k). 200-tick avg 24.4 (still part 2-upgrader).
- Upkeep live 12.0 (transitional: 4 upgraders, 5 haulers -> max 4, 2 leftover 6W builders) -> ~10 steady.
- RCL5 at ~25.5 e/t: 332k left -> ~15 h (10-20 ~06:00-09:00 UTC+8), was 42 h.

### 18:05 loss pass (a2523dd, cefd388, 233b0b8)
| e/t | 17:10 (1 h) | 18:00 (290 t, threat + filler buffer) | steady target (no threat) |
|---|---|---|---|
| harvest (40 max) | ~37 (local miners 85%) | ~31 (1 rminer holding in base on flee) | ~39 (6W miners) |
| rhaulers | 4.2 (75 CARRY) | 4.2 | 3.1 (56 CARRY) |
| upgraders | 2.3 | 2.3 | 2.3 |
| local haulers | 1.0-2.5 | 2.0 | 1.5 (3x10C5M) |
| builders | 2.4 (3x6W) | 0 | 0-0.6 |
| miners + rminers | 1.7 | 1.7 | 1.8 |
| filler | - | 0.6 | 0.6 |
| local defenders | - | 2.5 (home-sent 2.9 paid by home) | 0 |
| decay (conts 1.4, roads 0.2, ramparts 0.3) | 1.8 | 1.9 | 1.9 |
| build (rhauler WORK roads) | ~4 (builders' non-upgrade share) | 0.5 | 0.5 |
| storage | 0 | +3.6 (filler reserve fill, one-off) | 0 |
| upgrade | 20.3 | 10.5 | ~27 |
W47N7 road: 25 tiles missing = 6.9k energy for ~0.3 e/t (6 CARRY fewer) -> ~27 h payback; left to in-passing rhauler WORK, not accelerated.
Reserver (home-paid 2.17 e/t) doubles both W47N7 sources (+10 e/t): keep.

## 2026-10-19 21:4x strategy review: why upgrade is ~2/3 of ideal and the ctl container keeps emptying
6 h window to t83745409 (RCL4 165.2k/405k), model ideal 29.8 e/t, actual 21.1 e/t. Gap 8.7 e/t, all accounted for:
| item | ideal | actual | gap e/t | note |
|---|---|---|---|---|
| harvest (4 sources) | 40 | 38.2 | 1.8 | local A/B full (A 0 left at ttr 48); **W47N7 5W rminers lose ~10%** (below) |
| upkeep (excl. home-paid reserve7) | 8.5 | 11.2 | 2.7 | wrhauler 4.17 vs 2.7 (60 vs 48 CARRY), whauler 1.5 vs 1.0, wfiller 0.6 unmodelled (known, roadmap watch) |
| build (W47N7 roads by rhauler WORK) | 0 | 2.5 | 2.5 | temporary: 3 sites left at 21:13 |
| decay/tower/stock (waste_other) | 1.7 | 3.0 | 1.3 | tower heal/rampHold repair, container stock swings |
| storage | 0 | +0.4 | 0.4 | |
**Ctl container 13,26:** 30 WORK upgraders can burn 30 e/t; ~21 e/t reaches it, so it drains to 0 and refills in cycles (upgraders
queue_blocked 29%). That is the symptom of the energy gap above, not a routing fault — no hauler-priority change (as at 19:5x).

**Root cause found (new): remote container repair blocks harvest.** Reserved (unowned) room containers decay 5000 hits / 100 t = 50 hits/t
(CONTAINER_DECAY / CONTAINER_DECAY_TIME; owned room 500 t). `repair` and `harvest` share one action pipeline (docs.screeps.com
simultaneous-actions: the right-most wins, harvest is blocked). The w8rminer body was 5W1C3M = exactly 10/t with no slack, repairing
whenever the container is < 50% (both W47N7 containers sat at exactly 125,000/250,000 at t83745439), i.e. 1 tick in 10 → ~9 e/t per
source, plus every replacement gap lost for good. Live: R2 30,35 had 900 energy left at ttr 32 (t83745419). Home solved the same issue on
10-15 (`rmBody` 6W, measured 8.7 → 10 e/t); W47N8's module never got the port. The replacement lead was a fixed TTL 100 vs ~70 t walk
(R2) + 30 t spawn + queue behind upgraders/filler on the single Spawn2.
**Fix (751c6e7 t83745490 + guard 3ce6174 t83745499):** w8rminer 6W1C3M (800; empty CARRY weighs nothing → 1 tile/t on road;
250 harvest + ~25 repair ticks per 300 → full 10/t, +25 t slack), replacement lead = learned walk (`Memory.ops.w8rlead[si]`, set on first
reaching the source, only 1–300 t) + 3×parts + 20, default walk 90 → 140 t for the 10-part body. Upkeep +0.13 e/t. Expected +1.5–2 e/t
to upgrading once both rminers are replaced (current ttl 735 / 1150 at t83745493 → ~22:35 and ~23:05 UTC+8). `tests/w47n8_rminer.js`.
Model: remote miner cost 800; the `alloc` harvest proxy is now 2 × WORK × working per source capped at 10 (it was 10 × working, which
read 6W miners waiting for regen as lost harvest: 35.2 → 38.2 for the same window).
**Verify (w8patrol):** after each replacement, W47N7 source energy at ttr < 30 should be ~0; `Memory.ops.w8rlead` ~45–75; no rminer gap.
Remaining levers in order: (1) roads finish → build 2.5 → ~0.5 by itself; (2) hauler sizing at natural replacement (~+1.3, roadmap);
(3) RCL5 links (non-divertible ctl feed). With (1)+fix: ~24–25 e/t → RCL5 ~10-20 09:30–10:30 UTC+8 (ideal 9.3 h).

## 2026-10-29 11:4x strategy review: RCL6→RCL7 upgrade ~24 vs ideal ~30

**Question:** why is W47N8 stuck at ~23–24 e/t while the link-aware model says ~30, and what safe lever closes the gap?

**Live (tick ~83935480, 6 h window ~1970 t, cov 0.55):** RCL6 2.605M/3.645M, storage ~2.5k, ctl cont 13,26 ~1.1k, towers 2, sites 0.
Links **live and transferring**: A 26,12 → ctl 13,25 (both hold energy; hauler pickup at A = 0, link-meter artifact).
| stage | ideal (linkA→ctl) | actual |
|---|---|---|
| harvest (4 sources) | 40 | 38.5 |
| upgrade | 30.2 | 23.8 |
| upkeep (excl. home-paid reserve7) | ~6.5 | 10.8 |
| build/repair | ~0.7 | 1.1 |
| waste_other (decay/tower/stock) | ~1.7 | 2.8 |
| local CARRY need / live | **9** (B only) | **30** (3×10C) |
| remote CARRY need / live | 48.6 | 60 |
| wupgrader waiting_feed | — | 0.15 |
| delivered haulers ctl / hub | 75/25 mix | 15.5 / 18.1 |

**Gap ~6.4 e/t, accounted for:**
1. **waste_other ~2.8–3.4** — tower rampHold / road repair + container stock swings under the north-seal defense posture. By design at RCL6 with wall 300k; not a routing bug. TooAngel feeds the controller from storage beside the upgrader; we already have the Screeps-docs pattern (source-A link → ctl link), so architecture is fine.
2. **Fleet upkeep +2–3 vs ideal** — local haul stuck at 3×10C (HMAX floor 3) even though link-era need is ~9 CARRY + ~10 refill ≈ 2 haulers; remote 60 vs 48.6. Mild.
3. **waiting_feed 15%** — ctl is fed (cont ~1k, link draining) but not saturated; remotes still dump hub-first (hub delivered 18 > ctl 15). Not starving; hub→ctl link (gated `HUB_LINK=false`) stays optional.

**Root cause found (observability / spawn feed):** `tools/model_w8.py` wrote `Memory.ops.w8model.lcarry` from the **no-link** flow F4 (~22, still prices A haul) even after A→ctl links existed. Spawn `HMAX = max(3, min(4, ceil((lcarry+10)/10)+1))` therefore never saw the link-era need. Fixed this review: when both links are live, Memory gets `lcarry≈9`, `upw≈31`, `links:true` from the link-aware flow; Grafana `w8.upgrade` ideal also switches. **HMAX floor dropped to 2 when `Memory.ops.w8model.links`** (patrol 2026-10-29 15:54, post-raid abort): saves ~0.5–1.5 e/t local hauler upkeep; pre-link rooms keep floor 3. Unit test covers both.

**Plan recalibration (no Misaki decision):**
- Steady RCL6 upgrade under current defense: **~23–24 e/t** (not 30). Trimmed (HMAX→2 + quieter waste): ~26. Ideal 30 only with zero tower/stock waste.
- Remaining 1.04M at 23.8 e/t × 4.36 s/t ≈ **53 h → ~2026-10-31 16:00 UTC+8**; at 26 ≈ 48 h; at 30 ≈ 42 h.
- RCL7 gate unchanged: layoutRun places tower#3 (22,7) + spawn#2 (33,30) automatically; no early place (ERR_RCL_NOT_ENOUGH confirmed).
- Do **not** enable `HUB_LINK` / minerals yet; waiting_feed is mild and storage is thin (~2k).

**Verify (next model_w8 / w8patrol):** `Memory.ops.w8model.links === true` and `lcarry` ~9; local CARRY should fall toward ~20 (2×10C) as the 3rd hauler ages out; upgrade target ~24–26 while waste_other ~3.

## 2026-11-02 02:4x strategy: soft-cap + link HMAX backlog

**Symptom:** Post-RCL7 W47 under `LEAN_SOFT` soft-cap ≤2: upgrade ~14 vs ideal ~30; `src_A` ~2 vs 9.6; source+ctl containers full; links transferring; `upgrader_work` stuck at soft-cap 20; storage ~18–21k ready band.

**Mechanism:** Link path A→ctl is non-divertible. When ctl cont is full, link receive stalls and source-A container backs up until the miner pauses. With `HMAX=2` the loose-pile surplus rule could not add a hauler to drain B (and overflow A when link blocked) into storage via rebuild-band sink.

**Model note:** `w8model.lcarry≈9` / `links:true` still correct for **steady** link-fed upgrade. The 3rd hauler is an **overflow valve**, not a return to pre-link floor-3 upkeep. Expected upkeep +~0.5 e/t only while piles >1200; idle after drain.

**Research:** Overmind `UpgradeSite.storageBuffer` gates upgrader **scale** on storage assets; transporters still use storage as a logistics buffer when the upgrade battery is saturated. Matching shape at our tighter 15/25k: keep soft-cap, allow one surplus hauler (`HMAX=3`).

**Fix:** link-era `HMAX` 2→3; floor stays 2. See `docs/RCL7.md` "02:4x".

## 2026-11-04 08:4x strategy: link HMAX 3→4 overflow under softCap bank

**Symptom:** Peacetime softCap+leanBank: upgrade capped ≤2 (intentional); `looseE` stuck ~3–5k; nHaul=3 @HMAX; source-B cont+drop ~3.5k; model `waste_other` ~8–9; bank climb slow (~5k bankLeft).

**Mechanism:** 02:4x set link-era `HMAX=3`. Surplus still coded `Math.min(HMAX, loose>2000?4:3)` — with HMAX fixed at 3 the 4th never spawned. B has no link; soft-band parks correctly to storage but 30 CARRY cannot clear south overflow + decay while A link saturates ctl.

**Model note:** `w8model.lcarry≈9` / `links:true` still correct for **steady** link-fed upgrade. The 4th hauler is a **chronic-overflow valve** (same shape as the 3rd), not a return to pre-link floor. Expected upkeep +~0.5–1 e/t only while loose>2000; HMAX falls back to 3 after drain.

**Research:** Overmind transporters sized from mining e/t×distance independent of `storageBuffer`; logistics keep `requestOutput` on full containers while UpgradeSite parks. TooAngel: excess → storage.

**Fix:** `HMAX = links ? (loose>2000 ? 4 : 3) : …`. Floor stays 2. See `docs/RCL7.md` "08:4x".


## 2026-11-02 08:4x strategy: soft-band park vs soft-cap exit

**Symptom:** Hours after HMAX 2→3: upgrade still ~16.5/30 (55%); `upgrader_work=20`; stor flat ~20.1k; ctl+hub full; looseE~4.8k; `src_A` still soft in 2h meter (~0.8 — link-path artifact + occasional stall).

**Mechanism:** Soft-cap exit needs stor≥`LEAN_SOFT` 25k. Sink park stopped at `LEAN_STOR` 20k. Dead zone [20k,25k): soft-cap on, HMAX overflow has nowhere sticky to grow the cushion, surplus shows as `waste_other`.

**Model (2h / 24h):**
| stage | ideal | 2h actual | 24h actual |
|---|---|---|---|
| upgrade | 30.08 | 16.55 | 11.83 |
| upgrader WORK | 31 | 20 | 20 |
| local CARRY | 9 | 30 (HMAX=3 overflow) | 30 |
| harvest alloc | ~40 | 36.7 | 34.8 |

**Research:** Overmind `UpgradeSite.storageBuffer=100k` + logistics `bufferChoices` — storage remains a buffer while the upgrade battery is full; WORK scales only with surplus **above** buffer. TooAngel / docs: excess belongs in storage, not stranded at sources/ctl.

**Fix:** park through LEAN_SOFT. Soft-cap unchanged. See `docs/RCL7.md` "08:4x".

## 2026-11-02 11:4x — threat soft vs soft-cap exit

**Symptom:** After stor passed 25k, 2h upgrade ~46.7% with nUp=4 / WORK40 and `waiting_feed`, while threat soft (`w8soft.why=threat`) hoarded tower energy.

**Mechanism:** `LEAN_SOFT` soft-cap does not read threat. `wallsLow` is only the 100k urgent floor, so a quiet-looking seal under local threat still takes the peacetime upgrader rule (base 3, surplus to WORK cap 40).

**Fix:** `softCap2` = `TH.localOn()` **or** stor<25k. `w8threatN` excluded (chronic camp). See `docs/RCL7.md` "11:4x".

## 2026-11-02 14:4x — peacetime overshoot after softCap lift

**Symptom (t~84018710, ~11:46 HKT):** softCap2=0, stor~27–28k, nUp=4 WORK40, waiting_feed~0.30, upgrade **16.3 / 30.08 ≈ 54%**, delivered ctl~7.8 hub~18, storage_delta~+1.5 e/t. src_A soft ~0.85 (link era). ETA RCL8 ~785 h at actual (ideal ~425 h).

**Mechanism:** Surplus counted storage headroom, not ctl battery fill. Overmind: `UpgradeSite` requests input equal to upgrade power and scales WORK only with storageBuffer. TooAngel: storage beside upgrader. Our ctl is link+cont fed; hub is the larger sink until feedOk.

**Fix:** `FEED_MIN` + `ctlBattery` gate on surplus / recycle-to-3. See `docs/RCL7.md` "14:4x". Do not flip `HUB_LINK` on this evidence alone.

## 2026-11-02 23:4x — hub→ctl expected lift

With softCap cleared and nUp=3, measured upgrade ~19–20 e/t vs ideal ~30 (~66%); waiting_feed ~0.26; hub delivery ~26 e/t vs A→ctl ~8–10.
Enabling hub link (33,34) + filler ferry should add ~15–20 e/t effective to ctl after 3% loss when hub is topped from storage surplus — target waiting_feed <0.10 and short ≥70% at nUp3 before considering surplus nUp>3.
Plumbing shipped dormant (`HUB_LINK` still false). See `docs/RCL7.md` 23:4x.

## 2026-11-03 17:3x — feed ceiling without HUB_LINK (post roadCrit=0)

6 h window to t~84044700 (RCL7 ~917k/10.9M, stor 26k, softCap OFF, roadCrit 0, nUp3 WORK30):
| stage | ideal | actual |
|---|---|---|
| upgrade | 30.08 | **20.74** (~69%) |
| delivered ctl / hub | — | **10.48 / 20.44** |
| waiting_feed | — | 0.16 |
| build_repair (seal) | ~0–1 | 1.76 |
| upkeep | ~6.5 | 11.8 |

**Conclusion:** softCap/roadCrit/cont levers are exhausted. The ~9 e/t gap is A→ctl topology (hub skew). `w8day.feedBound=1` marks the pre-structure ceiling. **2026-11-03: Misaki nodded `HUB_LINK=true`.** Site 33,34 (~5k); `upgCeil` still waits `hubLinkLive` (hub→ctl ~range 20 → ~38.8 e/t net once the link stands). See `docs/RCL7.md`.

## 2026-11-04 02:4x — hub PRE-WARM arm LEAN_ARM (thrash band)

**Live gap:** softCap thrash parks stor in **19–22k** for hours → old prime arm `LEAN_SOFT_ARM(22k)` left `hubPrime=0` / hubLinkE=0 while filler idled at POST full. SoftCap hysteresis stays 22k; ferry prime arm drops to **LEAN_ARM(15k)** (home queen.standby / leanBank emergency floor). Bat-driven ferry still only after soft clear (≥25k).

**Model note:** Overmind `linksRequestBelow=200` is storageBuffer-agnostic. Prime-only (~200e one-shot) does not fight soft-band refill; bat ferry would. Expect: stor≥15k → hubPrime=1 once primed; thrash no longer cold-hub. See `docs/RCL7.md` 02:4x.

## 2026-11-03 23:4x — hub PRE-WARM during softCap bank

**Symptom:** `hubReady1` LIVE but softCap intentional bank left `hubLinkE=0` (ferry gated stor≥25k). Clear → `upgCeil6` before ferry + link cooldown(20) warmed hub→ctl → post-clear `waiting_feed` risk.

**Model note:** Overmind UpgradeSite tops upgrade links at `linksRequestBelow=200` independent of storageBuffer climb; our LEAN_SOFT bank needs the same pre-warm. Soft-band prime from `LEAN_SOFT_ARM(22k)` keeps one SEND (200) buffered; bat-driven ferry only after soft clear so soft-band refill is not fought.

**Expect (superseded 02:4x):** during bank once stor≥22k → `hubPrime=1`; on clear first hub→ctl SEND already ready; waiting_feed should not spike from cold hub. **02:4x:** arm is now LEAN_ARM(15k) so thrash [15–22k) also primes. See `docs/RCL7.md` 02:4x / 23:4x.
