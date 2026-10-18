# W47N8 after the claim: safe mode, RCL2→3, and holding the room (strategy review 2026-10-18 14:40 UTC+8)

Sources: Screeps engine `src/processor/intents/creeps/{claimController,upgradeController,attackController}.js`,
`src/processor/intents/controllers/{tick,activateSafeMode}.js`, `src/game/structures.js` (StructureController.activateSafeMode),
`@screeps/common/lib/constants.js`. Live state @ tick 83719393: W47N8 reserved by BustJetter, ticksToEnd 3285;
`cq.claim=true`, 1 cqbreaker out, quad 4/4 in W47N8; `cq.autoSafe` **unset**; W47N8 `safeModeAvailable` 0. Home: 51 barriers
all ≥131k (wall step 1 done), storage 39.3k, home SM 5 available.

## Engine facts that matter for this op (verified in source)

| Fact | Source | Consequence |
|---|---|---|
| `claimController` sets level 1, progress 0, `downgradeTime=null`; it does **not** touch `safeModeAvailable` | claimController.js | W47N8 starts with 0 charges (live: 0) |
| Next tick: `downgradeTime = now + 20001` | controllers/tick.js | RCL1 timer starts full |
| Level-up needs `progress ≥ 200` **and** `downgradeTime+100 ≥ now+CONTROLLER_DOWNGRADE[1]` (timer within 100 of max). Each upgrade tick restores +101 | upgradeController.js / tick.js | Workers that start upgrading late just need a few extra ticks; not a blocker |
| On RCL2: `safeModeAvailable += 1`, `downgradeTime = now + 5000` (half of 10000) | upgradeController.js | 1 charge at RCL2; room falls back to RCL1 (and loses all charges) after ~5000 t without upgrading |
| activateSafeMode: ERR_TIRED if `upgradeBlocked` or cooldown or `ticksToDowngrade < DOWNGRADE[lvl]/2 − 5000` (RCL2: 0, RCL3: 5000); ERR_BUSY if **any** of our rooms is in SM | structures.js / activateSafeMode.js | While W47N8 is in SM, **home cannot SM** (and vice versa) |
| In a novice room, `safeModeCooldown = null` (no 50000 t cooldown) | controllers/tick.js | Until 10-28 03:33 we can re-activate as soon as one SM ends, if a charge exists |
| Enemy `attackController` on an owned ctl (not in SM): −300 downgrade per CLAIM and **upgradeBlocked 1000 t** | attackController.js | One BustJetter CLAIM creep adjacent to 15,25 **between claim and SM** blocks both upgrading and SM for 1000 t |
| SM duration 20000 t | constants | ≈23.3 h at 4.2 s/tick |

## What this means

1. **The dangerous window is claim → RCL2 → SM.** If workers are already at the controller with energy when the breakers
   claim, 200 progress takes a few ticks (3×5W ≈ 15/t) and the window is tiny. If an enemy CLAIM creep reaches range 1 of
   15,25 inside it, we lose 1000 t (no upgrade, no SM). Quad post 21,7 is ~18 tiles from the controller, so a reserver that
   slips past the north post is not covered. Watchpoint: kill CLAIM creeps before they reach the controller; consider one
   reinforcement (cqrh) near 15,25 until SM is on.
2. **`cq.autoSafe` is off.** Workers will reach RCL2 and then wait for a human. Every tick between RCL2 and the SM click is
   exposed to (1). Misaki already ordered "RCL2 then safe mode", so the only open question is how `autoSafe` should behave,
   because the current code **re-activates when the SM ends** (chain), which keeps home locked out of SM.
3. **Chaining is possible during novice.** No cooldown in novice; each new RCL gives +1 charge. RCL2→3 needs 45k progress
   (+ spawn 15k + tower 5k ≈ 65k energy) inside 20000 t ≈ 3.3 e/t, easily covered by W47N8's two 3000-cap sources plus
   home haulers. So: SM1 at RCL2 (~23 h) → reach RCL3 + tower inside SM1 → SM2 (~23 h). RCL4 (135k more) inside SM2 needs
   ~7 e/t upgrade, possible once the W47N8 spawn runs its own miners. A full chain ends around 10-20 to 10-22 at best, not 10-28.
4. **Cost of chaining:** home W46N8 cannot use its 5 SM charges for the whole chain. Home has 2 towers (960/980e) and 51
   barriers ≥131k, and BustJetter's scouts have done 0 damage so far, so the home risk is low but non-zero.
5. **After novice ends (10-28 03:33)** every activation costs a 50000 t (~2.4 day) cooldown, and W47N8 sits next to his RCL6
   W47N9 (2 towers) and the W48N9 army. W47N8 must stand on its own tower(s) + ramparts by then, ideally RCL4+ with storage.

## Recommendation (needs Misaki: SM chain policy)
- **A (recommended):** `autoSafe` = activate **once**, the same tick W47N8 reaches RCL2; then use the 23 h to build spawn → RCL3 →
  tower → ramparts; decide on SM2 when SM1 is about to end (home SM stays the default emergency button after that).
- B: full auto-chain (current autoSafe code) — maximum W47N8 cover until ~10-20/22, home locked out of SM the whole time.
- C: manual — someone must click within ticks of RCL2 (exposed to the 1000 t upgradeBlock).
Code change for A is small (one-shot flag in `conquest.js` worker block) but **not done here**: quad/conquest code is being
edited live by the op session; this review deploys nothing.

## Energy note
Home upgrade/build pause is tied to "until W47N8 RCL2". After RCL2 the W47N8 RCL3 push (~65k) and home walls step 2 (300k)
compete. Suggest: W47N8 runs on its own sources + spawn as soon as the spawn is up; home resumes upgrade once the W47N8 spawn
is built (not at RCL2), keeping storage ≥ 20k as the defence reserve.
