#!/usr/bin/env python3
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import json, shutil

d = Path("/workspace/screeps/state/_halfhour_2026-11-24_0830")
root = Path("/workspace/screeps/state")
hk = ZoneInfo("Asia/Hong_Kong")
now = datetime.now(hk)
human = now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
nl = chr(10)
d.joinpath("wrapped_at.txt").write_text(str(int(now.timestamp())) + nl)
d.joinpath("wrapped_at_human.txt").write_text(human + nl)
print("wrapped_at", human)

pre = {
    "W46N8": {"distinct": 0, "rows": 0, "min": None, "max": None},
    "W47N8": {"distinct": 73, "rows": 1056, "min": 84450528, "max": 84450600},
    "W45N8": {"distinct": 0, "rows": 0, "min": None, "max": None},
    "W45N7": {"distinct": 0, "rows": 0, "min": None, "max": None},
    "W47N7": {"distinct": 0, "rows": 0, "min": None, "max": None},
}
post = {
    "W46N8": {"distinct": 0, "rows": 0, "min": None, "max": None},
    "W47N8": {"distinct": 100, "rows": 1468, "min": 84450501, "max": 84450600},
    "W45N8": {"distinct": 100, "rows": 602, "min": 84450501, "max": 84450600},
    "W45N7": {"distinct": 100, "rows": 250, "min": 84450501, "max": 84450600},
    "W47N7": {"distinct": 100, "rows": 511, "min": 84450501, "max": 84450600},
}
script = {"W46N8": 0, "W47N8": 412, "W45N8": 602, "W45N7": 340, "W47N7": 512}
(d / "just_published_post_counts.json").write_text(json.dumps(post, indent=2) + nl)
actual_total = 0
distinct_total = 0
for room in ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7"):
    pr, po = pre[room], post[room]
    actual_rows = int(po.get("rows") or 0) - int(pr.get("rows") or 0)
    actual_d = int(po.get("distinct") or 0) - int(pr.get("distinct") or 0)
    actual_total += actual_rows
    distinct_total += actual_d
    print(
        f"{room} pre distinct={pr.get('distinct')} rows={pr.get('rows')} range={pr.get('min')}..{pr.get('max')}  "
        f"post distinct={po.get('distinct')} rows={po.get('rows')} range={po.get('min')}..{po.get('max')}  "
        f"script={script[room]} actual_rows={actual_rows} actual_distinct={actual_d}"
    )
print("script_total", sum(script.values()), "actual_total", actual_total, "actual_distinct", distinct_total)

now_body = f"""---- wrap {human} ----
quiet 30-min trajectory backfill _halfhour_2026-11-24_0830 OK (wrap {human}, started_at 07:37:23). Official history shard3 5 rooms ticks 84449801..84450500 (700, published_bases 84449800..84450400 at game.time=84450581; first pass 35/35 official GETs 200, missing_chunks=0, inserted=15528 already_in_db=13071 ts_realigned=0). tick_s_in_use=4.30087 (first). First pass started 07:40:27 finished 07:41:13 exit=0 inserted=15528 already_in_db=13071 ts_realigned=0; tick_s printed 4.301 / first=4.30087 (min-all 84449800..84449900); tick_s_check chose live-anchor-best first 4.30087 (first 4.30087 over45=0 mean_off=-1.67; later_raw 4.32822 over45=0 mean_off=10.55; later_robust 4.32822 over45=0 mean_off=10.55; all_mean 4.32367 over45=0 mean_off=8.51; span_mean 4.32367 over45=0 mean_off=8.51; prev_later 4.26303 is quiet 0700 tick_s_in_use, over45=0 mean_off=-18.57); corrective_applied=False nfix=0 skipped_cross_chunk=0 at gt=84450603; tick_s_in_use=4.30087 (first). confirm 07:42:23 gt=84450608 leftover official inserted=0 / retry2 07:43:13 gt=84450620 leftover official inserted=0 / late 07:43:58 gt=84450630 leftover official inserted=0 / postjp 07:58:51 gt=84450841 still_404=[W46N8@84450500, W46N8@84448500, W45N8@84448600, W47N8@84448400, W47N8@84447700, W45N8@84447400, W47N7@84446600, W46N8@84445500, W45N7@84444900, W47N8@84445100, W46N8@84444500, W46N8@84444200, W47N8@84443800, W47N7@84443300, W45N7@84441900, W47N7@84440900, W45N8@84439200, W45N8@84439300, W45N8@84439500, W47N7@84438700] leftover official inserted=0. JP 84450500 GET 07:44:52 gt=84450643 all_five_200=False (W46N8 official 404); tool_inserted=1866 actual_rows=1775 actual_distinct=327 ticks 84450501..84450600 (W46N8 distinct +0 / rows 0/0, W47N8 +27 / 412/412, W45N8 +100 / 602/602, W45N7 +100 / 340/250, W47N7 +100 / 512/511). JP retry 07:48:55 gt=84450700 (+200) and retry2 07:56:03 gt=84450800 (+300) still_404=['W46N8@84450500'] official inserted=0 for that room (retry/retry2 also reported W45N7 +90 and W47N7 +1 each time, but post counts stayed 250 and 511; use actual_rows). NEW leftover official 404 W46N8@84450500 (first recorded as a just-published official 404 in this 0730 half-hour; still 404 through JP GET 07:44:54 gt=84450643 / retry 07:48:57 gt=84450700 / retry2 07:56:04 gt=84450800 / postjp 07:58:52 gt=84450841 official inserted=0; listener also 0/100 ticks 84450501..84450600; 241 ticks past chunk close 84450600 at postjp, not mere publish lag, because the other four rooms on 84450500 already succeeded at first JP +143; outside TMAX=84450500 of the 0730 window). Fold into the next 3h patrol, not a 12h review; do not relabel already-told leftovers as NEW. Already-told leftover official 404s W46N8@84448500 (listener 50/100 ticks 84448501..84448550) and W45N8@84448600 (listener 12/100 ticks 84448689..84448700) were told in the ~05:38 0522 USER_LOG; aged out of window start 84449801; retried through confirm/retry2/late/postjp, still 404 official inserted=0; W46N8@84448500 is 2241 ticks past chunk close 84448600 at postjp gt=84450841; W45N8@84448600 is 2141 ticks past chunk close 84448700; do not re-tell and do not relabel NEW. Already-told leftover official 404s W47N8@84448400, W47N8@84447700, W45N8@84447400, and W47N7@84446600 were told in the ~05:38 0522 USER_LOG; all aged out of window start 84449801; retried through confirm/retry2/late/postjp, still 404 official inserted=0; W47N8@84448400 listener 0/100 ticks 84448401..84448500; do not re-tell and do not relabel NEW. Already-told leftover official 404s W46N8@84445500, W45N7@84444900, W47N8@84445100, W46N8@84444500, W46N8@84444200, and W47N8@84443800 were told in the ~02:34 0221 USER_LOG; all aged out of window start 84449801; retried, still 404; W46N8@84445500 listener already 100/100 and W47N8@84443800 listener already 100/100 are not trajectory holes; do not re-tell and do not relabel NEW. Already-told leftover official 404s W47N7@84443300 and W45N7@84441900 were told in the ~23:33 2321 USER_LOG; both aged out of window start 84449801; retried, still 404; do not re-tell and do not relabel NEW. Already-told leftover official 404s W47N7@84440900, W45N8@84439200, W45N8@84439300, W45N8@84439500, and W47N7@84438700 were told in the ~20:44 2028 USER_LOG; all aged out of window start 84449801; retried, still 404; do not re-tell and do not relabel NEW. Coverage official_recovered=3500/3500 empty_no_creep=0 official_404=0. W46N8 is 700/700. W47N8 is 700/700. W45N8 is 700/700. W45N7 is 700/700. W47N7 is 700/700. JP 84450500 is outside the 40-min window (TMAX=84450500). inserted_first=15528 confirm=0 retry2=0 late=0 postjp=0 just_actual=327 total=15855. NEW 盒子休眠 07:16:30-07:36:22 (1188s, already healed; official-filled W47N8/W45N8/W45N7/W47N7 289/289, W46N8 260/289 missing 84450501..84450529 due to leftover official 404 W46N8@84450500; STATS 84450241..84450529; box_pauses row present; errors.log box frozen ~1188s plus ws ping/pong timed out; listener auto-restarted 07:36:25, python 3544250 started 07:36:34, parent 4035476) is NOT YET TOLD. Fold into the next 3h patrol, not a 12h review. Still-untold 盒子休眠 06:57:38-06:58:46 from quiet 0700 remains NOT YET TOLD (68s, already healed; now official-filled all five 29/29 after this 0730 window covered 84449981..84450009, including the 0700 W47N7 20/29 tail; STATS 84449981..84450009; listener 3533110 since 06:58:59); do not relabel NEW. Still-untold 盒子休眠 06:16:01-06:34:24 from quiet 0630 remains NOT YET TOLD (1097s, already healed; official-filled W46N8/W47N8/W45N8/W47N7 269/269, W45N7 132/269 official empty_no_creep 137t; STATS 84449401..84449669); do not relabel NEW. Still-untold 盒子休眠 05:51:59-05:56:28 from quiet 0600 remains NOT YET TOLD (261s, already healed; official-filled W46N8/W47N8/W45N8/W47N7 79/79, W45N7 19/79 official empty_no_creep on the remaining 60t; STATS 84449071..84449149); do not relabel NEW. Already-told 0522 盒子休眠 04:51:47-05:01:57 / 04:18:52-04:32:23 / 03:49:23-04:01:11 / 03:21:51-03:31:05 plus 监听短中断 02:57:18 must not be re-told or relabeled NEW. Last delivered patrol is ~05:38 0522 finished_at 05:38:12; already-told 0522/0221/2321/2028 leftovers/freezes must not be re-told. Services ok. Single listener 3544250 since 07:36:34, yield_absent=True, no second slot, war_cmd/pulse not restarted. Quiet wrap only.
"""

verify = f"""---- wrap {human} ----
quiet 30-min trajectory backfill _halfhour_2026-11-24_0830 OK (wrap {human}, started_at 07:37:23). Official history shard3 5 rooms ticks 84449801..84450500 (700, published_bases 84449800..84450400 at game.time=84450581; first pass 35/35 200, missing_chunks=0, inserted=15528 already_in_db=13071 ts_realigned=0). tick_s_in_use=4.30087 (first; over45=0 vs first; later_raw 4.32822 over45=0; prev_later 4.26303 from quiet 0700; corrective_applied=False nfix=0 skipped_cross_chunk=0 at gt=84450603). confirm 07:42:23 gt=84450608 / retry2 07:43:13 / late 07:43:58 / postjp 07:58:51 gt=84450841 leftover official inserted=0. JP 84450500 GET 07:44:52 gt=84450643 all_five_200=False (W46N8 official 404); tool_inserted=1866 actual_rows=1775 actual_distinct=327 (W46N8 0/0, W47N8 27/412, W45N8 100/602, W45N7 100/250, W47N7 100/511). JP retry +200 at 07:48:55 gt=84450700 and retry2 +300 at 07:56:03 gt=84450800 still_404 W46N8@84450500 official inserted=0. Coverage official_recovered=3500/3500 empty_no_creep=0 official_404=0. All five rooms 700/700. inserted_first=15528 confirm=0 retry2=0 late=0 postjp=0 just_actual=327 total=15855. NEW leftover official 404 W46N8@84450500 is NOT YET TOLD (JP 404 through postjp 07:58:52 gt=84450841 official inserted=0; listener 0/100 ticks 84450501..84450600; 241 ticks past chunk close 84450600; other four rooms already 200 at first JP +143; outside TMAX=84450500). NEW 盒子休眠 07:16:30-07:36:22 is NOT YET TOLD (1188s, already healed; official-filled W47N8/W45N8/W45N7/W47N7 289/289, W46N8 260/289 missing 84450501..84450529 due to leftover official 404 W46N8@84450500; STATS 84450241..84450529; listener 3544250 since 07:36:34). Still-untold 盒子休眠 06:57:38-06:58:46 (now official-filled all five 29/29), 06:16:01-06:34:24, and 05:51:59-05:56:28 remain NOT YET TOLD; do not relabel NEW. Already-told 0522 leftovers W46N8@84448500, W45N8@84448600, W47N8@84448400, W47N8@84447700, W45N8@84447400, W47N7@84446600 and already-told 盒子休眠 04:51:47-05:01:57 / 04:18:52-04:32:23 / 03:49:23-04:01:11 / 03:21:51-03:31:05 plus 监听短中断 02:57:18 must not be re-told or relabeled NEW. Last delivered patrol is ~05:38 0522 finished_at 05:38:12. Services ok. Single listener 3544250 since 07:36:34, yield_absent=True, no second slot, war_cmd/pulse not restarted. Quiet wrap only.
"""

(d / "_wrap_body.in.txt").write_text(now_body)
(d / "_halfhour_backfill_now.txt").write_text(now_body)
(d / "_halfhour_backfill_verify.txt").write_text(verify)
shutil.copyfile(d / "_halfhour_backfill_now.txt", root / "_halfhour_backfill_now.txt")
shutil.copyfile(d / "_halfhour_backfill_verify.txt", root / "_halfhour_backfill_verify.txt")
print("wrote wrap files, bytes now", len(now_body), "verify", len(verify))
