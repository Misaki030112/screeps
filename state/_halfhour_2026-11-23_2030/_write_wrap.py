#!/usr/bin/env python3
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-23_2030")
STATE = Path("/workspace/screeps/state")
HK = ZoneInfo("Asia/Hong_Kong")
now = datetime.now(HK)
wrapped = now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
nl = chr(10)
DIR.joinpath("wrapped_at.txt").write_text(str(int(now.timestamp())) + nl)
DIR.joinpath("wrapped_at_human.txt").write_text(wrapped + nl)

wrap = nl.join([
"---- wrap " + wrapped + " ----",
(
"confirm at 2026-11-23 19:41:42 Asia/Hong_Kong recovered=['W47N7@84440400'] still_404=[W45N8@84439200, W45N8@84439300, W45N8@84439500, W47N7@84438700] inserted=6 "
"(gt=84440544; W47N7@84440400 was a first-pass in-window 404 at game.time=84440511, only 111 ticks past the base, recovered on confirm as publish lag, not a leftover; "
"W45N8@84439200 1344 ticks past the base, W45N8@84439300 1244, W45N8@84439500 1044, W47N7@84438700 1844; not mere publish lag). "
"retry2 at 2026-11-23 19:41:50 Asia/Hong_Kong still_404=[W45N8@84439200, W45N8@84439300, W45N8@84439500, W47N7@84438700] inserted=0 (gt=84440546; "
"transient RemoteDisconnected on W45N8@84439200 attempt 1, then still_404). "
"late retry at 2026-11-23 19:42:09 Asia/Hong_Kong still_404=[W45N8@84439200, W45N8@84439300, W45N8@84439500, W47N7@84438700] inserted=0 (gt=84440551). "
"First pass --minutes 40. First pass 34/35 official GETs 200, missing_chunks=1 (W47N7@84440400, later recovered on confirm). "
"First pass started 2026-11-23 19:39:19 Asia/Hong_Kong and finished 19:40:08 (exit=0): inserted=12428 already_in_db=12623 ts_realigned=13504, printed tick_s=4.098 (exact first-interval 4.09847). "
"Inserts committed. already_in_db=12623 is from overlap with the 19:00 half-hour (official 84439301..84440000 / JP 84440000). "
"NEW first-pass in-window 404 W47N7@84440400 was recovered at confirm 19:41:42 gt=84440544 inserted=6 (publish lag; distinct=6 rows=6 ticks 84440495..84440500; the rest of that chunk is official empty_no_creep). Do not label it a leftover official 404. "
"Still-untold leftover official 404s W45N8@84439200, W45N8@84439300 and W45N8@84439500 (first recorded as first-pass in-window 404s in the quiet 1830 half-hour; still 404 through 1830 and 1900 confirm/retry2/late/postjp) aged out of window start 84439801 "
"(holes 84439201..84439300 / 84439301..84439400 / 84439501..84439600; listener 27/100 ticks 84439263..84439289 on W45N8@84439200 so official_404 missing=73 in that chunk; listener 0/100 on the other two); "
"they were retried as near-window on confirm/retry2/late/postjp and are still 404; do not relabel NEW; leave them NOT YET TOLD. "
"Still-untold leftover official 404 W47N7@84438700 (first recorded as a just-published 404 in the quiet 1730 half-hour; still 404 through the quiet 1800, 1830 and 1900 passes) aged out of window start 84439801 "
"(hole 84438701..84438800 ends 1000 ticks before the window; listener 0/100); it was retried as near-window on confirm/retry2/late/postjp and is still 404; do not relabel NEW. "
"Already-told leftover official 404 W45N8@84437100 was told in the ~17:46 _patrol_2026-11-23_1728 USER_LOG finished_at 17:44:55 (first recorded as a first-pass in-window 404 in the quiet 1600 half-hour); it aged out of window start 84439801 (hole 84437101..84437200) and was not retried this pass; do not re-tell and do not relabel NEW. "
"Already-told leftover official 404 W47N7@84436400 was also told in the 17:46 1728 USER_LOG (from quiet 1500); it aged out of window start 84439801 and was not retried this pass; do not re-tell and do not relabel NEW. "
"Already-told leftovers W47N8@84435500, W45N7@84435400, W45N7@84434800 and W47N7@84434000 were already told in the ~17:46 1728 USER_LOG (and earlier in the ~14:44 1427 USER_LOG), aged out of window start 84439801, and were not retried this pass; do not re-tell and do not relabel NEW. "
"tick_s_check chose live-anchor-best first 4.09847 (first is the first-interval / printed 4.098; first 4.09847 over45=42 over15=42 mean_off=-3.8253875746260135; "
"later_raw/later_mean 4.31146 over45=18880 over15=24197 mean_off=77.33349079087206; all_mean 4.27596 over45=17055 over15=23564 mean_off=63.80701106379658; "
"span_mean 4.27588 over45=17055 over15=23564 mean_off=63.77589234848312; prev_later 4.28803 is the quiet 1900 tick_s_in_use, over45=17710 over15=23827 mean_off=68.40559502063111). "
"later_raw was worse than live-anchor-best first (over45=18880 mean_off=77.3 vs over45=42 mean_off=-3.8); applied corrective first realign of 42 rows at game.time=84440534 tick_s=4.09847; after vs_first over45=0 over15=283 mean_off=-6.75143581923033; corrective_applied=True nfix=42 skipped_cross_chunk=0. "
"First-pass realign used 4.09847 (printed 4.098) and committed ts_realigned=13504. tick_s_in_use=4.09847 (first). "
"Last USER_LOG remains ~17:46 _patrol_2026-11-23_1728 (finished_at 17:44:55); do not re-tell it. "
"The earlier ~14:44 _patrol_2026-11-23_1427 USER_LOG (finished_at 14:44:04), the ~11:46 _patrol_2026-11-23_1129 USER_LOG (finished_at 11:46:33), the ~08:34 _patrol_2026-11-23_0821 USER_LOG, and the 12h review _review12h_2026-11-23_08 (~08:30) were already delivered; do not re-tell them. "
"This half-hour did not write a patrol or 12h-review folder and did not restart the listener, war_cmd, or pulse. "
"Quiet 19:00 half-hour _halfhour_2026-11-23_1900 already wrapped 19:16:11; do not re-tell that collect-only wrap. "
"Just-published 84440500 was not in first pass (first pass ended at published 84440400 / reconstructed 84439801..84440500 at game.time=84440511, 34/35 200, missing_chunks=1). "
"GET at 2026-11-23 19:48:30 Asia/Hong_Kong gt=84440640 all_five_200=True still_404=[] recovered=[W46N8@84440500, W47N8@84440500, W45N8@84440500, W45N7@84440500, W47N7@84440500] script inserted=3422. "
"JP retry/retry2 skipped (all_five_200, no JP-base 404s). "
"post-JP leftover retry at 2026-11-23 19:49:27 Asia/Hong_Kong gt=84440653 still_404=[W45N8@84439200, W45N8@84439300, W45N8@84439500, W47N7@84438700] inserted=0 "
"(W45N8@84439200 1453 ticks past the base, W45N8@84439300 1353, W45N8@84439500 1153, W47N7@84438700 1953; not mere publish lag). "
"script=3422 actual=3319; W46N8 script 427 vs actual 421 (pre listener distinct 66/100 rows=707 ticks 84440535..84440600; post distinct 100/100 rows=1128), "
"W47N8 script 1472 vs actual 1472 (pre 0/100; post distinct 100/100 rows=1472), "
"W45N8 script 500 vs actual 403 (pre listener distinct 6/100 rows=39 ticks 84440501..84440506; post distinct 100/100 rows=442; no official empty_no_creep in the JP chunk), "
"W45N7 script 265 vs actual 265 (pre listener distinct 28/100 rows=112 ticks 84440507..84440534; post distinct 100/100 rows=377), "
"W47N7 script 758 vs actual 758 (pre 0/100; post distinct 100/100 rows=758). "
"Coverage official_recovered=3307/3500 empty_no_creep=193 official_404=0. "
"W46N8 official empty_no_creep in this first-pass window: none. "
"W47N8 official empty_no_creep in this first-pass window: none. "
"W45N8 official empty_no_creep in this first-pass window: none. "
"W45N7 official empty_no_creep in this first-pass window: none. "
"W47N7 official empty_no_creep in this first-pass window: 193 ticks 84440302..84440494. "
"W47N7 official_404 in this first-pass window: none (W47N7@84440400 recovered on confirm). "
"inserted_first=12428 confirm=6 retry2=0 late=0 postjp=0 just_actual=3319 total=15753. "
"Still-untold leftover official 404s W45N8@84439200, W45N8@84439300 and W45N8@84439500 (first recorded as first-pass in-window 404s in the quiet 1830 half-hour, not yet told; still 404 through the quiet 1900 pass and this 1930 first pass / confirm 19:41:42 gt=84440544 / retry2 19:41:50 gt=84440546 / late 19:42:09 gt=84440551 / postjp 19:49:27 gt=84440653 inserted=0; 1453/1353/1153 ticks past the bases at postjp, not mere publish lag; aged out of window start 84439801; listener 27/100 ticks 84439263..84439289 on W45N8@84439200, 0/100 on the other two) remain NOT YET TOLD; do not relabel NEW. "
"Still-untold leftover official 404 W47N7@84438700 (first recorded as a just-published 404 in the quiet 1730 half-hour, not yet told; still 404 through the quiet 1800, 1830 and 1900 passes and this 1930 near-window retry at postjp 19:49:27 gt=84440653 inserted=0; 1953 ticks past the base at postjp, not mere publish lag; hole 100 ticks 84438701..84438800; listener 0/100) remains NOT YET TOLD; do not relabel NEW. "
"Already-told leftover official 404 W45N8@84437100 remains from the ~17:46 1728 USER_LOG (first recorded as a first-pass in-window 404 in the quiet 1600 half-hour; hole 100 ticks 84437101..84437200; listener 0/100; aged out of this window start 84439801 and not retried this pass); do not re-tell and do not relabel NEW. "
"Already-told leftover official 404 W47N7@84436400 remains from the ~17:46 1728 USER_LOG (hole 100 ticks 84436401..84436500; listener 0/100; aged out of this window start 84439801, not retried); do not re-tell and do not relabel NEW. "
"Already-told 盒子休眠 through 17:23:38-17:27:43 were told in the ~17:46 1728 USER_LOG, including 14:50:35-15:02:41, 15:21:27-15:31:14, 15:49:58-15:56:23, 16:14:02-16:29:04, and 16:52:03-17:06:19; do not re-tell and do not relabel NEW. "
"Still-untold 盒子休眠 18:16:12-18:35:22 Asia/Hong_Kong (1140s / ~19 min, box_pauses row; STATS 84439341..84439619, 279t; official-filled W46N8/W47N8/W45N7/W47N7 279/279, W45N8 119/279 — remaining shortfall is official-404 holes W45N8@84439300 covering 84439341..84439400 (60 ticks) and W45N8@84439500 covering 84439501..84439600 (100 ticks)). This freeze remains NOT YET TOLD; do not relabel NEW. "
"Still-untold 盒子休眠 18:52:46-18:58:58 Asia/Hong_Kong (366s / ~6.1 min, box_pauses row; STATS 84439851..84439959, 109t; official-filled all five rooms 109/109) remains NOT YET TOLD; do not relabel NEW. "
"NEW 盒子休眠 19:21:55-19:34:51 Asia/Hong_Kong (769s / ~12.8 min, box_pauses row; STATS 84440261..84440459, 199t; official-filled W46N8/W47N8/W45N8/W45N7 199/199, W47N7 41/199 — W47N7 shortfall is official empty_no_creep 84440302..84440459 (158 ticks of the 193-tick empty range 84440302..84440494; filled 84440261..84440301)). "
"Listener auto-restarted 19:34:55; python 3235006 started 19:35:04 remains up. This freeze is NOT YET TOLD. No new short listener WS gap this pass. "
"Services ok (postgres/views_apache/grafana/listener/dashboard). Single listener 3235006 since 19:35:04, yield_absent=True, no second slot, war_cmd/pulse not restarted. "
"Last delivered patrol remains ~17:46 _patrol_2026-11-23_1728 USER_LOG finished_at 17:44:55; do not re-tell already-told 1728 leftovers/freezes. Quiet wrap only."
),
]) + nl

verify = nl.join([
"---- verify " + wrapped + " ----",
(
"quiet 30-min trajectory backfill _halfhour_2026-11-23_2030 OK. Official history shard3 5 rooms ticks 84439801..84440500 (700, published_bases 84439800..84440400 at game.time=84440511; first pass 34/35 official GETs 200, missing_chunks=1 W47N7@84440400, recovered on confirm). "
"First pass started 19:39:19 finished 19:40:08 exit=0 inserted=12428 already_in_db=12623 ts_realigned=13504; tick_s printed 4.098 / first=4.09847; "
"tick_s_check chose live-anchor-best first 4.09847 (later_raw 4.31146 over45=18880 worse mean_off=77.3 vs -3.8; all_mean 4.27596 over45=17055 mean_off=63.8; prev_later 4.28803 is quiet 1900 tick_s_in_use, over45=17710 mean_off=68.4); "
"corrective_applied=True nfix=42 skipped_cross_chunk=0 at gt=84440534; after vs_first over45=0; tick_s_in_use=4.09847 (first). "
"confirm 19:41:42 gt=84440544 recovered W47N7@84440400 inserted=6 / retry2 19:41:50 gt=84440546 / late 19:42:09 gt=84440551 / postjp 19:49:27 gt=84440653 still_404=[W45N8@84439200, W45N8@84439300, W45N8@84439500, W47N7@84438700] inserted=0 after the confirm recovery "
"(1453/1353/1153/1953 ticks past the bases at postjp, not mere publish lag; no in-window official_404 in 84439801..84440500; W45N8@84439200 listener 27/100 ticks 84439263..84439289, aged out of window start 84439801; W45N8@84439300 and W45N8@84439500 listener 0/100; W47N7@84438700 listener 0/100). "
"Still-untold leftovers W45N8@84439200 / W45N8@84439300 / W45N8@84439500 (from quiet 1830) remain NOT YET TOLD; do not relabel NEW. "
"Still-untold leftover W47N7@84438700 (from quiet 1730 JP; still 404 through quiet 1800/1830/1900 and this 1930 near-window retry; hole 84438701..84438800, listener 0/100) do not relabel NEW. "
"Already-told leftovers W45N8@84437100 and W47N7@84436400 (told in the ~17:46 1728 USER_LOG) aged out of window start 84439801, not retried; do not re-tell and do not relabel NEW. "
"just-published 84440500 at 19:48:30 gt=84440640 all_five_200=True recovered all five script=3422 actual=3319; JP retry/retry2 skipped (no JP-base 404s); "
"W45N8 JP distinct 100/100 script 500 vs actual 403 (pre listener 6/100); W46N8 script 427 vs actual 421 (pre listener 66/100). "
"already_in_db overlap with 1900 official 84439301..84440000 / JP 84440000; inserted total=15753. "
"Coverage official_recovered=3307/3500 empty_no_creep=193 official_404=0 (W47N7 official empty_no_creep 193 ticks 84440302..84440494; W47N7@84440400 recovered on confirm). "
"NEW 盒子休眠 19:21:55-19:34:51 (769s, STATS 84440261..84440459, 199t; official-filled W46N8/W47N8/W45N8/W45N7 199/199, W47N7 41/199 due to official empty_no_creep 84440302..84440459) is NOT YET TOLD. "
"Listener auto-restarted 19:34:55, python 3235006 started 19:35:04 remains up. No new short listener WS gap. "
"Still-untold 盒子休眠 18:16:12-18:35:22 (1140s, STATS 84439341..84439619, 279t; official-filled W46N8/W47N8/W45N7/W47N7 279/279, W45N8 119/279; remaining shortfall official-404 W45N8@84439300 60t + W45N8@84439500 100t) remains NOT YET TOLD; do not relabel NEW. "
"Still-untold 盒子休眠 18:52:46-18:58:58 (366s, STATS 84439851..84439959, 109t; official-filled all five 109/109) remains NOT YET TOLD; do not relabel NEW. "
"Services ok (postgres/views_apache/grafana/listener/dashboard). Single listener 3235006 since 19:35:04, yield_absent=True, no second slot, war_cmd/pulse not restarted. "
"Still-untold leftover official 404s W45N8@84439200, W45N8@84439300, W45N8@84439500 and W47N7@84438700 remain NOT YET TOLD; do not relabel NEW. "
"Already-told leftover official 404s W45N8@84437100 and W47N7@84436400 were told in the ~17:46 1728 USER_LOG; aged out, not retried; do not re-tell. "
"Already-told 盒子休眠 through 17:23:38-17:27:43 were told in the ~17:46 1728 USER_LOG; do not re-tell. "
"Last delivered patrol remains ~17:46 _patrol_2026-11-23_1728 USER_LOG finished_at 17:44:55; do not re-tell already-told 1728 leftovers/freezes. Quiet wrap only."
),
]) + nl

DIR.joinpath("_wrap_body.in.txt").write_text(wrap)
DIR.joinpath("_verify_body.in.txt").write_text(verify)
DIR.joinpath("_halfhour_backfill_now.txt").write_text(wrap)
DIR.joinpath("_halfhour_backfill_verify.txt").write_text(verify)
DIR.joinpath("history_backfill_now.txt").write_text(wrap)
STATE.joinpath("_halfhour_backfill_now.txt").write_text(wrap)
STATE.joinpath("_halfhour_backfill_verify.txt").write_text(verify)
print("wrapped_at", wrapped)
print("wrap_chars", len(wrap), "verify_chars", len(verify))
