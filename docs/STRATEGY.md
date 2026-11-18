# Strategy — W46N8 (home) + W45N8 (remote), 20 CPU, shard3

Sources: Screeps docs (control, defense, invaders, CPU), screepers wiki, Overmind / TooAngel / Hivemind patterns.
Last full refresh: **2026-11-09 17:1x** (autonomous push — docs/canvas scoreboard; waiting on bank20 ticks; no game code); before that **2026-11-09 14:3x** (north-star = T3 kiter; peacetime energy order unchanged); before that **2026-11-09 08:1x** (12h peacetime plan holds / leanBank→softCap clear); before that **2026-11-08 20:1x**; before that **2026-11-08 08:1x**; before that **2026-11-07 20:2x** (12h peacetime plan holds / leanBank→softCap clear + defender #1 ea-budget); before that **2026-11-07 08:1x**; before that **2026-11-06 20:1x**; before that **2026-11-06 08:1x**; before that **2026-11-05 20:2x** (12h post-W47N9 peacetime / severe cont debt 2nd maint); before that **2026-11-04 17:4x** (soft-band surplus trim / softCap hysteresis nUp4 thrash); before that **2026-11-04 14:4x** (post-abort maint cont debt); before that **2026-11-04 11:4x** (soft-band sticky preempt post-clear ctl sk); before that **2026-11-04 08:4x** (W47 link HMAX 3→4 overflow under softCap bank); before that **2026-11-04 05:4x** (leanBank rebuild-band upgKeep ≤2); before that **2026-11-04 02:4x** (hub ferry prime arm LEAN_ARM / thrash-band hubPrime); before that **2026-11-03 23:4x** (hub-link PRE-WARM during softCap bank / hubPrime); before that **2026-11-03 HUB_LINK nod YES** (`config.HUB_LINK=true`; hubReady waits on structure 33,34; labs/industry/market still OFF; sealMinE 25k; 20:4x soft-band kept); before that **2026-11-03 20:4x** (W47 soft-band ≠ softE / softCap re-ON drain); before that **2026-11-03 17:3x** (W47 post-roadCrit feedBound / !HUB_LINK ceiling); before that **2026-11-03 14:4x** (W47 roadCrit before deep seal / Overmind critical=25%); before that **2026-11-03 11:3x** (W47 container-first repair / Overmind <50% battery); before that **2026-11-03 08:4x** (softCap2 leanBank-style hysteresis LEAN_SOFT_ARM=22k); before that **2026-11-03 05:4x** (HUB_LINK flip day-of upgCeil→hubLinkLive); before that **2026-11-03 02:4x** (seal soft-gate vs softCap2 / no sealMinE raise); before that **2026-11-02 23:4x** (W47 HUB_LINK plumbing readiness / no flip); before that **2026-11-02 20:4x** (softCap thrash / sealMinE briefly 35k then Misaki→25k); before that **2026-11-02 17:4x** (post-war fortify vs softCap / sealMinE→LEAN_SOFT); before that **2026-11-02 14:5x** (W47N9 wartime economy freeze / GO); before that **2026-11-02 14:4x** (W47 peacetime ctl-battery surplus gate); before that **2026-11-02 11:4x** (W47 threat-soft holds w8upgrader ≤2 past `LEAN_SOFT`); before that **2026-11-02 08:4x strategy review** (W47 soft-band park deadlock / WORK-bound ~55%); before that **2026-11-02 05:4x** (home energy-bound / short-soft); before that **2026-11-02 02:4x** (W47 HMAX 2→3); before that **2026-11-01 23:4x** (thin-K + KO activate seq); before that **2026-11-01 20:4x** (post-minBuild leanBank re-arm); before that **2026-11-01 17:4x** (w8mminer vs soft-cap spawn prio); before that **2026-11-01 14:4x** (home KO labReady propose); before that **2026-11-01 11:4x** (first-K send pacing); before that **2026-11-01 11:1x** (RCL6_MINERALS flip); before that **2026-11-01 08:4x** (hold-band sink → stor20k); before that **2026-11-01 05:4x** (soft-cap survives RCL6_MINERALS flip); before that **2026-11-01 02:4x** (leanBank hysteresis 15k + soft-cap 25k); before that **2026-10-31 23:4x** (RCL6_MINERALS flipReady + post-flip leanBank hold); before that **2026-10-31 20:4x** (leanBank arm on day-crit, not 50ext); before that **2026-10-31 17:4x** (day-of north tower ≥600 / close hubNeedy residual); before that **2026-10-31 14:4x** (dormant terminal.send K→W46N8); before that **2026-10-31 11:4x** (dormant w8mminer + haul→terminal); before that **2026-10-31 08:4x** (leanBank → stor≥20k); before that **2026-10-31 05:4x** (day-of energy crash / `w8day.towerMinE`); before that **2026-10-31 02:4x** (home upgrade vs ideal 26 / `upgFeed`); before that **2026-10-30 23:4x** (W47N8 lean KO scaffold / `RCL6_LABS` split / w8min); before that **2026-10-30 20:4x** (RCL7 day-of no pre-bank / w8day); before that **2026-10-30 17:4x** (soft-ramp SOFT_MIN+localOn); before that **2026-10-30 14:4x strategy review** (W47N8 soft-ramp staging 100k); before that **2026-10-30 11:4x** (post-300k fundSpend exit / energy reallocation); before that **2026-10-30 08:4x** (RCL7 peacetime hold at 300k / no auto 1M); before that **2026-10-30 05:4x** (W45N7 Invader-res reclaim via attackController); before that **2026-10-30 02:4x** (STATIONARY_FILL readiness — keep queens); before that **2026-10-29 23:4x** (lab ramparts); before that **2026-10-29 20:4x** (W47N8 RCL7 day-of gate + spur roads); before that **2026-10-29 17:4x** (fortify fundSpend); before that **2026-10-29 14:4x** (mineral/boost §4); before that **2026-10-20 00:0x** (remote posture after novice end: `docs/DEFENSE_NOVICE.md`); before that **2026-10-19** (CPU `docs/CPU.md`, market `docs/MARKET.md`); before that **2026-10-18 strategy review** (W47N8 hold / safe-mode mechanics: `docs/W47N8_HOLD.md`); before that **2026-10-17 strategy review** (neighbours: `docs/NEIGHBORS.md`); before that **2026-10-16 strategy review** (defence before novice end: `docs/DEFENSE_NOVICE.md`); prior: RCL6 readiness `docs/RCL6.md` (10-15), RCL5 `docs/RCL5.md` (10-14). Also `docs/DEFENSE.md`, `docs/DEFENSE_PLAN.md`, `docs/LAYOUT_V2.md`, `docs/REMOTE_W45N8.md`, `docs/MODEL.md`, `docs/DATA.md`.

## Principles

1. **Energy throughput is everything early.** Two home sources = 20 e/t max; reserved remote adds ~10 e/t raw. Static miners + containers + haulers (then links) beat generic workers.
2. **Upgrade hard; build only what unlocks the next step.** Layout v2 is live (compact hub + fast-filler stamps, fixed roles, cached paths).
3. **CPU (20/tick) is precious.** Prefer fixed routes and stations over per-tick `find`. Keep bucket ≥ 5000. Measured ~3.5–4.5 CPU at RCL3 with remote.
4. **Defence = towers + ramparts + Misaki-controlled safe mode.** Towers do most early work; ramparts protect spawn/tower/core. **NEVER auto-activate safe mode** — alert Misaki and wait for her decision (standing rule since 2026-10-12).
5. **Growth after RCL4:** remote mining (W45N8 approved and live), then links; a 2nd room only with explicit Misaki approval (GCL 2 already allows a claim).
6. **Major decisions need approval:** claim/expand, attack or provoke player neighbours, spend credits/pixels, activate safe mode, respawn.
7. **Commander overlay is opt-in.** `Memory.cmd` (docs/COMMANDER.md) can take one creep or one structure and hand it back. It does not replace roles, and it must not write `Memory.ops` / `raidOrder` / softCap. Absent `Memory.cmd` means peacetime scripts are unchanged.

## North star (2026-11-09 ~14:3x · Misaki)

**Goal:** field (then sustain) at least one Tom-Roy-class full-T3 RA+self-heal kiter (4T/28RA/8H/10M; XGHO2×4 XKHO2×28 XZHO2×10 XLHO2×8) plus a supporting dismantle+heal pair. Spawn+boost energy for one kiter ≈7740; compound minerals 1500 (raw ≈ O1500 H1500 X1500 K960 Z420 L360 U120). Detail / phase checklist: living Page「通向三级风筝兵的发展规划」(ops canvas); combat autopsy `data/bustjetter_wipe/`.

**Order of work (does not replace peacetime energy policy):**
0. Energy pad — leanBank→20k → hold 15k floor → softCap clear ≥25k; **labs stay OFF** at ~15k storage
1. Upgrade pull — nUp→ceil6 / short≥70% → seal→1M under soft-gate
2. Push both RCL7 → RCL8 (CONTROLLER_LEVELS[7]=10.935M)
3. Industry prep — energy buffer toward ~100k (Overmind-style); labs 3→6→10; missing H/X/Z/L/U later decision (no market gate now)
4. T3 reactions → first one-off boost stock → sustained production
**Explicitly not now:** labs-on in live code, market, assault / war_cmd restart, new remote grab for minerals.

**12h review scorecard (mandatory from 2026-11-09 17:1x):** every 12h strategic review MUST score the living T3 north-star phases in Findings, not only the peacetime energy line. Minimum lines:
- **Phase0 energy pad:** bankLeft / softLeft / home stor vs 15k floor / labs OFF? (pass|fail|waiting)
- **Phase1 upgrade pull:** gated until Phase0 exit — nUp/ceil6 / short≥70% / seal soft-gate (blocked|ready|active)
- **Phase2 RCL8 prep:** both rooms RCL% + rem to 10.935M (observe only until Phase1)
- **Phase3+ industry:** deferred until ~100k-style buffer + RCL8 lab capacity — **no labs/market re-ask**
- One-line verdict: `waiting on ticks` | `small safe ship` | `phase exit` — capability to stock a kiter ≠ order to fight.


## Current state (2026-11-18 ~08:2x Asia/Hong_Kong · 12h review)

| Room | Notes |
|------|-------|
| W46N8 (home) | **RCL7** 72.01% (7.874M/10.935M); +188k/12h ≈ 20.66 e/t → RCL8 ≈ **8.14 days** at this pace (pace held; tick_s 4.710→4.746 slightly slower); stor avg 16.11k max **19077** min 13298, **19.25% under 15k** (was 16.1%); live tip ~18.9–19.0k why=ok nUp=2 work=28; labsN=6, factory done, sites=0; **KO ON** (authorized; stockpile **14071** already ≥900 — 13236 stor + 835 lab; 15k reaction floor not pausing / 20k boost skip held); LIVE **8daf0494** (@84324673 / 23:30:52 HKT, already-live filler-post fix) |
| W47N8 | **RCL7** 42.54% (4.652M); +182k/12h ≈ **20.00 e/t** → RCL8 ≈ **17.26 days** (was 18.83 / 18.72 d); stor avg 28.45k max **38563** min 17514 (0% <15k, 99.3% ≥20k, 88.8% ≥25k, 35.5% ≥30k, 0% ≥40k); live stor 20214 keep=2 phase=ready siteRem=0 leanBank0 softCap2 **on** (new threatSoft leftover + stor under 22k/25k); two 10W upgraders; **no 40k camp this window**, latch not armed; first <22k ARM 60 t + 70 t |

**08:2x scorecard:** Phase0 home floor **wobbled but held** (19.25% of 12h under 15k, was 16.1%; min 13.3k overnight, recovered to ~19k at the tip with nUp=2; 20k gate never latched — **zero ≥20k samples**, max 19077). W47 energy-side is above 25k for 88.8% of samples and above 30k for 35.5% (was 99.2% / 70.1%); **no 40k camp** (0% ≥40k, max 38563 at the open) is a drain, not a latch; the all-time high remains yesterday morning's 44416; live 20214, upLatched=0, softCap2 **ON** from a new standing-ops leftover — do not unpark ceil/seal. First <22k ARM stretches of these reviews (60 t + 70 t, min 17514). 40k latch **waiting**. Phase1 blocked (mid leftover / mid 40k wait). Phase2 home is still the lead and has crossed 72% (~8.14 d, was 8.59 d; 3h 18.07). W47 pace ~20.00 e/t / ~17.26 d. Phase3 lean KO is **on** and the stockpile has grown **9516→14071**; boost still waits for stor ≥20k; full industry / XGH2O / market stay deferred (energy 18–20k live, window max 19–39k ≪ 100k). Verdict: `waiting on ticks` (20k gate + W47 40k latch held; a 20k miss and a 40k drain are not phase exits; KO 14071 is stockpile growth, not a boost/industry turn-on; already-live 8daf0494 post-deploy walks used 34,32 when hub 33,33 was occupied; no new game code this review).

### Previous (2026-11-17 ~20:2x Asia/Hong_Kong · 12h review)


| Room | Notes |
|------|-------|
| W46N8 (home) | **RCL7** 70.29% (7.686M/10.935M); +188k/12h ≈ 20.62 e/t → RCL8 ≈ **8.59 days** at this pace (pace up and tick_s 4.78→4.71); stor avg 16.43k max **20244** min 12164, **16.1% under 15k** (was 25.2%); live tip ~13.9–14.6k why=floor_bank nUp=1 work=14, second 14W hatching; labsN=6, factory done, sites=0; **KO ON** (authorized; stockpile **9516** already ≥900 — 8836 stor + 680 lab; 15k reaction floor paused at the tip / 20k boost skip held); LIVE **c6d43491** (@84321282 / 19:02:43 HKT, already-live spawn-pocket fix) |
| W47N8 | **RCL7** 40.88% (4.470M); +172k/12h ≈ **18.83 e/t** → RCL8 ≈ **18.72 days** (was 18.75 / 19.58 d); stor avg 32.95k max **43041** min 23932 (0% <15k, 100% ≥20k, 99.2% ≥25k, 70.1% ≥30k, 12.7% ≥40k); live stor ~38.6k keep=2 phase=ready siteRem=0 leanBank0 softCap2 **off**; two 10W upgraders; **closest clean 40k camp** 470 t (peak 43041, 30 t short of 500), latch not armed |

**20:2x scorecard:** Phase0 home floor **improved** (16.1% of 12h under 15k, was 25.2%; min 12.2k during the 08:30 W45N7 core, recovered; 20k gate never latched — only touch 20244 / 20 t). W47 energy-side is above 25k for 99.2% of samples and above 30k for 70.1%; **closest clean 40k camp yet** (470 t, peak 43041, no freeze merge) is progress, not a latch; the all-time high remains this morning's 44416; live ~38.6k, upLatched=0, this morning's threatSoft leftover has expired (softCap2 off). 40k latch **waiting**. Phase1 blocked (mid 40k wait). Phase2 home is still the lead and has crossed 70% (~8.59 d, was 10.15 d; 3h 22.14). W47 pace ~18.83 e/t / ~18.72 d. Phase3 lean KO is **on** and the stockpile has grown **4981→9516**; boost still waits for stor ≥20k; full industry / XGH2O / market stay deferred (energy 14–43k ≪ 100k). Verdict: `waiting on ticks` (20k gate + W47 40k latch held; 20244 / 20 t and 470 t / 43041 are not phase exits; KO 9516 is stockpile growth, not a boost/industry turn-on; already-live c6d43491 first post-deploy walk took the south bypass; no new game code this review).

### Previous (2026-11-17 ~08:2x Asia/Hong_Kong · 12h review)


| Room | Notes |
|------|-------|
| W46N8 (home) | **RCL7** 68.57% (7.498M/10.935M); +169k/12h ≈ 18.73 e/t → RCL8 ≈ **10.15 days** at this pace (calendar stretched as tick_s 4.62→4.78); stor avg 15.85k max **20753** min 12447, **25.2% under 15k** (was 21.7%); live tip ~13.9–15.2k around the 15k floor (nUp=2 why=ok work=28 at 15203, later 13853 paused KO); labsN=6, factory done, sites=0; **KO ON** (authorized; stockpile **4981** already ≥900 — 4436 stor + 545 lab; 15k reaction floor paused at the tip / 20k boost skip held); LIVE **85c19c2e** (@84303299 / 19:19 HKT) |
| W47N8 | **RCL7** 39.31% (4.298M); +170k/12h ≈ **18.75 e/t** → RCL8 ≈ **19.58 days** (was 18.35 / 19.83 d); stor avg 32.77k max **44416** min 21448 (0% <15k, 100% ≥20k, 94.1% ≥25k, 73.8% ≥30k, 8.2% ≥40k); live stor ~41.3–41.4k keep=2 phase=ready siteRem=0 leanBank0 softCap2 **on** (threatSoft leftover, expires ~84314391); two 10W upgraders; **new 40k high** 44416 / 341 t (generous merge 451 t), latch not armed |

**08:2x scorecard:** Phase0 home floor **wobbled but held** (25.2% of 12h under 15k, was 21.7%; min 12.4k after defender bills, recovered; 20k gate never latched — first touch 20753 / only 51 t). W47 energy-side is above 25k for 94.1% of samples and above 30k for 73.8%; **new 40k high** (44416 / 341 t, generous merge 451 t) is progress, not a latch; the live ~41k touch is the same wait (upLatched=0); softCap2 is ON at the tip only from a threatSoft leftover — do not unpark ceil/seal. 40k latch **waiting**. Phase1 blocked (mid leftover / mid 40k wait). Phase2 home is still the lead (~10.15 d, was 9.68 d; 3h 19.93). W47 pace ~18.75 e/t / ~19.58 d. Phase3 lean KO is **on** and the ≥900 stockpile is **already met** (4981); boost still waits for stor ≥20k; full industry / XGH2O / market stay deferred (energy 14–41k ≪ 100k). Verdict: `waiting on ticks` (20k gate + W47 40k latch held; 20753 / 51 t and 44416 / 341 t are not phase exits; KO≥900 is stockpile completion, not a boost/industry turn-on; live W45N7 core is standing ops; no new game code this review).

### Previous (2026-11-16 ~20:2x Asia/Hong_Kong · 12h review)

| Room | Notes |
|------|-------|
| W46N8 (home) | **RCL7** 67.02% (7.329M/10.935M); +187k/12h ≈ 19.91 e/t → RCL8 ≈ **9.68 days** at this pace (calendar stretched as tick_s 4.31→4.62); stor avg 16.30k max 19787 min 12916, **21.7% under 15k** (was 16.1%); live tip ~15.3–15.6k why=thin_surplus nUp=2 tUp=2 work=28 upExtra=0; labsN=6, factory done, sites=0; **KO ON** (authorized; output lab 410 KO, ko=446 <900; 15k floor / 20k boost skip held); LIVE **85c19c2e** (@84303299 / 19:19 HKT) |
| W47N8 | **RCL7** 37.76% (4.129M); +172k/12h ≈ **18.35 e/t** → RCL8 ≈ **19.83 days** (was 18.25 / 19.07 d); stor avg 30.14k max **40553** min 20920 (0% <15k, 100% ≥20k, 86.4% ≥25k, 49.4% ≥30k, 1.4% ≥40k); live stor ~31.6–34.3k keep=2 phase=ready siteRem=0 leanBank0 softCap2 **on** (threatSoft leftover, expires ~84304356); two 10W upgraders; **first 40k touch** 40553 / 211 t, latch not armed |

**20:2x scorecard:** Phase0 home floor **wobbled but held** (21.7% of 12h under 15k, was 16.1%; min 12.9k after defender bills, recovered; 20k gate never latched — zero ≥20k samples, max 19787). W47 energy-side is above 25k for 86.4% of samples and above 30k for 49.4%; **first 40k touch** (40553 / 211 t) is progress, not a latch; softCap2 is ON at the tip only from a threatSoft leftover — do not unpark ceil/seal. 40k latch **waiting**. Phase1 blocked (mid leftover / mid 40k wait). Phase2 home is still the lead (~9.68 d, was 9.23 d; 3h 21.87 / tip exact2h 100.3%). W47 pace ~18.35 e/t / ~19.83 d. Phase3 lean KO is **on** (authorized T1 stockpile with energy floors); full industry / XGH2O / market stay deferred (energy 15–34k ≪ 100k). Verdict: `waiting on ticks` (20k gate + W47 40k latch held; 40553 / 211 t is not a phase exit; lean KO runs under standing floors; no new game code this review).

### Previous (2026-11-16 ~08:2x Asia/Hong_Kong · 12h review)


| Room | Notes |
|------|-------|
| W46N8 (home) | **RCL7** 65.31% (7.142M/10.935M); +206k/12h ≈ 20.51 e/t → RCL8 ≈ **9.23 days** at this pace; stor avg 16.62k max 19862 min 12705, **16.1% under 15k** (was 26.5%); live tip ~15.8–16.0k why=remote_pause nUp=1 tUp=1 work=14 upExtra=0 (W45N7 core just dispatched); labsN=6, factory done, sites=0; labs OFF (6 empty shells, actOk=1); LIVE **ffdf767** (@84268045 / 00:27 HKT) |
| W47N8 | **RCL7** 36.18% (3.957M); +183k/12h ≈ **18.25 e/t** → RCL8 ≈ **19.07 days** (was 18.97 / 18.45 d); stor avg 29.68k max **39213** min 23891 (0% <15k, 100% ≥20k, 90.4% ≥25k, 47.0% ≥30k, 0% ≥40k); live stor ~25.2k keep=2 phase=ready siteRem=0 leanBank0 softCap2 **off** threatSoft **off**; two 10W upgraders; this window's 39213 is just shy of last evening's 39332 closest-yet |

**08:2x scorecard:** Phase0 home floor **improved** (16.1% of 12h under 15k, was 26.5%; min 12.7k, longest under-15k 331 t; 20k gate never latched — zero ≥20k samples, max 19862). W47 energy-side is above 25k for 90.4% of samples and above 30k for 47.0% (max 39213, longest ≥30k 1741 t) and softCap2 is **OFF** at the tip; 40k latch **waiting** (0% ≥40k; all-time closest remains 39332); labs OFF ✔. Phase1 blocked (do not unpark ceil mid 40k wait; seal min wall 553k→720k is the designed raise while stor was >25k, not a ceil/phase exit). Phase2 home is still the lead (~9.23 d, was 9.70 d). W47 pace ~18.25 e/t / ~19.07 d. Phase3+ deferred — shells finished, reactions stay off (energy 16–25k ≪ 100k). Verdict: `waiting on ticks` (20k gate + W47 40k latch held; 39213 / 1741 t ≥30k is progress, not a phase exit; live W45N7 core is standing ops; no new game code).

### Previous (2026-11-15 ~20:2x Asia/Hong_Kong · 12h review)


| Room | Notes |
|------|-------|
| W46N8 (home) | **RCL7** 63.43% (6.936M/10.935M); +206k/12h ≈ 20.16 e/t → RCL8 ≈ **9.70 days** at this pace; stor avg 15.84k max 20459 min 9073, **26.5% under 15k** (was 28.3%); live tip ~16.7–17.0k why=ok nUp=2 tUp=2 work=28 upExtra=0; labsN=6, factory done, sites=0; labs OFF (6 empty shells, actOk=1); LIVE **ffdf767** (@84268045 / 00:27 HKT) |
| W47N8 | **RCL7** 34.51% (3.773M); +194k/12h ≈ **18.97 e/t** → RCL8 ≈ **18.45 days** (was 19.20 / 19.7 d); stor avg 28.73k max **39332** min 22082 (0% <15k, 100% ≥20k, 86.8% ≥25k, 32.0% ≥30k, 0% ≥40k); live stor ~24.5–25.0k keep=2 phase=ready siteRem=0 leanBank0 softCap2 **off** threatSoft **off** (18:28 leftover expired ~20:16), [22k, 25k) hysteresis; two 10W upgraders; closest yet to 40k latch (39332) |

**20:2x scorecard:** Phase0 home floor **held** (26.5% of 12h under 15k, was 28.3%; min 9.1k after mid-day defender bills, recovered; 20k gate never latched — longest ≥20k only 41 t, max 20459). W47 energy-side is above 25k for 86.8% of samples (max 39332, closest yet) and softCap2 is **OFF** at the tip (leftover expired, designed [22k, 25k) hysteresis, sL=496); 40k latch **waiting** (longest ≥30k 231 t, 0% ≥40k); labs OFF ✔. Phase1 blocked (do not unpark ceil/seal mid 22–25k hysteresis / mid 40k wait). Phase2 home is again the lead (~9.70 d, was 11.6 d; 3h 20.96 e/t). W47 pace ~18.97 e/t / ~18.45 d. Phase3+ deferred — shells finished, reactions stay off (energy 17–25k ≪ 100k). Verdict: `waiting on ticks` (20k gate + W47 40k latch held; 39332 is progress, not a phase exit; no new game code).

### Previous (2026-11-15 ~08:2x Asia/Hong_Kong · 12h review)

| Room | Notes |
|------|-------|
| W46N8 (home) | **RCL7** 61.54% (6.730M/10.935M); +184k/12h ≈ 18.67 e/t → RCL8 ≈ **11.6 days** at this pace; stor avg 15.8k max 18946 min 9775, **28.3% under 15k** (was 39.0%); live tip ~18.9–19.0k why=ok nUp=2 tUp=2 work=28 upExtra=0; labsN=6, factory done, sites=0; labs OFF (6 empty shells); LIVE **ffdf767** (@84268045 / 00:27 HKT) |
| W47N8 | **RCL7** 32.73% (3.579M); +189k/12h ≈ **19.20 e/t** → RCL8 ≈ **19.7 days** (was 19.36 / 20.0 d); stor avg 26.2k max **35385** min 21653 (0% <15k, 100% ≥20k, 70.2% ≥25k, 0% ≥40k); live stor ~35.0–35.4k keep=2 phase=ready siteRem=0 leanBank0 softCap2 **on** (threatSoft leftover after 07:27 W47N7 core, sL=0); two 10W upgraders; closest yet to 40k latch |

**08:2x scorecard:** Phase0 home floor **improved** (28.3% of 12h under 15k, was 39.0%; min 9.8k after a defender bill, recovered; 20k gate never latched — zero ≥20k samples, max 18946). W47 energy-side is above 25k (70.2% of samples, live ~35k, sL=0) but softCap2 is **re-ON from threatSoft leftover** — known class, not a bank failure; 40k latch **waiting** (closest 35.4k, open ≥30k climb from 07:42); labs OFF ✔. Phase1 blocked (do not unpark ceil/seal mid leftover / mid 40k wait). Phase2 home is again the lead (~11.6 d, was 15.2 d; morning 1h 22.6 e/t). W47 pace ~19.2 e/t / ~19.7 d. Phase3+ deferred — shells finished, reactions stay off (energy 19–35k ≪ 100k). Verdict: `waiting on ticks` (20k gate + W47 40k latch held; 35k is progress, not a phase exit; no new game code).

### Previous (2026-11-14 ~20:2x Asia/Hong_Kong · 12h review)


| Room | Notes |
|------|-------|
| W46N8 (home) | **RCL7** 59.86% (6.546M/10.935M); +144k/12h ≈ 14.87 e/t → RCL8 ≈ **15.2 days** at this pace; stor avg 15.1k max 18568 min 10878, **39.0% under 15k** (was 50.2%); live tip 16.7–17.4k why=ok tUp=2 (2nd spawning) upExtra=0; last lab finished 13:21, labsN=6, factory done, sites=0; labs OFF (actOk=1, homeStor over 15k); LIVE **4ff78b4** (@84239549 / 13:26 HKT) |
| W47N8 | **RCL7** 31.00% (3.390M); +188k/12h ≈ **19.36 e/t** → RCL8 ≈ **20.0 days** (was post-resume 16.09 / ~24.6 d); stor avg 26.3k max 32038 min 22916 (0% <15k, 100% ≥20k, 83.1% ≥25k, 0% ≥40k); live stor 24.2–25.0k keep=2 phase=ready siteRem=0 labsN=6 factory done leanBank0 softCap2 **off** (sticky clear, never <22k ARM); two 10W upgraders |

**20:2x scorecard:** Phase0 home floor **improved but still thin** (39.0% of 12h under 15k, was 50.2%; min 10.9k; 20k gate never latched — zero ≥20k samples, max 18568). Last home lab **DONE**. W47 **softCap2 sticky-cleared**: never below the 22k ARM all window, 83.1% ≥25k, cap off, 40k latch **waiting** (closest 32.0k); labs OFF ✔. Phase1 blocked (do not unpark ceil/seal mid 23–32k camp). Phase2 home still the lead (~15.2 d, was 17.4 d; 3h pace 17.7 e/t). W47 forward pace ~19.4 e/t / ~20.0 d (pre-site was ~18 e/t / ~22 d). Phase3+ deferred — shells are finished, reactions stay off (energy 17–25k ≪ 100k). Verdict: `waiting on ticks` (20k gate + W47 40k latch held; softCap clear is a Phase0 step, not a phase exit; no new game code).

### Previous (2026-11-14 ~08:2x Asia/Hong_Kong · 12h review)


| Room | Notes |
|------|-------|
| W46N8 (home) | **RCL7** 58.54% (6.402M/10.935M); +130k/12h ≈ 13.31 e/t → RCL8 ≈ **17.4 days** at this pace; stor avg 14.5k max 17474 min 8532, **50.2% under 15k** (was 56.6%); live tip 13328–14578 why=floor_bank nUp=1 upExtra=0; one lab site left (34,20 29.1k/50k; labsN=5, factory done); labs OFF (actOk=0 homeStor); LIVE **4ff78b4** (@84239549 / 13:26 HKT) |
| W47N8 | **RCL7** 29.28% (3.202M); blended +51k/12h ≈ 5.25 e/t, post-resume from 04:22 **16.09 e/t** → RCL8 ≈ **24.6 days**; stor avg 10.8k max 25486 min 0 (20.8% ≥20k, 3.4% ≥25k, 0% ≥40k); live stor 24733–25183 keep=2 phase=ready siteRem=0 labsN=6 factory done leanBank0 softCap2 ON threatSoft leftover; two 10W upgraders |

**08:2x scorecard:** Phase0 home floor **still thin** (50.2% of 12h under 15k, was 56.6%; min 8.5k; 20k gate never latched — zero ≥20k samples, max 17474). W47 **authorized site wave DONE**: upgrade resumed 04:22, keep=2, phase=ready, stor recovered from a mid-window 0 crash to a 25k flicker (max 25486, longest ≥25k 31 t) — softCap2 still on, not a sticky clear; 40k latch **waiting**; labs OFF ✔. Phase1 blocked. Phase2 home still the lead (~17.4 d at this floor-bank pace, should tighten once the last home lab ends and nUp=2 can stick; most hours were a steady 13–14 e/t). W47 forward pace ~16.1 e/t / ~24.6 d (was frozen last window; pre-site pace was ~18 e/t / ~22 d). Phase3+ deferred — last shell may finish, reactions stay off (energy 13–25k ≪ 100k). Verdict: `waiting on ticks` (finish last home lab, let W47 softCap stick, keep the 20k gate; no new game code).

### Previous (2026-11-13 ~20:1x Asia/Hong_Kong · 12h review)


| Room | Notes |
|------|-------|
| W46N8 (home) | **RCL7** 57.35% (6.271M/10.935M); +132k/12h ≈ 13.49 e/t → RCL8 ≈ **17.6 days** at this pace; stor avg 14.4k max 18333 min 7518, **56.6% under 15k** (was 50.7%); live tip 13082 why=floor_bank nUp=1 upExtra=0; 2 lab sites still up (33,22 9.3k/50k, 34,20 4.3k/50k; factory done, labsN=4); labs OFF (actOk=0 homeStor); LIVE **4ff78b4** (@84239560 / 13:26 HKT) |
| W47N8 | **RCL7** 28.81% (3.151M); +0/12h ≈ 0.00 e/t (was 0.00); progress flat 3150854 since 17:24; stor avg 3.3k max 8800 min 0 (100% <15k, 0% ≥20/25/40k); live stor 5920 keep=1 (f7328c4, siteRem 123709 was 259481; lab 29,38 completed, live labs 3, factory done) phase=minBuild leanBank1 bankWhy=minBuild softCap2 ON threatSoft=0; builders=4 |

**20:1x scorecard:** Phase0 home floor **still thin** (56.6% of 12h under 15k, was 50.7%; min 7.5k at the open is the morning-dip tail, then mid-teens hugging the floor; 20k gate never latched — zero ≥20k samples, max 18333). W47 **authorized site wave more than halfway done**: 0 upgrade all 12h, stor 0–8.8k, softCap2 still on, 40k latch **waiting**; labs OFF ✔. `f7328c4` keep=1 while sites are up is held — do not revert (W47 rem 259k→124k, ~8–9 h at ~17 e/t; home two labs rem ~86k). Phase1 blocked. Phase2 home still the lead (~17.6 d at this depressed pace, should tighten once home lab spend ends and nUp=2 can stick; most hours were a steady 14 e/t). W47 frozen this window (pre-site pace was ~18 e/t / ~22 d). Phase3+ deferred — shells may finish, reactions stay off (energy 6–13k ≪ 100k). Verdict: `waiting on ticks` (finish authorized sites, recover both banks, keep the 20k gate; no new game code).

### Previous (2026-11-13 ~08:2x Asia/Hong_Kong · 12h review)


| Room | Notes |
|------|-------|
| W46N8 (home) | **RCL7** 56.13% (6.139M/10.935M); +129k/12h ≈ 13.63 e/t → RCL8 ≈ **18.6 days** at this pace; stor avg 14.7k max 17355 min 5428, **50.7% under 15k** (was 24.9%); live tip 7718 why=floor_bank nUp=1 upExtra=0; 4 lab/factory sites still up (factory 97.3k/100k, one lab at 750, two at 0); labs OFF (actOk=0 homeStor); LIVE **a72e3c0** (@84234754 / 07:34 HKT) |
| W47N8 | **RCL7** 28.81% (3.151M); +0/12h ≈ 0.00 e/t (was 11.84); progress flat 3150854 since 17:24; stor avg 769 max 5760 min 0 (100% <15k, 0% ≥20/25/40k); live stor 3494 keep=1 (f7328c4, 6 sites, siteRem 259481) phase=bank20 leanBank1 bankWhy=threat softCap2 ON threatSoft leftover; builders=4 |

**08:2x scorecard:** Phase0 home floor **worsened** (50.7% of 12h under 15k, was 24.9%; min 5.4k after a ~200 t W45N7-hold stall then a 5400e defender + factory spend; 20k gate never latched — zero ≥20k samples, max 17355). W47 **authorized site wave continues**: 0 upgrade all 12h, stor 0–5.8k, softCap2 still on, 40k latch **waiting**; labs OFF ✔. `f7328c4` keep=1 while sites are up is held — do not revert (sites 11→10; home factory nearly done; W47 rem ≈259k, ~1.5 d at ~8 e/t). Phase1 blocked. Phase2 home still the lead (~18.6 d at this depressed pace, should tighten once the 15k floor recovers; overnight was a steady 14 e/t). W47 frozen this window (pre-site pace was ~18 e/t / ~22 d). Phase3+ deferred — shells may finish, reactions stay off (energy 3–8k ≪ 100k). Verdict: `waiting on ticks` (finish authorized sites, recover both banks, keep the 20k gate; no new game code).

### Previous (2026-11-12 ~20:1x Asia/Hong_Kong · 12h review)


| Room | Notes |
|------|-------|
| W46N8 (home) | **RCL7** 54.96% (6.010M/10.935M); +193k/12h ≈ 19.79 e/t → RCL8 ≈ **12.8 days**; stor avg 15.8k max 18617 min 12190, **24.9% under 15k** (was 12.8%); live tip 14.0–14.7k why=floor_bank nUp=1 upExtra=0; 4 lab/factory sites still up (factory 22.6k/100k, 3 labs 0); labs OFF (actOk=0 homeStor); LIVE **afde7dd** (@84224625 / 18:43 HKT) |
| W47N8 | **RCL7** 28.81% (3.151M); +115k/12h ≈ 11.84 e/t (was 18.04) → RCL8 ≈ **33.9 days** at this pace; stor avg 13.7k max 26276 min 0 (46.3% <15k, 43.7% ≥20k, 6.8% ≥25k, 0% ≥40k); progress flat 3150854 since 17:24; live stor 0 keep=1 (f7328c4, 11 sites, siteRem 336100) phase=bank20 leanBank1 bankWhy=threat softCap2 ON threatSoft leftover; builders=0, emergency miners |

**20:1x scorecard:** Phase0 home floor **worsened** (24.9% of 12h under 15k, was 12.8%; min 12.2k after defender + site spend; 20k gate never latched — zero ≥20k samples, max 18617). W47 **authorized site wave + Invader drain**: stor 0 since 18:01, upgrade parked, softCap2 re-armed, 40k latch **waiting**; labs OFF ✔. Mid-day `f7328c4` keep=1 while sites are up is held — do not revert. Phase1 blocked. Phase2 home still the lead (~12.8 d, pace down 21.63→19.79); W47 ~33.9 d at this window (pre-site pace was ~18 e/t / ~22 d). Phase3+ deferred — shells may finish, reactions stay off (energy 0–15k ≪ 100k). Verdict: `waiting on ticks` (finish authorized sites, recover the W47 bank, keep the 20k gate; no new game code).

### Previous (2026-11-12 ~08:1x Asia/Hong_Kong · 12h review)


| Room | Notes |
|------|-------|
| W46N8 (home) | **RCL7** 53.20% (5.817M/10.935M); +211k/12h ≈ 21.63 e/t → RCL8 ≈ **12.1 days**; stor avg 16.5k max 19.7k min 13626, **12.8% under 15k** (was 25%); live tip 17.7k why=ok nUp=2 upExtra=0; labs OFF (actOk=1); LIVE **e98671f** (@84206586 / 20:34 HKT) |
| W47N8 | **RCL7** 27.76% (3.035M); +175k/12h ≈ 18.04 e/t (was 16.99) → RCL8 ≈ **22.3 days**; stor avg 21.7k max 26607 min 12487 (16.6% ≥25k, 72.5% ≥20k, 0% ≥40k); keep=2 / 40k sticky not armed (closest 26.6k); softCap2 **cleared** after 530 t ≥25k (peak 26607 @08:04), live post-clear hysteresis stor 23.2k (above 22k ARM, softLeft 1.8k) softBand1 phase=ready leanBank0 |

**08:1x scorecard:** Phase0 home floor **improved** (12.8% of 12h under 15k, was 25%; min 13.6k vs last window's 8.6k; 20k gate never latched — zero ≥20k samples); W47 **softCap2 cleared** into the designed [22k, 25k) hysteresis (530 t at 25–26.6k, then 23.2k) — not yet a sticky ≥25k hold, 40k latch **waiting**; labs OFF ✔. Phase1 blocked. Phase2 home lead (~12.1 d), W47 ~22.3 d (pace up). Phase3+ deferred. Verdict: `waiting on ticks` (20k gate + keep=2 / 40k latch held; softCap clear is progress, not a phase exit; no new game code).

### Previous (2026-11-11 ~20:2x Asia/Hong_Kong · 12h review)



| Room | Notes |
|------|-------|
| W46N8 (home) | **RCL7** 51.27% (5.606M/10.935M); +207k/12h ≈ 21.23 e/t → RCL8 ≈ **12.9 days**; stor avg 15.8k max 20.6k min 8574, **25% under 15k** (was 27%); live tip 19.1k why=ok nUp=2 upExtra=0; labs OFF (actOk=1); LIVE **d09e9c4** (#40 @84202370) |
| W47N8 | **RCL7** 26.14% (2.859M); +166k/12h ≈ 16.99 e/t (was 16.65) → RCL8 ≈ **24.3 days**; stor avg 24.0k max 32259 min 9478 (46.2% ≥25k, 0% ≥40k); keep=2 / 40k sticky not armed (closest 32.3k); phase=bank20 leanBank1 bankWhy=threat softCap2 ON threatSoft leftover WINDOW 1500 |

**20:2x scorecard:** Phase0 home floor **wobbling but improved** (25% of 12h under 15k; 8.6k evening dip + 19:29 2h 63.5% SOFT FIRST were two 5200e remote-defender bills, then designed 15k-floor recovery — the 20k gate never latched, best ≥20k streak 90 t); W47 reached a real 25–32k band (46% of samples ≥25k) then leanBank rebuild after the same bills, 40k sticky **waiting**; labs OFF ✔. Phase1 blocked. Phase2 home lead (~12.9 d), W47 ~24.3 d (pace up). Phase3+ deferred. Verdict: `waiting on ticks` (20k gate + keep=2 / 40k latch held; no new game code).

### Previous (2026-11-11 ~08:2x Asia/Hong_Kong · 12h review)


| Room | Notes |
|------|-------|
| W46N8 (home) | **RCL7** 49.37% (5.398M/10.935M); +202k/12h ≈ 20.63 e/t → RCL8 ≈ **13.7 days**; stor avg 15.6k max 21.1k, **27% under 15k** (was 32%); live tip 14.2k floor_bank nUp=1 upExtra=0; labs OFF (actOk=0 homeStor); LIVE **c27c44f** |
| W47N8 | **RCL7** 24.62% (2.693M); +163k/12h ≈ 16.65 e/t (was 12.76) → RCL8 ≈ **25.3 days**; stor avg 21.0k max 26.2k (18.4% ≥25k, 0% ≥40k); keep=2 / 40k sticky not armed; phase=ready bankWhy=soft softCap2 ON softLeft~4.6k |

**08:2x scorecard:** Phase0 home floor **wobbling but improved** (27% of 12h under 15k; overnight formal ALERT was defender bills, not the 16k yo-yo — that lever is settled); W47 25k touches did **not** stick, 40k sticky **waiting**; labs OFF ✔. Phase1 blocked. Phase2 home lead (~13.7 d), W47 ~25 d (pace up). Phase3+ deferred. Verdict: `waiting on ticks` (last review's 20k/300t gate held; no new game code).

### Previous (2026-11-10 ~20:2x Asia/Hong_Kong · 12h review)


| Room | Notes |
|------|-------|
| W46N8 (home) | **RCL7** 47.52% (5.196M/10.935M); +200k/12h ≈ 20.50 e/t → RCL8 ≈ **14.6 days**; stor avg 15.3k max 19.1k, **32% under 15k** (16k 3rd-upgrader yo-yo); labs OFF; LIVE **17b61c0** (PR 34) plus this review's sticky 20k gate |
| W47N8 | **RCL7** 23.13% (2.529M); +125k/12h ≈ 12.76 e/t (was 8.9); stor avg 19.4k max 25.7k (7.2% ≥25k, 0% ≥40k); keep=2 / 40k sticky not armed |

**20:2x scorecard:** Phase0 home floor **wobbling** (32% of 12h under 15k — this ship is the lever); W47 bank20 at the 25k edge but 40k sticky **waiting**; labs OFF ✔. Phase1 blocked. Phase2 home lead (~14.6 d), W47 ~34 d. Phase3+ deferred. Verdict: `small safe ship` (home 3rd-upgrader sticky 20k/300t; net spawn waste was only 3 e/t, the yo-yo was the limiter).

### Previous (2026-11-10 ~09:2x JST · 12h review)

| Room | Notes |
|------|-------|
| W46N8 (home) | **RCL7** 45.68% (4.995M/10.935M); +195k/12h ≈ 20 e/t → RCL8 ≈ 15 days; stor **14659** upBank=1 nUp1; labs OFF; LIVE **b9c984e** (ledger-only change on top of 87d8c84 behaviour) |
| W47N8 | **RCL7** 21.99% (2.404M); +87k/12h ≈ 8.9 e/t; stor **14380**; leanBank phase=bank20 equilibrium |

**09:2x scorecard:** Phase0 home floor **wobbling** (5 patrols <15k overnight after defender spend; back ~15k); W47 bank20 **waiting**; labs OFF ✔. Phase1 blocked. Phase2 home lead (~15 d). Phase3+ deferred. Verdict: `small safe ship` (ledger recycle refund) + next lever = home upgrader churn under floor-bank (sp:upgrader gross 13.8 e/t vs up 17 e/t; measure net first).

### Previous (2026-11-09 ~21:1x JST · 12h review)

| Room | Notes |
|------|-------|
| W46N8 (home) | **RCL7** 43.89% (4.80M/10.935M, rem ≈6.14M); stor **15742** ABOVE 15k floor; ~21 e/t → RCL8 ≈14–15 days; labs OFF; LIVE **87d8c84** |
| W47N8 | **RCL7** 21.19% (2.317M, rem ≈8.62M); stor **11051** (24h band 9.1–21.3k); ~10.8 e/t; leanBank phase=bank20; walls 502–589k, ramparts ~300k |

PEACETIME; war_cmd pause `aborted_by_misaki`; remotes SAFE (W45N7 cores ~7/day absorbed by home defenders); listener single-slot 5:5:1:1; CPU ~16–17/20 bucket 10k.

**12h scorecard (21:1x JST):**
- **Phase0 energy pad:** home floor **pass** (15.7k); W47 bank20/softCap clear **waiting** — stor oscillates 10–21k, no ≥25k clear for ~3 days (bankLeft≈8.9k, softLeft≈13.9k); labs **OFF** ✔.
- **Phase1 upgrade pull:** **blocked** (gated on Phase0 exit).
- **Phase2 RCL8 prep:** home 43.89% (≈14–15 d), W47 21.19% (≈40+ d at current pace) — observe; home is the lead room.
- **Phase3+ industry:** deferred (~100k buffer + RCL8 labs) — no re-ask.
- **Verdict:** `small safe ship` (box-only `tools/ledger.py`); game plan `waiting on ticks`.

**Wall/threat note (21:1x):** threatSoft's 100k urgent floor is a no-op while seal walls ≥500k / ramparts ~300k; wall repair ≈0.6 e/t over 10 days. Do not throttle it. Spawn-side defender cost is the larger, attributable sink (`tools/ledger.py diff`).

**RCL8 funnel (planned, not coded):** when home reaches RCL8 its upgrade caps at 15 e/t; surplus goes by terminal to W47 (range 1, ≈3% send cost) — community-standard "feed the room still climbing". Code this when home ≥~90%.

Ideal vs actual: `tools/model.py` / Grafana / `upgFeed` / `w8day` / `w8soft` / `labReady` / **`tools/ledger.py diff`** (spawn-by-role vs repair vs upgrade e/t). Peacetime order unchanged: leanBank→20k → softCap clear ≥25k → nUp→ceil6 → seal→1M → home floor ≥15k → labs KO (**no re-ask**); north-star after RCL8 + ~100k buffer. Commander stays a separate key (`docs/COMMANDER.md`).

## Phases

| Phase | Trigger | Goals | Exit |
|---|---|---|---|
| P0 Bootstrap | spawn placed | harvesters → miners path | RCL2 ✅ |
| P1 Economy | RCL2 | extensions, containers, static miners + haulers, core roads | RCL3 ✅ |
| P2 Defence | RCL3 | tower #1, ramparts spawn/tower, **alerts (no auto SM)**, 10 ext, layout v2 | tower live before novice ends ✅ early |
| P3 Storage + remote harden | RCL4 | storage, 20 ext, CLAIM2 reserver, rampart HP 50k, Invader defender ON (DEFENDER.md) | storage > 50k ✅ (economy); walls bank still pending |
| P4 Links | RCL5 | tower #2 first; link plan per `docs/RCL5.md` (recommended: hub + controller link at RCL5, source A at RCL6; stationary fillers from RCL7) — needs Misaki | CPU avg < 15 |
| P5 RCL6 | RCL6 | source A link + 10 ext first; v4 walls (bank 20k → step 1 100k before 10-28); terminal/extractor/labs **deferred** (`plan.RCL6_MINERALS`) | wall step 1 live; step 2 may finish after novice end |
| P6 Expand | RCL6+, GCL≥2 | **2nd room only with Misaki approval** | 2nd room RCL3 |
| P7 RCL7–8 | — | spawns 2–3, factory, 6 towers, power spawn, nuker, observer; min-cut if needed | RCL8 |

## Standing rules

- Never let refill/harvesters drop to 0 (emergency body from `energyAvailable`).
- ≤ 5 construction sites; planner every 50 ticks or on RCL change.
- Every upload passes `scripts/check.js` (+ `scripts/sim.js`).
- Remote: flee + pause on player combat; **NPC Invader defender ON** (W45N8); never attack players.
- Safe mode: **alert only** — Misaki decides.
- Patrol owns `state/next_iteration.json` cadence; strategy review updates docs/roadmap and small safe code fixes.
- Commander (phase 0, 2026-11-05): takeover lives in `Memory.cmd`, not in `Memory.ops.w47n9`. Release / TTL / `CMD.disarm()` restores the role. Do not auto-arm war, safe mode, claim, or market from that channel. Detail: `docs/COMMANDER.md`.
- Websocket rooms (2026-11-05): peacetime ops listener holds one slot, wall-clock W46N8:W47N8:W45N8:W45N7 = 5:5:1:1 (`tools/room_rot.py`). While the commander bot is live-commanding, ops drops room subscriptions (`touch metrics/listener_yield_rooms`); the commander subscribes the battle rooms and may use both official slots. Remove the file after handback. This is box ops, not `Memory.cmd`.
