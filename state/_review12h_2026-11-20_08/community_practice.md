# Community practice notes — 2026-11-20 08:2x 12h review

Overmind `UpgradeSite` was re-checked on the current public master blob `2eae97b` (still the June 2019 tree; no later change to these constants):

- `storageBuffer=100000`
- `energyPerBodyUnit=25000`
- `linksRequestBelow=200`

Upgraders spawn only above that 100k buffer (or ticksToDowngrade < 500) and are not recycled for banking. Surplus energy above the buffer adds upgrade power at 25k per extra body unit. Routine fortify still waits for 500k energy and targets 1M hits at RCL7. Public path: https://github.com/bencbartlett/Overmind/blob/2eae97b/src/hiveClusters/upgradeSite.ts

TooAngel / The International were not re-cloned this run. The 2026-11-18 08:2x check still applies: TooAngel (master, 17 Nov 2026) keeps one upgrader at almost any storage but sizes WORK so one lifetime spends about half the store (15k→5W, 20k→6W, 40k→13W) and treats 100k as "healthy" / lab-reaction storage. The International (Main) uses an emergency minimum of ~73–80k at mid/late RCL7 and will not spawn surplus upgraders below ~94–102k.

This window's numbers do not change the comparison:

- Home never touched 20k (max **18864**); live ~17.1k with 2×14W.
- W47 max **30080** this window (24h max still **35585** @17:13 11-19), live **24081**, keep=2. 40k/500t latch not armed.
- Live energy ~17k / 24k, window max 19k / 30k, still ≪ the ~100k "healthy / reaction / surplus-upgrader" band.

Our 15k / 20k / 40k floors, and running 14W or 2×14W on them, remain more aggressive than all three. The 20k/300t third and 40k/500t keep=3 are likewise more aggressive. That continues to argue for **holding** the existing gates, not loosening them, not adding a third, and not opening industry / market / T3. Three overnight Invader Cores on W45N7 were standing ops (designed full-budget melee, all cleared) and are not a reason to loosen the 15k floor or the 20k gate; the home formal fire already cleared once nUp returned to 2. Boost-skip under 20k is slightly conservative vs official XGH2O efficiency, but consistent with a tight store (zero ≥20k samples this window). Holding off a new remote matches shard3 CPU caution (12h avg 17.61 / 20, one combat spike 42.44, bucket stayed full). Authorized home KO growing 27886→33121 still matches "don't put off minerals" and is still not an Overmind-style ~100k industry turn-on.

See also `state/_review12h_2026-11-19_20/community_practice.md` and `state/_review12h_2026-11-18_08/community_practice.md`.
