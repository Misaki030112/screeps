# Remote evaluation — 2026-10-14 14:30 (UTC+8)

Analysis only. Nothing built, reserved or spawned. Generator: `tools/remote_eval.py`. Raw numbers: `metrics/remote_eval.json`. Map: `remote_eval.png`.
Inputs: live terrain and objects from the API (shard3, W46N8/W45N8/W45N7/W46N7), 24h of `creep_ticks` and `path_arrivals`, and 6h of `creep_cpu`. A tick is about 4.0 s.
Movement model: road 1, plain 2, swamp 10 fatigue per non-MOVE part; each MOVE removes 2 per tick.

## A) Pave the whole route from the W45N8 container (13,11) to the home controller container (30,30)

| Item | Value |
|---|---|
| Route | 35 tiles: W46N8 13 road + 9 plain; W45N8 1 road + 12 plain. **0 swamp** |
| Unpaved | 21 tiles, all plain: 21 × 300 = **6,300 e** (plus about 250 builder-ticks of 5 WORK, plus travel) |
| Decay upkeep (new tiles) | 21 × 0.001 = 0.021 e/t |
| Wear upkeep (ROAD_WEAROUT, 1 hit/part/step) | about 0.13 e/t on the new tiles |
| Measured rhauler cycle (24h, n=279) | q25/50/75 = 83 / 93 / 120 t. Model travel 74 t; the rest is waiting at the container. |
| Measured legs (path_arrivals) | W45N8 leg planned 12.0 / actual 12.2; W46N8 leg planned 19.8 / actual 22.0 |
| rhauler states (24h) | 51% loaded moving, 46% empty moving or waiting, 3% spawning |

Hauler options for 10 e/t from a reserved source:

| Body | Roads | Round trip | Creeps | Body cost e/t | Spawn share | CPU ms/t |
|---|---|---|---|---|---|---|
| 8C8M (live, 800 e) | today | 74 | 2 (need 1.85) | 1.07 | 6.4% | 0.45 |
| 8C8M | fully paved | 74 | 2 | 1.07 | 6.4% | 0.45 |
| 16C8M (1,200 e) | today | 95 (half speed on plain) | 2 | 1.60 | 9.6% | 0.45 |
| **16C8M** | **fully paved** | 74 | **1 (need 0.93)** | **0.80** | 4.8% | **0.23** |

Key point: the route has **no swamp**, so the 1:1 hauler already moves at full speed (1 tile per tick) on plain. Roads would not make deliveries faster. They only let us drop half the MOVE parts and one hauler.
- Gain: 1.07 − 0.80 = 0.27 e/t, minus about 0.15 e/t of upkeep = **about +0.12 e/t net**. CPU saving 0.23 ms/t (about 5% of our CPU).
- Payback: 6,300 / 0.12 ≈ **52k ticks ≈ 58 h** (ignoring builder time).
- Risks:
  - A single hauler at 93% utilisation has no slack. One death or one Invader pause means 0 delivery until it is replaced.
  - The 16C8M costs 1,200 of our 1,300 capacity, which competes with the defender's 1,300.
  - Roads in W45N8 sit on the Invader path from the bottom edge. Invaders rarely target roads, but stray damage is possible.
- **Recommendation A: not now.** It is a positive return but small, with a 2.4-day payback and lower robustness. It becomes worthwhile when:
  - (a) a second remote shares the same trunk (see B, where paving pays back about 8× faster), or
  - (b) at RCL6+ one 32C16M could serve 20 e/t.
  - The ~20 tiles already flagged are worth paving only together with (a).

## B) W45N7 as an additional reserved remote

Live state (API, 14:20):
- Status: normal; novice zone (same novice timestamp as our rooms).
- **1 source** at (21,16), currently 1,500 because it is unreserved. invaderHarvested = **169,254**, so an Invader wave there is likely soon or overdue.
- Controller (6,40): unowned, no reservation, no sign. It is 97 tiles from our spawn (reserver walk).
- **BustJetter (The Council) container construction site at (22,15) next to the source: 2,865 of 5,000 progress.** The Council is actively setting up this source as their remote. The 169k harvested is consistent with them mining it.
- An inactive spawn of user `fhl` sits at (13,10) (off: true, an abandoned leftover).
- Exits:
  - North to W45N8 and south to W45N6.
  - The east edge is a constructed-wall line (x=49, y 4–47), the novice border, so there is no exit there.
  - The west edge is terrain wall.
  - It is reachable only through W45N8's bottom edge. That is the same edge Invaders use for W45N8, and Council creeps going to W45N7 pass the same corridor.
- W46N7 (south of home) is FungousCoast245's **RCL8** room, with 6 towers and 3 spawns. It has no exits north or east, so it cannot be reached directly. Not relevant for this route, but a strong neighbour.

Economics (route 76 tiles to the ctl container; 18 tiles shared with route A; 3 swamp tiles in W45N8):

| | Unreserved | Reserved, today's roads | Reserved, fully paved (+58 tiles, 21,000 e) |
|---|---|---|---|
| Gross | 5 e/t | 10 e/t | 10 e/t |
| Haulers | 3 × 8C8M | 5 × 8C8M (need 4.2), round trip 168 | 2 × 16C8M (need 1.95), round trip 156 |
| Hauler e/t | 1.60 | 2.67 | 1.60 |
| Miner, container, reserver | 0.30 + 0.5 | 0.47 + 0.5 + 1.29 (1 CLAIM2 per ~1,006 t; walk 97 of 600 TTL) | same + roads 0.11 |
| Defender exposure | ~0.03–0.28 | ~0.03–0.28 (1 wave per ~10k t at 10 e/t; 280 e net per dispatch) | same |
| **Net** | **≈ 2.3 e/t** | **≈ 4.8 e/t** (≈ 4.1 after an assumed ~15% Invader pause) | **≈ 5.75 e/t** |
| Upfront | container 5,000 | container 5,000 | container 5,000 + roads 21,000 |
| Spawn time added | ~10% | **+19%** (26% → ~45% of the single spawn) | +13% |
| CPU added | ~1.0 ms/t | ~1.7 ms/t (7.5 creeps × 0.23) | ~1.0 ms/t |

- Measured overhead: real W45N8 cycles run about 25% above model travel, so the realistic need is 5–6 haulers unpaved.
- Alternatives:
  - Spending the same spawn time on extra upgraders gives **nothing**. Upgrading is energy-bound: 2 × 12 WORK already use about 24 e/t of the ~20–24 available. The spawn sits at 26% busy.
  - An extra remote is the only lever that raises income. +4.8 e/t is about **+25% upgrade rate** (19 → 24 e/t), roughly 2.5 h earlier to RCL5 over the remaining ~135k.
- Invaders: W45N7's counter is already 169k, so a wave is due. Our defender only engages a single non-healer. Mining there would also count towards the next wave (one per ~10k ticks at 10 e/t).

**Political risk: high.** This is not "adjacent to" a Council remote; it **is** an active Council remote under construction right now. Reserving the controller would block their harvesting at 3,000 and block their reservation. It would very likely be read as a hostile act by BustJetter and Fandalah, who already scout us daily. Our standing rule says to ask before provoking The Council.

**Recommendation B: do not take W45N7 now.** Re-evaluate if:
- the Council container site is abandoned (it decays) and no Council creeps are seen there for more than 5k ticks; or
- after RCL5, when a bigger spawn capacity and the defence review (10-25) are done.

If Misaki wants more income without politics, the next step is to scout the other neighbours of W45N8 and W46N8 for free sources. Ask before expanding.

## Decisions for Misaki
1. A: accept "don't pave now". This is the default; nothing changes.
2. B: confirm we leave W45N7 to The Council, or explicitly approve contesting it. Contesting is not recommended because it is a provocation and needs approval under the standing rule.
