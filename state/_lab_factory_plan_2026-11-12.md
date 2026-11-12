# Lab + Factory placement plan — 2026-11-12

Planning only. No construction sites were placed, no live Memory flags were edited (`ops.labs`, `RCL6_LABS`, `RCL7_INDUSTRY`, market), no deploy, and no game-code change.

**Live source:** `tools/q.py` console query at **Game.time 84217332** (~09:43 Asia/Hong_Kong). Both rooms were visible. Construction-site lists were empty. Not a snapshot fallback.

RCL7 allows 1 factory and 6 labs per room. This plan also reserves the remaining 4 lab tiles so the RCL8 10-lab cluster can be finished later without moving anything.

---

## 1. W46N8 (home)

**Already standing (do not rebuild, do not move):**

- Storage **(37,31)** — plain, ramparted
- Terminal **(35,31)** — plain, ramparted. **Exists. No reserved extra terminal tile.**
- Labs 1–3 (RCL6, already built, already ramparted):
  - **1 (34,22)** swamp — reagent / input A (reaches all 8 other labs in the finished cluster)
  - **2 (35,21)** swamp — reagent / input B (the unique partner of lab 1)
  - **3 (33,21)** swamp — first output
- Spawns (35,28) / (30,34); hub link (37,29); controller link (30,31); upgrader stands in use **(30,30)** and **(31,30)** (container on 30,30). Mineral **O (40,24)** + extractor + container (41,24).

**Factory (build now):** **(35,30)** plain, empty. This is the coded hub slot in `src/layouts/W46N8.js`.

- Distance: storage range **2**, terminal range **1**, mineral range 6.
- Exception to “factory range 1 of storage,” justified: every tile in range 1 of storage is already the manager stand **(36,30)**, extensions (37,30)/(36,31), the storage-door / srcA roads (36,32)/(37,32)/(38,30)/(38,31), or miner-B’s stand (38,32). None of those should be stolen.
- The empty manager tile **(36,30)** is range 1 of factory, storage, terminal, **and** hub link (37,29). That is the intended hub transfer. Do not build on 36,30.

**Full 10-lab cluster** (coded 4×4 stamp at x=33–36, y=20–23, with the srcA/lab trunk roads kept on 34,21 and 35,22, plus 33,20 and 36,23):

| # | Pos | Terrain | When | Role | d(storage) | d(terminal) | d(mineral) |
|---|-----|---------|------|------|------------|-------------|------------|
| 1 | 34,22 | swamp | **already built** | input A | 9 | 9 | 6 |
| 2 | 35,21 | swamp | **already built** | input B | 10 | 10 | 5 |
| 3 | 33,21 | swamp | **already built** | output | 10 | 10 | 7 |
| 4 | 34,23 | swamp | **build now (RCL7)** | output | 8 | 8 | 6 |
| 5 | 33,22 | swamp | **build now (RCL7)** | output | 9 | 9 | 7 |
| 6 | 34,20 | swamp | **build now (RCL7)** | output | 11 | 11 | 6 |
| 7 | 35,23 | swamp | reserve for RCL8 | output | 8 | 8 | 5 |
| 8 | 36,22 | swamp | reserve for RCL8 | output | 9 | 9 | 4 |
| 9 | 36,21 | swamp | reserve for RCL8 | output | 10 | 10 | 4 |
| A (10) | 35,20 | swamp | reserve for RCL8 | output | 11 | 11 | 5 |

Reaction check: the only input pair that reaches all 8 others is **(34,22)+(35,21)** — both already built. Every lab has a walkable neighbour (the trunk roads 34,21 / 35,22 / 33,20 / 36,23, or open swamp/plain). The two roads through the stamp must stay roads; they are the hauler spine, not lab tiles.

All 10 lab tiles are swamp. That is already committed by the three standing labs. There is no equal-access all-plain 10-pack that keeps those three in place, so swamp is accepted here.

**Ramparts:** labs 1–3 already have point ramparts. Factory (35,30) sits against the existing terminal rampart (35,31) and tower rampart (36,29) but has no rampart yet; the layout already reserves one at RCL7. Labs 4–10 also have planned point ramparts in the layout. **Do not place those ramparts in this wave.**

Upgrader stands, the queen path through stamp A, and the main energy roads are untouched.

### W46N8 neighborhood (x=28–41, y=18–36)

Legend: `#` wall, `~` swamp, `.` plain, `r` road, `S` spawn, `N` storage, `T` terminal, `L` link, `t` tower, `U` upgrader stand, `c` container, `E` extension, `X` mineral/extractor, `C` controller, `F` factory, `m` manager stand (keep open), labs `1–9` and `A`=10. Existing labs are 1–3.

```
      3         4
    89012345678901
 18 ####.r.....~~~
 19 ####r......~~~
 20 ###..r6A~~~~~~
 21 .....3r29~~rr~
 22 .....51r8~r~~r
 23 ..rEE~47rr.trr
 24 ..E.EEEcEErr#c
 25 .E.EEErErEr###
 26 ~~ErEEErEEr###
 27 ~ErEEErErEr###
 28 ~~~r.EESEEr###
 29 ...rr..rtLr###
 30 #.UU.rrFmEr###
 31 #rL..rrTENr###
 32 #rEEEEErrr.###
 33 rrErErEr.t####
 34 ..SELEc..#####
 35 ..ErErE..#####
 36 ..EEEEE~######
```

---

## 2. W47N8 (colony)

**Already standing:**

- Storage **(35,32)** — plain, ramparted
- Terminal **(33,32)** — plain, ramparted. **Exists. No reserved extra terminal tile.**
- Spawns **(34,30)** and **(33,30)** (live hub; ignore stale `config.SPAWN [15,18]`)
- Hub container **(33,33)**; hub link **(33,34)**; controller **(15,25)**; ctl container **(13,26)**; upgrader stands **(12,25) / (14,26) / (14,27)**
- Mineral **K (37,45)** + extractor + container **(37,44)**
- 3 towers (33,35 / 24,8 / 22,7). RCL8 tower tiles **(34,31), (36,31), (36,33)** are still empty and must stay reserved. Power spawn **(36,32)**, nuker **(34,28)**, observer **(33,28)**, spawn3 **(39,30)** also stay reserved.
- No labs, no factory, no construction sites.

**Factory (build now):** **(35,30)** plain, empty. This is the coded slot in `src/rooms/w47n8/layout.js`.

- Distance: storage range **2**, terminal range **2**, mineral range 15.
- Exception to “factory range 1 of storage,” justified: the four open tiles in range 1 of storage are exactly the reserved RCL8 towers / power spawn (34,31 / 36,31 / 36,32 / 36,33). The other three neighbours are the south-short-path road **(34,32)**, the factory door road **(35,31)**, and a wall **(35,33)**. Do not steal a future tower or landlock the south path.
- Door tile **(35,31)** (already a road) is range 1 of both factory and storage. A hauler standing there transfers both. (34,31) currently also touches factory+storage+terminal, but that tile becomes a tower at RCL8, so 35,31 is the lasting door.
- Adjacent to live spawn (34,30). Not on the south short path, not on an upgrader stand, not on the west bypass.

**Full 10-lab cluster — new site, not the coded `ORDER.lab` list.**

The layout’s 10 lab tiles `33,29 / 34,29 / 35,29 / 36,29 / 35,28 / 29,37 / 28,37 / 28,38 / 29,38 / 40,30` are **not a reaction cluster**. They fall into three range-2 components (a 5-lab north-hub row, a 2×2 south of the B2 extensions, and a lone tile at 40,30). `runReaction` cannot use that as one chamber, and later labs would not fit together without moving the first six. The north-hub pocket only has five free tiles once factory / nuker / observer / spawns / walls are respected, so a 10-lab stamp cannot sit next to storage.

Recommended cluster is the compact cap of the open pocket just south of the B2 extension strip (y=36), west of the walls at x=29–30, and east of the south-exit road (24,37 / 25,38 / 26,39–42). It does **not** sit on the south short path (12,28–15,33–24,35–31,35–33,33/34,32), the upgrader stands, or the west 1-wide bypass.

| # | Pos | Terrain | When | Role | d(storage) | d(terminal) | d(mineral) |
|---|-----|---------|------|------|------------|-------------|------------|
| 1 | 29,38 | plain | **build now** | output | 6 | 6 | 8 |
| 2 | 28,37 | plain | **build now** | output | 7 | 5 | 9 |
| 3 | 28,38 | plain | **build now** | output | 7 | 6 | 9 |
| 4 | 27,38 | plain | **build now** | **input A** | 8 | 6 | 10 |
| 5 | 27,39 | plain | **build now** | **input B** | 8 | 7 | 10 |
| 6 | 27,40 | plain | **build now** | output | 8 | 8 | 10 |
| 7 | 28,40 | plain | reserve for RCL8 | output | 8 | 8 | 9 |
| 8 | 26,38 | **swamp** | reserve for RCL8 | output | 9 | 7 | 11 |
| 9 | 26,37 | plain | reserve for RCL8 | output | 9 | 7 | 11 |
| A (10) | 25,37 | plain | reserve for RCL8 | output | 10 | 8 | 12 |

Reaction check: the unique input pair for the finished 10 is **(27,38)+(27,39)**. Both are in the first six, so the chamber is already reaction-valid at RCL7. The first three (29,38 / 28,37 / 28,38) are also all within range 2 of each other (usable as a 3-lab starter).

**Access aisles — keep these three tiles empty forever (no lab, no factory, no extension):**

- **(27,37)** plain — north door for labs 2 and 3 (the y=36 row is a solid wall of extensions, so 28,37 / 29,37 would otherwise landlock)
- **(29,37)** plain — east door for labs 1 and 2
- **(28,39)** plain — hole giving lab 7 (28,40) a walkable neighbour; also a natural manager/hauler stand (range 1 of labs 1, 3, 5, 7 and range 2 of the inputs)

Lab 8 **(26,38)** is the only swamp in the 10. It is required for a compact, access-safe, 2-input-reach-all pack in this pocket (dropping it makes the remaining candidates either landlock or fall outside range 2 of the inputs). It is not used for the factory. Haulers can also walk the already-paved south-exit road on 24,37 / 25,38 / 26,39.

Access path from storage is the existing south trunk (34,32 → 32,35 → 24,35) then 23,36 / 24,37 into the pocket. That is **not** the west 1-wide bypass (8,18–22 / 9,17 / 9,23 / 10,16 / 10,24 / 11,15 / 11,25 / 12,26).

**Ramparts:** factory (35,30) is adjacent to the live spawn rampart at 34,30 but has no rampart yet. The whole lab cluster is **outside** the existing core rampart envelope (storage / terminal / spawns / towers / gate 29,3). Point ramparts would be needed later. **Do not place them now.**

### W47N8 neighborhood (x=22–42, y=24–44)

Same legend, plus: `a` = access aisle (do not build), `t` = reserved RCL8 tower (empty), `P` / `K` / `O` / `s` = reserved power spawn / nuker / observer / spawn3. Labs `1–9` and `A`=10. South short path is the `r` row at y=35 leading into `c` (33,33) / `r` (34,32).

```
            3         4
    234567890123456789012
 24 #....EE.ErE##########
 25 #....rrrErE##########
 26 ##...EE.ErE##########
 27 ####....ErE##########
 28 #########rEOK.#######
 29 ##########r....r####r
 30 ##########rSSFrErs.r.
 31 .#########ErtrtErEr..
 32 ..########.TrNPErE..#
 33 .~~..#####.cr#tErE..#
 34 r~EEEEE###EL###ErE..#
 35 ~rrrrrrrrrrt####rE...
 36 #rEEEEEEEEE#####rE...
 37 ##rA9a2a#######ErE..#
 38 ###r8431######.ErE..#
 39 ####r5a######..ErE.##
 40 ####r67######..ErE.##
 41 ####r..######......##
 42 ####r..######..r...##
 43 #####r.#######r....##
 44 #####r.########c.~###
```

Controller / upgrader / west-bypass pocket (untouched; stands marked `U`):

```
      1         2
    8901234567890
 22 r############
 23 .r###########
 24 ..r.#########
 25 ...rUL#######
 26 ....rcU.#####
 27 #....rU.#####
 28 ####r.r..####
 29 #####r...###~
 30 ######r.~###.
 31 #######r~###.
 32 #######r~.#..
 33 #######rrrrrr
 34 ######.r.....
 35 ......r......
 36 .....r..#####
```

---

## 3. Rationale and alternatives

### W46N8 — why this cluster

It is the already-coded 4×4 stamp, and **labs 1–3 plus both reagent seats are already built**. Moving them would throw away 150k and break the assumption in `src/managers/labs.js`. Factory (35,30) is the hub slot the manager at (36,30) was planned to touch.

**Next-best alternatives (do not use):**

- A from-scratch all-plain 10-pack closer to storage: would require destroying or abandoning the three standing labs and their ramparts. Not worth it.
- Putting the factory on (36,30) or (38,32): those are the manager stand and miner-B stand. (36,30) is the only tile that touches storage, terminal, factory, and hub link together.

### W47N8 — why this cluster

It is the closest access-safe 10-lab pack that is a real 2-input reaction chamber, is almost all plain, reuses three of the old plan’s southern tiles (28,37 / 28,38 / 29,38) without keeping the broken 29,37 landlock, and is fed from the existing south trunk rather than the west bypass.

**Next-best alternatives (do not use as the main cluster):**

1. **Old `ORDER.lab` list** — (33–36,29), (35,28), (28–29,37–38), (40,30). Three disconnected groups; 40,30 is also next to the W46 inter-room road. First six built there could not grow into a 10-lab chamber without moving buildings. Rejected.
2. **2×5 at (27–28, 38–42)**, all plain, slightly farther south. Inputs would be (27,40)+(28,40), but (28,40) and (28,41) are landlocked against the x=29 wall. Rejected without cutting holes, which then loses compactness to the chosen pack.
3. **East corridor (40–41, 32–36)** — closer to storage (min range 5) but a 2-wide strip boxed by the x=39 extension wall and terrain walls, so interior labs have no walkable neighbour. The inter-room road on 40,31 / 41,30 also cuts the pocket. Rejected.
4. **Mineral-side 3×4 around (38–40, 41–43)** — close to the K mineral (range 2–4) but storage/terminal range 9–12, and a tight pack landlocks 39,42 / 40,42 / 40,43. Only worth a later look if we ever wanted a second, mineral-adjacent chamber; not this build.
5. **West filler tiles (23–26, 24–26)** — still-needed unbuilt RCL8 extension slots on a congested approach toward the controller. Do not relocate them for labs.

---

## 4. Conflicts with the existing coded layout

**W46N8:** none. Factory (35,30) and labs 4–10 are exactly `src/layouts/W46N8.js` / `data/layout_W46N8_v2.json`. They are currently hidden from auto-placement only because `plan.RCL7_INDUSTRY` is still `false` (labs 1–3 were placed under `RCL6_MINERALS=true`).

**W47N8:** the factory slot matches `layout.js` (`ORDER.factory = [35,30]`). The lab coordinates do **not**. Recommend replacing `ORDER.lab` with the 10 tiles above when (and only when) someone later flips `config.RCL6_LABS` / edits the layout module. Until then, manual sites or a layout edit would be required; this report does neither. Leave 29,37 as an aisle even though the old plan listed it as a lab. The five old north-hub lab tiles (33–36,29 and 35,28) stay empty and available for the already-planned nuker/observer or general breathing room; do not put labs there.

---

## 5. What must NOT be built or flipped yet

This is a coordinates plan so Misaki can see the tiles first. Even after a later nod to place sites:

- Do **not** flip `plan.RCL7_INDUSTRY` or `config.RCL6_LABS` / `config.RCL7_INDUSTRY` as part of “just telling her where.”
- Do **not** set `Memory.ops.labs` and do **not** start reactions or boosts. Home `labs.js` is still dormant; W47 has no lab/factory operator code.
- Do **not** touch market.
- Do **not** place the four RCL8 labs (W46: 35,23 / 36,22 / 36,21 / 35,20; W47: 28,40 / 26,38 / 26,37 / 25,37).
- Do **not** build on W47 aisles **(27,37), (29,37), (28,39)**, on W46 manager **(36,30)**, or on W46 lab-stamp roads **(34,21), (35,22), (33,20), (36,23)**.
- Do **not** place ramparts, nuker, observer, power spawn, or the reserved RCL8 towers in this wave.
- Do **not** put anything on W47 upgrader stands (12,25 / 14,26 / 14,27), the south short path, or the west bypass.

Energy bill if the first wave were placed today: W46 factory 100k + 3 labs 150k = **250k**; W47 factory 100k + 6 labs 300k = **400k**; **650k total**. Live storage is still in the mid-teens / low-20k, far under the ~100k cushion the colony has been using as the industry gate. Placing the sites now would also pull builders off upgrade via `siteRem`. The tiles above are where they should go when she actually wants them built.

---

## 6. First-wave construction-site list

**11 sites, not 14**, because W46 already has three labs. Suggested order: factory and the first three labs nearest storage in each room, then the remaining new labs (the ones that complete the RCL7 set of 6).

### W46N8 (4 sites)

1. `STRUCTURE_FACTORY` **(35,30)**
2. `STRUCTURE_LAB` **(34,23)** — lab 4, closest new output to storage
3. `STRUCTURE_LAB` **(33,22)** — lab 5
4. `STRUCTURE_LAB` **(34,20)** — lab 6 (fills the RCL7 six; labs 1–3 already exist)

### W47N8 (7 sites)

1. `STRUCTURE_FACTORY` **(35,30)**
2. `STRUCTURE_LAB` **(29,38)** — lab 1, closest to storage
3. `STRUCTURE_LAB` **(28,37)** — lab 2, closest to terminal
4. `STRUCTURE_LAB` **(28,38)** — lab 3
5. `STRUCTURE_LAB` **(27,38)** — lab 4, input A
6. `STRUCTURE_LAB` **(27,39)** — lab 5, input B
7. `STRUCTURE_LAB` **(27,40)** — lab 6

No terminal sites. No RCL8 lab sites. No rampart sites. Nothing was submitted to the server.
