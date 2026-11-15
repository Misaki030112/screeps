# Patrol slice 2026-11-15 08:2x–19:24 Asia/Hong_Kong (from iterations.log)

## 08:2x REVIEW (610 chars)
- lead: 2026-11-15 08:2x Asia/Hong_Kong 12h review: PLAN HOLDS, docs only, no game deploy. LIVE ffdf767 held (@84268045 / 00:27; already-live ops ship, not this review). Home 61.54% 18.67 e/t (was 14.87) RCL8~11.6d at this pace, 20k gate held (max 18946, zero ≥20k samples), under-15k 28.3% (was 39.0%), min 9775, live ~18.9–19.0k why=ok nUp=2. W47 32.73% 19
- handoff: nUp=2. W47 32.73% 19.20 e/t (was 19.36) keep=2, stor live ~35k closest yet to 40k lat
- soft: 40k latch (max 35385, 0% ≥40k), softCap2 on from 07:27 threatSoft leftover (sL=0)
- soft: 40k latch.

## 08:28 PATROL (3153 chars)
- ALERT: FORMAL ALERT (a) holds on W47: exact2h 18.
- ALERT: FORMAL ALERT (a) CLEARS on home: exact2h 20.
- ALERT: FORMAL ALERT (b) RESET at analysis tip 18892 ABOVE consec-under=0 (prev tip 14914 UNDER consec-under=1);
- core/inv: W47N7 Invader core inc=84273302 KILLED 84273674 07:27 why=killed dur=372 (last patrol 7000 hits@84273664 ETA ~9-10t, matched)
- stor: W47 stor min 24187@84273600 07:22 max 34965@tip later 35385-36878@84274510-84274540, bankWhy=threatSoft softCap2=1 threatSoft=1 (w8threat=84273147 age=1388@84274535 WINDOW=1500 expires 842
- handoff: keep=2 designed 20 e/t=66.5% already under the 70% bar
- handoff: handoff softness has recovered to a solid 20.00 all short windows
- handoff: keep=2
- freeze: freeze not used alone
- freeze: freeze then stayed ABOVE
- soft: threatSoft/evac/handoff softness has recovered to a solid 20.00 all short windows
- soft: 20k/300t not hit (3h max 18892 later 18992, best>=20k span=0)
- soft: threatSoft softCap2=1 threatSoft=1 (w8threat=84273147 age=1388@84274535 WINDOW=1500 expire

## 09:28 REVIEW (6790 chars)
- ALERT: FORMAL ALERT (a) holds on W47: exact2h 19.
- ALERT: FORMAL ALERT (b) stays RESET at analysis tip 17532 ABOVE consec-under=0 (prev tip 18892 ABOVE consec-under=0);
- core/inv: W47N7 core inc=84273302 cleared 84273674 07:27 expired 84274647 ~08:36 as designed
- stor: W47 stor min 28236@tip later 27936@84275390 / 27336@84275400 09:28 max 38466@84274670 08:37 (closest yet to the 40k/500t lock, prior high 36878 last hour / 35385 12h review
- stor: W47 stor min 28236 max 38466 live later 27336 keep=2 phase=ready bankWhy=ready leanBank=0 threatSoft=0 softCap2=0 sealPark off sealMinE=25000 hubLink=1 feedOk=1 upLatched=0 softLeft=0
- handoff: keep=2 designed
- handoff: w8up 2→3@84274690 08:38 →2@84274790 08:45 handoff plus two box-sleep gaps)
- handoff: keep=2 designed 20 e/t=66.5% already under the 70% bar
- freeze: freeze then designed handoff (upgrader84273906 ttl~85 + upgrader84275355 spawning at t
- freeze: freeze to 32103@09:04 then 28236@09:24 (model 1h storage_delta -10.17 e/t)
- soft: 20k/300t not hit (3h max 18992, best>=20k span=0)
- soft: 40k/500t lock, prior high 36878 last hour / 35385 12h review
- soft: 40k, best>=40k span=0, not a latch)

## 10:25 PATROL (2917 chars)
- ALERT: FORMAL ALERT (a) holds on W47: exact2h 19.
- ALERT: FORMAL ALERT (b) stays RESET at analysis tip 16974 ABOVE consec-under=0 (prev tip 17532 ABOVE consec-under=0);
- stor: W47 stor since_last min 22082@84275510 09:36 max 28236@84275360 09:25 (last tip) tip 25180 later 24780-25070@84276160-84276200
- handoff: keep=2 design 20.00=66.5% span=70-200
- handoff: keep=2 designed 20 e/t=66.5% already under the 70% bar
- handoff: keep=2
- soft: 20k/300t not hit (3h max 18992, best>=20k span=0)
- soft: 40k, not a latch)
- soft: softCap2=0 threatSoft=0 sealPark=1 (known, updateSealPark clears only at nUp>=3, deferre

## 11:26 PATROL (6585 chars)
- ALERT: FORMAL ALERT (a) holds on W47: exact2h 18.
- ALERT: FORMAL ALERT (b) stays RESET at analysis tip 18036 ABOVE consec-under=0 (prev tip 16974 ABOVE consec-under=0);
- stor: W47 stor since_last min 24073@84276990 11:20 (thaw dip) max 28194@84276780 11:05 tip 25223 later 25223
- stor: W47 stor min 24073 max 28194 live later 25223 keep=2 phase=ready bankWhy=ready leanBank=0 threatSoft=0 softCap2=0 sealPark on sealMinE=25000 hubLink=1 feedOk=1 upLatched=0 softLeft=0
- handoff: keep=2 designed
- handoff: keep=2 plus two long freezes)
- handoff: keep=2 designed 20 e/t=66.5% already under the 70% bar
- freeze: freeze not used alone
- freeze: freezes)
- soft: 20k/300t not hit (3h max 18992@84274510 08:26, best>=20k span=0)
- soft: 40k, not a latch)
- soft: softCap2=0 threatSoft=0 (w8threat stamp 84273147 is expired residue, WINDOW=1500 ended 0

## 12:26 PATROL (5448 chars)
- ALERT: FORMAL ALERT (a) holds on W47: exact2h 17.
- ALERT: FORMAL ALERT (b) not fired: analysis tip 14162 UNDER consec-under=1 (prev tip 18036 ABOVE consec-under=0);
- stor: W47 stor since_last min 24147@84277240 11:38 max 28932@tip later 29902@84277960 / 29552@84277970
- stor: W47 stor min 24147 max 28932 live later 29552–29902 keep=2 phase=ready bankWhy=ready leanBank=0 threatSoft=0 softCap2=0 sealPark off sealMinE=25000 hubLink=1 feedOk=1 upLatched=0 softLeft=
- handoff: keep=2 20 e/t=66.5%
- handoff: w8up 2→3@84277570 12:01 handoff →2@84277880 12:23 with waiting_feed on newborns
- handoff: keep=2 designed 20 e/t=66.5% already under the 70% bar
- freeze: freeze not used alone
- freeze: box freezes 11:31-11:33 ~30t/130s, 11:40-11:43 ~50t/212s, 11:50-11:58 ~110t/467s, 12:05-12:22 ~240t/1010s (this wake, listener restart 12:21:51)
- soft: 40k/500t lock
- soft: 20k/300t not hit (3h max 18778@84276760 11:04, 18992@08:26 aged out, best>=20k span=0)
- soft: 40k, not a latch

## 13:31 PATROL (6413 chars)
- ALERT: FORMAL ALERT (a) FIRES on home: exact2h 11.
- ALERT: FORMAL ALERT (a) CLEARS on W47: exact2h 19.
- ALERT: FORMAL ALERT (b) RESET at analysis tip 16747 ABOVE consec-under=0 (prev tip 14162 UNDER consec-under=1);
- stor: W47 stor since_last min 26901@84278710 13:22 max 32486@84278240 12:48 tip 27751 later 27751@84278820 / 27847@84278830-84278840
- stor: W47 stor min 26901 max 32486 live later 27847 keep=2 phase=ready bankWhy=threatSoft leanBank=0 threatSoft=1 softCap2=1 sealPark on sealMinE=25000 hubLink=1 feedOk=1 upLatched=0 softLeft=0
- handoff: nUp=1@84277930 stor 14162 why=floor_bank → brief 2@84278230 12:47 stor 11927 (handoff
- handoff: keep=2 design 20.00=66.5% span=20-30
- handoff: keep=2 designed, do not revert or add a third until 40k/500t lock
- freeze: freeze not used alone
- freeze: freeze not used alone
- soft: 40k/500t lock
- soft: 20k/300t not hit (3h max 18778@84276760 11:04, best>=20k span=0)
- soft: 40k, not a latch

## 14:31 PATROL (6389 chars)
- ALERT: FORMAL ALERT (a) HOLDS on home: exact2h 12.
- ALERT: FORMAL ALERT (b) stays RESET at analysis tip 17291 ABOVE consec-under=0 (prev tip 16747 ABOVE consec-under=0);
- stor: W47 stor since_last min 24488@tip max 32083@84278930 13:37 later 25127@84279650-84279680 then 24127@84279690-84279700 after the core-breaker spawn+refill
- stor: W47 stor min 24488 max 32083 live later 24127 keep=2 phase=ready bankWhy=ready leanBank=0 threatSoft=0 softCap2=0 sealPark on sealMinE=25000 hubLink=1 feedOk=1 upLatched=0 softLeft=873
- handoff: nUp=1@84278810 stor 16747 why=floor_bank through almost the hour → 2@84279630 14:26 s
- handoff: keep=2 designed 20 e/t=66.5%
- handoff: keep=2 designed, do not revert or add a third until 40k/500t lock
- freeze: freeze not used alone
- freeze: freeze not used alone
- soft: 40k/500t lock
- soft: 20k/300t not hit (3h max now 17291@tip, 18778@11:04 aged out, best>=20k span=0)
- soft: 40k, not a latch

## 15:31 PATROL (6344 chars)
- ALERT: FORMAL ALERT (a) FIRES on W47: exact2h 20.
- ALERT: FORMAL ALERT (b) not formal: analysis tip 14447 UNDER consec-under=1 (prev tip 17291 ABOVE consec-under=0);
- stor: W47 stor since_last min 24104@84279790 14:38 max 25595@84279810 14:39 later 25020@tip then 25346@84280510 / 26739@84280530 / 27239@84280540-84280550
- stor: W47 stor min 24104 max 25595 live later 27239 keep=2 phase=ready bankWhy=ready leanBank=0 threatSoft=0 softCap2=0 sealPark off sealMinE=25000 hubLink=1 feedOk=1 upLatched=0 softLeft=0
- handoff: keep=2 20 e/t=66.5%
- handoff: keep=2 designed, do not revert or add a third until 40k/500t lock
- handoff: w8up 2→3@84280460 15:24:56 handoff (84279001 ttl dying + 84280440 arriving) →2@84280540 15:30:31
- freeze: freeze not used alone 16.67=55.4%
- freeze: freeze 22.20=85.4% / last20 19.30=74.2% also not soft)
- soft: 40k/500t lock
- soft: 20k/300t not hit (3h max still 17781@84279700, best>=20k span=0)
- soft: 40k, not a latch

## 16:31 PATROL (6579 chars)
- ALERT: FORMAL ALERT (a) HOLDS on W47: exact2h 19.
- ALERT: FORMAL ALERT (b) RESET at analysis tip 17638 ABOVE consec-under=0 (prev tip 14447 UNDER consec-under=1);
- stor: W47 stor since_last min 23858@84281340 16:26 max 30264@84280690 15:40 later 25291@tip then 25791@84281390-84281410 16:31
- stor: W47 stor min 23858 max 30264 live later 25791 keep=2 phase=ready bankWhy=ready leanBank=0 threatSoft=0 softCap2=0 sealPark designed around sealMinE=25000 hubLink=1 feedOk=1 upLatched=0 sof
- handoff: keep=2 20 e/t=66.5%
- handoff: handoff ran ~10 e/t with waiting_feed on w8upgrader84280440/84279001
- handoff: keep=2 designed, do not revert or add a third until 40k/500t lock
- freeze: freeze not used alone 20.30=67.5%
- freeze: freeze gaps the rate is designed 20, later 16:30-16:31 24-26)
- soft: 40k/500t lock
- soft: 20k/300t not hit (3h max still 17781@84279700 14:31, best>=20k span=0)
- soft: 40k, not a latch

## 17:31 PATROL (6885 chars)
- ALERT: FORMAL ALERT (a) HOLDS on W47: exact2h 17.
- ALERT: FORMAL ALERT (b) stays RESET at analysis tip 16318 ABOVE consec-under=0 (prev tip 17638 ABOVE consec-under=0);
- core/inv: W47N7 core, not new stuck
- stor: W47 stor since_last min 22111@84281910 17:06:29 max 27804@tip later 28552@84282230-84282240 / 29302@84282250 17:30
- stor: W47 stor min 22111 max 27804 live later 29302 keep=2 phase=ready bankWhy=ready leanBank=0 threatSoft=0 softCap2=0 sealPark designed around sealMinE=25000 hubLink=1 feedOk=1 upLatched=0 sof
- handoff: keep=2 20 e/t=66.5%
- handoff: handoff: w8up 2→3@84281890 17:05:06 (w8upgrader84281887 spawn) then w8upgrader84280440 left the 14,26 stand empty@84281941 and died ~84281978 walki
- handoff: w8upgrader84280653 kept working at ~10 e/t
- freeze: freeze not used alone 6.67-10.00
- freeze: freeze 28.00=107.7% also not soft)
- soft: 40k/500t lock
- soft: 20k/300t not hit (3h max 17948@84281840, best>=20k span=0)
- soft: 40k, not a latch

## 18:26 PATROL (6934 chars)
- ALERT: FORMAL ALERT (a) HOLDS on W47: exact2h 17.
- ALERT: FORMAL ALERT (b) stays RESET at analysis tip 19659 ABOVE consec-under=0 (prev tip 16318 ABOVE consec-under=0);
- stor: W47 stor since_last min 27804@84282210 17:27:41 max 39332@84282960 18:20:52 tip 38632 later 38032@84282990 / 37582@84283020 / 37082@84283030-84283038
- stor: W47 stor min 27804 max 39332 live later 37082 keep=2 phase=ready bankWhy=ready leanBank=0 threatSoft=0 softCap2=0 sealPark=0 hubLink=1 feedOk=1 upLatched=0 softLeft=0
- handoff: keep=2 20 e/t=66.5%
- handoff: handoff tail continued: w8upgrader84281887 first loaded 12,25@84282170 17:24 after ~223t hub waiting_feed, but w8upgrader84282092 spawned@84282094 
- handoff: keep=2 designed 20 e/t=66.5% already under the 70% bar
- freeze: freeze not used alone 20.00=66.5%
- freeze: freeze
- soft: 40k/500t lock
- soft: 20k/300t not hit (just recrossed at 18:25, 3h max now 20259@later, best>=20k span ~16t s
- soft: 40k, not a latch

## 19:24 PATROL (5151 chars)
- ALERT: FORMAL ALERT (a) CLEARED on W47: exact2h 17.
- ALERT: FORMAL ALERT (b) stays RESET at analysis tip 15093 ABOVE consec-under=0 (prev tip 19659 ABOVE consec-under=0);
- stor: W47 stor since_last min 30978@84283350 18:48:20 max 38632@84282980 (prev tip) later 32058@tip / 31958@84283810 / 31608@84283822-84283850
- stor: W47 stor dropped around the spawn/refill (home 20459→14859, W47 37082→30978)
- stor: home stor E17361 O17324 term K172792 O126976, W47 stor E31608 K64 term E1096 K33708
- handoff: keep=2 designed 20 e/t=66.5% plus w8builder84282432 dwelling at 15,26 from ~84283266 1
- handoff: w8up 2@84282980 →3@84283330 18:46:59 handoff (w8upgrader84283326 spawn, seated 14,27) →2@84283490 18:58:
- handoff: w8upgrader84281887 ttl (last 12,25 then walked out 84283425) →3@84283540 19:01:42 handoff (w8upgrader842
- freeze: freeze not used alone 26.00=86.4%
- freeze: freeze also 14.00 not used alone
- soft: 40k/500t lock
- soft: 20k/300t not hit (3h max 20459@84283060, best>=20k span=50)
- soft: 40k, not a latch
