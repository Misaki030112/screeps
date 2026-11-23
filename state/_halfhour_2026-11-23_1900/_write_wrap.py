
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-23_1900")
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
"confirm at 2026-11-23 19:05:59 Asia/Hong_Kong still_404=[W45N8@84439300, W45N8@84439500, W45N8@84439200, W47N7@84438700] inserted=0 "
"(gt=84440045; W45N8@84439300 745 ticks past the base, W45N8@84439500 545, W45N8@84439200 845, W47N7@84438700 1345; not mere publish lag). "
"retry2 at 2026-11-23 19:06:15 Asia/Hong_Kong still_404=[W45N8@84439300, W45N8@84439500, W45N8@84439200, W47N7@84438700] inserted=0 (gt=84440048). "
"late retry at 2026-11-23 19:06:26 Asia/Hong_Kong still_404=[W45N8@84439300, W45N8@84439500, W45N8@84439200, W47N7@84438700] inserted=0 (gt=84440051). "
"First pass --minutes 40. First pass 33/35 official GETs 200, missing_chunks=2 (W45N8@84439300, W45N8@84439500). "
"First pass started 2026-11-23 19:03:37 Asia/Hong_Kong and finished 19:04:24 (exit=0): inserted=9436 already_in_db=14877 ts_realigned=9623, printed tick_s=4.349 (exact first-interval 4.34947). "
"Inserts committed. already_in_db=14877 is from overlap with the 18:30 half-hour (official 84438901..84439600 / JP 84439600). "
"Still-untold in-window official 404s W45N8@84439300 and W45N8@84439500 (first recorded as first-pass in-window 404s in the quiet 1830 half-hour) remain in this window (holes 84439301..84439400 / 84439501..84439600, listener 0/100 on both, official_404 missing=200); they were retried on confirm/retry2/late/postjp and are still 404; do not relabel NEW; leave them NOT YET TOLD. "
"Still-untold leftover official 404 W45N8@84439200 (first recorded as a first-pass in-window 404 in the quiet 1830 half-hour; still 404 through 1830 confirm/retry2/late/postjp) aged just before window start 84439301 (hole 84439201..84439300 ends at the window start; listener 27/100 ticks 84439263..84439289 so official_404 missing=73 in that chunk); it was retried as near-window on confirm/retry2/late/postjp and is still 404; do not relabel NEW. "
"Still-untold leftover official 404 W47N7@84438700 (first recorded as a just-published 404 in the quiet 1730 half-hour; still 404 through the quiet 1800 and 1830 passes) aged out of window start 84439301 (hole 84438701..84438800 ends 500 ticks before the window); it was retried as near-window on confirm/retry2/late/postjp and is still 404; do not relabel NEW. "
"Already-told leftover official 404 W45N8@84437100 was told in the ~17:46 _patrol_2026-11-23_1728 USER_LOG finished_at 17:44:55 (first recorded as a first-pass in-window 404 in the quiet 1600 half-hour); it aged out of window start 84439301 (hole 84437101..84437200) and was not retried this pass; do not re-tell and do not relabel NEW. "
"Already-told leftover official 404 W47N7@84436400 was also told in the 17:46 1728 USER_LOG (from quiet 1500); it aged out of window start 84439301 and was not retried this pass; do not re-tell and do not relabel NEW. "
"Already-told leftovers W47N8@84435500, W45N7@84435400, W45N7@84434800 and W47N7@84434000 were already told in the ~17:46 1728 USER_LOG (and earlier in the ~14:44 1427 USER_LOG), aged out of window start 84439301, and were not retried this pass; do not re-tell and do not relabel NEW. "
"tick_s_check chose live-anchor-best prev_later 4.28803 (prev_later is the quiet 1830 tick_s_in_use 4.28803; first 4.34947 over45=139 over15=5284 mean_off=9.833040175452302; later_raw/later_mean 4.22735 over45=9758 over15=15071 mean_off=-34.987237482771384; all_mean 4.24771 over45=8750 over15=14057 mean_off=-27.517191205879936; span_mean 4.24771 over45=8750 over15=14057 mean_off=-27.517191205879936; prev_later over45=0 over15=16632 mean_off=-12.717304245600328). "
"later_raw was worse than live-anchor-best prev_later (over45=9758 mean_off=-35.0 vs over45=0 mean_off=-12.7); prev_later already inside the 45s gate (over45=0), no corrective realign; corrective_applied=False nfix=0 skipped_cross_chunk=0. "
"First-pass realign used 4.34947 (printed 4.349) and committed ts_realigned=9623. tick_s_in_use=4.28803 (prev_later). "
"Last USER_LOG remains ~17:46 _patrol_2026-11-23_1728 (finished_at 17:44:55); do not re-tell it. "
"The earlier ~14:44 _patrol_2026-11-23_1427 USER_LOG (finished_at 14:44:04), the ~11:46 _patrol_2026-11-23_1129 USER_LOG (finished_at 11:46:33), the ~08:34 _patrol_2026-11-23_0821 USER_LOG, and the 12h review _review12h_2026-11-23_08 (~08:30) were already delivered; do not re-tell them. "
"This half-hour did not write a patrol or 12h-review folder and did not restart the listener, war_cmd, or pulse. "
"Quiet 18:30 half-hour _halfhour_2026-11-23_1830 already wrapped 18:47:39; do not re-tell that collect-only wrap. "
"Just-published 84440000 was not in first pass (first pass ended at published 84439900 / reconstructed 84439301..84440000 at game.time=84440012, 33/35 200, missing_chunks=2). "
"GET at 2026-11-23 19:12:58 Asia/Hong_Kong gt=84440141 all_five_200=True still_404=[] recovered=[W46N8@84440000, W47N8@84440000, W45N8@84440000, W45N7@84440000, W47N7@84440000] script inserted=2823. "
"JP retry/retry2 skipped (all_five_200, no JP-base 404s). "
"post-JP leftover retry at 2026-11-23 19:14:02 Asia/Hong_Kong gt=84440156 still_404=[W45N8@84439300, W45N8@84439500, W45N8@84439200, W47N7@84438700] inserted=0 "
"(W45N8@84439300 856 ticks past the base, W45N8@84439500 656, W45N8@84439200 956, W47N7@84438700 1456; not mere publish lag). "
"script=2823 actual=2586; W46N8 script 138 vs actual 138 (pre listener distinct 84/100 rows=841 ticks 84440017..84440100; post distinct 100/100 rows=979), "
"W47N8 script 1591 vs actual 1591 (pre 0/100; post distinct 100/100 rows=1591), "
"W45N8 script 700 vs actual 494 (pre 0/100; post distinct 100/100 rows=494; no official empty_no_creep in the JP chunk), "
"W45N7 script 128 vs actual 97 (pre listener distinct 16/100 rows=35 ticks 84440001..84440016; post distinct 100/100 rows=132), "
"W47N7 script 266 vs actual 266 (pre 0/100; post distinct 100/100 rows=266). "
"Coverage official_recovered=3300/3500 empty_no_creep=0 official_404=200. "
"W46N8 official empty_no_creep in this first-pass window: none. "
"W47N8 official empty_no_creep in this first-pass window: none. "
"W45N8 official empty_no_creep in this first-pass window: none. "
"W45N7 official empty_no_creep in this first-pass window: none. "
"W47N7 official empty_no_creep in this first-pass window: none. "
"W45N8 official_404 in this first-pass window: 200 ticks 84439301..84439400 and 84439501..84439600 (W45N8@84439300 0/100; W45N8@84439500 0/100). "
"inserted_first=9436 confirm=0 retry2=0 late=0 postjp=0 just_actual=2586 total=12022. "
"Still-untold leftover official 404s W45N8@84439200, W45N8@84439300 and W45N8@84439500 (first recorded as first-pass in-window 404s in the quiet 1830 half-hour, not yet told; still 404 through this 1900 first pass / confirm 19:05:59 gt=84440045 / retry2 19:06:15 gt=84440048 / late 19:06:26 gt=84440051 / postjp 19:14:02 gt=84440156 inserted=0; 956/856/656 ticks past the bases at postjp, not mere publish lag; in-window official_404 missing 200 ticks on W45N8@84439300 and W45N8@84439500; W45N8@84439200 aged just before window start 84439301, listener 27/100 ticks 84439263..84439289) remain NOT YET TOLD; do not relabel NEW. "
"Still-untold leftover official 404 W47N7@84438700 (first recorded as a just-published 404 in the quiet 1730 half-hour, not yet told; still 404 through the quiet 1800 and 1830 passes and this 1900 near-window retry at postjp 19:14:02 gt=84440156 inserted=0; 1456 ticks past the base at postjp, not mere publish lag; hole 100 ticks 84438701..84438800; listener 0/100) remains NOT YET TOLD; do not relabel NEW. "
"Already-told leftover official 404 W45N8@84437100 remains from the ~17:46 1728 USER_LOG (first recorded as a first-pass in-window 404 in the quiet 1600 half-hour; hole 100 ticks 84437101..84437200; listener 0/100; aged out of this window start 84439301 and not retried this pass); do not re-tell and do not relabel NEW. "
"Already-told leftover official 404 W47N7@84436400 remains from the ~17:46 1728 USER_LOG (hole 100 ticks 84436401..84436500; listener 0/100; aged out of this window start 84439301, not retried); do not re-tell and do not relabel NEW. "
"Already-told 盒子休眠 through 17:23:38-17:27:43 were told in the ~17:46 1728 USER_LOG, including 14:50:35-15:02:41, 15:21:27-15:31:14, 15:49:58-15:56:23, 16:14:02-16:29:04, and 16:52:03-17:06:19; do not re-tell and do not relabel NEW. "
"Still-untold 盒子休眠 18:16:12-18:35:22 Asia/Hong_Kong (1140s / ~19 min, box_pauses row; STATS 84439341..84439619, 279t; official-filled W46N8/W47N8/W45N7/W47N7 279/279, W45N8 now 119/279 — was 100/279 at the quiet 1830 wrap; this pass filled 19 more ticks 84439601..84439619 in the overlap/JP chunk 84439600; remaining shortfall is official-404 holes W45N8@84439300 covering 84439341..84439400 (60 ticks) and W45N8@84439500 covering 84439501..84439600 (100 ticks)). "
"This freeze remains NOT YET TOLD; do not relabel NEW. "
"NEW 盒子休眠 18:52:46-18:58:58 Asia/Hong_Kong (366s / ~6.1 min, box_pauses row; STATS 84439851..84439959, 109t; official-filled all five rooms 109/109). "
"Listener auto-restarted 18:59:01; python 3222459 started 18:59:11 remains up. This freeze is NOT YET TOLD. No new short listener WS gap this pass. "
"Services ok (postgres/views_apache/grafana/listener/dashboard). Single listener 3222459 since 18:59:11, yield_absent=True, no second slot, war_cmd/pulse not restarted. "
"Last delivered patrol remains ~17:46 _patrol_2026-11-23_1728 USER_LOG finished_at 17:44:55; do not re-tell already-told 1728 leftovers/freezes. Quiet wrap only."
),
]) + nl

verify = nl.join([
"---- verify " + wrapped + " ----",
(
"quiet 30-min trajectory backfill _halfhour_2026-11-23_1900 OK. Official history shard3 5 rooms ticks 84439301..84440000 (700, published_bases 84439300..84439900 at game.time=84440012; first pass 33/35 official GETs 200, missing_chunks=2 W45N8@84439300, W45N8@84439500). "
"First pass started 19:03:37 finished 19:04:24 exit=0 inserted=9436 already_in_db=14877 ts_realigned=9623; tick_s printed 4.349 / first=4.34947; "
"tick_s_check chose live-anchor-best prev_later 4.28803 (later_raw 4.22735 over45=9758 worse mean_off=-35.0 vs -12.7; first 4.34947 over45=139 mean_off=9.8; all_mean 4.24771 over45=8750 mean_off=-27.5; prev_later 4.28803 is quiet 1830 tick_s_in_use, over45=0 over15=16632 mean_off=-12.7); "
"corrective_applied=False nfix=0 skipped_cross_chunk=0; tick_s_in_use=4.28803 (prev_later). "
"confirm 19:05:59 gt=84440045 / retry2 19:06:15 gt=84440048 / late 19:06:26 gt=84440051 / postjp 19:14:02 gt=84440156 still_404=[W45N8@84439300, W45N8@84439500, W45N8@84439200, W47N7@84438700] inserted=0 "
"(856/656/956/1456 ticks past the bases at postjp, not mere publish lag; W45N8 in-window official_404 missing 200 ticks, listener 0/100 on W45N8@84439300 and W45N8@84439500; W45N8@84439200 listener 27/100 ticks 84439263..84439289, aged just before window start 84439301; W47N7@84438700 listener 0/100). "
"Still-untold leftovers W45N8@84439200 / W45N8@84439300 / W45N8@84439500 (from quiet 1830) remain NOT YET TOLD; do not relabel NEW. "
"Still-untold leftover W47N7@84438700 (from quiet 1730 JP; still 404 through quiet 1800/1830 and this 1900 near-window retry; hole 84438701..84438800, listener 0/100) do not relabel NEW. "
"Already-told leftovers W45N8@84437100 and W47N7@84436400 (told in the ~17:46 1728 USER_LOG) aged out of window start 84439301, not retried; do not re-tell and do not relabel NEW. "
"just-published 84440000 at 19:12:58 gt=84440141 all_five_200=True recovered all five script=2823 actual=2586; JP retry/retry2 skipped (no JP-base 404s); "
"W45N8 JP distinct 100/100 script 700 vs actual 494; W45N7 script 128 vs actual 97 (pre listener 16/100). "
"already_in_db overlap with 1830 official 84438901..84439600 / JP 84439600; inserted total=12022. "
"Coverage official_recovered=3300/3500 empty_no_creep=0 official_404=200 (W45N8 200 ticks 84439301..84439400 and 84439501..84439600). "
"NEW 盒子休眠 18:52:46-18:58:58 (366s, STATS 84439851..84439959, 109t; official-filled all five 109/109) is NOT YET TOLD. "
"Listener auto-restarted 18:59:01, python 3222459 started 18:59:11 remains up. No new short listener WS gap. "
"Still-untold 盒子休眠 18:16:12-18:35:22 (1140s, STATS 84439341..84439619, 279t; official-filled W46N8/W47N8/W45N7/W47N7 279/279, W45N8 now 119/279 after this pass filled 19 more ticks 84439601..84439619; remaining shortfall official-404 W45N8@84439300 60t + W45N8@84439500 100t) remains NOT YET TOLD; do not relabel NEW. "
"Services ok (postgres/views_apache/grafana/listener/dashboard). Single listener 3222459 since 18:59:11, yield_absent=True, no second slot, war_cmd/pulse not restarted. "
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
# keep a copy of this writer beside the wrap
print("wrapped_at", wrapped)
print("wrap_chars", len(wrap), "verify_chars", len(verify))
print("wrap_lines", wrap.count(nl), "verify_lines", verify.count(nl))
