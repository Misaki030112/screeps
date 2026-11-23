from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-24_0000")
STATE = Path("/workspace/screeps/state")
hk = ZoneInfo("Asia/Hong_Kong")
now = datetime.now(hk)
wrapped = now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
DIR.joinpath("wrapped_at.txt").write_text(str(int(now.timestamp())) + "\n")
DIR.joinpath("wrapped_at_human.txt").write_text(wrapped + "\n")
nl = "\n"

body = (
"quiet 30-min trajectory backfill _halfhour_2026-11-24_0000 OK (wrap " + wrapped + ", started_at 00:01:08). "
"Official history shard3 5 rooms ticks 84443501..84444200 (700, published_bases 84443500..84444100 at game.time=84444208; "
"first pass 33/35 official GETs 200, missing_chunks=2 W47N8@84443800, W47N7@84444100). "
"First pass started 00:03:12 finished 00:03:59 exit=0 inserted=7972 already_in_db=15450 ts_realigned=444; "
"tick_s printed 4.360 / first=4.36015; tick_s_check chose live-anchor-best all_mean 4.31524 "
"(first 4.36015 over45=0 mean_off=16.08; later_raw 4.30626 over45=0 mean_off=-5.52; all_mean 4.31524 over45=0 mean_off=-1.92; "
"prev_later 4.30282 is quiet 2330 tick_s_in_use, over45=0 mean_off=-6.90); "
"corrective_applied=False nfix=0 skipped_cross_chunk=0 at gt=84444234; tick_s_in_use=4.31524 (all_mean). "
"confirm 00:05:22 gt=84444237 recovered W47N7@84444100 inserted=318 (publish lag: first pass gt=84444208 was only 8 ticks past chunk close 84444200; confirm was 37 ticks past close) / "
"retry2 00:05:56 gt=84444245 inserted=54 / late 00:06:25 gt=84444252 inserted=54 / "
"postjp 00:18:00 gt=84444413 still_404=[W47N8@84443800, W47N7@84443300, W45N7@84441900, W47N7@84440900, W45N8@84439200, W45N8@84439300, W45N8@84439500, W47N7@84438700] inserted=54 "
"(613/1113/2513/3513/5213/5113/4913/5713 ticks past the bases at postjp; W47N8@84443800 is 513 ticks past chunk close 84443900, not mere publish lag, because the other four rooms on 84443800 already succeeded at the 2330 JP +140). "
"JP 84444200 GET 00:12:52 gt=84444341 all_five_200=False still_404=[W46N8@84444200] script=1657 actual=1462 "
"(W46N8 official 404; listener 0/100 ticks 84444201..84444300 before the first JP GET and still 0/100 through retry2; "
"the other four rooms recovered_or_ok at +140; script vs actual: W45N7 373/295, W47N7 404/287). "
"JP retry 00:17:11 gt=84444400 and retry2 00:24:23 gt=84444500 still_404=[W46N8@84444200] inserted=195+195 "
"(W45N7/W47N7 only; official W46N8 still 0). W46N8@84444200 is 300 ticks past the base / 200 past chunk close 84444300 at retry2, not mere publish lag, because the other four rooms on 84444200 already succeeded at +140. "
"Coverage official_recovered=3500/3500 empty_no_creep=0 official_404=0. "
"JP 84444200 is outside the 40-min window (TMAX=84444200), so the W46N8 official 404 does not reduce window coverage (all five 700/700). "
"W47N8@84443800 is in-window but listener already had 100/100 ticks 84443801..84443900 / 1208 rows, so it also does not reduce coverage (W47N8 700/700). "
"inserted_first=7972 confirm=318 retry2=54 late=54 postjp=54 just_actual=1462 total=9914. "
"NEW leftover official 404 W46N8@84444200 (first recorded as a just-published 404 in this 0000 half-hour; still 404 through JP retry +200 and retry2 +300 inserted=0 official; listener also 0/100, so this is a real trajectory hole just outside the window) is NOT YET TOLD. "
"Still-untold leftover official 404 W47N8@84443800 remains NOT YET TOLD from the quiet 2330 wrap; still in window start 84443501; retried, still 404; listener already 100/100; do not relabel NEW. "
"Already-told leftover official 404s W47N7@84443300 and W45N7@84441900 were told in the ~23:33 2321 USER_LOG; both aged out of window start 84443501; both retried, still 404; do not re-tell and do not relabel NEW. "
"Already-told leftovers W47N7@84440900, W45N8@84439200, W45N8@84439300, W45N8@84439500 and W47N7@84438700 remain still 404; do not re-tell and do not relabel NEW. "
"No new 盒子休眠 this pass after the last box_pauses row 22:59:15-23:05:47. "
"Already-told 盒子休眠 20:56:44-21:01:46, 21:21:51-21:28:39, 21:43:28-22:01:34, 22:23:02-22:35:40, and 22:59:15-23:05:47 "
"(official-filled W46N8/W47N8/W45N8/W45N7 199/199; W47N7 99/199 missing 84443301..84443400 due to leftover official 404 W47N7@84443300) "
"were told in the ~23:33 2321 USER_LOG; do not re-tell and do not relabel NEW. "
"Already-told 盒子休眠 18:16:12-18:35:22, 18:52:46-18:58:58, 19:21:55-19:34:51, and 20:14:37-20:28:31, plus 监听短中断 20:01:56, "
"were told in the ~20:44 2028 USER_LOG; do not re-tell and do not relabel NEW. "
"No new short listener WS ping/pong gap this pass after the already-told 20:01:56 shortws. "
"Services ok (postgres/grafana/listener). Single listener 3316604 since 23:06:00, yield_absent=True, no second slot, war_cmd/pulse not restarted. "
"Last delivered patrol is ~23:33 _patrol_2026-11-23_2321 USER_LOG finished_at 23:33:16; do not re-tell already-told 2321/2028/1728 leftovers/freezes. Quiet wrap only."
)

verify_body = (
"quiet 30-min trajectory backfill _halfhour_2026-11-24_0000 OK. "
"Official history shard3 5 rooms ticks 84443501..84444200 (700, published_bases 84443500..84444100 at game.time=84444208; "
"first pass 33/35 official GETs 200, missing_chunks=2 W47N8@84443800, W47N7@84444100). "
"First pass started 00:03:12 finished 00:03:59 exit=0 inserted=7972 already_in_db=15450 ts_realigned=444; "
"tick_s printed 4.360 / first=4.36015; tick_s_check chose live-anchor-best all_mean 4.31524 "
"(first 4.36015 over45=0 mean_off=16.08; later_raw 4.30626 over45=0 mean_off=-5.52; all_mean 4.31524 over45=0 mean_off=-1.92; "
"prev_later 4.30282 is quiet 2330 tick_s_in_use, over45=0 mean_off=-6.90); "
"corrective_applied=False nfix=0 skipped_cross_chunk=0 at gt=84444234; tick_s_in_use=4.31524 (all_mean). "
"confirm 00:05:22 gt=84444237 recovered W47N7@84444100 inserted=318 (publish lag) / retry2 00:05:56 gt=84444245 inserted=54 / "
"late 00:06:25 gt=84444252 inserted=54 / postjp 00:18:00 gt=84444413 still_404=[W47N8@84443800, W47N7@84443300, W45N7@84441900, W47N7@84440900, W45N8@84439200, W45N8@84439300, W45N8@84439500, W47N7@84438700] inserted=54. "
"JP 84444200 GET 00:12:52 gt=84444341 all_five_200=False still_404=[W46N8@84444200] script=1657 actual=1462 "
"(W46N8 official 404 and listener 0/100; other four rooms recovered at +140). "
"JP retry 00:17:11 gt=84444400 and retry2 00:24:23 gt=84444500 still_404=[W46N8@84444200] inserted=195+195; "
"300 ticks past the base / 200 past chunk close 84444300 at retry2, not mere publish lag. "
"Coverage official_recovered=3500/3500 empty_no_creep=0 official_404=0. "
"JP 84444200 is outside the 40-min window (TMAX=84444200), so W46N8 official 404 does not reduce window coverage (all five 700/700); listener also 0/100, so it is a real hole just outside the window. "
"W47N8@84443800 is in-window but listener 100/100, coverage not reduced. "
"inserted_first=7972 confirm=318 retry2=54 late=54 postjp=54 just_actual=1462 total=9914. "
"NEW leftover official 404 W46N8@84444200 is NOT YET TOLD. "
"Still-untold leftover official 404 W47N8@84443800 remains NOT YET TOLD from quiet 2330; still in window start 84443501; retried, still 404; listener already 100/100; do not relabel NEW. "
"Already-told leftovers W47N7@84443300 and W45N7@84441900 were told in the ~23:33 2321 USER_LOG; aged out of window start 84443501; retried, still 404; do not re-tell and do not relabel NEW. "
"Already-told leftovers W47N7@84440900, W45N8@84439200, W45N8@84439300, W45N8@84439500 and W47N7@84438700 remain still 404; do not re-tell and do not relabel NEW. "
"No new 盒子休眠 this pass after the last box_pauses row 22:59:15-23:05:47. "
"Already-told 盒子休眠 20:56:44-21:01:46, 21:21:51-21:28:39, 21:43:28-22:01:34, 22:23:02-22:35:40, and 22:59:15-23:05:47 were told in the ~23:33 2321 USER_LOG; do not re-tell and do not relabel NEW. "
"Already-told 盒子休眠 18:16:12-18:35:22 / 18:52:46-18:58:58 / 19:21:55-19:34:51 / 20:14:37-20:28:31 and 监听短中断 20:01:56 were told in the ~20:44 2028 USER_LOG; do not re-tell and do not relabel NEW. "
"No new short listener WS ping/pong gap this pass after the already-told 20:01:56 shortws. "
"Last USER_LOG is ~23:33 _patrol_2026-11-23_2321 finished_at 23:33:16; do not re-tell it. "
"This half-hour did not write a patrol or 12h-review folder and did not restart the listener, war_cmd, or pulse. "
"Single listener 3316604 since 23:06:00, yield_absent=True, no second slot. Quiet wrap only."
)

wrap = "---- wrap " + wrapped + " ----" + nl + body + nl
verify = "---- verify " + wrapped + " ----" + nl + verify_body + nl

(DIR / "_halfhour_backfill_now.txt").write_text(wrap)
(DIR / "history_backfill_now.txt").write_text(wrap)
(DIR / "_wrap_body.in.txt").write_text(wrap)
(DIR / "_halfhour_backfill_verify.txt").write_text(verify)
(DIR / "_verify_body.in.txt").write_text(verify)
(STATE / "_halfhour_backfill_now.txt").write_text(wrap)
(STATE / "_halfhour_backfill_verify.txt").write_text(verify)
print("wrapped_at", wrapped)
print("wrap_chars", len(wrap), "verify_chars", len(verify))
