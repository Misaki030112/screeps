#!/usr/bin/env python3
from pathlib import Path
ROOT = Path("/workspace/screeps")

ROADMAP_BLOCK = """## 2026-11-18 20:2x Asia/Hong_Kong 12h strategic review: plan holds; home 73.8% ~7.17 d, still no 20k touch, W47 leftover expired back to 25k, KO 18716, 20k/40k gates held (docs only)

- **Chose:** Full-board 12h review (~12h after 08:2x). SoftCap / industry / market widgets outstanding — **never re-ask**. Home KO is already authorized (`Memory.ops.labs={W46N8:'KO'}`) and is no longer a widget. War_* stay stopped (`aborted_by_misaki`). Question: after home accelerated to 21.57 e/t and crossed 73.8%, a W47 leftover that expired and banked back to 25k with still no 40k camp, a KO stockpile that has grown 14071→18716, and the already-live filler-park fix, does the peacetime energy order still hold, and is there a small safe ship?
- **Findings:** Live t84340700–717 LIVE **289a7f06** (deploy@84334122 / 11:55:12 HKT, W47 filler parks on 34,32 when full; occupied-hub bypass kept; already-live this window, not this review; 8daf0494 held from the open until then). Window t84331400→84340690 (9290 t, tick_s 4.673, ~12.06 h, coverage 674/930 ≈ 72.5% — better than this morning's 58.7% after 19 box pauses totalling 11280 s). Home RCL7 **73.84%** (8.074M; +200k in 12h ≈ **21.57 e/t**, was 20.66; RCL8 ≈ **7.17 days** at this window's pace — calendar tightened on both a faster pace and tick_s 4.746→4.673), stor avg 16.54k max **19772** min **11500**, **15.73% of samples under the 15k floor** (was 19.25%); live tip **~18.9–19.0k** why=ok nUp=2 work=28, above the floor, energy-bound, upExtra=0. The 20k/300t latch never armed — **0 samples ≥20k** this window (max 19772 @20:14–20:22), after this morning's max 19077 and last evening's only touch 20244 / 20 t. Under-15k share eased 19.25%→15.73%; longest stretch **401 t** (14:05–14:36, min **11500**) after the 13:48 W45N7 Invader — do not change the 15k floor. Home 3h **20.23** e/t / 6h 20.68 / exact2h 19.28/26=74.1% ABOVE is a solid afternoon, not a 3rd. W47 **44.18%** (4.831M; +180k ≈ **19.33 e/t**, was 20.00; RCL8 ≈ **17.07 days**). Stor avg 24.75k max **34155** @15:44 min **15078** @17:22, **0% under 15k, 80.7% ≥20k, 62.2% ≥25k, 7.7% ≥30k, 0% ≥40k** (was 99.3% / 88.8% / 35.5% / 0%). **No 40k camp this window**; all-time high remains yesterday morning's **44416 / 341 t**; closest clean camp remains last evening's 470 t / peak 43041; longest ≥30k this window only 211 t. This morning's first <22k ARM leftover expired; after the 16:48 W47N7 Invader the room spent several <22k stretches (longest 330 t at 19:18–19:44, min 15078) and **banked back above 25k by 20:00**. Live stor **25271**, **upLatched=0**, keep=2 phase=ready siteRem=0 leanBank=0 softE=0 softCap2 **OFF** threatSoft=0 sealPark=1 bankWhy=ready softLeft=0 upgCeil=2 hubLink ready. Designed Phase0 recovery, not a phase exit — do not unpark ceil/seal, do not add a third. Remotes **ALL SAFE** at the tip (W45N8/W45N7/W47N7 res 2385/1927/2579, cores 0 host 0). Standing ops this window, not a phase change: W45N7 solo Invader 13:48–14:05 cleared SAFE why=killed (225 t; an alert_escalated fired after the clear — observability only), W47N7 16:48 / 17:01–17:10 cleared SAFE why=killed (281 t), plus a brief owned-room hostile in W47N8 @11:32. FORMAL W47 upgrade alert **FIRED at 19:20** (second consecutive dual after 18:26). At the 20:21 tip exact2h 18.52/30.08=61.6% is still under 70%; last20–300 20.00–20.57 e/t=66.5–68.4% are soft, but last500 22.10=73.5% is not soft — the 20:17 hourly patrol will settle hold vs non-confirm. Either way, keep=2's designed 20 e/t is 66.5% of the 30.08 ceiling, so formal short-soft ALERTs at the designed rate remain expected, not a reason to add a third. Home exact2h 19.28/26=74.1% ABOVE. CPU 12h avg **17.24** p95 20.54 max 33.16, bucket min 9947, n_cpu≥40=0 (was 17.82). Home KO is **ON** (authorized) and the stockpile grew **14071→18716** (output lab 34,22 **680 KO**, storage **18036 KO**, terminal 0); inputs 33,21/33,22 1220 K / 1220 O. At the tip `labReady` why=active actOk=1 homeStor≈18972 — the 15k reaction floor is **not** pausing. The 20k boost skip held — no kite boost, even though KO ≫ 900, because home never touched 20k. Industry / market / W47 labs stay OFF (w8min why=ready, not a labs turn-on). Home walls/ramparts still ≥300k; W47 rampart min **300001** @33,35 recovered from this morning's 295301 — do not start a fortify push mid 40k wait / mid ~19–25k stor. At the tip, filler 84339665 was parked on 34,32 with 1200e — the already-live 289a7f06 branch is visible; observe further walks, do not start another routing pass. Ledger clean 12h snap t84331436→84340747: home net sp:upgrader **1.66** (under the 5 e/t waste gate); W47 up 19.34 matches room_stats 19.335. Community: not re-cloned this run; this morning's Overmind `UpgradeSite` / TooAngel (17 Nov 2026) / The International comparison still applies — energyBuffer 100k, TooAngel sizes one upgrader to about half the store and treats 100k as healthy, International will not spawn surplus upgraders below ~94–102k. This window's floors (home max 19772, W47 max 34155, live ~19k / 25k) remain far below that band, so the existing 15k / 20k / 40k gates should be **held**, not loosened, and industry should stay off. CPU 17.24 / 20 still argues against a new remote. KO already running matches "don't put off minerals." Sites 0; labs/factory/terminal 6+1+1 both rooms. Memory.cmd.on=1 at=84224348 is the same stale empty cmd. lastErrorTick 83976900 unchanged. W47 model src_A 1h 2.83 / 2h 1.52 vs ideal 9.6 (stand-A container 26,11 empty at the 20:21 model tip) is a watch item, not a ship — 12h upgrade is still 19.33 and storage recovered.
- **Shipped:** Nothing (docs + ROADMAP only). SoftCap / leanBank / sealMinE / HUB_LINK / industry / market / war_* / listener / 15k floor / 20k boost skip / W47 keep=2 unchanged. No game deploy this review. (Already-live this window, not this review: **289a7f06** @84334122 / 11:55:12, filler parks on 34,32 when full; tip filler 84339665 was on that post.)
- **Reprioritise (next 1–3):** (1) **Keep the 20k gate** — 2×14W remain energy-bound; a 3rd still should not arm until a real 20k surplus holds 300 t (this window never touched 20k, max 19772). Do not change the 15k floor. Home is still the RCL8 lead (~7.17 d at this 21.57 e/t pace; 3h 20.23) and has crossed 73.8%. home→W47 terminal funnel still coded only at home ≥~90%. (2) W47 stays **keep=2 until the 40k/500 t latch**. This window had **no 40k camp** (0% ≥40k, max 34155) and a post-Invader <22k dip that then banked back to 25k; the all-time high remains yesterday morning's 44416 / 341 t, and the closest clean camp remains last evening's 470 t. The morning leftover has expired (live 25271, softCap2 off, bankWhy=ready) — do not add a third; do not unpark ceil/seal mid 40k wait; do not lift keep because a formal short-soft is firing at the designed 20 e/t rate. The filler-park fix is already live — watch further walks, do not start another routing pass. (3) **Authorized home KO continues** (18716, was 14071). Boost still waits for stor ≥20k — do not loosen the skip, do not fire boosts on a sub-20k store. Keep letting reactions run whenever stor is over 15k. Do not open industry / market / W47 labs / new remotes / T3 (**no re-ask**).
- **Plan check:** plan holds (energy gates unchanged; the W47 leftover expiry and the bank back to 25k are designed Phase0 recovery, not a phase exit; KO 18716 is the authorized stockpile growing, not a new widget or a boost/industry turn-on). No softCap / industry / market re-ask. No war_* restart.


"""

RCL7_BLOCK = """## 2026-11-18 20:2x Asia/Hong_Kong — 12h strategic review (plan holds; home 73.84% ~7.17d, still no 20k touch, W47 leftover expired back to 25k, KO 18716, gates held, docs only)

**Board.** Home 73.84% stor avg 16.54k max 19772 min 11500 (21.57 e/t → RCL8 ≈7.17 d; 15.73% of 12h under 15k, was 19.25%; live tip ~18.9–19.0k why=ok nUp=2 work=28; labsN=6, factory done, home sites=0; Memory.ops.labs={W46N8:'KO'} why=active, KO stockpile **18716** — 18036 stor + 680 in output lab 34,22). W47 44.18% stor avg 24.75k max 34155 min 15078 (19.33 e/t → RCL8 ≈17.07 d, was 20.00 / 17.26 d; 0% <15k, 80.7% ≥20k, 62.2% ≥25k, 7.7% ≥30k, 0% ≥40k; keep=2, siteRem=0, softCap2 off, live 25271 bankWhy=ready). Remotes ALL SAFE (res 2385/1927/2579). CPU avg 17.24 p95 20.54 max 33.16, bucket min 9947, n_cpu≥40=0. LIVE **289a7f06** already live (@84334122 / 11:55:12).

**Finding.** The sticky 20k/300t 3rd-upgrader gate still did its job — it never came close. This window has **zero ≥20k samples** (max **19772** @20:14–20:22), closer than this morning's 19077, still under. Live tip is above the 15k floor with nUp=2 why=ok — do not change the 15k floor; upExtra=0. Under-15k share eased 19.25%→15.73%; longest stretch **401 t** (14:05–14:36, min **11500**) after the 13:48 W45N7 Invader. Home 3h 20.23 e/t is a solid afternoon, not a 3rd. Home crossed **73.8%**. W47 stayed a keep=2 20 e/t room (designed 66.5% of the 30.08 ceiling, so formal short-soft ALERTs at that rate are expected; 12h 19.33, 3h 19.22, exact2h 18.52=61.6%). **No 40k camp this window** (0% ≥40k, max 34155 @15:44; longest ≥30k only 211 t); all-time high remains yesterday morning's 44416 / 341 t; closest clean camp remains last evening's 470 t / peak 43041. This morning's <22k leftover expired; after the 16:48 W47N7 Invader the room dipped (min 15078 @17:22) and **banked back above 25k by 20:00**. Live 25271, upLatched=0, softCap2 OFF, bankWhy=ready — designed Phase0 recovery, do not unpark ceil/seal. FORMAL W47 upgrade alert FIRED at 19:20 (second consecutive dual); the 20:21 tip is still exact2h-under, with last20–300 soft and last500 22.10=73.5% not soft — the 20:17 hourly will settle hold vs non-confirm; strategy is unchanged either way. Standing defence handled every wave (W45N7, W47N7, brief W47N8 hostiles); all remotes SAFE at the tip. An alert_escalated after the already-cleared W45N7 wave is observability only, not a live threat. Home KO is the already-authorized lean stockpile: **14071→18716**; 15k reaction floor is not pausing at the tip (actOk=1); 20k boost skip held — no kite boost. Already-live 289a7f06 is visible (tip filler 84339665 parked on 34,32 with 1200e). W47 rampart min 300001 recovered from this morning's 295301 — do not start a fortify push mid 40k wait. Known sealPark nUp≥3 handoff unlatch stays deferred.

**Community.** Not re-cloned this run. This morning's re-check still applies: Overmind `UpgradeSite` (`src/hiveClusters/upgradeSite.ts` on master, last commit still June 2019) still `energyBuffer=100000` / `energyPerBodyUnit=10000` / `linksRequestBelow=200`; the **100k buffer gate is unchanged**. Upgraders spawn only above that buffer (or ticksToDowngrade < 500) and are not recycled for banking; routine fortify waits for 500k energy and targets 1M hits at RCL7. TooAngel (master, 17 Nov 2026) keeps one upgrader at almost any storage but sizes WORK so one lifetime spends about half the store (15k→5W, 20k→6W) and treats 100k as “healthy” / lab-reaction storage. The International (Main) uses an emergency minimum of ~73–80k at mid/late RCL7 and will not spawn surplus upgraders below ~94–102k. Our 15k / 20k / 40k floors, and running 14W or 2×14W on them, are more aggressive than all three; the 20k/300t third and 40k/500t keep=3 are likewise more aggressive. That comparison argues for **holding** the existing gates, not adding a third and not opening industry (live energy 19k / 25k, window max 20k / 34k ≪ 100k). Boost-skip under 20k is slightly conservative vs official XGH2O (+100% upgrade, no extra upgrade energy) but consistent with a tight store. Holding off industry / market / T3 / a new remote matches these codebases and shard3 CPU caution (12h avg 17.24 / 20). Lean home KO has grown its T1 stockpile (18716) and that still is not an Overmind-style ~100k industry turn-on. Do not restart war_cmd.

**Moves:** (1) keep the 20k gate — home stays the RCL8 lead (~7.17 d at this 21.57 e/t pace) and has crossed 73.8%; do not change the 15k floor; funnel still coded only at home ≥~90%; (2) W47 stay keep=2 until the 40k latch; do not add a third; the leftover expiry and the bank back to 25k are not a latch; do not unpark ceil/seal; the filler-park fix is already live — watch further walks; (3) authorized home KO continues (18716); boost still waits for stor ≥20k; defer industry / market / W47 labs / new remotes / T3 (**no re-ask**).

**Shipped:** Nothing (docs + ROADMAP only). SoftCap / leanBank / sealMinE / HUB_LINK / industry / market / war_* / listener / 15k / 20k boost skip / W47 keep=2 **unchanged**. No game deploy this review. (Already-live this window: **289a7f06** @84334122 / 11:55:12.)

"""

STRATEGY_NEW = """## Current state (2026-11-18 ~20:2x Asia/Hong_Kong · 12h review)

| Room | Notes |
|------|-------|
| W46N8 (home) | **RCL7** 73.84% (8.074M/10.935M); +200k/12h ≈ 21.57 e/t → RCL8 ≈ **7.17 days** at this pace (was 20.66 / 8.14 d; tick_s 4.746→4.673 slightly faster); stor avg 16.54k max **19772** min 11500, **15.73% under 15k** (was 19.25%); live tip ~18.9–19.0k why=ok nUp=2 work=28; labsN=6, factory done, sites=0; **KO ON** (authorized; stockpile **18716** already ≥900 — 18036 stor + 680 lab; 15k reaction floor not pausing / 20k boost skip held); LIVE **289a7f06** (@84334122 / 11:55:12 HKT, already-live filler-park fix) |
| W47N8 | **RCL7** 44.18% (4.831M); +180k/12h ≈ **19.33 e/t** → RCL8 ≈ **17.07 days** (was 20.00 / 17.26 d); stor avg 24.75k max **34155** min 15078 (0% <15k, 80.7% ≥20k, 62.2% ≥25k, 7.7% ≥30k, 0% ≥40k); live stor 25271 keep=2 phase=ready siteRem=0 leanBank0 softCap2 **off** (morning leftover expired; banked back above 25k); two 10W upgraders; **no 40k camp this window**, latch not armed |

**20:2x scorecard:** Phase0 home floor **improved** (15.73% of 12h under 15k, was 19.25%; a deeper post-Invader dip min 11.5k / 401 t recovered to ~19k at the tip with nUp=2; 20k gate never latched — **zero ≥20k samples**, max 19772). W47 leftover **expired** and the room banked back to 25k (live 25271, softCap2 off, bankWhy=ready); energy-side is above 25k for 62.2% of samples and above 30k for 7.7% (was 88.8% / 35.5%); **no 40k camp** (0% ≥40k, max 34155 @15:44) is a mid-wait band, not a latch; the all-time high remains yesterday morning's 44416; live 25271, upLatched=0 — do not unpark ceil/seal. 40k latch **waiting**. Phase1 blocked (mid 40k wait). Phase2 home is still the lead and has crossed 73.8% (~7.17 d, was 8.14 d; 3h 20.23). W47 pace ~19.33 e/t / ~17.07 d. Phase3 lean KO is **on** and the stockpile has grown **14071→18716**; boost still waits for stor ≥20k; full industry / XGH2O / market stay deferred (energy 19k / 25k live, window max 20k / 34k ≪ 100k). Verdict: `waiting on ticks` (20k gate + W47 40k latch held; a 20k miss and a leftover expiry back to 25k are not phase exits; KO 18716 is stockpile growth, not a boost/industry turn-on; already-live 289a7f06 tip filler was parked on 34,32; no new game code this review).

### Previous (2026-11-18 ~08:2x Asia/Hong_Kong · 12h review)

"""

MODEL_BLOCK = """## 2026-11-18 20:2x — 12h actuals (plan holds)

12h window t84331400→84340690: home upgrade **21.57** e/t (72.01%→73.84%, +200k; RCL8 ≈ **7.17 d**, was 8.14 d). 2×14W remain energy-bound (live why=ok, exact2h 19.28/26=74.1% ABOVE, 3h 20.23 / 6h 20.68). Stor avg 16.54k max **19772** min **11500**; **15.73% under 15k** (was 19.25%); **0 samples ≥20k**, 20k/300t gate held. Longest under-15k 401 t after the 13:48 W45N7 Invader — do not change the 15k floor. Ledger net sp:upgrader **1.66**, under the 5 e/t waste gate. See `docs/RCL7.md` 20:2x.

"""

MODEL_W47_BLOCK = """## 2026-11-18 20:2x — keep=2, no 40k camp this window, morning leftover expired, tip ~25k bankWhy=ready (plan holds)

12h window: W47 upgrade **19.33** e/t vs ideal ~30 (42.54%→44.18%, +180k). Forward RCL8 ≈ **17.07 d** (was 20.00 / 17.26 d; pace 20.00→19.33, tick_s 4.746→4.673 slightly faster so the calendar still tightened a little). Stor avg 24.75k max **34155** @15:44 min **15078** @17:22; **0% under 15k, 80.7% ≥20k, 62.2% ≥25k, 7.7% ≥30k, 0% ≥40k**. **No 40k camp this window**; all-time high remains yesterday morning's **44416 / 341 t**; closest clean camp remains last evening's 470 t / peak 43041; longest ≥30k this window only 211 t. This morning's <22k leftover expired; after the 16:48 W47N7 Invader the room dipped under 22k (min 15078) and **banked back above 25k by 20:00**. Live stor **25271**, keep=2 phase=ready leanBank=0 softE=0 softCap2 **OFF** threatSoft=0 sealPark=1 bankWhy=ready softLeft=0, upLatched=0, upgCeil=2, hubLink ready. Designed Phase0 recovery — do not unpark ceil/seal, do not add a third. keep=2 designed 20 e/t = 66.5% of the 30.08 ceiling; 3h pace 19.22 e/t / exact2h 18.52=61.6%, so short-soft upgrade ALERTs at the designed rate are expected. Formal W47 alert FIRED at 19:20; the 20:21 tip is still exact2h-under, with last500 22.10=73.5% not soft — hourly will settle hold vs non-confirm. Already-live 289a7f06 is visible (tip filler parked on 34,32 with 1200e). W47 rampart min 300001 recovered from this morning's 295301 — do not start a fortify push mid 40k wait. Model src_A 1h 2.83 / 2h 1.52 vs ideal 9.6 (stand-A container 26,11 empty at the 20:21 model tip) is a watch item, not a ship. **contMinPct50 roadCrit0**. See `docs/RCL7.md` 20:2x.

"""

MINERAL_BLOCK = """## 2026-11-18 20:2x — home KO stockpile grew 14071→18716; boost still waits on the 20k energy skip; industry / market stay off

12h review: Misaki-authorized `Memory.ops.labs={W46N8:'KO'}` stayed ON all window (**no re-ask**). The T1 stockpile continued to grow: output lab 34,22 has **680 KO**, storage **18036 KO**, terminal 0, **total 18716** (was 14071 this morning). Inputs 33,21/33,22 1220 K / 1220 O. At the tip `labReady` why=active actOk=1 homeStor≈18972 — reactions are running because home stor is over the 15k floor (~18.9–19.0k), which is the designed resume, not a new gate. The 20k boost skip held: no kite boost, even though KO ≫ 900, because this window had **zero ≥20k samples** (max 19772). W47 labs remain empty shells (w8min why=ready is mineral-pipeline readiness, not a labs turn-on), RCL6_LABS / RCL7_INDUSTRY / market stay OFF. This is still a lean authorized T1 stockpile, not an Overmind-style ~100k industry turn-on (live home ~19k / W47 ~25k ≪ 100k; TooAngel / International also treat ~100k as the healthy / reaction band). Next: keep letting KO run whenever stor is over 15k; boost still waits for stor ≥20k. Do not loosen the skip, do not open factory / XGH2O / T3 / market / W47 labs. Detail: `docs/RCL7.md` 20:2x.

"""

def insert_after(path: Path, marker: str, block: str, unique: str):
    text = path.read_text()
    if unique in text:
        raise SystemExit(f"already patched: {path}")
    i = text.find(marker)
    if i < 0:
        raise SystemExit(f"marker not found in {path}: {marker[:80]!r}")
    i = i + len(marker)
    path.write_text(text[:i] + block + text[i:])
    print(f"patched {path} +{block.count(chr(10))} lines")

# ROADMAP: after the Safe mode paragraph (ends with alert Misaki.\n\n)
roadmap = ROOT / "ROADMAP.md"
rt = roadmap.read_text()
mark = "**Safe mode: NEVER auto-activate** — alert Misaki.\n\n"
if "2026-11-18 20:2x Asia/Hong_Kong 12h strategic review" in rt:
    raise SystemExit("ROADMAP already has 20:2x")
if mark not in rt:
    raise SystemExit("ROADMAP marker missing")
roadmap.write_text(rt.replace(mark, mark + ROADMAP_BLOCK, 1))
print("patched ROADMAP")

# RCL7: after the title line following the HTML comment
rcl7 = ROOT / "docs/RCL7.md"
r7 = rcl7.read_text()
mark7 = "# Home W46N8 RCL7 readiness (strategy review 2026-10-19 18:4x UTC+8)\n\n"
if "2026-11-18 20:2x Asia/Hong_Kong — 12h strategic review (plan holds; home 73.84%" in r7:
    raise SystemExit("RCL7 already has 20:2x")
if mark7 not in r7:
    raise SystemExit("RCL7 marker missing")
rcl7.write_text(r7.replace(mark7, mark7 + RCL7_BLOCK, 1))
print("patched RCL7")

# STRATEGY: replace current-state heading
st = ROOT / "docs/STRATEGY.md"
s = st.read_text()
old_h = "## Current state (2026-11-18 ~08:2x Asia/Hong_Kong · 12h review)\n"
if "## Current state (2026-11-18 ~20:2x Asia/Hong_Kong · 12h review)" in s:
    raise SystemExit("STRATEGY already has 20:2x")
if old_h not in s:
    raise SystemExit("STRATEGY old heading missing")
st.write_text(s.replace(old_h, STRATEGY_NEW, 1))
print("patched STRATEGY")

# MODEL: before the 08:2x actuals heading
insert_after(
    ROOT / "docs/MODEL.md",
    "## Actuals (DB, default 6 h)\nupgrade rate (room_stats progress), pickups per source (positive store deltas within 2 tiles of the source, normalised by tick coverage — a lower bound), deliveries (hub vs controller container), per-role idle/repaths/CPU (creep_cpu), planned vs actual path length (path_arrivals), hauler cycle median, share of hauling traffic on ideal-route tiles ± 1.\n\n",
    MODEL_BLOCK,
    "## 2026-11-18 20:2x — 12h actuals (plan holds)",
)

# MODEL_W47: after the reserve7 paragraph, before 08:2x heading
mw = ROOT / "docs/MODEL_W47N8.md"
mt = mw.read_text()
markw = "reserve7 (2 CLAIM) is spawned and paid by home.\n\n"
if "2026-11-18 20:2x — keep=2, no 40k camp this window, morning leftover expired" in mt:
    raise SystemExit("MODEL_W47 already has 20:2x")
if markw not in mt:
    raise SystemExit("MODEL_W47 marker missing")
mw.write_text(mt.replace(markw, markw + MODEL_W47_BLOCK, 1))
print("patched MODEL_W47")

# MINERAL: before the 08:2x heading (after the 11:4x intro paragraphs)
mn = ROOT / "docs/MINERAL_DEFENSE_ROADMAP.md"
mnt = mn.read_text()
markm = "## 2026-11-18 08:2x — home KO stockpile grew 9516→14071; boost still waits on the 20k energy skip; industry / market stay off\n"
if "2026-11-18 20:2x — home KO stockpile grew 14071→18716" in mnt:
    raise SystemExit("MINERAL already has 20:2x")
if markm not in mnt:
    raise SystemExit("MINERAL marker missing")
mn.write_text(mnt.replace(markm, MINERAL_BLOCK + markm, 1))
print("patched MINERAL")

print("ALL OK")
