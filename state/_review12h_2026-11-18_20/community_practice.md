# Community practice notes — 2026-11-18 20:2x 12h review

This evening's review does **not** re-clone Overmind / TooAngel / The International. This morning's 08:2x re-check (same calendar day) is still the source:

- Overmind `UpgradeSite` (`src/hiveClusters/upgradeSite.ts` on master, last commit still June 2019): `energyBuffer=100000` / `energyPerBodyUnit=10000` / `linksRequestBelow=200`. Upgraders spawn only above that 100k buffer (or ticksToDowngrade < 500) and are not recycled for banking. Routine fortify waits for 500k energy and targets 1M hits at RCL7.
- TooAngel (master, commit 17 Nov 2026): keeps one upgrader at almost any storage but sizes WORK so one lifetime spends about half the store (15k→5W, 20k→6W, 40k→13W) and treats 100k as "healthy" / lab-reaction storage.
- The International (Main): emergency minimum of ~73–80k at mid/late RCL7; will not spawn surplus upgraders below ~94–102k.

Those buffers do not move in 12 hours, and this window's numbers do not change the comparison:

- Home never touched 20k (max **19772**); live ~18.9–19.0k with 2×14W.
- W47 max **34155**, live **25271**, keep=2 (two 10W upgraders). 40k/500t latch not armed.
- Live energy ~19k / 25k, window max 20k / 34k, still ≪ the ~100k "healthy / reaction / surplus-upgrader" band.

Our 15k / 20k / 40k floors, and running 14W or 2×14W on them, remain more aggressive than all three. The 20k/300t third and 40k/500t keep=3 are likewise more aggressive. That continues to argue for **holding** the existing gates, not loosening them, not adding a third, and not opening industry / market / T3. Boost-skip under 20k is slightly conservative vs official XGH2O efficiency, but consistent with a tight store. Holding off a new remote matches shard3 CPU caution (12h avg 17.24 / 20). Authorized home KO growing 14071→18716 still matches "don't put off minerals" and is still not an Overmind-style ~100k industry turn-on.

See also this morning's `state/_review12h_2026-11-18_08/community_practice.md`.
