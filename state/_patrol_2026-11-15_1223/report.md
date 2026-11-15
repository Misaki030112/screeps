# Patrol 2026-11-15 12:26 Asia/Hong_Kong (1h peacetime)

TIP 84277930 12:26:44 HKT LIVE ffdf767 (held, deploy@84268045 00:27). No src change, no deploy.

## Alerts
- FORMAL ALERT (a) HOLDS on W47 only: exact2h 17.07/30.08=56.8% (prev 18.60=61.9%) is the NINTH consecutive patrol under 70% AND short is soft (last20-200 span=20-60 after 12:05-12:22 freeze not used alone; last300 10.77=35.8% span=300, below designed keep=2 20 e/t=66.5%; 1h 16.62=55.2%). w8up 2→3@84277570 12:01 handoff →2@84277880 12:23; new ups waiting_feed. Do not revert keep=2; 40k/500t lock not hit.
- Home (a) NOT formal: exact2h 16.28/26=62.6% (prev 22.63=87.0%) is the first under after CLEARED; short also soft (last300 11.06=42.5% span=300; 1h 13.38=51.4%). nUp=1 since 84277190 11:34 why=floor_bank, also remote_pause during W45N7 DEFEND; later why=floor_bank after clear. Watch next patrol. Do not change 15k floor.
- (b) NOT formal: tip 14162 UNDER consec-under=1 (prev tip 18036 ABOVE consec-under=0). Later 12862@84277960 / 12162@84277970 still UNDER. since-last min 10864@84277620 12:04 max 18136@84277050 11:24 under15k 29/51=56.9%.
- no formal (c)/(d)/(e)/(f). reserver zero_run 160t 84277090-84277250 is spawn-busy behind defender84277048 (spawn 145t until 84277192); replacement reserver84277251 at 84277252, not formal (c).

## Remotes / defense
- W45N7 solo inc=84277047 appeared 11:24 at (46,49) hits=1000 invOnly. rdef/kiter defender84277048 spawn_start 84277048 waited=1 hits=4800 body 18RA/24M/6H (~5400e, not 2500 cap); defend 84277192 dur=145; arrive 84277258 travel=65; alert_ended 84277330 11:44 dur=221 totalDamage=5280. incidents missing cleared row (known ingest class). Last in W45N7 84277361, then W45N8 (25,41).
- W45N7 lv0 core inc=84277556 appeared 12:00 at (4,35) hitsMax=100000 invOnly. defender84277557 spawn_start 84277557 waited=1 hits=5000 body 25A/25M (full budget). Entered W45N7 84277777 12:16, fought at (4,34), KILLED 84277944 12:27:42 dur=388 why=killed, now SAFE cores=0 host=0. Defender walking out (21,8) hits 5000.
- Remotes after clear: W45N8 SAFE res~2378, W45N7 SAFE res~735 (bled during fight; reserver84277945 walking, 84277389 ttl short), W47N7 SAFE res~2932 reserve784277324 seated (39,27). r7.on endTime=84280873.
- Memory.cmd.on=1 at=84224348 stale c={} s={} v=1, not touched. sma 6/6 ttd 150000/150000 never activated.

## Energy / strategy
- Home sites=0 progress 6770593→6798324@tip later 6798712 RCL7 62.17%. uf tip why=remote_pause nUp=1 tUp=1 work=14 surplus=-788; later why=floor_bank nUp=1 stor 12162. 20k/300t not hit (3h max 18778@11:04, 18992@08:26 aged out; best>=20k span=0).
- W47 stor since_last min 24147@11:38 max 28932@tip later 29902@84277960 / 29552@84277970. 3h max now ~29902 (38466@08:37 aged out of 3h). upArm=40000 upLatched=0, zero samples >=40k, not a latch. keep=2 bankWhy=ready softCap2=0 threatSoft=0 sealPark=0 (cleared when w8up briefly hit 3 at 12:01). phase=ready siteRem=0 feedOk=1 hubLink=1 leanBank=0. Known src A link-metering bias 2h 0.66 / 1h 1.19 e/t, deferred.
- model home 2h upgrade 16.19 e/t, 1h 13.22, storage_delta 2h -1.01 / 1h -2.35. W47 model 2h 17.13 / 1h 16.58, storage_delta 2h +1.55 / 1h +4.42.
- minerals hsO=17324 termO=126976 termK=172792 W47 termE=1096 termK=28960 wsK=64. labs OFF, do not enable, do not re-ask.

## Motion / CPU / infra
- creep_audit --patrol exit 2 known REGRESSION[deploy] vs ffdf767 (same class: defender.cpu, queen.trip_med, reserver.cpu/trip, rhauler.cpu, rminer.cpu/trip, upgrader.rp100/work_per_cpu, wfiller.cpu, wminer.rp100, wmminer.cpu, wrminer.cpu). Not shipped.
- motion 1h/2h --patrol exit 1 known waiting_pickup / target_full / parked_threat / queue_blocked / no_task / waiting_feed. w8filler ABA known target_full hub weave. miner84277567 excess 13.17 queue_blocked designed source-B replacement. w8rminer swamp is W47N7 source sit. No new stuck/oscillation after last deploy.
- CPU 1h avg 17.07 max 25.03@84277360 11:46 bucket 10000. 2h avg 17.51.
- Infra OK: postgres/grafana200/dashboard8787/q.py/DB writers fresh. grafana_check 20/20. peacetime single-slot 5:5:1:1 no yield. Box freezes 11:31-11:33 ~30t/130s, 11:40-11:43 ~50t/212s, 11:50-11:58 ~110t/467s, 12:05-12:22 ~240t/1010s. History backfill filled creep_ticks in those gaps except noted holes.
