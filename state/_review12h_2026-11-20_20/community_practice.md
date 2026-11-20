# Community practice notes — 2026-11-20 20:2x 12h review

Overmind `UpgradeSite` was re-checked on the current public master file `src/hiveClusters/upgradeSite.ts` (raw master; file history on that path still ends in 2019):

- `energyBuffer=100000`
- `energyPerBodyUnit=10000`
- `linksRequestBelow=200`

Upgraders scale only with energy above that 100k buffer (and the 10k-per-body scaling, plus 2× / 4× multipliers above 500k / 800k surplus, only applies after the buffer). Public path: https://github.com/bencbartlett/Overmind/blob/master/src/hiveClusters/upgradeSite.ts

This morning's citation of blob `2eae97b` (`storageBuffer=100000` / `energyPerBodyUnit=25000`) is a different, older snapshot of the same file, not current master. Current master matches the 2026-11-18 08:2x reading. The **100k buffer gate is unchanged**; the 10k vs 25k scaling factor only matters above that buffer and does not argue for loosening our 15k / 20k / 40k floors.

TooAngel / The International were not re-cloned this run. The 2026-11-18 08:2x check still applies: TooAngel (master, 17 Nov 2026) keeps one upgrader at almost any storage but sizes WORK so one lifetime spends about half the store (15k→5W, 20k→6W, 40k→13W) and treats 100k as "healthy" / lab-reaction storage. The International (Main) uses an emergency minimum of ~73–80k at mid/late RCL7 and will not spawn surplus upgraders below ~94–102k.

This window's numbers do not change the comparison:

- Home never touched 20k (max **19431**); live ~17.4k with 2×14W (tip nUp=3 is a ttl-8 handoff).
- W47 max **36384** this window (24h max is this same 36384; longest ≥30k 331 t), live **~24k**, keep=2. 40k/500t latch not armed.
- Live energy ~17k / 24k, window max 19k / 36k, still ≪ the ~100k "healthy / reaction / surplus-upgrader" band.

Our 15k / 20k / 40k floors, and running 14W or 2×14W on them, remain more aggressive than all three. The 20k/300t third and 40k/500t keep=3 are likewise more aggressive. That continues to argue for **holding** the existing gates, not loosening them, not adding a third, and not opening industry / market / T3. Four daytime W45N7 Invader Cores were standing ops (designed full-budget melee, all cleared) and are not a reason to loosen the 15k floor or the 20k gate; the home exact2h dip at this tip is the designed pause sliding into the 2h window, with short last200 already HARD. Boost-skip under 20k is slightly conservative vs official XGH2O efficiency, but consistent with a tight store (zero ≥20k samples this window, and none in the trailing 24h). Holding off a new remote matches shard3 CPU caution (12h avg 17.18 / 20, max 25.77, no ≥40 spike, bucket stayed full). Authorized home KO growing 33121→38281 still matches "don't put off minerals" and is still not an Overmind-style ~100k industry turn-on.

See also `state/_review12h_2026-11-20_08/community_practice.md` and `state/_review12h_2026-11-18_08/community_practice.md`.
