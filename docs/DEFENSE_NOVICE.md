# Defence timeline before novice end

Strategy review **2026-10-16 ~14:34 UTC+8**. Geometry and wall budget live in `docs/DEFENSE_PLAN.md`; home/remote combat code in `docs/DEFENSE.md` / `docs/DEFENDER.md`. This page is the **schedule only**.

**Novice zone ends: 2026-10-28 03:33 UTC+8** (~11.5 days from this review).  
**Safe mode: NEVER auto-activate** — alert Misaki and wait.

## Snapshot at review (verify on patrol)

| | |
|---|---|
| Home | W46N8 RCL5 **~631k / 1.215M** (~52%), ctl_ema ~1.1–1.2k ≈ **~21–23 e/t**, storage **~2.0–2.4k** (48h max still ~2.4k) |
| RCL6 ETA | **~2026-10-17 21:00 – 10-18 morning** (~31 h at 21.6/t, 4.12 s/tick) |
| Towers | 2 live (36,29 + 37,33), energy ~970 each; focus-fire + anti-drain ON |
| Core ramparts | Spawn / both towers / storage **≥100k**; filler stand-tiles intentionally decaying (~8–10k) while `STATIONARY_FILL=false` |
| Outer walls | **0** built; v4 phase coded (`managers/walls.js`) dormant until RCL6 + bank 20k (or post-novice player combat) |
| Remote W45N8 | SAFE, `remoteDefender` **ON**, cont hits 100k, delivered **~506k**, reservation ~1.9k, claim2 |
| CPU | ~4.0–4.5 avg, bucket 10000, nerr 0 |
| Safe mode | **4 available**, none active |
| Neighbours | BustJetter (Council) W48N9 ~8 combat (≈26 ATTACK + ≈26 RA + ≈16 HEAL parts, unboosted mix) — thinned from 13 at midday; W47N9 economy only (no claimer visible now). Fandalah W44N8 RCL6, no combat creeps. RCL8 rooms N/S of us still outside our novice exits. |

## 2026-10-19 20:5x refresh: what actually opens at 10-28 03:33 (live API, tick ~83744650)

The 10-16 plan assumed the RCL8 rooms north and south of home (W46N9 drtk712, W46N7 FungousCoast245) are the post-novice risk.
Terrain says otherwise: **W46N8 has 0 exit tiles north and south**, W47N8 has 0 to the west (W48N8), W47N7 has 0 to W48N7/W46N7,
W45N7 has 0 to W46N7, W45N8 has 0 to W45N9. Home is reachable only through W47N8 (west) and W45N8 (east).

Novice walls (constructedWall, `decayTime` 1793129589429 = 10-28 03:33) that drop near us, and who is behind them:

| Opening | Tiles | Behind it | Path to us |
|---|---|---|---|
| **W45N7 x=49** (our remote) | 44 | **W44N7 Cody132** RCL7 (GCL ~3), 2 towers full, 92 walls, 0 combat creeps now; beyond: Solstice W43N7/W43N6 RCL7 (GCL ~4) | straight into W45N7 -> W45N8 -> home east (22 tiles, outer ring 142k+) |
| **W44N8 y=49** (Fandalah) | 18 | W44N7 Cody132 | W44N8 -> W45N8 east edge (7 tiles) -> home |
| **W47N9 x=49** (BustJetter) | 20 | **W46N9 drtk712** RCL8 (GCL ~14.5), 6 towers, nuker, observer, 0 combat creeps now | W47N9 -> W47N8 north (23 tiles, 12 seal walls 50k) |
| W45N6 / W47N6 west sides | - | W46N6 = SK room with an Invader stronghold (lvl 5); FungousCoast245 (GCL ~70) only via SK rooms | W45N6 -> W45N7, W47N6 -> W47N7 (long way round) |

So after 10-28 the **remotes W45N7/W45N8 become the first rooms an outsider walks into**, and W47N8's north gets a second
possible visitor (drtk712) through BustJetter's room. Our existing posture fits: remotes flee + pause on player combat,
home outer ring (41 walls min 142.1k, 11 gates min 168.8k = step 1 done), W47N8 seal walls 50k + tower 2 at RCL5 (~10-20).
After 10-28 we are also inside drtk712's nuker range; nothing to do about that except not provoking him.

**Status vs section A:** items 1-6, 8, 9 live; item 7 (wall step 1, 100k) **done** (min 142.1k). Step 2 (300k, ~69k energy) is
not moving: the 50k wall fund is fully accrued but the `reserveE=15000` builder gate needs storage > 17k and storage sits at
15-17k (upgraders take the surplus), so 0 home builders. Step 2 therefore starts only if Misaki trades upgrade for it
(about 2.3 e/t = ~10% of upgrade, RCL7 slips ~0.8 day) or after RCL7. Recommendation: keep upgrade-first; RCL7 (3rd tower +
2nd spawn, ETA ~10-26 late) is worth more in a fight than +158k per wall.

**Gap fixed (b62f49f):** with a hostile *player* combat creep inside home, the reserveE gates also blocked any builder, so
nobody would repair an attacked wall while storage was under ~17k. `walls.siege(room)` now allows one builder that may
draw storage to 5k (tower cushion) - Misaki's doctrine "builders repair attacked walls" and "reserve floors may be spent for
defense". Dormant until a player attacks home. `tests/defense_reserve.js`.

**Watch:** `tools/neighbor_scan.py` now also scans W44N7 (Cody132), W46N9 (drtk712) and counts any player combat creep in
W45N7/W45N8 as NEW. The 10-25 deadline review stays; add "who came through the three openings in the first 24 h".

## A. Must be LIVE by 2026-10-28 03:33

These are the minimum that should already be working when the novice walls drop:

1. **Two towers + energy discipline** — combat reserve ≥800 / queen top-up ≥900. ✅ live.
2. **Tower smart targeting** — focus-fire, healer-first, net-damage hold, observed drain-pattern ban. ✅ live (Misaki rules 10-16).
3. **Civilian flee + queen tower priority** under home hostiles. ✅ live.
4. **Remote Invader defender ON** for W45N8 (NPC only; still flee players). ✅ live; keep default ON.
5. **Attack alerts** with `safeModeAvailable` / never-auto note. ✅ live.
6. **RCL6 core build done** — source-A link 30,11 + 10 extensions (~35k). Minerals/terminal/labs stay gated off (`plan.RCL6_MINERALS=false`).
7. **Wall phase latched and step 1 underway** — bank storage to **20k**, then place gates + trunks + 41 walls; barriers rising evenly toward **100k** (step 1 ≈43k energy incl. ~5.4k TR trunk). Prefer step 1 **finished** before 10-28; step 2 (300k) can finish after if bank is late (see C).
8. **Core critical ramparts held ≥100k** (spawn, towers, storage) — towers/builders already do this.
9. **Patrol / neighbor_scan / attack alerts** still paging on MEDIUM+; safe-mode decision waits for Misaki.

Not required as *creeps* by 10-28 unless Misaki unpauses: home guards, early threat-latch walls (`Memory.defense.guards` / `earlyWalls` stay default **off** per 10-16).

## B. Can wait until after 10-28

| Item | Why it can wait |
|---|---|
| Outer barrier step 2 → **300k** | Step 1 (100k) already stalls a small unboosted raid long enough for SM / Misaki; 300k is the next budget tranche |
| RCL7+ hits (1M / 3M) | Post-novice scaling |
| Terminal / extractor / labs / sell O | No market or mineral code; payback ≫ defence deadline (`docs/RCL6.md`) |
| W45N7 remote claim / roads | Analysis + full plan only until Misaki approves |
| 2nd room / GCL push | Approval required; slows upgrade + walls |
| Home player-guards standing army | Misaki paused; towers + walls + SM cover the small Council probes for now |
| Min-cut redesign | Final outer line already approved (DEFENSE_PLAN); Overmind-style bunker-only trim is an RCL7+ optional |
| Invader-core buster role | Spawn on sight; none seen |
| Stationary fillers / stand-tile rampart upkeep | Deferred until RCL7 link plan |

## C. Realistic schedule (tied to RCL6 + bank)

Assumptions: upgrade stays ~21–23 e/t until RCL6; model net ~23 e/t after; wall fund = 20k bank + 10% of net while storage &lt;50k; tick ≈4.12 s.

| When (UTC+8) | Milestone | Notes |
|---|---|---|
| **Now → 10-17 evening** | Push RCL6; no new luxury builds | Storage will stay ~1–2k (supply-follows-demand). Do **not** unpause early walls/guards unless Council force jumps. |
| **RCL6 + ~2 h** | Core sites done (ext + link 30,11) | Watch: miner A → link; queen serves new ext; home hauler idle → consider T.hauler 0 if idle &gt;70%. |
| **RCL6 + ~3 h** | **Bank latch** — hold upgrader extras until storage ≥20k | ~870 ticks ≈ **1 h** of upgrade deferred (not lost). Walls phase `bank` → `build`. |
| **+0.5–1 day** | Gates + TR/W/S trunks + wall sites placed; fund spends bank first | Sites ≤2 at a time; builder repairs +10k chunks. |
| **~10-19 … 10-21** | **Step 1 (100k) complete** if latch by ~10-18 | Remaining ~23k after bank dump @2.3 e/t ≈11 h wall work + placement overhead → comfortably before 10-28. |
| **10-22 … 10-25** | **Deadline review** (already on ROADMAP) | Confirm step 1 done / step 2 started; revisit guards & SM tree with Misaki; neighbor posture. |
| **10-25 … 10-28** | Hold step 1; start step 2 if fund allows; no expansion | If bank slipped: at minimum **gates up at 1 hit + towers full** before novice drop — then crash-repair under threat (cap lifted). |
| **After 10-28** | Step 2 (300k), minerals decision, W45N7 reopen | Outer walls buy time; SM is last resort (20k ticks, one room/shard). |

**Banking is the critical path.** Without the 20k latch, outer walls never place (coded correctly). Storage has never exceeded ~2.4k in this room — the RCL6 banking hold is mandatory, not optional.

### Tower math vs likely early raids (why step 1 is enough for day-1)

- 2 towers at hub range ≤5 → **1200 dmg/t** before tough; falloff to ~300 each at range 20.
- Unboosted HEAL parts: 12 heal/t adjacent. BustJetter’s current W48N9 stack (~16 HEAL) can out-heal 2 towers **if stacked on healers at the edge** — our anti-drain already holds fire on net≤0 / banned drain cycles.
- A small probe (2 RA + 1 HEAL, as seen in W47N8 earlier) dies to focus fire inside the hub; it does **not** justify pausing upgrade for standing guards.
- Post-novice, RCL8 neighbours can path in: walls delay; SM is the panic button Misaki holds.

## D. Gaps vs current code (small / safe)

| Gap | Severity | Action this review |
|---|---|---|
| Wall policy unreachable without bank | Was critical | ✅ coded 10-16 (`bank` phase). Verify at RCL6 latch. |
| `RCL6_MINERALS` luxury drain | Was critical | ✅ gated off. |
| Remote defender default | Was mis-set off briefly | ✅ restored ON. |
| Home guards / early walls | Intentional pause | Leave off; console flags ready. |
| Safe-mode **decision tree** (when Misaki would press it) | Process, not code | Proposal only — see E. |
| Core filler ramparts decaying | Accepted (11ce9f9) | No change; outer walls supersede. |
| Invader-core dismantle role | Low | Park until a core appears. |
| Observability: wall fund / novice countdown panel | Nice-to-have | Skipped this run (docs + ROADMAP enough). |

**No code shipped this review** — wall/tower/remote stacks from today already cover the pre-10-28 must-haves; churn would risk the RCL6 night.

## E. Decisions for Misaki (proposals only — do not execute)

1. **Safe-mode tree** — draft: activate only if (a) spawn or both towers threatened and walls &lt;50k effective, or (b) boosted siege / healer ball that towers cannot net-damage and no free SM cooldown plan. Still **her button**; bots only alert.
2. **Unpause `earlyWalls` / `guards`** — only if Council stages a real squad on our border again (≫ today’s thinned W48N9 pack) *and* she accepts a temporary upgrade dip.
3. **Minerals / terminal / labs** — keep off until walls step 2 **and** she wants to sell O (credit *spending* always her call). Recommend after 10-28.
4. **W45N7 remote** — stay analysis/plan-only until she approves a full build order (ramp-up, spawn capacity, roads later).
5. **Upgrade-first until walls latch** — confirmed preference: do not divert to expansion or standing home army before bank→build.

## Neighbour posture (10-16 afternoon)

- **BustJetter / Council**: scouts through W46N8 continue (LOW, 0 dmg). Combat mass concentrated in **W48N9** (not next door); W47N8 claim/reserve empty of combat at last scan. Treat as watch, not panic.
- **Fandalah**: RCL6 east of remote; no combat creeps visible — remote defender stays NPC-only.
- **Post-10-28**: RCL8 rooms on N/S edges become relevant only via east/west exits; outer W/S walls (x=6 / y=44+) are the planned choke.

## Checklist (rolls forward from DEFENSE.md)

- [x] Tower 2 + energy discipline + smart targeting
- [x] Alerts include safeMode fields; never auto SM
- [x] Remote Invader defender ON
- [x] Outer wall geometry + v4 policy coded (dormant)
- [x] RCL6 core + bank + wall step 1 (100k) before 10-28 (min 142.1k on 10-19)
- [ ] 10-25 defence deadline review with Misaki (SM tree, guards, minerals, W45N7)
- [ ] Wall step 2 (300k) — may finish after 10-28
