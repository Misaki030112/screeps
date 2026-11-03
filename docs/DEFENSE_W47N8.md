# W47N8 defence doctrine (2026-10-19 17:3x, Misaki t249u)
Defensive only. Never leaves W47N8, never crosses the seal (y<=3), never safe mode (advice only), no new ramparts.
Code: `src/rooms/w47n8/defense.js` (pure, `tests/w47n8_defense.js`), wired in `index.js` towerRun/spawnRun and `roles.js` w8defender.
Model: `tools/combat_sim.py` (same tick model as `defense.sim`). Revert switch: `Memory.ops.w8defOld = 1` (old spawn trigger).

## 2026-11-03 14:4x — roadCrit before deep seal

Peacetime softCap clear re-armed `sealRaise`; lone builder was sticky on north seal→1M while `roadCrit`~38. Repair order now puts kept roads `<25%` **before** deep `wallJob` (Overmind RoadLogistics critical / fortifyDutyThreshold). KEY/STAGE3/sealMinE/soft-gate unchanged; under-attack seal path unchanged. Detail: `docs/RCL7.md` 14:4x.

## 2026-11-03 11:3x — repair debt (containers before roads)

Peacetime KEY DONE / sealPark: builders now repair owned containers `<50%` **before** seal wallJob and road paving (Overmind-aligned). Ctl standee tops ctl battery. Not a fortify target change — KEY/STAGE3/sealMinE unchanged. Detail: `docs/RCL7.md` 11:3x.

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

## Healer positioning (Misaki 10-20 07:31)
- The dedicated healer (w8healer) never stands by the walls. It waits at a safe spot >= 4 tiles inside the seal
  (`HIDLE` 21,8 / 20,8 / 19,8 / 22,8: plain, off roads), out of reach of enemy ranged standing north of the seal (y<=2 reaches y<=5).
- It leaves only when a friendly is hurt: it moves to the nearest walkable, off-road tile within 3 of the target that is outside every
  armed hostile's reach (y>=6, >4 from RA, >2 from melee) and uses rangedHeal (heal when adjacent). No such tile -> it stays home.
  When nobody is hurt it walks back to its spot. HP rule 60/90 unchanged (retreat to tower).
- Defenders below 60% retreat to the healer (tower if no healer), back at 90% as before.

## 2026-10-20 23:4x strategy review: BustJetter's biggest group vs the two seal segments
- **Biggest group so far (neighbor scan 21:45, W48N9, all unboosted):** melee 5T10A15M, 4T8A12M, 6T12A18M; 3x 6RA6M; healers 4/4/4/5/6/5 = **28 HEAL** (336 heal/t if all stack), 18.2k hp, 1080 structure dps. Back to 4 creeps by 23:41. Boost stock still tiny (W48N9 KO 11, UH 104; W47N9 UH 20).
- **Geometry after the spawn move:** towers 33,35 and 24,8. East seal 27,3 = r32 + r5 (750 dps). **West seal x 8-11 = r32 + r13-16 (420-510 dps)**. Spawn 34,30 = r5 + r22 (750). Exits from W47N9 are x 9-24 and 32-38 on y=0, so a north squad can reach either segment.
- **Sim (`tools/combat_sim.py`, all healers stacked, pessimistic):** 21:45 group vs towers alone: east seal win 32 t / 620 e; spawn win 32 t; **west seal r14 win 47 t / 920 e, r16 win 59 t / 1160 e**. Break-even towers-only: east ~64 HEAL, **west ~36 HEAL** (2 more 4H healers than the peak). West with 2 local defenders holds well past that. Seal wall 134k vs 1080 dps: ~124 t unrepaired, ~206 t with tower repair.
- **Gap fixed:** the in-game border pre-assessment (`assessRun`, from the north_watch W47N9 signal) and the alert verdict always scored the east seal, and the alert's "inside" verdict still used old Spawn2 15,18 (1 tower r19). Now `sealAt(w8invNx)` picks the segment nearest the announced group (x < 18 = west) and north_watch reports both segments when they differ (nearer first; W48N9 groups get both) and scores intrusions at the new spawn 34,30. Once hostiles are inside W47N8 the planner already used their real position, so this only moves the defender decision earlier (~100 t: spawn + walk to the west posts) and fixes what Misaki reads in alerts. `tests/w47n8_seal_west.js`, `tests/north_watch_test.py`.
- **Not proposed:** a 3rd tower only comes at RCL7 (22,7 in the plan: r12 to the west seal). Nothing to ask Misaki; the existing towers+2-defenders rule covers the west side.

## 2026-10-22 08:4x strategy review: W47N8 vs BustJetter after W47N9 safe mode ends (~10-22 15:00 UTC+8)
Question: BustJetter has 3 armed creeps massing in W48N9 since 07:46 (2x 6RA3M + 1x 3A2M, no HEAL) with UH 104 / KO 11 in
stock there (UH 20 in W47N9). W47N9's safe mode ends ~15:00 today. Does W47N8 (RCL5, towers 24,8 + 33,35, north wall 300k,
towers kept 800-1000 by the >200-free refill rule) need anything before then?

Method: `tools/combat_sim.py` `fight()` at the north seal 29,3 (tower ranges 5 / 32), towers only (0 defenders), tower energy
820 (the low end of the refill sawtooth). Boost modelled by doubling RA/ATTACK part counts (pessimistic: also doubles their hp).
- Seen group, unboosted / boosted: win in 6 / 7 ticks, 100-120 tower energy. Core: 4-6 t. Spawn2 area: 6-9 t.
- Same group + N healers (6H6M each), boosted: 1-3 healers win in 9-13 t; 4-10 healers still win (15-50 t, 280-980 energy);
  **the towers only lose at >= 11 healers (~66 HEAL parts)**. BustJetter's largest stack seen (10-16) had ~16 HEAL parts.
- Their damage on the 300k north wall: ~420/t boosted, ~700 t to breach, i.e. far longer than they live under the towers.
- W47N9 itself: towers 162/130, storage 0 at the 07:42 scan, so a follow-up from W47N9 has little energy behind it.

Conclusion: no change. Towers alone beat the visible force with a wide margin; the on-demand defender (inBase only) and
W47N7 flee (`w8flee`, armed hostiles in W47N7 or W47N8 y<=10) cover the remote. Tower 820-1000 is the normal refill band,
not a threat-posture leak (refill triggers at free > 200). Re-check only if the neighbour scan shows >= 6 healers or LO/GO
(heal / tough) boosts in W48N9/W47N9. Safe mode stays Misaki's button.

## 2026-11-02 retaliation hardening (Misaki: "加固城防，尤其面对他那一方")
Memory.defense knobs (absent = old behaviour):
- `w8seal` (set 1,000,000): north seal walls + gate 29,3 cap above the 300k STAGE3, clamped to WALL_TARGET[rcl] (1M at RCL7).
  Builders raise lowest-first. Spawn rule 6 only spawns a builder for the part above 300k while storage >= `w8sealMinE`.
  **`w8sealMinE` default 25000 (= LEAN_SOFT)** — 17:4x raised 5000→25000; 20:4x briefly 35000 then **Misaki rejected** (back to 25k).
  `wallJob` / spawn rule 6 use `TH.sealDeepOk` (02:4x): softCap2 shape + sticky `Memory.ops.w8sealPark` until nUp recovers +
  `SEAL_EDGE` intensity (2nd builder only with sealMinE+5k headroom). Override `<LEAN_SOFT` no longer deep-seals under softCap2.
- `w8key` (set 300,000): KEY ramparts (spawn/tower/storage/terminal) soft target above SOFT_RAMP, while storage >= `w8keyMinE`
  (default 8000) and no local threat. Above GATE_TOWER only towers within 10 tiles repair (efficiency 800 vs 200 hits/10e).

### 2026-11-02 17:4x post-war fortify vs softCap (strategy)
Live ~17:40 Asia/Shanghai t~84023920 peacetime: threat expired (`w8soft.why=ok`); KEY ~204–216k→300k via near towers; seal ~314k+
already above STAGE3; stor~19–21k < LEAN_SOFT → softCap2 ON. With `w8seal=1M` + old `w8sealMinE=5000`, builders kept raising seal
314k→1M (~100k e) and competed with softCap lift / KEY catch-up. Overmind gates routine fortifyDuty until colony energy ≥500k;
we keep KEY raise (towers, `w8keyMinE=8k`) and only defer deep seal. Priority peacetime: softCap lift (stor≥25k → nUp3) → KEY→300k
→ then seal→1M. Do **not** unset Misaki's `w8seal`/`w8key` knobs — gate energy instead.

### 2026-11-02 20:4x softCap thrash at LEAN_SOFT / Memory sealMinE override (strategy)
Live ~20:47 Asia/Shanghai t~84026600 peacetime post-KEY: home ~18.1% stor~17k ABOVE 2h~88%; W47 ~4.96% stor oscillating
19→25→24k; softCap2 briefly 0 then back ON (softLeft~0.7k); KEY DONE (stor/tower/spawn ~300k); seal min~396k / gate~445k climbing
to `w8seal=1M` with **live builder on north y=3**; upgrade 2h~57% short~18–34%; remotes SAFE; labs OFF no re-ask; K deposit empty.

**Root cause:** (1) `Memory.defense.w8sealMinE=5000` (set with fortify knobs #23 @15:22 alongside `w8seal`/`w8key`) overrode the
17:4x code default of 25000 — `wallJob` + spawn rule 6 kept deep-raising seal while softCap2 needed the energy. (2) Even
sealMinE=LEAN_SOFT has **zero hysteresis**: the tick stor≥25k, softCap lifts and seal starts, draining stor back under 25k →
softCap thrash (live 24947→24347 in ~10t). Overmind `fortifyDutyThreshold=500k` parks *all* routine fortify until colony energy
is fat (`barrierHits[7]=1M`); we keep KEY tower raise ungated (DONE) and only defer deep seal, but need headroom **above**
LEAN_SOFT so upgrade can hold nUp3 before seal burns surplus. TooAngel gates walls on room-healthy / storage floors — same shape.

**Shipped:** default `sealMinE` **25000→35000** (LEAN_SOFT+10k); live Memory `w8sealMinE` **5000→35000** (stale override fixed;
`w8seal`/`w8key` untouched); `w8day.sealMinE`/`sealRaise` + `w8soft.sealMinE`/`sealCap`/`sealRaise` obs so patrols see the
effective gate. Tests fortify + dayobs.

### 2026-11-03 02:4x seal soft-gate vs softCap2 (strategy; no sealMinE raise)
Live ~02:47 Asia/Shanghai t~84031795 peacetime: home ~19.22% stor~16k ABOVE; W47 ~5.90% stor**25004** softCap2 OFF
sealRaise1 builders2 nUp3 KEY DONE sealMinE=25000 (Misaki rejected 35k) hubReady0; 2h upg ~64–69% consec soft; remotes SAFE;
labs OFF no re-ask. SoftCap has been thrashing the LEAN_SOFT edge for hours — when ON, short crashes (~30%); when OFF, seal
immediately resumes and drains the band.

**Research:** Overmind `fortifyDutyThreshold`~500k parks *routine* fortify until colony energy is fat (+ `storageBuffer`);
TooAngel gates walls on healthy/storage floors. We already keep KEY ungated (DONE) and only deep-seal above STAGE3 — but the
energy gate was `stor≥sealMinE` alone, so (a) threatSoft with fat stor still deep-sealed, (b) Memory override `<LEAN_SOFT`
re-opened the 17:4x failure mode, (c) zero sticky hysteresis at 25k.

**Shipped (sealMinE stays 25000):** `TH.softThin` / `sealDeepOk` / `updateSealPark` → sticky `Memory.ops.w8sealPark` until
softThin off **and** nUp≥peacetime base; wallJob + spawn rule 6 clamp; edge intensity `SEAL_EDGE=5k` (max 1 deep-seal builder
near the band); `w8day.sealPark` + `sealRaise` via sealDeepOk. Tests fortify + dayobs. **No** HUB_LINK/labs flips; **no** re-ask.

### 2026-11-03 08:4x softCap2 energy hysteresis (strategy; seal softThin stays strict)
Live ~08:26–08:47 Asia/Shanghai e7f2017: softCap JUST cleared after ≥70 then **ON again** at stor~23.2k — zero-hysteresis energy half. Seal soft-gate (02:4x) already parks seal while softThin; the remaining thrash was softCap itself recycling nUp 3↔2.

**Research:** leanBank 15/20k sticky is the in-repo pattern; Overmind storageBuffer/fortifyDuty are fat single thresholds; TooAngel healthy floors. Raising sealMinE again is off the table (Misaki rejected 35k).

**Shipped:** `LEAN_SOFT_ARM=22000` + `softEnergyCap` / `w8day.softE` (clear@25k re-arm@22k). `softCap2 = threatSoft || softEnergyCap`. roles soft-band follows softE (threat does not park). **`softThin` / `sealDeepOk` stay STRICT <LEAN_SOFT** so seal still waits for a true ≥25k clear — do not couple seal park to the softCap ARM band. sealMinE stays 25000. Tests dayobs/mminer/filler. No HUB_LINK/labs flips; no re-ask.

