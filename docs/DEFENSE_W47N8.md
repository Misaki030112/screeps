# W47N8 defence doctrine (2026-10-19 17:3x, Misaki t249u)
Defensive only. Never leaves W47N8, never crosses the seal (y<=3), never safe mode (advice only), no new ramparts.
Code: `src/rooms/w47n8/defense.js` (pure, `tests/w47n8_defense.js`), wired in `index.js` towerRun/spawnRun and `roles.js` w8defender.
Model: `tools/combat_sim.py` (same tick model as `defense.sim`). Revert switch: `Memory.ops.w8defOld = 1` (old spawn trigger).

## Before (22844c1 / 6d15f72) vs home W46N8
| | W47N8 before | Home W46N8 (`managers/tower.js`, `utils/focus.js`) |
|---|---|---|
| eligible | claimer, y>=4, armed within 3 of ours/walls | every hostile in room (edge drainers banned after 2 heal-back cycles) |
| net check | tower dmg vs own heal formula (12 adj / 4 r<=3) | `effective` (TOUGH/boost) - `healOn` |
| priority | claim > in-base > highest dmg-heal | healer first, fastest kill, sticky near-kill |
| floor | 300 unless in-base armed / claim | 300 unless hurting / dying in 2 |
| defenders | 2 on any armed in W47N8 or >=2 armed in W47N9; closest armed; idle at 27,6 until death | guards OFF by default (Misaki 10-16) |

## Now
Tower math: 600 at r<=5, -30/tile, 150 at r>=20. Tower 33,35 -> seal 27,3 is r32 (150); Spawn2 15,18 is r18 (210); core r<=5 (600).
Break-even vs heal H (12 per HEAL part, all stacked): tower wins only if sum(tower dmg) > 12*H.
- **Tower** (`towerPick`): claimer anywhere | anything inside the seal | armed creep hurting us (in reach of our creeps/structures/seal walls).
  Unarmed drain tanks north of the seal are never shot. Net damage > 0 only. Healer > ranged > melee > other, fastest kill, sticky if dying in 2.
  Non-urgent target: only towers >= 400 energy. Drain tracker (`focus.track`, `room.memory.drain8`) bans knocked-down-and-healed creeps 1500 t.
- **Spawn gate** (`assess`, every 5 t while armed hostiles are in W47N8 or north_watch reports a W47N9 group with bodies
  `Memory.ops.w8invNb`): towers alone win -> no defenders; towers + 2 defenders win with 0 losses -> spawn (max 2);
  otherwise no defenders (do not feed a lost fight) and, if the force is inside the seal, `Memory.ops.w8adv = {advise:'safemode'}`.
- **Defender** (`defPlan`): shoots the tower focus when in range 3 (focus fire), else healer-first pick, `rangedMassAttack` when >=3 within 2;
  heals self/allies; keeps >=3 from melee (kite); <60% hp -> retreat to the tower (tower heals), back at 95%; unwinnable -> stay within 8
  of a tower, do not chase; ignores north-of-seal drain tanks; 100 ticks quiet -> recycle at Spawn2.
- **north_watch**: intrusion/group alerts carry a `verdict` from the combat model (towers / towers+2 / unwinnable -> recommend safe mode).

## Sim (unboosted BustJetter W48N9 squad: 11RA, 7RA, 10A5T, 8A4T, 6H, 7H, 6H = 19 HEAL -> 228 heal/t; 720 structure dps)
| scenario | result |
|---|---|
| RCL4 seal, tower + 2 def | lose (defenders out in ~6 t, 2600 energy wasted) |
| RCL4 Spawn2, tower +/- 2 def | lose |
| RCL4 core (r<=5) tower alone | win, 26 t, 250 energy |
| RCL5 Spawn2, 2 towers alone | win, 47 t, 920 energy |
| RCL5 seal, 2 towers alone (r32/r28) | win, 60 t, 1180 energy (marginal; needs refills) |
| melee + 2 healers at seal, RCL4 | towers lose, + 2 def win (the case defenders exist for) |
| seal wall 50k vs full squad | 69 t (94 t with tower repair at r32) |
Caveat: model assumes the squad stands and fights; a real player retreats to heal (drain) — the tracker and net>0 rule cover that.
Conclusion RCL4: full squad breaking in = unwinnable for us; recommend Misaki activates safe mode (3 left) when it passes the seal
and heads to Spawn2. From RCL5 (2nd tower 34,31) towers alone are expected to hold.

## 17:34-17:40 updates (Misaki)
- **Joint defence** (`defense.plan`, the one planner; `index.js assessRun` writes `Memory.ops.w8roster = {home, w8}`): whenever an armed
  threat is active (armed in W47N8, or north_watch W47N9 group) and W46N8 has no player combat creeps, home spawns ONE `w8defender`
  (`memory.jd = 'W46N8'`, home W47N8, RA+MOVE max fit: 11RA11M at cap 2300) via `managers/spawn.js` 1b2 (overrides the storage floor,
  queen first). Local W47N8 defenders = fewest (0-2) that make towers + home + local win with no losses in the sim, else 0.
- **Bodies**: RA+MOVE only, no HEAL; no healer role (HP rule instead of damage prediction).
- **HP rule**: fight while >= 60%; < 60% retreat to the nearest tower (towers heal); back to the wall at >= 90%.
- **Targeting** (towers and defenders): healers always first, then ranged, then melee; lowest hp within a class; defenders shoot the
  towers' focus when in range 3. Towers still need net damage > 0 (anti-drain).
- **Wall posts**: tile right behind the seal (y=4) of the segment nearest the enemy (east 24-31 minus swamp 27,4; west 8-11),
  2 tiles apart per defender; pre-staged from north_watch's mean enemy x (`Memory.ops.w8invNx`). Melee north of the seal cannot reach y=4.
- **Seal repair under fire**: w8builders with energy repair the lowest seal wall an armed hostile can reach, standing within 3 of it on our
  side as far from enemy range as possible (`repairPick` / `repairStand`).
- Sim: 17:34 pair (8RA+6RA) at the seal: tower + home 11RA11M win in ~15 t; pair + 2x7H: needs home + 1 local (planner picks it).

## 2026-10-19 17:5x strategy review: tower 2 is the decisive step, so it is built first at RCL5
- Sim F2/F3 above: with 2 towers the full unboosted squad loses to towers alone (Spawn2 47 t, north seal 60 t); with 1 tower it needs defenders.
- Old layoutRun PRIO was spawn > extension > tower: at RCL5 the 10 new extensions (30k build, 6-site cap) went up first and tower 34,31
  waited ~2-3 h behind them at W47N8's ~10-15 e/t build. Now spawn > tower > extension, and nothing new is queued while a tower site
  stands (c7357bc, `tests/w47n8_tower_first.js` fails on the old order). Builders already pick the closest site; 34,31 is beside storage.
- ETA (RCL4 96.2k/405k at tick 83742113, ~4.1 s/tick): RCL5 at live ~23 e/t ~10-20 09:00, at model ideal 29.6 ~10-20 05:45 (UTC+8);
  tower 2 (5k) built ~0.5-1 h later. Until then the joint-defence roster (W47N8 + home 11RA11M) carries the 4-creep case.
- Boost watch: north_watch sees UH (ATTACK x2) in W48N9 labs (97) and W47N9 (20). UH only helps the melee pair (10A/8A): 18A boosted
  = 1080 dmg/t on a seal wall, 50k wall in ~46 t without repair. Ranged/heal parts are unaffected, so the tower verdicts stand.

## 17:45 roster rule (Misaki, supersedes the joint-defence bullet above)
Home always sends a baseline of 1 defender while an armed threat is active and W46N8 is safe (below the storage floor is OK).
Local W47N8 defenders = fewest 0-2 that win together with the baseline. A 2nd home defender only if the sim says it turns a loss into a win.
Still unwinnable: baseline only, no local spawns; inside the seal -> `Memory.ops.w8adv` advises safe mode.
Model examples (RCL4, tower r32): pair 8RA+6RA -> home 1, local 0; pair + 2x7H -> home 1, local 1; full W48N9 squad -> home 2 + local 2 win.

## 2026-10-20 05:4x strategy review: the W47N9 border camp and what tower 2 changes

- **What sits north now (live t83752265):** W47N9 is BustJetter's own RCL6 room (2 towers, 69 ramparts, 1 spawn). Their 8RA and 9RA creeps camp at (31-32,47) with two healers (7H at 33,47, 5H at 34,47), two tiles from our north exit. A third healer (7H) is at (25,30) in their core. This is the same camp spot as 83741903 / 83742061 / 83750434 (32,47 / 31,47). The pair never crossed and dealt 0 damage.
- **Cost of the camp:** `north_watch` sets `w8invN` for any 2+ armed creeps anywhere in W47N9, so the joint roster stays live and each 1500-tick life gets refilled. Defence waves in the last 12 h: 03:32-03:52 (home 2x22-part + home healer + 3 local 12-part) and 05:23-05:38 (3 local 12-part + 1 home 22-part), about 6-9k energy per wave, roughly 4-6 e/t combined while the camp holds.
- **Alert verdict bug, fixed (tools only):** the alert verdict only fed the armed bodies to the combat model, so 2RA + 2 escort healers read "towers win". With the healers the model says 1 tower at r32 **loses** and towers + 2 defenders win. The in-game planner already counted the healers (`w8invNb` = armed + drain), so the roster was right and only the alert text was wrong. `tools/north_watch.py` now adds healers within 3 tiles of the group to the verdict, uses live W47N8 tower ranges to the seal (27,3) and records `support` (number of escort healers). `tests/north_watch_test.py` covers both.
- **Tower 2 at 24,8 ends the standing bill:** range 5 to the seal (600 dmg). Model at the seal, towers only: [32] loses to 2RA+2H and to 2RA+3H, [32, 5] wins both in about 10 ticks. Once 24,8 is built, the minimal winning combination is towers only, so under the 17:45 rule only the baseline home defender stays (~1.5 e/t) instead of 3 local + home. Keep 24,8 as the only site at RCL5 (RCL5 ~08:15-08:40, then build), ahead of extensions.
- **Not changed (Misaki's call):** the in-game force still includes every W47N9 healer, including the one in their core 17 tiles away, so it sizes the roster one healer heavier than the border group. Counting only escorts would save about one local 12-part defender per wave until tower 2 is up (~2.5 h). Not worth changing defence sizing for that window.
