# Ideal-efficiency model (`tools/model.py`)
Rerun (the patrol can call this every iteration): `.venv/bin/python tools/model.py [--hours 6] [--no-db]`
Outputs: `metrics/model.json`, `docs/model_routes.png` (terrain + ideal routes + 6h traffic + tiles to pave), DB table `model_params(ts,key,ideal,actual,unit)` → Grafana panels "Ideal vs actual".

## Model
- Terrain from `data/terrain_<room>.txt` (API fetch if missing), live objects from `game/room-objects`. W46N8 and W45N8 are joined into one 100×50 grid (exit seam x=49|50).
- Paths: Dijkstra, cost road 1 / plain 2 / swamp 10 (same as `src/utils/move.js`), obstacles = non-walkable structures; target range 1.
- Ticks/tile: fatigue = terrain factor × non-MOVE parts (empty CARRY weightless), each MOVE −2/tick. 1:1 hauler loaded: plain/road 1, swamp 5.
- Per source 3000/300 = 10 e/t (owned or reserved). Miner needs 5 WORK. Hauler CARRY = income × (round-trip ticks + 4) / 50 (≈ 2·dist·income/50 without swamps).
- Overhead = Σ body cost / lifetime (1500, CLAIM 600) + container decay (0.1 owned / 0.5 remote) + road decay. Max upgrade = income − overhead. Upgraders are WORK-bound if Σ WORK < that, energy-bound otherwise.
- ETA RCL4..6 = remaining progress / max upgrade rate (3.9 s/tick).

## Actuals (DB, default 6 h)
upgrade rate (room_stats progress), pickups per source (positive store deltas within 2 tiles of the source, normalised by tick coverage — a lower bound), deliveries (hub vs controller container), per-role idle/repaths/CPU (creep_cpu), planned vs actual path length (path_arrivals), hauler cycle median, share of hauling traffic on ideal-route tiles ± 1.

## Audit 2026-10-15 (first principles + 6 h data, window 05:38–11:38 after the Invader incident)
| Component | Verdict | Note / fix |
|---|---|---|
| Source 3000/300 = 10/t, reserved 3000 | correct | unreserved remote would be 1500 (5/t) |
| Container decay 0.1 owned / 0.5 remote | correct | |
| Road decay 0.001/t plain, 0.005 swamp | correct | road on wall (×150) not handled, none today |
| Body cost / 1500, CLAIM 600 | correct | upgrader upkeep folded via 1300/1500/12 per upgrade/t |
| Miner 5W1C3M = 700 | correct | |
| WORK-bound vs energy-bound | correct | 24 WORK > 23.2 available → energy-bound |
| Travel/fatigue + carry formula | correct shape, optimistic ~10% | measured cycles hauler 70 vs 64, rhauler 92 vs 84: add swap/pickup/blocked overhead |
| Tick time 3.9 s | **wrong** → fixed | now measured from room_stats (4.08 s) |
| Link loss 3% | **missing** | ~0.2–0.3/t on hub→controller flow |
| Tower energy (repair/attack), rampart decay 0.03/t each | **missing** | small now; grows with walls (RCL6+) |
| Construction / storage refill (Δstorage) | **missing** | model is steady-state; actual upgrade must be compared as upgrade + build + Δstorage |
| Miner replacement gap (no pre-spawn) | **missing** | remote pickup 8.2/t vs 10; miner pre-spawn pending |
| Structure | improve | rewrite as explicit flow balance: gross income − (upkeep + decay + link loss + tower) = upgrade + build + Δstorage |

## Source-rooted flow (tools/flow.py, 2026-10-15) — replaces the "income − overhead" headline
Per source: gross 10/t → losses (container decay, link 3% on B's storage→ctl leg) → source upkeep (miner, haulers with ×1.10
congestion/pickup on the round trip, reserver for the remote) = net. Shared upkeep (queen, builder-lite, roads, ramparts 0.03/t each)
once; upgrade = net / (1 + 1300/1500/12). Steady state has no downtime (REMOTE_AVAIL=1); Invader risk is the separate stochastic layer:
EV = episodes per tick (events table, 7 d) × per-episode (downtime ×10/t, defender 1300 × defenders/episode, container rebuild 5000 × 0.25).
Gains: Invader tombstones only hold carried resources (none), body energy is not refunded → 0.
Validation compares upgrade_expected with measured upgrade + build + storage delta. ETA hours use measured tick seconds.

10-15 11:45 (6 h): A 8.78, B 9.13, R 5.99 net; shared 1.43; net 22.47 → upgrade 20.96 steady, 20.31 with Invader EV 0.69/t (range 0.11–1.15;
3 episodes / 7 d ≈ one per 19.5k ticks ≈ 195k remote energy). Measured sinks 18.40 + 0.51 + 0.19 = 19.10 (−6%; last 2 h upgrade 20.7, +2%).

## 2026-10-16 18:00 update: W45N7 added (flow.EXTRA_REMOTES)
W45N7 net = 10 − 0.5 container − 0.53 miner − 1.23 reserver − 3.20 haulers (6×8C8M) = **4.54/t** (the design figure of 4.2 included congestion).
Total net 28.09 → **upgrade ceiling 26.2/t** (steady state, before Invader EV). Invader EV in the DB is 0 now: the events table was lost in the 10-15 reset. The last measured value was 0.69/t for one remote; budget 0.7–1.4 for two. The realised share has been about 94% of the model (10-15 check: −6%). **Realistic steady rate is 24–25/t.**
WORK cap: 12W per upgrader (1800 cap, code min 12); 3 upgraders = 36 WORK, so the rate is energy-bound, not WORK-bound. 2 upgraders = 24 WORK is binding just below the ceiling.
Spawn: about 0.38 utilisation pre-W45N7, plus about 0.23 for W45N7 (96 hauler parts, 10 miner, reserver ×2.5), plus a 3rd upgrader → about 0.65. One spawn is enough.
Fluctuation (hourly W46N8 rate 10-16 00–15h, W45N8 only): 17.0–23.4, median about 20; a ±3/t band per hour. New sources of dips: remote opening spawn contention (16:00h 14.6/t, fixed in 147bbda); a miner swap deadlock (fixed in 00e1ded); the 3rd upgrader gate (storage ≥ floor+1000).


## 2026-10-20 00:5x: home ideal includes W45N7; upgraders were the cap

- `upgrade_max_ideal` summed A + B + W45N8 only (21.8). tools/flow.py already had W45N7 (net 4.54 after its rminer, 4x8C haulers, reserver), and the hauler need was fixed for the same gap at 21:5x. The ideal is now 26.0 (3-source value kept as `upgrade_max_ideal_3src`). `upgrade_max_live_comp` / `upgrader_bound` still use 3 sources; read them with that in mind.
- 6h balance: upgrade 22.7 + builder 2.4 + storage -0.2, plus upgrader upkeep ~1.7, comes to ~26.9 of a flow net of 28.1, so ~1.2 e/t is overhead above the model (extra queen/rhauler bodies). Energy is not lost. Live at 00:4x the ctl container was full (2000) with 2x12W: WORK-bound, not energy-bound.
- Lever: 14W1C2M upgraders at RCL6-7 (e1df502). 28 WORK sits just above the ~26 feed, so the room stays slightly energy-bound and the 3rd-upgrader gate is a sticky surplus latch (storage ≥ floor+5000 / ctlEma ≥ 1200 for 300 t, leave floor+3000 or ema<700; 12h review 2026-11-10 20:2x). The old floor+1000 / ema 700 gate yo-yoed a 1550 body the ≈21.7 e/t feed cannot support. 12h review 2026-11-11 08:2x: latch settled (net sp:upgrader 1.18 e/t; upExtra never armed — no ≥20k stretch held 300 t).

## 2026-10-20 02:4x strategy review: does home still need its hauler at RCL6?

Open question from the 23:5x evaluation: the home hauler (link era, 6C3M, 450 e, upkeep 0.30 e/t) shows ~97-100% waiting_pickup.
- **Measured (creep_ticks, 6 h to t83749739, role hauler in W46N8):** picked 900 e and delivered 1050 e in 5109 ticks, about **0.18 e/t**. All pickups were at 33,30 (hub side) and 750 of the deliveries at 31,29 (ctl container 30,30); 0 pickups at source A container 31,12. Live: container 31,12 at 72, link 30,11 cycling (150, cooldown 6), 0 drops. Link 30,11 carries all of source A; the hauler is a slow spare ferry.
- **Saving if removed:** ~0.3 e/t (about 1.1% of the 26 e/t upgrade), so RCL7 lands ~1.5 h earlier out of ~5.5 days. Small.
- **Why not remove it now:** (1) `bodyEnergy('queen')` sizes a queen to `energyAvailable` when no hauler is alive, so hauler 0 would quietly shrink queen bodies; (2) the hauler is the only creep that empties the mineral container 41,24 during an O cycle (next regen ~10-21 20:30) and clears source A overflow if link 30,11 stalls; (3) the 2-creep emergency path (`!alive.hauler && !alive.queen ...`) assumes it. Taking it out means decoupling all three for 0.3 e/t.
- **Decision:** keep 1x 6C3M through RCL6. At RCL7 sizing, if Misaki pauses the O cycle (`Memory.ops.mineralCap`, still awaiting her answer since 22:4x), revisit as spawn-on-demand (hauler only while container 31,12 > 1000, mineral container > 400, or drops > 300) after decoupling the queen sizing from `alive.hauler`.

## 2026-10-20 04:4x strategy review: home realistic upgrade ceiling, RCL7 ETA, reserve7 owner

Question: home "ideal" is 26.0 e/t but hours rarely exceed ~25 and the 24 h average is 18.7. Is energy being lost, and when does RCL7 really land?

- Measured (room_stats, RCL6): 24 h 18.69 e/t (4.25 s/t; includes the 10-19 W47N8 fight and the wall builder before the 00:3x step-2 hold),
  6 h 21.86 e/t (+ build 1.71 + storage +0.19 = **23.75 e/t to sinks**). Hourly 10-20: 00h 25.4, 01h 24.8, 02h 26.3, 03h 13.8, 04h 18.8.
- Conservation holds: 03h upgrade+Δstorage = 16.0 vs ~24.4 the hours before; the ~8.4 e/t x ~850 t ≈ 7.1k gap matches the home-funded joint
  defence (2x 11RA11M 2200 + w8healer 11H11M 3300 ≈ 7.7k). The bank-first rule (0ff7935) only changes *when* storage is refilled; it loses nothing
  while upgraders are not WORK-capped (28 WORK vs ~24 e/t). Closes the 03:5x ROADMAP watch on the "hard 15k switch".
- Why ~23.75 and not 26.0: the flow ideal (net 28.09) omits upgrader bodies (2x 14W1C2M = 2.07 e/t), the 2nd queen (Misaki's refill-speed
  sizing, 16C8M + 22C11M = 1.9 vs 0.43 modelled) and **reserve7** (W47N7, W47N8's remote, paid by home ≈ 1.3 e/t). 28.09 - 2.07 - 1.47 - 1.3 ≈ 23.3
  → home runs at its realistic ceiling. Use **~22-23 e/t** (not 26) for home ETAs.
- **RCL7 ETA:** 3.049M left at t83751450. 6 h rate 21.9 → ~139k t → **~10-27 01:00 UTC+8**; 24 h rate 18.7 → ~10-28 04:40 (after novice end 10-28 03:33).
  Each home-funded defence episode like 03h costs ~7k ≈ 20 min. Wall step 2 (300k, ~69k e) waits for RCL7 (Misaki 10-19 20:51), so it starts ~10-27.
- **Lever shipped bd442b2 (deployed t83751519, dormant until W47N8 cap ≥ 1800 = RCL5 ~08:50):** reserve7 is spawned by W47N8 Spawn2; home is the
  fallback only when our W47N7 reservation is < 1000 (or W47N8 can't). PathFinder: Spawn1 → W47N7 ctl 102 tiles, Spawn2 73 tiles, so the colony saving
  is small (~0.1 e/t); the point is moving ~1.3 e/t off home (≈ 8k t ≈ 9-10 h earlier RCL7) onto W47N8 (≈ 2-3 h later RCL6 ~10-22, which adds no tower).
  tests/reserve7_owner.js. Revert = one commit if Misaki prefers W47N8 RCL6 first.
- Not changed: queen pair (Misaki's call), rhaulers (64 CARRY vs need ~65; idle 84% waiting_pickup is remote containers near-empty, not overcapacity of note).

## 2026-10-20 17:4x strategy review: home overhead + CPU

Question: home upgrades ~18.8 e/t against a flow ideal of 26.2 and the 04:4x "realistic ceiling" of 23.3. Where does the rest go, are the
hauler fleets oversized, and what is the cheapest safe cut? Data: `Memory.ledger` (t0 83760934, 1603 t to t83762537, 15:4x-17:3x),
`room_stats` / `creep_ticks` / `idle_by_reason` / `creep_cpu` / `cpu_prof` for 6 h (t83757400-83762600, 5200 t, 4.18 s/t).

**Income (ledger, harvested):** source A 10.00, B 10.00, W45N8 9.92, W45N7 10.11 = **40.0 e/t**. Regen waste 0.08. Every source is fully mined.

**Where it goes, 1603-t ledger window (e/t):**

| Sink | e/t | Note |
|---|---|---|
| upgrade | 19.25 | room_stats progress (ledger `up` says 16.79: about 13% undercount, open measurement issue) |
| spawn bodies, gross | 19.65 | rhauler 3.62, reserver 3.24, **builder 4.37**, upgrader 2.90, queen 1.50, rminer 1.50, w8defender 1.37, miner 0.87, hauler 0.28 |
| ...of which recycled back | -3.5 | 6 builders recycled at TTL ~1300-1450 (tombstones picked up by the home hauler) |
| towers: roads/containers `tr` | 2.62 | **upper bound**: the hook counts every OK `repair()`, the engine charges nothing on a full target (see below) |
| towers: ramparts `tw` | 0.86 | decay top-up of the `rampHW` ratchet (~17 ramparts x 3 hits/t) |
| build `b` | 1.78 | home road sites |
| remote container repair | 1.00 | 0.5 each (decay 0.5/t, as modelled) |
| link loss | 0.38 | |
| storage + ctl container | -1.5 | 15.15k -> 14.1k, ctl container 1.4k -> 0 |

Balance: 40.0 + 1.5 + 3.5 = 45.0 in vs ~45.5 out, closed to ~0.5 e/t.

**Six-hour picture (5200 t):** upgrade **18.80**, storage -0.18. Spawn gross 16.3 e/t: rhauler 4.46, reserver 2.75, upgrader 2.09,
builder 1.73 (~0.5 net), queen 1.38, rminer 1.23, w8defender 0.85, miner 0.81, reserve7 0.75 (home-paid until t83758200; W47N8 pays now), hauler 0.26.
Steady-state bodies for today's fleet: rhauler 3.87 + reserver ~2.5 + upgrader 2.07 + queen 1.60 + rminer 1.07 + miner 0.93 + hauler 0.30 = **12.3 e/t**.

**Gap 26.2 -> 18.8 (7.4 e/t), item by item against the flow model:**
- Towers about +1.3 to +2.9 over the modelled 0.56 (roads 0.23 + ramparts 0.33). Since e3d66d7 (11:4x) towers also keep the W45N8 haul leg 38,30->48,15
  above 60%. That leg is 10-14 tiles from towers 36,29/37,33, so a repair yields 44-60 hits/e, against 100 for a creep. The ledger figure is
  inflated: `towerRep` is re-picked only every 10 ticks, and both towers keep calling `repair()` on a road that is already full (the engine skips it at no cost).
  Closing the balance puts the real tower spend at ~1.5-2 e/t.
- Builds plus builder bodies about +1.9 (b 1.78 + net builder bodies ~0.5, minus the 0.4 builder-lite in the model). This includes the **builder churn** below.
- W47N8 support +1.6 (w8defender 0.85 joint defence, reserve7 0.75 until t83758200). Now ~0.85 and only while the north camp lasts.
- Queens +1.0..1.2 (2x 16C8M = 1.6 vs 0.43 modelled; Misaki's refill-speed sizing, kept).
- Upgrader bodies +0.7 (2-3x 14W1C2M vs the 1300/1500/12 fold).
- Spawn cohorts +0.9 (rhauler/reserver lives bunched in the 6 h window; this shifts energy in time and loses none).
Sum ~9.0 against 7.4 + the -0.2 storage change. The ~1.5 surplus is the tower overcount.
**Root cause, not 4 e/t of loss:** the 23.3 ceiling assumed model tower upkeep (0.56) and no build or defence spend. Correct it for
reserve7 leaving home (+1.3 -> 24.6), then subtract real towers (~-1.5), build (-1.8), W47N8 defence (-0.85) and cohorts plus builder churn (-1.4).
That gives ~19. Upgraders are energy-bound at the 15k floor, so every non-upgrade spend comes straight out of upgrade.

**Builder churn (bug, shipped e774b85 + a263131):** spawn.js spawns one 5W5C5M "road builder" at the 15k floor when a W45N8 route road is
< 30% (`roads.repairTarget(0.3)`; W45N8 2,12 swamp road 6000/25000 = 24%). `builder.remoteRefill` only refilled at the remote container
for road **sites**, so for a **repair** job the builder got nothing at defLow. It idled 50 t next to the spawn (`waiting_feed`) and recycled,
then spawn.js spawned the next one. That happened 7 times in ~1400 t (builder83761171 ... 83762373, lives 18-213 t): 7 x 1000 e cycled through the
extensions, ~45 t of Spawn1 each (~22% of the only home spawn), builder CPU ~0.2 ms/t. Meanwhile 2,12 kept decaying, against
Misaki's "remote roads must never decay away". Fix: `routeJob()` = W45N8 road site or route road < 50%. The builder refills at the W45N8
container for it, route roads < 50% go before home road sites, and a remote repair target stays sticky until 90%. The spawn trigger
stays at 30%, which gives hysteresis. Companion fix: with a builder alive but `T.builder` 0, the "sites ? 1 : 2" rule no longer drops the upgrader target to 1.
Live: 2,12 went 6000 -> 16000 in ~50 t (t83762731), roleTargets upgrader 2 / builder 0, errors 0. Expected: about +0.3-0.5 e/t (recycle loss and
refill churn), ~0.15-0.2 ms CPU, ~20% of Spawn1 time freed, route road kept. Builder churn shows up in patrols as `builder` spawn names < 300 t apart.

**Fleet checks (6 h idle_by_reason, per creep):**
- W45N7 rhaulers 5x 8C8M: moving 70-79%, `waiting_pickup` 14-24%. The W45N8 24C12M: moving 47-54%, waiting 32-45%. Both remotes deliver
  ~9-10 e/t, which is near full. The "83% idle" figure counted only idle reasons; as a share of all ticks, waiting is ~21%. **Not oversized in energy terms.** Trimming
  W45N8 to 16C8M saves only ~0.4 e/t, and with 800 carry container 13,11 reached 1891/2000 on 10-18. Kept.
- Home hauler 6C3M: waiting 69%, 0.3 e/t, 0.16 ms. It is the creep that picked up the recycled builders' tombstones (300 per trip at 34,30) and
  the mineral container. Kept; the spawn-on-demand idea (02:4x) still stands for RCL7.
- Queens x2 (16C8M): target_full 29%, moving 48%, working 19%; energy_fill 0.83. A 3rd is not needed, and 2 -> 1 is Misaki's call (refill speed).


## 2026-10-21 17:4x: home upgrade gap by hour
Hourly `room_stats` (W46N8, progress delta per tick; ctl = avg controller container energy):
quiet hours 10-21 00-08: 22.7 23.4 24.7 19.8 25.8 19.4 25.0 22.8 25.8 (mean 23.3, ctl 280-900).
event hours: 11:00 14.3 (ctl 43, W45N7 Invader pause), 14:00 9.3 (ctl 0, raid9 spawns), 16:00 19.0 (ctl 40, turnover).
12 h model: measured 21.0 vs expected 26.1; storage delta -0.01 e/t; overhead_live 8.74 vs ideal 6.64.
Reading: storage pinned at the 15k floor means upgrade = income - upkeep - event spend. A low hour is the floor rule letting upgraders absorb a spawn burst, which is energy-neutral (the energy is upgraded later). Floor-rule changes cannot raise the long-run rate; only lower overhead or fewer spend events can.

## 2026-10-31 02:4x strategy review: upgrade ~16 vs ideal 26 after walls HOLD (waiting_feed)

**Question:** After peacetime walls HOLD 300k and storage ≥15k floor, why is home upgrade stuck ~16 e/t vs ideal 26 with `waiting_feed` — SEND/CTL_LOW, upgrader count/body, queen/hauler priority, or remote-pause carry gap?

**Quant (room_stats + idle_by_reason, Asia/Hong_Kong):**
| Window | upgrade e/t | vs ideal 26 | vs live_comp ~20.3 | waiting_feed | notes |
|---|---|---|---|---|---|
| 10-30 20–23h (post-HOLD, remotes SAFE) | 19.0–23.3 | 73–90% | ~93–115% | 17–28% | healthy vs live_comp |
| 10-31 00–01h (W45N7 CORE pause) | 16.5–16.5 | ~63% | ~81% | 30–37% | −W45N7 ≈ −4.5 net |
| 10-31 02h (core still ONGOING) | ~19.8 recovering | ~76% | ~98% | ~30% | buster DPS; stor briefly dipped under 15k mid-fight |

- Ideal 26 = A+B+W45N8+W45N7 after upkeep (`upgrade_max_ideal`). Realistic / live_comp ≈ **20–22** (fleet + events). 6h measured **18.8** ≈ 93% of live_comp — ALERT vs 26 is mostly baseline mismatch when a remote is paused.
- Δ pre-core → core ≈ **3.6 e/t** ≈ W45N7 flow net 4.54 / 1.072. Carry "54 vs need 72.8" includes paused W45N7's 48 design CARRY — not a hauler bug.
- 2×14W = 28 WORK capacity; at ~70% working ≈ 19.6 e/t matches measured. Queens ~40% `target_full` (thin surplus 0–2k above floor) — ferry already maxed under supply-follows-demand.
- ctlLink / SEND=400 / CTL_LOW=400 already match Overmind-ish receive threshold (Overmind `linksRequestBelow=200`; we are more aggressive). Lowering SEND further would thrash cooldown without raising long-run rate while income is capped by pause.
- Overmind `UpgradeSite`: scales WORK only with storage surplus above `energyBuffer=100k` — we now gate the 3rd upgrader on a sticky `stor≥floor+5k` and `ctlEma≥1200` for 300 t (leave floor+3k or ema<700). The old floor+1k / ema 700 gate was too tight and spawn-then-recycled. **Do not add WORK while feed-starved.**

**Do / don't:**
| Do | Don't |
|---|---|
| Compare patrol upgrade % to **live_comp / pause-adjusted ideal** (`Memory.ops.upgFeed.idealAdj`) | Treat consec-<70% vs raw 26 as an economy defect during remote DEFEND/WAIT |
| Wait for W45N7 SAFE → expect ~20–22 e/t again | Flip mineral gates / cut reserveE / raise upgrader count |
| Keep CTL_LOW/SEND=400; supply-follows-demand | Tune link SEND mid-core fight |

**Shipped:** `src/managers/upgfeed.js` → `Memory.ops.upgFeed` every 5t from `stats.js` (`why`: remote_pause / ctl_starved / thin_surplus / waiting_feed / ok; `pausedNet`, `idealAdj`, ctl/link/stor/nUp/work/hungry). `tests/upgfeed.js`. No spawn/link behavior change.

## 2026-11-02 05:4x — live_comp~9 vs measured ~20; floor_bank obs

- Snapshot `upgrade_max_live_comp~9` / `upgrader_bound=energy` with stor ABOVE is **misleading**: live_comp = income − **full live fleet** overhead (colony+remotes), so 2×14W always looks energy-bound even when measured upgrade is ~19–20 e/t (~75% of ideal 26). Prefer progress-delta (Grafana/`room_stats`) or patrol 2h %.
- Short soft near 15k is usually **`upBank` hysteresis** (spawn enter reserve−500 / leave +1000), not waiting_feed. `Memory.ops.upgFeed.why=floor_bank` + `upBank`/`tUp`/`allowExtra`/`boundHint` (shipped this review) separates that from ctl_starved / thin_surplus.
- Keep comparing soft to idealAdj / ≥70% band; do not chase live_comp back to 26 by cutting remotes or lowering the floor.

## Wartime upgrade ideal (2026-11-02 14:5x)

Under `pauseCivilians` (W47N9 GO), treat home/W47 **upgrade ideal as ~0** except the downgrade keep (1 upgrader if `ticksToDowngrade < 20000`). Do not chase peacetime 26 / 30.08 e/t until stand-down. Obs: `upgFeed.why=war`, `w8day.bankWhy=war`.

