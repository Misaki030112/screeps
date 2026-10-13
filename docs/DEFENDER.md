# W45N8 anti-NPC defender (design, 2026-10-13) — code in place, **disabled** (`remote.CFG.W45N8.defend=false`)

Enable only after: RCL4 stable (energyCapacity 1300 reliably full) **and** reserver is CLAIM×2.
Enable = set `defend: true` in `src/managers/remote.js` and deploy, or console `Memory.remote.W45N8.defend=true`.

## 1. Invader mechanics (read from the engine/back-end source, screeps/engine + screeps/backend-local)
| Item | Fact |
|---|---|
| Trigger | Every harvest adds to `source.invaderHarvested`. When the **room total** ≥ `room.invaderGoal`, a raid spawns (checked by a cron for rooms with no Invader inside). Goal = 100 000 × U(0.7, 1.3) ⇒ **70k–130k**; 10% of the time ×2 or ×0 (×0 = next raid immediately). Counter resets to 0 after each raid. We record `Memory.remote.W45N8.invaderHarvested`. |
| Precondition | There must be a live invader core (level>0) in the sector — true here (we already had one raid). |
| Where | One random exit **side**, random tile on it. Sides whose neighbour room is owned or reserved are excluded ⇒ never from W46N8 (left). W45N8 has no top exit ⇒ **bottom (x4–38, y49) or right (x49, y26–32)**, both ≥ 30 tiles from our source (14,12) / container (13,11). |
| Size | Unowned controller ⇒ always **small** bodies. 90% single creep; 10% 2+ (then 20%×: up to 5). First creep is always Melee; others Ranged or Healer (≈50/50). |
| Bodies | smallMelee: 2 TOUGH, 5 MOVE, 1 RANGED_ATTACK, 1 WORK, 1 ATTACK (1000 hp; 30 melee + 10 ranged/t; WORK dismantles 50/t). smallRanged: 2 TOUGH, 5 MOVE, 3 RA (30/t at ≤3, flees to range 3 — kites). smallHealer: 5 MOVE, 5 HEAL (60 hp/t adjacent). |
| Boosts | **50%** chance for small raids: TOUGH GO (takes 70%), ATTACK UH ×2, RA KO ×2, HEAL LO ×2, WORK ZH. Boosted melee = 60 + 20 /t adjacent. |
| Life | 1500 ticks; they never leave the room (pathing maxRooms 1); in an **unowned** room they do not suicide, they hunt our creeps then hit structures. |
| Today | One smallMelee 13:40–14:40 (≈ tick 83613200+); our container (13,11) was **destroyed** during the pause (needs 5 000 energy to rebuild). |
| Invader cores | Level-0 cores (100k hits, no creeps) appear in unowned rooms of the sector and attack/hold reservations. This defender (50 dmg/t) is **not** for cores (2000 ticks). A core needs a separate melee buster (10 ATTACK + 10 MOVE = 1300, 300 dmg/t ⇒ ≈340 ticks); not built, decide when one appears. |

## 2. Cost model (RCL4, ≈3.9 s/tick, ≈22 150 ticks/day)
**Body: 5 RANGED_ATTACK + 6 MOVE + 1 HEAL = 1300 energy, 12 parts, spawn 36 ticks.** Damage 50/t at range 1–3, self-heal 12/t, 1200 hp, speed 1 tile/t on plain/road (swamp 1/5).

| Quantity | Value | Source |
|---|---|---|
| Raids/day | goal 100k ÷ harvest rate: at today's ≈6 e/t ⇒ **≈1.3/day**; at full reserved 10 e/t ⇒ **≈2.2/day** | engine constant + DB |
| Pause per raid now | detection→TTL end (≈1450) + 80 buffer + ≈60 resume travel ⇒ **≈1 590 ticks** (≈1.7 h) | `remote.js`, events 13:40–14:40 |
| Energy lost per raid now | 1 590 × 4.7–8 e/t net = **7.5k–12.7k** + container rebuild 5k (if dismantled, it was today) + reservation decay (≈1 500 ticks of reserve) ⇒ **≈12k–18k** | model.py remote actual/ideal |
| Defender cycle | spawn 36 + travel ≈40 + fight ≈50 (sim median 48–52) + return ≈40 ⇒ ≈170 ticks, remote back in ≈170 ticks instead of ≈1 590 | duel sim |
| Defender net cost | 1300 − recycle refund. Refund = Σ min(125, partCost × TTL/1500), TTL≈1 370 ⇒ RA 5×125 + MOVE 6×45.6 + HEAL 125 ≈ **1 020** ⇒ **≈280 energy** + 36 spawn-ticks | engine `_die.js` (rate 1.0, cap 125/part) |
| Saving per raid | ≈1 420 ticks × 4.7–8 + container saved ⇒ **≈7k–16k** | |
| Per day | +9k … +35k energy for ≈400–600 energy spent | |
| Break-even | One successful intercept pays for ≈25–50 defenders. Even a death (1300, ≈5% in sim) is < 1/10 of one raid's loss. | |

Pre-spawning on the harvest counter is **rejected**: the goal is hidden and random (70k–130k, sometimes 0 or 200k), so a pre-spawned creep would idle most of its 1500 ticks (cost 1300 instead of ≈280).

## 3. Behaviour (src/roles/remote.js `defender`, ≈40 lines, no PathFinder except `moveTo` while approaching)
1. **Spawn on demand only** (`managers/spawn.js`): remote paused **and** Invader-only **and** exactly 1 Invader **and** no HEAL part **and** its TTL > 300 **and** RCL ≥ 4 **and** no defender alive. Otherwise keep today's behaviour (pause, wait it out).
2. **Travel** on the fixed remote route (same exits as haulers: home (49,14) → remote (0,14)).
3. **Engage only `owner === 'Invader'`.** Any player creep with ATTACK/RANGED, a second Invader, or an Invader healer ⇒ abort and go home (we never fight players: diplomacy with The Council).
4. **Ranged + kite** (not melee): melee would trade 30–60/t adjacent; at range 3 a smallMelee only lands its 1 RA (10–20/t), which ≤ self-heal 12/t unboosted. When the target has ATTACK and range ≤ 2, step to the best neighbour (max range, avoid swamp −25, prefer open space); approach with `moveTo(range 3)` when range > 3. `rangedAttack` + `heal(self)` every tick (both allowed together).
5. **Damaged < 60%** ⇒ retreat to W46N8 park (46,21); Invaders cannot follow across the border; the tower heals our hurt creeps; re-engage at ≥ 95% if the target still lives. No "standing still until death".
6. **Done** (no Invader for 10 ticks after arrival, or TTL < 80) ⇒ walk to Spawn1 and `recycleCreep` (refund ≈1 000 energy dropped by the spawn; the queen/manager picks it up).
7. **Early resume**: `managers/remote.js` lifts the Invader-only pause as soon as the room is visible with no combat hostiles ⇒ miners/haulers/reserver go back at once.

CPU: one `find(FIND_HOSTILE_CREEPS)` per tick in the remote room, ≤ 1 `moveTo` per tick while approaching; ≈0.2–0.4 ms/tick for ≈170 ticks per raid ⇒ negligible.

## 4. Test (`node tests/defender_duel.js`, results in metrics/defender_duel.json)
Real W45N8 terrain, engine bodies/damage/fatigue/boost rules, Invader AI per engine `findAttack.js`, spawn edge random (bottom/right), 20 runs each:

| Scenario | Expect | Wins | Retreats | Defender died | Median ticks | Median dmg taken |
|---|---|---|---|---|---|---|
| smallMelee | win | 19 | 0 | 1 | 48 | 140 |
| smallMelee boosted (50% of raids) | win | 19 | 0 | 1 | 52 | 340 |
| melee + ranged | retreat (not spawned) | 0 | 20 | 0 | – | 0 |
| melee + healer | retreat (not spawned) | 0 | 20 | 0 | – | 0 |

`scripts/check.js` (build + 600-tick home sim) passes with the code present and the flag off.

## 5. Not done / later
- Healer pairs and 2+ raids (≈10%): need 2 defenders or a 1800+ body (RCL5). Skipped for now.
- Optional cheap win independent of the defender: don't flee at first sight; Invaders spawn ≥30 tiles away, so remote creeps could keep working until an Invader is within ~8 tiles. Not implemented (more logic, needs testing).
- Invader core buster (see §1).
