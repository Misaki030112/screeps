# Community practice briefing — mid-to-late RCL7

Research for Misaki Ausuka's 12-hour strategic review, morning 18 Nov 2026 Asia/Hong_Kong.
Sources fetched live this morning. Comparative only: this note does not recommend changing keep, floors, remotes, industry, or market.

---

## 1. Official RCL7 vs RCL8 (what opens, and typical advice)

Official Control table ([docs.screeps.com/control.html](https://docs.screeps.com/control.html), footer “Last updated: Nov 11, 2026”) and `CONTROLLER_STRUCTURES` on [docs.screeps.com/api/](https://docs.screeps.com/api/):

| Already open at RCL6 | New / bigger at RCL7 | New / bigger at RCL8 |
| --- | --- | --- |
| Extractor, 3 labs, terminal | **2nd spawn**, 50 extensions at **100** energy each, 3 towers, 4 links, **6 labs**, **factory** | **3rd spawn**, 60 extensions at **200** energy each, 6 towers, 6 links, **10 labs**, factory, **observer**, **power spawn**, **nuker** |
| Ramparts max 30M | Ramparts max **100M** | Ramparts max **300M** |
| RCL6→7 costs 3,645,000 | RCL7→8 costs **10,935,000** | No further RCL; upgrade still feeds GCL, cap 15 e/t unboosted (`CONTROLLER_MAX_UPGRADE_PER_TICK`) |

RCL7 is the last long climb (official plus wiki: “each level takes exponentially more energy… until the transition from RCL 7 to 8, which costs 10,935,000 energy,” [wiki.screepspl.us/Room_Control_Level](https://wiki.screepspl.us/Room_Control_Level/)). The distinctive RCL7 unlock is the **factory** and the **second spawn** / doubled extension size; observer, power spawn, and nuker wait for RCL8.

Official resources page ([docs.screeps.com/resources.html](https://docs.screeps.com/resources.html), same Nov 11, 2026 footer):

- Minerals need an extractor at RCL6+. “By mining and processing minerals, you can significantly speed up your economy and boost the effectiveness of your creeps.”
- Upgrade boosts, “without increasing the energy cost”: **GH +50%**, **GH2O +80%**, **XGH2O +100%** `upgradeController`. Boosting one body part costs 30 compound + 20 energy.
- Factory is “available at RCL 7.” An unleveled factory only makes basic / “any level” commodities (including compression such as batteries). “The full use of factories is possible with Operators only, and their `OPERATE_FACTORY` power.”

Official defense ([docs.screeps.com/defense.html](https://docs.screeps.com/defense.html)): walls and ramparts start at **1 hit** and must be fortified; safe mode is last resort and only one room per shard; towers weaken with range; “a well-secured team of creep invaders are able to withstand the attack by multiple towers,” so creep defenders behind ramparts matter.

Downgrade timers: use the API constants, not the slightly jumbled prose on the Control page. `CONTROLLER_DOWNGRADE` is **150,000** ticks at RCL7 and **200,000** at RCL8 ([docs.screeps.com/api/](https://docs.screeps.com/api/)).

Typical official / wiki advice at this band, in one line: keep upgrading toward RCL8 (GCL grows in parallel), use minerals/labs for boosts once you can, do not leave walls at 1 HP, and treat factory commodities as a later, power-creep-gated industry.

---

## 2. Overmind (master re-checked this morning)

Repo: [github.com/bencbartlett/Overmind](https://github.com/bencbartlett/Overmind). **Last commit on master is 14 Jun 2019 20:55 UTC** (15 Jun 2019 04:55 Asia/Hong_Kong). No 2024–2026 changes to UpgradeSite. The constants below were re-fetched from current master raw and match last evening's re-check.

`UpgradeSite.settings` ([src/hiveClusters/upgradeSite.ts](https://github.com/bencbartlett/Overmind/blob/master/src/hiveClusters/upgradeSite.ts)):

```ts
static settings = {
    energyBuffer     : 100000, // Number of upgrader parts scales with energy - this value
    energyPerBodyUnit: 10000,  // Scaling factor: this much excess energy adds one extra body repetition
    minLinkDistance  : 10,
    linksRequestBelow: 200,
};
```

Upgrade power: `1 + floor((assets.energy - 100000) / 10000)`, then ×2 if surplus > 500k and ×4 if > 800k; cap 15 WORK at RCL8. **A room sitting at 15–40k energy is 60–85k under the buffer**, so this formula yields the floor of **1 WORK** only after the buffer is cleared.

Spawning gate ([src/overlords/core/upgrader.ts](https://github.com/bencbartlett/Overmind/blob/master/src/overlords/core/upgrader.ts)): upgraders are wishlisted only if `assets[RESOURCE_ENERGY] > UpgradeSite.settings.energyBuffer` **or** `ticksToDowngrade < 500`. Upgraders request **T3 upgrade boosts** (`boostResources.upgrade[3]`, i.e. XGH2O) when they do spawn.

Related Overmind energy / defense constants (same 2019 master, still accurate as published code, not as a living bot):

- `Energetics` ([src/logistics/Energetics.ts](https://github.com/bencbartlett/Overmind/blob/master/src/logistics/Energetics.ts)): terminal in-threshold 25k, equilibrium 50k, out-threshold 100k; `lowPowerMode` only for an adult (RCL8) colony with storage and terminal both near cap.
- Barriers built from RCL3, **bunkerize at RCL7**, 3-tile padding ([src/roomPlanner/BarrierPlanner.ts](https://github.com/bencbartlett/Overmind/blob/master/src/roomPlanner/BarrierPlanner.ts)).
- Fortify targets ([src/overlords/core/worker.ts](https://github.com/bencbartlett/Overmind/blob/master/src/overlords/core/worker.ts)): RCL7 **1,000,000** hits, RCL8 **20,000,000**, critical 2,500; **`fortifyDutyThreshold: 500000`** — “ignore fortify duties until this amount of energy is present in the room.” That is a very high energy gate for *routine* wall spend (critical barriers are still handled separately).

Older commit `2eae97b` used the names `storageBuffer: 100000` and `energyPerBodyUnit: 25000`. Current master is **100k / 10k / 200**, unchanged.

---

## 3. TooAngel and The International

### TooAngel (actively maintained)

Repo: [github.com/TooAngel/screeps](https://github.com/TooAngel/screeps). Last commit fetched: **17 Nov 2026 07:51 UTC** (15:51 Asia/Hong_Kong), so this is current.

Config ([src/config.js](https://github.com/TooAngel/screeps/blob/master/src/config.js)):

- `storage.lowValue: 2000` — storage is “low.”
- `room.upgraderMinStorage: 0` — an upgrader may be spawned above this.
- `room.upgraderStorageFactor: 2` — pre-RCL8 body sizing.
- `room.isHealthyStorageThreshold: 100000` — “healthy” storage.
- `terminal.minEnergyAmount: 40000` / `maxEnergyAmount: 50000`.
- `boosts.enabled: true`, `mineral.enabled: true`, `mineral.storage: 100000`, `commodities.disabled: false`.
- `nextRoom.cpuPerRoom: 13`.

Pre-RCL8 upgrader size ([src/role_upgrader.js](https://github.com/TooAngel/screeps/blob/master/src/role_upgrader.js)):

> “One work part one energy per tick multiplied by config value with lifetime. So have at least a specific amount of energy in storage that the upgrader can use. Example with upgraderStorageFactor 2: 6453 energy in storage are 2 workParts; 3000 energy will be put in the controller.”

Formula: `workParts = floor((storage.energy + 1) / (CREEP_LIFE_TIME * upgraderStorageFactor))` = `floor((energy+1) / 3000)` with the default factor 2. Arithmetic from that published formula (not a documented table):

| Storage energy | TooAngel WORK parts (RCL&lt;8, factor 2) | Lifetime energy into the controller |
| --- | --- | --- |
| 15,000 | 5 | ~7,500 |
| 20,000 | 6 | ~9,000 |
| 30,000 | 10 | ~15,000 |
| 40,000 | 13 | ~19,500 |

They spawn **one** such upgrader if `storage.store.energy > upgraderMinStorage` (default 0), and **stop upgrading** if storage `isLow()` (2,000) unless the controller is about to downgrade. Upgraders list `boostActions: ['upgradeController']`.

Mineral *extraction* starts once extractor + terminal exist and terminal stock is below 100k of the room mineral — **no 100k energy gate** ([`isRoomReadyForExtractor`](https://github.com/TooAngel/screeps/blob/master/src/prototype_room_my.js)). Lab / reaction creeps wait for `isRoomReadyForMineralHandling()`, which requires terminal, storage, **and** `isHealthy()` (storage energy ≥ 100k). Power processing also waits for that 100k healthy line. When not healthy, builders are restricted to “essential” construction sites only.

### The International (open-source, last push 27 Aug 2024)

Repo: [The-International-Open-Source](https://github.com/The-International-Screeps-Bot/The-International-Open-Source) branch `Main`. Last commit **27 Aug 2024 10:39 UTC−7** (28 Aug 2024 01:39 Asia/Hong_Kong). No 2025–2026 policy commits were present on Main.

`CommuneUtils.minStoredEnergy` ([src/room/commune/communeUtils.ts](https://github.com/The-International-Screeps-Bot/The-International-Open-Source/blob/Main/src/room/commune/communeUtils.ts)) is documented in-code as “the minimum amount of stored energy the room should only use in emergencies”:

```ts
let minStoredEnergy =
  Math.pow(room.controller.level * 6000, 1.06) + threatened * 20
// then, if there is a next RCL:
minStoredEnergy -= Math.pow((progress / progressTotal) * 20, 3.35)
storedEnergyUpgradeThreshold = floor(minStoredEnergy * 1.3)
```

Arithmetic at threatened=0, RCL7 (derived from that formula):

| Controller progress | minStoredEnergy | upgrade threshold (×1.3) |
| --- | --- | --- |
| 0% | 79,550 | 103,415 |
| 41% (colony-like) | 78,399 | 101,918 |
| 70% (home-like) | 72,639 | 94,430 |

Spawn policy ([src/room/commune/spawning/spawnRequests.ts](https://github.com/The-International-Screeps-Bot/The-International-Open-Source/blob/Main/src/room/commune/spawning/spawnRequests.ts)): if storage/terminal exist, **do not spawn surplus upgraders unless stored energy ≥ `storedEnergyUpgradeThreshold`**, except when “desperate” (RCL1, or `ticksToDowngrade` ≤ 75% of `CONTROLLER_DOWNGRADE`). With a terminal at RCL≥6, rooms that are not the funnel target spawn no upgraders. Construction sites or tower inferiority also suppress non-desperate upgraders. Comment in the same function: “If there is a storage, prefer needed remote creeps over upgraders.”

Factory ([src/room/commune/factory.ts](https://github.com/The-International-Screeps-Bot/The-International-Open-Source/blob/Main/src/room/commune/factory.ts)): convert energy → battery only when stored energy **> `minStoredEnergy * 1.2`** (about 87k at 70% RCL7); decompress batteries back to energy when stored energy **< `minStoredEnergy`**.

---

## 4. Timing: minerals / labs / boosts vs remotes vs walls

What strong, documented practice actually does at this band:

1. **Minerals and basic lab work start at RCL6**, not RCL8. Official resources page presents mining → compounds → boosts as the way to speed the economy. The plus wiki’s intermediate guide is blunt: if you put off mineral code, “you’ll end up at a disadvantage compared to your neighbors who started earlier,” because peacetime **XGH2O doubles** upgrade and GCL gain ([wiki.screepspl.us/Intermediate-level_tips](https://wiki.screepspl.us/Intermediate-level_tips/)). TooAngel will mine the room mineral as soon as extractor+terminal exist, but holds *reactions* until storage is “healthy” (100k). Overmind wishlists T3 upgrade boosts on upgraders, but those upgraders themselves only appear above 100k energy (or a downgrade emergency).
2. **Boosted upgrading is the peacetime accelerator, not a substitute for a storage buffer.** Official XGH2O is +100% progress with **no extra upgrade energy cost** (only 20 energy + 30 compound per boosted part). That is energy-efficient *once compounds and a stable energy stock exist*. The same strong bots that want XGH2O still refuse a large upgrader crew at 15–40k energy.
3. **Factory / market / high commodities are later than labs.** Official: unleveled RCL7 factory is basic commodities only; leveled industry needs Operators and `OPERATE_FACTORY`. International will not even pack batteries until energy is ~20% above its emergency minimum (~87k at late RCL7). TooAngel enables commodities in config but gates “healthy” rooms at 100k for reactions and power.
4. **Remotes and a third claimed room are CPU- and support-gated**, especially on shard3. The plus wiki: before claiming, “Do you have enough CPU? … If you’re short on CPU (i.e. on shard3) … it should be well thought before.” Also: do you have a room that can support the new one, and is the empire energy-starved or under attack? ([wiki.screepspl.us/Claiming_new_room](https://wiki.screepspl.us/Claiming_new_room/)). International’s spawn comment prefers **needed remotes over upgraders** when a storage exists — i.e. fix income before adding upgrade drain. TooAngel budgets `cpuPerRoom: 13` for new claims.
5. **Walls:** official docs say unfortified 1-HP walls are useless; the plus wiki notes a boosted dismantler can remove “6m hitpoints (or more) … over 1000 ticks,” so towers alone will not do later. Overmind, by contrast, only routinely fortifies above **500k** energy and targets a modest **1M** hits at RCL7 (max allowed is 100M). Community practice here is mixed: defense writeups are more aggressive on HP; the best-known automated bots are conservative on wall spend until energy is plentiful.

For the specific picture “home ~1 week from RCL8 with tight 15–20k, second room mid-RCL7 with 30–40k, KO already running”: documented strong bots would treat KO / T1 lab work as already in-band, would **not** treat 30–40k as a healthy surplus, would **not** scale a large upgrader crew or factory on the tight home, and would use XGH2O only once both compounds and a much larger energy buffer were in place. They would not claim a third room on a tight, shard3 CPU budget just because GCL allowed it.

---

## 5. Common mistakes at mid-to-late RCL7

Drawn from the sources above (not from folklore):

- **Over-upgrading into an empty storage.** Overmind and International simply do not spawn surplus upgraders below ~100k / ~94–102k. TooAngel will keep a single upgrader but **shrinks the body** so one lifetime spends about half of current storage, and it stops at 2k unless a downgrade is imminent. Running a 14-WORK (or 2×14-WORK) crew while storage sits at 15–20k is the opposite of all three.
- **Opening industry too early.** Factory is an RCL7 unlock, but official high-level commodities need power creeps, and both TooAngel and International wait for a high energy floor before reactions or battery packing. Building a factory or turning on market logistics on a 15–20k home stockpile is earlier than those codebases.
- **Claiming a third room too soon.** Plus wiki: CPU (explicitly shard3), a supporting room, and not doing it while energy-starved or under attack. TooAngel also applies a CPU-per-room budget.
- **Under-building walls** (1 HP, or no perimeter) relative to official defense docs and the plus wiki’s boosted-attacker numbers — *or*, conversely, dumping scarce energy into high ramparts while storage is tight (Overmind’s 500k fortify gate).
- **Putting off minerals until RCL8.** Official and the plus wiki both treat labs/boosts as the mid-game speedup; XGH2O is the peacetime headline compound. Delaying even T1 KO-style work is the documented mistake. (Authorized KO already running is the opposite of this mistake.)
- **Treating “short of the upgrade ceiling” as a crisis.** A designed keep=2 rate at 66.5% of a 30.08 e/t ceiling is a local policy choice; none of the cited bots try to push mid-RCL7 rooms to the 15 e/t (or unboosted per-tick) ceiling while storage is thin.

---

## 6. Implications for our board (comparative only, not a decision)

Context used for comparison only: shard3; home W46N8 late RCL7 (~70%, ~8.6 days at last evening’s 20.62 e/t) often at/under a 15k floor with 1–2×14W; 3rd home upgrader latches only at 20k/300t (touches so far were flickers); colony W47N8 mid RCL7 (~41%) keep=2 until 40k/500t; designed keep=2 is 20 e/t; KO running; boosts skipped under 20k; industry, market, W47 labs, new remotes, and T3 are off.

- **15k home floor.** More conservative than TooAngel’s “stop if storage is low” line (2,000), and far **more aggressive** than Overmind’s 100k spawn buffer and International’s emergency minimum (~73–80k at mid/late RCL7) plus upgrade threshold (~94–102k). In those codebases, ~100k is the “healthy / allowed to upgrade” band. 15k is a local safety net, not a community “enough energy” line. We are also far below Overmind’s unchanged 100k `energyBuffer`.
- **20k/300t third 14W (home).** More aggressive than all three cited bots. At 20k, TooAngel would size about **6 WORK total** on one creep; Overmind and International would spawn no surplus upgrader at all. A third 14W is another 14 e/t, on the order of 21k energy over one lifetime — comparable to the entire 20k latch itself. The 300-tick hold is more careful than a flicker, but the *size* of the third body is the outlier, not the idea of a latch.
- **40k/500t W47 keep=3.** Still well under Overmind / International upgrade buffers and TooAngel’s 100k `isHealthy` line. At 40k, TooAngel would size about **13 WORK** on one creep — the same order as a single 14W, not an extra keep on top of a designed 20 e/t keep=2 crew. The 500-tick hold is in the spirit of “don’t flicker,” but keep=3 at 40k is more aggressive than TooAngel’s storage-proportional body and much more aggressive than Overmind/International.
- **Boost skip under 20k.** Official XGH2O is energy-efficient (+100% progress, no extra upgrade energy). The plus wiki would not want minerals delayed for that reason. Strong bots, however, only run the large upgrader crews you would bother boosting once energy is around 100k. Skipping boosts at 15–20k is slightly conservative versus the efficiency argument and consistent with “don’t add lab logistics on a tight floor.” Authorized KO already running is aligned with “don’t put off minerals.”
- **No industry / market / T3 yet.** Consistent with TooAngel (reactions need 100k healthy), International (battery production only above ~`minStoredEnergy * 1.2`), and official `OPERATE_FACTORY` gating of high commodities. Opening a factory or market on a 15–20k home would be early versus these bots. This is a comparison, not a request to reopen those boards.
- **No new remotes / no third room.** Plus wiki explicitly flags shard3 CPU for new claims and asks whether a supporting room can fund them. International would rather staff remotes than add upgraders when storage exists; tight home energy is treated there as an income problem, not a “need more WORK” problem. Adding another remote is *one* community response to a tight floor, not a universal one, and shard3 CPU is a real counter-argument. Three remotes and a ~18 CPU 12h average already look like a working remote economy, not an empty one.
- **Biggest gap vs documented practice.** It is not that 15k / 20k / 40k floors are “too high.” Relative to Overmind and International they are **low**. The gap is running **14W (or 2×14W)** while storage is sitting on those floors. Overmind/International would idle surplus upgrade; TooAngel would shrink the body so a lifetime cannot empty the store.

Honest split: some human writeups (plus wiki on XGH2O, official “minerals speed the economy”) are more aggressive about *boosted* upgrading once compounds exist. The best-known open-source bots are more conservative than our current home/W47 upgrade intensity at 15–40k storage, and more conservative than our third/keep=3 latches, while being *less* conservative than a hard “never boost below 20k” rule once a large surplus actually appears.

---

## Source list (fetched 18 Nov 2026 morning Asia/Hong_Kong)

| Source | Fetched | Notes |
| --- | --- | --- |
| [docs.screeps.com/control.html](https://docs.screeps.com/control.html) | Yes (footer Nov 11, 2026) | Official RCL structure table |
| [docs.screeps.com/api/](https://docs.screeps.com/api/) | Yes | `CONTROLLER_STRUCTURES`, `CONTROLLER_LEVELS`, `CONTROLLER_DOWNGRADE`, `CONTROLLER_MAX_UPGRADE_PER_TICK` |
| [docs.screeps.com/defense.html](https://docs.screeps.com/defense.html) | Yes (footer Nov 11, 2026) | Walls, ramparts, towers, safe mode |
| [docs.screeps.com/resources.html](https://docs.screeps.com/resources.html) | Yes (footer Nov 11, 2026) | Minerals, GH/GH2O/XGH2O, factory / `OPERATE_FACTORY` |
| [wiki.screepspl.us/Room_Control_Level](https://wiki.screepspl.us/Room_Control_Level/) | Yes | Narrative unlocks; points back to official Control |
| [wiki.screepspl.us/Intermediate-level_tips](https://wiki.screepspl.us/Intermediate-level_tips/) | Yes | XGH2O, room choice, walls vs boosted attackers |
| [wiki.screepspl.us/Claiming_new_room](https://wiki.screepspl.us/Claiming_new_room/) | Yes | CPU / shard3 / support-room cautions |
| Overmind master `upgradeSite.ts`, `upgrader.ts`, `Energetics.ts`, `worker.ts`, `BarrierPlanner.ts` | Yes, raw.githubusercontent.com | Last commit Jun 2019; 100k/10k/200 confirmed |
| TooAngel `config.js`, `role_upgrader.js`, `prototype_room_my.js` | Yes, clone of master | Last commit 17 Nov 2026 |
| International `communeUtils.ts`, `spawnRequests.ts`, `factory.ts` | Yes, clone of Main | Last commit 27 Aug 2024; no later policy commits on Main |

No cited source failed to fetch. Slack-only writeups were not used (not publicly archived in a verifiable form). Overmind should be treated as a stable, widely copied reference, not as a 2024–2026 maintained bot.
