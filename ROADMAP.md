# Roadmap (priority order) — see docs/STRATEGY.md for phases

Novice zone ends **2026-10-28 03:33 UTC+8**. Defence timeline: `docs/DEFENSE_NOVICE.md` (2026-10-16); detail `docs/DEFENSE.md` / geometry `docs/DEFENSE_PLAN.md`.
**Safe mode: NEVER auto-activate** — alert Misaki.

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
