#!/usr/bin/env python3
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import json

hk = ZoneInfo("Asia/Hong_Kong")
now = datetime.now(hk)
human = now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
nl = chr(10)
epoch = str(int(now.timestamp())) + nl

d = Path("/workspace/screeps/state/_halfhour_2026-11-26_1330")
state = Path("/workspace/screeps/state")
started = (d / "started_at_human.txt").read_text().strip()

paras = []
paras.append(
    "2026-11-26 ~" + human + ": 30-min trajectory backfill OK (quiet, folder _halfhour_2026-11-26_1330). "
    "Official history shard3 5 rooms ticks 84494001..84494800 (800, published_bases 84494000..84494600 at game.time=84494772 plus just-published 84494700). "
    "First pass tools/history_backfill.py --minutes 40 13:02:33-13:03:23 exit 0, game.time=84494772 reconstructed 84494001..84494700 (700), 35/35 official GETs 200, missing_chunks=0, already_in_db=16148 inserted=9272 ts_realigned=7917 tick_s printed 4.454. "
    "db_after all five distinct 700/700. pre_run exit 0 at 13:02:12 (started_at 12:59:28). "
    "tick_s_check 13:03:34-13:03:41 first=4.29095 later_mean_robust=4.38863 span_mean=4.37235 prev_later=4.36782; live-anchor best=first (first over45=10718 mean_off=-54.4 vs later over45=14838 mean_off=27.1); first-pass realign at printed 4.454 left many over45; corrective first realign nfix=11286 at game.time=84494786 brought over45 to 0 (mean_off=-14.86); tick_s_in_use=4.29095 (first). "
    "Confirm 13:03:57, retry2 13:04:17 and late 13:04:32 skipped no targets inserted=0. "
    "Just-published base 84494700 at 13:07:39 gt=84494842 tick_s=4.29095 all_five_200=True still_404=[] claimed inserted=2319; "
    "pre W47N8 already 87/100 (1295 rows range 84494714..84494800), other four 0/100; "
    "post all five 100/100 (W46N8 861 / W47N8 1489 / W45N8 523 / W45N7 274 / W47N7 373 rows range 84494701..84494800); "
    "actual_rows=2225 (W46N8 script 861 vs actual 861, W47N8 194 vs 194, W45N8 523 vs 523, W45N7 322 vs 274, W47N7 419 vs 373). No JP retry needed. Use actual 2225, do not add the claimed 2319 into inserted_total. "
    "postjp 13:08:35 skipped no targets. Coverage official_recovered=4000/4000 empty_no_creep=0 official_404=0. All five rooms 800/800. "
    "inserted_first=9272 confirm=0 retry2=0 late=0 postjp=0 just_actual=2225 total=11497. "
    "tick_s_in_use=4.29095 (first / live-anchor best; confirm/JP used this; first-pass printed 4.454; corrective nfix=11286)."
)
paras.append(
    "No leftover official 404 this 1300 pass. First pass had missing_chunks=0; no in-window official 404. "
    "Aged leftovers W47N8@84492600 and W47N7@84492300 were already told in the 2026-11-26 ~12:48 Tokyo / 11:47 HK _patrol_2026-11-26_1230 USER_LOG and are outside this window start 84494001; pre_run still saw both 0/100, not retried as in-window. "
    "After the ~12:48 Tokyo patrol (and the later ~13:40 Asia/Tokyo 1h patrol), new_official_404_untold=[] and still_untold_404=[]. Fold only newer leftover official 404s than the already-told set."
)
paras.append(
    "NEW 盒子休眠 12:46:32-12:48:55 (137s, already healed; official-filled all five 39/39 ticks 84494551..84494589; STATS still 0/39 because the listener was down; box_pauses row present; errors.log box frozen ~137s since 12:46:32 plus ws ping/pong timed out; listener auto-restarted 12:48:58, room slot visible 12:49:10). Not yet told — fold into the next patrol. "
    "NEW 盒子休眠 12:51:44-12:58:02 (377s, already healed; official-filled all five 99/99 ticks 84494621..84494719; STATS still 0/99 because the listener was down; box_pauses row present; errors.log box frozen ~377s since 12:51:44; listener auto-restarted 12:58:05, python 3894985 started 12:58:15, parent 4035476). Not yet told — fold into the next patrol. "
    "The 11:51:10-12:02:35 and 12:25:04-12:28:49 freezes were already told in the 2026-11-26 ~13:40 Asia/Tokyo 1h patrol (as 12:51:10-13:02:35 and 13:25:04-13:28:49 Tokyo). Do not relabel those NEW. "
    "No other new box_pauses row or len>=11 STATS gap. "
    "Listener still python 3894985, parent 4035476, single slot, yield absent, peacetime 5:5:1:1 (rot i=3 W45N7 at wrap). "
    "last_delivered_patrol folder remains _patrol_2026-11-26_1230 finished 2026-11-26 11:47:43 Asia/Hong_Kong; a later ~13:40 Asia/Tokyo 1h patrol was also already delivered (told the 11:51 and 12:25 HK freezes). "
    "new_freeze_untold=[\"12:46:32\",\"12:51:44\"] still_untold_freeze=[]."
)
text = (nl * 2).join(paras) + nl + nl

(d / "_halfhour_backfill_now.txt").write_text(text)
(state / "_halfhour_backfill_now.txt").write_text(text)
(d / "wrapped_at.txt").write_text(epoch)
(d / "wrapped_at_human.txt").write_text(human + nl)

by_room = {room: {"distinct": 800, "missing": 0, "empty": 0, "official_404": 0}
           for room in ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")}
meta = {
  "wrap_at": human,
  "inserted_total": 11497,
  "tick_s_in_use": 4.29095,
  "window": "84494001..84494800",
  "new_official_404_untold": [],
  "still_untold_404": [],
  "new_freeze_untold": ["12:46:32", "12:51:44"],
  "still_untold_freeze": [],
  "last_delivered_patrol": "_patrol_2026-11-26_1230",
  "last_delivered_patrol_finished_at": "2026-11-26 11:47:43 Asia/Hong_Kong",
  "last_halfhour": "_halfhour_2026-11-26_1330",
  "started_at": started,
  "inserted_breakdown": {
    "first": 9272,
    "confirm": 0,
    "retry2": 0,
    "late": 0,
    "postjp": 0,
    "just_claimed": 2319,
    "just_actual": 2225,
    "total": 11497,
  },
  "coverage": {
    "official_recovered": 4000,
    "expected": 4000,
    "empty_no_creep": 0,
    "official_404": 0,
    "by_room": by_room,
  },
  "tick_s_note": "tick_s_in_use=4.29095 (first / live-anchor best). first-pass printed 4.454; exact first-interval 4.29095; later_mean_robust=4.38863 span_mean=4.37235 prev_later=4.36782; first-pass ts_realigned=7917 at 4.454; over45 first 10718 mean_off=-54.4 vs later 14838 mean_off=27.1 so live-anchor chose first; corrective first realign nfix=11286 at gt=84494786 brought over45 to 0 (mean_off=-14.86). confirm/JP used 4.29095.",
  "new_official_404_this_run": [],
  "new_freeze_this_run": ["12:46:32", "12:51:44"],
  "outcome": "ok",
  "later_delivered_patrol_note": "A later 2026-11-26 ~13:40 Asia/Tokyo 1h patrol already told the 11:51:10-12:02:35 and 12:25:04-12:28:49 HK freezes (Tokyo 12:51/13:25); no new local patrol folder was found after _patrol_2026-11-26_1230.",
}
blob = json.dumps(meta, indent=2, ensure_ascii=False) + nl
(d / "wrap_meta.json").write_text(blob)
(d / "wrap_meta_for_state.json").write_text(blob)
print("wrapped_at", human)
print("wrote wrap_meta and _halfhour_backfill_now.txt")
