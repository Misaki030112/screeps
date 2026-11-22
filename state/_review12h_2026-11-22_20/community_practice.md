# Community practice notes — 2026-11-22 20:3x 12h review

Overmind UpgradeSite was re-checked on the current public master file src/hiveClusters/upgradeSite.ts (raw master):

- energyBuffer=100000
- energyPerBodyUnit=10000
- linksRequestBelow=200

Upgraders scale only with energy above that 100k buffer (and the 10k-per-body scaling, plus 2× / 4× multipliers above 500k / 800k surplus, only applies after the buffer). Public path: https://github.com/bencbartlett/Overmind/blob/master/src/hiveClusters/upgradeSite.ts

This matches this morning's reading. The **100k buffer gate is unchanged**. (An older Overmind commit used the name storageBuffer and energyPerBodyUnit=25000; current master is still energyBuffer=100000 / energyPerBodyUnit=10000.)

TooAngel / The International were not re-cloned this run. The 2026-11-18 08:2x check still applies: TooAngel (master, 17 Nov 2026) keeps one upgrader at almost any storage but sizes WORK so one lifetime spends about half the store (15k→5W, 20k→6W, 40k→13W) and treats 100k as "healthy" / lab-reaction storage. The International (Main) uses an emergency minimum of ~73–80k at mid/late RCL7 and will not spawn surplus upgraders below ~94–102k.

This window's numbers do not change the comparison — they argue more clearly for holding the gates:

- Home did **not** touch 20k this window (max **19770**, 0 samples ≥20k). Live ~16.0–16.4k is comfortably above the 15k floor (why=ok, nUp=2 tUp=2) after a similar under-15k day (13.56%, min 12382, longest clean stretch 131 t) to this morning's 12.54%. The 20k/300t third remains unlatched.
- W47 produced **no** ≥40k samples (max **36252**, longest ≥30k clean **551 t**). Live **25000** with softCap2 / threatSoft / sealPark **ON** after the ~20:00 box-wake threat (w8inv=84420528). 40k/500t latch not armed. keep=2 held.
- Live energy ~16k / 25k, window max 20k / 36k, still far below the ~100k "healthy / reaction / surplus-upgrader" band.

Our 15k / 20k / 40k floors, and running 14W or 2×14W (W47 2×10W) on them, remain more aggressive than all three. The 20k/300t third and 40k/500t keep=3 are likewise more aggressive. A dry 20k window and a 36.3k W47 high (no 40k touch) are mid-wait, not an argument to loosen the gates or to open industry / market / T3 / a new remote. The W47N7 solo and the W45N7 boosted solo were standing ops (designed defenders; both already SAFE by the tip — the W45N7 cleared event was cut by the 17:41 freeze, later status why=killed). They are not a reason to loosen the 15k floor, the 20k gate, or the 40k lock, nor to start a commander or Safe Mode. Live W47 threatSoft / sealPark is the designed colony threat response after the 19:43–19:59 box wake, not a policy change and not a reason to unpark ceil/seal or add a third. Authorized home KO growing 53631→58851, with the 15k reaction floor currently running (~16k homeStor), still matches "don't put off minerals" and is still not an Overmind-style ~100k industry turn-on. Boost-skip under a stable 20k remains slightly conservative vs official XGH2O efficiency, but consistent with a tight store (no ≥20k sample this window). Holding off a new remote matches shard3 CPU caution (12h avg 17.44 / 20, max 34.94, zero ≥40, bucket stayed full).

See also state/_review12h_2026-11-22_08/community_practice.md and state/_review12h_2026-11-21_20/community_practice.md.
