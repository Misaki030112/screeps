# Home energy-transport analysis — 2026-11-10 (Asia/Hong_Kong)

Misaki (t461u, ~18:29) sent a close-up of the W46N8 controller cluster: three upgraders on the usual spots and a bright yellow glow just below them, and asked whether this is actually appropriate, how the logistics model was built, and whether it is optimal. She asked for recent trajectories, inward and outward haul routes, a real mathematical model, then a self-decision.

This note is measurement-first. No deploy, no Memory write, no PR. Live commit remains `c6c80d3` (PR 33, deploy tick 84183977). All numbers below come from TimescaleDB (`room_stats`, `creep_ticks`, `creep_cpu`) or official shard3 room-history (`GET https://screeps.com/room-history/shard3/{room}/{base}.json`, cached under `state/hist_cache/`). Official history is a full per-tick snapshot of structures and creeps; `creep_ticks` alone cannot support container/link/storage energy. History tick T is the room *after* that tick's intents.

## 1. The screenshot moment

**Best match: official history ticks 84185187–84185191, ~18:20:53 Asia/Hong_Kong.**

The photo was sent at ~18:29, shortly after the 18:28 patrol (tick ~84185280, third upgrader `upgrader84185246` just starting a 2→3 spawn). That later moment is *not* three upgraders waiting at the controller (see §1.2). The literal “三个都在那里等待着取能量” frame is a few minutes earlier, during the 18:14–18:23 box-sleep gap in `room_stats`. Official history covers it completely.

Interpolation: `room_stats` 84185100 = 18:14:39, 84185230 = 18:23:45 → 4.200 s/tick. Tick 84185189 is 18:14:39 + 89 × 4.200 s ≈ **18:20:53 Asia/Hong_Kong**.

### 1.1 What official history shows at the wait frame

Controller geometry (plan): container **(30,30)**, link **(30,31)**, drop tile **(31,29)**, spots `[30,30], [31,30], [29,30], [31,31], [29,31]`. Bodies are **14W1C2M** (hits 1700), not 15 WORK.

| Tick | stor | ctl cont | ctl link | battery | eAvail | upgrader84184270 | upgrader84184399 | upgrader84184827 | who was feeding |
|---:|---:|---:|---:|---:|---:|---|---|---|---|
| 84185185 | 17026 | 32 | 0 | 32 | 3660 | (29,30) e36 | (30,30) e22 | (30,29) e0 | queens filling ext; rh84015 still at 36,32 with 400 |
| 84185186 | 16226 | 32 | 0 | 32 | 3760 | (29,30) e22 | (30,30) e8 | (30,29) e0 | queen84059 withdrew 800 from storage (fill) |
| **84185187** | 16226 | **0** | **0** | **0** | 3860 | (29,30) e8 | (30,30) e26 | (30,29) e0 | battery empty |
| **84185188** | 16226 | 0 | 0 | 0 | 3860 | (29,30) **e0** | (30,30) e12 | (30,29) e0 | rh84015 at 33,30 with 400, not yet arrived |
| **84185189** | 16226 | 0 | 0 | 0 | 3860 | (29,30) **e0** | (30,30) **e0** | (30,29) **e0** | **all three empty, battery 0** |
| **84185190** | 16276 | 0 | 0 | 0 | 3860 | (29,30) e0 | (30,30) e0 | (30,29) e0 | rh84015 now on drop **(31,29) e400** |
| 84185191 | 15476 | 400 | 0 | 400 | 3860 | (29,30) e0 | (30,30) e0 | **(31,30) e0** | rh84015 dumped 400 into the container; queen withdrew another 800 |
| 84185192 | 15476 | 300 | 0 | 300 | 3860 | (29,30) e50 | (30,30) e50 | (31,30) **e0** | the two stables withdraw; the 3rd still does not (recycle has armed, stor 15476 < 16k) |

The bright yellow glow just below the cluster is almost certainly **rhauler84184015 on the drop tile (31,29)** with 400 energy (or the third upgrader one tile south at 30,29). The controller container itself was empty in these five ticks.

Duration of the all-empty / battery-0 event: **5 ticks ≈ 21 s**. It is short, but it is real, and it is the visible tip of a chronic 3rd-upgrader policy problem (see §4).

A second, earlier cluster also matches the photo layout: ticks 84184894–84184906 (~18:00, end of the 17:47–18:00 box sleep). The same two stables sit on (29,30) and (30,30) working (store cycling 8/36); `upgrader84184827` has just reached **(29,31)** and is empty. Battery is *not* empty then (ctl 1306 + link 178). Only the third is waiting, and it leaves west along the W-wall trunk instead of withdrawing (it is not yet on its assigned spot 31,30; see §4.2).

### 1.2 What 18:29 actually was

`upgrader84185246` (name = spawn start) is a repeat of the same 16k yo-yo, *not* the three-at-the-controller photo:

- 84185246 18:25:18 (`room_stats` stor **16026**, just over allowExtra) — spawn starts, `eAvail` 5000→3450 (the 1550 body is paid from extensions).
- 84185246–84185296 — still `spawning` at Spawn1 (35,28). The two stables at (29,30)/(30,30) stay **loaded** (8/22/36 cycle). Battery 1496→830, never empty. `hungry` (store≤14 and battery=0) = **0**.
- 84185297 18:28:43 — leaves spawn empty at (35,29). Storage is already **15726 < 16k**, so `allowExtra` is false and `roleTargets.upgrader` is 2. The new creep is surplus on birth.
- 84185307–84185319 (~18:29:41) — only two live upgraders: 84184270 working at (29,30), 84184399 walking to spawn to recycle (31,29 → 34,29), empty. Battery 564→438. Not three waiting.

So at the moment the message was sent, the room was already in the recycle half of the yo-yo. The photo is the previous 3rd (`upgrader84184827`) at the controller.

## 2. Coverage

Official history fetched 2026-11-10 ~18:38 Asia/Hong_Kong, `game.time` 84185432, latest published base 84185300 (ticks through 84185399). In-progress chunk 84185400+ unpublished, as expected (~100 tick lag).

| Stream | Rooms | Tick range | Samples | Holes (labelled, not averaged over) |
|---|---|---|---:|---|
| Official history W46N8, W47N8 | owned | **84180200–84185399** | **5200 / 5200** | none in this window |
| Official history remotes | W45N8, W45N7, W47N7 | 84183200–84185399 (2.5 h) | 2100 / 2200 / 2200 | **W45N8@84184200 404** (ticks 84184201–84184300); **W45N7@84184700 404** (84184701–84184800, already known). W45N8/W45N7 sample 2100 vs span 2200. |
| `room_stats` | W46N8, W47N8 | 84178260–84185400 | 441 each (~10 t cadence, with sleeps) | many box-sleep gaps; the two that matter for this question are **84184731–84184919 (189 t, 17:47–18:01)** and **84185101–84185229 (129 t, 18:14–18:23)**. The all-wait sits inside the second hole. |
| `creep_ticks` W46N8 | home | complete 100/100 per 100-tick bucket 84184000–84185200; 84185300 only 1 tick | — | after 84185300 the listener had rotated off W46N8; post-85300 positions come from official history only |
| `creep_cpu` | colony | 84180200–84185380, **941 distinct ticks** | ~18% of the span | gaps 84180471–84180674 (204), 84182211–84182314, 84182581–84182634, 84182991–84183114, plus the box sleeps. Idle % below are from this sparse stream, not the official 5200. |

`cpu_prof` stops at 84182970 in this window and is not used for the transport rates.

## 3. The energy-flow model (measured, both owned rooms)

### 3.1 Equations

Per source \(s\):

\[
I_s^\star = 10\ \text{e/t} \quad (3000/300,\ \text{owned or reserved})
\]

\[
\hat I_s = \frac{1}{T}\sum_t \max(E_s(t-1)-E_s(t),\,0)
\quad\text{(regen jumps excluded; leftover at regen is waste \(W_s\))}
\]

Link send (observed as a drop of ≥50 on the sender):

\[
L_{A\to ctl} = \eta\cdot \hat S_{srcA},\quad \eta=0.97
\]

Controller battery (cap 2000 + 800 = 2800):

\[
B = E_{ctl\_cont} + E_{ctl\_link}
\]

\[
\frac{dB}{dt} = L_{A\to ctl} + H_{ctl} + Q_{ferry} + H_{hand} - U - 0.1
\]

where \(H_{ctl}\) is hauler/rhauler deliveries into the controller container or drop tile, \(Q_{ferry}\) is the queen storage→hub→ctl path, \(H_{hand}\) is adjacent handoff, \(U\) is upgrade spend.

Upgrader demand (measured body 14W1C2M):

\[
U_{cap}(n) = 14n \qquad (n=2\Rightarrow 28,\ n=3\Rightarrow 42)
\]

A creep only withdraws when `store <= WORK` **and** it is already standing on its assigned spot (`upgrader.js`: `move.to(spot, 0)` must return true first). If the battery is empty or the creep is in surplus-recycle, \(U=0\) for that creep (waiting_feed).

Steady-state upgrade ceiling from the existing flow model (`tools/flow.py`, re-run 18:25, not treated as gospel but re-checked against official harvest):

\[
U^\star = \frac{\sum_s (I_s - \text{decay}_s - \text{upkeep}_s) - \text{shared}}{1 + 1300/1500/12} \approx 26.0\ \text{e/t}
\]

for home (A+B+W45N8+W45N7). W47's link-era ideal is **30.08 e/t**. Live comparison is always energy-bound when \(U_{cap}(n) > \) feed.

Queen ferry rule (code, `queen.standby`): only if the room is full enough to leave refill, `ctlLink < 400`, **and** `storage - floor > 0` (floor = 15k). Otherwise \(Q_{ferry}=0\). Haulers, when a queen is alive, skip the fill route unless `energyAvailable < 0.3 · cap`, and under `defLow` (storage < 15k) they put **storage before the controller**.

### 3.2 Home (W46N8) — measured rates

Official history 84180200–84185399 (5200 t, no holes):

| Hop | Capacity / design | Measured | Utilisation |
|---|---|---|---|
| Source A harvest | 10 e/t | **9.88 e/t** (waste at regen 610 e, 0.12 e/t) | 98.8% |
| Source B harvest | 10 e/t | **9.95 e/t** (waste 230 e, 0.04 e/t) | 99.5% |
| Source A container 31,12 | overflow buffer | mean **29 e** | empty — link is taking the mine |
| Source A link 30,11 → ctl 30,31 | SEND=400, ~10 e/t available | **9.19 e/t sent** (~8.91 received after 3%) | ~92% of A, essentially the whole mine |
| Hub link 37,29 → ctl | same SEND/CTL_LOW | **0.00 e/t sent**, mean energy **0** over 5200 t | **unused** |
| Storage 37,31 | floor 15k | mean 15 274, end 15 626, Δ **+0.03 e/t** | pinned to the floor |
| Filler container 35,24 | queen buffer | mean 340 | modest |
| Extensions+spawns | cap 5600 | mean eAvail 4 703 (84%) | often not full, so queens stay on fill |
| Rhauler+hauler deliveries, last 2 h (84183799–84185399, 1601 t) | — | **ctl 13.03 e/t** (49 drops), **spawn/filler 5.20**, **storage 4.46** | ctl is the main drop when not defLow |
| Controller battery | 2800 | 6 h mean 894, min 0, max 2474; last 2 h mean 1 243, min 0 | see §3.4 |
| Home hauler 6C3M × 1 | spare / mineral / A overflow | A-cont mean 29; `creep_cpu` waiting_pickup 57.9%, source_empty 18.2% | correctly idle; not the bottleneck |
| Live CARRY vs need (`model.json` 18:25) | need 72.8 | live **78** (one 24C12M + five 8C8M rhaulers + 6C home) | 107% of need |

Last 2 h official harvest: A 9.93, B 9.94, A-link sent 8.93 e/t. Combined **link + rhauler-to-ctl ≈ 8.93×0.97 + 13.03 ≈ 21.7 e/t** into the upgrade battery. That is the measured feed. Two 14W upgraders demand **28 e/t**. The ~6 e/t gap is why the battery trends down whenever nUp=2 is sustained and the queen ferry is off, and why the room is **energy-bound at 2 already** — which is the original 10-20 design (28 W just above the 26 ceiling).

Queen ferry is off because storage sits on the 15k floor (surplus ≈ 0) and/or extensions are mid-wave (eAvail often 3–4k). `creep_cpu` queens: 67.2% `target_full`, 31.7% working — they are not missing a haul job; they have nothing they are allowed to pull for the controller.

Residual empty extension 31,34 (known leftover after 720380f) is **not** the cause of this wait. Extension deficit in the wait window is a normal spawn-wave / 1550-upgrader withdrawal (eAvail 3060–3860), and queens are visibly refilling it. It does not block the A-link or rhauler-to-ctl path.

### 3.3 Remotes (into home) — last 2.5 h official history

| Source | Ideal | Harvest e/t | Regen waste | Container mean | Verdict |
|---|---:|---:|---:|---:|---|
| W45N8 (14,12) | 10 | **8.97** (span 2200, 2100 samples; 100-tick official 404 at 84184201–300) | 888 e (0.40 e/t) | 13,11 = 279 | healthy, not overflowing |
| W45N7 (21,16) | 10 | **9.44** (same 404 at 84184701–800) | 84 e (0.04 e/t) | 21,15 = 682 | healthy |
| W47N7 R1 (17,17) *W47's remote* | 10 | **8.86** | 1848 e (**0.84 e/t**) | 18,17 = **1920 / 2000** | **saturated** |
| W47N7 R2 (30,35) | 10 | **9.09** | 2172 e (**0.99 e/t**) | 31,34 = **1997 / 2000** | **saturated** |

Home remotes (W45N8/W45N7) are not the fault. Combined they still put ~18.4 e/t onto the road, and last-2 h rhaulers delivered 13 e/t to the home controller plus 4.5 to storage plus 5.2 to spawn/filler — the fleet is moving the energy. Body/count for home rhaulers still match the existing model (78 CARRY vs 72.8 need; W45N8 24C kept because the container used to hit 1891/2000 on a smaller body).

W47N7 containers being full is a **W47 haul tightness**, not a home-route failure. Do not cut W47 overflow haulers (see §3.5).

### 3.4 Upgrade vs nUp and storage band (home)

`room_stats` samples 84180200–84185400 (holes labelled in §2; rates use only adjacent samples with 1–40 tick gaps):

Hourly upgrade (Asia/Hong_Kong), home:

| Hour | up e/t | avg stor | min stor | avg ctl | avg nUp (sampled) |
|---|---:|---:|---:|---:|---:|
| 10 | 23.34 | 15578 | 12615 | 531 | 1.93 |
| 11 | 14.87 | 14867 | 12405 | 1201 | 1.64 |
| 12 | 21.12 | 15385 | 14180 | 1397 | 2.61 |
| 13 | 17.59 | 15325 | 13300 | 552 | 1.77 |
| 14 | 25.67 | 16057 | 15172 | 1023 | 2.74 |
| 15 | 9.70 | 13417 | 12063 | 241 | 1.50 |
| 16 | 20.31 | 14996 | 13329 | 776 | 1.78 |
| 17 | 22.09 | 15561 | 14672 | 1200 | 2.09 |
| 18 (to 18:36) | 23.45 | 16168 | 14026 | 1072 | 2.38 |

Patrol exact 2 h ending 18:28: 24.63 / 26 = 94.7%. `model.json` measured sinks in the same spirit: upgrade 24.63 + storage Δ +0.41.

nUp × storage band (`room_stats` counts; `creeps.upgrader` includes a spawning 3rd, so “nUp≥3” is a slightly loose flag):

| Band | nUp | samples | avg ctl | min ctl |
|---|---|---:|---:|---:|
| under 15k | ≤1 | 56 | 277 | 0 |
| under 15k | 2 | 29 | 669 | 0 |
| under 15k | ≥3 | 7 | 1370 | 545 |
| 15–16k | ≤1 | 27 | 1121 | 0 |
| 15–16k | 2 | 97 | 976 | 0 |
| 15–16k | ≥3 | 33 | 998 | 0 |
| ≥16k | 2 | 9 | 1189 | 452 |
| ≥16k | ≥3 | 59 | 817 | **0** |

The 3rd is almost only present once storage has crossed 16k, and in that band the controller battery still hits **0**. Under 15k the battery is already thin (avg ctl 277 with nUp≤1) because haulers bank to storage and the queen will not ferry.

From official history, wait fractions (live upgrader with store≤14 *and* battery=0):

| Window | span | nUp mix (leaky at a few chunk boundaries; use as order of magnitude) | empty among live | hungry (bat=0 & e≤14) | all-empty & bat=0 ticks |
|---|---:|---|---:|---:|---:|
| 5200 t (6 h-ish) | 5200 | mostly 2, then 1, then 3 | 15.9% | **6.3%** | 258 |
| last 2 h | 1601 | 2:1107, 3:373, 1:121 | 15.4% | **1.3%** | 16 |
| 84184880–84185207 (nUp=3 stretch, 84827's life) | 328 | 3 almost the whole time | **33.2%** (one of three always empty) | 1.1% | 2 |
| 84185170–84185210 (3rd arrives at 31,30) | 41 | 3 then 2 | 29.4% | **9.2%** | 2 |
| 84185240–84185399 (18:25–18:35, 85246 era) | 160 | mostly 2 | 4.6% | **0** | 0 |

The 33% empty during the nUp=3 stretch is **not** three creeps starving. It is one creep (84184827) empty for almost its entire life because of pathing / recycle (321 empty ticks of 330 non-spawn). The two stables kept the 8/22/36 withdraw cycle with a healthy battery most of the time (mean B=910). The all-three-wait is a short spike at the end, when the battery finally hits 0.

`creep_cpu` upgrader (941 ticks, sparse): 75.3% working, 18.0% waiting_feed (`u`), 6.6% moving. That 18% mixes genuine battery-empty ticks with walk-in / recycle / the swamp detour, and should not be read as “the feed is 18% short all day.”

### 3.5 W47N8 — measured, and the “src_A soft” caveat

Official history 84180200–84185399:

| Hop | Design | Measured 6 h | Last 2 h |
|---|---|---|---|
| Source A (27,11) harvest | 10 (link 26,12 → ctl 13,25) | **9.93 e/t** (waste 288 e) | **9.69** (waste 288, one regen leftover) |
| Source B (11,44) harvest | 10 (hauler) | **9.85 e/t** | **10.12** |
| A-link sent | — | 6.99 e/t | 8.43 e/t |
| Hub-link sent | HUB_LINK on | 3.21 e/t | 5.06 e/t |
| Ctl battery (cont 13,26 + link 13,25) | — | mean 2247, min 1471, max 2799 | mean 2180, min 1471 — **never empty** |
| Storage | softCap keep=2 until 40k×500 t, re-arm 30k | 17351→24157, Δ **+1.31 e/t** (last 2 h +1.91) | last 2 h 21097→24157, never crossed 25k |
| nUp | keep=2 (PR 33) | last 2 h 2 for 1539/1601 ticks | holding |
| Upgrade (room_stats hours 16–18) | ideal 30.08 | 16.45 / 14.43 / 18.08 | by design under keep=2 |

`model_w47n8.json` 18:25 (its own window): upgrade 16.3 / 30.08, pickup meter A **2.04** / B 9.14, delivered hub 21.65 / ctl 4.55, w8upgrader waiting_feed 0.20, w8hauler waiting_pickup 0.24, wrhauler moving 0.79 / waiting_pickup 0.12. Storage 23 664 at that snapshot.

**Important:** the long-running “W47 source-A is soft ~2.0–2.47 vs ideal 9.6” figure is the *hauler pickup* meter. Official source energy shows A is actually being mined at **9.7–9.9 e/t** in this window; the miner→container→link path does not show up as a hauler pickup. The overflow-hauler valve must still stay: W47N7 containers are full (1920 and 1997) with ~0.8–1.0 e/t regen waste, so extra haul on the W47 side is earning its keep. Deeper A pathing is still a later item; it is not the cause of the home controller wait.

W47's upgrade being ~54–60% of 30.08 is the keep=2 policy, not a failed haul to an empty battery (battery min 1471).

## 4. Root cause of the three waiting upgraders

Stacked, in order. This is not “haulers forgot the controller” and it is not a body-recipe failure.

### 4.1 Demand overshoot at the 16k gate (primary)

Home feed into the controller is measured at **≈21.7 e/t** (A-link ~8.9 + rhauler-to-ctl 13.0). Two 14W upgraders already demand **28 e/t**. The original model was explicit about this: 28 W sits just above the ~26 ceiling so the room stays slightly energy-bound, and the 3rd is only for *real* surplus.

The live gate is not “real surplus”:

```97:100:src/managers/spawn.js
  const SURPLUS = 1000;
  const extra = Math.floor(ctlEnergy / 700);
  const allowExtra = !st || room.storage.store[RESOURCE_ENERGY] >= require('../roles/queen').storageFloor(room) + SURPLUS;
  T.upgrader = rcl >= 8 ? 1 : Math.min(P.pos.upgraders.length, (sites ? 1 : 2) + (allowExtra ? extra : 0));
```

`allowExtra` fires at **floor + 1000 = 16k**, and `extra` fires when `ctlEma ≥ 700`. Storage yo-yos across that line every spawn wave (we measured 16226→15526 and 15726→14226 in this hour, 1.5–2 k dips when queens refill the 1550 body). Result: a 3rd 14W is started, \(U_{cap}\) jumps 28→42, the battery drains at ~16 e/t, and by the time the 51-tick spawn finishes, storage is often already back under 16k so the new creep is recycled on birth.

`upgrader84184827` is the rare 3rd that lived long enough (379 ticks, 49 of them spawning) to reach the cluster and be in the photo. In the same 6 h window the pattern is chronic: `84180374, 84182131, 84182537, 84182762, 84183432, 84183982, 84184646, 84184726, 84185246` each lived **50–51 ticks** — a full spawn, then immediately recycled, never a useful upgrade tick. Several others walked a short way and died empty (`84180070, 84180482, 84182015, 84182534`, 89–103 t, loaded_t = 0).

Spawning a 1550-energy 3rd also *causes* the extension deficit that turns the queen ferry off (fill has priority). At 84185246, eAvail dropped 5000→3450 the same tick the spawn started. During 84185170–84185210 storage fell 17676→15626 (−48.8 e/t) while queens pulled 800 at a time to refill, and the battery was allowed to run to 0.

**A 3rd 14W at 16k cannot be supported by the measured feed.** It does not raise the long-run upgrade rate (energy-bound at 2 already). It empties the battery, makes even the first two wait, and wastes spawn time.

### 4.2 Pathing / assignment of the 3rd (why this one looked so bad)

Spots are tried in order `[30,30], [31,30], [29,30], [31,31], [29,31]`. With 84184399 on (30,30) and 84184270 on (29,30), the 3rd is assigned **(31,30)** — the tile behind two stationary 14W creeps, with the controller link (30,31) and the occupied container (30,30) in the way. Those standing tiles are expensive in `move.js`, so PathFinder took the paved **west defense trunk** (plan `defense.trunks.W.path`):

`(29,31) → 29,32 → 28,33 → 27,34 → … → 23,35 → 22,35 → 21,34 → … → 17,30`, then turned east along **y=28 swamp at 35 ticks/tile** (14 non-MOVE parts, 2 MOVE, swamp cost 10: \(140/4=35\)). It sat 35 ticks each on (23,28)…(27,28), arrived at (31,30) only at 84185192 — **about 300 ticks after spawn**, almost all of them empty.

Compounding bugs:

- `upgrader.js` only withdraws *after* `move.to(spot, 0)` succeeds. At 84184894–84184906 the 3rd sat on **(29,31)**, which *is* a legal stand, adjacent to the link and the container (battery 1400+), and still did not withdraw because 29,31 was not *its* assigned spot.
- By the time it reached 31,30 (84185191–97), storage was 15476 < 16k, surplus-recycle was on, and the recycle branch **refuses to withdraw**. It stood on its spot with a 300-energy container and stayed empty, then took a 50-energy handoff from rh83660 at 31,29 and walked to Spawn1 (34,29) to be recycled at 84185207.

So for most of the “nUp=3” stretch only two upgraders were actually upgrading. The photo of three in a tight cluster is the last ~20 ticks, when the 3rd finally crawled back, plus the 5-tick all-wait.

### 4.3 Logistics was late, not broken

At the all-wait frame the A-link had already run the ctl link down (346→0 over the previous ~15 ticks) and no rhauler was yet on the drop tile. rh84015 (400) arrived at (31,29) on 84185190 and refilled the container on 84185191; rh83660 (828) dumped the rest on 84185199 (ctl 216→910). Mines were fully harvested the whole time (A=B=9.95 e/t in that 379-tick life). Home hauler `hauler84184192` was idle empty at (32,28) — correct, given source-A container mean 29. Hub link stayed 0 because surplus was thin and extensions were mid-fill.

So: the *pipeline* can deliver (and did, 400+828 within a few ticks). It cannot deliver **42 e/t**, and the queen will not dip the 15k floor to try. Calling this a “hauler body/count failure” would be wrong; calling the 16k 3rd “optimal” would also be wrong.

### 4.4 What this is not

- Not a same-tick double-spawn (PR 32 still holding; 85246 is a single 2→3).
- Not W47 keep=2 / 25k overflow (W47 battery never below 1471; nUp held at 2).
- Not W45N8/W45N7 haul loss.
- Not extension 31,34 trapping a queen as the main upgrade fault.
- Not a reason to open a third room, flip labs, or turn the market on (CPU post-deploy avg 17.78 / 20, no margin).

## 5. Does the existing hauler body/count model still hold?

**Yes, for bodies and counts. The user re-opened the whole logistics model (routes, counts, feed, nUp), and the part that is wrong is the nUp / allowExtra policy, not the recipes.**

Evidence:

- Home A and B are mined at 9.88 / 9.95 e/t. A-link carries 9.19 e/t. The 6C3M home hauler is a spare (waiting_pickup 58%, A-cont 29 e), as the 10-20 model already concluded; it still earns its keep as mineral/overflow/tombstone insurance. Changing it would not have filled the battery at 84185189.
- Home rhauler CARRY 78 vs need 72.8. W45N8/W45N7 containers are not full (279 / 682). Last 2 h they delivered 13.0 e/t to the controller, 5.2 to spawn/filler, 4.5 to storage. That is a healthy mix, not a stuck-at-storage bug (defLow banking is doing what it was asked to do under 15k).
- W47 local harvest is actually full on official history (A 9.7–9.9, B 9.9–10.1). Keep the overflow hauler valve: W47N7 containers are at 1920 and 1997 with ~1.8 e/t combined regen waste. Do not trim W47 haulers while that is true.
- The 18:25 Page conclusion that recipes are near-appropriate is therefore **not overturned** by this wait evidence. What is overturned is the claim that “storage ≥ 16k and ctlEma ≥ 700 means we can afford a 3rd 14W.”

## 6. Recommended self-decision

Ranked. Intended for a later CloudAgent; not applied in this pass.

### 1. (Do now) Tighten the home 3rd-upgrader gate — policy, not bodies

**File:** `src/managers/spawn.js`, `targets()`. Optionally surface the new latch on `Memory.ops.upgFeed` via `src/managers/upgfeed.js` (already has `allowExtra`, `upBank`, `ctlEma`).

**Policy:** keep the base of 2 (or 1 if sites). Only allow a 3rd when there is *sustained* surplus the 42 W feed can actually burn, with hysteresis wide enough to survive a spawn wave:

- Enter (`upExtra` latch): `storage >= 20000` (floor+5000) **and** `ctlEma >= 1200` for **300 ticks**.
- Leave: `storage < 18000` or `ctlEma < 700` (drop extra immediately; existing `upBank` still collapses to 1 below 14.5k).
- Do not start the 3rd while `energyAvailable` is far below cap (e.g. `< cap - 1550`), so a spawn wave cannot both pay for the body and starve the queen ferry in the same minute.

This is the same shape as W47's “keep=2 until 40k for 500 ticks, re-arm 30k”, sized to home's 15k floor and 26 e/t ceiling.

**Expected:** long-run upgrade stays ~24–26 e/t (energy-bound at 2×14W; the 3rd was not adding a long-run e/t). Short 0-battery stalls like 84185187–91 go away. Spawn waste of ~1550 × (8–12 failed 3rds per 6 h) and the 51-tick spawn occupancy go away. CPU slightly down (no 300-tick swamp PathFind for a creep that will be recycled; fewer spawn intents). No change to the 15k floor, to remotes, or to W47 overflow haulers.

### 2. (Do with #1, small) Make the 3rd's walk survivable if it is ever spawned

**File:** `src/layouts/W46N8.js` positions (or the generated layout export) and `src/roles/upgrader.js`.

- Reorder stands so the 3rd is **(29,31)** (16-tick walk from Spawn2/Spawn1, adjacent to the battery) rather than **(31,30)** behind two occupied stands. Suggested order: `[29,30], [30,30], [29,31], [31,31], [31,30]`.
- Withdraw when adjacent to the ctl link or container even if `move.to(spot, 0)` has not yet returned true. The 13 ticks 84184827 spent empty on (29,31) with 1400 in the battery are free upgrade left on the table.
- Recycle path: nearest spawn, roads only. The W-trunk swamp loop must not be a valid recycle route.

These do not fix the overshoot; they stop a mis-spawned 3rd from being useless for 300 ticks and from looking like “everyone is waiting.”

### 3. What not to change, and why

- **Home / W45 rhauler bodies and counts** — model still holds (78 vs 72.8; remotes not overflowing; 13 e/t reaching ctl).
- **Home 6C3M hauler** — still the overflow/mineral/tombstone spare; A is on the link.
- **W47 overflow haulers** — W47N7 containers are full; official A harvest is not actually soft. Do not cut the valve.
- **15k storage floor, CTL_LOW/SEND=400, link plan** — the floor is doing its job; the unused hub ferry is a *consequence* of surplus≈0, not a broken threshold. Lowering SEND would thrash cooldown and would not create 42 e/t.
- **Labs, market, a third room, a new remote** — CPU 17.78/20, no margin; out of scope and previously declined.
- **W47 keep=2 / 40k latch (PR 33)** — holding, battery healthy. Leave it.

### Self-decision

Implement #1 (and #2 with it) in a later coding pass. Do not deploy from this analysis. The 16k / ctlEma 700 3rd-upgrader gate is not optimal on the measured feed, and it is what put three upgraders on the controller with an empty battery.

## Appendix: key identities and times

- Shard3, homes W46N8 and W47N8 (RCL7), remotes W45N8, W45N7, W47N7.
- Live `c6c80d3` @ 84183977. Analysis time 18:35–18:50 Asia/Hong_Kong, 2026-11-10.
- Home upgrader bodies confirmed 14W1C2M (hits 1700) from traces and `model.json` `bodies_live`.
- Official history cache: `state/hist_cache/{room}_{base}.json`. Working numbers: `state/_energy_flow_numbers.json` (nUp in long windows can be 1 creep too high at a few chunk boundaries because a chunk-start snapshot does not null prior objects; tick tables in §1 were re-checked with a replace-on-snapshot reconstruct and match raw objects).
- Known official 404s in this pull: W45N8@84184200, W45N7@84184700.
