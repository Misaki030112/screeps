# W47N8 conquest (manual)

Plan approved in spirit by Misaki (try two ranged+heal creeps, kill the reserver, then claim and safe-mode). Code is inert until `Memory.ops.cq` is set. **Do not deploy or write Memory until Misaki reviews this doc.**

Code: `src/roles/conquest.js` (roles `cqsquad` / `cqbreaker` / `cqworker`), spawn hook in `managers/spawn.js` §2c (after probe), flee exclusion in `main.js`, control `tools/conquest.py`, tests `tests/conquest.js`.

## Bodies (RCL5 1800 cap)

| role | body | cost | notes |
|------|------|------|-------|
| cqsquad | 6R 2H 8M | 1800 | 60 ranged dps, 24 heal, full speed |
| cqbreaker | 2CLAIM 2M | 1300 | `attackController` −2 reservation ticks/tick; then `claimController` |
| cqworker | 5W 5C 5M | 1000 | carries 250; upgrade / build / opt-in safe mode |

Squad of 2 → combined 120 ranged dps, 48 heal. Storage floor 3100 (same defender reserve as the probe).

## Commands (`python3 tools/conquest.py …`)

| cmd | effect |
|-----|--------|
| `status` | cq memory + W47N8 hostiles/controller + last log |
| `spawn` | `cq.spawn=true` → spawn up to `cq.squadMax` (default 2) cqsquad |
| `cmd hold` | everyone waits at W46N8 (3,20) |
| `cmd go` | squad enters W47N8; kill CLAIM first, then healers/armed; patrol north; breakers/workers run their jobs |
| `cmd retreat` | everyone home on the safe path; **all conquest spawning stops** (abort) |
| `claim` | `cq.claim=true` → spawn breakers (default 3) then workers (default 4) |
| `autoSafe on\|off` | workers call `activateSafeMode` when available. **Default off** (standing rule: never auto-activate) |
| `set <key> <json>` | `squadMax`, `breakers`, `workers`, `respawn`, `forceWorkers`, `owner` |

Writes create `Memory.ops` / `Memory.ops.cq` parents and poll until the value is visible (same lesson as the probe).

## Pathing / safety

- Forbidden rooms: W47N9, W48N9, W48N8 (cost 255).
- W47N8 rows `y<8` blocked (north edge toward his W47N9).
- Retreat / home target: W46N8 (28,24) under towers.
- Auto-retreat (before we own W47N8 **and** it is in safe mode): any squad member hits&lt;70%, hostile tower with ≥10 energy, or armed hostile dps in the squad's room &gt; total squad heal → `cmd=retreat`, `cq.auto={why,t}`. Stays retreated until a human sets a new cmd.
- Target priority: CLAIM (reserver) → HEAL → armed (by dps) → CARRY → WORK → rest; shared `cq.focus` so both shoot the same creep. Kite: keep range 3 from melee, stick within 2 of buddy, mutual heal every tick.

## Phased timeline (tick ≈ 3.65 s; clock = Asia/Shanghai)

Reference at planning time: tick ~83686400, wall ~2026-10-17 00:16 UTC+8. W47N8 reservation endTime 83690004 → **~3600 ticks / ~3.7 h left** (expires ~04:00 UTC+8). Re-check `conquest.py status` before go-time; numbers shift.

| # | phase | ticks | wall clock (from T0=deploy+arm) | energy |
|---|-------|------:|---------------------------------|-------:|
| 0 | Deploy code (upload). **No Memory writes yet.** | — | T0 | 0 |
| 1 | Fill storage ≥6k (comfort). `conquest.py spawn` + `cmd hold`. Spawn 2×cqsquad. | 80–150 | T0+5–10 min | 3600 |
| 2 | Form up at W46N8 (3,20), wait for both. | 20 | +1 min | 0 |
| 3 | `cmd go`. Travel into W47N8 via east edge (y13–27). | 40–60 | +3–4 min | 0 |
| 4 | Kill reserver (`rvep393` 2CLAIM near (15,25)). 120 dps vs ~400–600 hits. | 5–30 | +1 min | 0 |
| 5 | Patrol north (PATROL y≥8), kill inbound economy / small combat. **Do not push y&lt;8.** | ongoing | — | 0 |
| 6 | When reservation ≲ 1000 ticks (~1 h left) **or** on Misaki's call: `conquest.py claim`. Spawn 3×breaker. | 50–80 | — | 3900 |
| 7 | Breakers `attackController`: 3×2 + 1 natural = 7 ticks/tick. 1000 rem → ~145 ticks. | 150–500 | 10–30 min | 0 |
| 8 | Reservation gone → `claimController` (1 tick). Log `claimed`. | 1–5 | — | 0 |
| 9 | Workers (spawned as reservation &lt;400 or after claim) haul 250 from home, upgrade 200 → RCL2 (~10 ticks with 4×5W). | 80–150 | +5–10 min | 4000 spawn + ~1–2k haul |
| 10 | **Misaki** (or `autoSafe on`): `activateSafeMode` in W47N8. Home cannot SM at the same time. | 1 | — | 0 |
| 11 | Under SM (~20000 ticks / ~20.3 h): build spawn (15k) at (12,26), ramparts on spawn/controller/tower tiles, push RCL3 (45k), tower at (14,28). Home keeps remotes+upgraders; workers siphon only above storage floor. | 20000 | ~20 h | ~25–40k total from home over the day |
| 12 | Chain SM while novice (no cooldown until **2026-10-28 03:33 UTC+8**): each RCL-up grants +1 charge. Same-room-only: W47N8 SM means home has no SM. | until 10-28 | — | — |
| 13 | After novice: SM cooldown returns (~50000 ticks / ~2.1 days). Exposure window between SM uses. By then aim RCL5+ with tower(s) and ramparts. | — | after 10-28 | — |

**Earliest claim window:** if we arm around 00:30 and wait for reservation ~1000, breakers go ~02:50, claim ~03:10–03:30 UTC+8. Faster if we start breaking earlier (more breaker-ticks, same energy).

## Energy & RCL6 impact

- Combat+claim spawn cost: ~3600+3900+4000 ≈ **11.5k**.
- Bootstrap haul to RCL2+spawn: ~**17–20k** in the first SM day (spawn 15k + upgrade crumbs + tower later).
- Home net ~28/t; upgrade realistic 24/t. Pulling ~12k over 2 h for the assault delays RCL6 by roughly **0.5–1.5 h** (queue contention + storage dips). Current ETA ~Oct 17 19:30 → **~20:00–21:00 UTC+8** if we run the op today.
- Prefer: finish RCL6 first (tonight), then conquer tomorrow with 2300 cap (bigger squad / faster bootstrap). Misaki asked to try now — plan supports either; gate is her go-ahead after review.

## Home support rules (coded)

- Conquest spawns only when `storage ≥ 3100` and not under threat/energyHold.
- Workers refuse to withdraw if it would leave storage &lt; 3100+250.
- `cmd retreat` clears the pipeline (no further cq spawns until re-armed).
- Upgraders/remotes keep their normal targets; cq is a side queue after miners/probe.

## Risks (honest)

1. **13 combat next door.** Two 6R2H cannot beat a 7T14A21M (420 melee dps) or the W48N9 pack. Auto-retreat saves the squad once; replacements need `cq.respawn=true` and still lose a straight fight. Success case = he does not react (as with the observer). Failure case = we retreat and abort.
2. **Open north edge.** No chokepoint; "hold the north gate" is a patrol of y≈10, not a wall. Anything that walks south of y=8 is fought at range 3.
3. **Safe mode is one-room.** W47N8 SM ⇒ home cannot SM. Home still has towers + 4 SM charges for later; novice wall does **not** block BustJetter (same novice zone).
4. **New controller starts at 0 SM charges.** Must hit RCL2 (200) before the first SM. ~50 min exposure from claim to SM if workers are pre-staged; longer if not.
5. **CLAIM downgrade.** His claimers can `attackController` our new controller after SM ends. Keep upgrading (downgrade timer must stay above half to allow SM).
6. **GCL.** GCL3 → 3 rooms owned max. Home + W47N8 leaves one slot.
7. **Storage currently ~3.5k.** Wait for ≥6k before `spawn` so the floor is not a tripwire mid-squad.

## Abort

`python3 tools/conquest.py cmd retreat` — every cqsquad/cqbreaker/cqworker walks home on the safe matrix; `wantSpawn` returns null until spawn/claim are set again.
