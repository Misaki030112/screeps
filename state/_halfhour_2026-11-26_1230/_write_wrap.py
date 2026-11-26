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

d = Path("/workspace/screeps/state/_halfhour_2026-11-26_1230")
state = Path("/workspace/screeps/state")

paras = []
paras.append(
    "2026-11-26 ~" + human + ": 30-min trajectory backfill OK (quiet). "
    "Official history shard3 5 rooms ticks 84493301..84494100 (800, published_bases 84493300..84493900 at game.time=84494010 plus just-published 84494000). "
    "First pass tools/history_backfill.py --minutes 40 12:07:02-12:07:49 exit 0, game.time=84494010 reconstructed 84493301..84494000 (700), 34/35 official GETs 200, missing_chunks=1 W47N7@84493900, already_in_db=11850 inserted=11049 ts_realigned=0 tick_s printed 4.368. "
    "db_after four rooms distinct 700/700, W47N7 600/700. pre_run exit 0 at 12:06:46. "
    "tick_s_check 12:08:53-12:08:56 first=4.36782 later_mean_robust=4.35693 span_mean=4.35670 prev_later=4.38390; live-anchor best=first (over45 all 0; first mean_off=1.3 vs later -2.9); no corrective realign; tick_s_in_use=4.36782 (first). "
    "Confirm 12:09:11 gt=84494039 recovered W47N7@84493900 inserted=463 (actual db 462 rows / 100 distinct 84493901..84494000); retry2 12:09:34 gt=84494044 and late 12:09:52 gt=84494048 already 100/100, claimed inserted=1 each not added. "
    "Just-published base 84494000 at 12:16:45 gt=84494142 tick_s=4.36782 all_five_200=True still_404=[] claimed inserted=2755; actual_rows=2750 actual_distinct=400 ticks 84494001..84494100 "
    "(W46N8 distinct +58 / rows +541 from pre 42/511 range 84494059..84494100 to window 100/1052 script claimed 542; "
    "W47N8 +96 / 1194 from pre 4/44 range 84494001..84494004 to 100/1238; "
    "W45N8 +73 / 276 from pre 27/171 range 84494005..84494031 to 100/447 script claimed 279; "
    "W45N7 +73 / 289 from pre 27/103 range 84494032..84494058 to 100/392 script claimed 290; "
    "W47N7 +100 / 450 from pre 0/0 to 100/450). No JP retry needed. Use actual 2750, do not add the claimed 2755 into inserted_total. "
    "postjp 12:17:24 skipped no targets. Coverage official_recovered=4000/4000 empty_no_creep=0 official_404=0. All five rooms 800/800. "
    "inserted_first=11049 confirm=463 retry2=0 late=0 postjp=0 just_actual=2750 total=14262. "
    "tick_s_in_use=4.36782 (first / live-anchor best; confirm/JP used this; first-pass printed 4.368)."
)
paras.append(
    "No leftover official 404 this 1200 pass. First-pass in-window 404 W47N7@84493900 was publish lag and recovered at confirm 12:09:11 gt=84494039 (other four rooms already 200 at first pass gt=84494010); do not label it a leftover. "
    "Aged leftovers W47N8@84492600 and W47N7@84492300 were already told in the 2026-11-26 ~12:48 Tokyo / 11:47 HK _patrol_2026-11-26_1230 USER_LOG and are outside this window start 84493301; not retried. "
    "After that patrol, new_official_404_untold=[] and still_untold_404=[]. Fold only newer leftover official 404s than the already-told set."
)
paras.append(
    "NEW 盒子休眠 11:51:10-12:02:35 (684s, already healed; official-filled all five 169/169 ticks 84493791..84493959; STATS still 0/169 because the listener was down; box_pauses row present; errors.log box frozen ~684s since 11:51:10; listener auto-restarted 12:02:38, python 3866271 started 12:02:48, parent 4035476). Not yet told — fold into the next patrol. "
    "The 11:20:31 WS drop was already told in the 1230 patrol (12:20 Tokyo). No other new box_pauses row or len>=11 STATS gap. "
    "Listener still python 3866271, parent 4035476, single slot, yield absent, peacetime 5:5:1:1. "
    "last_delivered_patrol is now _patrol_2026-11-26_1230 finished 2026-11-26 11:47:43 Asia/Hong_Kong; previous new_freeze_untold 14:19:05, 14:36:14, 17:56:07 and still_untold_freeze 13:46:32, 13:23:34, 12:51:59, 13:01:53, 12:31:00, 11:58:28 were told in that patrol and are not carried forward. "
    "new_freeze_untold=[\"11:51:10\"] still_untold_freeze=[]."
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
  "inserted_total": 14262,
  "tick_s_in_use": 4.36782,
  "window": "84493301..84494100",
  "new_official_404_untold": [],
  "still_untold_404": [],
  "new_freeze_untold": ["11:51:10"],
  "still_untold_freeze": [],
  "last_delivered_patrol": "_patrol_2026-11-26_1230",
  "last_delivered_patrol_finished_at": "2026-11-26 11:47:43 Asia/Hong_Kong",
  "last_halfhour": "_halfhour_2026-11-26_1200",
  "started_at": "2026-11-26 12:04:15 Asia/Hong_Kong",
  "inserted_breakdown": {
    "first": 11049,
    "confirm": 463,
    "retry2": 0,
    "late": 0,
    "postjp": 0,
    "just_claimed": 2755,
    "just_actual": 2750,
    "total": 14262,
  },
  "coverage": {
    "official_recovered": 4000,
    "expected": 4000,
    "empty_no_creep": 0,
    "official_404": 0,
    "by_room": by_room,
  },
  "tick_s_note": "tick_s_in_use=4.36782 (first / live-anchor best). first-pass printed 4.368; exact first-interval 4.36782; later_mean_robust=4.35693 span_mean=4.35670 prev_later=4.38390; over45 all 0 so live-anchor chose first (mean_off=1.3 vs later -2.9); no corrective realign. confirm/JP used 4.36782.",
  "new_official_404_this_run": [],
  "new_freeze_this_run": ["11:51:10"],
  "outcome": "ok",
}
blob = json.dumps(meta, indent=2) + nl
(d / "wrap_meta.json").write_text(blob)
(d / "wrap_meta_for_state.json").write_text(blob)
print("wrapped_at", human)
print("wrote wrap files, now_chars", len(text))
