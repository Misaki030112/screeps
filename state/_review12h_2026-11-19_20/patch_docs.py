#!/usr/bin/env python3
from pathlib import Path
ROOT = Path("/workspace/screeps")

ROADMAP_BLOCK = """## 2026-11-19 20:2x Asia/Hong_Kong 12h strategic review: plan holds; home 77.3% ~6.25 d, 20k only 20829 / 150 t, W47 post-fight ~22k, KO 27886, 20k/40k gates held (docs only)

- **Chose:** Full-board 12h review. The 08:2x morning run failed (box/DB outage 05:33–09:23, 2910 t / 3.84 h), so this pass also recaps the 24 h since last evening's successful review. SoftCap / industry / market widgets outstanding — **never re-ask**. Home KO is already authorized (`Memory.ops.labs={W46N8:'KO'}`) and is no longer a widget. War_* stay stopped (`aborted_by_misaki`). Question: after home crossed 77.3% and first touched 20k for 150 t, a W47 combat dip that recovered to ~22k with still no 40k camp, and a KO stockpile that has grown 18716→27886, does the peacetime energy order still hold, and is there a small safe ship?
- **Findings:** Live t84359040–057 LIVE **2b5398f7** (deploy@84345299 / 02:28:52 HKT, hold W47N7 civilians while the remote threat FSM is open; already-live this window, not this review). Also already-live this window: **6d153087** @84340798 / 20:35 last evening (POST2 35,31 + yield occupied south-rail exit 33,34), deployed after the last 12h review. Sampled window t84350530→84359020 (8490 t, tick_s 4.694, ~11.07 h; estimated 08:20 start 84349700, but the first room_stats sample is 09:23 after the 05:33–09:23 hole). Coverage 447/850 ≈ 52.6% after 21 box pauses totalling 17513 s — worse than last evening's 72.5%. Home RCL7 **77.27%** (8.449M; +183k in the sampled window ≈ **21.61 e/t**, was 21.57; RCL8 ≈ **6.25 days** at this window's pace — calendar tightened on the faster percent even though tick_s 4.673→4.694 was slightly slower), stor avg 16.34k max **20829** min **12757**, **12.75% of samples under the 15k floor** (was 15.73%); live tip **15530** why=ok nUp=2 work=28, above the floor, energy-bound, upExtra=0. The 20k/300t latch never armed — **one stretch 150 t** (11:21–11:32, 20029–20829, max **20829** @11:28), after last evening's 0 samples / max 19772 and the earlier 20244 / 20 t touch. Under-15k share eased 15.73%→12.75%; longest stretch **130 t** (16:27–16:37, min **14077**) after the 16:08 W45N7 Invader — do not change the 15k floor. Home 3h **22.57** e/t / 6h 20.96 / exact2h 24.07/26=92.6% ABOVE is a strong afternoon, not a 3rd. W47 **47.44%** (5.187M; +165k ≈ **19.46 e/t**, was 19.33; RCL8 ≈ **16.04 days**). Stor avg 25.99k max **35585** @17:13 min **18926** @10:30, **0% under 15k, 98.4% ≥20k, 64.0% ≥25k, 14.1% ≥30k, 0% ≥40k** (was 80.7% / 62.2% / 7.7% / 0%). **No 40k camp this window**; 24h max since last evening is **36249 @00:06**; all-time high remains 11-17 morning's **44416 / 341 t**; closest clean camp remains 11-17 evening's 470 t / peak 43041; longest ≥30k this window **840 t** (16:33–17:40, peak 35585) then the 17:32 fight. After that W47N7 Invader the room dipped to 21320 @18:20 and is live **22025**, **upLatched=0**, keep=2 phase=ready siteRem=0 leanBank=0 softE=0 softCap2 **OFF** threatSoft=0 sealPark=1 bankWhy=ready softLeft=2975 upgCeil=2 hubLink ready, contMinPct=52 roadCrit=0. The 17:32 threat window expired ~19:51; sealPark is the strict ≥25k rule (stor still under 25k), and softLeft=2975 is designed hysteresis after the <22k dip — not a cap-on, not a phase exit. Do not unpark ceil/seal, do not add a third. Remotes **ALL SAFE** at the tip (W45N8/W45N7/W47N7 res 2233/2101/2430, cores 0 host 0, no defenders left). Standing ops this window, not a phase change: W45N7 solo Invader 16:08–16:26 cleared SAFE why=killed (227 t), W47N7 17:32–17:35 cleared why=killed, plus a 10:00 W47N7 spawn_start still in the incidents table. FORMAL W47 upgrade alert **CLEARED at 19:22** after 21 consecutive duals (short was 26 e/t from an idle builder helping at the controller, not a standing third). At the 20:27 tip exact2h 19.96/30.08=66.3% is under 70% again; last20–300 designed 20.00=66.5% IS soft — the concurrent 20:23 hourly patrol will settle first dual vs hold. Either way, keep=2's designed 20 e/t is 66.5% of the 30.08 ceiling, so formal short-soft ALERTs at the designed rate remain expected, not a reason to add a third. Home exact2h 24.07/26=92.6% ABOVE. CPU 12h avg **17.87** p95 21.36 max 28.94, bucket min 9920, n_cpu≥40=0 (was 17.24; slightly up after two Invader waves, still not 15.8–16.2, no speculative trim). Home KO is **ON** (authorized) and the stockpile grew **18716→27886** (output lab 34,22 **650 KO**, storage **27236 KO**, terminal 0); inputs 33,21/33,22 1650 K / 1650 O. At the tip `labReady` why=active actOk=1 homeStor=15630 — the 15k reaction floor is **not** pausing (barely over). The 20k boost skip held — no kite boost, even though KO ≫ 900, because the only ≥20k camp was 150 t. Industry / market / W47 labs stay OFF (w8min why=ready, not a labs turn-on). Home walls/ramparts still ≥300k (min wall 300001 / rampart 300601); W47 wall min **1000001**, rampart min **300001** — do not start a fortify push mid 40k wait / mid ~22k stor. At the tip, fillers were on 34,32 and POST2 35,31 with 1200e, plus a spawning replacement — the already-live park fixes are visible; observe further walks, do not start another routing pass. Ledger (24 h, no morning snap) t84340747→84359069: home net sp:upgrader **1.63** (under the 5 e/t waste gate); W47 up 19.42 matches 24h room_stats 19.42. 24h since last successful review: home 73.84%→77.27% ≈ 20.45 e/t, W47 44.18%→47.44% ≈ 19.42 e/t; overnight W47 max 36249 still never hit 40k. Community: Overmind `UpgradeSite` re-checked on blob 2eae97b — `storageBuffer=100000` / `energyPerBodyUnit=25000` (correcting last evening's typo of energyPerBodyUnit=10000); the 100k gate is unchanged. TooAngel / International not re-cloned; 18 Nov morning comparison still applies. This window's floors (home max 20829, W47 max 35585, live ~15.5k / 22k) remain far below that band, so the existing 15k / 20k / 40k gates should be **held**, not loosened, and industry should stay off. CPU 17.87 / 20 still argues against a new remote. KO already running matches "don't put off minerals." Sites 0 at the tip (W47 briefly had 1 site 13:56–14:08); labs/factory/terminal 6+1+1 both rooms. Memory.cmd.on=1 at=84224348 is the same stale empty cmd. lastErrorTick 83976900 unchanged.
- **Shipped:** Nothing (docs + ROADMAP only). SoftCap / leanBank / sealMinE / HUB_LINK / industry / market / war_* / listener / 15k floor / 20k boost skip / W47 keep=2 unchanged. No game deploy this review. (Already-live this window, not this review: **2b5398f7** @84345299 / 02:28:52; **6d153087** @84340798 / 20:35 last evening.)
- **Reprioritise (next 1–3):** (1) **Keep the 20k gate** — 2×14W remain energy-bound; a 3rd still should not arm until a real 20k surplus holds 300 t (this window's closest camp was 20829 / 150 t). Do not change the 15k floor. Home is still the RCL8 lead (~6.25 d at this 21.61 e/t pace; 3h 22.57) and has crossed 77.3%. home→W47 terminal funnel still coded only at home ≥~90%. (2) W47 stays **keep=2 until the 40k/500 t latch**. This window had **no 40k camp** (0% ≥40k, max 35585; 24h max 36249 @00:06) and a post-Invader <22k dip that recovered to ~22k; the all-time high remains 11-17 morning's 44416 / 341 t, and the closest clean camp remains 11-17 evening's 470 t. Live 22025, softCap2 off, threat expired, bankWhy=ready, sealPark because stor <25k — do not add a third; do not unpark ceil/seal mid 40k wait; do not lift keep because a formal short-soft may reappear at the designed 20 e/t rate. The filler-park / POST2 fixes are already live — watch further walks, do not start another routing pass. (3) **Authorized home KO continues** (27886, was 18716). Boost still waits for stor ≥20k — do not loosen the skip, do not fire boosts on a 150 t touch. Keep letting reactions run whenever stor is over 15k. Do not open industry / market / W47 labs / new remotes / T3 (**no re-ask**).
- **Plan check:** plan holds (energy gates unchanged; the 150 t 20k touch is not a latch; the W47 post-fight ~22k recovery and expired threat window are designed Phase0 recovery, not a phase exit; KO 27886 is the authorized stockpile growing, not a new widget or a boost/industry turn-on). No softCap / industry / market re-ask. No war_* restart.

"""

RCL7_BLOCK = """## 2026-11-19 20:2x Asia/Hong_Kong — 12h strategic review (plan holds; home 77.27% ~6.25d, 20k only 20829/150t, W47 post-fight ~22k, KO 27886, gates held, docs only)

**Board.** Home 77.27% stor avg 16.34k max 20829 min 12757 (21.61 e/t → RCL8 ≈6.25 d; 12.75% of the sampled window under 15k, was 15.73%; live tip 15530 why=ok nUp=2 work=28; labsN=6, factory done, home sites=0; Memory.ops.labs={W46N8:'KO'} why=active, KO stockpile **27886** — 27236 stor + 650 in output lab 34,22). W47 47.44% stor avg 25.99k max 35585 min 18926 (19.46 e/t → RCL8 ≈16.04 d, was 19.33 / 17.07 d; 0% <15k, 98.4% ≥20k, 64.0% ≥25k, 14.1% ≥30k, 0% ≥40k; keep=2, siteRem=0, softCap2 off, live 22025 bankWhy=ready, softLeft=2975 hysteresis). Remotes ALL SAFE (res 2233/2101/2430). CPU avg 17.87 p95 21.36 max 28.94, bucket min 9920, n_cpu≥40=0. LIVE **2b5398f7** already live (@84345299 / 02:28:52). The 08:2x morning review failed (box outage 05:33–09:23).

**Finding.** The sticky 20k/300t 3rd-upgrader gate still did its job — it came closer than in recent reviews, but not close enough. This window has **one 150 t ≥20k stretch** (max **20829** @11:28), after last evening's zero samples / max 19772. Live tip is above the 15k floor with nUp=2 why=ok — do not change the 15k floor; upExtra=0. Under-15k share eased 15.73%→12.75%; longest stretch **130 t** (16:27–16:37, min **14077**) after the 16:08 W45N7 Invader. Home 3h 22.57 e/t is a strong afternoon, not a 3rd. Home crossed **77.3%**. W47 stayed a keep=2 20 e/t room (designed 66.5% of the 30.08 ceiling, so formal short-soft ALERTs at that rate are expected; 12h 19.46, 3h 19.75, exact2h 19.96=66.3%). **No 40k camp this window** (0% ≥40k, max 35585 @17:13; 24h max 36249 @00:06; longest ≥30k 840 t); all-time high remains 11-17 morning's 44416 / 341 t; closest clean camp remains 11-17 evening's 470 t / peak 43041. After the 17:32 W47N7 Invader the room dipped (min 21320 @18:20) and is live **22025**; the threat window expired ~19:51; softCap2 is OFF; sealPark is the ≥25k rule; softLeft=2975 is designed hysteresis after a <22k dip — do not unpark ceil/seal. FORMAL W47 upgrade alert CLEARED at 19:22 after 21 consecutive duals (short was 26 e/t from an idle builder, not a standing third); the 20:27 tip is exact2h-under again with last20–300 designed 20 e/t=66.5% soft — the 20:23 hourly will settle first dual vs hold; strategy is unchanged either way. Standing defence handled every wave (W45N7, W47N7); all remotes SAFE at the tip, defenders already aged out. Home KO is the already-authorized lean stockpile: **18716→27886**; 15k reaction floor is not pausing at the tip (actOk=1); 20k boost skip held — no kite boost on a 150 t touch. Already-live 2b5398f7 / 6d153087 are visible (tip fillers parked on 34,32 and POST2 35,31 with 1200e). W47 rampart min 300001, wall min 1000001 — do not start a fortify push mid 40k wait / mid ~22k stor. Known sealPark nUp≥3 handoff unlatch stays deferred.

**Community.** Overmind `UpgradeSite` re-checked on master blob 2eae97b (still June 2019): `storageBuffer=100000` / `energyPerBodyUnit=25000` / `linksRequestBelow=200` — the **100k buffer gate is unchanged** (last evening's recap mistyped energyPerBodyUnit as 10000). Upgraders spawn only above that buffer (or ticksToDowngrade < 500) and are not recycled for banking; routine fortify waits for 500k energy and targets 1M hits at RCL7. TooAngel / The International were not re-cloned; the 18 Nov morning check still applies (TooAngel sizes one upgrader to about half the store and treats 100k as healthy; International will not spawn surplus upgraders below ~94–102k). Our 15k / 20k / 40k floors, and running 14W or 2×14W on them, are more aggressive than all three; the 20k/300t third and 40k/500t keep=3 are likewise more aggressive. That comparison argues for **holding** the existing gates, not adding a third and not opening industry (live energy 15.5k / 22k, window max 21k / 36k ≪ 100k). Boost-skip under 20k is slightly conservative vs official XGH2O (+100% upgrade, no extra upgrade energy) but consistent with a tight store. Holding off industry / market / T3 / a new remote matches these codebases and shard3 CPU caution (12h avg 17.87 / 20). Lean home KO has grown its T1 stockpile (27886) and that still is not an Overmind-style ~100k industry turn-on. Do not restart war_cmd.

**Moves:** (1) keep the 20k gate — home stays the RCL8 lead (~6.25 d at this 21.61 e/t pace) and has crossed 77.3%; do not change the 15k floor; funnel still coded only at home ≥~90%; (2) W47 stay keep=2 until the 40k latch; do not add a third; the post-fight ~22k recovery is not a latch; do not unpark ceil/seal; the filler-park / POST2 fixes are already live — watch further walks; (3) authorized home KO continues (27886); boost still waits for stor ≥20k; defer industry / market / W47 labs / new remotes / T3 (**no re-ask**).

**Shipped:** Nothing (docs + ROADMAP only). SoftCap / leanBank / sealMinE / HUB_LINK / industry / market / war_* / listener / 15k / 20k boost skip / W47 keep=2 **unchanged**. No game deploy this review. (Already-live this window: **2b5398f7** @84345299 / 02:28:52; **6d153087** @84340798 / 20:35 last evening.)

"""

STRATEGY_NEW = """## Current state (2026-11-19 ~20:2x Asia/Hong_Kong · 12h review)

| Room | Notes |
|------|-------|
| W46N8 (home) | **RCL7** 77.27% (8.449M/10.935M); +183k/sampled 11.07h ≈ 21.61 e/t → RCL8 ≈ **6.25 days** at this pace (was 21.57 / 7.17 d; tick_s 4.673→4.694 slightly slower, calendar still tightened); stor avg 16.34k max **20829** min 12757, **12.75% under 15k** (was 15.73%); live tip 15530 why=ok nUp=2 work=28; labsN=6, factory done, sites=0; **KO ON** (authorized; stockpile **27886** already ≥900 — 27236 stor + 650 lab; 15k reaction floor not pausing / 20k boost skip held); LIVE **2b5398f7** (@84345299 / 02:28:52 HKT, already-live civilian-hold fix) |
| W47N8 | **RCL7** 47.44% (5.187M); +165k ≈ **19.46 e/t** → RCL8 ≈ **16.04 days** (was 19.33 / 17.07 d); stor avg 25.99k max **35585** min 18926 (0% <15k, 98.4% ≥20k, 64.0% ≥25k, 14.1% ≥30k, 0% ≥40k); live stor 22025 keep=2 phase=ready siteRem=0 leanBank0 softCap2 **off** (threat expired ~19:51; sealPark because stor <25k; softLeft=2975 hysteresis); two 10W upgraders; **no 40k camp this window**, latch not armed |

**20:2x scorecard:** Phase0 home floor **improved** (12.75% of the sampled window under 15k, was 15.73%; longest post-Invader dip 130 t / min 14.1k, recovered to 15.5k at the tip with nUp=2; 20k gate never latched — closest camp **20829 / 150 t**, still short of 300 t). W47 threat leftover **expired** ~19:51 and the room recovered from the combat dip to ~22k (live 22025, softCap2 off, bankWhy=ready, sealPark because stor <25k); energy-side is above 25k for 64.0% of samples and above 30k for 14.1% (was 62.2% / 7.7%); **no 40k camp** (0% ≥40k, max 35585 @17:13; 24h max 36249 @00:06) is a mid-wait band, not a latch; the all-time high remains 11-17 morning's 44416; live 22025, upLatched=0 — do not unpark ceil/seal. 40k latch **waiting**. Phase1 blocked (mid 40k wait). Phase2 home is still the lead and has crossed 77.3% (~6.25 d, was 7.17 d; 3h 22.57). W47 pace ~19.46 e/t / ~16.04 d. Phase3 lean KO is **on** and the stockpile has grown **18716→27886**; boost still waits for stor ≥20k; full industry / XGH2O / market stay deferred (energy 15.5k / 22k live, window max 21k / 36k ≪ 100k). Verdict: `waiting on ticks` (20k gate + W47 40k latch held; a 150 t 20k touch and a post-fight ~22k recovery are not phase exits; KO 27886 is stockpile growth, not a boost/industry turn-on; already-live 2b5398f7 / 6d153087 tip fillers were parked on 34,32 and POST2 35,31; no new game code this review). The 08:2x morning review failed during a 05:33–09:23 box outage; the 24h recap since last evening does not change the plan.

### Previous (2026-11-18 ~20:2x Asia/Hong_Kong · 12h review)

"""

MODEL_BLOCK = """## 2026-11-19 20:2x — 12h actuals (plan holds)

Sampled 12h window t84350530→84359020 (8490 t, tick_s 4.694, coverage 447/850 ≈ 52.6%; morning 08:2x review failed during a 05:33–09:23 box hole): home upgrade **21.61** e/t (73.84% last evening → 77.27%, +183k in this sampled window; RCL8 ≈ **6.25 d**, was 7.17 d). 2×14W remain energy-bound (live why=ok, exact2h 24.07/26=92.6% ABOVE, 3h 22.57 / 6h 20.96). Stor avg 16.34k max **20829** min **12757**; **12.75% under 15k** (was 15.73%); **one 150 t ≥20k stretch**, 20k/300t gate held. Longest under-15k 130 t after the 16:08 W45N7 Invader — do not change the 15k floor. 24h ledger net sp:upgrader **1.63**, under the 5 e/t waste gate. See `docs/RCL7.md` 20:2x.

"""

MODEL_W47_BLOCK = """## 2026-11-19 20:2x — keep=2, no 40k camp this window, post-fight ~22k, threat expired, tip softCap2 off (plan holds)

Sampled 12h window: W47 upgrade **19.46** e/t vs ideal ~30 (44.18% last evening → 47.44%, +165k). Forward RCL8 ≈ **16.04 d** (was 19.33 / 17.07 d; pace 19.33→19.46, tick_s 4.673→4.694 slightly slower, calendar still tightened on the faster percent). Stor avg 25.99k max **35585** @17:13 min **18926** @10:30; **0% under 15k, 98.4% ≥20k, 64.0% ≥25k, 14.1% ≥30k, 0% ≥40k**. **No 40k camp this window**; 24h max since last evening is **36249 @00:06**; all-time high remains 11-17 morning's **44416 / 341 t**; closest clean camp remains 11-17 evening's 470 t / peak 43041; longest ≥30k this window **840 t** (16:33–17:40, peak 35585) then the 17:32 fight. After the 17:32 W47N7 Invader the room dipped under 22k (min 21320 @18:20) and is live **22025**. Live keep=2 phase=ready leanBank=0 softE=0 softCap2 **OFF** threatSoft=0 sealPark=1 bankWhy=ready softLeft=2975, upLatched=0, upgCeil=2, hubLink ready. Threat window expired ~19:51; sealPark is the ≥25k rule; softLeft=2975 is designed hysteresis after the <22k dip — do not unpark ceil/seal, do not add a third. keep=2 designed 20 e/t = 66.5% of the 30.08 ceiling; 3h pace 19.75 e/t / exact2h 19.96=66.3%, so short-soft upgrade ALERTs at the designed rate are expected. Formal W47 alert CLEARED at 19:22 after 21 duals (idle builder helping); the 20:27 tip is exact2h-under again with last20–300 designed 20 e/t=66.5% soft — hourly will settle first dual vs hold. Already-live 2b5398f7 / 6d153087 are visible (tip fillers parked on 34,32 and POST2 35,31 with 1200e). W47 rampart min 300001, wall min 1000001 — do not start a fortify push mid 40k wait / mid ~22k stor. **contMinPct52 roadCrit0**. See `docs/RCL7.md` 20:2x.

"""

MINERAL_BLOCK = """## 2026-11-19 20:2x — home KO stockpile grew 18716→27886; boost still waits on the 20k energy skip; industry / market stay off

12h review (morning 08:2x run failed during a box outage, so this is the first written pass since last evening): Misaki-authorized `Memory.ops.labs={W46N8:'KO'}` stayed ON all window (**no re-ask**). The T1 stockpile continued to grow: output lab 34,22 has **650 KO**, storage **27236 KO**, terminal 0, **total 27886** (was 18716 last evening). Inputs 33,21/33,22 1650 K / 1650 O. At the tip `labReady` why=active actOk=1 homeStor=15630 — reactions are running because home stor is over the 15k floor (~15.5k), which is the designed resume, not a new gate. The 20k boost skip held: no kite boost, even though KO ≫ 900, because this window's only ≥20k stretch was **150 t** (max 20829). W47 labs remain empty shells (w8min why=ready is mineral-pipeline readiness, not a labs turn-on), RCL6_LABS / RCL7_INDUSTRY / market stay OFF. This is still a lean authorized T1 stockpile, not an Overmind-style ~100k industry turn-on (live home ~15.5k / W47 ~22k ≪ 100k; TooAngel / International also treat ~100k as the healthy / reaction band). Next: keep letting KO run whenever stor is over 15k; boost still waits for stor ≥20k. Do not loosen the skip, do not open factory / XGH2O / T3 / market / W47 labs. Detail: `docs/RCL7.md` 20:2x.

"""


def insert_after(path: Path, marker: str, block: str, unique: str):
    text = path.read_text()
    if unique in text:
        raise SystemExit(f"{path.name} already has {unique}")
    if marker not in text:
        raise SystemExit(f"{path.name} marker missing")
    path.write_text(text.replace(marker, marker + block, 1))
    print(f"patched {path.name}")


# ROADMAP: after the Safe mode paragraph (ends with alert Misaki.\n\n)
roadmap = ROOT / "ROADMAP.md"
rt = roadmap.read_text()
mark = "**Safe mode: NEVER auto-activate** — alert Misaki.\n\n"
if "2026-11-19 20:2x Asia/Hong_Kong 12h strategic review: plan holds; home 77.3%" in rt:
    raise SystemExit("ROADMAP already has 20:2x")
if mark not in rt:
    raise SystemExit("ROADMAP marker missing")
roadmap.write_text(rt.replace(mark, mark + ROADMAP_BLOCK, 1))
print("patched ROADMAP")

# RCL7: after the title line following the HTML comment
rcl7 = ROOT / "docs/RCL7.md"
r7 = rcl7.read_text()
mark7 = "# Home W46N8 RCL7 readiness (strategy review 2026-10-19 18:4x UTC+8)\n\n"
if "2026-11-19 20:2x Asia/Hong_Kong — 12h strategic review (plan holds; home 77.27%" in r7:
    raise SystemExit("RCL7 already has 20:2x")
if mark7 not in r7:
    raise SystemExit("RCL7 marker missing")
rcl7.write_text(r7.replace(mark7, mark7 + RCL7_BLOCK, 1))
print("patched RCL7")

# STRATEGY: replace current-state heading
st = ROOT / "docs/STRATEGY.md"
s = st.read_text()
old_h = "## Current state (2026-11-18 ~20:2x Asia/Hong_Kong · 12h review)\n"
if "## Current state (2026-11-19 ~20:2x Asia/Hong_Kong · 12h review)" in s:
    raise SystemExit("STRATEGY already has 20:2x")
if old_h not in s:
    raise SystemExit("STRATEGY old heading missing")
st.write_text(s.replace(old_h, STRATEGY_NEW, 1))
print("patched STRATEGY")

# MODEL: before the previous actuals heading
insert_after(
    ROOT / "docs/MODEL.md",
    "## Actuals (DB, default 6 h)\nupgrade rate (room_stats progress), pickups per source (positive store deltas within 2 tiles of the source, normalised by tick coverage — a lower bound), deliveries (hub vs controller container), per-role idle/repaths/CPU (creep_cpu), planned vs actual path length (path_arrivals), hauler cycle median, share of hauling traffic on ideal-route tiles ± 1.\n\n",
    MODEL_BLOCK,
    "## 2026-11-19 20:2x — 12h actuals (plan holds)",
)

# MODEL_W47: after the reserve7 paragraph, before previous heading
mw = ROOT / "docs/MODEL_W47N8.md"
mt = mw.read_text()
markw = "reserve7 (2 CLAIM) is spawned and paid by home.\n\n"
if "2026-11-19 20:2x — keep=2, no 40k camp this window, post-fight ~22k" in mt:
    raise SystemExit("MODEL_W47 already has 20:2x")
if markw not in mt:
    raise SystemExit("MODEL_W47 marker missing")
mw.write_text(mt.replace(markw, markw + MODEL_W47_BLOCK, 1))
print("patched MODEL_W47N8")

# MINERAL: after the intro paragraphs, before previous heading
mn = ROOT / "docs/MINERAL_DEFENSE_ROADMAP.md"
mtxt = mn.read_text()
# insert after the long intro, before the 11-18 20:2x heading
markm = "## 2026-11-18 20:2x — home KO stockpile grew 14071→18716; boost still waits on the 20k energy skip; industry / market stay off\n"
if "2026-11-19 20:2x — home KO stockpile grew 18716→27886" in mtxt:
    raise SystemExit("MINERAL already has 20:2x")
if markm not in mtxt:
    raise SystemExit("MINERAL marker missing")
mn.write_text(mtxt.replace(markm, MINERAL_BLOCK + markm, 1))
print("patched MINERAL_DEFENSE_ROADMAP")
