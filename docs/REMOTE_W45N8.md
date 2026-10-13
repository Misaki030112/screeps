# Remote mining evaluation: W45N8 (east of W46N8), 2026-10-13 09:20 (UTC+8)

**Status: LIVE** (Misaki approved 2026-10-13). Defence / invader policy: see `docs/DEFENSE.md`.
Listener still records W45N8 activity (DB + archived `metrics/archive/w45n8_activity.jsonl`).

## Facts (game API)
| Item | W45N8 |
|---|---|
| Status | normal, **novice zone, same zone as W46N8** (novice ends 1793129589429 = 2026-10-28 03:33 UTC+8) |
| Owner / reservation | none / none |
| Controller | (7,36), level 0. **Signed by BustJetter: "Under the protection of The Council. Allies welcome: discord…"** |
| Sources | **1** at (14,12) → 5/tick unreserved, 10/tick reserved |
| Source keepers / invader core | none |
| Infrastructure | a neutral **container (13,11) next to the source, full (2000 energy)**: built by someone else and currently not being hauled |
| Mineral | (44,9) |
| Exits | W → **W46N8 (only us)**, S → W45N7 (unowned; BustJetter and `fhl` creeps seen there), E → W44N8 (**Fandalah RCL5, sign "Conquered by The Council"**). No N exit. |
| Path | storage (37,31) → our east exit (49,14) → source: **31 tiles** (4 swamp); from spawn 28 tiles. The planned v2 trunk (x=38) covers the first part. |

W46N8 itself only has W and E exits. West is W47N8, **reserved by BustJetter** (reservation to tick ~83613706). BustJetter's
creeps that cross our room travel W47N8 → W46N8 → W45N8.

### Neighbours (map-stats, user/find)
| Room | Owner | RCL | Notes |
|---|---|---|---|
| W47N9 | BustJetter (GCL≈3, 10.4M) | 6 | "The Council"; also reserves W47N8/W47N7 |
| W44N8 | Fandalah (GCL≈3, 9.0M) | 5 | "Conquered by The Council" |
| W45N9 | FearlessBroccoli | 5 | not adjacent to W45N8 (no N exit) |
| W44N9 | Tekyera | 4 | "peaceful neighbor" |
| W46N9 / W46N7 | drtk712 (GCL very high) / FungousCoast245 (very high) | 8 / 8 | **outside our novice zone** (their novice expired); no exits into W46N8 anyway |

## Risk
- **Novice protection does not cover creeps against players inside the same zone.** The Council (BustJetter RCL6 + Fandalah RCL5)
  is inside our zone and on **both** sides (W47N8 reserved to our west, W44N8 to W45N8's east). They can kill remote creeps at any time.
  It only keeps out players from outside the zone (the RCL8 giants) until 2026-10-28.
- Safe mode protects only W46N8 (active ~5200 ticks more ≈ 5.5 h; 2 more available), never remote creeps.
- **Diplomatic:** W45N8 is signed as Council-protected, their creeps pass through it, and the container there is probably theirs. Reserving it is
  an open challenge. Unreserved mining from "their" container is a softer but still visible one. Retaliation could hit our room after
  safe mode ends, and we are RCL3 with 1 tower.
- **NPC invaders:** ~100k harvested (±30%) + sector stronghold; enter only via exits to neutral rooms (for W45N8: south W45N7).
  First live Invader 2026-10-13 → flee+pause (see DEFENSE.md). Optional cheap defender proposed post-RCL4.

## Economics (energy/tick, creeps last 1500 ticks; reserver 600)
Round trip storage↔source ≈ 62 tiles + loading ≈ 66 ticks. Without roads haulers need 1 MOVE per CARRY.

| | Unreserved (5/t) | Reserved (10/t) |
|---|---|---|
| Miner | WORK3 MOVE2 (400) → 0.27 | WORK5 CARRY1 MOVE3 (700) → 0.47 |
| Haulers (carry ≈ income × 66) | 2 × CARRY4 MOVE4 (2×400) → 0.53 | 2 × CARRY7 MOVE7 (2×700) → 0.93 |
| Container repair (5000 hits/100 t in unowned room = 0.5 e/t) | 0.5 | 0.5 |
| Reserver | – | CLAIM1 MOVE1 (650, 1.08/t) or CLAIM2 MOVE2 (1300, RCL4+; ≈1.1/t effective) |
| **Net** | **≈ +3.7/t** | **≈ +7.0/t** |
| % of current income (≈20/t) | +18% | +35% |
| Up-front | 0 (reuse container) | 0 |
| Roads (optional) | 31 tiles ≈ 14k energy (4 swamp tiles at 1500 each); saves ≈0.3/t of MOVE parts → payback ≈ 2 days. **Not worth it early.** | same |
| CPU | miner 0.2 + 2 haulers ≈0.5 + cross-room pathing → **≈0.7–0.9 CPU/t** | +reserver 0.2 → **≈1 CPU/t** |
| Spawn time | ≈ 40 ticks per 1500 | ≈ 60 ticks per 1500 (+ reserver 6 per 600) |

**Break-even:** any lifetime that pays back its creeps. A miner+hauler set (≈1200 energy) pays back after ≈330 ticks unreserved, ≈170 ticks reserved.
A set lost to invaders or players before that is a net loss. CPU is not the constraint (we use ≈3.7 of 20), so the CPU has no better
use. The real costs are **risk and diplomacy**.

### Timing
- Now (RCL3, cap 650 → 800 once the 10 v2 extensions finish): unreserved is possible (bodies ≤ 400). A reserver at 650 is a CLAIM1 that can't stack.
- RCL4 (ETA ≈ 6 h, 135k−62k at ≈12/t): storage as the sink, cap 1300, so a CLAIM2 reserver is possible and the v2 trunk road is built. **This is the natural start.**
- Alternatives: extra energy in our own room is already capped by 2 sources (≈20/t). Remote mining is the only income growth before a
  2nd room (GCL 2 already allows one claim, but that is a bigger decision and a bigger diplomatic footprint).

## Recommendation
**Don't start now. Observe 24 h, decide diplomacy, then start unreserved at RCL4 only if W45N8 is unused or the Council agrees.**

### Phased plan
0. **Observe (running now, 0 CPU in game):** log W45N8 activity for ~24 h. If BustJetter keeps the container drained or reserves the room, it is theirs, so skip.
1. **Diplomacy (Misaki):** optionally contact The Council (Discord link in the sign): ask to share W45N8 or join as an ally. Their answer decides everything.
2. **Pilot (RCL4, after approval):** 1 miner (WORK3) + 2 haulers (CARRY4 MOVE4), unreserved, reuse the existing container, no roads.
   Abort if any creep is attacked by a player, the room gets reserved by someone, or hostile military shows up (alerts.py ≥ medium for W45N8).
3. **Reserve (only with Council OK or clearly abandoned room):** CLAIM2 reserver, WORK5 miner, haulers 2×CARRY7 MOVE7 → ≈ +7/t.
4. **Harden:** a small defender for invaders, the remote road only if traffic justifies it, and remote alerts in alerts.py.

## Decision points for Misaki
1. Accept the 24 h observation and the start at RCL4? (recommended)
2. Contact The Council first (and in what tone: ask to share / ask to join), or mine without asking?
3. Unreserved only (low profile, +3.7/t) or reserve (+7/t, open claim)?
4. Accept the creep-loss risk (~1200 energy per lost set) and spend ≈1 CPU?

## LIVE (approved by Misaki 2026-10-13 09:26 UTC+8: reserve + mine now)
Code: `src/managers/remote.js` (config, safety, Memory.remote), `src/roles/remote.js` (rminer / rhauler / reserver),
spawn hook in `managers/spawn.js` (after home miners/queen/haulers, before fillers/upgraders/builders; no remote spawning while home is starving).
- Route: fixed exits W46N8 (49,14) ↔ W45N8 (0,14), cached per-room paths (utils/move).
- rhauler ×2 (×3 while container > 1200): withdraw from container (13,11) and pick up drops → home, delivers via normal hauler logic.
- rminer ×1: stands on the container, harvests, repairs the container when hits < 30k, rebuilds it if it is gone. WORK4 at cap 650, WORK5 at ≥700.
- reserver ×1: CLAIM1 MOVE1 at cap < 1300, CLAIM2 MOVE2 at ≥ 1300 (RCL4). Never attacks a controller reserved by someone else.
- **Safety:** hostile ATTACK/RANGED_ATTACK creeps in W45N8 or W46N8, or any of our remote creeps damaged → `Memory.remote.W45N8.pauseUntil = now+1500`,
  remote creeps flee to W46N8 (33,26), remote spawning is paused, and `ALERT {...severity medium|high, remote:"W45N8"}` is logged.
  The listener → `metrics/alerts_state.json` → `alerts.py` exit 2. The standard alert scan (`managers/alerts.js`) also runs on W45N8 while visible.
  Nothing attacks; safe mode is untouched.
- Status: `python3 tools/remote_status.py` (Memory.remote: reservation, container, delivered energy) and `metrics/w45n8_activity.jsonl`.
