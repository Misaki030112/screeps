# Patrol 2026-11-17 12:25 / wrap 12:37 Asia/Hong_Kong

## Alerts
**None.** No new standing formal alerts.

- Formal upgrade (a): HOME exact2h 17.05/26=65.6% (prev 17.20=66.2%) is the **fourth** consecutive under-70% after the 08:23 clear, but short last20–300 is 28.00 e/t=107.7% (not soft). W47 exact2h 17.15/30.08=57.0% (prev 18.90=62.8%) is still under, but short last200–300 recovered to 22.25/21.50 e/t = 74.0%/71.5% after w8upgrader84315293 seated at 11:49. Last hour was the **first** dual-condition (exact2h-under PLUS short-soft at 10.00 e/t). This hour is **not** a second consecutive dual-condition, so formal (a) does not fire. last20–100 softer (15–20 e/t) is a handoff dip (84314793 leaving, 84316232 not seated), not the hour's short window. Designed 15k-floor 14 e/t is not in play for home this hour.
- Formal storage (b): tip stor 17012 ABOVE (prev 15154 ABOVE, tip_consec_under=0). since_last under15k=0/73. Does not fire.
- Formal missing-role (c): colony reserver count was zero only 70 t (12:16–12:22), under the 100 t threshold. Miners/rminers/queens/w8fillers present.
- Formal deploy (d): creep_audit --patrol exit 2, REGRESSION [deploy] **identical** to 11:37 and 10:33 vs 85c19c2e. Known, not new.
- Formal CPU (e): 1h mean 18.92 max 29.11, bucket min 9999 / 10000. Not near drain.

## Key numbers (TIP 84316290 12:30:54 HKT; later live ~84316355 12:35)
- HOME: exact2h 17.05/26=65.6%; 1h 21.01=80.8%; short 28.00=107.7%; stor tip 17012, later ~16672; nUp 1→2@11:54, brief 3@12:29 handoff, live nUp=2 work=28; RCL7 69.04%. 20k/300t unlocked (6h max 19439, hour max 19088, span=0).
- W47: exact2h 17.15/30.08=57.0%; 1h 17.51=58.2%; model_w8 1h 17.55 / 2h 17.2 vs 30.03; short last200 22.25=74.0% last300 21.50=71.5% last20 15.00=49.9%; stor tip 31038, later 30238; keep=2. 40k/500t unlocked (longest span still 470 t, 30 short; 6h max 44416; hour max 35289). src_A 0.0 is the known link-at-26,12 measurement artifact.
- W47N7 core: killed 11:44 by full-budget rdef84315321; rdef recycled ~11:51; live SAFE, no core, reservation ~3012, miners seated.
- W47 second upgrader: 84315293 seated 14,27 at 11:49 after ~200 t spawn-pocket oscillation and is still working (ttl~476). New 84316232 (12:26 hatch 12:29) is repeating the 32,30/33,31 empty oscillation as of 12:35 dest 12,25. Root is CMV creep-ignored pathing + stuck-detour bounce in the hub pocket (10W1C2M, 1 tile / 3 t). No code change this hour; do not add a standing third; do not change the 15k floor.
- Remotes: W45N7/W45N8 SAFE, res ~1928 / ~2216. W45N8 reserver expired ~12:16, no replacement yet (reservation healthy). defender84314982 back in W45N8 ttl~260, not recycled. W47N9 still aborted. Labs KO (actOk=0 kBuf). Memory.cmd untouched. safeModeAvailable 6.
- Motion/audit: deploy regression identical; motion findings are known waiting_* plus the pocket upgrader.
- CPU/bucket: mean ~18.9, max 29.11, bucket full.
- Infra: postgres/Grafana/listener/dashboard ok. Listener single-slot 5:5:1:1, no commander yield. Box pause 11:48:38–11:51:05 (137 s) is a known platform limit.

## Backfill / leftovers
- 40m official backfill 84315501..84316200: missing_chunks=0, inserted=11100, already_in_db=15803, all 5 rooms 700/700.
- tick_s first 4.66586 (printed 4.666) over45=120; in-use 4.67987 (12:00 later-mean-robust); corrective nfix=0.
- Retry: all 21 leftover 404s still 404, inserted=0.
- Remaining unfilled holes to report: **W45N8@84314900 (84314901..84315000)** and **W47N7@84315100 (84315101..84315200)**. Older leftovers unchanged (incl. W45N7@84314500). Unpublished latest ~100-tick chunk (84316201+) expected. W45N7 previous-window empty-no-creep gaps are not 404s.

## Code / deploy
No code change, no new deploy. LIVE still 85c19c2e.

## Userlog
See `state/_patrol_2026-11-17_1225/userlog_zh.txt` (plain Chinese for Misaki).
