# Community practice notes — 2026-11-23 08:2x 12h review

Overmind UpgradeSite was not re-fetched this morning; last evening's 2026-11-22 20:3x check of the current public master file src/hiveClusters/upgradeSite.ts still applies (12 h ago, same master):

- energyBuffer=100000
- energyPerBodyUnit=10000
- linksRequestBelow=200

Upgraders scale only with energy above that 100k buffer (and the 10k-per-body scaling, plus 2× / 4× multipliers above 500k / 800k surplus, only applies after the buffer). Public path: https://github.com/bencbartlett/Overmind/blob/master/src/hiveClusters/upgradeSite.ts

The **100k buffer gate is unchanged**. (An older Overmind commit used the name storageBuffer and energyPerBodyUnit=25000; current master is still energyBuffer=100000 / energyPerBodyUnit=10000.)

TooAngel / The International were not re-cloned this run. The 2026-11-18 08:2x check still applies: TooAngel (master, 17 Nov 2026) keeps one upgrader at almost any storage but sizes WORK so one lifetime spends about half the store (15k→5W, 20k→6W, 40k→13W) and treats 100k as "healthy" / lab-reaction storage. The International (Main) uses an emergency minimum of ~73–80k at mid/late RCL7 and will not spawn surplus upgraders below ~94–102k.

This window's numbers do not change the comparison — they argue more clearly for holding the gates:

- Home did **not** touch 20k this window (max **19585**, 0 samples ≥20k; 24h max remains last evening's 19770). Live ~13.9k is under the 15k floor (why=floor_bank, nUp=1 tUp=1) after a better under-15k day (7.75%, min 13299, longest clean stretch 121 t) than last evening's 13.56%. The floor is doing its job at the tip. The 20k/300t third remains unlatched.
- W47 produced **no** ≥40k samples (max **33302**, longest ≥30k clean **301 t**) and even had a short 21 t dip under 15k after the 22:12 W47N7 guard wave. Live **~25.0–25.2k** with softCap2 / threatSoft **OFF** and sealPark **ON** (the 25k sealMinE rule; last evening's threat leftover has expired). 40k/500t latch not armed. keep=2 held.
- Live energy ~14k / 25k, window max 20k / 33k, still far below the ~100k "healthy / reaction / surplus-upgrader" band.

Our 15k / 20k / 40k floors, and running 14W or 2×14W (W47 2×10W) on them, remain more aggressive than all three. The 20k/300t third and 40k/500t keep=3 are likewise more aggressive. A dry 20k window, a 33.3k W47 high (no 40k touch), and a tip that is currently under the 15k floor are mid-wait, not an argument to loosen the gates or to open industry / market / T3 / a new remote. The W47N7 guard, the W47N8 north Invader, and the W47N7 boosted solo were standing ops (already told in the 02:42 / 05:38 patrols; remotes SAFE at the tip). They are not a reason to loosen the 15k floor, the 20k gate, or the 40k lock, nor to start a commander or Safe Mode. Authorized home KO growing 58851→63861, with the 15k reaction floor currently pausing (~13.9k homeStor), still matches "don't put off minerals" and is still not an Overmind-style ~100k industry turn-on. Boost-skip under a stable 20k remains slightly conservative vs official XGH2O efficiency, but consistent with a tight store (no ≥20k sample this window, and the tip is under 15k). Holding off a new remote matches shard3 CPU caution (12h avg 17.39 / 20, max 28.09, zero ≥40, bucket stayed full).

Home crossing 90% at 04:51 is the already-planned trigger to *prepare* the RCL8 home→W47 terminal funnel (community-standard "feed the room still climbing" once home's upgrade caps at 15 e/t). That is preparation for RCL8, not a reason to send energy now, and not a reason to loosen the energy gates. Overmind's 100k buffer still says: do not treat a sub-20k home store as a surplus funnel.

See also state/_review12h_2026-11-22_20/community_practice.md and state/_review12h_2026-11-22_08/community_practice.md.
