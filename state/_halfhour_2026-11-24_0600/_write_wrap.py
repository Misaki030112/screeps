#!/usr/bin/env python3
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-24_0600")
STATE = Path("/workspace/screeps/state")
hk = ZoneInfo("Asia/Hong_Kong")
now = datetime.now(hk)
wrapped = now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
DIR.joinpath("wrapped_at.txt").write_text(str(int(now.timestamp())) + "\n")
DIR.joinpath("wrapped_at_human.txt").write_text(wrapped + "\n")
nl = "\n"

body = (
"quiet 30-min trajectory backfill _halfhour_2026-11-24_0600 OK (wrap " + wrapped + ", started_at 05:58:26). "
"Official history shard3 5 rooms ticks 84448501..84449100 (600, published_bases 84448500..84449100 at game.time=84449201; "
"first pass 28/35 official GETs 200, missing_chunks=7 W46N8@84448500, W45N8@84448600, and all five @84449100 (publish lag, recovered at JP), "
"inserted=5280 already_in_db=14469 ts_realigned=4783). "
"tick_s_in_use=4.39926 (first). "
"First pass started 06:00:55 finished 06:01:43 exit=0 inserted=5280 already_in_db=14469 ts_realigned=4783; "
"tick_s printed 4.399 / first=4.39926 (min-all 84448500..84448600); "
"tick_s_check chose live-anchor-best first 4.39926 "
"(first 4.39926 over45=313 mean_off=19.43; later_raw 4.29535 over45=4783 mean_off=-27.59; later_robust 4.29535 over45=4783 mean_off=-27.59; "
"all_mean 4.28837 over45=6689 mean_off=-30.75; span_mean 4.31055 over45=4783 mean_off=-20.71; "
"prev_later 4.40292 is quiet 0530 tick_s_in_use, over45=671 mean_off=21.08); "
"corrective_applied=True nfix=644 skipped_cross_chunk=0 at gt=84449241; after vs_first over45=0; tick_s_in_use=4.39926 (first). "
"confirm 06:04:06 gt=84449245 inserted=0 (all 19 leftover targets still 404) / "
"retry2 06:04:54 gt=84449256 inserted=0 / late 06:05:38 gt=84449266 inserted=0 / "
"postjp 06:07:18 gt=84449289 still_404=[W46N8@84448500, W45N8@84448600, W47N8@84448400, W47N8@84447700, W45N8@84447400, W47N7@84446600, W46N8@84445500, W45N7@84444900, W47N8@84445100, W46N8@84444500, W46N8@84444200, W47N8@84443800, W47N7@84443300, W45N7@84441900, W47N7@84440900, W45N8@84439200, W45N8@84439300, W45N8@84439500, W47N7@84438700] inserted=0. "
"W46N8@84448500 is 689 ticks past chunk close 84448600 at postjp; not mere publish lag, because the other four rooms on 84448500 already succeeded at the 0530 first pass; listener 50/100 ticks 84448501..84448550. "
"W45N8@84448600 is 589 ticks past chunk close 84448700 at postjp; not mere publish lag, because the other four rooms on 84448600 already succeeded at the 0530 first pass; listener 12/100 ticks 84448689..84448700. "
"W47N8@84448400 is 789 ticks past chunk close 84448500 at postjp; not mere publish lag, because the other four rooms on 84448400 already succeeded at the 0500 JP +141; listener 0/100 ticks 84448401..84448500; aged out of window start 84448501. "
"JP 84449100 GET 06:06:23 gt=84449276 all_five_200=True tool_inserted=3096 actual_rows=3096 actual_distinct=347 ticks 84449101..84449200 "
"(W46N8 distinct +41 / rows 465/465, W47N8 +100 / 1646/1646, W45N8 +100 / 725/725, W45N7 +6 / 17/17 official mostly empty_no_creep, W47N7 +100 / 243/243). "
"No JP retry (no remaining 404). "
"Coverage official_recovered=2571/3000 empty_no_creep=291 official_404=138. "
"W47N8 is 600/600. W47N7 is 600/600. "
"W45N7 is 309/600 with official empty_no_creep 84448791..84449077 and 84449097..84449100 (291t; official 200, not a 404). "
"W46N8 is 550/600 missing 84448551..84448600 due to leftover official 404 W46N8@84448500 (listener already 50/100 on 84448501..84448550). "
"W45N8 is 512/600 missing 84448601..84448688 due to leftover official 404 W45N8@84448600 (listener already 12/100 on 84448689..84448700). "
"JP 84449100 is outside the 40-min window (TMAX=84449100). "
"inserted_first=5280 confirm=0 retry2=0 late=0 postjp=0 just_actual=347 total=5627. "
"No NEW leftover official 404 this 0600 pass (the all-five first-pass 404 on 84449100 was publish lag at gt=84449201, only +101 past the base, and was recovered at JP all_five_200). "
"Already-told leftover official 404s W46N8@84448500 and W45N8@84448600 were told in the ~05:38 0522 USER_LOG; still in window start 84448501; retried through confirm/retry2/late/postjp, still 404 official inserted=0; listener 50/100 and 12/100 respectively; do not re-tell and do not relabel NEW. "
"Already-told leftover official 404s W47N8@84448400, W47N8@84447700, W45N8@84447400, and W47N7@84446600 were told in the ~05:38 0522 USER_LOG; all aged out of window start 84448501; retried through confirm/retry2/late/postjp, still 404 official inserted=0; do not re-tell and do not relabel NEW. "
"Already-told leftover official 404s W46N8@84445500, W45N7@84444900, W47N8@84445100, W46N8@84444500, W46N8@84444200, and W47N8@84443800 were told in the ~02:34 0221 USER_LOG; all aged out of window start 84448501; retried, still 404; W46N8@84445500 listener already 100/100 and W47N8@84443800 listener already 100/100 are not trajectory holes; do not re-tell and do not relabel NEW. "
"Already-told leftover official 404s W47N7@84443300 and W45N7@84441900 were told in the ~23:33 2321 USER_LOG; both aged out of window start 84448501; retried, still 404; do not re-tell and do not relabel NEW. "
"Already-told leftover official 404s W47N7@84440900, W45N8@84439200, W45N8@84439300, W45N8@84439500, and W47N7@84438700 were told in the ~20:44 2028 USER_LOG; all aged out; retried, still 404; do not re-tell and do not relabel NEW. "
"NEW 盒子休眠 05:51:59-05:56:28 (261s, already healed; official-filled W46N8/W47N8/W45N8/W47N7 79/79, W45N7 19/79 with official empty_no_creep on the remaining 60t 84449071..84449077 and 84449097..84449149, official 200 on 84449000 and JP 84449100, not a 404; STATS 84449071..84449149 still 0/79 because official history does not recover room_stats; box_pauses row present; errors.log box frozen ~261s; listener auto-restarted 05:56:31, python 3508501 started 05:56:40, parent 4035476) is NOT YET TOLD. "
"Already-told 盒子休眠 04:51:47-05:01:57, 04:18:52-04:32:23, 03:49:23-04:01:11, and 03:21:51-03:31:05, plus 监听短中断 02:57:18, were told in the ~05:38 0522 USER_LOG; do not re-tell and do not relabel NEW. "
"Already-told 盒子休眠 02:03:03-02:21:36 was told in the ~02:34 0221 USER_LOG (1108s, official-filled all five 269/269 STATS 84445891..84446159); do not re-tell and do not relabel NEW. "
"Already-told 监听短中断 00:34:41 and 01:02:38 (plus 01:04:10 ping/pong) were told in the ~02:34 0221 USER_LOG; do not re-tell and do not relabel NEW. "
"Already-told 盒子休眠 20:56:44-21:01:46, 21:21:51-21:28:39, 21:43:28-22:01:34, 22:23:02-22:35:40, and 22:59:15-23:05:47 were told in the ~23:33 2321 USER_LOG; do not re-tell and do not relabel NEW. "
"Already-told 盒子休眠 18:16:12-18:35:22, 18:52:46-18:58:58, 19:21:55-19:34:51, and 20:14:37-20:28:31, plus 监听短中断 20:01:56, were told in the ~20:44 2028 USER_LOG; do not re-tell and do not relabel NEW. "
"Services ok (postgres/grafana/listener). Single listener 3508501 since 05:56:40, yield_absent=True, no second slot, war_cmd/pulse not restarted. "
"Last delivered patrol is ~05:38 _patrol_2026-11-24_0522 USER_LOG finished_at 05:38:12; do not re-tell already-told 0522/0221/2321/2028 leftovers/freezes. Quiet wrap only."
)

verify = (
"quiet 30-min trajectory backfill _halfhour_2026-11-24_0600 OK (wrap " + wrapped + ", started_at 05:58:26). "
"Official history shard3 5 rooms ticks 84448501..84449100 (600, published_bases 84448500..84449100 at game.time=84449201; "
"first pass 28/35 200, missing_chunks=7 W46N8@84448500, W45N8@84448600, and all five @84449100 publish lag recovered at JP, "
"inserted=5280 already_in_db=14469 ts_realigned=4783). "
"tick_s_in_use=4.39926 (first; first 4.39926 over45=313 then corrective nfix=644 over45=0; later_raw 4.29535 over45=4783; prev_later 4.40292 from quiet 0530; corrective_applied=True nfix=644 at gt=84449241). "
"confirm/retry2/late/postjp inserted=0, still_404 includes already-told W46N8@84448500 (689 ticks past chunk close 84448600 at postjp gt=84449289; listener 50/100; still in window start 84448501) and already-told W45N8@84448600 (589 ticks past chunk close 84448700; listener 12/100; still in window). "
"Already-told W47N8@84448400, W47N8@84447700, W45N8@84447400, and W47N7@84446600 remain aged out of window start 84448501. "
"JP 84449100 GET 06:06:23 gt=84449276 all_five_200=True tool_inserted=3096 actual_rows=3096 actual_distinct=347 "
"(W46N8 41/465, W47N8 100/1646, W45N8 100/725, W45N7 6/17 empty_no_creep, W47N7 100/243). No JP retry. "
"Coverage official_recovered=2571/3000 empty_no_creep=291 official_404=138. "
"W47N8 600/600; W47N7 600/600; W45N7 309/600 empty 84448791..84449077 and 84449097..84449100; W46N8 550/600 missing 84448551..84448600; W45N8 512/600 missing 84448601..84448688. "
"inserted_first=5280 confirm=0 retry2=0 late=0 postjp=0 just_actual=347 total=5627. "
"No NEW leftover official 404 this 0600 pass. "
"NEW 盒子休眠 05:51:59-05:56:28 is NOT YET TOLD (261s, already healed; official-filled W46N8/W47N8/W45N8/W47N7 79/79, W45N7 19/79 official empty_no_creep on the remaining 60t; STATS 84449071..84449149; listener 3508501 since 05:56:40). "
"Already-told 0522 leftovers W46N8@84448500, W45N8@84448600, W47N8@84448400, W47N8@84447700, W45N8@84447400, W47N7@84446600 and already-told 盒子休眠 04:51:47-05:01:57 / 04:18:52-04:32:23 / 03:49:23-04:01:11 / 03:21:51-03:31:05 plus 监听短中断 02:57:18 must not be re-told or relabeled NEW. "
"Last delivered patrol is ~05:38 0522 finished_at 05:38:12; already-told 0522/0221/2321/2028 leftovers/freezes must not be re-told. "
"Services ok. Single listener 3508501 since 05:56:40, yield_absent=True, no second slot, war_cmd/pulse not restarted. Quiet wrap only."
)

header = "---- wrap " + wrapped + " ----" + nl
now_txt = header + body + nl
verify_txt = header + verify + nl
for path in (DIR / "_halfhour_backfill_now.txt", STATE / "_halfhour_backfill_now.txt"):
    path.write_text(now_txt)
for path in (DIR / "_halfhour_backfill_verify.txt", STATE / "_halfhour_backfill_verify.txt"):
    path.write_text(verify_txt)
(DIR / "_wrap_body.in.txt").write_text(now_txt)
print("wrote wrap", wrapped)
print("now bytes", len(now_txt), "verify bytes", len(verify_txt))
