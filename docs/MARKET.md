# Market and minerals (strategy review 2026-10-19 22:4x)

Snapshot tool: `python3 tools/market.py` (read-only, 3 console queries, writes `state/market.json`). It never trades.
Any `Game.market.deal` / `createOrder` / credit spending is **Misaki's decision**.

## State (t83746371, 2026-10-19 22:45 UTC+8)
| | W46N8 (home, RCL6) | W47N8 (RCL4) |
|---|---|---|
| Mineral | **O**, density 2 (35k/cycle), **depleted**; regen in 39,050 t, about **10-21 20:30 UTC+8** | **K** 35,000, no extractor (RCL6) |
| Built | terminal (0 energy), extractor, container 41,24 (152 O), **3 labs (empty, no lab code)** | - |
| Stock | **34,848 O** (storage 17,324 + terminal 17,524) | 0 |
| Credits | **0** (never traded) | |

One full O cycle (10-18 10:11 to 10-19 07:57, ~16.6k ticks) took **11 mminers (12W3M, 1,350 e each) ≈ 14.9k energy** plus home-hauler
trips, i.e. **~0.9 e/t**, about 4% of the home upgrade rate (23 e/t). That is ~0.43 energy per O.

## Market (shard3, 22:45)
- Market is thin: 17 O buy orders, 18 energy sell orders. O history avg 27.0 / 24.3 / 22.3 (10-17..19, ~1.5-2.9M/day); K 13-16; energy 15.5-17.6.
- Best O bids: **W20N0 27.52 x 13,944, transfer 0.58 e/unit** (47 credits per energy spent), then 23.4-26.6 at 0.73-0.86 e/unit.
- Energy asks: best delivered **38.0 credits per gross unit at 0.65 e/unit transfer = ~107 credits per NET energy**.
  Transfer cost = `ceil(amount * (1 - exp(-dist/30)))` (Screeps docs). The dealer pays it. Every seller is 30+ rooms away, so
  a bought unit of energy arrives with ~0.35 net.
- Round trip O -> credits -> energy: 1,000 O = 27.5k credits minus 580 e, which buys ~720 gross / ~256 net energy. **Net about -320 energy.**
  **Buying energy is never worth it from this location.** Remove it from the option list.
- Creating our own orders costs a 5% credit fee up front (docs). With 0 credits, the first sale can only be a `deal` against an existing bid.

## How the reference bots handle it
- **Overmind** (`TerminalNetwork.handleExcess`, threshold 25k per resource): above 25k it sells through its own orders. Above 50k
  (2x), or when the terminal is near full, it sells directly. `TraderJoe` keeps reserveCredits 10k and buys energy only with credits > 50k.
- **TooAngel** (`config.market`): keeps `minAmountToSell` 50k of each mineral in the terminal and sells only above that. It sorts bids
  by `transferCost - price*amount` (energyCreditEquivalent 1). `mineral.storage` caps extraction at 100k.
- Both run many rooms and labs. Neither sells below ~25-50k, and neither buys energy across the map.

## Conclusions
1. **Energy purchases: no** (~107 credits per net energy, and we have 0 credits). Selling energy is also no: home is energy-bound and every unit goes to the controller.
2. **O stock 34.8k is idle.** Labs have no code, and making compounds needs a second mineral (buy = spending credits). The O has
   two uses: (a) a credit fund for emergency boost/mineral purchases after 10-28, or (b) future labs (OH etc.) after RCL7/8.
   Selling the W20N0 lot (13.9k O at 27.5, transfer 8.1k energy) would give **~384k credits** and leave ~21k O. That is a
   Misaki decision, and the energy cost is real: 8.1k e ≈ 350 ticks of home upgrade, ~25 min later RCL7. The energy has to be
   in the terminal first (now 0).
3. **The next O cycle (from ~10-21 20:30) costs ~15k energy (~0.9 e/t for ~16.6k ticks) during the RCL7 push.** Stock is already
   above Overmind's 25k excess line. Pausing extraction until labs/market are used saves ~15k energy, about **40 min earlier RCL7**
   (15k / 23 e/t ≈ 650 t). The minerals stay in the ground, so nothing is lost: regen restarts only after depletion, so pausing delays
   the following cycles too. Over a 50k-tick regen we forgo ~35k O (~0.95M credits gross at today's bids) per 15k energy.
   The trade is worth it only once credits or labs have a use.
4. W47N8 K: no extractor until W47N8 RCL6. Nothing to do.

## Switch shipped (dormant)
`Memory.ops.mineralCap = N` (`src/managers/spawn.js mineralCapped`, `tests/mineral_cap.js`): no mineral miner while
storage + terminal hold >= N of the room's mineral. Unset (default) = unchanged behaviour (mine whenever the mineral has amount).
- Pause the next cycle (recommended until RCL7 or until a market/lab decision): `Memory.ops.mineralCap = 30000`.
- Undo: `delete Memory.ops.mineralCap`.
It has no effect before ~10-21 20:30 in any case, because the mineral is depleted.

## Decisions for Misaki
- A. Next O cycle (from ~10-21 20:30 UTC+8): pause it until RCL7 (`mineralCap 30000`, recommended, ~+15k energy to upgrade), or keep mining (default).
- B. Sell O: none (default, recommended until there is a credit use), or sell the best lot only (~13.9k O -> ~384k credits for ~8.1k energy) as an emergency credit fund for after 10-28.
- No energy buying in any case (~107 credits per net energy).

## Lab scaffold + boost path (2026-10-20 21:0x, Misaki "开矿物线")
Live t83765239: terminal, extractor, container 41,24, mminer, hauler mineral run and 3 labs (34,22 out; 33,21 + 35,21 in, all range <= 2)
already stand since 10-18. O 34,848 in stock, mineral regen ~10-21 20:37. Credits 0.
`src/managers/labs.js` (tests/labs.js) runs the reaction only with `Memory.ops.labs = { W46N8: 'KO' }`; `task()` (terminal<->lab
moves) is not wired to a carrier yet. Off = zero cost.
Prices (sell, shard3): K 14.95 (hist 18.7), L 148, U 15.7, H 144, KO 44.9 (500 only), LO 157, UH 15.5 (327 only), OH 686.
Realistic: sell O for credits -> buy K -> KO (ranged x2 via RANGED_ATTACK boost) with our own O. 1 KO = 1 K + 1 O; boost = 30 KO + 20 e per part.
