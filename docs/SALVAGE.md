# Salvage: dropped energy, tombstones, ruins (2026-10-16)

## Live finding (tick 83673317, room history 83670300–83673300)
- W46N8: 481 dropped at (33,30), ruin (34,28) 122, scout tombstone (1,24) 45. W45N8: nothing.
- Source: carriers dying of old age while loaded — haulers 700 (34,30) and 650 (33,30), rhaulers 400 (48,14) and 296 (46,16)
  at the home exit, queen 200 (38,28); BustJetter scout tombstones 45 each. ~2.4k in ~3000 ticks ≈ 0.8 energy/tick.
- Miner containers never overflowed (miner B transfers into storage, A container well below 2000). No overflow fix needed.
- Nothing picked these up: haulers only took drops within 1 of their own miner container.

## Rules (src/utils/salvage.js)
- Candidates: dropped energy, tombstones, ruins with >= 50 energy, not within 5 tiles of a hostile creep with ATTACK/RANGED_ATTACK.
- Worth it: expected take (minus decay ceil(a/1000)/tile for drops, minus other carriers' claims) >= 50 + 8 x range, range <= 25.
- Reservation: each carrier's `memory.salv` claims its free capacity on that pile; others see only the rest.
- Users: home haulers (before their fixed container), rhaulers inside W45N8.
- Root cause: `retire()` — hauler TTL <= 50, queen <= 25: no new load; carrying -> deliver; empty -> recycle at spawn.
  rhaulers do not leave home when TTL < measured round trip (`memory.rt`, default 200) + 40; they work as home haulers.
- Fits the final RCL8 plan: no structures, no new routines. Test: `tests/salvage.js`.
