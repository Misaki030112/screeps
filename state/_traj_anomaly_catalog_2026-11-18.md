# Trajectory anomaly catalog — 2026-11-18

Analysis only. No game-code change, no PR, no deploy, no Memory writes.
Live shard SHA: `8daf0494` (occupied-hub bypass, deploy tick 84324673). GitHub `origin/master` is docs-only on top of game `c6d43491` (PR 61 yieldPost) and is **not** live.

Times are Asia/Hong_Kong (UTC+8) unless a timestamp already carries a zone.

---

## Parent-facing summary

Stored history covers `creep_ticks` from **2026-10-13 10:04** through **2026-11-18 11:15** (about 10.2 million rows, ticks 83609908–84333615, 12,874 creep names, 36 roles). `creep_cpu` and `path_arrivals` start the same day. Dense five-room coverage (W46N8, W47N8, W45N8, W45N7, W47N7) begins **2026-11-10 09:25** when W47N7 data starts. Older data is real but uneven: a multi-day hole around 2026-10-22–10-28, and sparse days 2026-11-06–11-09. W47N9 appears only as a short 2026-11-05 raid.

This pass went deep on the last **72 hours** (2026-11-15 11:16–2026-11-18 11:15; 2.12M tick rows, 56,689 distinct ticks) and scanned recurring patterns back through the dense Nov 10 window (and exit/flee stalls back 8–10 days). `room_stats` in the same 72 hours has 270 freeze gaps (~48,890 missing room_stats ticks across the two owned rooms). Official history often still fills `creep_ticks`; a creep that “teleports” across a freeze or a 404 hole is not a movement bug.

Known official 404 holes already reported (data holes, not new bugs): W45N8@84328100, W45N7@84328300, W47N7@84330300, W47N7@84331000, W45N8@84332200, W47N8@84332600 and W47N8@84332700 (combined 84332601–84332783), W47N7@84332600, plus older leftovers. A **new box freeze after the 10:25 patrol**: 10:47:39–10:53:38 (~358 s, event tick 84333141).

Distinct patterns reviewed: about **16**, of which

- **4 shippable** logic/pathing/assignment bugs (plus one low-frequency jam worth fixing later),
- **2 already fixed**, and post-fix traces are clean for the intended walks,
- several **designed** behaviors that must not be “fixed” (keep=2, 15k floor, reserver thresholds, TTL-stay defenders, 1-tick road pass-bys, threat softCap / 封仓停工),
- several **infrastructure artifacts** (freezes, 404s, official-history ghosts, source-A link metering),
- **3 items that need more data** or have dropped out of recent traces (termPark under-fill, W47N7 “full containers / haulers not pulling”, W47N7 reserve bounce after 84317657).

Recommended shippable fix order (no locked-policy changes):

1. W47 filler `target_full` oscillation around post 34,32 (live, highest loss).
2. W45N7 rhauler dual-creep bounce at the container approach (recurring ~40-tick jams).
3. Remote miner stall on home/via exit tiles during pause/flee (clear `flee()` guard hole; 576 t as recently as last night).
4. W45N7 defender that sits in W45N8 and never enters when `inv=0` on arrive (three confirmed cases).
5. Optional later: rare W47 south-road 10–14 t multi-hauler head-on jams; milder home-queen “walk the route while full” sibling of (1).

Do **not** change the 15k floor, W47 keep=2 / 40k-500t latch, standing third upgrader, softCap unseal by policy fiat, market, factory, W47 labs, new remotes, C.SPAWN, or extension 32,34.

---

## Coverage

| Source | Rows | Min tick / time HKT | Max tick / time HKT |
|---|---:|---|---|
| creep_ticks | 10,207,128 | 83609908 / 2026-10-13 10:04 | 84333615 / 2026-11-18 11:15 |
| creep_cpu | 3,060,926 | 83609905 / 2026-10-13 10:04 | 84333600 / 2026-11-18 11:15 |
| path_arrivals | 75,652 | 83609919 / 2026-10-13 10:05 | 84333598 / 2026-11-18 11:15 |
| room_stats | 61,654 | 83594467 / 2026-10-12 17:20 | 84333610 / 2026-11-18 11:15 |

Per-room `creep_ticks` (all stored history):

| Room | Rows | Distinct ticks | First HKT | Last HKT (at query) |
|---|---:|---:|---|---|
| W46N8 | 3,845,249 | 375,269 | 2026-10-13 10:04 | 2026-11-18 11:09 |
| W47N8 | 4,194,997 | 274,667 | 2026-10-18 16:19 | 2026-11-18 11:15 |
| W45N8 | 1,007,325 | 221,699 | 2026-10-13 10:04 | 2026-11-18 10:59 |
| W45N7 | 536,111 | 166,390 | 2026-10-16 16:25 | 2026-11-18 10:59 |
| W47N7 | 621,760 | 149,907 | 2026-11-10 09:25 | 2026-11-18 10:59 |
| W47N9 | 2,294 | 691 | 2026-11-05 15:52 | 2026-11-05 17:30 |

Last 72 hours: creep_ticks 2,122,961 rows / 56,689 ticks; creep_cpu 388,439; path_arrivals 7,184; room_stats 6,568. Hourly five-room coverage is generally 650–860 ticks/hour; softer hours (450–600 in one remote) line up with evac, official holes, or freezes. The current 11:00 hour is still filling.

Method: role-by-role and room-by-room bounce-pair aggregation (consecutive ticks only, so freezes/404s are not counted as moves), bounce **episode length** (to separate 1-tick pass-bys from real jams), idle codes from `creep_cpu`, stand/store proxies, defender room occupancy, and pre/post-deploy slices at yieldPost (84321282) and yieldHub (84324673). A repeated tile bounce or a long stall was required; a single pause was not.

Deploys used as cut points: PR 61 `c6d43491` @ 84321282 (2026-11-17 19:02:43); live `8daf0494` @ 84324673 (2026-11-17 23:30:52); 16C8M home hauler `3cf63791` @ 84302295 (2026-11-16 17:59:14).

---

## Designed / not bugs

These look noisy in audit output and must not be treated as anomalies to ship.

- **W47 keep=2 seated ~20 e/t is only 66.5% of the 30.08 ceiling.** This is why formal W47 upgrade alerts fire. Do not add a standing third upgrader; do not raise keep until 40k storage actually locks 500 ticks.
- **Home 15k floor** cutting to 1 upgrader (14 e/t) until 17.55k. Do not change `reserveE`.
- **Reservers** not spawning while reservation stays above 2500 (W47N7) / 2000 (other remotes).
- **Defenders / guards staying for full TTL** after the fight (Nov 11 decision). Today’s rdef84331123 remaining in W47N7 until ~10:10 is this.
- **w8up=3 only during handoff overlap**, not a policy third.
- **Threat-window softCap and 封仓停工** after an NPC/hostile event, including the residual window after the 08:16 W47N7 evac. SoftCap unseal vs keep=2 until the 40k latch is a **policy/design tension**, not a motion bug to “fix” by changing softCap.
- **1-tick A-B-A on 1-wide roads** (W47 13,29↔14,30, 14,30↔15,31, 15,31↔15,32, and almost all 28,35↔29,35). Episode length avg 1.05–1.16, 90%+ of episodes are a single bounce. Pass-by swaps.
- **waiting_pickup** when the source/container really is empty or below the withdraw threshold; **waiting_feed** at the controller battery; **source_empty** on miners during regen; **no_task** on builders when sites are gone; **parked_threat** / **queue_blocked** on guards and post-fight rdefs.
- **Filler and queen sitting still with `target_full`** when duty is actually full — that idle code is correct. The bug is when they **keep moving and bouncing** with a full carry (see S1).
- **Occupied-hub replacements taking 34,32→34,33** after `8daf0494`. That is what yieldHub is for.
- **Fatigue pauses** on 10W1M/10W2M upgrader walks (same tile for several ticks on the south road) are not stuck.
- Home hauler (`hauler`) 72h codes: 45,028 / 54,715 ticks `waiting_pickup` (~82%). This is the single 16C8M mineral/lab/termPark hauler idle when there is no park/lab task and no drop to pick up, not a motion loop.

---

## Artifacts (freezes, 404s, ghosts)

- **Box freezes** leave `room_stats` gaps and can make a creep appear to jump. Last 72h includes many already folded into patrols (09:47–10:02, 08:39–09:04, 09:16–09:24, 06:37–07:05, etc.). **New after the 10:25 patrol:** 10:47:39–10:53:38 (~358 s).
- **Official 404 holes** listed above. W47N8 84332601–84332783 is why one handoff’s predecessor vanished inside a hole. Empty remote ticks with official HTTP 200 and no friendly creeps are evac / not-yet-entered / brief absence, not missing chunks.
- **Official-history ghosts** (an expired upgrader still appearing at 12,25 after death) remain a known ingest artifact, not a third upgrader. Coverage holes of 52–201 ticks on upgrade stands in the last 72h match freeze/404 widths, not a live extra creep.
- **Audit exit 2 vs live `8daf0494`** is a baseline-compare artifact used by patrols, not a regression by itself.
- **W47 source A harvest tally at link 26,12** (item 6 below): metering, not motion.

---

## Already fixed — post-fix status

### F1. W47 spawn-pocket / yieldPost (PR 61, `c6d43491`, tick 84321282)

**What it was:** Replacements shuffled with the filler on post 34,32 instead of taking the 32,32 south-road bypass.

**Post-fix:** First 150 ticks after leaving spawn, role counts of “touched 34,32”:

| Era | wupgrader touched post | wrhauler | whauler | wminer |
|---|---|---|---|---|
| Pre-yieldPost (sample in 84318000–84321282) | 1/7 | 13/18 | 3/8 | 1/6 |
| Post-yieldPost, pre-yieldHub | **0/4** | **0/13** | **0/6** | **0/5** |
| Post-yieldHub (see F2) | 2/13 (occupied-hub path, designed) | **0/27** | 2/19 (1 tick each) | 1/12 |

Clear-hub replacement walks stay off the post. Filler itself sitting on 34,32 is designed (12/12 post-hub fillers touched the post, hundreds of ticks).

**Verdict: already fixed.** Clear-hub traces are clean.

### F2. Occupied-hub cul-de-sac 32,32↔33,31 (`8daf0494`, tick 84324673)

**What it was:** When hub container 33,33 was occupied, a 1-MOVE replacement bounced in the 32,32 pocket.

**Post-fix:** Exact pair `32,32↔33,31` is essentially gone: 3 one-tick touches after 84324673 (one each wfiller/wbuilder/whauler), no multi-tick episodes. Pre-yieldHub the same pair was already rare except a 3-tick whauler blip; the dangerous pattern was the pocket bounce, which yieldHub was aimed at.

Occupied-hub walk **w8upgrader84329740** (born 84329795, ~00:00 11-18): `34,32→34,33→33,34→32,35` then the south road to seat 14,26. Matches live observations (clear hub 32,32→33,33→33,34; occupied hub 34,32→34,33). **No new failure mode after the fix.** w8upgrader84330641 also stepped 34,32 then 33,31; repeated tiles are fatigue, and a mid-walk jump to 28,35 / 14,27 lines up with a coverage hole, not a teleport bug.

**Verdict: already fixed.** Later walks stay clean for the intended cases.

Historical border bounce **W47N8 18,49↔W47N7 18,0** (rdef84218203, 171 t, 2026-11-12 11:05, already documented in `remote.js`; wrhauler max 139 t on 2026-11-11) is **sharply reduced** after 2026-11-14 (Nov 16–18: max episode 1–5 ticks). Treat as already improved / not a current systematic bug. The rmove/step-off-exit fix in `fleeHome` is the matching code comment.

---

## Shippable anomalies

### S1. W47 filler oscillates around post 34,32 while carry is full and duty is `target_full`

- **Rooms / roles:** W47N8, `wfiller`.
- **What:** With a full 1200 carry and no useful fill target, the filler does not park on POST 34,32. It bounces between the post and its neighbors for ~7–11 ticks at a time, then repeats, for hours.
- **Evidence (last 72h, consecutive-tick bounces only):**

  | Pair | Bounce ticks | Episodes | Share of episodes length 10–29 | Avg / max length | Longest example |
  |---|---:|---:|---:|---|---|
  | 34,32↔35,31 (post–storage diagonal) | 9,100 | 1,224 | 762 | 7.43 / 11 | w8filler84285601 @ 84285838 ×11 |
  | 33,31↔34,32 (pocket–post) | 6,782 | 1,207 | 505 | 5.62 / 12 | w8filler84317755 @ 84318523 ×12 |
  | 33,33↔34,32 (hub–post) | 4,722 | 588 | 398 | 8.03 / 11 | w8filler84326865 @ 84328071 ×11 |
  | 34,32↔34,33 | 3,661 | 548 | 249 | 6.68 / 11 | w8filler84303516 @ 84304616 ×11 |

  Last 6 hours: those four pairs still dominate, and **every bounce has store=1200**. Last 24h `creep_cpu` for wfiller: 14,199 / 38,121 ticks `target_full` (37%), 17,805 moving (47%), only 3,541 working (9%), 2,695 repaths, 544 stuck events, 27 creeps. Last 6h still 3,410 `target_full`, 4,446 moving, 691 repaths, 127 stuck. Motion audit 2h (patrol 10:18) had w8filler84331242 at 367 ABA + 197 circle + 455 `target_full`.
- **How often / how recent:** Continuous across the 72h window (t0 84276929 – t1 84333615) and still live this morning. ~24k bounce ticks in 72h on the four post pairs alone (~330 bounce-ticks/hour).
- **Root cause:** `src/rooms/w47n8/fill.js` idle path: when duty is empty it still `go(c, POST)` and, when already off the post, keeps issuing `moveTo` / repath. Combined with storage (35,32) and hub (33,33) being adjacent to the post, a full filler retries those tiles, gets `target_full`, walks back to 34,32, and repeats. Trace correctly marks `f`, but the creep does not stand still. This also knocks the filler off the post that yieldPost is trying to keep clear for replacements.
- **Loss:** CPU (repaths + move), blocked post, zero energy moved during the bounce (carry already 1200). Not an energy-throughput hole while extensions are truly full, but it is wasted intent and it fights the spawn-pocket fix.
- **Verdict: shippable logic/pathing bug.** Fix should be: if duty is empty / all targets full, stand on POST and stop repathing (keep the `f` code). Do not “fix” this by loosening fill rules or unsealing softCap.

**Sibling, lower priority — home queen walks the route while `target_full`:** 72h queen codes 55,850 / 111,164 ticks `target_full` (50%), 40,374 moving, 11,143 repaths. Bounce episodes on 34,27↔35,26 are almost all length 1 (designed route steps). 24h: 18,840 `target_full`, 13,279 moving, 3,431 repaths, only 3,012 working. Same class (“don’t keep walking when duty is full”), much less tile-bounce damage than the W47 filler. Park when the route is fully topped.

### S2. W45N7 rhauler dual-creep bounce at the container approach (20,13↔21,14 / 19,13↔20,14)

- **Rooms / roles:** W45N7, `rhauler`. Container is 21,15 (tight neighborhood: ~3 free neighbors; 22,15 is the foreign container and is avoided).
- **What:** Two empty (or nearly empty) rhaulers bounce on the approach tiles for ~26–45 ticks at the same time, over and over.
- **Evidence:** Last 72h episode stats: 20,13↔21,14 — 14 episodes, 10 of length ≥30, avg 34, max 44 (rhauler84308644 @ 84309517); 19,13↔20,14 — 27 episodes, 9 of length ≥30, avg 16.7, max 45 (rhauler84308134 @ 84309517, same tick). Over 8 days, paired long episodes recur almost every few hours, usually `store=0` or 12, two creeps starting the same tick, for example:

  - 2026-11-10 15:23 — 42+43 t
  - 2026-11-16 16:49 — 40+42 t (rhauler84300260 / 84300500)
  - 2026-11-17 03:40 — 45+44+41 t (**three** haulers, 84308134 / 84308644 / 84308884)
  - 2026-11-17 21:05 — 43+40 t (rhauler84321662 / 84322388) — last long pair in the 8-day list

  Shorter residual bounces on 19,13↔20,14 still reach t1 84333231 (this morning), so the traffic is not gone; only the ≥8-tick list ends last night.
- **How often / how recent:** ~2–4 long paired jams per day through 2026-11-17 21:05. Each costs ~80 creep-ticks of not withdrawing, and can leave the 21,15 container to fill.
- **Root cause:** Tight 3-neighbor container plus `yieldToMiner` / wait-stand logic in `src/roles/remote.js` (comments already describe this geometry). Two empty haulers compete for the same range-1 stands and bounce instead of one backing off to a legal wait tile (or staging in W45N8). Not explained by a freeze (consecutive ticks, store unchanged).
- **Verdict: shippable assignment/pathing bug.** Still present. Do not “fix” by adding haulers.

### S3. Remote miner stalls on home / via exit tiles during pause or outbound (flee guard hole)

- **Rooms / roles:** W46N8, W45N8, `rminer` (home remotes). Related W47N8/W47N7 `wrminer` stalls are shorter.
- **What:** A miner that should park inward at `C.park` (default 33,26) or continue into the remote instead stands on an exit tile for 100–576 ticks. The known-issue label said “home west exit”; stored traces are at the **home east gates** used by W45N8/W45N7 (W46N8 49,14 and 48,19) and the **W45N8 south via exit** 21,49. No long rminer stalls were found on W46N8 x=0 (true west exit).
- **Evidence (stalls ≥20 t on exit-ish tiles, last 8 days), selected:**

  | Creep | Tile | Stall ticks | When HKT | Note |
  |---|---|---:|---|---|
  | rminer84324635 | W46N8 49,14 | **292 + 282 = 576** | 2026-11-17 23:33–24:00 | Newly spawned (born 23:27 at 30,34), walked the east road, then sat on the exit; afterwards mined at W45N8 13,11 for 1,019 t |
  | rminer84264151 | W45N8 21,49 | 477 | 2026-11-14 19:50 | Via exit to W45N7 |
  | rminer84222594 | W46N8 48,19 | 378 + 102 | 2026-11-12 18:06 / 17:50 | W45N7 home-gate approach |
  | rminer84282436 | W45N8 2,23 | 290 + 179 | 2026-11-15 18:10 / 17:55 | Near home west-of-remote entrance |
  | rminer84252947 | W46N8 49,14 | 170+101+100 | 2026-11-14 05:55–06:24 | Same east gate |
  | w8rminer84288627 | W47N8 18,49 | 300 | 2026-11-16 01:07 | W47N7 gate (shorter class, fleeHome already has an exit-step fix) |

- **How often / how recent:** Multiple 100–500 t stalls per week; **most recent 576 t last night** (after yieldHub deployed). Matches the “~200 t evac-boundary” report in scale; the tile is 49,14 not x=0.
- **Root cause:** `flee()` in `src/roles/remote.js`:

  ```js
  if (c.room.name === C.home && c.pos.x > 1 && c.pos.x < 48) {
    // park inward / run a home role
  }
  go(c, C.home, px, py, 1); // fallback
  ```

  On x=0/49 (or a via room’s y=0/49) the inward-park branch **does not run**. A paused or not-yet-allowed miner walks to the home exit and then fails to step inland for hundreds of ticks. rminer84324635 is the clean example: spawn at home during/after a W45N7 threat window (defender84322461 spawned 20:36), walk to 49,14, stall, then enter only later.
- **Loss:** ~200–576 miner ticks per episode (no harvest, delayed resume). After pause lifts, the miner is still sitting on the gate instead of already being inward or already on the container.
- **Verdict: shippable logic/pathing bug.** Fix the flee/outbound guard so an exit tile in the home (or via) room is treated as “not yet parked”: step inland (`x` in 2–47) toward `C.park`, never stand on 49,14 / 49,21 / 21,49.

### S4. W45N7 defender never enters W45N7 (sits in W45N8, often with inv=0 on arrive)

- **Rooms / roles:** W45N8 / W46N8 / W45N7, `defender`.
- **What:** A dispatched W45N7 defender walks home→W45N8 and never crosses into W45N7, then dies or is recycled in the via room. Later a “full-spec defender in W45N8 with no enemies” is the same pattern, not a different one.
- **Evidence (all `defender` creeps from tick 84254940 onward).** Three lives with **zero ticks in W45N7** but substantial W45N8 time:

  | Creep | Span HKT | W46N8 | W45N8 | W45N7 |
  |---|---|---:|---:|---:|
  | defender84263223 | 2026-11-14 18:30:57–19:06:08 | 181 | 282 | **0** |
  | defender84268008 | 2026-11-15 00:24:42–01:23:45 | 201 | 591 | **0** |
  | defender84311109 | 2026-11-17 05:45:39–06:23:53 | 202 | 292 | **0** |

  The first is the ROADMAP/ops note: dispatched for the 18:30 W45N7 core, arrive logged ~18:45 with `inv=0`, never entered. The third **is** the historically mentioned 05:46–06:26 window (it is 2026-11-17, not Nov 18). Most other defenders in the same period **did** enter W45N7 (typically ~200 t there), so this is intermittent, not “all defenders are broken.”
- **How often / how recent:** 3 confirmed misses in 4 days (Nov 14, 15, 17). Last miss 2026-11-17 05:45–06:23. Subsequent defenders 84313214, 84314982, 84322461 entered W45N7 correctly.
- **Root cause (hypothesis, tied to mechanism):** Threat FSM + patrol/hold in the via room. When the defender arrives and `inv=0` (core already gone, or the hostile is in W45N7 but the creep is still in W45N8), it can adopt the W45N8 patrol (`PATROL` in `remote.js` includes W45N8 24,43) or a hold, and never issue the cross into W45N7. `readyTimeout` / arrive-with-inv=0 is the documented failure mode. Related: rdef84283942 and rdef84296720 spent their whole lives in W47N8 and never entered W47N7 (411 and 428 ticks) — same family, weaker evidence (fight may have ended before dispatch completed).
- **Loss:** A full-spec defender body and spawn time, and no presence in the threatened room if the hostile is still there. When `inv=0` the energy loss is the wasted body, not a missed fight.
- **Verdict: shippable assignment/combat-pathing bug.** Verify against `incidents` arrive rows (`inv=0`) and force a W45N7 entry (or an explicit cancel) instead of a via-room patrol when the incident remote is W45N7.

### S5. Occasional W47 south-road multi-hauler jam (28,35↔29,35 and neighbors) — low frequency

- **Rooms / roles:** W47N8 south road, `wrhauler` / `whauler`.
- **What:** The 05:40 11-18 observation was **ordinary 1-tick pass-bys** (five single bounces between 05:31 and 05:52, mixed loaded/empty). It is not a standing 28,35 bug.
- **Evidence:** 72h 28,35↔29,35 is 251 wrhauler + 173 whauler bounces, but avg episode 1.13–1.16 and ~90% length 1. True jams (length ≥6) over 8 days: **9 episodes**, 7–14 ticks, last on **2026-11-17 13:10** (w8rhauler84316565, 13 t at 27,35↔28,35). One 13 t episode at 2026-11-16 06:46 involved **three** loaded rhaulers at once on adjacent pairs.
- **Root cause:** Head-on traffic on a 1-wide planned road (roads.js includes 26,35–31,35). Swap usually resolves in 1 tick; occasionally three bodies deadlock for ~10–14 t.
- **Verdict: shippable but low priority.** Do not rip up the south road or retarget C.SPAWN / extension 32,34. A stickier swap / yield-on-road rule would be enough if this is worth a pass after S1–S4.

---

## Needs more data (keep or drop with evidence)

### N1. termPark leaving with a partial 16C8M load — **not reproducing as systematic under-fill**

Home terminal is 35,31; pickups in traces occur at adjacent 34,30. Before `3cf63791` (16C8M @ 84302295), repeated **300** pickups are full loads of the old 6C body, not a bug. After 16C8M, terminal pickups are **800** (full carry) until a leftover last trip (113, 100, 500, 748, 439, 637). Examples: hauler84308716 800+800+113 (2026-11-17 03:39); hauler84332220 800 then 748 (today 10:03–10:04). `pull()` already does `min(want, freeCarry, have)`. A leftover last trip when remaining surplus < 800 is designed. Whether the hauler should also top the rest of the carry with a second resource (O then K/KO) cannot be proven from total `store` alone (no per-resource breakdown in `creep_ticks`). No immediate second-resource pickup after those leftovers appears in the 72h event list.

**Verdict: needs more data** (or drop as a current bug). Not in the shippable list.

### N2. W47N7 full containers / remote haulers not pulling — **unproven in stored ticks**

There is no container energy series in TimescaleDB. `wrminer` stand store at 18,17 / 31,34 never exceeds 50 (1C body); `stand_store100` is 0 every hour of the last 72h. High `stand_store50` is consistent with harvest+repair holding a full 50 carry, not with a 2000-full container. Hours with few wrhaulers in W47N7 line up with threat/evac (e.g. 11-18 08:00 Invader — miner fails drop to 0). wrhauler already withdraws only at ≥200 and otherwise waits in range 2 of the fullest container (`roles.js` w8rhauler). Over-haul of W47N7 vs a full local source B was an older, opposite problem and has a dedicated hook.

**Verdict: needs more data** (live `Memory.ops.w8lo7` / container energy). Do not ship a “pull more” change on this evidence. Do not open new remotes.

### N3. W47N7 `reserve` bounce at 38,28↔39,27 — **stopped after 84317657**

72h: 519 bounces, 57 episodes, 48 of length 10, avg 9.11, last tick **84317657** (~2026-11-17 14:00). No ≥5-bounce pair after that in the 72h query, including this morning. Looks like two reserves swapping near controller 38,26. No matching deploy at 84317657. Currently absent.

**Verdict: needs more data / currently dropped.** Re-open only if it returns.

### N4. W47 source A harvest tally known-low at link 26,12 — **metering artifact, not motion**

Source A stand is 26,11, link 26,12 (`config.js`). Last 72h: miner ticks on 26,11 every hour, **zero ticks on 26,12** (correct). Store on the stand is normal (avg ~25–37, max 50). Docs already call this a **link-meter artifact** (“hauler pickup at A = 0, link-meter artifact”; energy goes 26,12 → ctl 13,25). High `wminer` `fails` (~200/creep) are consistent with harvest during regen and/or transfer when the link is on cooldown, not with a wander bug.

**Verdict: infrastructure / model artifact**, not a trajectory bug. Any tally fix belongs in `tools/model_w8.py` / `Memory.ops.w8model`, not creep pathing.

---

## Other patterns scanned and not raised as new bugs

- **Stuck events table:** 8 rows total; recent ones are w8filler 33,33→34,32 on 2026-11-13 / 11-16 (pre-yieldPost/yieldHub) plus old raid9 border stucks. No new STUCK events after 84303971.
- **Home miners / queens / rhaulers** on the mineral and east-road tiles: almost all 1-tick bounces.
- **w8builder `no_task`:** 7,990 / 52,954 ticks in 72h when sites are sparse — expected.
- **wrminer / wminer fails:** large counts, dominated by empty-source or link-cooldown intents, not pathing loops.
- **Handoff seating** at W47 14,26 / 14,27 / 12,25 and home 31,30 / 29,30: no new failed handoff pattern beyond freeze/404 holes and designed overlap.
- **Combat pathing inside a live fight** after the Nov 12 rdef exit-camp fix: today’s rdef84331123 entered W47N7 and stayed until TTL, as designed.

---

## Recommended fix order (shippable only; no policy changes)

1. **S1 — W47 filler:** if extensions/hub/storage duty is full, stand on 34,32 and do not repath. Highest ongoing loss; still live this morning; also protects the yieldPost post.
2. **S2 — W45N7 rhauler approach:** one empty hauler must yield a legal wait stand instead of bouncing 30–45 t with a partner. Recurring through 11-17 21:05.
3. **S3 — rminer flee/outbound:** treat home/via exit tiles as “not parked”; step inland to `C.park`. Clear code hole; 576 t stall last night.
4. **S4 — W45N7 defender entry:** if the incident remote is W45N7, do not settle for a W45N8 patrol/hold when `inv=0` on arrive; enter or cancel. Three confirmed misses.
5. **S5 — optional:** stickier yield/swap on the W47 south road for the rare 10–14 t three-hauler jam. Then, if convenient, park the home queen when the fill route is already full (S1 sibling).

Leave locked: 15k floor, W47 keep=2 until a real 40k/500t lock, no standing third upgrader, no fiat softCap unseal, no market/factory/W47 labs/new remotes, C.SPAWN stays [15,18], do not move extension 32,34.

---

*Work files under `/workspace/screeps/state/_traj_anomaly_work_2026-11-18/`. Catalog written 2026-11-18 ~11:30 Asia/Hong_Kong from stored TimescaleDB only; no live console slot and no official-history refetch were required.*
