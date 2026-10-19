# Roadmap (priority order) — see docs/STRATEGY.md for phases

Novice zone ends **2026-10-28 03:33 UTC+8**. Defence timeline: `docs/DEFENSE_NOVICE.md` (2026-10-16); detail `docs/DEFENSE.md` / geometry `docs/DEFENSE_PLAN.md`.
**Safe mode: NEVER auto-activate** — alert Misaki.

## 2026-10-19 19:5x strategy review: W47N8 RCL5 transition (`docs/PLAN_W47N8.md` "RCL5 transition")

- **Tower 2 slot verified: 24,8** (Misaki 18:06) in layout.js ORDER.tower[0], PLAN_W47N8.md and tests/w47n8_tower_first.js; live since 108baf0 (18:09). The 17:55 note "34,31" is superseded.
- **Deployed 75f8265 (t83743900, dormant until RCL5):** 24,8 is fed from source A (2 tiles) instead of the hub filler (23 tiles, ~50 t away from the extensions): source-A miner skips link 26,12 while that tower < 600, overflow into 26,11, haulers score 26,11 x3 -> tower; filler serves only core towers (<= 8 of POST).
- RCL5 ETA **10-20 ~06:30-09:15 UTC+8** (274.7k left at 24-30 e/t, 4.2 s/t). Build order unchanged: tower 24,8 -> 10 ext (slots verified empty, strip roads built) -> links 13,25 + 26,12.
- 19:37 ctl stall: no hauler-priority change (spawn-first with empty storage, energy not lost, ~6 min ETA); the RCL5 link gives the ctl a non-divertible ~10 e/t. Watch line below unchanged.
- **W47N8 patrol at RCL5:** follow the 4-point checklist in PLAN_W47N8.md (24,8 only site; links after ext; 24,8 >= 600 within ~100 t via 26,11; filler stays home).

## 2026-10-19 20:27 two-room evaluation (45-min window 19:41-20:26 vs 18:56-19:41)

- Home W46N8: controller progress 22.4 e/t (prev 23.4; model 1h 22.6, 6h 20.9 vs ideal 21.8). Storage 16.1k -> 15.8k (flat, ~-0.5 e/t), dipped to 14.3k at 20:06 on queen/miner replacements and recovered. RCL6 439.0k/3.645M. Walls 142101 no loss, ramparts min 168.9k rising, 0 sites, no safe mode. Spawn utilisation 47%.
- W47N8: controller progress 26.0 e/t (prev 23.3; model 1h 25.4, 6h 19.5 vs ideal 29.85). Recovery continues now that all w8defenders expired. RCL4 144.7k/405k; RCL5 ETA ~11.7 h at the window rate (~10-20 08:00 UTC+8), ideal 10.2 h. Storage 1.6k -> 2.3k, ctl container 13,26 at 0 again (30 WORK drain faster than ~25 e/t sustainable; upgraders queue_blocked 21%, energy not lost). 10 ramparts, no new ones.
- Cross-room: CPU avg 13.6 (prev 13.5), single 55.2 at t83743900 = 75f8265 deploy global reset; bucket 10000. Memory 33.1k. DB lag 26 s. Tests all pass, src clean. 0 new game errors (errors.log tail is t83730121, old).
- **W47N8 upkeep gap explained (for the w8patrol, no change now):** live upkeep 11.2 e/t (excl. home-paid reserve7) vs model ~8.5 incl. upgraders. Extra ~2.7 e/t = wrhauler 4.17 vs 2.78 (60-75 CARRY vs 50 need; 15-CARRY granularity + replacement overlap), whauler 1.5 vs 1.04 (3x10 = 30 vs 20.7), wfiller 0.6 (model omits the filler), wbuilder 0.8 vs 0.67. Only lever is hauler size: if the next remote hauler can be 13 CARRY (4x13 = 52) and local 2x11 instead of 3x10, ~1.3 e/t returns to upgrading. Patrol decides at the next natural replacement; not worth a deploy before RCL5 (the link changes the haul routes anyway).
- Model note: `tools/model_w8.py` 1h window had coverage 0.66 and showed src A/B 7.0/7.5 e/t; live check t83744370 shows both miners 6 WORK on station and source A on pace (1596 left, ttr 183). Treat sub-0.7 coverage source rates as measurement noise.

## 2026-10-19 19:42 two-room evaluation (45-min window 18:56-19:41 vs 18:11-18:56)

- Home W46N8: controller progress 23.3 e/t (prev 23.4; model 1h 23.4, 6h 20.9 vs ideal 21.8). Storage 12.2k -> 16.2k (+6.4 e/t; prev -8.8 e/t): back above the 15k reserve since ~19:29, so a1d78b3 (rminers first across remotes) is verified. RCL6 425.1k/3.645M, RCL7 ETA ~10-26 afternoon at this rate. Walls 142101 no loss, ramparts min 168.3k, 0 sites, no safe mode.
- W47N8: controller progress 24.0 e/t (prev 19.5; live ~30 after 19:37, model 1h 20.8, 6h 17.4 vs ideal 29.8). RCL4 128.4k/405k, RCL5 ETA ~13.5 h at the window rate (model 15.6 h 1h / 18.6 h 6h, ideal 10.9 h). Threat-mode defenders 6 -> 2 and expiring with none added (ead1e7f withdraw rule working). 0 sites, rampart count 10, no new ramparts, no safe mode.
- CPU avg 13.5 (prev 13.1), one 22.5 tick at 19:15 (t83743400, no deploy; coincides with the large q.py query that timed out), bucket 10000. Memory 33.8k (prev 34.7k). Tests: scripts/test_all.sh all pass. src clean. DB lag < 30 s.
- **W47N8 patrol, watch:** at 19:37 the ctl container 13,26 ran dry for ~80 t during a replacement spawn burst while storage was < 100 (upgraders 4 = 40 WORK during overlap vs upw 30). With defenders gone storage should build; if the container empties again once storage is > 3k, look at whauler priority between extensions and 13,26 before anything else.
- **Home patrol, watch:** hauler 54 CARRY live vs 24.6 needed, idle/waiting 95%; cheap (0.7 e/t) but when it is next replaced, check the body is sized from the model need.

## 2026-10-19 18:58 two-room evaluation (45-min window 18:11-18:56 vs 17:26-18:11)

- Home W46N8: controller progress 23.4 e/t (prev 12.8; model 1h 22.5 vs ideal 21.8), but storage 18.9k -> 12.5k (1h delta -5.0 e/t), below the 15k reserve again since ~18:47: spawn burst (W45N8 + W45N7 rminer/reserver/rhaulers ~6k) plus W45N7 unmined ~160 t per cycle. Patrol fix a1d78b3 (rminers of all remotes first) live 18:51. Walls 142101 no loss, gates 167.5k rising, sites 0, safe mode untouched.
- W47N8: controller progress 19.5 e/t (prev 13.5; model 1h 18.5 vs ideal 29.7), RCL4 113.6k/405k, RCL5 ETA 18.5 h (1h rate) / 22.3 h (6h) vs 11.6 h ideal. The gap is still the 6 threat-mode w8defenders (6.2 e/t upkeep) while BustJetter stays north; ead1e7f cleared-threat path has not triggered yet because the threat never cleared. 0 sites, no new ramparts.
- CPU avg 13.1 (prev 14.8), max 15.7 (prev 63.0 deploy spike), bucket >= 9973; Memory 34.7k; top creep CPU = rhaulers in both rooms (wrhauler, rhauler), then whauler, queen. DB lag < 1 min, listener healthy.
- Code health: tests/conquest.js and tests/quad.js had been failing on stale body costs (worker/hauler 1000 vs live 1600 since Misaki's 15:25 "faster" change); asserts updated. New `scripts/test_all.sh` runs every test — use it for the "tests pass" check instead of a subset.
- **Home patrol, verify a1d78b3 by ~19:40:** the next W45N7 rminer replacement must finish spawning before its predecessor dies; storage should climb back above 15k once the burst ends. If storage is still < 15k at 19:40 with no spawn burst, look at remote delivery (model remote net ~11.4 e/t vs measured) before anything else.
- **W47N8 patrol:** keep watching; defender upkeep is by design while the threat stands. Once north_watch clears, confirm no replacements and the ctl feed back to >= 25 e/t within 2 patrols.

## 2026-10-19 18:4x strategy review (home RCL7 readiness, `docs/RCL7.md`)

- Home RCL7 ETA **~10-26 afternoon to 10-27 evening** (401k/3.645M at 20-24 e/t), 0.5-1.5 d before novice end 10-28 03:33.
- As planned, RCL7 cost 305k, of which factory 100k + labs 4-6 150k had no code to use them. Shipped `plan.RCL7_INDUSTRY=false` (RCL7 = spawn 2 + tower 3 + 10 ext + link, ~55k) and kept the home hauler at RCL7 (it was set to 0 at 4 links, which would have stopped the mineral run). Dormant until RCL7; `tests/rcl7_gate.js`.
- **Patrol at RCL7:** no duplicate same-role spawns from two spawns; refill time at cap 5600; first sites = spawn 30,34 / tower 39,23.
- **For Misaki (before ~10-26):** keep factory/labs off until code exists (recommended); link 4 at 32,34 is idle without stationary fillers.

## 2026-10-19 18:10 two-room evaluation (45-min window 17:21-18:06 vs 16:36-17:21)

- Home W46N8: upgrade 12.4 e/t (prev 22.4), storage +4.6k (prev -3.9k) = energy rerouted to storage by the 15k reserve hold after joint-defence spent ~4.4k on 2 home w8defenders; recovered by 18:06 (storage 17.4k, 2 upgraders). Walls 142101 no loss, gates rising.
- W47N8: upgrade 16.1 e/t (prev 13.4), still ~half of ideal 29.6; ctl container 13,26 repeatedly empty because 6 threat-mode defenders (spawn + 6.2 e/t upkeep) drained every store. RCL4 100.5k/405k.
- CPU avg 14.1 (prev 12.4), one 44.9 spike at the 17:41 joint-defence deploy, bucket >= 9958. Deploy churn: 21 deploys in 70 min, two tagged +dirty carried other agents' uncommitted edits; deploy.py now lists dirty files in the deploys note.
- **W47N8 patrol, verify after ead1e7f (18:08):** no new w8defender once the north squad is gone (cleared after 60 t); a w8healer only while threat is active and the roster is >= 4 combat; then ctl container refills and live upgrade climbs back to >= 25 e/t within ~2 patrols, else investigate hauler routing to 13,26.
- **Home patrol, watch:** the reserve hold (T.upgrader=0 under 15k) fires after every spawn cohort and every joint-defence send because the ferry floor sits only ~1k above the reserve. Energy is deferred, not lost. If it holds > 30 min twice more today, propose to Misaki: keep 1 upgrader while ctl container >= 1500 (that energy is already parked at the controller), or a lower reserve during peacetime.
- **Proposal (parent/Misaki):** deploy.py refuses +dirty src unless `--allow-dirty`; not switched on mid-incident because it could block an urgent defence deploy.

## 2026-10-19 strategy review (CPU budget, `docs/CPU.md`)

- 24 h: W47N8 RCL2→3 (10-18 22:00) →4 (10-19 ~10:00), now 48.6k/405k at ~10 e/t → **RCL5 (tower 2) ETA ~10-21 07:00**. Its 3 SM charges are unused (the 10-18 autoSafe question is moot).
- Home RCL6 337k/3.645M at ~18.8 e/t (4 h) → **RCL7 ETA ~10-28**, i.e. around novice end. Storage pinned at the 15k floor; gates min 163.7k, walls 142.1k (flat, no step 2 progress while energy goes to upgrade).
- CPU 6.5–8.8 → 11.7–14.2 avg since the claim (limit 20, bucket full). Creeps are 76% at ≈0.27/creep, close to the 0.2 intent floor: savings now come from fewer/bigger creeps and links. **A 3rd room needs CPU work first.** Shipped fbe8a00 (home spawn idle re-check every 4 ticks, ≈ −0.6 ms).
- Threat: BustJetter staged 4 armed unboosted creeps in W48N9 (10-19 14:26). W47N8 has threat mode + core ramparts (parent, 14:14–14:30).
- Option for Misaki (not urgent): generate pixels from the full bucket (1 per ~1.5 h, empties the combat reserve). Default **off**.

## 2026-10-18 strategy review (W47N8 hold, `docs/W47N8_HOLD.md`)

- Engine-verified: RCL2 gives W47N8 its first SM charge; enemy `attackController` between claim and SM = 1000 t upgradeBlock (no upgrade, no SM); one SM at a time across our rooms; no cooldown while novice.
- **Decision for Misaki:** SM policy for W47N8 — A one-shot auto at RCL2 (recommended) / B auto-chain (home SM locked) / C manual. `cq.autoSafe` currently unset.
- Next after SM1: W47N8 spawn → RCL3 (45k) → tower → ramparts inside the 23 h window; resume home upgrade when the W47N8 spawn is built; keep storage ≥ 20k.
- Home wall step 1 ✅ (51 barriers ≥131k). Step 2 (300k) after the op.

## 2026-10-17 strategy review (neighbours, `docs/NEIGHBORS.md`)

- W48N9 army 4–15 combat creeps all 48 h (median 6), towers unfed, nothing ever staged in W47N8/W47N7 → **watch, not escalation**. `neighbor_scan.py` prints a `trend` line; page on `trend NEW`.
- W48N8 = Evans_702 RCL6 (no exit into W47N8); spawns defenders nonstop — BustJetter's army may be busy there (hypothesis).
- **RCL6 ETA today ~18:40–19:20** (98.6k left at 24–28/t). Gates verified (`rcl6_gate`, `walls_bank` pass). Order after RCL6: core sites (~35k) → bank 20k → walls step 1. W47N8 conquest (~11.5k) only on Misaki's start; it competes with the bank for the same energy.

## Priority now (2026-10-16 strategy review: defence before novice end, `docs/DEFENSE_NOVICE.md`)

- RCL5 ~631k/1.215M (~52%); upgrade ~21–23/t. **RCL6 ETA 10-17 ~21:00 – 10-18 morning.**
- ✅ Wall v4 coded + dormant (44da00e bank latch + 9233cfc barriers). Critical path = **RCL6 → bank storage 20k → build**. Step 1 (100k) ≈43k energy; target finish **before 10-28**. Step 2 (300k) may finish after.
- ✅ Towers ×2, focus-fire / anti-drain, civilian flee, remote Invader defender **ON**. Home guards + early walls **paused** (fccf46c) — Misaki: upgrade-first while BustJetter force is small.
- ✅ `plan.RCL6_MINERALS=false` (source-A link + 10 ext only at RCL6).
- ⏳ **Next:** RCL6 night watchpoints (miner A→link, queen new ext, hauler idle). Then banking hold → wall latch. Deadline review **2026-10-25**.
- ⏸ Terminal/extractor/labs, W45N7 build, 2nd room, unpause guards/earlyWalls: **Misaki decisions** — see DEFENSE_NOVICE.md §E. Prefer after walls step 1 / after 10-28.

## 2026-10-14 strategy review priorities

Focus (Misaki 10-14): **W46N8 upgrade speed**; expansion (2nd account W47N8, W45N7 remote, W45N8 road paving) shelved until after RCL5 + defence assessment.

1. ✅ RCL4 (10-13 17:01): storage 37,31, 20 ext, CLAIM2, 16 ramparts ≥ 50k, remote W45N8 live (~7.5 e/t delivered 24h, 175k total).
2. ✅ Upgrade economy near model ideal: 2–3 × 12W, queen storage→ctl ferry, pre-spawn upgrader/hauler/queen; ~20/t (2h), 24/t when ctl fed (ideal 23.5).
3. ✅ **RCL5** (10-14 ~21:30) — see `docs/RCL5.md`.
   - ✅ Shipped: `plan.STATIONARY_FILL=false` (queen regime continues; no link sites), build order tower→extension, rampart growth throttle.
   - Patrol watchpoints in RCL5.md (tower 37,33 first; queen serves stamp B + tower 2; storage ≥ 1300 despite rampart growth).
4. ✅ **Link plan A approved by Misaki (10-14)** and coded in 55b6242 (`plan.LINK_PLAN`: hub 37,29 + ctl 30,31 at RCL5, source A 30,11 at RCL6; queen until RCL7). Deployed 15:21; dormant until RCL5 — patrol verifies link sites + transfers after RCL5.
5. ⏳ **Defence before novice end (deadline review 2026-10-25):** see `docs/DEFENSE_NOVICE.md`. Tower 2 ✅; outer walls designed+coded (dormant); SM tree still Misaki. Threat: BustJetter scouts 0 dmg + W48N9 combat pack (watch).
6. ⏸ After RCL5 + defence review: re-open expansion proposals (`docs/REMOTE_EVAL.md`) — **approval required**.
7. Later: RCL6 terminal/extractor/labs; 2nd room (**approval required**).

## Log
- 2026-10-19 19:5x strategy review: topic **W47N8 RCL5 transition** (`docs/PLAN_W47N8.md`). Tower 2 = 24,8 verified in code/test/doc/live; deployed 75f8265 (north tower fed from source A 26,11, filler core towers only; dormant until RCL5); link timing and hauler priority unchanged (reasoned); RCL5 ETA 10-20 ~06:30-09:15.
- 2026-10-19 18:4x strategy review: topic **home RCL7 readiness** (`docs/RCL7.md`). 250k of the 305k RCL7 bill was idle (factory + 3 labs, no code); gated by plan.RCL7_INDUSTRY=false; home hauler kept at RCL7 for the mineral run. RCL7 ETA ~10-26/27, W47N8 RCL5 ETA ~10-20 evening (live ~16 e/t, 104.6k/405k).
- 2026-10-19 17:5x strategy review: topic **W47N8 2nd-tower timing** (`docs/DEFENSE_W47N8.md`). Sim: 2 towers alone beat the full BustJetter squad; the RCL5 build order put tower 2 behind 10 extensions (~2-3 h). Deployed c7357bc tower-first (+ test). RCL5 ETA 10-20 05:45 (ideal) – 09:00 (live 23 e/t); home RCL7 ETA ~10-26 (390.8k/3.645M at ~22 e/t), before novice end. UH boosts seen in W48N9/W47N9 labs only speed the enemy melee on walls.
- 2026-10-19 14:40 strategy review: topic **CPU budget for two rooms** (`docs/CPU.md`). Live prof: total 12.0, creeps 9.1, home spawn 0.91 (run1 ≈2.4 ms, idle 36% of ticks), w8spawn 0.49, mem 0.34. Deployed fbe8a00 spawn idle throttle. RCL7 ETA ~10-28, W47N8 RCL5 ETA ~10-21.
- 2026-10-18 14:40 strategy review: topic **W47N8 after the claim** (engine source: claim/upgrade/attackController/safe mode). 24h: RCL6 at 10-17 ~19:00; walls step 1 done (all ≥131k); storage peak 57.8k (06:00) → walls → 15.8k (11:00) → 39k banked for the op; CPU 6.6–8.7, bucket ~10k; LOW scouts only. Docs only, no deploy (op code edited live).
- 2026-10-17 14:40 strategy review: topic **neighbour strength** (`docs/NEIGHBORS.md`). W48N9 count is noise inside its 48h band; added trend line + W48N8/W47N8/W47N7 to neighbor_scan; RCL6 ETA 18:40–19:20.
- 2026-10-16 14:34 strategy review: topic **defence readiness before novice end** (~11.5 d). Wrote `docs/DEFENSE_NOVICE.md`; refreshed STRATEGY current-state; ROADMAP priority → RCL6→bank→wall step 1 before 10-28, upgrade-first, expansion/minerals parked. 24h: RCL5 361k→631k (~+270k / ~15.5 h DB window ≈20/t avg; recent ctl_ema ~21–23/t); CPU ~4.0–4.5 bucket 10k nerr0; remote SAFE delivered ~506k defender ON; storage max ~2.4k (bank still the gate); walls coded dormant; early walls/guards paused; LOW BustJetter/Fandalah scouts; BustJetter W48N9 ~8 combat (thinned). No code this run.
- 2026-10-15 14:40 strategy review: topic RCL6 readiness. 24h: RCL5 at ~21:30 10-14; build/fix night 22:00–06:00 at 4–10/t, since 06:00 17–23/t; CPU 3.6–4.3, bucket 10000; 1 HIGH (defender death 04:30, kite fix), BustJetter scouts only. Found RCL6 would sink ~260k into idle terminal/labs and the wall start condition is unreachable (storage max 2.3k). Shipped RCL6_MINERALS gate.
- 2026-10-14 14:45 strategy review: topic RCL5 transition (RCL5 ETA tonight). Found the as-built RCL5 role switch would drop the queen (only storage→ctl carrier) once 2 links exist → upgrade ~10/t instead of ~20–24; stamp B / tower 2 unserved; tower 2 queued behind 10 extensions; 2 towers would pour ~10.6k into ramparts at 20 e/t. Shipped gate + build order + throttle (tests/rcl5_gate.js); link plan proposal → Misaki.
- 2026-10-13 16:13 patrol: remote container 13,11 decayed during the Invader pause (30k repair cap = 600t) -> R income 0 since resume; 99e654b: rminer keeps container >=100k, rebuild 7.1/t. Paused-creep home work deferred (home energy-bound).

## 2026-10-13 14:40 strategy review (first run)
- Topic: defence readiness before novice end. Wrote `docs/DEFENSE.md`; refreshed `docs/STRATEGY.md` (removed wrong safe-mode auto-trigger).
- 24h: RCL2→RCL3, v2 live, remote +27k then Invader pause; upgrade ~16–19/t last hour vs ideal ~23.6 (remote paused); CPU ~4; nerr 0.
- Code: tower repair reserve 800, queen tower top-up 900, alerts include safeMode fields, remote Invader-only pause uses TTL+80.
- **Not implemented (proposal):** remote Invader defender — wait until RCL4+CLAIM2 stable; Misaki approval to fight NPCs.
- Safe mode spawn buffer ending ~15:00; 2 available. Patrol next_at 15:15 unchanged.

## 2026-10-13: Layout v2 live
- ✅ v2 layout manager (plan JSON → sites per RCL, safe conflict removal), fixed-position roles (miner spots, queen stops,
  upgrader spots), cached paths (`utils/move.js`), per-RCL role table (`managers/spawn.js`), link manager (RCL5+),
  tower repairs only planned structures. Multi-tick simulator `scripts/sim.js` runs in every check.
- ✅ RCL3 extensions: 10/10 all on v2 tiles (11:35: 33,24–33,28, 34,24/26/28, 35,25, 36,31); v1 swap done. 35,27 waits for RCL4 (36,31 is an RCL4 plan ext used early). Earlier notes: 2026-10-13 09:56: 5 v2 built → gradual swap started (c4680d1: one v1 ext destroyed per 50 cap above 650, so the CLAIM1 reserver stays spawnable). v1 36,25 + 38,29 gone; 38,27 + 34,31 go as v2 sites finish; 36,31 kept (RCL4 plan ext), so 35,27 waits for RCL4.
- ⏳ RCL4 (ETA ~18:00–21:00 10-13 at 7–10/t during the build phase): storage (37,31); miner B delivers straight into storage; hub extensions.
- ⏳ RCL5: filler A link + hub link → stationary fillers + manager replace the queen; tower 2.
- Tuning: CPU is ~4 (vs ~3.6 before) while the 5 old haulers age out to the target of 2–3.
- 2026-10-13 14:10 patrol: Invader (ATTACK+RANGED) in W45N8 → remote paused until ~tick 83614741; reservation will likely expire before unpause (no fight — wait). Queen fix f5dde98 holding (rp/100≈6.9, cpu≈0.29). Upgrade ~16.5/t (1h). Deployed 31d71ef: RCL3 swamp roads 41,22/42,21/43,20 + remote road 2,12; builder dismantles empty unplanned container 31,11.
- 2026-10-13 13:06 patrol: queen walked to far source 31,12 because filler container A (35,24) was never fed → f5dde98: queen refills storage > fc > nearest source; haulers feed fc first (<400) and stay off queen stops while a queen lives (fill route only <30% energy).
- 2026-10-13 11:35 patrol: audit found haulers ping-ponging between source containers mid-trip (rp/100 ≈ 14) → fixed pickup per hauler (deterministic round-robin, far source first, wait until full, 60-tick fallback); move: straight last step, wait behind stationary creep on range-0 goal, repath reason codes (rp_why); skip spawning creeps; listener seg90 dedup (DB had ~14× duplicate creep_cpu rows, cleaned).
- 2026-10-13 10:40 patrol: CLAIM1 reservation buffer stuck ~13 (net 0) → spawn 2nd reserver when ticksToEnd<800 to rebuild; resLead 150; haulers leave 10% spawn headroom for ctl container.

- [x] 2026-10-13 Continuous creep telemetry (ts.sqlite, segment 90 ring buffer, creep_audit.py windows/regressions/heatmaps) + simplified movement with fallback ladder.
- [ ] Use audit findings each patrol: fix worst creeps/roles; consider shared per-route path cache if repaths/100 stays high.
- [x] 2026-10-13 TimescaleDB + Grafana data platform (docs/DATA.md); JSON metrics migrated.
