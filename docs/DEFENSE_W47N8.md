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
  (`memory.src = 'W46N8'`, home W47N8, RA+MOVE max fit: 11RA11M at cap 2300) via `managers/spawn.js` 1b2 (overrides the storage floor,
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
