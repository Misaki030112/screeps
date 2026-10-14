# Model and road audit, 2026-10-14 14:50 (analysis only: no deploys, no construction sites placed)

Data window: the last 24 h from TimescaleDB (creep_ticks, creep_cpu codes, path_arrivals, room_stats, events), plus live terrain and objects.
Script used: `tools/model.py --hours 24`. Heat map: `docs/road_heatmap.png`.

## 1. Model assumptions vs measured

| # | Assumption | Model | Measured (24 h) | Error | Fix |
|---|---|---|---|---|---|
| 1 | A→ctl hauler round trip | 54 (8C8M body) → **55** (live 14C7M) | median cycle 59.5 | +8% | **Done:** per-route live body. The remaining ~4 ticks are pickup waits (code p is 15%). The old "28 vs 57" gap was already closed by an earlier route fix. |
| 2 | Remote round trip | 74 | median 92.5 | +25% | The extra time is waiting at the remote container: rhauler p 17.7%, and the top standing tile is W45N8 (12,10) with 4567 ticks. Haulers are over capacity: 16 CARRY live vs the 13.8 needed. Next: feed the measured wait into the model as a term. |
| 3 | Remote income | 10/t | 6.9/t (includes the pause) | −31% | **Done:** `REMOTE_AVAIL=0.93`. The Invader pause on 10-14 ran 04:56–06:41, about 105 min, which is about 7% of the day. Model income is now 9.3. The rest of the gap comes from hauler and miner turnover and the rminer's n/e codes (7%). |
| 4 | Home source income | 10 + 10 | 9.29 + 9.23 | −7% | Miners spend 95.8% of ticks in w. The losses come from the replacement walk: miner A plans 26 tiles but takes 53–55 ticks, because 5W1C3M moves at 2 ticks per plain tile. Next: add a miner pre-spawn lead of about 55 ticks, or 6W3M. |
| 5 | Upgrader cap | 24 WORK = 24/t | 1 h 19.9/t, peak 24 (13:55–14:25), 24 h 14.8 | — | The cap is right. The 24 h figure includes the early regime: upgraders waited on energy (code u) 27.7% of the time over 24 h, against ~5–11% now. |
| 6 | Upgrader walk to post | not modelled (plan 4–6 tiles) | 16–47 ticks | ×4–8 | A 12W1C1M body moves at 7 ticks per road tile and 13 per plain tile. The pre-spawn lead of 70 covers this. The model should add travel ticks × 12 WORK as lost upgrade, about 0.4/t for 2 upgraders. |
| 7 | 24 h upgrade rate came out null | bug | — | — | **Done:** the query now uses only rows at the current RCL, because the window spanned RCL3→4. |
| 8 | Queen ferry storage→ctl | not modelled | queen m 58%, f 24%, w 15.5% | — | Add it as a carrier term: 8C4M moves at 2 ticks per plain tile loaded, about 7 tiles each way. It is not a bottleneck today. |
| 9 | Tick coverage | assumed 100% | **79%** (17112/21688 ticks; per hour 47–100%) | — | Not 38%. Income is already normalised by coverage. Keep the normalisation, and show coverage next to every rate. |
| 10 | room_stats ingestion | — | 1711 rows / 24 h, last row 14:47 | — | **Recovered:** rows are about every 10 ticks again. The 02:13 stall is no longer present. |
| 11 | Road decay | 0.103 e/t | — | — | 47 roads, 14 of them on swamp. The number is negligible. |
| 12 | Ideal overhead | 6.5 e/t (live 8.5) | — | — | Live creeps cost 7.7 e/t. Spawn is busy 35% of the time. |

Still missing from the model:
- RCL5: a controller link, and the switch of A and remote deliveries from ctl to storage. Routes A→storage are 20 tiles vs A→ctl 25, and R→storage 30 vs R→ctl 35, so the carry need drops by about 20%.
- Link transfer loss: 3%.
- Build energy and ramparts at RCL5: about 40k, which costs roughly 2–3 h of upgrade time.
- CPU per energy: about 4.1 ms per 20 e/t, so about 0.2 ms per energy.
- The pickup-wait term, the per-role travel lead, and the remote pause as a stochastic term (waves are triggered by energy harvested).

## 2. Road audit (heat map = creep moves into each tile, 24 h)

- **Unused roads (0 moves):** W46N8 (25,16), (26,15), (27,14) (an old west spur) and (31,24). Together they cost about 0.004 e/t to keep up, which is negligible. Recommendation: drop them from the builder repair list and let them decay. Do not spend effort dismantling them.
- **Most-walked unpaved tiles at home:**
  - (35,26) 866, (35,24) 856, (34,25) 466, (36,25) 379: these are the filler-A stamp interior (link at 35,26, container at 35,24, filler stand tiles). **Do not pave them**; they are reserved by layout v2.
  - (36,30) 392: the manager tile. Do not pave.
  - (39,24) 548: the planned mineral container tile.
  - (40,23) 679, (44,19)…(49,14) about 370 each: gaps in the remote trunk.
- **Remote trunk gaps:** 21 tiles, about 6300 energy. Re-checked with the heat data. The rhaulers are 8C8M, so they already move at 1 tile per tick on plain. Paving only pays through a 2:1 body swap, with about a 58 h payback and a single-hauler risk. **Verdict unchanged: wait for RCL6 or a second remote that shares the trunk** (see REMOTE_EVAL).
- **Swamp walked off-road:** (32,26) 111 hauler, 82 rhauler and 71 queen moves; (32,24) and (31,25) 30–80 each. These are swap and side-step detours around the stamp. A loaded 14C7M hauler takes 10 ticks on swamp. Total waste is about 400 moves/day, which is too small to justify a 1500-energy swamp road.
- **Standing hotspots** (hauler, rhauler and queen ticks with no move):
  - W45N8 (12,10) 4567 and (13,10) 2019: waiting at the remote container.
  - (31,13) 2169: hauler A waiting at its container.
  - (34,25) 2011: the queen.
  - (37,32) 1211: the storage edge.
  - These are waits for cargo, not congestion. No stuck or ping-pong pattern: planned vs actual path length is 19.2 vs 20.3 for haulers and 15.8 vs 16.9 for rhaulers, about 6% over.
- **Spawn exit:** (35,29) is unpaved plain, so a 1-MOVE upgrader spends 13 ticks on its first step. Paving (35,29) costs 300 and saves about 6 ticks per upgrader spawn. That is roughly 0.05 e/t, about a 6k-tick payback. Optional, low priority.
- **Fixed routes vs reality:** 86% of hauling ticks are on or next to the model routes. The off-route ticks are the stamp interior and the spawn.

### RCL5 plan check
With the recommended option A (links at hub 37,29 and controller 30,31, docs/RCL5.md):
- Hauler A can deliver to storage, 20 tiles instead of 25. The A→ctl road segment south of y≈24, (30–32, 24–29), then carries only queen and builder traffic. Keep it, since it is also the upgrader and builder access.
- Remote deliveries go to storage, 30 tiles instead of 35.
- No new roads are needed for links. Re-run this audit after the links are live.

## Recommended changes (proposals, nothing placed)

| Change | Energy | Benefit |
|---|---|---|
| Stop repairing the 4 unused roads | 0 | about 0.004 e/t plus builder trips |
| Pave (35,29), the spawn exit | 300 | about 0.05 e/t, faster upgrader and hauler exits (optional) |
| Remote trunk, 21 tiles | 6300 | +0.12 e/t, 58 h payback: **defer** |
| Pave swamp (32,26) | 1500 | <0.02 e/t: **no** |
