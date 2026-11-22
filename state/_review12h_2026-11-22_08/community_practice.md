# Community practice notes — 2026-11-22 08:2x 12h review

Overmind UpgradeSite was re-checked on the current public master file src/hiveClusters/upgradeSite.ts (raw master; file history on that path still ends in 2019):

- energyBuffer=100000
- energyPerBodyUnit=10000
- linksRequestBelow=200

Upgraders scale only with energy above that 100k buffer (and the 10k-per-body scaling, plus 2× / 4× multipliers above 500k / 800k surplus, only applies after the buffer). Public path: https://github.com/bencbartlett/Overmind/blob/master/src/hiveClusters/upgradeSite.ts

This matches last evening's reading. The **100k buffer gate is unchanged**.

TooAngel / The International were not re-cloned this run. The 2026-11-18 08:2x check still applies: TooAngel (master, 17 Nov 2026) keeps one upgrader at almost any storage but sizes WORK so one lifetime spends about half the store (15k→5W, 20k→6W, 40k→13W) and treats 100k as "healthy" / lab-reaction storage. The International (Main) uses an emergency minimum of ~73–80k at mid/late RCL7 and will not spawn surplus upgraders below ~94–102k.

This window's numbers do not change the comparison:

- Home touched 20k again (max **20870**), but the longest clean stretch was only **81 t**. Live ~14.1–14.4k is on the 15k floor (why=floor_bank, tUp=1) after a healthier under-15k night (12.54%, min 12152) than last evening's 23.80%. The 20k/300t third remains unlatched.
- W47 produced another short ≥40k kiss (max **41133**, longest clean **71 t**), smaller than last evening's first touch (42468 / 211 t). Live **~27k** with softCap2 off and keep=2. 40k/500t latch not armed.
- Live energy ~14k / 27k, window max 21k / 41k, still far below the ~100k "healthy / reaction / surplus-upgrader" band.

Our 15k / 20k / 40k floors, and running 14W or 2×14W (W47 2×10W) on them, remain more aggressive than all three. The 20k/300t third and 40k/500t keep=3 are likewise more aggressive. An 81 t 20k kiss and a 41.1k / 71 t W47 high are progress toward our own gates, not an argument to loosen them or to open industry / market / T3 / a new remote. One W45N7 core and the W45N7 / W47N7 solos were standing ops (designed defenders, all already cleared by the tip) and are not a reason to loosen the 15k floor, the 20k gate, or the 40k lock, nor to start a commander or Safe Mode. The 15k reaction floor pausing KO while homeStor is ~14k is the designed pause, not a labs policy change. Boost-skip under a stable 20k remains slightly conservative vs official XGH2O efficiency, but consistent with a tight store (no 300 t ≥20k camp) and a tip that is back on the 15k floor. Holding off a new remote matches shard3 CPU caution (12h avg 17.29 / 20, max 33.99, zero ≥40, bucket stayed full). Authorized home KO growing 48511→53631 still matches "don't put off minerals" and is still not an Overmind-style ~100k industry turn-on.

See also state/_review12h_2026-11-21_20/community_practice.md and state/_review12h_2026-11-18_08/community_practice.md.
