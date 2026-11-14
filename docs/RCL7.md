<!-- 2026-11-09 17:1x: Phase0 waiting on ticks; see STRATEGY Current state + ROADMAP 17:1x; 12h reviews must score T3 Phase0/1/2. -->
# Home W46N8 RCL7 readiness (strategy review 2026-10-19 18:4x UTC+8)

## 2026-11-14 08:2x Asia/Hong_Kong — 12h strategic review (plan holds; W47 sites done, upgrade resumed, softCap thrashing 25k, 20k gate held, docs only)

**Board.** Home 58.54% stor avg 14.5k max 17474 min 8532 (13.31 e/t → RCL8 ≈17.4 d; 50.2% of 12h under 15k, was 56.6%; live tip 13328–14578 why=floor_bank nUp=1 upExtra=0). W47 29.28% stor avg 10.8k max 25486 min 0 (blended 5.25 e/t; post-resume from 04:22 **16.09 e/t** → RCL8 ≈24.6 d; 69.1% <15k, 20.8% ≥20k, 3.4% ≥25k, 0% ≥40k; keep=2, siteRem=0, labsN=6, softCap2 still on). Remotes ALL SAFE (res ~2.0/2.0/2.9k, cores0 host0). CPU avg 17.39 p95 20.70 max 25.96, bucket min 9992. LIVE 4ff78b4 held (@84239549).

**Finding.** The sticky 20k/300t 3rd-upgrader gate still did its job — it never came close. Ledger 10521 t (t84244408→84254929, 12.91 h): home sp:upgrader **1.18 gross / 0.02 refund / net 1.16 e/t** (was 1.11; well under the 5 e/t waste gate). **Zero ≥20k samples** this window (max 17474 @23:26), so upExtra never latched. Under-15k share eased 56.6%→50.2% because the authorized site wave ended and home spent the night on the 15k floor (steady ~13–14 e/t, nUp=1) with only the last lab still drawing — designed floor-bank, not a gate bug. Window min **8532** @20:31 is an early-window floor dip (longest under-15k 361 t at the open); later dips were shorter. The authorized site wave is **done on W47**: sites first hit 0 at **84251780 / 04:25:03** (labsN **6**, factory done; a brief 1-site road blip 07:37–08:02 is already gone). Upgrade left the flat 3150854 at **84251750 / 04:22:50**; keep returned to 2 and phase=ready as designed (`f7328c4`). Mid-window W47 stor crashed to **0** at 23:33–00:07 while five sites were still up, then recovered and climbed to a 25k flicker (max **25486** @08:04). Longest ≥25k stretch is only **31 t** (open at tip); softLeft hit 0 at 25183 then re-armed to 267 at 24733 — designed [22k, 25k) hysteresis, **not a sticky softCap clear**, 40k latch not close. Live W47 stor 24733–25183, leanBank=0, threatSoft leftover (w8threat window from the 06:28 W47N7 core clear, expiry ~84254948 / almost the tip) holds upgCeil=2 — known class, expires on its own; remotes are SAFE. Home has **one lab site left** (34,20 29050/50000, rem ~21k, labsN=5). Do not unpark ceil/seal mid-thrash, do not enable labs, do not add rampart covers.

**Community.** Overmind `UpgradeSite` re-checked this run: blob 2eae97b still `storageBuffer=100000` / `energyPerBodyUnit=25000`; master still `energyBuffer=100000` / `energyPerBodyUnit=10000`; the **100k buffer gate is unchanged**. Upgraders spawn only above that buffer and are not recycled for banking. Our 20k/300t latch and W47 40k/500t latch (now active again now that sites are gone) are the same shape at our floors. Placing the last RCL7 lab shell is normal at this band; enabling reactions / XGH2O still waits on an Overmind-style ~100k energy cushion (live home ~13–15k / W47 ~25k ≪ 100k) even though termO 126976 termK 156748 are fat. TooAngel parks upgrade when thin, keeps logistics+repair warm. New remotes stay nod-only: CPU 12h avg 17.39 / 20 is quieter than last window but still tight. Do not restart war_cmd.

**Moves:** (1) finish the last home lab site — no new rampart covers, no labs-on; W47 shells are done and keep=2 is correct; (2) keep the 20k gate, home stays the RCL8 lead (~17.4 d at this pace, should tighten once the last lab ends and nUp=2 can stick); funnel still coded only at home ≥~90%; (3) let W47 softCap clear stick ≥25k, then the 40k latch; do not unpark ceil/seal mid-thrash. Defer labs KO / boost / industry / market / new remotes (**no re-ask**).

**Shipped:** Nothing (docs + ROADMAP only). SoftCap / leanBank / sealMinE / HUB_LINK / labs / industry / market / war_* / listener **unchanged**. No game deploy.


## 2026-11-13 20:1x Asia/Hong_Kong — 12h strategic review (plan holds; finish authorized lab/factory sites, keep=1 and 20k gate held, docs only)

**Board.** Home 57.35% stor avg 14.4k max 18333 min 7518 (13.49 e/t → RCL8 ≈17.6 d; 56.6% of 12h under 15k, was 50.7%; live tip 13082 why=floor_bank nUp=1 upExtra=0). W47 28.81% stor avg 3.3k max 8800 min 0 (0.00 e/t, progress flat 3150854 since 17:24; 100% <15k, 0% ≥20/25/40k, keep=1, W47 siteRem 123709 was 259481). Remotes ALL SAFE (W45N7 leave-alive defender on station, host 0). CPU avg 18.07 p95 20.92 max 89.10, bucket min 9891. LIVE 4ff78b4 held (@84239560).

**Finding.** The sticky 20k/300t 3rd-upgrader gate still did its job — it never came close. Ledger 11340 t (t84233068→84244408, 13.89 h): home sp:upgrader **1.37 gross / 0.26 refund / net 1.11 e/t** (was 1.08; well under the 5 e/t waste gate). **Zero ≥20k samples** this window (max 18333 @14:36), so upExtra never latched. Under-15k share ticked 50.7%→56.6% because home spent the day on the 15k floor (steady ~14 e/t, nUp=1) while two remaining lab sites plus routine respawns absorbed the surplus — designed floor-bank, not a gate bug. Window min **7518** is the start-of-window tail of this morning's post-defender dip; the bank recovered into the mid-teens and kept hugging the floor (longest under-15k streak this window 540 t at the open, then shorter 70–370 t dips). Mid-day yesterday `f7328c4` keep=1 while sites are up is held — do not revert. The authorized site wave is more than halfway done: W47 siteRem **259481→123709** (~8–9 h at measured 17.29 e/t build); lab **29,38 completed** this evening (live labs 3, factory done); remaining W47 labs 28,37 at 28529/50000, 27,40 at 3542, 28,38 still 0, plus minCont 37,44 0/5000. Home factory is done, labsN=4; two lab sites remain (33,22 9338/50000, 34,20 4303/50000, rem ~86k). Live W47 stor 5920, builders=4, upgraders=0, threatSoft off, phase=minBuild leanBank1 bankWhy=minBuild — stor 5.9k would keep softE/leanBank on anyway. roadCrit 39 is repair debt under the thin bank and the mid-day #45 re-site wave (sites briefly spiked to 41 @12:38 then drained), not a reason to unpark ceil/seal or revert keep=1. Remotes are SAFE (res 1959/1752/2763). PRs 45 / 46 / 47 are already live and are not this review.

**Community.** Overmind `UpgradeSite` (blob 2eae97b) re-checked this run: still `storageBuffer=100000` / `energyPerBodyUnit=25000`; upgraders spawn only above that buffer and are not recycled for banking. Our 20k/300t latch and W47 40k/500t latch (paused to keep=1 only while sites are up) are the same shape at our floors. Placing RCL7 lab/factory shells is normal at this band; enabling reactions / XGH2O still waits on an Overmind-style ~100k energy cushion (live home ~13.1k / W47 5.9k ≪ 100k) even though termO 126976 termK 151080 are fat. TooAngel parks upgrade when thin, keeps logistics+repair warm. New remotes stay nod-only: CPU 12h avg 18.07 / 20 is tight (deploy spikes, not a new baseline). Do not restart war_cmd.

**Moves:** (1) finish the already-placed lab/factory sites — no new rampart covers, no labs-on, do not revert keep=1; (2) keep the 20k gate, home stays the RCL8 lead (~17.6 d at this pace, should tighten once home lab spend ends); funnel still coded only at home ≥~90%; (3) after sites, W47 leanBank rebuild → softCap ≥25k / 40k latch; do not unpark ceil/seal mid-bank. Defer labs KO / boost / industry / market / new remotes (**no re-ask**).

**Shipped:** Nothing (docs + ROADMAP only). SoftCap / leanBank / sealMinE / HUB_LINK / labs / industry / market / war_* / listener **unchanged**. No game deploy.


## 2026-11-13 08:2x Asia/Hong_Kong — 12h strategic review (plan holds; finish authorized lab/factory sites, keep=1 and 20k gate held, docs only)

**Board.** Home 56.13% stor avg 14.7k max 17355 min 5428 (13.63 e/t → RCL8 ≈18.6 d; 50.7% of 12h under 15k, was 24.9%; live tip 7718 why=floor_bank nUp=1 upExtra=0). W47 28.81% stor avg 769 max 5760 min 0 (0.00 e/t, progress flat 3150854 since 17:24; 100% <15k, 0% ≥20/25/40k, keep=1, 6 sites, siteRem 259481). Remotes ALL SAFE (W45N7 Invader killed). CPU avg 15.92 p95 19.85 max 28.82, bucket min 9923. LIVE a72e3c0 held (@84234754).

**Finding.** The sticky 20k/300t 3rd-upgrader gate still did its job — it never came close. Ledger 10130 t (t84225238→84235368): home sp:upgrader **1.38 gross / 0.30 refund / net 1.08 e/t** (was 1.34; well under the 5 e/t waste gate). **Zero ≥20k samples** this window (max 17355 @01:47), so upExtra never latched. Under-15k share rose 24.9%→50.7% because home spent the night on the 15k floor (steady 14 e/t, nUp=1) and then paid a 5400e defender after a ~200 t upgrade stall. Window min **5428** @08:04–08:05 is that post-defender + factory drain (open under-15k streak from 07:33, 600 t, recovering 5428→7718) — designed 15k-floor recovery, not a gate bug. Root of the stall: W45N7 solo Invader from 84234459 held upgraders while ea sat at 5500/5600 on unfillable stamp-B ext 31,34; **a72e3c0** (already live, not this review) sizes the kite to the payable pile and treats short as avail<cap-100 so readyTimeout can fire. Upgrade resumed 14 e/t. Mid-day yesterday `f7328c4` keep=1 while sites are up is held — do not revert. Sites 11→10 (W47 lab 27,38 finished); home factory nearly done (97261/100000); W47 factory 66840/100000, siteRem 259481 (~1.5 days at ~8 e/t build). Live W47 stor 3494, builders=4, upgraders=0, threatSoft leftover (w8threat=84234904, expires ~84236404 / ~70 min) is the known class; stor 3.5k would keep softE/leanBank on anyway. Remotes are SAFE (W45N7 why=killed, defender84234755 leave-alive). PRs 44 / a72e3c0 are already live and are not this review.

**Community.** Overmind `UpgradeSite` (blob 2eae97b) still `storageBuffer=100000` / `energyPerBodyUnit=25000`; upgraders spawn only above that buffer and are not recycled for banking. Our 20k/300t latch and W47 40k/500t latch (paused to keep=1 only while sites are up) are the same shape at our floors. Placing RCL7 lab/factory shells is normal at this band; enabling reactions / XGH2O still waits on an Overmind-style ~100k energy cushion (live home ~7.7k / W47 3.5k ≪ 100k) even though termO 126976 termK 147220 are fat. TooAngel parks upgrade when thin, keeps logistics+repair warm. New remotes stay nod-only: CPU 12h avg 15.92 / 20 is improved but still tight. Do not restart war_cmd.

**Moves:** (1) finish the already-placed lab/factory sites — no new rampart covers, no labs-on, do not revert keep=1; (2) keep the 20k gate, home stays the RCL8 lead (~18.6 d at this pace, should tighten once the 15k floor recovers); funnel still coded only at home ≥~90%; (3) after sites + leftover threat, W47 leanBank rebuild → softCap ≥25k / 40k latch; do not unpark ceil/seal mid-bank. Defer labs KO / boost / industry / market / new remotes (**no re-ask**).

**Shipped:** Nothing (docs + ROADMAP only). SoftCap / leanBank / sealMinE / HUB_LINK / labs / industry / market / war_* / listener **unchanged**. No game deploy.


## 2026-11-12 20:1x Asia/Hong_Kong — 12h strategic review (plan holds; finish authorized lab/factory sites, keep=1 and 20k gate held, docs only)

**Board.** Home 54.96% stor avg 15.8k max 18617 min 12190 (19.79 e/t → RCL8 ≈12.8 d; 24.9% of 12h under 15k, was 12.8%; live tip 14.0–14.7k why=floor_bank nUp=1 upExtra=0). W47 28.81% stor avg 13.7k max 26276 min 0 (11.84 e/t → RCL8 ≈33.9 d at this pace, was 18.04 / ~22.3 d; 46.3% <15k, 6.8% ≥25k, 0% ≥40k, keep=1, 11 sites, progress flat since 17:24). Remotes ALL SAFE (W47N7 wave gone). CPU avg 17.45 p95 20.88 max 92.5, bucket min 9912. LIVE afde7dd held (@84224625).

**Finding.** The sticky 20k/300t 3rd-upgrader gate still did its job. Ledger 9742 t (t84216162→84225904): home sp:upgrader **2.23 gross / 0.89 refund / net 1.34 e/t** (was 1.83; well under the 5 e/t waste gate). **Zero ≥20k samples** this window (max 18617), so upExtra never latched. Under-15k share rose 12.8%→24.9% because of defender bills plus site builders (longest 431 t, window min 12190 @17:32–18:03), then designed 15k-floor recovery — not a gate bug. Mid-day Misaki shipped **f7328c4**: new lab/factory covers cap at 300k, and W47 keep drops to 1 while any construction site is open (returns to the 40k latch when sites are gone). 11 sites remain (home factory 22.6k/100k, 3 labs still 0, rem ≈227k; W47 siteRem 336100, lead lab 27,38 at 40680/50000). Four W47 builders then a 4-Invader W47N7 wave during the 17:41–18:00 freeze drained W47 stor to 0 since 18:01; upgrade has been 0 since the keep-1 upgrader aged ~17:18 (progress stuck at 3150854 from 17:24). Live: stor 0, ea ~547, builders=0, emergency 1–2W miners and a tiny hauler just spawned — energyBank recovery, not a reason to undeploy keep=1 or cancel sites. Remotes are SAFE again (W47N7 why=gone, host 0, res 1963/1960/873). threatSoft leftover (w8threat=84225378, WINDOW 1500, expires ~84226878 / ~70 min) is the known class; stor 0 would keep softE/leanBank on anyway. PRs 42/43 (max-body first-tick defenders, kite at range 3) are already live and are not this review.

**Community.** Overmind `UpgradeSite` (blob 2eae97b) still `storageBuffer=100000` / `energyPerBodyUnit=25000`; upgraders spawn only above that buffer and are not recycled for banking. Our 20k/300t latch and W47 40k/500t latch (paused to keep=1 only while sites are up) are the same shape at our floors. Placing RCL7 lab/factory shells is normal at this band; enabling reactions / XGH2O still waits on an Overmind-style ~100k energy cushion (live home ~14k / W47 0 ≪ 100k) even though termO~127k termK~136k are fat. TooAngel parks upgrade when thin, keeps logistics+repair warm. New remotes stay nod-only: CPU 12h avg 17.45 / 20 is tight. The 11-09 smaller defender-#1 proposal is superseded by Misaki's max-spec standing order and PRs 42/43 — not re-asked. Do not restart war_cmd.

**Moves:** (1) finish the already-placed lab/factory sites — no new rampart covers, no labs-on, do not revert keep=1; (2) keep the 20k gate, home stays the RCL8 lead (~12.8 d); funnel still coded only at home ≥~90%; (3) after sites + leftover threat, W47 leanBank rebuild → softCap ≥25k / 40k latch; do not unpark ceil/seal mid-bank. Defer labs KO / boost / industry / market / new remotes (**no re-ask**).

**Shipped:** Nothing (docs + ROADMAP only). SoftCap / leanBank / sealMinE / HUB_LINK / labs / industry / market / war_* / listener **unchanged**. No game deploy.


## 2026-11-12 08:1x Asia/Hong_Kong — 12h strategic review (plan holds; 20k gate held, W47 softCap2 cleared into hysteresis, docs only)

**Board.** Home 53.20% stor avg 16.5k max 19.7k min 13626 (21.63 e/t → RCL8 ≈12.1 d; 12.8% of 12h under 15k, was 25%; live tip 17.7k why=ok nUp=2 upExtra=0). W47 27.76% stor avg 21.7k max 26607 min 12487 (18.04 e/t → RCL8 ≈22.3 d, was 16.99 / ~24.3 d; 16.6% ≥25k, 72.5% ≥20k, 0% ≥40k, keep=2). Remotes SAFE. CPU avg 17.25 p95 20.11 max 26.12, bucket min 9935. LIVE e98671f held (@84206586).

**Finding.** The sticky 20k/300t 3rd-upgrader gate still did its job, and the 15k floor looks healthier. Ledger 9731 t (aligned to last review t84206431→84216162): home sp:upgrader **3.03 gross / 1.20 refund / net 1.83 e/t** (was 1.82; well under the 5 e/t waste gate). **Zero ≥20k samples** this window (max 19717 @20:25, the tail of last review's 20017), so upExtra never latched. Under-15k dips were short (longest 180 t, window min 13626 lasted 20 t) — no repeat of last window's 1010 t / 8.6k crash. W47 keep=2 delivered another pace rise (16.99→18.04) while camping the 20–25k band; a morning ≥25k stretch **530 t** (07:30–08:09, peak **26607** @08:04) **cleared softCap2**. Live is the designed post-clear hysteresis: stor 23238, still above 22k ARM (softLeft 1762), softCap2=0 softE=0 softBand=1 phase=ready leanBank=0 upgKeep=2 upLatched=0 sealPark=1. Seal stays strict ≥25k; the 40k/500t latch is unchanged and was not close. Two Invader waves (W47N7 84212446 03:45–04:01 229 t; W45N7 84213313 05:02–05:05 228 t) were handled by standing leave-alive defence (rdef84212447 / defender84213314, later aged undamaged). threatSoft leftover from 84212664 expired ~05:51 and is off. A 26.6k peak that falls back into [22k, 25k) is progress on the softCap path, not a reason to unpark ceil/seal or move the 40k latch; if stor drops below 22k the cap will re-arm (known thrash).

**Community.** Overmind `UpgradeSite` (blob 2eae97b) still `storageBuffer=100000` / `energyPerBodyUnit=25000`; upgraders spawn only above that buffer and are not recycled for banking. Our 20k/300t latch and W47 40k/500t latch are the same shape at our floors. TooAngel parks upgrade when thin, keeps logistics+repair warm. Labs / XGH2O still wait on an Overmind-style ~100k energy cushion (live home 17.7k / W47 23.2k ≪ 100k) even though termO~127k termK~136k are fat. New remotes stay nod-only: CPU 12h avg 17.25 / 20 is tight. Standing remote defence cleared both Invaders; do not restart war_cmd.

**Moves:** (1) keep the 20k gate, home stays the RCL8 lead (~12.1 d); funnel still coded only at home ≥~90%. (2) W47 stays Phase0 — keep=2 until 40k sticky 500 t; do not unpark ceil/seal mid 22–25k hysteresis. (3) Defer labs KO / boost / industry / market / new remotes (**no re-ask**). Defender #1 threat-sizing still awaiting Misaki (proposed 11-09; two more first-bodies this window, leave-alive; not re-asked).

**Shipped:** Nothing (docs + ROADMAP only). SoftCap / leanBank / sealMinE / HUB_LINK / labs / industry / market / war_* / listener **unchanged**. No game deploy.


## 2026-11-11 20:2x Asia/Hong_Kong — 12h strategic review (plan holds; designed recovery after two 5200e defenders, docs only)

**Board.** Home 51.27% stor avg 15.8k max 20.6k min 8574 (21.23 e/t → RCL8 ≈12.9 d; 25% of 12h under 15k, was 27%; live tip 19.1k why=ok nUp=2 upExtra=0). W47 26.14% stor avg 24.0k max 32259 min 9478 (16.99 e/t → RCL8 ≈24.3 d, was 16.65 / ~25.3 d; 46.2% ≥25k, 0% ≥40k, keep=2). Remotes SAFE. CPU avg 17.80 p95 21.05 max 31.75, bucket min 9932. LIVE d09e9c4 held (#40 @84202370).

**Finding.** The sticky 20k/300t 3rd-upgrader gate still did its job, including through an evening defense spend. Ledger 9809 t: home sp:upgrader **3.00 gross / 1.18 refund / net 1.82 e/t** (was 1.18; well under the 5 e/t waste gate). Longest ≥20k stretch was **90 t** (max 20640 @15:12–15:18 HKT); a single 20017 sample at 20:19 did not hold, so upExtra never latched. Two full-budget remote defenders this window, both **5200e** (not the proposed ~2500 cap): W45N7 Invader 84204603–84204845 (242 t, defender84204604) then W47N7 Invader pause 84205796 SAFE since 84206031 (235 t, rdef84205797, still alive ttl~1012 — leave-alive policy). Home stor min **8574** @18:31, under-15k 1010 t, recrossed 15k @84205610 / 19:22, now 19.1k why=ok — designed floor recovery, not a new policy bug. The 19:29 exact2h 63.5% SOFT FIRST is that same episode (next hourly is the formal ALERT watch). W47 keep=2 delivered a slight pace rise and a real 25–32k band (longest ≥25k **980 t**, max 32259); then bled to 9478 after the defender bills + mutual w8guard/w8defender (aged out ~20:17) and is in leanBank keep=1 rebuild. threatSoft leftover is not stuck and did **not** postpone the 32k peak: w8threat=84206020 is the W47N7 seen-tick, WINDOW=1500, expires ~84207520; current stor <15k would keep softE on anyway; keep=2 until 40k is unchanged.

**Community.** Overmind `UpgradeSite` (blob 2eae97b) still `storageBuffer=100000` / `energyPerBodyUnit=25000`; upgraders spawn only above that buffer and are not recycled for banking. Our 20k/300t latch is the same shape at the 15k floor. TooAngel parks upgrade when thin, keeps logistics+repair warm. Labs / XGH2O still wait on an Overmind-style ~100k energy cushion (live home 19.1k / W47 13.9k ≪ 100k) even though termO~127k termK~136k are fat. New remotes stay nod-only: CPU 12h avg 17.80 / 20 is tight. Standing remote defence cleared both Invaders (waited=1 both times); do not restart war_cmd.

**Moves:** (1) keep the 20k gate, home stays the RCL8 lead (~12.9 d); funnel still coded only at home ≥~90%. (2) W47 stays Phase0 — keep=2 until 40k sticky 500 t (closest this window: 32.3k); do not unpark ceil/seal mid leanBank rebuild. (3) Defer labs KO / boost / industry / market / new remotes (**no re-ask**). Defender #1 threat-sizing still awaiting Misaki (proposed 11-09; two more 5200e first-bodies tonight; not re-asked).

**Shipped:** Nothing (docs + ROADMAP only). SoftCap / leanBank / sealMinE / HUB_LINK / labs / industry / market / war_* / listener **unchanged**. No game deploy.


## 2026-11-11 08:2x Asia/Hong_Kong — 12h strategic review (plan holds; 20k gate settled, docs only)

**Board.** Home 49.37% stor avg 15.6k max 21.1k (20.63 e/t → RCL8 ≈13.7 d; 27% of 12h under 15k, was 32%; live tip 14.2k floor_bank). W47 24.62% stor avg 21.0k max 26.2k (16.65 e/t → RCL8 ≈25.3 d, was 12.76 / ~34 d; 18.4% ≥25k, 0% ≥40k, keep=2). Remotes SAFE. CPU avg 17.52 p95 21.16, bucket min 9952. LIVE c27c44f held.

**Finding.** The sticky 20k/300t 3rd-upgrader gate did its job. Ledger 9846 t: home sp:upgrader **4.25 gross / 3.07 refund / net 1.18 e/t** (was 2.98; well under the 5 e/t waste gate). After deploy leftovers aged out, nUp stayed at 1–2; the only ≥20k stretch (max 21071 @20:32–20:39) lasted <300 t, so upExtra never latched. Last-hour upgrade recovered to 25.6 e/t. Remaining under-15k samples (and the overnight formal storage ALERT, later RESET) were full-budget defender waves: W47N7 twice, W45N7 once, plus a 7-tick unboosted Invader in owned W47N8 that spawned a joint home defender (overrides the 15k floor, documented). W47 keep=2 delivered the pace jump; several 25–26k touches (longest ~540 t, max 26167) bled back — live softCap2 ON, softLeft ~4.6k, 40k latch still waiting. model_w8 src_A "0.63 e/t" is a link-path accounting artefact: wminer was on stand A (26,11) and B almost the whole window.

**Community.** Overmind `UpgradeSite` (blob 2eae97b) still `storageBuffer=100000` / `energyPerBodyUnit=25000`; upgraders spawn only above that buffer and are not recycled for banking. Our 20k/300t latch is the same shape at the 15k floor. TooAngel parks upgrade when thin, keeps logistics+repair warm. Labs / XGH2O still wait on an Overmind-style ~100k energy cushion (live home 14.2k / W47 ~20k ≪ 100k) even though termO~127k termK~136k are fat. New remotes stay nod-only: CPU 12h avg 17.52 / 20 is tight. Standing remote defence absorbed the wave; do not restart war_cmd.

**Moves:** (1) keep the 20k gate, home stays the RCL8 lead (~13.7 d); funnel still coded only at home ≥~90%. (2) W47 stays Phase0 — keep=2 until 40k sticky 500 t; do not unpark ceil/seal mid soft-band. (3) Defer labs KO / boost / industry / market / new remotes (**no re-ask**). Defender #1 threat-sizing still awaiting Misaki (proposed 11-09; not re-asked).

**Shipped:** Nothing (docs + ROADMAP only). SoftCap / leanBank / sealMinE / HUB_LINK / labs / industry / market / war_* / listener **unchanged**. No game deploy.



## 2026-11-10 20:2x Asia/Hong_Kong — 12h strategic review (plan holds; sticky 20k 3rd-upgrader gate shipped)

**Board.** Home 47.52% stor avg 15.3k max 19.1k (20.50 e/t → RCL8 ≈14.6 d; 32% of 12h under 15k). W47 23.13% stor avg 19.4k max 25.7k (12.76 e/t → RCL8 ≈34 d; 7.2% ≥25k, 0% ≥40k, keep=2). Remotes SAFE. CPU avg 17.57, bucket 10k. LIVE 17b61c0 + this ship.

**Finding.** Ledger net sp:upgrader **2.98 e/t** (gross 11.30 − refund 8.32) is under the morning 5 e/t energy-waste gate, but the 16k `allowExtra` + `ctlEma≥700` gate still yo-yos a 1550 body the ≈21.7 e/t feed cannot support (last hour nUp hit 6; 1h upgrade 62%). Two 14W already demand 28 and are energy-bound; the 3rd does not raise long-run e/t.

**Community.** Overmind `UpgradeSite` sizes WORK from a stable buffer (100k) and never spawn-then-recycles. Our 1k band was the anti-pattern. New gate matches W47's 40k/500t latch, sized to the 15k floor.

**Moves:** (1) shipped sticky enter 20k + ctlEma≥1200 for 300 t, leave 18k or ema<700, no 3rd start while `energyAvailable < cap-1550`; (2) home = RCL8 lead, funnel at ~90%; (3) W47 40k sticky + defender threat-sizing still waiting.


## 2026-11-10 09:2x JST — 12h strategic review (plan holds; upgrader churn under floor-bank)

**Board.** Home 45.68% stor 14.7k (~20 e/t → RCL8 ≈15 d). W47 21.99% stor 14.4k (~8.9 e/t). Remotes SAFE (routine W45N7 cores). CPU ~16, bucket 10k.

**Finding.** Ledger 12h: home sp:upgrader **13.78 e/t gross** vs upgrade 17.07 e/t. Floor-bank hysteresis (enter <14.5k / leave ≥16k) spawns 2–3 extra 17-part upgraders at 16k, storage dips, extras recycled young (4 spawned 84176010–245, all gone by 84176975). Refund is TTL-proportional (≤125/part) and haulers salvage, so net loss unmeasured until now → shipped `rf:<role>` ledger hook (b9c984e).

**Community.** Overmind upgrade power = 1 + floor((energy − 100k)/10–25k) WORK, upgraders spawned only above the buffer and never recycled for banking — stable counts, no spawn/recycle oscillation.

**Moves:** (1) measure net upgrader spawn; fix churn if net >~5 e/t (don't recycle TTL>1000 under upBank / wider leave band); (2) home = RCL8 lead, funnel at ~90%; (3) defender threat-sizing awaits Misaki.

## 2026-11-09 21:1x JST — 12h strategic review (plan holds; W47 walls not the sink; RCL7→8 funnel)

**Board.** Home 43.89% stor 15.7k (~21 e/t → RCL8 ≈14–15 d). W47 21.19% stor 11.1k (~10.8 e/t; bank20 equilibrium 10–21k, no 25k clear for ~3 d). Remotes SAFE; CPU ~17, bucket 10k.

**W47 threatSoft wall question.** Seal walls 502–589k, ramparts 297–303k at the 20:08 JST hostile → threat floor 100k (`TH.urgentTarget`) queued nothing. Ledger (~190k t): `rw`+`tw` ≈ 0.6 e/t. The 6.4k drop = 5400 e first remote defender (full extension budget for one W47N7 Invader) + routine respawns while remote hauling paused. **No wall cap/throttle change.**

**Community (RCL7→8):**
- screepspl.us RCL: 7→8 costs 10.935M; RCL8 caps upgrading at 15 e/t. Common practice (jonwinsley "For Science", Harabi logistics) = terminal-funnel the capped room's surplus to the room still climbing; send only on explicit need, closest donor.
- Overmind: upgrade WORK scales only above a fat energy buffer (100k); `barrierHits[7]=1M`, fortify duty ~500k → our walls/ramparts are within norms for a non-war RCL7.
- Overmind `RangedDefenseOverlord.computeNeededHydraliskAmount` sizes defenders from hostile healing and our damage, i.e. threat-sized bodies; our defender #1 is budget-sized (min(cap, energyAvailable)). Candidate change, needs Misaki nod.

**Moves:** (1) home = RCL8 lead room, unchanged pull; (2) plan home→W47 terminal funnel for post-RCL8 (code at home ≥~90%); (3) propose threat-sized defender #1 for solo NPC Invaders. Shipped: `tools/ledger.py` (box-only).

## 2026-11-09 08:1x — 12h strategic review (peacetime plan holds / leanBank→softCap clear)

**Question:** After ~12h since 20:1x (plan holds / leanBank→softCap clear): did a softCap clear stick? Overnight home exact2h went SOFT then recovered; W47 peaked ~21.3k then bled; W45N7 saw more InvaderCore waves (one after the 07:27 patrol). Still the same order? Labs/boost/new-remote timing? Any small safe ship?

**Answer: PLAN HOLDS — docs only; nothing game-shipped.** SoftCap bank remains the gate. This window did **not** produce a 25k near-clear (unlike 25172/25391 two windows ago; last window peaked 22280). W47 storage peaked at **21275@23:00** then bled, with the 04:00 hour min **10682**, touched the leanBank 20k target (20057@00:00) without sticking, and is climbing again at 17329 (softLeft 7671 / bankLeft 2671 / phase=bank20 / upgKeep 2). A ~21.3k peak that does not stick is the known softCap-thrash / leanBank-rebuild path, not a new bottleneck class. SoftCap/labs/industry/market widgets outstanding — **never re-ask**. War_* stay stopped (`aborted_by_misaki`).

Home exact2h oscillated around the 70% soft line overnight (02:28 68.5% SOFT FIRST → 03:27 61.3% consec-soft=2 NOTIFY → 04:30 69.5% consec-soft=3 → 05:32 81.1% CLEAR RESET → 07:27 72.2% hold). Storage hugged the 15k floor (overnight BELOW 00:32–02:28 then ABOVE RESET @03:27; live 15560 surplus+560 floor_bank). Both are the known floor_bank + remote-pause coupling, not a code gap.

W45N7 had **four** InvaderCore waves this window after the 20:1x review: (1) pauseStart=84148641 CLEARED since 84149082; (2) inc=84151311 defender84151312 CLEARED since 84151704 dur 393; (3) pauseStart=84152844 defender84152848 CLEARED since 84153044 dur 200; (4) inc=84156537 @07:30 why=core defender84156538 spawned next tick (waited=1), dispatched dur 151, arrived travel 68, CLEARED since 84156930 dur 393. Latest reservation dipped 2116→866 (attackController) and is rebuilding with the reserver on-site in W45N7. Standing ea-budget defender handled all four. Do **not** restart war_cmd.

### Live (~08:15–08:18 Asia/Hong_Kong, LIVE **87d8c84** deploy@84127638, tick 84157161–196)
| Room | Notes |
|------|-------|
| W46N8 | RCL7 **42.00%** (4.593M/10.935M); stor 15560 ABOVE15k; nUp1 work14 tUp1 why=floor_bank surplus+560; last hourly exact2h **72.2% CLEAR** consec-soft=0 (12h 40.35→42.00%, +181k ≈18.62/26 ≈71.6%); smA=6 |
| W47N8 | RCL7 **20.40%** (2.231M); stor 17329 softCap2 **ON** softLeft 7671 softBand1 bankWhy=bank leanBank1 phase=bank20 bankLeft 2671; hubReady1 hubPrime0 (hubLinkE=0 cd=5 just-sent flap); upgKeep2 sealPark1; **contMinPct49 contLow1 roadCrit3** (was 48/1/38); hMax4 builders2 looseE 2730 |
| Remotes | W45N8 / W45N7 / W47N7 **ALL SAFE** (vis; foes0 cores0; res 2199/866/2453); W45N7 why=killed CLEARED since 84156930 (recycling defender84156538); r7.on end=84159625 by=Misaki left~2445; raidLeft=0; ops.w47n9.on=false phase=fallback ABORT |
| Colony | PEACETIME; war_cmd pause `aborted_by_misaki`; listener single-slot 5:5:1:1; yield gone; CPU live 15.6 / 12h model 16.8 / hourly 15.8–17.6 / bkt10k n=38; labs OFF labReady propose/ready actOk=1 actGaps="" homeStor 15610 (**no re-ask**; last review actOk=0 actGaps=homeStor); softCap widget outstanding (**no re-ask**); termO~127k termK~95.5k Ostor~17.3k |

12h Timescale + model (from ~20:16): home 4.412M→4.593M (Δp~+181k / 9710t ≈18.62 e/t); W47 2.115M→2.231M (Δp~+116k ≈11.94 e/t vs ideal 30.08, intentional park). `tools/model.py --hours 12` measured upgrade **18.62**/26.00; `tools/model_w8.py --hours 12` **11.94**/30.08 (WORK20 park). W47 stor this window: max **21275@23:00**, min **10682** (04:00 hour), avg oscillating ~14–20k; 06:00 hour missing (metrics gap 1300t ~05:37–07:19, stor 19562→13511 inside the gap).

### Research (community + our stack)
1. **Overmind UpgradeSite** (re-checked github master `upgradeSite.ts` 2026-11-09 morning): `energyBuffer=100000` / `energyPerBodyUnit=10000` / `linksRequestBelow=200` (same as 20:1x; blob 2eae97b still has `storageBuffer=100000` / `energyPerBodyUnit=25000` — the **100k buffer gate is unchanged**). Scale WORK only above 100k. We park at LEAN_SOFT=25k (and leanBank rebuild under 20k); soft clear remains the gate before ceil6 / labs. Live ~15.6k / 17.3k ≪ 100k.
2. **Overmind WorkerOverlord** (re-checked master `worker.ts`): containers <50% + RoadLogistics size `repairTicks` independent of `fortifyDutyThreshold=500k` / `barrierHits[7]=1M`. Cont49 / contLow1 — repair duty mid-band, not severe debt; roadCrit 38→3 under softCap is the known `energyBank`/`mvp` pause draining (do **not** unpark deep seal mid leanBank; KEY 300k DONE).
3. **screepspl.us Intermediate / StructureLab / TooAngel:** RCL7 unlocks 6 labs; XGH2O / reactions after energy buffer + mineral network (wiki: typically a full mineral set / SK), not while storage thrash. TooAngel parks upgrade when thin, keeps logistics+repair warm. Our O+K stocks are fatter (termO~127k termK 80k→95.5k) but energy cushion is not — flipping `ops.labs=KO` now would compete with softCap climb. `labReady` actOk flipped 0→1 only because homeStor recovered above 15k — **no re-ask**.
4. **Harabi remotes / `docs/CPU.md`:** new remotes need spawn budget + Misaki nod; CPU~16–17/20 with 2 rooms (12h model avg 16.8) — 3rd room / extra remote still nod-only and CPU-tight.
5. **Standing remote defence:** four W45N7 InvaderCore waves this window were CLEARED by the existing ea-budget defender (latest waited=1, dur 393 — same proof as 20:2x). Recurrence is normal remote cadence, not a new strategic topic and not a reason to restart war_cmd. Post-core reservation dip is expected (`attackController`); the home reserver is on-site rebuilding.

### Next 1–3 (same order; leanBank is the current softCap-bank phase)
1. **leanBank→20k → softCap bank→clear ≥25k** (soft-band park + surplus trim nUp≤3 while stor<25k) — current bottleneck (softLeft 7671 / bankLeft 2671; 21.3k peak did not stick; climbing again at 17.3k).
2. **On true clear:** nUp→ceil6 / short≥70%; hold contMinPct≥50 (now 49 / contLow1; roadCrit already 3).
3. **seal→1M under soft-gate** after clear sticks; home floor≥15k hold. **Defer** labs KO / boost / industry / market / new remotes (**no re-ask**).

### Shipped
**Nothing** (docs + ROADMAP only). SoftCap / leanBank / sealMinE / HUB_LINK / labs / industry / market / war_* / listener **unchanged**. No game deploy.

## 2026-11-08 20:1x — 12h strategic review (peacetime plan holds / leanBank→softCap clear)

**Question:** After ~12h since 08:1x (plan holds / leanBank→softCap clear): did a softCap clear stick? Home upgrade oscillated around the 70% line (hourly notify @17:24 then recover) and storage hugged the 15k floor; W45N7 saw two more InvaderCore waves; W47 bankLeft went 1.7k→4.8k after a noon peak. Still the same order? Labs/boost/new-remote timing? Any small safe ship?

**Answer: PLAN HOLDS — docs only; nothing game-shipped.** SoftCap bank remains the gate. This window did **not** produce a 25k near-clear (unlike the previous window's 25172@19:00 and 25391@21:00). W47 storage peaked at **22280@12:51** (tick 84141310) then bled, with the 17:00 hour min **10524**, and is climbing again at ~15.2k (softLeft~9.8k / bankLeft~4.8k / phase=bank20). A ~22.3k peak that does not stick is the known softCap-thrash / leanBank-rebuild path, not a new bottleneck class. SoftCap/labs/industry/market widgets outstanding — **never re-ask**. War_* stay stopped (`aborted_by_misaki`).

Home exact2h oscillated around the 70% soft line (13:28 60.9% SOFT FIRST → 14:32 76.4% → 15:30 84.1% → 16:29 69.1% FIRST → 17:24 65.1% consec-soft=2 FIRST-FIRE notify → 18:25 83.1% RESET → 19:32 71.9% hold). Storage hugged the 15k floor, dipping on W45N7 remote_pause / floor_bank (19:32 tip 14267 consec-under=1 FIRST; live ~14.5–15.3k knife-edge). Both are the known floor_bank + remote-pause coupling, not a code gap.

W45N7 had two more InvaderCore waves this window after the overnight clear: (1) InvaderCore[7,44] inc=84143284 / dispatched@84143452 / CLEARED since 84143693; (2) pauseStart=84145966 / defender84146005 / CLEARED since 84146395 dur 429. Standing ea-budget defender handled both. Do **not** restart war_cmd.

### Live (~20:20–20:22 Asia/Hong_Kong, LIVE **87d8c84** deploy@84127638, tick 84147479–494)
| Room | Notes |
|------|-------|
| W46N8 | RCL7 **40.35%** (4.412M/10.935M); stor knife-edge ~14.5–15.3k (q 15276@84147479; room_stats 14476@84147480; labReady homeStor 14526@84147486); nUp3 work42 tUp2 why=ok surplus~-524; last hourly exact2h **71.9% CLEAR** consec-soft=0 (12h 38.58→40.35%, +192k ≈19.3/26 ≈74%); smA=6 |
| W47N8 | RCL7 **19.34%** (2.115M); stor~15.2k softCap2 **ON** softLeft~9.8k softBand1 bankWhy=bank leanBank1 phase=bank20 bankLeft~4.8k; hubReady1 hubPrime1 upgKeep2 sealPark1; **contMinPct48 contLow1 roadCrit38** (mvp pause under softCap); hMax4 builders1 |
| Remotes | W45N8 / W45N7 / W47N7 **ALL SAFE** (vis; foes0 cores0; res~2353/1934/2535); W45N7 why=killed (today's waves CLEARED); r7.on end=84150021 by=Misaki; raidLeft=0; ops.w47n9.on=false phase=fallback ABORT |
| Colony | PEACETIME; war_cmd pause `aborted_by_misaki`; listener single-slot 5:5:1:1; yield gone; CPU live~13–15 / 12h model avg 16.7 / bkt10k n~35–36; labs OFF labReady propose/ready actOk=0 actGaps=homeStor (**no re-ask**); softCap widget outstanding (**no re-ask**); termO~127k termK~80.3k Ostor~17.3k |

12h Timescale (from 08:16): home 4.220M→4.412M (Δp~+193k / 9970t ≈19.3 e/t); W47 2.014M→2.115M (Δp~+101.5k ≈10.2 e/t vs ideal 30.08, intentional park). `tools/model.py --hours 12` measured upgrade **19.32**/26.00; `tools/model_w8.py --hours 12` **10.13**/30.08 (WORK20 park). W47 stor this window: max **22280@12:51**, min **10524** (17:00 hour), avg~16.8k.

### Research (community + our stack)
1. **Overmind UpgradeSite** (re-checked github master `upgradeSite.ts` 2026-11-08 evening): `energyBuffer=100000` / `energyPerBodyUnit=10000` / `linksRequestBelow=200` (same as 08:1x; blob 2eae97b still has `storageBuffer=100000` / `energyPerBodyUnit=25000` — the **100k buffer gate is unchanged**). Scale WORK only above 100k. We park at LEAN_SOFT=25k (and leanBank rebuild under 20k); soft clear remains the gate before ceil6 / labs. Live ~14.5–15.3k ≪ 100k.
2. **Overmind WorkerOverlord** (re-checked master `worker.ts`): containers <50% + RoadLogistics size `repairTicks` independent of `fortifyDutyThreshold=500k` / `barrierHits[7]=1M`. Cont48 / contLow1 — repair duty mid-band, not severe debt; roadCrit38 under softCap is the known `energyBank`/`mvp` pause (do **not** unpark deep seal mid leanBank; KEY 300k DONE).
3. **screepspl.us Intermediate / StructureLab / TooAngel:** RCL7 unlocks 6 labs; XGH2O / reactions after energy buffer + mineral network, not while storage thrash. TooAngel parks upgrade when thin, keeps logistics+repair warm. Our O+K stocks are fat (termO~127k termK~80k) but energy cushion is not — flipping `ops.labs=KO` now would compete with softCap climb (**no re-ask**).
4. **Harabi remotes / `docs/CPU.md`:** new remotes need spawn budget + Misaki nod; CPU~13–17/20 with 2 rooms (12h model avg 16.7) — 3rd room / extra remote still nod-only and CPU-tight.
5. **Standing remote defence:** two W45N7 InvaderCore waves this window were CLEARED by the existing ea-budget defender (dur 429 on the latest). Recurrence is normal remote cadence, not a new strategic topic and not a reason to restart war_cmd.

### Next 1–3 (same order; leanBank is the current softCap-bank phase)
1. **leanBank→20k → softCap bank→clear ≥25k** (soft-band park + surplus trim nUp≤3 while stor<25k) — current bottleneck (softLeft~9.8k / bankLeft~4.8k; noon peak 22.3k did not stick).
2. **On true clear:** nUp→ceil6 / short≥70%; hold contMinPct≥50 (now 48 / contLow1; roadCrit residual drains after mvp lifts).
3. **seal→1M under soft-gate** after clear sticks; home floor≥15k hold. **Defer** labs KO / boost / industry / market / new remotes (**no re-ask**).

### Shipped
**Nothing** (docs + ROADMAP only). SoftCap / leanBank / sealMinE / HUB_LINK / labs / industry / market / war_* / listener **unchanged**. No game deploy.

## 2026-11-08 08:1x — 12h strategic review (peacetime plan holds / leanBank→softCap clear)

**Question:** After ~12h since 20:2x (plan holds / leanBank→softCap clear + defender #1 ea-budget): did a softCap clear stick? Overnight W45N7 InvaderCore + home 04:31 SOFT then recover — still the same order? Labs/boost/new-remote timing? Any small safe ship?

**Answer: PLAN HOLDS — docs only; nothing game-shipped.** SoftCap bank remains the gate. W47 near-cleared twice this window (19:00 max stor 25172, already noted last review; **21:00 max 25391** after that review) then bled through leanBank (morning dip min~13.3k @05–07). Live now climbing again: softLeft~6.7k / bankLeft~1.7k / phase=bank20 / stor~18.3k — same band as 20:2x (softLeft~6.0k / bankLeft~1.0k). Two near-clears that do not stick is the known softCap-thrash path, not a new bottleneck class. SoftCap/labs/industry/market widgets outstanding — **never re-ask**. War_* stay stopped (`aborted_by_misaki`).

Overnight W45N7 InvaderCore@[3,37] (since 84132510, `defender84132511` next tick) was CLEARED by ~03:26 — standing defence, and live proof the 20:2x ea-budget ship works. Home exact2h dipped to 68.9% SOFT consec-soft=1 FIRST @04:31 then recovered CLEAR by 05:23 (last hourly @07:23 72.7% CLEAR consec-soft=0). Storage knife-tipped ~15k and recovered ABOVE.

### Live (~08:16 Asia/Hong_Kong, LIVE **87d8c84** deploy@84127638, tick 84137532–542)
| Room | Notes |
|------|-------|
| W46N8 | RCL7 **38.58%** (4.220M/10.935M); stor~17.4k ABOVE15k; nUp3 work42 why=ok surplus~2.4k; last hourly exact2h **72.7% CLEAR** consec-soft=0 (12h 36.73→38.58%, +204k ≈20.5/26 ≈79%); smA=6 |
| W47N8 | RCL7 **18.42%** (2.014M); stor~18.3k softCap2 **ON** softLeft~6.7k softBand1 bankWhy=bank leanBank1 phase=bank20 bankLeft~1.7k; hubReady1 hubPrime1 upgKeep2 sealPark1; **contMinPct50 contLow0 roadCrit24** (mvp pause under softCap); hMax4 |
| Remotes | W45N8 / W45N7 / W47N7 **ALL SAFE** (vis; foes0 cores0; res~2111/2078/2831); raidLeft=0; ops.w47n9.on=false phase=fallback ABORT |
| Colony | PEACETIME; war_cmd pause `aborted_by_misaki`; listener single-slot 5:5:1:1; yield gone; CPU~15.5/20 bkt10k n~38; labs OFF labReady propose/actOk/ready (**no re-ask**); softCap widget outstanding (**no re-ask**); termO~127k termK~69k Ostor~17.3k |

12h Timescale: home 36.73%→38.58% (Δp~+204k / 9960t ≈20.5 e/t); W47 17.31%→18.42% (Δp~+121k ≈12.1 e/t vs ideal~30, intentional park). W47 stor: near-clear 25172@19:00 and 25391@21:00, then 16k→13k morning dip, now 18.3k climbing.

### Research (community + our stack)
1. **Overmind UpgradeSite** (re-checked github master `upgradeSite.ts` 2026-11-08): `energyBuffer=100000` / `energyPerBodyUnit=10000` (prior reviews cited 25k at blob 2eae97b — the **100k buffer gate is unchanged**). Scale WORK only above 100k; `linksRequestBelow=200`. We park at LEAN_SOFT=25k (and leanBank rebuild under 20k); soft clear remains the gate before ceil6 / labs. Live ~17–18k ≪ 100k.
2. **Overmind WorkerOverlord** (re-checked master `worker.ts`): containers <50% + RoadLogistics size `repairTicks` independent of `fortifyDutyThreshold=500k` / `barrierHits[7]=1M`. Cont50 / contLow0 — repair duty satisfied; roadCrit24 under softCap is the known `energyBank`/`mvp` pause (do **not** unpark deep seal mid leanBank; KEY 300k DONE).
3. **screepspl.us Intermediate / StructureLab / TooAngel:** RCL7 unlocks 6 labs; XGH2O / reactions after energy buffer + mineral network, not while storage thrash. TooAngel parks upgrade when thin, keeps logistics+repair warm. Our O+K stocks are fat (termO~127k termK~69k) but energy cushion is not — flipping `ops.labs=KO` now would compete with softCap climb (**no re-ask**).
4. **Harabi remotes / `docs/CPU.md`:** new remotes need spawn budget + Misaki nod; CPU~15–16/20 with 2 rooms — 3rd room / extra remote still nod-only and CPU-tight.
5. **Standing remote defence:** overnight W45N7 core spawned `defender84132511` the next tick (20:2x ea-budget). Recurrence is normal remote cadence (~1 core + earlier solo invader this window), not a new strategic topic.

### Next 1–3 (same order; leanBank is the current softCap-bank phase)
1. **leanBank→20k → softCap bank→clear ≥25k** (soft-band park + surplus trim nUp≤3 while stor<25k) — current bottleneck (softLeft~6.7k / bankLeft~1.7k; two near-clears this window did not stick).
2. **On true clear:** nUp→ceil6 / short≥70%; hold contMinPct≥50 (already 50; roadCrit residual drains after mvp lifts).
3. **seal→1M under soft-gate** after clear sticks; home floor≥15k hold. **Defer** labs KO / boost / industry / market / new remotes (**no re-ask**).

### Shipped
**Nothing** (docs + ROADMAP only). SoftCap / leanBank / sealMinE / HUB_LINK / labs / industry / market / war_* / listener **unchanged**. No game deploy.

## 2026-11-07 20:2x — 12h strategic review (peacetime plan holds / leanBank→softCap clear; defender #1 ea-budget)

**Question:** After ~12h since 08:1x (plan holds / leanBank→softCap clear): did softCap clear stick? Cont reclaim done? Labs/boost/new-remote timing? Any small safe ship?

**Answer: PLAN HOLDS — plus one standing-ops ship.** SoftCap bank remains the gate. Live hit near-clear ~19:28 (softLeft~78 / stor~25.2k) then bled into leanBank re-arm (classic softCap thrash) — now softLeft~6.0k / bankLeft~1.0k / phase=bank20 climbing again. Cont reclaim **DONE** (contMinPct50 / contLow0 / roadCrit0). SoftCap/labs/industry/market widgets outstanding — **never re-ask**. War_* stay stopped (`aborted_by_misaki`).

**Ops gap shipped:** solo W45N7 Invader THREAT held home spawn 125+t because `planDefender` sized body #1 to full RCL7 cap (cost=5600) while peacetime `energyAvailable` stuck ~4680 (`lastFull` stale ~43k ticks under floor_bank). Original hold was "collect the 1300". Body #1 now sizes to `min(cap, max(avail, 1300))`; extras still full-cap + extrasOk. Live proof: `defender84127622` (40 parts) spawned immediately @84127622 for W45N7.

### Live (~20:18–20:25 Asia/Hong_Kong, tip was **6dcd577** → deploy **8c9556e+dirty** @84127622)
| Room | Notes |
|------|-------|
| W46N8 | RCL7 **36.73%** (4.016M/10.935M); stor~19.0–19.2k ABOVE15k; model2h upg **18.49/26 ≈71% SOFT** (12h 34.9→36.7%; short floor_bank); smA=6 |
| W47N8 | RCL7 **17.31%** (1.893M); stor~17.8–19.0k softCap2 **ON** softLeft~6.0k softBand1 bankWhy=bank leanBank1 phase=bank20 bankLeft~1.0k; hubReady1 upgKeep2 sealPark1; **contMinPct50 contLow0 roadCrit0** builders2; hMax4 |
| Remotes | W45N8 SAFE res~2.2k; **W45N7 THREAT solo** (defender spawning post-fix); W47N7 SAFE; raidLeft=0; ops.w47n9 ABORT |
| Colony | PEACETIME; war_cmd pause `aborted_by_misaki`; listener single-slot 5:5:1:1; yield gone; CPU~14–17/20 bkt10k; labs OFF (**no re-ask**); softCap widget outstanding (**no re-ask**); termO~127k termK~69k |

12h Timescale: home 33.1%→36.7% (Δp~+221k); W47 15.0%→17.3% under softCap park. W47 stor saw ~25.2k near-clear @19:xx then leanBank dip ~17–19k.

### Research (community + our stack)
1. **Overmind UpgradeSite** ([upgradeSite.ts](https://github.com/bencbartlett/Overmind/blob/2eae97b/src/hiveClusters/upgradeSite.ts)): `storageBuffer=100000` / `energyPerBodyUnit=25000` — scale WORK only above 100k. We park at LEAN_SOFT=25k; soft clear remains the gate before ceil6 / labs. Live ~18–19k ≪ 100k.
2. **Overmind WorkerOverlord** ([worker.ts](https://github.com/bencbartlett/Overmind/blob/2eae97b/src/overlords/core/worker.ts)): containers <50% + RoadLogistics critical size `repairTicks` independent of `fortifyDutyThreshold=500k` / `barrierHits[7]=1M`. Cont50 / roadCrit0 — repair duty satisfied; do **not** unpark deep seal mid softCap/leanBank.
3. **screepspl.us Maturity Matrix / StructureLab** ([Maturity Matrix](https://wiki.screepspl.us/Maturity_Matrix/), [StructureLab](https://wiki.screepspl.us/StructureLab/)): RCL7 unlocks 6 labs; XGH2O / boosts after energy buffer + mineral network. Common mistake = flip labs/reactions while storage thrash. Our O+K fat (termO~127k termK~69k) but energy cushion thin — **no re-ask**.
4. **TooAngel / Harabi remotes / `docs/CPU.md`:** energy + remotes first; new remotes need spawn budget + Misaki nod. CPU~14–17/20 with 2 rooms — 3rd room / extra remote still nod-only and CPU-tight.
5. **Standing remote defence:** size first responder to available energy so soft peacetime economies do not freeze the spawn queue waiting for a never-filled RCL7 cap (this ship).

### Next 1–3 (same order; leanBank is the current softCap-bank phase)
1. **leanBank→20k → softCap bank→clear ≥25k** (soft-band park + surplus trim nUp≤3 while stor<25k) — current bottleneck (softLeft~6.0k / bankLeft~1.0k after near-clear thrash).
2. **On true clear:** nUp→ceil6 / short≥70%; hold contMinPct≥50 (already 50 / roadCrit0).
3. **seal→1M under soft-gate** after clear sticks; home floor≥15k hold. **Defer** labs KO / boost / industry / market / new remotes (**no re-ask**).

### Shipped
1. `src/managers/spawn.js` `planDefender`: body #1 `eBudget = min(cap, max(avail, 1300))` (extras still full cap).
2. `tests/defender_squad.js` soft-ea + full-ea + extras cases.
3. Deployed **8c9556e+dirty** @84127622 — live `defender84127622` for W45N7.
SoftCap / leanBank / sealMinE / HUB_LINK / labs / industry / market / war_* / listener **unchanged**. **No softCap/labs re-ask.**

## 2026-11-07 08:1x — 12h strategic review (peacetime plan holds / leanBank→softCap clear)

**Question:** After ~12h since 20:1x (plan holds / leanBank rebuild), overnight home exact2h SOFT + stor UNDER then recover, W47 still leanBank/softCap: does softCap→clear→seal still hold? Cont reclaim / labs/boost/new-remote timing? Any small safe ship?

**Answer: PLAN HOLDS — docs only; nothing game-shipped.** SoftCap bank remains the gate: live softLeft~8.4k with **leanBank1 / phase=bank20 / bankLeft~3.4k** climbing (improved from softLeft~12.4k @07:30). Cont mid-band (~46–52) with **builders=2** is the 20:2x debt ship working; roadCrit≈1. SoftCap/labs/industry/market widgets outstanding — **never re-ask**. War_* stay stopped (`aborted_by_misaki`).

### Live (~08:11–08:13 Asia/Hong_Kong, LIVE **6dcd577** deploy@84088055, tick ~84117890–920)
| Room | Notes |
|------|-------|
| W46N8 | RCL7 **34.94%** (3.821M/10.935M); stor~15.7–16.0k ABOVE15k; exact2h ~18.1/26 = **~69.5% SOFT recovering** (was 67.8% @07:30; 12h Δp~223k ≈20.7/26 ≈80% overnight mean); short floor_bank nUp2–3 work28; smA=6 |
| W47N8 | RCL7 **16.15%** (1.766M); stor~15.2–15.5k softCap2 **ON** softLeft~8.4k softBand1 bankWhy=bank leanBank1 phase=bank20 bankLeft~3.4k; hubReady1 hub link E=800 upgKeep2 sealPark1; **contMinPct~46–52 contLow2–3 roadCrit1** builders**2**; hMax3; KEY~300k DONE |
| Remotes | W45N8 / W45N7 / W47N7 **ALL SAFE** (res~2217/2238/2427); raidLeft=0; ops.w47n9.on=false phase=fallback ABORT |
| Colony | PEACETIME; war_cmd pause `aborted_by_misaki`; listener single-slot 5:5:1:1; yield gone; CPU~15–16/20 bkt10k; labs OFF labReady propose/actOk (**no re-ask**); softCap widget outstanding (**no re-ask**); termO~127k termK~69k |

12h hourly (Timescale): home 33.1%→34.9%; W47 15.0%→16.2% under softCap park (~12 e/t vs ideal~30 intentional). Overnight W47 softLeft 9→12→8.4k (dip then rebuild); home stor thrash UNDER@07:30 then ABOVE again.

### Research (community + our stack)
1. **Overmind UpgradeSite** (re-checked github `upgradeSite.ts`): `storageBuffer=100000` / `energyPerBodyUnit=25000` — scale WORK only above 100k; linksRequestBelow=200. We park at LEAN_SOFT=25k (and leanBank rebuild under 20k); soft clear remains the gate before ceil6 / labs. Live ~15–16k ≪ 100k.
2. **Overmind WorkerOverlord** (`worker.ts`): containers <50% + RoadLogistics critical=25% size `repairTicks` independent of `fortifyDutyThreshold=500k` / `barrierHits[7]=1M`. Cont~46–52 / roadCrit1 / builders=2 — repair duty correctly warm under softCap; do **not** unpark deep seal mid softCap/leanBank (soft-gate + sealPark already correct; KEY 300k DONE).
3. **screepspl.us Intermediate / TooAngel:** XGH2O / mineral reactions after energy buffer + mineral network; TooAngel parks upgrade when thin, keeps logistics warm. Our O+K stocks are fat (termO~127k termK~69k) but energy cushion is not — flipping `ops.labs=KO` now would compete with softCap climb (**no re-ask**).
4. **Harabi remotes / `docs/CPU.md`:** new remotes need spawn budget + Misaki nod; CPU~16/20 with 2 rooms — 3rd room / extra remote still nod-only and CPU-tight.

### Next 1–3 (same order; leanBank is the current softCap-bank phase)
1. **leanBank→20k → softCap bank→clear ≥25k** (soft-band park + surplus trim nUp≤3 while stor<25k) — current bottleneck (softLeft~8.4k / bankLeft~3.4k).
2. **On true clear:** nUp→ceil6 / short≥70%; hold contMinPct≥50 (roadCrit already ~0; 2 builders reclaiming).
3. **seal→1M under soft-gate** after clear sticks; home floor≥15k hold. **Defer** labs KO / boost / industry / market / new remotes (**no re-ask**).

### Shipped
**Nothing** (docs + ROADMAP only). SoftCap / leanBank / sealMinE / HUB_LINK / labs / industry / market / war_* / listener **unchanged**. No game deploy.

## 2026-11-06 20:1x — 12h strategic review (peacetime plan holds / softCap clear next; leanBank rebuild)

**Question:** After ~12h since 08:1x (plan holds / softCap clear next), mid-day softLeft near-clear (~1.8k) then leanBank re-arm (W47 stor~6.7k @18:24): does softCap→clear→seal still hold? Labs/boost/new-remote timing? Any small safe ship?

**Answer: PLAN HOLDS — docs + ops q.py only; nothing game-shipped.** Cont reclaim held (~48%); **roadCrit 32→0** under softCap (better than 08:1x "paused by design" residual). SoftCap bank remains the gate: live softLeft~8.7–9.7k with **leanBank1 / phase=bank20** climbing from the afternoon dip. SoftCap/labs/industry/market widgets outstanding — **never re-ask**. War_* stay stopped (`aborted_by_misaki`).

### Live (~20:18–20:20 Asia/Shanghai, LIVE **6dcd577** deploy@84088055, tick ~84107980–999)
| Room | Notes |
|------|-------|
| W46N8 | RCL7 **33.07%** (3.617M/10.935M); stor~15.9–16.1k ABOVE15k knife-edge; exact2h ~20.8/26 = **~80% CLEAR** (12h Δp~213k; short floor_bank/ok nUp1 work14); smA=6; upgFeed rem SAFE |
| W47N8 | RCL7 **15.03%** (1.644M); stor~16.3k softCap2 **ON** softLeft~8.7–9.7k softBand1 bankWhy=bank leanBank1 phase=bank20 bankLeft~3.7–4.7k; hubReady1 hubPrime1 upgKeep2 sealPark1; **contMinPct~48 contLow1 roadCrit0**; builders1; hMax3 |
| Remotes | W45N8 / W45N7 / W47N7 **ALL SAFE** (res~2.1–2.7k; W45N7 fhl Spawn1 gone; W47N7 killed); raidLeft=0; ops.w47n9.on=false phase=fallback ABORT |
| Colony | PEACETIME; war_cmd pause `aborted_by_misaki`; listener single-slot 5:5:1:1; yield gone; CPU~12–13/20 bkt10k; labs OFF labReady propose/actOk (**no re-ask**); softCap widget outstanding (**no re-ask**); termO~127k termK~69k |

12h hourly (Timescale): home 31.1%→33.1%; W47 13.9%→15.0% under softCap park (~12 e/t vs ideal~30 intentional). Afternoon W47 stor dipped ~6.7k @18:24 then rebuilt to ~16k.

### Research (community + our stack)
1. **Overmind UpgradeSite:** `storageBuffer=100000` / `energyPerBodyUnit=25000` — scale WORK only above 100k. We park at LEAN_SOFT=25k (and leanBank rebuild under 20k); soft clear remains the gate before ceil6 / labs. Live ~16k ≪ 100k.
2. **Overmind WorkerOverlord:** containers <50% + RoadLogistics critical=25% size `repairTicks` independent of `fortifyDutyThreshold=500k` / `barrierHits[7]=1M`. Cont~48 / roadCrit0 — repair duty satisfied enough; do **not** unpark deep seal mid softCap/leanBank (soft-gate + sealPark already correct).
3. **screepspl.us Intermediate / TooAngel:** XGH2O / mineral reactions after energy buffer + mineral network; TooAngel parks upgrade when thin, keeps logistics warm. Our O+K stocks are fat (termO~127k termK~69k) but energy cushion is not — flipping `ops.labs=KO` now would compete with softCap climb (**no re-ask**).
4. **Harabi remotes / `docs/CPU.md`:** new remotes need spawn budget + Misaki nod; CPU~13/20 with 2 rooms — 3rd room / extra remote still nod-only and CPU-tight.

### Next 1–3 (same order; leanBank is the current softCap-bank phase)
1. **leanBank→20k → softCap bank→clear ≥25k** (soft-band park + surplus trim nUp≤3 while stor<25k) — current bottleneck.
2. **On true clear:** nUp→ceil6 / short≥70%; hold contMinPct≥50 (roadCrit already 0).
3. **seal→1M under soft-gate** after clear sticks; home floor≥15k hold. **Defer** labs KO / boost / industry / market / new remotes (**no re-ask**).

### Shipped
**Docs + `tools/q.py` (no user/memory fallback — ops safety).** SoftCap / leanBank / sealMinE / HUB_LINK / labs / industry / market / war_* / listener **unchanged**. No game deploy.

## 2026-11-06 08:1x — 12h strategic review (peacetime plan holds / softCap clear next)

**Question:** After ~12h peacetime since the 20:2x severe-cont-debt ship (`6dcd577` @84088055), does softCap→clear→seal still hold? Cont/road debt reclaim status? Any small safe ship, or labs/boost/new-remote timing?

**Answer: PLAN HOLDS — docs only; nothing shipped.** Cont reclaim largely succeeded (contMinPct 12→~46–50, contLow4→0–1). Residual `roadCrit~32` under softCap is **by design**: `energyBank`/`mvp` pauses roadNeed(0.25/0.6) so only containers<50% + roads<10% run while banking (15:5x/08:4x). SoftCap bank (softLeft~8.3k, stor~16–20k thrash→climb) remains the bottleneck. SoftCap/labs/industry/market widgets outstanding — **never re-ask**. War_* stay stopped (`aborted_by_misaki`).

### Live (~08:09–08:12 Asia/Shanghai, LIVE **6dcd577** deploy@84088055, tick ~84097840–870)
| Room | Notes |
|------|-------|
| W46N8 | RCL7 **31.10%** (3.401M/10.935M); stor~15.5–16.2k ABOVE15k knife-edge; exact2h ~72–78% CLEAR (12h Δp~208k ≈20.2 e/t / ideal26 ≈78%); smA=6; upgFeed why=ok rem SAFE |
| W47N8 | RCL7 **13.89%** (1.519M); stor~16.7–17.7k softCap2 **ON** softLeft~8.3k softBand1 bankWhy=hold leanBank0; hubReady1 hubPrime1 upgKeep2 sealPark1; **contMinPct~46–50 contLow0–1 roadCrit~32** (was 12/4/62 @20:2x); builders1; hMax3; phase=ready |
| Remotes | W45N8 / W45N7 / W47N7 **ALL SAFE**; raidLeft=0; ops.w47n9.on=false phase=fallback ABORT |
| Colony | PEACETIME; war_cmd pause `aborted_by_misaki`; listener single-slot 5:5:1:1 roomSlot rotates; yield gone; CPU~15–17/20 bkt10k; labs OFF labReady propose/actOk (**no re-ask**); softCap widget outstanding (**no re-ask**) |

12h hourly (Timescale): home 29.2%→31.1%; W47 13.05%→13.89% under softCap park (~8.9 e/t vs ideal~30 intentional). Overnight W47 stor dipped ~5k @00:00 then rebuilt.

### Research (community + our stack)
1. **Overmind UpgradeSite:** `storageBuffer=100000` / `energyPerBodyUnit=25000` — scale WORK only above 100k. We park at LEAN_SOFT=25k; soft clear is the right next gate before ceil6 / labs.
2. **Overmind WorkerOverlord:** containers <50% + RoadLogistics critical=25% size `repairTicks` independent of `fortifyDutyThreshold=500k` / `barrierHits[7]=1M`. Our 20:2x 2nd maint when contDebtN≥3 matched that; cont reclaim done. RoadCrit mid-band stays paused under `energyBank` (mvp) — do **not** unpause mid softCap bank (would burn the cushion the soft-band is refilling).
3. **Screeps docs / screepers wiki:** RCL7 unlocks 6 labs + factory; XGH2O upgrade boosts matter once mineral network + buffer exist. Common mistake = flip labs/reactions while storage thrash or repair debt unpaid — we still sit ~17k vs Overmind's 100k buffer.
4. **TooAngel / Harabi remotes:** energy + remotes first; new remotes need spawn budget + Misaki nod. CPU~16/20 with 2 rooms — 3rd room still nod-only and CPU-tight (`docs/CPU.md`).

### Next 1–3 (unchanged order, advanced past debt reclaim)
1. **softCap bank→clear ≥25k** (soft-band park + surplus trim nUp≤3 while stor<25k) — current bottleneck.
2. **On true clear:** nUp→ceil6 / short≥70%; `mvp` off restores roadCrit→0 reclaim (no code change).
3. **seal→1M under soft-gate** after clear sticks; home floor≥15k hold. **Defer** labs KO / boost / industry / market / new remotes (**no re-ask**).

### Shipped
**Nothing** (docs + ROADMAP only). SoftCap / leanBank / sealMinE / HUB_LINK / labs / industry / market / war_* / listener **unchanged**.

## 2026-11-05 20:2x — 12h strategic review (post-W47N9 peacetime / severe cont debt)

**Question:** After W47N9 abort (~17:30 Asia/Shanghai) and peacetime handback, does the softCap→clear→seal order still hold, and is post-war container/road debt bad enough for a small safe ship? SoftCap/labs/industry/market widgets outstanding — **never re-ask**. Do not restart war_*.

**Answer: YES order holds; ship 2nd maint builder for severe debt.** SoftCap bank (intentional ~20k, softLeft~5k) + soft-band park + sealPark remain correct. Gap: 14:4x armed the 1st maint under partial spawn, but live contMinPct slid **20→16→12** (contLow4) and roadCrit~62 with builders=1 working~14% — container decay (~50 hits/t × N) was winning. Overmind sizes workers from repairTicks (containers <50%) up to MAX_WORKERS=5, independent of fortifyDutyThreshold=500k / storageBuffer=100k. TooAngel keeps repair warm while upgrade parks. Our LEAN_SOFT=25k is far below Overmind's 100k buffer → labs/boost/industry stay deferred (no re-ask).

### Live (~20:20–20:24 Asia/Shanghai, tip 0cafc00, tick ~84087960–88020)
| Room | Notes |
|------|-------|
| W46N8 | RCL7 ~29.20% (3.193M/10.935M); stor~15.7k ABOVE15k; exact2h recovered CLEAR post-war; smA=6 |
| W47N8 | RCL7 ~13.05% (1.427M); stor~19.8–20.2k softCap2 ON softLeft~5k softBand1 bankWhy=hold leanBank0; hubReady1 hubPrime1 upgKeep2 sealPark1; **contMinPct~12 contLow4 roadCrit~62**; builders1; hMax4 |
| Remotes | W45N8 / W47N7 / W45N7 SAFE (QQ); raidLeft=0 |
| Colony | PEACETIME; war_cmd pause `aborted_by_misaki`; listener single-slot 5:5:1:1 roomSlot=W46N8; yield gone; CPU~15–20/20 bkt10k; labs OFF (**no re-ask**); softCap widget outstanding (**no re-ask**) |

### Research
1. **Overmind WorkerOverlord:** `repairStructures` includes owned containers with hits <50% hitsMax; `numWorkers` from `repairTicks + paveTicks (+ fortifyTicks only if assets.energy > fortifyDutyThreshold 500k)`; MAX_WORKERS=5. Fortify to `barrierHits[7]=1e6` is gated separately — repair is not "wait for fat bank".
2. **Overmind UpgradeSite:** `storageBuffer=100000` / `energyPerBodyUnit=25000` — surplus WORK only above 100k. We park at 25k; do not rush labs while thin.
3. **TooAngel / community RCL7:** remotes + energy buffer before lab reaction queues / XGH2O boosts; common mistake = flip labs while storage thrash or repair debt unpaid.
4. **Local:** 14:4x 1st-builder gate stays; raise max maint to 2 only when `contDebtN≥3`.

### Shipped
1. `index.js` maint: `contDebtN≥3 && nB<2 && eAvail≥200` → 2nd `w8builder`.
2. `tests/w47n8.js` 20:2x (≥3 conts → 2nd; 2 conts → stay at 1).
3. SoftCap / leanBank / sealMinE / HUB_LINK / labs / industry / market **unchanged**. **No re-ask.**

**Expect after deploy:** builders 1→2 while contLow≥3; contMinPct climb toward ≥50 then roadCrit fall; softCap climb undisturbed (2 builders ≪ fortify burst).

---
## 2026-11-04 17:4x — soft-band surplus trim (softCap hysteresis nUp4 thrash)

**Question:** SoftCap near-clear / post-clear edge (softLeft <2k, stor~23–25k): do sealPark + soft-band + upgKeep correctly prevent thrash and premature deep seal while short is still recovering? Live cleared @15:57 (25181) then re-armed softCap by 16:26 (22685) — ~30 min bleed — with nUp=4 during soft-band hysteresis.

**Answer: PARTIAL → YES after surplus trim.** sealPark (STRICT softThin <25k) and soft-band park (STRICT se<25k + sticky preempt) were already correct. The gap was softEnergyCap hysteresis (08:4x): softCap2 stays OFF in post-clear [ARM,SOFT) so base nUp stays 3 (good — avoids 3↔2 flicker), but `!softCap2` also armed surplus → nUp=4, and hub+fat ctl skipped the feed-gate ≤3 recycle. Overmind scales WORK only above `storageBuffer=100k`; TooAngel parks upgrade when thin. Gate surplus spawn on STRICT `stor≥LEAN_SOFT && !threatSoft`; recycle keep=3 while `stor<LEAN_SOFT` (soft-band surplus trim). SoftCap/sealMinE/HUB_LINK/labs unchanged. **No softCap re-ask. No labs re-ask. No W47N9 reopen.**

### Live (~17:46 Asia/Hong_Kong, deploy 31c895b, tick ~84065600)
| Room | Notes |
|------|-------|
| W46N8 | RCL7 ~25.40% (2.778M/10.935M); stor~16–17k ABOVE15k; smA=6; 1h progress ~18k ≈82% of ideal26 |
| W47N8 | RCL7 ~11.02% (1.205M); stor**23598** softE0 softCap2**0** softLeft1402 softBand1 softArm22k; hubReady1 hubPrime1 hubLinkE800 upgCeil6 feedOk1; **upgraders=4** upgKeep was0 → **3 after trim**; sealPark1 sealRaise0; contMinPct48 contLow1 roadCrit0; builders1; hMax3 looseE~1.1k |
| Remotes | W45N8 SAFE; W47N7 SAFE; **W45N7 DEFEND InvaderCore** (mission=core, defender arrived@84065499, cont hits90.4k, pauseStart84065370, no structureHitLoss) |
| Colony | peacetime+war fallback; ops.w47n9.on=false phase=fallback; CPU~15–17/20 bkt10k; labs OFF (**no re-ask**); softCap widget outstanding (**no re-ask**) |

Also verified post-31c895b cont reclaim: contMinPct 38→50 (16:59/17:23) → 48 live — residual one cont ~48%, builder=1 armed, roadCrit=0. Not the chosen question; healthy enough.

Thrash proof earlier today: clear 15:57@25181 sealRaise1 nUp4 → 15:59 softLeft77 sealPark1 → 16:26 softCap2 RE-ARM@22685.

### Research
1. **Our stack (pre-fix):** 08:4x softEnergyCap clear@25k / re-arm@22k kept softCap2 OFF in [ARM,SOFT) so base spawn stayed 3. Surplus line used `!softCap2(stor)` — same hysteresis — so surplus armed mid soft-band. Recycle: softCap2→≤2; else feed-gate ≤3 only when `!hubLinkLive || ctlBat < FEED_MIN/2`. Live hubReady1 + ctlBat~1.7k skipped both → nUp=4 drain vs soft-band refill.
2. **Overmind:** `UpgradeSite.settings.storageBuffer=100000` / `energyPerBodyUnit=25000` — upgrade power scales only from energy *above* buffer; `linksRequestBelow=200` keeps logistics topping independently. No surplus WORK while under buffer.
3. **TooAngel:** parks upgrade when storage thin; keeps logistics warm (matches our soft-band STRICT park + HMAX overflow).
4. **Local safety kept:** softCap2 hysteresis still protects base 3 (no 3↔2 flicker). softThin/sealDeepOk STRICT <25k unchanged. soft-band STRICT park + 11:4x sticky preempt unchanged. threatSoft ≤2 unchanged.

### Shipped
1. `index.js` surplus: `!threatSoft() && stor >= LEAN_SOFT` (not `!softCap2`).
2. `index.js` recycle: `storE < LEAN_SOFT` → keep=3 (soft-band surplus trim) before feed-gate.
3. `w8day.upgKeep`: 2=softCap / 3=soft-band trim / 0=clear≥25k.
4. Tests: `w47n8_dayobs.js` hysteresis + hub+fat-bat trim; `w47n8.js` spawn blocks 4th at 23598, allows at 26000.
5. SoftCap / leanBank / sealMinE / HUB_LINK / labs / industry / market **unchanged**. **No re-ask.**

**Expect after deploy:** in post-clear [22k,25k) expect softE0 softCap20 softBand1 **upgKeep3** nUp≤3 (4th recycles); stor re-climbs to ≥25k instead of falling under 22k; true ≥25k still allows surplus toward ceil6.

---

## 2026-11-04 14:4x — post-abort maint spawn under softCap (container debt)

**Question:** After Misaki aborted W47N9 (~14:19 Asia/Hong_Kong), raid recycle left `builders=0` while softCap/leanBank rebuilt W47 stor from ~0→22k. Live `contMinPct` slid 46→38 (`contLow` 2–3) and stayed there; maint spawn required `energyAvailable===cap` AND `Game.time%50`. During soft-band park, fillers keep topping towers/ext so eAvail often sits 3–5.5k/5600 for long stretches — does the full-cap+%50 gate freeze container reclaim post-abort?

**Answer: YES — split the gate.** Container debt (`hits < 50%`) arms a maint `w8builder` at `energyAvailable≥200` with no `%50` throttle. RoadCrit-only (`hits < 25%` on `roads.js`) keeps the stricter full-cap + `%50` (optional polish, not crash). SoftCap/sealMinE/HUB_LINK/labs unchanged. **No softCap re-ask. No labs re-ask. No W47N9 reopen.**

### Live (~14:43–14:49 Asia/Hong_Kong, deploy c8f5082, tick ~84062990–84063067)
| Room | Notes |
|------|-------|
| W46N8 | RCL7 ~24.92%; stor~14.8–15.0k ≈UNDER/floor recovering from war drain ~8.8k; remotes SAFE |
| W47N8 | RCL7 ~10.59%; leanBank0 softCap2 ON softE1 softLeft~2.1k softBand1; hubReady1 hubPrime1 hubLinkE~336 upgCeil6; upgKeep2 nUp=2; hMax4 looseE~7.3k; sealPark1 roadCrit0; **contMinPct38 contLow2**; eAvail~5500/5600 (shy of cap) |
| Colony | peacetime+war fallback; ops.w47n9.on=false phase=fallback; warMode0; CPU~15–16/20 bkt10k; labs OFF (**no re-ask**); softCap widget outstanding (**no re-ask**); neighbor scans PAUSED; W47N9 10m war patrol stays paused |

### Research
1. **Our stack (pre-fix):** Maint shared one gate with seal surplus builders: `energyAvailable===cap && %50`. Seal raise is surplus polish; container decay under softCap bank is income infrastructure (miner stands / haul sinks). Post-abort recycle wiped builders while pauseCivilians/warMode residue drained spawn energy into fillers — eAvail rarely hit exactly 5600.
2. **Overmind:** `WorkerOverlord` sizes workers from `repairTicks` (containers <50% hits fraction) and `RoadLogistics.criticalThreshold` (~0.25) — independent of `fortifyDutyThreshold` / `storageBuffer`. Repair duty does not wait for a full spawn bar.
3. **TooAngel:** keeps a repairer warm under thin storage; logistics/repair ahead of fortify when economy is recovering.
4. **Local safety kept:** Upgrader/hauler/filler floors still win the spawn queue before maint. Seal deep raise still wants full-cap. SoftCap thresholds / leanBank / hubPrime / HMAX valve untouched. RoadCrit stays strict so we do not churn tiny road patches every tick under partial energy.

### Shipped
1. `index.js` maint: contDebt → arm at eAvail≥200; roadCrit-only → full-cap+%50.
2. `tests/w47n8.js`: cont<50% @3200/5600 → w8builder; road-only @3200/5600 → null.
3. SoftCap / leanBank / sealMinE / HUB_LINK / labs / industry / market **unchanged**. **No re-ask.**

**Expect after deploy:** while softCap parks nUp≤2 and eAvail sits shy of cap, a container under 50% still queues one maint builder; contMinPct climbs back toward ≥50 without waiting for a perfect full spawn tick.

---

## 2026-11-04 11:4x — soft-band sticky preempt (post-clear ctl sk)

**Question:** SoftCap clears briefly (≥25k) then storage bleeds 25→21k within minutes even while `ctlBat` stays ≥1200 (holdBand should be ON). 20:4x already made soft-band STRICT `se<LEAN_SOFT` independent of softE — so why do haulers keep feeding ctl through the post-clear dip? Is sticky `memory.sk` the gap?

**Answer: YES — soft-band must preempt sticky ctl/hub.** `sink()` only released sticky *storage* when holdBand dropped; it never broke sticky ctl/hub when holdBand rose. Post-clear haulers kept `sk=ctl` from the ≥25k feed window and ignored the new soft-band park. SoftCap/sealMinE/HUB_LINK/labs unchanged. **No softCap re-ask.**

### Live (~11:42–11:46 Asia/Shanghai, deploy aa18731, tick ~84060380–84060420)
| Room | Notes |
|------|-------|
| W46N8 | RCL7 ~24.70%; stor~16.0–16.1k ABOVE15k; upgFeed why=ok nUp3 work42 energy-bound; 2h soft CLEARED ~84%; remotes SAFE |
| W47N8 | RCL7 ~10.47%; leanBank0 softCap2 ON softE1 softLeft~2.0k softBand1; hubReady1 hubPrime1 hubLinkE~381 upgCeil6; upgKeep2 nUp=4 (2× recycle TTL~800); hMax3 looseE~1.4k nHaul4; sealPark1 roadCrit0 contMinPct50 |
| Colony | peacetime; CPU~16–17/20 bkt10k; labs OFF propose/actOk (**no re-ask**); softCap widget outstanding (**no re-ask**); neighbor scans PAUSED |

3h room_stats: only **2** soft clears (11:15, 11:31 @~25.1k) then fast bleed (11:31 25148 → 11:32 23619 ctl1920 → 11:40 21427). holdBand was true at ctl1920 but park did not retarget.

### Research
1. **Our stack (pre-fix):** 20:4x restored STRICT soft-band `se<25k && ctl≥1200`. Selection path was correct for *fresh* `sk=undefined`. Sticky path returned `was=ctl` whenever ctl had free capacity — holdBand never consulted for non-storage sk. Classic post-clear: sk stuck on ctl from the feed window.
2. **Overmind:** `UpgradeSite.storageBuffer=100k` gates upgrader *scale*; logistics `requestInput`/`bufferChoices` retarget to storage whenever colony assets are under buffer — no sticky sink that ignores the buffer floor. Transport power stays warm while upgrade parks.
3. **TooAngel:** parks upgrade when storage thin; deposit priority stays storage-first under healthy floors.
4. **Local safety kept:** ctl≥1200 gate unchanged (pre-hub deadlock guard when ctl sat at 0). softE hysteresis still nUp-only. sealPark / hubPrime / HMAX valve untouched. Secondary watch: when ctl dips <1200 mid-bleed (live 11:35 ctl1100 @stor22k) holdBand drops — hub→ctl can cover that later if thrash persists.

### Shipped
1. `roles.js` `sink()`: if holdBand && storage free → clear sticky ctl/hub (`was=null`) so park retargets to storage.
2. Tests filler: sticky ctl @23.6k/ctl1920 → storage; sticky hub → storage; ctl hungry <1200 keeps sticky ctl.
3. SoftCap / leanBank / sealMinE / HUB_LINK / labs / industry / market **unchanged**. **No re-ask.**

**Expect after deploy:** next soft clear → first dip under 25k with ctl≥1200 retargets haulers to storage within one load (no multi-minute 25→21k bleed from sticky ctl); softLeft drain resumes; softE re-arm under 22k less often.

---

## 2026-11-04 08:4x — W47 link-era HMAX overflow valve (softCap bank)

**Question:** Under softCap+leanBank, W47 keeps `looseE` ~3–5k (source-B south cont+drop, A overflow when ctl battery fat) while link-era `HMAX=3` is saturated and bank climb is slow. The surplus line comments "4th when >2k piles" but `Math.min(HMAX=3, 4)=3` made that dead. Should link-era HMAX allow a 4th hauler when loose is chronically high — matching Overmind logistics-still-moves-while-upgrade-parks?

**Answer: YES — dynamic link HMAX: 3 steady / 4 while `looseE>2000`. Floor stays 2. SoftCap / leanBank / seal / labs unchanged. No softCap re-ask.**

### Live (~08:48–08:52 Asia/Hong_Kong, deploy 9df28e6, tick ~84057860–84057923)
| Room | Notes |
|------|-------|
| W46N8 | RCL7 ~24.18%; stor~15.1–15.8k ABOVE; 2h soft ~67–70%; remotes SAFE post-W45N7 Invader clear |
| W47N8 | RCL7 ~10.09%; leanBank1 bankLeft~4.7–5.4k softCap2 ON softLeft~9.7–10.4k softBand1; hubReady1 hubPrime1 upgKeep2 nUp=2; **nHaul=3 @HMAX**; **looseE~4.2–4.8k** (B cont~1.6k + drop~1.8k); model waste_other~8.7; contMinPct~46–48 contLow2 roadCrit0 sealPark1 |
| Colony | peacetime; CPU~14–17/20 bkt10k; ~37–39 creeps; labs OFF (**no re-ask**); neighbor force scan PAUSED; softCap widget outstanding (**no re-ask**) |

src_A meter ~0.07 is the **link-era harvest artifact** (A→ctl link, not idle mine). B has no link — overflow is real.

### Research
1. **Our stack (pre-fix):** 02:4x raised link HMAX 2→3 as overflow valve. Surplus rule still said `loose>2000 → 4`, but `Math.min(HMAX, 4)` with HMAX fixed at 3 never spawned a 4th. Soft-band correctly parks to storage when ctl≥1200; the pipe was CARRY-bound at 3×10C vs south B path + decay.
2. **Overmind:** `UpgradeSite.storageBuffer` gates **upgrader scale** only. `TransportOverlord.neededTransportPower()` sizes transporters from mining `energyPerTick × distance` (± upgrade battery) **independent** of storageBuffer. Logistics `requestOutput` on saturated mining containers continues while upgrade parks; transporters deposit excess at storage/`bufferChoices`.
3. **TooAngel / Screeps docs:** excess belongs in storage, not decaying at sources. Keep upgrade parked under soft floor; keep logistics warm.
4. **Local safety:** softCap≤2 / leanBank upgKeep / soft-band STRICT park / sealPark / hubPrime already protect the cushion. A transient 4th hauler (+~0.5–1 e/t upkeep while piles>2k) only accelerates bank refill; ages out when loose drains below 2000 (HMAX→3).

### Shipped
1. Link-era `HMAX = looseE>2000 ? 4 : 3` (floor `hFloor=2` unchanged).
2. `w8day.hMax` observability.
3. Tests: 3rd under soft-cap still; **new** 4th when 3 haulers + loose>2000.
4. SoftCap / leanBank / sealMinE / HUB_LINK / labs / industry / market **unchanged**. **No re-ask.**

**Expect after deploy:** with looseE>2k → spawn 4th w8hauler → B cont+drop drain into storage via soft-band; bankLeft/softLeft fall faster; looseE→<2k → HMAX back to 3; waste_other shrinks. No softCap/labs decision needed.

---

## 2026-11-04 05:4x — leanBank rebuild-band upgKeep (post-defense dual-stack)


**Question:** After Invader/remote DEFEND drain re-arms leanBank (stor dipped below `LEAN_ARM` 15k), leanBank kept nUp at **0/1 until stor≥20k** even though softCap already caps ≤2 and soft-band+sealPark protect the climb. Live spent hours at ~8 e/t upgrade in the 15–18k band. Should post-minBuild leanBank in `[LEAN_ARM, LEAN_STOR)` allow softCap parity (≤2) instead of hard 0/1?

**Answer: YES — band leanBank upgrader ceiling. Emergency `<LEAN_ARM` → ≤1; rebuild `[15k,20k)` while leanBank sticky → ≤2 (= softCap). SoftCap/sealMinE/HUB_LINK/labs unchanged. No softCap re-ask.**

### Live (~05:45 Asia/Hong_Kong, deploy c5334c8, tick ~84055220)
| Room | Notes |
|------|-------|
| W46N8 | RCL7 ~23.74% (2.596M/10.9M); stor~16.0–16.7k ABOVE; 2h prior~76–80%; last1h ~14.2 e/t (ideal~26); remotes SAFE post-W45N7 InvaderCore kill@~84054839 |
| W47N8 | RCL7 ~9.85% (1.077M); **leanBank=1** bankLeft~2.8k bankWhy=bank; softCap2 ON softLeft~7.8k softE1 softBand1; **hubReady1 hubPrime1** hubLinkE~369 upgCeil6; sealPark1 roadCrit0 contMinPct50; **upgraders=1**; last3h ~8.7 e/t (prior3h ~13.7); last1h ~8.4 |
| Colony | peacetime; CPU~12–15/20 bkt10k; ~35 creeps; labs OFF propose=1 actOk (**no re-ask**); K regener miners0; neighbor scan PAUSED |

6h stor path: ~00:30 W47 ~23.5k near-clear → thrash 19–22k (02:4x LEAN_ARM prime) → **~03:00 dip ≤15k** (Invader episode drain) → leanBank re-arm → stuck 15–18k with nUp≤1 for ~2.5h while softLeft stayed ~7–10k.

### Research
1. **Our stack (pre-fix):** leanBank sticky 15→20k with hard nUp 0/1, THEN softCap 20→25k with ≤2. Dual freeze after every defense dip below ARM.
2. **Overmind UpgradeSite:** `storageBuffer=100k`; spawn upgraders only when assets > buffer (or downgrade <500); scale WORK by surplus — **single** threshold, never dual-stack 0/1 then ≤2 at a second lower band.
3. **TooAngel:** storage-centric upgrader; parks when thin / not healthy but keeps a floor — does not zero upgrade for a 5k cushion chase once past emergency.
4. **Local safety already present in [15k,25k):** soft-band STRICT park to storage (ctl≥1200); sealPark; hubPrime LEAN_ARM; softCap≤2. Hard 0/1 only adds upgrade freeze, not cushion safety.
5. **Hub live:** with hub→ctl ~40 e/t gross, 2×10W is feed-safe (live ctlBat~2.5k feedOk with 1; 02:4x thrash ran ≤2 without crash).

### Shipped
1. `leanUpKeep(storE)`: `<LEAN_ARM → 1`, else `2`.
2. `leanBankRecycle` uses `leanUpKeep` (was hard `keep=1`).
3. Spawn energyBank branch: `<LEAN_ARM` → 0/1 (downgrade); `[ARM,STOR)` → **2**.
4. `w8day.upgKeep` obs (1 emergency / 2 rebuild|soft / 0 clear).
5. Tests dayobs: emergency 12k ≤1; rebuild 17.2k ≤2 (recycle exactly 1 of 3).
6. SoftCap / sealMinE / HUB_LINK / labs / industry / market / softCap widget **unchanged**. **No re-ask.**

**Expect after deploy:** stor in [15k,20k) leanBank sticky → `upgKeep=2` / nUp→2; bank climb continues via soft-band; W47 e/t should leave ~8 toward softCap-band ~12–16; softLeft drain resumes without waiting full 20k first.

---

## 2026-11-04 02:4x — hub ferry prime arm LEAN_ARM (thrash band)


**Question:** SoftCap thrash often parks W47 storage in the common **19–22k** band for hours. Ferry prime-only was armed at `LEAN_SOFT_ARM(22k)` — does that leave `hubPrime=0` / `hubLinkE=0` through the thrash while filler idles at POST with full carry, recreating the cold-hub gap 23:4x tried to close?

**Answer: YES — lower prime arm to `LEAN_ARM(15k)`. SoftCap hysteresis stays 22k. Bat ferry still ≥25k.**

Live ~02:28–02:43 Asia/Hong_Kong deploy `0483c6b`: peacetime; W47 ~9.6% softCap2 ON softLeft~3.5–4.8k stor~19.4–21k thrash; **hubReady1 hubPrime flaps 0↔1**; filler at POST with ~1200e idle while hubLinkE=0; model_w8 upg ~14/30 waiting_feed~0.23 hub deliv~21.6 ctl~6.9. Soft-band fight is bat-driven (drain vs refill); prime-only is one-shot ~200e then stable (SEND idle while ctlBat fat under softCap nUp≤2).

**Sources:** Overmind UpgradeSite `linksRequestBelow=200` is storageBuffer-agnostic (top link whenever under threshold). Home `queen.standby` uses defender/lean floor (~LEAN_ARM). TooAngel keeps logistics warm while upgrade parks when thin. SoftCap sticky `LEAN_SOFT_ARM` itself must stay 22k (08:4x hysteresis) — do NOT couple softE re-arm to ferry.

**Shipped:**
1. `fill.js` ferry: prime arm `LEAN_SOFT_ARM(22k)` → `LEAN_ARM(15k)`; soft bank still prime-only (`hubE < HUB_SEND`); soft clear still bat ferry.
2. Tests filler (H): below-ARM now 14k; **new thrash-band 19.5k MUST prime**.
3. SoftCap / sealMinE / HUB_LINK / labs / industry / market **unchanged**. **No softCap re-ask.**

**Expect after deploy:** stor in [15k, 22k) → `hubPrime=1` (once hubE≥200); thrash no longer cold-hub; post-clear waiting_feed still should not spike from empty hub.

---

## 2026-11-03 23:4x — hub-link PRE-WARM during softCap bank

**Question:** With `HUB_LINK` LIVE (`hubReady1` / upgCeil6) but softCap2 intentional bank (stor climbing ~19–21k, short≈0), the idle hub ferry only armed at stor≥25k — does post-clear raise WORK before hub→ctl is warm, recreating waiting_feed?

**Answer: YES gap — prime the hub link in soft-band.** Ferry gate moved to `LEAN_SOFT_ARM(22k)` with prime-only (`hubE < HUB_SEND=200`) while `stor < LEAN_SOFT`; full bat-driven ferry (`bat<800 || hubE<200`) only after soft clear. Matches Overmind UpgradeSite `linksRequestBelow=200` (top link independent of storageBuffer climb).

**Live (~23:28–23:41 Asia/Hong_Kong, deploy 3310be3):**
- Peacetime; home RCL7 ~22.71% 2h~91.4% soft CLEARED stor~14.2k UNDER15k consec-under=1; W47 RCL7 ~9.28% flat 2h~41.3% softCap2 ON softE1 softLeft~5.2–5.5k stor~19.5–20.6k climbing consec-soft70=2 short≈0; **hubReady1 hubLinkLive link 33,34 upgCeil6 feedBound0 hubLinkE=0** (pre-fix); remotes SAFE; labs OFF; roads.phase=done; CPU~12–18 bucket10k.

**Shipped:**
1. `fill.js` ferry: arm ≥22000; soft bank prime-only; soft clear bat ferry.
2. `w8day.hubPrime` (1 when hubReady && hubLinkE≥200) — patrol sees pre-warm.
3. Tests filler (H) + dayobs hubPrime.
4. **No** HUB_LINK / labs / industry / market / sealMinE flips; **no** re-ask.

**Expect after deploy:** once stor≥22k during bank → `hubPrime=1` before clear; on clear, first hub→ctl SEND already buffered (cooldown 20 already payable); post-clear waiting_feed should not spike from cold hub.


## 2026-11-03 — HUB_LINK nod YES (armed)

**Misaki nodded YES** for W47N8 hub link (枢纽链路). `config.HUB_LINK=true`. Labs / `RCL7_INDUSTRY` / market stay OFF. `sealMinE` stays **25000** (`LEAN_SOFT`). softCap sticky / `LEAN_SOFT_ARM` unchanged. 20:4x soft-band stays STRICT `se < LEAN_SOFT` (independent of softE).

Live path (plumbing from 23:4x / 05:4x, now ungated):
1. `layoutRun` places the link site at **33,34** (~5k), beside hub container 33,33. RCL5 links 13,25 and 26,12 unchanged.
2. While the site stands, `hubLinkLive` is false → `w8day.hubReady=0`, `upgCeil` stays 2 (`siteRem≥3000`) or 3, recycle keeps ≤3. `w8day.hubLink=1` as soon as the flag is live. The 5k site is bigBuild, so surplus spawn stays at 2 until it stands.
3. Structure stands → `hubReady=1`, filler ferry + `linkRun` hub→ctl, `upgCeil` 6, `feedBound=0`.

## 2026-11-03 20:4x — softCap re-ON drain (soft-band ≠ softE)

**Question:** With softCap2 re-ON after clears ~25–26k (patrol softLeft~3k → live softLeft~1k), and feedBound already diagnosed — what autonomous drain still pulls W47 storage back under softArm (22k)? sealRaise mid-clear, SEAL_EDGE 2nd builder, hub drop pile, hauler soft-band, mineral haul, or home/colony balance?

**Answer: hauler soft-band was wrongly tied to softE hysteresis.** Seal soft-gate works; sustained bleed in post-clear [22k,25k) was nUp3 + park OFF. Restored STRICT soft-band at LEAN_SOFT; softE stays nUp-only.

### Live (~20:44–20:50 Asia/Shanghai, t~84047400, deploy adcc35f → this ship)
- Peacetime; home RCL7 ~22.18% 2h~22.2/26 (~85%) stor~15k ABOVE; W47 RCL7 ~8.96% stor**24000** softE=1 softCap2=1 softLeft1000 softArm22k nUp2; KEY DONE; **sealRaise0 sealPark1** gate~477k→1M; hubReady0; contMinPct50 roadCrit0; feedBound0 (soft ON); looseE~571; remotes SAFE; labs OFF propose=1 actOk=1; w8min miners0 / term K~92 homeTermK~34k; CPU~14–15/20 bkt10k.
- 6h stor: clears ≥25k @~17:39 (26.0k), ~18:14 (25.0k), ~19:26 (25.0k) then bleed through [22k,25k) until softE re-arms <22k. One deep dip ~18:48–18:58 (24k→16k, ctl→0) looks like a spawn/delivery stall, not steady seal.
- Builder live at ~15,26 (ctl-side maint), **not** north seal y=3 — matches sealPark.
- Hub cont 33,33 empty; earlier hub-drop ~1.9k was transient (not the multi-hour softArm breach).

### Drain matrix
| candidate | live evidence | sustained softArm breach? |
|---|---|---|
| sealRaise mid-clear | sealPark1 / sealRaise0 below 25k; softThin parks | brief window only while ≥25k (1 builder, SEAL_EDGE blocks 2nd until 30k) — **not** the [22k,25k) bleed |
| SEAL_EDGE 2nd builder | edgeFat needs sealMinE+5k=30k | no — never armed in this band |
| hub drop pile | looseE~0.6k; hub cont 0 | transient accounting, not hours-long |
| **hauler soft-band** | 08:4x followed softE → park OFF in post-clear [ARM,SOFT) while nUp3 | **YES** — primary autonomous drain |
| mineral haul | w8min miners0 / gaps=miner | no |
| home balance | home ~15k stable ABOVE | no cross-room pull |

### Overmind / TooAngel
- **Overmind** `UpgradeSite.settings.storageBuffer=100k` + logistics `requestInput` while battery <50–75%: keep topping the reserve while upgrade is fed. **WorkerOverlord.fortifyDutyThreshold=500k** parks routine fortify until fat — our seal soft-gate already mirrors that; measured seal is parked under softThin.
- **TooAngel** healthy/storage floors park upgrade when storage thin. We keep softE hysteresis for nUp (avoid 3↔2 thrash) and only restore haul park under the soft floor.
- Coupling park to softE fought the soft floor: after a clear, nUp3 correctly held, but surplus haul went to ctl instead of storage → stor walked down to softArm.

### Shipped
1. `roles.js` soft-band / holdBand: STRICT `se < LEAN_SOFT` (25000) + ctl≥1200 — **independent of softE**.
2. `w8day.softBand` — 1 when `storE < LEAN_SOFT && ctlBat ≥ 1200` (patrol sees park≠softE in the hold band).
3. Tests filler (23k softE=0 → storage) + dayobs softBand with ctl battery.
4. **No** HUB_LINK / labs / industry / market / sealMinE flips; **no** re-ask.

### Patrol watch
- After deploy: in [22k,25k) post-clear expect `softE=0 softCap2=0 softBand=1` (nUp3 + park ON) — stor should re-climb to ≥25k instead of falling under 22k.
- `softE=1 softBand=1` while climbing from <22k is normal.
- `sealPark=1` whenever stor<25k; sealRaise only above clear with park cleared.
- feedBound returns when soft clears + nUp≥3 and the hub link is not yet live. HUB_LINK nod landed after this review (see top).

---

## 2026-11-03 17:3x — post-roadCrit feed ceiling (!HUB_LINK)

**Question:** With softCap clear (stor≥26k), roadCrit drained to 0, contMinPct≥50, and sealRaise re-armed — is W47 upgrade still at the A→ctl feed ceiling, proving further softCap/seal/road tuning will not close the ~9 e/t gap (only `HUB_LINK` will)?

**Answer: YES — feed-bound at non-hub WORK30.** softCap/roadCrit/cont debt are DONE; seal→1M at ~1.8 e/t is not the upgrade bottleneck. Remaining unlock = Misaki nod `HUB_LINK` (plumbing + hubLinkLive ceil gate already LIVE — **do not re-ask**).

### Live (~17:27–17:40 Asia/Shanghai, t~84044500–84044700, deploy 5d902ed)
- Peacetime; home RCL7 ~21.65% 2h~21/26 (~80–87%) stor~13–16k floor_bank (W45N7 DEFEND dipped home briefly); W47 RCL7 ~8.36% stor**26032** softE=0 softCap2=0 softLeft0 nUp3 feedOk ctlBat~1983; KEY DONE; sealRaise**1** sealPark0 gate~485k→1M; hubReady0 hubLink0; contMinPct=50 contLow0 **roadCrit=0**; remotes SAFE (W47); labs OFF propose=1 actOk=0 (homeStor~14.5k); K regener / homeTermK~34k; CPU~13/20 bkt10k.
- Model 6h (`tools/model_w8.py`): ideal **30.08** / actual **20.74** (~69%); delivered **hub 20.44 vs ctl 10.48**; waiting_feed **0.16**; WORK **30**; alloc build_repair **1.76** (seal) / upkeep 11.8 / waste_other 2.4; harvest ~37.
- 24h trend: W47 4.5%→8.4% (~+3.9pp); home 17.7%→21.7%. 3h e/t: home ~22.7 / W47 ~20.8.

### Gap analysis
| lever | status | closes ~9 e/t gap? |
|---|---|---|
| softCap / hysteresis | CLEAR (stor 26k, softE=0) | no — already nUp3 |
| contMinPct / roadCrit | **DONE** (50 / 0) | no — 14:4x + 11:3x succeeded |
| seal→1M soft-gate | re-armed (sealRaise1) | no — only 1.76 e/t build; Overmind fortifyDuty parks fat fortify, our soft-gate already protects softCap |
| A→ctl only (no hub) | LIVE | **YES bottleneck** — ctl ~10 e/t vs hub ~20; WORK30 waiting_feed 16% |
| HUB_LINK hub→ctl | plumbing LIVE; flag false | **only remaining unlock** (~+ hub→ctl ~38 e/t net capacity once live) |

### Overmind / TooAngel
- **Overmind UpgradeSite**: places upgrade link when storage path >10; `linksRequestBelow=200`; battery input at `upgradePowerNeeded`; WORK scales off `storageBuffer=100k`. Our LEAN_SOFT 25k + `upgCeil=3` without `hubLinkLive` is the tight-buffer analogue; hub→ctl matches UpgradeSite link topology (home `managers/links.js` already).
- **Overmind WorkerOverlord** `fortifyDutyThreshold=500k`: routine fortify only when fat — we already soft-gate seal; measured seal spend is small vs the feed gap.
- **TooAngel**: storage-centric hub; we stay ctl-centric — flip still needs the 5k hub link site + ferry (23:4x/05:4x shipped).

### Shipped
1. `w8day.upgCeil` — effective ceil (2/3/6) mirroring spawn/`hubLinkLive`.
2. `w8day.feedBound` — 1 when `!hubLinkLive && !softCap2 && !war && nUp≥ceil` (at non-hub WORK ceiling). Patrol signal: do not re-chase softCap/seal/roads for the upgrade gap.
3. Tests dayobs (no-hub feedBound=1; hub live clears; softCap clears feedBound).
4. **No** HUB_LINK / labs / industry / market flips; **no** re-ask.

### Patrol watch
- `feedBound=1` + `roadCrit=0` + softCap clear → expect 2h upg stuck ~68–72% until HUB_LINK nod.
- After Misaki nod: siteRem~5k → upgCeil 2 (bigBuild) → stand → `hubReady=1` / `feedBound=0` / upgCeil 6; waiting_feed↓; short≥70%.
- sealRaise may stay 1; builder on seal is fine while feedBound=1.
- labs: actOk still gated on homeStor≥15k — do not re-ask.

---

## 2026-11-03 14:4x — roadCrit before deep seal (Overmind critical=25%)

**Question:** contMinPct hit ≥50% after 11:3x — with softCap clear + sealRaise, is deep seal→1M starving `roadCrit`, and should critical roads outrank fortify like Overmind RoadLogistics?

### Live (~14:40–14:45 Asia/Shanghai, t~84042100, 5de0c2e)
- Peacetime; home ~21.15% stor~14.3–15.6k floor_bank 2h~22.8 e/t (~88% of ideal26); W47 ~7.90% stor~25.4k softE=0 softCap2=0 softLeft0 nUp3 feedOk; KEY DONE; sealRaise1 sealPark0 hubReady0; remotes SAFE; labs OFF no re-ask; K regener~29.9k.
- Containers: all five **50–53%** (`contMinPct=50`, `contLow=0`) — 11:3x SUCCESS.
- Roads: **38 <25% / 69 <30% / 94 <50%** (`roadCrit=33–38`). Builder sticky on seal wall **27,3 @~542k** (sealMin~488k).

### Gap
Repair order after 11:3x: urgent10% → cont50% → **wallJob** → road25% → road60%. Once softCap cleared, `sealDeepOk` made `wallJob` return deep seal→1M every rescan; sticky rj on walls never hits 0.95×hitsMax. Roads in the 10–25% band never won.

### Overmind / TooAngel
- **Overmind** `fortifyDutyThreshold=500000` — routine fortify ticks only when colony energy is fat; `RoadLogistics.settings.criticalThreshold=0.25` is an independent paver duty.
- **TooAngel**: dedicated wall `repairer`; economy creeps keep roads/containers — fortify must not monopolize the lone maint builder.

### Shipped
1. Order: urgent → cont50% → **`roadNeed(0.25)`** → `wallJob` → road60% (mvp still skips mid-band).
2. Break sticky when `roadCritNeed` and sticky target is wall/rampart.
3. Maint spawn road threshold **20%→25%** (align `w8day.roadCrit`).
4. Tests: roadCrit prefers over seal + sticky-break. Under-attack seal path unchanged.

### Patrol watch
- `roadCrit` should fall from ~38 toward 0 over ~1–2 builder TTLs; `contMinPct` stay ≥50; sealRaise may stay 1 but builder should not sticky-seal while roadCrit>0.
- Do **not** re-ask HUB_LINK / ops.labs.

---

## 2026-11-03 11:3x — W47 container repair debt (Overmind <50% before roads)

**Question:** KEY DONE + softCap sticky clear (~24.5k) + one live builder — why are ctl/hub/minCont at ~23–25% hits (~1.3–1.4h of container decay left) while ~140 roads sit under 50%?

### Live (~11:38–11:45 Asia/Shanghai, t~84039480, 613a205)
- Peacetime; home ~20.6% stor~14.5k UNDER floor_bank; W47 ~7.4% stor~24.3k softE=0 softCap2=0 softLeft~0.7k; KEY DONE; sealPark1; hubReady0; nUp4 feedOk; labs OFF no re-ask; K regener~32.5k ticks.
- Containers: minCont(37,44) **23.1%**, ctl(13,26) **25.1%**, hub(33,33) **25.2%**; source conts ~50% (miner underfoot already).
- Roads: 4 <25% / 52 <30% / **139/142 <50%**.

### Gap
Builder maintenance used a single `rr(f)` over `CONTAINER|ROAD` with `findClosestByRange`. With seal walls already ≥STAGE3 (`wallJob`→null) and urgent `<10%` empty, the builder spent its life on the nearest mid-band road. Sticky `c.memory.rj` assignment from 10-21 had drifted into the trailing comment, so every tick re-picked the closest road. Ctl battery had **no** standee repair (unlike source/minCont miners at `<50%`).

### Overmind / TooAngel
- **Overmind** `WorkerOverlord.repairStructures`: owned-room containers when `hits < 0.5 * hitsMax`, listed **before** paving and fortify. `RoadLogistics.settings.criticalThreshold=0.25`, `repairThreshold=0.9`.
- **TooAngel**: dedicated `repairer` for walls/ramparts; economy creeps still keep containers healthy — same split we want (containers ≠ fortify).

### Shipped
1. **Split pools:** `contNeed(f)` / `roadNeed(f)`. Order: cont/road `<10%` → **containers `<50%`** → `wallJob` → roads `<25%` → roads `<60%` (mvp/leanBank: urgent + containers only before park).
2. Restore sticky `rj`/`rjt` and **break sticky** when a container is under 50% and the sticky target is not a container.
3. **One** ctl-stand upgrader (lexicographically first in range) repairs ctl cont `<50%` instead of upgrading that tick.
4. Maint spawn: containers `<50%` **or** kept roads `<20%` (was both `<20%`).
5. Obs: `w8day.contMinPct`, `contLow`, `roadCrit`. Test `tests/w47n8_repair_prio.js`.

### Patrol watch
- `contMinPct` should climb toward ≥50% within ~1–2 builder TTLs; `roadCrit` drains after batteries are safe.
- Do **not** re-ask HUB_LINK / ops.labs.

---

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

## 2026-11-01 02:4x — leanBank hysteresis + soft-cap

**Question:** Why did leanBank thrash ready↔bank20 within ~1 h and then fail to rebuild the 20k cushion under W47N7 DEFEND?

**Answer: Add 15k re-arm hysteresis + ≤2 upgrader soft-cap while stor < 25k. Do NOT flip gates.**

### Live
- ready@~00:14 stor~23k → 4 upgraders; dn20@~01:06; re-arm@~01:25 stor~16k; DEFEND@~01:28 → stor~1.7k by ~02:40; prog frozen@74778.
- Drain after upg=0 is income collapse (remote pause + soft local) + defender spawn fill — bankEta@20e/t lies while `bankWhy=threat`.

### Overmind
- `storageBuffer` 100k; upgraders only when assets > buffer; WORK scales with surplus. Our 20k is intentional but needs hysteresis.

### Shipped
- `LEAN_ARM=15k` / `LEAN_SOFT=25k`; recycle ≤2 soft / ≤1 bank; `w8day.bankWhy/bankArm/bankSoft`.
- Tests dayobs + move_bank. **No gate flips. No home throttle.**

## 2026-11-01 05:4x — soft-cap survives RCL6_MINERALS flip

**Question:** After Misaki nods and we flip the gate, does the 02:4x `LEAN_SOFT` soft-cap still protect the post-minBuild window when stor is spent into ~110k terminal+minCont sites?

**Answer: No — soft-cap was gated behind `!RCL6_MINERALS`. Extend it past the flip. Do NOT flip gates this run.**

### Live
- t~83992670: phase=ready hold stor~18k; flipReady=0 (stor20k+homeStor); W45N7 DEFEND core; home ~11.9% stor thin; 04:57 propose stale.
- Overmind `storageBuffer` is mineral-agnostic; our soft-cap must match that shape at a tighter 25k.

### Shipped
- Drop `!C.RCL6_MINERALS` from spawn soft-cap + `leanBankRecycle`. leanBank≤1 still wins during minBuild.
- Tests dayobs post-gate soft recycle @5k. **No gate flips.**

## 2026-11-01 08:4x — hold-band sink finishes stor20k

**Question:** Soft-cap + hysteresis left W47 in `bankWhy=hold` at stor~16–18k with flipGaps only `stor20k`, while ~6–7k sat in source conts (`w8lo7`). Why does the cushion never land in storage?

**Answer: `sink()` ctl/hub-first after filler buffer met starves storage in the 15–20k band. Prefer storage while hold-band + ctl≥1200. Do NOT flip gates.**

### Live
- t~83995200 (~08:40 Asia/Hong_Kong): storE~16.7k bankLeft~3.3k leanBank=0 hold soft≤2; homeStor~18k; remotes SAFE; CPU~14/20.
- 3h: home ~18 e/t ABOVE; W47 ~12 e/t under soft-cap; stor oscillates under 20k.
- Overmind parks assets in storage (`storageBuffer`); our ctl-first fights flipReady.

### Shipped
- Hold-band sink in `roles.js` (LEAN_ARM–LEAN_STOR + ctl≥1200 → storage; sticky kept).
- `w8day.looseE` obs. Tests filler hold-band + dayobs. **No gate flips.**

## 2026-11-01 11:4x — first-K send pacing (post-minBuild)

**Question:** After `RCL6_MINERALS` flip + minBuild, will `SEND_BATCH=5000` + `termFuel` stor≥2000 stall the first K send (`noE`) while colony stor sits ~5–8k?

**Answer: Yes risk. Thin-batch 1k under LEAN_ARM + termFuel stor floor 500. Obs batch/homeFree/fee. Do NOT flip labs/industry.**

### Live
- t~83998040 (~11:47 Asia/Hong_Kong): W47 minBuild siteRem~79k stor~5.5k leanBank=1; home stor~15k ABOVE-ish; remotes SAFE; deploy b758f38.
- Adjacent fee ≈33e/1k; home terminal free~173k OK.

### Shipped
- `SEND_BATCH_THIN=1000` when storE < LEAN_ARM; `TERM_FUEL_STOR=500`; `w8min.{batch,homeFree,fee}`; tests. Detail: `docs/MINERAL_DEFENSE_ROADMAP.md` §5.17.

## 2026-11-01 14:4x — home KO labReady propose

**Question:** After minBuild + first thin-batch K arrives home, is the dormant KO reaction pipeline complete, and when should patrol **propose** `Memory.ops.labs={W46N8:'KO'}`?

**Answer: Pipeline complete (labs.run + hauler.labRun + send). Ship `Memory.ops.labReady` with propose at K≥1000. Do NOT auto-set ops.labs. Reaction needs no lab energy.**

### Live
- t~84000540 (~14:40 Asia/Hong_Kong): W47 minBuild siteRem~36k stor~3.4k leanBank=1; home stor~17.8k term K=0 O~127k; remotes SAFE; CPU~14.6/20.
- ETA: minBuild ~1.8h + mine first 1k K ~5h ≈ **~7 h** to first propose.

### Shipped
- `labs.readyObs` → `Memory.ops.labReady`; stale carrier comments fixed; tests. Detail: `docs/MINERAL_DEFENSE_ROADMAP.md` §5.18.

## 2026-11-01 17:4x — w8mminer vs soft-cap spawn priority

**Question:** After minCont stands and leanBank drops, will spawn raise `w8mminer` under thin stor + soft-cap ≤2, or do upgraders starve mineral start?

**Answer: Old queue put mminer last (after remotes) — soft-cap would win. Elevate mminer after economy floors / before soft upgraders (Overmind mineral 520 < upgrade 600). Do NOT set ops.labs.**

### Live
- t~84003240 (~17:45 Asia/Hong_Kong): terminal DONE; minCont siteRem~1.7k leanBank=1 stor~12.3k; home~16k ABOVE; remotes SAFE; labReady noK.
- Detail: `docs/MINERAL_DEFENSE_ROADMAP.md` §5.19.

### Shipped
- Elevate `w8mminer` spawn; `w8min.minerPrio=1`; soft-cap priority test. **No gate / labs flips.**

## 2026-11-01 20:4x — post-minBuild leanBank re-arm + rebuild-band

**Question:** After terminal+minCont stand, why does leanBank stay permanently off (`bankWhy=gate`) while stor collapses to ~3–5k? Is soft-cap ≤2 enough to rebuild the 20k cushion?

**Answer: Drop §5.13 permanent gate-off; keep 15/20k hysteresis post-gate; extend hold-band sink to rebuild-band (stor<20k + ctl≥1200). Do NOT set ops.labs.**

### Live
- t~84005916 (~20:47 Asia/Hong_Kong) pre-deploy: W47 stor~4.2k leanBank=0 bankWhy=gate phase=ready bankLeft=0; w8mminer=1 K~30k@deposit; home~19.3k ABOVE termK=4444 labReady.propose=1; remotes SAFE; CPU~15/20.
- Root: `if (RCL6_MINERALS && !minBuild) return false` + ctl-first sink below ARM never parks energy; soft-cap alone feeds 2 upgraders forever.
- Overmind `storageBuffer` is gate-agnostic — match that shape at our tighter 15/20k.

### Shipped
- Remove permanent post-minBuild leanBank disable; honest phase/bankLeft/bankWhy; rebuild-band sink; flipGaps skip stor20k when already; tests. Detail: `docs/MINERAL_DEFENSE_ROADMAP.md` §5.20.
- **No labs/industry/market flips; ops.labs still Misaki.**

## 2026-11-01 23:4x — thin-K + KO lab activation sequence

**Question:** With W47 in the 15–20k hold band, `labReady.propose=1`, and homeTermK≥9k, what is the safest order to start KO reaction without starving RCL7 upgrade?

**Answer: Nod `ops.labs={W46N8:'KO'}` now is safe — reaction needs no lab energy and does not throttle upgrade (Overmind/TooAngel). Prefer actOk (homeStor≥15k, kTerm≥3k). Boost still waits KO≥900. Do NOT auto-set.**

### Live
- t~84008500 (~23:44 Asia/Hong_Kong): home ~14.8% stor~15.4k upg~22.5 e/t termK~9.1k; W47 ~2.2% stor~18.9k hold soft upg~12 e/t; labReady propose=1 ops.labs null; remotes SAFE; CPU~14.7/20.

### Shipped
- `labReady` actOk/actGaps + ko/homeStor obs; tests. Detail: `docs/MINERAL_DEFENSE_ROADMAP.md` §5.21.
- **No labs/industry/market flips; ops.labs still Misaki.**

## 2026-11-02 02:4x — link-era HMAX vs soft-cap backlog

**Question:** Under soft-cap ≤2 (`LEAN_SOFT`) + A→ctl links, why do W47 source containers fill (~2k) and `src_A` harvest soft (~2 e/t vs model 9.6) while storage sits in the rebuild band? Is the lever more upgraders, or more local haul?

**Answer: Keep soft-cap; raise link-era `HMAX` 2→3 so the loose>1200 surplus can spawn a 3rd hauler to park overflow into storage. Floor stays 2 (`hFloor`). Do NOT lift soft-cap / flip labs/industry.**

### Live (tick ~84011166–84011271, ~02:47–02:54 Asia/Hong_Kong)
- home RCL7 ~15.25% (`1668150/10.935M`) stor~16.5k ABOVE; walls HOLD 300k; termK~14.8k O~127k KO32; `labReady.propose=1 actOk=1` `ops.labs=null`.
- W47N8 RCL7 ~2.60% (`283879`) stor~20.7k `leanBank=0 phase=ready`; upgraders=2; links live (A 26,12 → ctl 13,25); both source conts + ctl nearly full; `w8model.links=true lcarry=9`.
- Upgrade actual ~14 e/t vs ideal ~30; `src_A` harvest soft while ctl saturated — classic sink-full + no overflow drain.
- Overmind: upgrade power scales only with **storage** surplus above `storageBuffer` (100k); logistics treat storage/links as **buffers** (`LogisticsGroup.bufferChoices`) so transporters still move when the upgrade battery is full. Screeps link loss 3% — links are for latency, not infinite sink.
- TooAngel / docs pattern: controller fed from near-ctl energy; excess belongs in storage, not stranded at sources.

### Why HMAX=2 was wrong under soft-cap
- 10-29 correctly dropped **floor** to 2 (link-era local need ~9 CARRY).
- Cap was also set to 2, so `loose>1200` surplus could never spawn a 3rd hauler.
- Soft-cap ≤2 upgraders fills ctl cont/link → miners stall on full source conts → harvest soft. Raising upgraders would fight the cushion rebuild; a spare hauler parks into rebuild-band storage (hold-band/rebuild-band sink already prefers storage when ctl≥1200).

### Shipped
- `src/rooms/w47n8/index.js`: `HMAX = wm.links ? 3` (was 2); `hFloor` remains 2.
- `tests/w47n8.js`: links floor=2 + soft-cap overflow → 3rd hauler; Screeps lodash3 `_.sum` compat.
- **No gate / labs / industry / market flips; `ops.labs` still Misaki.**

### Watch
- After deploy: `w8.upgrade` recover toward ≥20; source cont energy leave the 1800–2000 band; stor stay ≥15k; local haulers ≤3.

## 2026-11-02 05:4x — home upgrade energy-bound / short-soft at storage ABOVE

**Question:** Why is home (W46N8) upgrade energy-bound / short-soft with storage ABOVE (~15–17k) while model ideal is ~26 e/t and `live_comp` ~9?

**Answer: Not a ctl/link feed bug.** (1) `live_comp~9` is a model artifact (full-fleet overhead vs income) — measured 2h upgrade is **~19.6 e/t (~75% of ideal 26)**, 6h **~18.7**. (2) 2×14W=28 WORK is **designed slightly energy-bound** vs ~26 feed; 3rd upgrader needs stor≥floor+1000. (3) Short soft = **15k floor hysteresis / `upBank`**: stor oscillates 14.5–17.7k → brief UNDER freezes `T.upgrader→0` until reserve+1000 → rebuild windows look energy-bound while `upgFeed.why` is often `ok` and hungry=0. (4) Hub DROP@31,33 is overflow when ctl battery saturates (improving ~2.7→0.9k) — secondary. Do **not** lower the floor or lift upBank; protect the cushion like Overmind's storageBuffer (they scale WORK only above ~100k surplus).

### Live (tick ~84013580–84013700, ~05:33–05:41 Asia/Hong_Kong)
- Deploy HEAD strategy `922fe38` (W47 HMAX 2→3); tip routine ~`96134c4`; no `deploy.lock`.
- Home RCL7 ~15.7% (`~1.717M/10.9M`) stor~15.5–16.1k ABOVE-ish; ctl~0.8–1.9k (brief 0 then rebuild); towers full; walls HOLD 300k; termK~19.3k O~127k KO32.
- `upgFeed`: surplus~504, hungry=0, why=`ok`, nUp=2 work=28, ctlLink~178 hub=0; remotes SAFE; `roleTargets.upgrader=2` (not banked this snapshot).
- W47N8 RCL7 ~3.0% stor~20.0k leanBank=0 phase=ready; 2h upg **~18.3** (HMAX drain working); links LIVE; K mining ON; LABS/industry OFF.
- `labReady.propose=1 actOk=1` `ops.labs=null` — **do not re-ask** this run.
- CPU ~16/20 bucket 10k; GCL4.

### Energy inventory (why not transport-starved)
| Bucket | Typical | Read |
|---|---|---|
| Storage | 15–17k around floor | Cushion thrash, not empty |
| Ctl container | 0.8–2.0k (EMA~1.3k) | Battery OK when why=ok |
| Ctl/hub links | often 0 when ctl full | Idle is correct (supply-follows-demand) |
| Hub drop@31,33 | ≤1k improving | Enclosed overflow parking |
| Extensions/spawns | filled | Queen pathing not the bottleneck |

### Overmind / TooAngel compare
- Overmind `UpgradeSite.settings.storageBuffer=100000`: upgrade power scales with surplus **above** buffer; logistics still treat storage/links as buffers when the upgrade battery is full (`LinkNetwork` greedy match + command-center drain).
- We gate the 3rd upgrader at floor+1k and freeze via `upBank` (enter reserve−500 / leave reserve+1000). Same philosophy at a tighter RCL7 cushion — short soft is the cost of not eating the 15k defense reserve.
- TooAngel / docs: ctl fed from near-ctl energy; excess belongs in storage, not stranded at sources (W47 HMAX 02:4x already addressed colony side).

### Root-cause ranking
1. **Designed energy-bound at nUp=2** (28W > ~26 feed) + 3rd-upgrader gate → model `upgrader_bound=energy` / `boundHint=energy` even when feed is healthy.
2. **`upBank` / floor thrash** → short soft windows (nUp→0) that patrols label energy-bound / mid-UNDER rebuild.
3. **`live_comp~9` misread** — do not chase ideal−live_comp; compare to measured ~19–22 or pause-adjusted ideal.
4. Hub drop / remote soft harvest — secondary; remotes SAFE.

### Shipped
- `src/managers/upgfeed.js`: new `why=floor_bank` when `room.memory.upBank`; obs `upBank`, `tUp`, `allowExtra`, `boundHint`. **No spawn/link behavior change.**
- `tests/upgfeed.js`: floor_bank + remote_pause precedence.
- **No labs/industry/market/W47N9/HUB_LINK flips; ops.labs still Misaki; no re-ask.**

### Watch
- Patrol: treat `upgFeed.why=floor_bank` as expected near-floor, not a haul defect; keep soft ≥70% vs ideal when why∈{ok,thin_surplus,floor_bank}.
- Home stor prefer ≥16k so allowExtra can admit a 3rd when ctlEma healthy (optional; not forced this run).
- W47 conts leave 1800–2000 / upg stay ≥18 after HMAX.

## 2026-11-02 08:4x — W47 soft-band park deadlock (WORK-bound ~55%)

**Question:** Why is W47N8 still WORK-bound / ~55% of ideal (~16.5 vs ~30 e/t) hours after HMAX 2→3 and links LIVE, with stor~20k `phase=ready`?

**Answer: Soft-cap exit was unreachable.** Sink park-to-storage stopped at `LEAN_STOR` 20k while soft-cap holds `nUp≤2` until `LEAN_SOFT` 25k. Extend park through 25k (`bankWhy=soft`). Do NOT lift soft-cap / flip labs.

### Live (tick ~84016000–84016020, ~08:40 Asia/Hong_Kong)
- Deploy tip strategy `df89ab7` (05:4x upgFeed); HEAD routine later; no `deploy.lock`.
- Home RCL7 ~16.1% stor~16.7k ABOVE; 2h upg **22.7/26 (~87%)** `boundHint=energy` why=`waiting_feed` intermittent; walls HOLD 300k; termK~23.6k O~127k KO32.
- W47N8 RCL7 ~3.35% (`366148/10.935M`) stor~20.1k leanBank=0 phase=ready; **nUp=2 uw=20**; links LIVE (A 26,12 → ctl 13,25); ctl+hub conts **2000/2000**; source B 2000 A~300; looseE~4.8k; w8lo7~5.5k.
- Model 2h: ideal 30.08 / actual **16.55** (55%); alloc harvest 36.7 / upg 16.55 / upkeep 13.3 / waste_other 6.3 / storage ~0; delivered hub 16 > ctl 7.5.
- `labReady.propose=1 actOk=1` `ops.labs=null` — **do not re-ask**.
- CPU ~15/20 bucket 10k; remotes SAFE; roads DONE.

### Root cause
1. Soft-cap ≤2 (`LEAN_SOFT`) → max ~20 WORK → WORK-bound ceiling ~16–20 e/t when feed OK.
2. 02:4x HMAX=3 correctly drains source overflow **toward** storage, but rebuild/hold-band sink released at 20k → ctl-first again.
3. With ctl+hub full, surplus oscillates as `waste_other` / link+cont stock instead of climbing stor → softLeft stuck ~5k forever.
4. Overmind: transporters still use storage as a logistics buffer when the upgrade battery is saturated (`LogisticsGroup.bufferChoices`); UpgradeSite scales WORK only above `storageBuffer`. Matching shape: **keep soft-cap**, finish parking to the soft exit.

### Shipped
- `src/rooms/w47n8/roles.js`: sink hold-band + park through **LEAN_SOFT 25k** (was 20k); ctl≥1200 feed floor unchanged.
- `src/rooms/w47n8/index.js`: `w8day.bankWhy=soft` when ready but stor<25k; `softLeft` obs.
- `tests/w47n8_filler.js` / `tests/w47n8_dayobs.js`: soft-band park + bankWhy.
- **No soft-cap / labs / industry / market / HUB_LINK / W47N9 flips; ops.labs still Misaki.**

### Watch
- `w8day.bankWhy=soft` → `ready` and `softLeft→0` within ~0.5–1 h if loose drains.
- Then nUp→3, upg recover toward ≥24 (ideal 30 still trimmed by waste/upkeep) — **unless threat soft** (`TH.localOn`). See 11:4x: that window keeps ≤2 even after 25k.
- Source conts leave 1800–2000; home soft ≥70% hold.

## 2026-11-02 11:4x — threat soft holds w8upgrader ≤2

**Question:** After storage passed `LEAN_SOFT` 25k, why did W47 2h upgrade drop to ~46.7% with w8upgrader at 4 / WORK40 and lots of `waiting_feed` while threat soft was hoarding energy? Does the soft-cap rise on stor≥25k even under threat soft?

**Answer: Yes — verified.** The ≤2 cap was only `stor < LEAN_SOFT`. Threat soft (`TH.localOn()`, `w8soft.why=threat`) never entered it. With seal walls already above the 100k urgent floor, `wallsLow` is false, so the peacetime base (3 with no sites) plus surplus climbed to 4×10W while towers held energy for combat. **Hold ≤2 for the local threat window only.** Neighbor `w8threatN` does not count. When the 1500-tick window ends, normal soft-band / soft-cap resumes. Do NOT flip labs/industry/market or the home upgrader cap.

### Gate
- `threatSoft()` = `TH.localOn()` = `Memory.ops.w8threat` within 1500 ticks (same predicate as soft-ramp `why=threat`).
- `softCap2(storE)` = `threatSoft() || storE < LEAN_SOFT` (25000).
- While `softCap2`: base spawn `min(base, 2)`, surplus upgraders off, `leanBankRecycle` keeps ≤2 (leanBank ≤1 still wins).
- `w8day.threatSoft`, `w8day.softCap2`, `bankWhy=threatSoft` when stor≥25k and the cap is threat-held.
- Reversible by doing nothing: the flag clears when `w8threat` ages out. No Memory toggle to remember to undo.

### Shipped
- `src/rooms/w47n8/index.js`: `threatSoft` / `softCap2` on spawn, surplus, and recycle.
- Tests: `w47n8_dayobs.js` (recycle + `w8threatN` does not hold), `w47n8_mminer.js` (spawn stays ≤2 / fills to 2 / 3rd returns in peace).
- **No `ops.labs` / `RCL6_LABS` / industry / market flips. Home W46N8 upgrader soft-cap untouched.**

## 2026-11-02 14:4x — peacetime ctl-battery surplus gate

**Question:** After softCap2 lifts (stor≥25k and threatSoft=0), why does W47 still stall ~53% of ideal with nUp=4 / WORK40 and `waiting_feed`~30% while storage climbs?

**Answer: Surplus spawned off storage alone; ctl battery was not yet saturated.** SoftCap2 correctly cleared. Base nUp→3 and the surplus rule `floor((stor-2000-…)/600)` immediately allowed a 4th 10W body. A→ctl link throughput is ~10 e/t gross (~8 net after losses); hub delivery ~18 e/t. Four stands need ~40 e/t when fed — they starve. Overmind pairs storageBuffer WORK scaling with **battery input requests** at `upgradePowerNeeded` (keep battery ≥50%). TooAngel places storage next to the upgrader so haul distance is near zero. We keep LEAN_SOFT 25k (tighter than Overmind’s ~100k) but must gate surplus on the ctl container+link battery.

### Gate
- `FEED_MIN = 800` (link almost full; hold-band uses 1200).
- `ctlBattery(room)` = energy in `CTL_CONT` [13,26] + `CTL_LINK` [13,25].
- Peacetime surplus spawn: requires `!softCap2 && ctlBattery ≥ FEED_MIN`; **upgCeil = HUB_LINK ? 6 : base 3** (no 4th while hub→ctl link gated off).
- Recycle: if softCap2 off and (`!HUB_LINK` or `ctlBattery < FEED_MIN/2`), keep ≤3. softCap2 ≤2 and leanBank ≤1 still win.
- Obs: `w8day.ctlBat`, `w8day.feedOk`.

### Shipped
- `src/rooms/w47n8/index.js` + `tests/w47n8_dayobs.js`.
- **No softCap2 predicate change / labs / HUB_LINK / industry / market / home upgrader flips. ops.labs still Misaki — no re-ask.**

### Watch
- After deploy: nUp should trim 4→3 until ctlBat≥800; waiting_feed↓; 2h upg climb toward ≥24; stor may rise slower (good).
- Do **not** enable `HUB_LINK` yet — measure feed-gate first.

## Wartime economy freeze (2026-11-02 14:5x)

While `Memory.ops.w47n9.on` + `pauseCivilians` (Misaki GO):

| Lever | Wartime behavior |
|---|---|
| Home / W47 upgraders | target **0** (keep 1 only if `ticksToDowngrade < 20000`); living surplus → recycle |
| Builders | target **0** + recycle |
| softCap2 / feedOk / ctlBattery | peacetime only; war does **not** lift surplus when softCap2 clears |
| HUB_LINK / labs / industry / market | **stay OFF** — do not flip for war |
| Raid spawn floors | home stor ≥ **12k**, colony ≥ **15k** (`raid9.WAR_STOR`) |
| Queens / fillers / miners / haulers / remotes | keep feeding spawn + towers |
| Ideal upgrade | wartime ideal ≈ **0** (downgrade insurance only); resume peacetime ideal after stand-down |

Refs: Overmind `storageBuffer` + warSpawnCutoff; TooAngel `upgraderMinStorage` / underSiege. Detail: `docs/RAID_W47N9.md`, `ROADMAP.md` 14:5x.

## 2026-11-02 23:4x — HUB_LINK plumbing readiness (no flip)

**Question:** with softCap cleared, KEY DONE, tower3+spawn2 DONE, and sealMinE back at LEAN_SOFT 25k (Misaki rejected +10k headroom), is it time to flip `HUB_LINK` so hub→ctl can close the ~66% upgrade gap?

**Answer: plumbing YES, flip NOT YET — need Misaki nod.** Shipped dormant hub→ctl + filler ferry; keep `HUB_LINK=false` until she approves the 5k site + upgCeil lift.

### Live (~23:28–23:40 Asia/Shanghai, t~84028896–84029075, aa4446b)
- Peacetime; home ~18.63% stor~15.5–16k ABOVE 2h~84%; W47 ~5.37% stor~25.4k softCap2 OFF KEY DONE sealRaise flap at 25k band; 2h upg ~66% (ideal~30 → actual~19–20); waiting_feed~0.26; remotes SAFE; K empty regener; labs OFF no re-ask; CPU~14.4/20.
- Delivered: hub ~26 e/t vs ctl ~8–10 e/t — remotes/B pile at hub while A→ctl alone cannot sustain WORK30 intermittently.

### Research (Screeps + Overmind / TooAngel)
- Screeps link transfer is 3% loss; RCL7 allows 4 links — we have A + ctl (+ hub gated).
- Overmind `UpgradeSite`: requests input when battery <50% / upgrade link <200; places upgrade link when storage path >10 (our ctl is ~20+ tiles from storage) — **hub→ctl is the right topology**.
- TooAngel: storage-centric hub link; fillers keep linkStorage topped; other links push *to* storage. Ours is **ctl-centric** (home `managers/links.js`: queen fills hub, hub→ctl when ctl <400) — match home, not TooAngel reverse.

### Gap before flip
1. `linkRun` only did A→ctl — no hub→ctl even if structure existed.
2. `w8filler` never deposited into hub link 33,34 (POST is range-2).
3. Flipping alone would place 5k site and raise `upgCeil` to 6 once feedOk — risk of WORK40+ before ferry is proven.

### Shipped (dormant; `HUB_LINK` stays false)
- `linkRun`: hub→ctl when hub exists, ctl <400, hub ≥200 (own cooldown; A still first).
- `fill.js`: idle hub-link ferry when stor≥25k and ctlBat <800 or hubE <200 (no-op without structure).
- `w8day.hubLinkE` / `hubReady` / `hubLink` obs. Tests flow + dayobs.

### Flip checklist (propose to Misaki)
1. Peacetime, softCap2 OFF, KEY DONE, sealMinE=25k accepted.
2. Deploy with hub plumbing LIVE (this commit).
3. Set `config.HUB_LINK=true` → layout places 33,34; builders finish; **upgCeil waits for structure** (`hubLinkLive` / 05:4x); watch `hubReady`/`hubLinkE` rise, `waiting_feed`↓, upg ≥24 / short≥70%.
4. Do **not** flip labs/industry/market with it. K still regenerating — minerals not the bottleneck.

## 2026-11-03 02:4x — seal soft-gate vs softCap2 (no sealMinE raise)

**Question:** With KEY DONE and sealMinE = LEAN_SOFT = 25k (Misaki accepted edge thrash; rejected 35k buffer), how should seal→1M wallJob / builders interact with softCap2 so peacetime upgrade recovery is not starved every time stor dips under 25k mid-seal?

**Answer: soft-gate deep seal to softCap2 + sticky park + edge intensity — do not raise sealMinE.** Overmind parks routine fortify until ~500k colony energy; TooAngel uses storage/healthy floors. We keep KEY ungated and only park seal→1M.

### Live (~02:47 Asia/Shanghai, t~84031795, deploy 8075205)
- Peacetime; home ~19.22% stor~16.0k ABOVE 2h~81%; W47 ~5.90% stor25004 softCap2 OFF sealRaise1 builders2 nUp3 KEY DONE sealMinE=25000 hubReady0; 2h ~64–69% consec soft; remotes SAFE; labs OFF no re-ask; K regener~40.5k.
- SoftCap thrash pattern (patrols 00:23–02:27): ON→short crash ~30%; OFF→sealRaise1 drains band back under 25k.

### Gate
- `TH.softThin(storE)` = `localOn() || storE < LEAN_SOFT` (softCap2 shape).
- `TH.updateSealPark`: set `Memory.ops.w8sealPark` while softThin / below sealMinE; clear only when softThin off **and** nUp ≥ peacetime base (sites?2:3).
- `TH.sealDeepOk(storE)` = !parked && !softThin && storE ≥ sealMinE.
- wallJob + spawn rule 6: deep raise only while sealDeepOk; `SEAL_EDGE=5k` → 2nd builder only with sealMinE+5k headroom; parked still allows 1 builder for STAGE3 floor only.
- Obs: `w8day.sealPark` / `sealRaise` (via sealDeepOk); `w8soft.sealPark`.

### Shipped
- `src/rooms/w47n8/threat.js` + `index.js` + `roles.js`; tests `w47n8_fortify.js` / `w47n8_dayobs.js`.
- **sealMinE stays 25000.** **No** HUB_LINK / labs / industry / market flips. **No** re-ask.

### Watch
- After deploy: when softCap2 re-ON, `sealPark=1` / `sealRaise=0` and live builders stop climbing above 300k; when softCap clears, park holds until nUp≥3 then seal resumes; 2nd builder only above ~30k.
- HUB_LINK nod remains open (~23:45) — do not re-spam. Biggest remaining upg gap is still !HUB_LINK feed.

## 2026-11-03 05:4x — HUB_LINK flip day-of: upgCeil must wait for structure

**Question:** When Misaki nods `HUB_LINK=true`, does `upgCeil` 3→6 fire before the 5k hub link at 33,34 stands — recreating the 14:4x waiting_feed thrash — and should surplus/recycle gate on `hubReady` (structure) rather than the config flag alone?

**Answer: YES it was a gap; gate on structure (`hubLinkLive`).** Plumbing (23:4x) is enough to ferry+send once the link stands, but raising ceil on the flag alone would spawn WORK40+ while A→ctl still ~8 e/t during the ~5k build. Do **not** flip the flag this run; do **not** re-ask — nod stays open. Shipped the gate so the day-of sequence is safe when she nods.

### Live (~05:29–05:42 Asia/Shanghai, deploy 3301591)
- Peacetime; home W46N8 RCL7 ~19.63% 2h~81% stor~16.0–16.1k ABOVE15k nUp2–3.
- W47N8 RCL7 ~6.33% 2h~68.4% (FIRST soft after held≥70) softCap2 JUST cleared KEY 300k DONE; seal soft-gate LIVE (sealPark0 / sealMinE 25k); hubReady0; HUB_LINK nod open.
- Remotes: W45N7 Invader1 + defender1; labs OFF no re-ask; K regener~37.9k; roads.phase=done; CPU~10–16/20.

### Research (Screeps + Overmind / TooAngel)
1. **Screeps link cooldown** = `pos.getRangeTo(target)` ticks (1 tick/tile). Hub 33,34 → ctl 13,25 Chebyshev **20** → cooldown 20 → max **800/20 = 40 e/t** gross ≈ **38.8 e/t** net after 3% loss — enough for WORK40+ once live. A→ctl range 13 → ~61 e/t theoretical but A only produces ~10.
2. **Overmind UpgradeSite** places an upgrade link when the storage path is long and requests battery input when thin — hub→ctl matches that topology (23:4x). Surplus WORK must not outrun the battery before the link exists.
3. **TooAngel** is storage-centric; we stay ctl-centric like home `managers/links.js`. Filler ferry (23:4x) tops hub when stor≥25k — no-op without structure.
4. **Seal soft-gate (02:4x)** interaction: during the 5k site, `bigBuild` (siteRem≥3k) already caps base at 2; with structure-gated ceil, surplus cannot jump to 6 mid-build even if softCap clears and sealPark drops.

### Gap (pre-fix)
- `upgCeil = C.HUB_LINK ? 6 : (bigBuild ? 2 : 3)` and recycle `(!C.HUB_LINK || ctlBat < FEED_MIN/2)` keyed the **config flag**.
- Day-of: flag→true places site; feedOk + softCap OFF could spawn toward 6 while hub is still a construction site → same 14:4x starve (A→ctl only).
- `linkRun` / filler ferry already required the structure; only ceil/recycle did not.

### Day-of sequence (after Misaki nod — do not re-ask)
1. Set `config.HUB_LINK=true` → layout places link site 33,34 (5k).
2. **While site:** `hubLinkLive=false` → upgCeil = bigBuild?2:3; recycle keep≤3; seal soft-gate still applies; builders finish site (~minutes at softCap OFF).
3. **Structure stands:** `hubReady=1` / `hubLinkLive` → upgCeil 6 unlocked; filler ferry tops hub; `linkRun` hub→ctl (own cooldown, A still first).
4. Patrol watch: `hubLinkE` rising, `waiting_feed`↓, short≥70%, nUp toward 4–6 only while `feedOk` + `!softCap2`; sealPark must not thrash stor under 25k mid-build (02:4x gate).
5. Do **not** flip labs / industry / market with it. K regenerating — minerals not the bottleneck.

### Shipped
- `hubLinkLive(room)` — `C.HUB_LINK &&` structure at `L.ORDER.link[0]`.
- Surplus `upgCeil` + leanBankRecycle keep≤3 use `hubLinkLive` (not flag alone).
- `w8day.hubReady` now mirrors `hubLinkLive`. Tests `w47n8_dayobs` (flag-on without structure still recycles; structure+feedOk allows surplus).
- **`HUB_LINK` stays false.** No labs/industry/market flips. No re-ask.

### Watch after next nod-deploy
- Tick of flip: hubReady 0, siteRem~5k, upgCeil effectively ≤2 (bigBuild).
- After stand: hubReady 1, hubLinkE≥0, recycle clears when feedOk, waiting_feed↓ within ~1–2k ticks.

## 2026-11-03 08:4x — softCap2 leanBank-style hysteresis (LEAN_SOFT_ARM)

**Question:** SoftCap energy half clears at `LEAN_SOFT=25k` with **zero hysteresis**, so live storage thrash 23.4↔25.5k recycles nUp 3↔2 every boundary cross (seal soft-gate already parks seal; Misaki rejected raising sealMinE to 35k). Should softCap itself get leanBank-style ARM/SOFT sticky?

**Answer: Yes — `LEAN_SOFT_ARM=22000` + sticky `w8day.softE`. Do NOT raise sealMinE / LEAN_SOFT. softThin stays STRICT <25k.**

### Live (~08:26–08:47 Asia/Shanghai, deploy e7f2017)
- Peacetime; home ~20.1% 2h~83% stor~15.9k ABOVE floor_bank.
- W47 ~6.85% 2h~70% CROSSED≥70 soft-streak BROKEN then softCap **ON again** at ~23.2k; KEY DONE; HUB_LINK await nod hubReady0.
- Remotes SAFE; labs OFF no re-ask; K regener~35.4k; roads.phase=done.

### Research (Screeps + Overmind / TooAngel)
1. **leanBank precedent (02:4x):** `LEAN_ARM=15k` / `LEAN_STOR=20k` sticky via prior `w8day.leanBank` — same thrash class, already proven.
2. **Overmind** `storageBuffer=100k` + `fortifyDutyThreshold=500k` are single thresholds (no ARM) but sit on a fat cushion; our 25k edge is thin enough that zero-hysteresis thrash is the failure mode.
3. **TooAngel** healthy/storage floors — same "don't flicker" shape.
4. **Seal soft-gate (02:4x)** already parks seal while `softThin` (strict `<LEAN_SOFT`). Coupling softCap clear to the same sticky would re-open seal thrash; keep softThin strict and only sticky the upgrader/hauler softCap energy half.

### Gap (pre-fix)
- `softCap2 = threatSoft || stor < LEAN_SOFT` — no ARM.
- roles soft-band parked whenever `se < 25000`, so after a clear the next 24k tick forced park + nUp≤2 again.
- Patrols: softCap JUST cleared → ON again within ~20m at stor~23k.

### Shipped
- `LEAN_SOFT_ARM=22000`; `softEnergyCap(stor)` sticky via `Memory.ops.w8day.softE` (clear@25k / re-arm@22k).
- `softCap2 = threatSoft || softEnergyCap`; `w8day.softArm` / `softE`; bankWhy=`soft` only on energy half.
- roles.js soft-band follows `softE` (threat does **not** park — combat needs ctl fed).
- softThin / sealDeepOk unchanged (strict). Tests dayobs / mminer / filler.
- **No** HUB_LINK / labs / industry / market flips; **no** re-ask. sealMinE stays 25000.

### Watch
- Climb past 25k once → softE=0; dip to 23k should keep softCap2=0 / nUp3 / bankWhy=ready.
- Re-arm only below 22k (softE=1, recycle ≤2).
- softLeft still reports distance to LEAN_SOFT (obs honesty).

