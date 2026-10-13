# Defence readiness — W46N8 + remote W45N8

First strategy-review write-up: **2026-10-13 14:40 (UTC+8)**.  
Novice zone ends **2026-10-28 03:33 UTC+8** (~14.5 days). Hard rule: **NEVER auto-activate safe mode** — alert Misaki and wait.

## Home (W46N8) — current

| Item | Live (2026-10-13 ~14:40) | Policy |
|---|---|---|
| Tower | 1 at **(36,29)** (kept from v1; v2 plan tower was 36,33) | Attack hostiles first; heal; repair only if tower energy **> 800** |
| Tower energy | Queen tops tower to **≥ 900** (was 700) | Keep combat reserve; 10 energy per shot |
| Ramparts | Spawn (35,28) + tower (36,29), ~27k hits | Targets by RCL: `[0,0,0,20k,50k,100k,300k,1M,3M]` (see `tower.js`) |
| Safe mode | Spawn SM ends ~tick 83614428 (~15:00 UTC+8 today); **2 available** | Alert only — Misaki decides |
| CPU / economy | ~3.5–4.2 CPU, bucket full | Headroom for combat intents |

### Tower damage falloff (Screeps constants)

`amount -= amount * 0.75 * (range - 5) / 15` for range in (5, 20]; ≤5 → full, ≥20 → 25% of full.

| Action | ≤5 | 10 | 15 | ≥20 |
|---|---|---|---|---|
| Attack | 600 | 450 | 300 | 150 |
| Heal | 400 | 300 | 200 | 100 |
| Repair | 800 | 600 | 400 | 200 |

Coverage from tower **(36,29)** (Chebyshev range):

| Point | Range | Atk dmg |
|---|---|---|
| Spawn / hub / stamp A | 0–3 | 600 |
| Future storage (37,31) | 2 | 600 |
| Controller (28,32) | 8 | ~510 |
| Source B (39,33) | 4 | 600 |
| Source A (32,11) | 18 | ~210 |
| East exit (49,14) | 15 | ~300 |
| West exit (0,y) | ≥29 | 150 |

**Implication:** one tower fully covers the hub and source B; source A and the west exit are weak. Early player raids that sit on the west edge and snipe with ranged parts take little tower damage — ramparts on spawn/tower still buy time. Tower 2 at RCL5 **(37,33)** improves south/east hub coverage.

### Typical early player raids (novice neighbours)

Inside our novice zone today:

| Room | Owner | RCL | Notes |
|---|---|---|---|
| W47N9 / reserves W47N8,W47N7 | **BustJetter** (The Council) | 6 | West of us; creeps transit W46N8 |
| W44N8 | **Fandalah** (The Council) | 5 | East of W45N8 |
| W45N9 | FearlessBroccoli | 5 | No N exit into W45N8 |
| W44N9 | Tekyera | 4 | Sign: peaceful neighbour |
| W46N9 / W46N7 | drtk712 / FungousCoast245 | 8 / 8 | **Outside** our novice zone until 10-28 |

Likely shapes before 10-28: 1–3 combat creeps (ATTACK/RANGED + MOVE, sometimes HEAL), probing remotes or walk-through kills — not bunker-siege. After novice ends, RCL8 neighbours can reach us; walls/min-cut matter then.

### Rampart plan (layout v2)

- **RCL3:** spawn + tower only (live). Target 20k (met: ~27k).
- **RCL4:** + storage + core filler tiles (plan list in `src/layouts/W46N8.js`). Target 50k.
- **RCL5+:** each new tower gets a rampart; fill out manager/filler tiles (27 ramparts total by RCL8).
- **Min-cut perimeter:** deferred. Rough terrain check: W46N8 has **E=22 and W=15** exit tiles, **N=S=0**. Protecting stamp A+hub (~133 walkable tiles) has ~22 perimeter openings; a tight hub+1 ring has ~15 openings. Feasible later (~15–25 rampart wall tiles + choke), **not needed while novice holds and core is compact**. Revisit **before 2026-10-25**.

### Home invaders while remote is unreserved

Invaders only spawn on exits to **neutral** rooms. W46N8 exits: W→W47N8 (BustJetter reserved → blocked), E→W45N8 (blocked only while **we** reserve it). When W45N8 reservation lapses, home can receive NPC invaders from the east. Home `invaderHarvested` ≈ 168k/source (past the ~100k goal), so this is real. One tower kills light invaders in the hub in a few ticks; do not leave W45N8 unreserved for long after a pause.

---

## Remote W45N8 — invaders

### How NPC invaders spawn (docs + engine)

- Per-room harvest counter ≈ **`INVADERS_ENERGY_GOAL` 100 000** (±30%, 10% chance ×0.5/×2). Needs a sector **stronghold**.
- Spawn only on exits to **neutral** rooms. W45N8: W=ours (blocked), E=Fandalah owned (blocked), **S=W45N7 neutral** → invaders enter from the south.
- Light bodies in reserved / RCL≤3 rooms; heavy in owned RCL≥4. 10% chance of a 2–5 creep raid (melee / ranged / healer; sometimes boosted).
- Invaders **cannot** change rooms; TTL 1500; they hunt creeps, mostly ignore structures unless blocked.
- Strongholds also drop **level-0 invader cores** into unowned/reserved rooms that reserve the controller until destroyed.
- Killing NPC Invaders does **not** provoke players.

### Live incident (2026-10-13)

- Invader `invader_W45N8_937` (user id 2): body T2 M5 RA1 W1 A1, 1000 hits, ageTime **83614707** (dies of age).
- Remote paused `pauseUntil` **83614741**; delivered **27 362**; reservation will have lapsed before unpause (CLAIM1 was net-zero; vision lost while paused).
- Policy today: **flee + wait** (no fight). Code improvement: Invader-only pauses use `min(1500, invaderTTL+80)` so we resume soon after they age out.

### Wait vs small defender (numbers)

Assumptions: reserved remote net ≈ **+7–8.5 e/t** (observed ~8.5/t delivered before pause); pause **1500** ticks; re-reserve CLAIM1 **650** (or CLAIM2 **1300** at RCL4).

| Option | Energy cost | Downtime | Notes |
|---|---|---|---|
| **Wait** (current) | ~0 combat; **~12k** lost income (1500×8) + re-reserve 650–1300 | Full invader TTL | Safe; zero combat bugs; reservation often lapses |
| **Solo light defender** ATTACK5 MOVE5 (=650) | 650 + ~30 travel + maybe one loss | ~50–100 ticks | Beats one light invader (1000 hits, no heal); Overmind `DirectiveGuard` / `DefenseNPCOverlord` fights remotes |
| **Raid with healer** | Need ATTACK+HEAL pair or kite (≥1500–2500) | Uncertain | Waiting is usually cheaper until RCL5+ |

**Break-even:** one successful solo clear saves ~12k − 650 ≈ **11k** vs waiting. Frequency: ~every 70–130k harvested ≈ **2–4 h** at 10 e/t reserved → waiting costs **~50–100k/day** if every wave is waited out.

### Recommendation (needs Misaki approval to *fight*)

1. **Until RCL4 + CLAIM2 stable (~today evening):** keep **wait/flee**. Do not divert spawn from the RCL4 push.
2. **After RCL4:** optional **Invader-only** defender:
   - Trigger: hostile owner `Invader`, no HEAL parts in room, total enemy ATTACK+RANGED parts ≤ 6.
   - Body: `ATTACK5 MOVE5` (650) at cap ≥650; recycle when clear.
   - Still flee on **any player** combat creep (unchanged).
   - Expected: ~650–1300/day combat overhead vs ~50k+/day wait loss.
3. **Invader cores:** dismantle with WORK creep when seen (proposal; not coded).
4. **Diplomacy:** Council (BustJetter/Fandalah) still the main *player* risk on the remote — separate from NPC math.

---

## Open-source bot patterns

| Bot | Remote NPC invaders | Player on remote |
|---|---|---|
| **Overmind** | `DirectiveGuard` (blue/blue) → `DefenseNPCOverlord` (or `GuardSwarm` below required RCL) | `DirectiveOutpostDefense` (blue/red) skirmish |
| **TooAngel** | Tower-centric at home; queueable `defender` role; remotes pause under threat | Manual/queue combat roles |
| **Common early** | Flee + wait **or** one cheap melee guard | Suspend remotes; never auto safe mode without intent |

We match the conservative early pattern today; Overmind’s fight-remotes pattern is the next step once economy is RCL4-stable.

## Checklist before novice ends (deadline **2026-10-25** review)

- [ ] RCL4 storage + rampart target 50k
- [ ] Tower energy discipline (≥800 combat reserve) — **done 2026-10-13**
- [ ] Attack alerts include `safeModeAvailable` — **done 2026-10-13**
- [ ] Decide remote Invader-defender policy (proposal above)
- [ ] RCL5 tower 2
- [ ] Min-cut / outer ramparts design pass
- [ ] Confirm safe-mode decision tree with Misaki (when she would activate)
