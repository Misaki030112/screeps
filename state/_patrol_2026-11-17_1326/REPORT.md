# Patrol 2026-11-17 13:26 / wrap 13:36 Asia/Hong_Kong

## Alerts
**None.** No new standing formal alerts.

- Formal upgrade: HOME exact2h 20.62/26=79.3% (prev 17.05=65.6%) is ABOVE 70% and short last300 19.83=76.3% is not soft — this **clears** the four-consecutive under-70% streak after the 08:23 clear. W47 exact2h 16.61/30.08=55.2% (prev 17.15=57.0%) is still under AND short is soft (designed keep=2 20 e/t=66.5% at the tip; last200–300 14.85/14.90=49.4%/49.5% from the two ~200 t pocket handoffs). Last hour was exact2h-under but short NOT soft, so this is only the **first** dual-condition, and formal upgrade alert does not fire.
- Formal storage: tip stor 18854 ABOVE (prev 17012 ABOVE, tip_consec_under=0). since_last under15k=3/58 min 14322@12:47. Does not fire.
- Formal missing-role: miners/queens/w8fillers/rminers/reserver present all hour. W47N7 reserve expired 12:45 (550 t zero) but that is a remote reserver with reservation still ~2535, not an owned-room critical-role miss.
- Formal deploy: creep_audit --patrol exit 2, REGRESSION [deploy] **identical** to 12:37, 11:37 and 10:33 vs 85c19c2e. Known, not new.
- Formal CPU: 1h mean 18.77 max 25.60, bucket min 9997 / 10000. Not near drain.
- Formal infra: history backfill succeeded (40m window complete after retry). Writers fresh. Three box freezes are the known platform limit.

## Key numbers (TIP 84317030 13:29:13 HKT; later live 84317110 13:35:30)
- HOME: exact2h 20.62/26=79.3%; 1h 20.62=79.3%; short 28.00=107.7% / last300 19.83=76.3%; stor tip 18854, later 19544; nUp 2→1@12:49 floor_bank →2@13:13; live nUp=2 work=28; RCL7 69.18% later 69.20%. 20k/300t unlocked (6h max 19439, later 19544, span=0).
- W47: exact2h 16.61/30.08=55.2%; 1h 15.86=52.7%; model_w8 1h 15.8 / 2h 16.59 vs 30.03; short last200 14.85=49.4% last300 14.90=49.5% tip 20.00=66.5%; stor tip 30746, later 33240; keep=2. 40k/500t unlocked (longest span still 470 t, 30 short; 6h max 43041; this hour no ≥40k). src_A 0.35/0.77 is the known link-at-26,12 measurement artifact.
- W47 second upgrader: 84316232 seated 12,25 at 12:43 after ~209 t pocket stall and is still working (ttl~676). New 84316732 (13:05 spawn) repeated the 33,31 pocket for ~199 t, seated 14,26 at 13:17, still working (ttl~1176). Root is CMV creep-ignored pathing + stuck-detour bounce in the hub pocket. No code change this hour; do not add a standing third; do not change the 15k floor.
- Remotes: all three SAFE, no cores/hostiles; res ~2082 / 2369 / 2535. W47N7 reserver expired ~12:45, reservation healthy. W45N8 reserver ttl~74, replacement due soon. w8rminer84317021 walking in for 18,17.
- Motion/audit: deploy regression identical; motion findings are known waiting_* plus the two pocket handoffs (both resolved).
- CPU/bucket: mean ~18.7, max 25.60, bucket full.
- Infra: postgres/grafana/listener/dashboard ok. Listener single-slot 5:5:1:1, no commander yield. Box pauses 12:52–12:54, 12:57–13:00, 13:18–13:26 (436 s) are a known platform limit.

## Backfill / leftovers
- 40m official backfill 84316301..84317000: first-pass missing_chunks=3 (W47N8/W45N8/W47N7@84316900), inserted=7633, already_in_db=17691; retry recovered all 3 (inserted=2410); after retry all 5 rooms 700/700, holes [].
- tick_s first 4.58527 (printed 4.585) over45=479; in-use 4.58527 after corrective nfix=479 (later_mean 4.73886 would have drifted ~107 s on already-aligned rows); after over45=0.
- Retry leftovers: all 21 older official 404s still 404, no older recoveries.
- Remaining unfilled holes to report (outside this 40m window): **W45N8@84314900 (84314901..84315000)** and **W47N7@84315100 (84315101..84315200)**. Older leftovers unchanged (incl. W45N7@84314500, W47N8@84314000, W46N8@84313200). Unpublished latest ~100-tick chunk (84317001+) expected.

## Code / deploy
No code change, no new deploy. LIVE still 85c19c2e.

## Userlog
See `state/_patrol_2026-11-17_1326/userlog_zh.txt` (plain Chinese for Misaki).
