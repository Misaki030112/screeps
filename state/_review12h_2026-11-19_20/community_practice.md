# Community practice notes — 2026-11-19 20:2x 12h review

Overmind `UpgradeSite` was re-checked on master blob `2eae97b` (still the June 2019 tree, no later change to these constants):

- `storageBuffer=100000`
- `energyPerBodyUnit=25000`
- `linksRequestBelow=200`

Upgraders spawn only above that 100k buffer (or ticksToDowngrade < 500) and are not recycled for banking. Surplus energy above the buffer adds upgrade power at 25k per extra body unit. Routine fortify still waits for 500k energy and targets 1M hits at RCL7.

Note: last evening's recap mistyped those constants as `energyBuffer=100000` / `energyPerBodyUnit=10000`. The live source is `storageBuffer=100000` / `energyPerBodyUnit=25000`. The 100k gate itself is unchanged, so the comparison does not move.

TooAngel / The International were not re-cloned this run. The 2026-11-18 08:2x check still applies: TooAngel (master, 17 Nov 2026) keeps one upgrader at almost any storage but sizes WORK so one lifetime spends about half the store (15k→5W, 20k→6W, 40k→13W) and treats 100k as "healthy" / lab-reaction storage. The International (Main) uses an emergency minimum of ~73–80k at mid/late RCL7 and will not spawn surplus upgraders below ~94–102k.

This window's numbers do not change the comparison:

- Home touched 20k for only 150 t (max **20829**); live ~15.5k with 2×14W.
- W47 max **35585** this window (24h max **36249** @00:06), live **22025**, keep=2. 40k/500t latch not armed.
- Live energy ~15.5k / 22k, window max 21k / 36k, still ≪ the ~100k "healthy / reaction / surplus-upgrader" band.

Our 15k / 20k / 40k floors, and running 14W or 2×14W on them, remain more aggressive than all three. The 20k/300t third and 40k/500t keep=3 are likewise more aggressive. That continues to argue for **holding** the existing gates, not loosening them, not adding a third, and not opening industry / market / T3. Boost-skip under 20k is slightly conservative vs official XGH2O efficiency, but consistent with a tight store (the only ≥20k camp was 150 t). Holding off a new remote matches shard3 CPU caution (12h avg 17.87 / 20). Authorized home KO growing 18716→27886 still matches "don't put off minerals" and is still not an Overmind-style ~100k industry turn-on.

See also `state/_review12h_2026-11-18_08/community_practice.md`.
