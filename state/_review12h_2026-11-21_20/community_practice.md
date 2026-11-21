# Community practice notes — 2026-11-21 20:2x 12h review

Overmind UpgradeSite was re-checked on the current public master file src/hiveClusters/upgradeSite.ts (raw master; file history on that path still ends in 2019):

- energyBuffer=100000
- energyPerBodyUnit=10000
- linksRequestBelow=200

Upgraders scale only with energy above that 100k buffer (and the 10k-per-body scaling, plus 2× / 4× multipliers above 500k / 800k surplus, only applies after the buffer). Public path: https://github.com/bencbartlett/Overmind/blob/master/src/hiveClusters/upgradeSite.ts

This matches this morning's reading. The **100k buffer gate is unchanged**.

TooAngel / The International were not re-cloned this run. The 2026-11-18 08:2x check still applies: TooAngel (master, 17 Nov 2026) keeps one upgrader at almost any storage but sizes WORK so one lifetime spends about half the store (15k→5W, 20k→6W, 40k→13W) and treats 100k as "healthy" / lab-reaction storage. The International (Main) uses an emergency minimum of ~73–80k at mid/late RCL7 and will not spawn surplus upgraders below ~94–102k.

This window's numbers do not change the comparison:

- Home touched 20k again (max **21259**), but the longest clean stretch was only **121 t**. Live ~19.3k with 2×14W after a worse under-15k afternoon (23.80%, min 10928). The 20k/300t third remains unlatched.
- W47 produced its first ≥40k samples of the day (max **42468**, longest clean **211 t**), live **~35k** with softCap2 on from a live remote solo, keep=2. 40k/500t latch not armed.
- Live energy ~19k / 35k, window max 21k / 42k, still far below the ~100k "healthy / reaction / surplus-upgrader" band.

Our 15k / 20k / 40k floors, and running 14W or 2×14W (W47 2×10W) on them, remain more aggressive than all three. The 20k/300t third and 40k/500t keep=3 are likewise more aggressive. A 121 t 20k kiss and a first 42.5k W47 high are progress toward our own gates, not an argument to loosen them or to open industry / market / T3 / a new remote. Three W45N7 cores and the W47N7 solos were standing ops (designed defenders, cores already cleared, one solo still hatching at the tip) and are not a reason to loosen the 15k floor, the 20k gate, or the 40k lock, nor to start a commander or Safe Mode. Boost-skip under a stable 20k remains slightly conservative vs official XGH2O efficiency, but consistent with a tight store (no 300 t ≥20k camp) and a 23.80% under-15k afternoon. Holding off a new remote matches shard3 CPU caution (12h avg 17.84 / 20, one 40.06 pre-freeze spike, bucket stayed full). Authorized home KO growing 43431→48511 still matches "don't put off minerals" and is still not an Overmind-style ~100k industry turn-on.

See also state/_review12h_2026-11-21_08/community_practice.md and state/_review12h_2026-11-18_08/community_practice.md.
