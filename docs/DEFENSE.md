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

- [x] RCL4 storage + rampart target 50k — done 2026-10-14 (16 ramparts 50–57k)
- [ ] Tower energy discipline (≥800 combat reserve) — **done 2026-10-13**
- [ ] Attack alerts include `safeModeAvailable` — **done 2026-10-13**
- [ ] Decide remote Invader-defender policy (proposal above)
- [ ] RCL5 tower 2 — first RCL5 site since 2026-10-14 review (build order tower→extension); RCL5 assessment in `docs/RCL5.md`
- [ ] Min-cut / outer ramparts design pass
- [ ] Confirm safe-mode decision tree with Misaki (when she would activate)

## Home defense (2026-10-16, BustJetter squad 2x RA + 6 HEAL in W47N8)
- **Towers** (`utils/focus.js`, `managers/tower.js`): all towers fire one target. net = tower dmg at range (600 ≤5 → 150 ≥20; TOUGH/boost reduced) − max heal reachable from every hostile healer (self/adjacent 12/HEAL, range 2-3 4, boosts ×2-4). Healer first if net>0, else fastest kill; net≤0 → hold fire unless it is hurting us; edge-strip targets only if dead within 1 tick (anti-drain). Sticky on a target dying within 2 ticks. Holding fire: heal own creeps, repair only barriers <2000 hits with tower >500.
- **Guards** (`roles/guard.js`, `managers/home.js`): while player combat creeps are in W46N8, 1 guard (2 if RA+ATTACK parts ≥12), body nRA+(n+1)M+HEAL sized from available energy. Never leave the room, fight only within 15 of a tower, shoot the towers' focus (healer first), kite melee, retreat <60% to the spawn, recycle 100t after clear. Spawn order under threat: emergency → remote defender → queen → guards → miners; upgraders/builders/remote held.
- **Civilians**: every non-combat creep steps away (PathFinder flee) from a hostile ATTACK/RANGED creep within 4 in our room. Queen refills towers first under threat. Remote creeps already wait at home on any player combat creep (threat FSM `player`).
- **Early walls**: `room.memory.defAlert = <tick>` (set from console when a squad is adjacent — Misaki's approved trigger) or a player combat creep inside starts the wall phase at any RCL (`why: threat`, fund 0, threat lifts the cap). Site order puts the west gate (6,28) and west wall x=6 first, then the final-plan order. Nothing off-plan. Safe mode is never automatic.

### Paused 2026-10-16 09:51 (Misaki: "就这点兵力先不用大惊小怪，提前修墙和防守兵暂时不需要，会拖慢升级")
- Switches in `managers/home.js` `FLAGS` (code default **off**), overridable from the console without deploying:
  `Memory.defense = { earlyWalls: true, guards: true }` (either key alone works; `delete Memory.defense` = back to defaults).
- `earlyWalls` off: `defAlert` / a squad in the room no longer starts walls. A wall latch with `why: 'threat'` is cleared once
  (`defAlert` deleted, phase back to the normal off/bank/build schedule of DEFENSE_PLAN.md) and unbuilt planned rampart/wall
  sites (<10% progress) are removed; built structures and progressed sites stay.
- `guards` off: no guards and no threat spawn hold — upgraders/builders/remote keep spawning with hostiles in the room.
- Still active: tower focus fire (healer-first, heal-aware, anti-drain), civilian flee, queen tower priority, remote creeps
  waiting at home on a player combat creep (threat FSM), remote Invader defender (unchanged).

## Tower anti-drain v2 (2026-10-16, Misaki)
- Towers shoot hostile player creeps in the room **by default**, edge-sitters included (old rule "edge target only if killable in 1 tick" removed; it let BustJetter's 4T4M pbefv33 sit at (1,27) untouched).
- Healer-first / net-damage focus fire unchanged for squads; net<=0 hold only happens when real healers out-heal us.
- Drain tracker `focus.track` → `room.memory.drain[id]`: a cycle = we damaged it, then it recovered to ≥90% (healed on strip or outside). ≥2 cycles, or ≥1000 tower energy spent with hits recovered → banned for 1500 ticks.
- Banned creep: held fire only while on the exit strip (x/y ≤1 or ≥48); still shot if it moves inward, hurts us, or dies within 2 ticks.
- Energy floor: targets that neither hurt us nor die within 2 ticks are only shot by towers with ≥300 energy (`FIRE_FLOOR`).

## 2026-10-16: home combat creeps off; remote anti-Invader on (Misaki)
`Memory.defense` / `managers/home.js` FLAGS:
- `guards` (home vs players), `earlyWalls`: **default off** since fccf46c (BustJetter squad not worth slowing upgrade).
- `remoteDefender` (W45N8 anti-NPC-Invader, docs/DEFENDER.md): briefly defaulted off in c6ce97e (misread as home guards);
  **restored default ON** 10-16 ~10:39 (Misaki: keep remote defender). `threat.armed()` follows the flag; WAIT `'gate'`
  re-arms to THREAT when the flag is on and a solo Invader is still present. Explicit off without redeploy:
  `Memory.defense.remoteDefender = false`. Mid-fight disarm still drops THREAT/DEFEND → WAIT and recycles a live defender.
Kept always: tower focus fire, civilian flee, remote creeps parking at home on player combat / wait-out.

## Remote defender review — invader_W45N8_499 (2026-10-16)
Invader: boosted smallMelee (2 TOUGH GO, 5 MOVE, 1 RA KO, 1 WORK ZH, 1 ATTACK UH), seen 83674476 at (13,33).
Timeline: 476 seen -> WAIT 'gate' (remoteDefender flag had been switched off by us) -> 590 flag back on, THREAT -> 621 spawn start
(31 ticks collecting 1300) -> 657 out -> 681 arrived (24 travel) -> 683–687 stuck 5 ticks on swamp (2,16) while approaching ->
684–698 Invader walked to us, defender held range 4–7 (kite) -> 699 range 3, shooting -> 723 Invader dead (~24 ticks of fire,
matches 1086 effective hp / 50). Defender ended 1200/1200, then recycled at home. Remote resumed (rhauler at (3,11) by 750).
Findings: combat logic worked as simulated (duel test: boosted smallMelee median 54 ticks, 0 deaths). Real losses were outside
the fight: 114 ticks of flag-off wait (human/agent decision, not code) and 31 ticks waiting for 1300 energy. Missed loot fixed
in salvage (docs/SALVAGE.md). Combat approach: no clear win (swamp step ≤5 ticks). Energy wait fixed below.

### Energy reserve for remote defender (2026-10-16)
Last fight waited **31 ticks** to gather 1300 (`spawn_start` waited). Fix (does not touch home `guards`, still default off):
- `spawn.js`: while `wantDefender` and `avail < 1300`, hold **all** spawns except queen (miners no longer sneak in and reset the pool).
- `roles/upgrader.js`: `threat.holding()` pauses withdrawals with **or without** storage until `noteSpawn` sets `th.def` (holding clears → upgraders resume).
- Haulers already fill extensions to 100% while holding; builders still respect the 1300 storage reserve.

### Fixes from the W45N8 fight trajectory review (2026-10-16)
Tests: `tests/remote_fixes.js` (+ existing duel/kite/threat suites). Sim 600 ticks: 0 errors.
1. **rminer repair** (`roles/remote.js repairNow`): repair first only <30k; <100k batch-repair when the store is full (was <50k in 0247656; raised 10-16 13:15 to keep the ~2000t pause buffer, same cost); while the
   source regenerates repair for free up to 100k. (Was: any repair <100k beat harvest.)
2. **Kite hold** (`utils/kite.js`): target approaching, range ≥4, not on swamp → stand still (it walks into our range 3).
   **Ranged-only targets** (`rangedOf` without ATTACK): close to range 3 and fire, no kiting away.
3. **Swamp/flip-flop**: `move.to` already uses plain 2 / swamp 10; the defender's direct `moveTo` now does too.
   Kite has direction inertia (`memory.kd`: +2 same step, −4 reverse).
4. **After the kill**: during `clearTicks` the defender holds at the kill spot (`memory.lk`), no walk to the container.
5. **resumeEarly** (`threat.earlyNext`, `safe(r, role)`): DEFEND + defender in the room + every target <15% hp (or already dead)
   → rminer/rhauler return early; sticky until a target is healed back ≥30% or DEFEND ends. Reserver and spawning unchanged.
6. **Birth side** (`spawn.birthDirs`): remote roles take the outside-stamp spawn tiles nearest W45N8's home exit (49,14)
   first. Spawn 35,28 only has the south row (34–36,29) outside the stamp, so order is (36,29),(35,29),(34,29).
