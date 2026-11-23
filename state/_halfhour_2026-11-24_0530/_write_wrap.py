#!/usr/bin/env python3
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-24_0530")
STATE = Path("/workspace/screeps/state")
hk = ZoneInfo("Asia/Hong_Kong")
now = datetime.now(hk)
wrapped = now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
DIR.joinpath("wrapped_at.txt").write_text(str(int(now.timestamp())) + "\n")
DIR.joinpath("wrapped_at_human.txt").write_text(wrapped + "\n")
nl = "\n"

body = (
"quiet 30-min trajectory backfill _halfhour_2026-11-24_0530 OK (wrap " + wrapped + ", started_at 03:32:53). "
"Official history shard3 5 rooms ticks 84446401..84447100 (700, published_bases 84446400..84447000 at game.time=84447182; "
"first pass 34/35 official GETs 200, missing_chunks=1 W47N7@84446600, inserted=8279 already_in_db=14810 ts_realigned=213). "
"tick_s_in_use=4.27706 (prev_later). "
"First pass started 03:35:11 finished 03:35:58 exit=0 inserted=8279 already_in_db=14810 ts_realigned=213; "
"tick_s printed 4.273 / first=4.27265 (min-all 84446400..84446500); "
"tick_s_check chose live-anchor-best prev_later 4.27706 "
"(first 4.27265 over45=0 mean_off=-9.92; later_raw 4.32115 over45=57 mean_off=12.46; all_mean 4.31307 over45=34 mean_off=8.73; "
"span_mean 4.31307 over45=34 mean_off=8.73; prev_later 4.27706 is quiet 0300 tick_s_in_use, over45=0 mean_off=-7.88); "
"corrective_applied=False nfix=0 skipped_cross_chunk=0 at gt=84447218; tick_s_in_use=4.27706 (prev_later). "
"confirm 03:38:03 gt=84447222 inserted=0 (all 14 leftover targets still 404) / "
"retry2 03:38:45 gt=84447232 inserted=0 / late 03:39:21 gt=84447241 inserted=0 / "
"postjp 03:40:58 gt=84447263 still_404=[W47N7@84446600, W46N8@84445500, W45N7@84444900, W47N8@84445100, W46N8@84444500, W46N8@84444200, W47N8@84443800, W47N7@84443300, W45N7@84441900, W47N7@84440900, W45N8@84439200, W45N8@84439300, W45N8@84439500, W47N7@84438700] inserted=0. "
"W47N7@84446600 is 563 ticks past chunk close 84446700 at postjp; not mere publish lag, because the other four rooms on 84446600 already succeeded at the 0300 confirm or this first pass; listener 0/100 ticks 84446601..84446700. "
"JP 84447100 GET 03:40:13 gt=84447253 all_five_200=True script=2648 actual=2611 "
"(script vs actual: W46N8 811/811, W47N8 424/424, W45N8 579/544, W45N7 416/416, W47N7 418/416). "
"No JP retry (no remaining 404). "
"Coverage official_recovered=3400/3500 empty_no_creep=0 official_404=100. "
"W46N8/W47N8/W45N8/W45N7 are 700/700. "
"W47N7 is 600/700 missing 84446601..84446700 due to leftover official 404 W47N7@84446600. "
"JP 84447100 is outside the 40-min window (TMAX=84447100). "
"inserted_first=8279 confirm=0 retry2=0 late=0 postjp=0 just_actual=2611 total=10890. "
"Still-untold leftover official 404 W47N7@84446600 remains NOT YET TOLD from the quiet 0300 wrap; still in window start 84446401; retried through confirm/retry2/late/postjp, still 404 official inserted=0; listener also 0/100 ticks 84446601..84446700; 563 ticks past chunk close 84446700 at postjp, not mere publish lag; reduces this window W47N7 600/700; do not relabel NEW. "
"Already-told leftover official 404s W46N8@84445500, W45N7@84444900, W47N8@84445100, W46N8@84444500, W46N8@84444200, and W47N8@84443800 were told in the ~02:34 0221 USER_LOG; all aged out of window start 84446401; retried, still 404; W46N8@84445500 listener already 100/100 and W47N8@84443800 listener already 100/100 are not trajectory holes; do not re-tell and do not relabel NEW. "
"Already-told leftover official 404s W47N7@84443300 and W45N7@84441900 were told in the ~23:33 2321 USER_LOG; both aged out of window start 84446401; retried, still 404; do not re-tell and do not relabel NEW. "
"Already-told leftover official 404s W47N7@84440900, W45N8@84439200, W45N8@84439300, W45N8@84439500, and W47N7@84438700 were told in the ~20:44 2028 USER_LOG; all aged out; retried, still 404; do not re-tell and do not relabel NEW. "
"NEW 盒子休眠 03:21:51-03:31:05 (553s, already healed; official-filled all five 139/139 STATS 84446991..84447129 after first pass plus JP 84447100; box_pauses row present; errors.log box frozen ~553s; listener auto-restarted 03:31:08, python 3445130 started 03:31:17, parent 4035476) is NOT YET TOLD. "
"Still-untold 监听短中断 02:57:18 remains NOT YET TOLD from the quiet 0300 wrap (errors.log ws error ping/pong timed out; no box_pauses row and no box-frozen line; listener auto-restarted 02:57:21, python 3431965 started 02:57:31, parent 4035476; STATS gap 84446631..84446659 29t; official-filled W46N8/W47N8/W45N8/W45N7 29/29; W47N7 0/29 missing 84446631..84446659 due to leftover official 404 W47N7@84446600); do not relabel NEW. "
"Already-told 盒子休眠 02:03:03-02:21:36 was told in the ~02:34 0221 USER_LOG (1108s, official-filled all five 269/269 STATS 84445891..84446159); do not re-tell and do not relabel NEW. "
"Already-told 监听短中断 00:34:41 and 01:02:38 (plus 01:04:10 ping/pong) were told in the ~02:34 0221 USER_LOG; do not re-tell and do not relabel NEW. "
"Already-told 盒子休眠 20:56:44-21:01:46, 21:21:51-21:28:39, 21:43:28-22:01:34, 22:23:02-22:35:40, and 22:59:15-23:05:47 (official-filled W46N8/W47N8/W45N8/W45N7 199/199; W47N7 99/199 missing 84443301..84443400 due to leftover official 404 W47N7@84443300) were told in the ~23:33 2321 USER_LOG; do not re-tell and do not relabel NEW. "
"Already-told 盒子休眠 18:16:12-18:35:22, 18:52:46-18:58:58, 19:21:55-19:34:51, and 20:14:37-20:28:31, plus 监听短中断 20:01:56, were told in the ~20:44 2028 USER_LOG; do not re-tell and do not relabel NEW. "
"Services ok (postgres/grafana/listener). Single listener 3445130 since 03:31:17, yield_absent=True, no second slot, war_cmd/pulse not restarted. "
"Last delivered patrol is ~02:34 _patrol_2026-11-24_0221 USER_LOG finished_at 02:34:33; do not re-tell already-told 0221/2321/2028 leftovers/freezes. Quiet wrap only."
)

verify = (
"quiet 30-min trajectory backfill _halfhour_2026-11-24_0530 OK (wrap " + wrapped + ", started_at 03:32:53). "
"Official history shard3 5 rooms ticks 84446401..84447100 (700, published_bases 84446400..84447000 at game.time=84447182; "
"first pass 34/35 200, missing_chunks=1 W47N7@84446600, inserted=8279 already_in_db=14810 ts_realigned=213). "
"tick_s_in_use=4.27706 (prev_later from quiet 0300; first 4.27265 over45=0; later_raw 4.32115 over45=57; corrective_applied=False nfix=0 at gt=84447218). "
"confirm/retry2/late/postjp inserted=0, still_404 includes leftover W47N7@84446600 (563 ticks past chunk close 84446700 at postjp gt=84447263; listener 0/100; not mere publish lag). "
"JP 84447100 GET 03:40:13 gt=84447253 all_five_200=True script=2648 actual=2611 (W46N8 811/811, W47N8 424/424, W45N8 579/544, W45N7 416/416, W47N7 418/416). No JP retry. "
"Coverage official_recovered=3400/3500 empty_no_creep=0 official_404=100. W46N8/W47N8/W45N8/W45N7 700/700; W47N7 600/700 missing 84446601..84446700. "
"inserted_first=8279 confirm=0 retry2=0 late=0 postjp=0 just_actual=2611 total=10890. "
"NEW 盒子休眠 03:21:51-03:31:05 (553s, already healed; official-filled all five 139/139 STATS 84446991..84447129) is NOT YET TOLD. "
"Still-untold leftover official 404 W47N7@84446600 and 监听短中断 02:57:18 remain NOT YET TOLD from quiet 0300; do not relabel NEW. "
"Last delivered patrol is ~02:34 0221; already-told 0221/2321/2028 leftovers/freezes must not be re-told. "
"Services ok. Single listener 3445130 since 03:31:17, yield_absent=True, no second slot, war_cmd/pulse not restarted. Quiet wrap only."
)

header = "---- wrap " + wrapped + " ----" + nl
now_txt = header + body + nl
ver_txt = header + verify + nl
for path in (DIR / "_halfhour_backfill_now.txt", STATE / "_halfhour_backfill_now.txt"):
    path.write_text(now_txt)
for path in (DIR / "_halfhour_backfill_verify.txt", STATE / "_halfhour_backfill_verify.txt"):
    path.write_text(ver_txt)
(DIR / "_wrap_body.in.txt").write_text(now_txt)
print("wrapped_at", wrapped)
print("now_bytes", len(now_txt), "verify_bytes", len(ver_txt))
