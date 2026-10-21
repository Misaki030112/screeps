# Neighbours (living page)

Strategy review **2026-10-17 ~14:40 UTC+8**. Raw data: hourly `tools/neighbor_scan.py` rows (`events.kind='neighbor'`), live API reads.

## Who is around W46N8

| Room | Owner | What we saw 10-17 | Can it reach us? |
|---|---|---|---|
| W47N9 | BustJetter (GCL ~10.8M, 3 rooms) RCL6 | economy only, towers ~900, storage ~22k | via W47N8 (west of home) |
| W48N9 | BustJetter RCL6 | army room: 4–15 combat creeps all day; **towers unfed (~0) for 38 h+** while storage grew 12k→80k | via W47N9→W47N8 |
| W49N9 | BustJetter RCL5 | economy only | far side |
| W47N8 / W47N7 | reserved by BustJetter | 7 / 5 economy creeps (CLAIM2 reservers, haulers), **no combat** | border rooms (W47N8 touches home) |
| W48N8 | **Evans_702** (GCL ~1.96M, 1 room) RCL6 | 1 tower (empty), 20 walls up to 2.39M, spawns a 2RA2M `Defender<tick>` every ~50 ticks (6 alive, parked at 38–40,22–24) | **no east exit** (terrain) — cannot walk into W47N8 |
| W47N6 | yousukeman3 (GCL ~56k) RCL3, safe mode | economy only | not adjacent |
| W46N7 | FungousCoast245 (GCL ~26.5B, 67 rooms) RCL8, 6 towers | 2 workers | no N/E exits; outside novice zone until 10-28 |
| W44N7 | **Cody132** (GCL ~3) RCL7, 2 towers, 92 walls | 0 combat (10-19) | **from 10-28**: novice wall W45N7 x=49 (44 tiles) and W44N8 y=49 (18) drop -> our remotes |
| W46N9 | **drtk712** (GCL ~14.5) RCL8, 6 towers, nuker | 0 combat (10-19) | 0 exits to home; **from 10-28** via W47N9 x=49 (20 tiles) -> W47N8 north |
| W44N8 / W47N5 | Fandalah RCL6 | no combat creeps, towers full | east of remote |

## Reading the W48N9 army

- 42 scans in 48 h: combat-creep count **min 0 / median 6 / max 15**. The 13:48 count of 10 is inside that band, not an escalation.
- Bodies are unboosted and mixed (7T14A21M, 5T10A15M, 8–11 RA, 4–7 HEAL). Total at the 13:48 peak ≈ 38 ATTACK, 28 RA, 22 HEAL ≈ 21k HP.
- No combat creeps in W47N8/W47N7 at any scan we have, so nothing has staged next to us.
- Hypothesis (unproven): Evans_702 in W48N8, directly south of W48N9, keeps spawning defenders with an empty tower, which looks like a room under pressure. BustJetter's army may be busy with him. History replay endpoints were not reachable, so we have no direct combat log.

### Tower math if the whole 10-creep stack came in

- 2 towers deal 600 each at range ≤5, ~150 at range ≥20. Focus-fire on one melee (4.2k HP) against all 22 HEAL (264/t) at mid-room (~900/t total) kills it in ~7 ticks; at the room edge (~300/t) towers barely out-heal and the anti-drain hold should stop firing.
- 38 ATTACK + 28 RA ≈ 1.4k dmg/t vs a 100k core rampart ≈ 70 ticks per rampart while standing in tower range.
- Limiting factor is **our energy**: towers ~970 each + storage ~1.9k ≈ 380 tower shots. Enough to kill the stack once if it fights inside, not for a long drain. The RCL6 bank (20k) fixes this too.

## Alerting change (10-17)

`neighbor_scan.py` severity is unchanged (so it is "high" almost every hour because W48N9 always has ≥3 combat creeps). It now also scans W48N8, W47N8, W47N7 and prints a second line:

```
trend no change vs 48h band {...}            # normal
trend NEW: W48N9 16 combat > 48h max 15; ... # real change
```

Real changes = above the room's 48 h max, any combat creep in W47N8/W47N7, or boosted parts. Page Misaki on `trend NEW`, not on bare "high".

## 2026-10-21 14:4x strategy review: BustJetter after the W47N9 probe raid (t83779880)

Live `game/room-objects` read (no Memory quota):
- **W47N9 safe mode ends t83799469** (~19.6k ticks, at 4.4-4.6 s/tick ~ **10-22 14:45-15:45 UTC+8**). safeModeAvailable 4. RCL6 992k. Until then nothing of ours can hurt anything in W47N9; their creeps can still leave it, and in W47N8 our towers work as normal, so W47N8 defence math (`docs/DEFENSE_W47N8.md`) is unchanged.
- **Response so far is economic, not military.** W47N9: 11 creeps, all haulers/workers (0 ATTACK/RANGED/HEAL), towers 654/465, storage 7.8k, **terminal 29.6k** energy, ramparts max 27.6k (weak), 3 construction sites. W48N9 storage fell 93k -> 56.6k in ~1 h while its towers sit at 1/8: energy is being shipped by terminal into W47N9 to refill towers and rebuild. W48N9 ramparts 79-92k, 21 creeps, none combat.
- **Our garrison** (raid9 2 melee + 2 ranged, inside the W47N8 north wall since 3d38834) has TTL 704-944 -> gone ~15:40-16:00 UTC+8 today, not respawned. After that W47N8 is back to towers + guard logic only.
- **Read:** no sign of retaliation yet; the window to watch is the next ~24 h of safe mode (they can stage freely) and right after it ends. Neighbor scan already flags any combat creep in W47N9/W48N9 and in the approach rooms; no new tooling needed.
- **Decision for Misaki (not taken):** whether anything follows the probe after safe mode ends ~10-22 15:00. Default: nothing, defend only.
