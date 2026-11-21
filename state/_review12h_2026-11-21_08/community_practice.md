# Community practice notes — 2026-11-21 08:2x 12h review

Overmind UpgradeSite was re-checked on the current public master file src/hiveClusters/upgradeSite.ts (raw master; file history on that path still ends in 2019):

- energyBuffer=100000
- energyPerBodyUnit=10000
- linksRequestBelow=200

Upgraders scale only with energy above that 100k buffer (and the 10k-per-body scaling, plus 2× / 4× multipliers above 500k / 800k surplus, only applies after the buffer). Public path: https://github.com/bencbartlett/Overmind/blob/master/src/hiveClusters/upgradeSite.ts

This matches last evening's reading. The **100k buffer gate is unchanged**.

TooAngel / The International were not re-cloned this run. The 2026-11-18 08:2x check still applies: TooAngel (master, 17 Nov 2026) keeps one upgrader at almost any storage but sizes WORK so one lifetime spends about half the store (15k→5W, 20k→6W, 40k→13W) and treats 100k as "healthy" / lab-reaction storage. The International (Main) uses an emergency minimum of ~73–80k at mid/late RCL7 and will not spawn surplus upgraders below ~94–102k.

This window's numbers do not change the comparison:

- Home finally touched 20k (max **21122**), but the longest clean stretch was only **70 t**. Live ~16k with 2×14W. The 20k/300t third remains unlatched.
- W47 max **37439** this window (24h max is this same 37439; longest ≥30k 331 t), live **~25k** at the sealMinE edge, keep=2. 40k/500t latch not armed.
- Live energy ~16k / 25k, window max 21k / 37k, still far below the ~100k "healthy / reaction / surplus-upgrader" band.

Our 15k / 20k / 40k floors, and running 14W or 2×14W (W47 2×10W) on them, remain more aggressive than all three. The 20k/300t third and 40k/500t keep=3 are likewise more aggressive. A first 20k kiss and a new 37.4k W47 high are progress toward our own gates, not an argument to loosen them or to open industry / market / T3 / a new remote. Two overnight solo Invaders were standing ops (designed defenders, both cleared, no cores this window) and are not a reason to loosen the 15k floor or the 20k gate. Boost-skip under a stable 20k remains slightly conservative vs official XGH2O efficiency, but consistent with a tight store (no 300 t ≥20k camp). Holding off a new remote matches shard3 CPU caution (12h avg 17.46 / 20, max 28.2, no ≥40 spike, bucket stayed full). Authorized home KO growing 38281→43431 still matches "don't put off minerals" and is still not an Overmind-style ~100k industry turn-on.

See also state/_review12h_2026-11-20_20/community_practice.md and state/_review12h_2026-11-18_08/community_practice.md.
