#!/usr/bin/env python3
from __future__ import annotations
import json, shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-20_1730")
STATE = Path("/workspace/screeps/state")
ROOT = Path("/workspace/screeps")
HK = ZoneInfo("Asia/Hong_Kong")
AT = datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")

cov = json.loads((DIR / "coverage_final.json").read_text())
jp = json.loads((DIR / "just_published_84377300.json").read_text())
summary = json.loads((DIR / "just_published_post_summary.json").read_text())
tickj = json.loads((DIR / "tick_s_realign.json").read_text())
live = json.loads((ROOT / "metrics" / "live.json").read_text())
rot = json.loads((ROOT / "metrics" / "listener_rot.json").read_text())

post = summary["post"]
pre = summary["pre"]
actual_by = summary["actual_by_room"]
script_by = summary["script_by_room"]
actual_total = int(summary["actual_sum"])
script_total = int(summary["script_sum"])
tips = summary["tips"]
holes = summary["holes"]
gaps = summary["gaps"]

ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
all_five_200 = all(g.get("code") == 200 and g.get("ok") for g in jp["gets"]) and not jp.get("still_404")
jp_distinct = ", ".join(f"{room} {post[room]['distinct']}/100" for room in ROOMS)
mismatch = [room for room in ROOMS if script_by.get(room, 0) != actual_by[room]]
mismatch_s = ", ".join(f"{r} script {script_by[r]} vs actual {actual_by[r]}" for r in mismatch)

INSERTED_FIRST = 9495
INSERTED_CONFIRM = 0
INSERTED_RETRY2 = 0
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + actual_total

payload = {
    "at": AT,
    "ok_quiet": True,
    "game_time_first": 84377301,
    "published_bases": "84376600..84377200",
    "reconstructed": [84376601, 84377300],
    "ticks": 700,
    "creep_rows": 22451,
    "missing_chunks": 5,
    "already_in_db": 12956,
    "inserted_first": INSERTED_FIRST,
    "inserted_confirm": INSERTED_CONFIRM,
    "inserted_retry2": INSERTED_RETRY2,
    "inserted_just_script": script_total,
    "inserted_just_actual": actual_total,
    "inserted_window": INSERTED_WINDOW,
    "inserted_total": INSERTED_TOTAL,
    "first_pass_by": "reused concurrent 1h patrol _patrol_2026-11-20_1725 history_backfill --minutes 40 finished 17:28:01; this run did not start a second backfill",
    "tick_s_printed": 4.260,
    "tick_s_first": 4.25984,
    "tick_s_in_use": 4.25984,
    "tick_s_in_use_name": "first",
    "ts_realigned_first": 349,
    "corrective": 0,
    "coverage_official_recovered": cov["official_recovered"],
    "coverage_expected": cov["expected"],
    "empty_no_creep": cov["empty_no_creep"],
    "official_404": cov["official_404_missing"],
    "per_room_new_first": {
        "W46N8": 3919,
        "W47N8": 1164,
        "W45N8": 1381,
        "W45N7": 1848,
        "W47N7": 1183,
    },
    "per_room_new_window": {
        "W46N8": 3919,
        "W47N8": 1164,
        "W45N8": 1381,
        "W45N7": 1848,
        "W47N7": 1183,
    },
    "in_window_404_after_retry2": ["W45N7@84376800", "W47N8@84377100"],
    "first_pass_404_recovered_before_confirm": [
        "W47N8@84377200",
        "W45N8@84377200",
        "W47N7@84377200",
    ],
    "just_published_base": 84377300,
    "just_published_at": jp.get("at"),
    "just_published_gt": jp.get("game_time"),
    "just_published_all_five_200": all_five_200,
    "just_published_script_by_room": script_by,
    "just_published_actual_by_room": actual_by,
    "new_box_freeze": {
        "from": "2026-11-20 17:09:11",
        "to": "2026-11-20 17:26:01",
        "sec": 1005,
        "why": "box frozen ~1005s since 2026-11-20 17:09:11 (VM hibernated; wall jumped, monotonic did not)",
        "listener_restart": "17:26:04",
        "listener_pid": 1407596,
        "listener_started": "17:26:13",
        "stats": "84377041..84377289",
        "span": 249,
        "last_stats": "84377040 at 17:08:58",
        "next_stats": "84377290 at 17:26:28",
        "wall_s": 1050,
        "official_fill": {room: gaps["freeze_1709"][room]["fill"] for room in ROOMS},
        "filled_by": (
            "First pass through 84377300 covers W46N8/W45N7 fully in this gap, including W46N8/W45N7@84377200. "
            "W47N8/W45N8/W47N7@84377200 were 404 on the first pass at 17:28 but already fully present (100/100) "
            "at confirm 17:33:56-17:34:02 (inserted=0; likely filled by the concurrent 1h patrol after 17:28). "
            "W47N8 still missing 84377101..84377200 (100t) because official 404 W47N8@84377100 remains unfilled "
            "after confirm 17:33:54 gt=84377394 and retry2 17:35:51 gt=84377422 "
            "(no live ticks present; hole 84377101..84377200)."
        ),
        "told": False,
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1730",
    },
    "new_short_listener_gap": None,
    "already_recorded_untold_box_freeze_in_window": {
        "from": "2026-11-20 16:45:36",
        "to": "2026-11-20 16:56:32",
        "sec": 647,
        "why": "box frozen ~647s since 2026-11-20 16:45:36 (VM hibernated; wall jumped, monotonic did not)",
        "listener_restart": "16:56:35",
        "listener_pid": 1400927,
        "listener_started": "16:56:45",
        "stats": "84376701..84376869",
        "span": 169,
        "last_stats": "84376700 at 16:45:15",
        "next_stats": "84376870 at 16:57:04",
        "wall_s": 709,
        "official_fill": {room: gaps["freeze_1645"][room]["fill"] for room in ROOMS},
        "filled_by": (
            "Already filled by the 17:00 half-hour first pass through 84376800 plus just-published 84376800 "
            "for W46N8/W47N8/W45N8/W47N7. W45N7 missing 84376801..84376869 (69t) because official 404 "
            "W45N7@84376800 still unfilled after the 17:00 just-published/retries and this run confirm "
            "17:33:53 gt=84377394 and retry2 17:35:50 gt=84377422 (no live ticks present; hole 84376801..84376900)."
        ),
        "told": False,
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1700",
    },
    "already_recorded_untold_short_listener_gap_in_window": None,
    "aged_out_already_told_short_listener_gap": None,
    "new_official_404": [
        {
            "chunk": "W47N8@84377100",
            "hole": "84377101..84377200",
            "live_ticks_present": "none (0t)",
            "still_404_after": "confirm 17:33:54 gt=84377394 and retry2 17:35:51 gt=84377422",
            "db": holes["W47N8@84377100"],
            "told": False,
            "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1730 (also 404 on the concurrent 1h patrol first pass at 17:28)",
        }
    ],
    "already_recorded_untold_in_window_404": [
        {
            "chunk": "W45N7@84376800",
            "hole": "84376801..84376900",
            "live_ticks_present": "none (0t)",
            "still_404_after": "17:00 just-published 17:02:32/17:04:06/17:04:57 (gt=84376945/84376971/84376983) and this run confirm 17:33:53 gt=84377394 and retry2 17:35:50 gt=84377422",
            "db": holes["W45N7@84376800"],
            "told": False,
            "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1700",
        }
    ],
    "already_told_in_window_404": [],
    "aged_out_already_told_404_not_retried": [
        "W46N8@84376100",
        "W45N8@84375300",
        "W45N7@84373700",
        "W47N8@84373800",
        "W45N7@84373300",
        "W47N7@84373200",
        "W46N8@84371600",
    ],
    "prior_told_box_freeze_aged_out": {
        "from": "2026-11-20 16:17:08",
        "to": "2026-11-20 16:22:02",
        "sec": 289,
        "stats": "84376291..84376369",
        "span": 79,
        "official_fill": {room: gaps["freeze_1617"][room]["fill"] for room in ROOMS},
        "told": True,
        "told_by": "1h patrol _patrol_2026-11-20_1624 ~16:31",
        "first_recorded_by": "1h patrol _patrol_2026-11-20_1624",
        "aged_out_of_window_start": 84376601,
    },
    "also_prior_told_box_freeze_aged_out": {
        "from": "2026-11-20 15:44:21",
        "to": "2026-11-20 16:03:39",
        "sec": 1152,
        "stats": "84375811..84376109",
        "span": 299,
        "official_fill": {room: gaps["freeze_1544"][room]["fill"] for room in ROOMS},
        "told": True,
        "told_by": "1h patrol _patrol_2026-11-20_1624 ~16:31",
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1600",
        "aged_out_of_window_start": 84376601,
    },
    "aged_out_already_told_box_freeze": {
        "from": "2026-11-20 15:15:12",
        "to": "2026-11-20 15:26:38",
        "sec": 686,
        "stats": "84375391..84375569",
        "span": 179,
        "told": True,
        "told_by": "1h patrol _patrol_2026-11-20_1526 ~15:29",
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1530",
        "aged_out_of_window_start": 84376601,
    },
    "listener": {
        "single_slot": True,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "pid": 1407596,
        "started": "17:26:13",
        "parent": 4035476,
        "yield": False,
        "restarted_this_run": False,
        "auto_restart": "17:26:04 after box freeze 17:09:11-17:26:01",
    },
    "war_cmd_pulse_restarted": False,
    "concurrent_1h_patrol": "_patrol_2026-11-20_1725 started 17:27:15; ran the reused first-pass history_backfill finished 17:28:01; this run did not write the patrol folder",
    "cpu_tip": tips["creep_cpu"],
    "path_tip": tips["path_arrivals"],
    "room_stats_tip": tips["room_stats"],
}

cur = STATE / "history_backfill.json"
if cur.exists():
    shutil.copy2(cur, STATE / "history_backfill.prev.json")

(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
shutil.copy2(DIR / "history_backfill.json", STATE / "history_backfill.json")

first = (DIR / "history_backfill_first_attempt.txt").read_text().rstrip()
wrap = f"""
---- wrap {AT} ----
confirm 17:33:53 gt=84377394 still_404 W45N7@84376800 and W47N8@84377100; W47N8/W45N8/W47N7@84377200 already 100/100 in db (inserted=0). retry2 17:35:50 gt=84377422 still_404 W45N7@84376800 and W47N8@84377100 inserted=0. Already-recorded leftover official 404 W45N7@84376800 remains unfilled (hole 84376801..84376900, no live ticks). NEW leftover official 404 W47N8@84377100 still unfilled (hole 84377101..84377200, no live ticks). Aged-out already-told 404s W46N8@84376100, W45N8@84375300, W45N7@84373700, W47N8@84373800, W45N7@84373300, W47N7@84373200, W46N8@84371600 were not retried.
tick_s_first=4.25984 printed=4.260 in_use=4.25984 (first) ts_realigned_first=349 corrective=0
coverage official_recovered=3300/3500 empty_no_creep=0 official_404=200
just-published 84377300 at {jp.get("at")} game.time={jp.get("game_time")} all_five_200={all_five_200} actual_inserted={actual_total} ticks 84377301..84377400 ({jp_distinct}); script inserted={script_total}{" (" + mismatch_s + ")." if mismatch_s else "."} W47N7 30/100 is official empty-no-creep 84377331..84377400 (GET 200, 34 creep rows), not a 404.
inserted_window={INSERTED_WINDOW} inserted_total={INSERTED_TOTAL}
ok_quiet=True
"""
now_txt = first + "\n" + wrap
(DIR / "history_backfill_now.txt").write_text(now_txt)
(DIR / "history_backfill.txt").write_text(first + "\n")
shutil.copy2(DIR / "history_backfill_now.txt", STATE / "_halfhour_backfill_now.txt")

verify = f"""{AT} verify
first pass game.time=84377301 published_bases=84376600..84377200 reconstructed 84376601..84377300 (700) creep_rows=22451 missing_chunks=5 W45N7@84376800 W47N8@84377100 W47N8@84377200 W45N8@84377200 W47N7@84377200
already_in_db=12956 inserted_first=9495 confirm=0 retry2=0 just_script={script_total} just_actual={actual_total} inserted_window={INSERTED_WINDOW} inserted_total={INSERTED_TOTAL}
per_room first W46N8:700t/3919new W47N8:500t/1164new W45N8:600t/1381new W45N7:600t/1848new W47N7:600t/1183new. First pass reused from concurrent 1h patrol _patrol_2026-11-20_1725 finished 17:28:01; this run did not start a second backfill. In-window official 404 after confirm+retry2: W45N7@84376800 (already recorded, untold) and W47N8@84377100 (new). W47N8/W45N8/W47N7@84377200 recovered to 100/100 before confirm (inserted=0).
tick_s_first=4.25984 printed=4.260 in_use=4.25984 (first) ts_realigned_first=349 corrective=0
coverage official_recovered=3300/3500 empty_no_creep=0 official_404=200 unique_room_ticks=3300 unique_creep_tick_rows=25113 (no dups).
Official 404 in this first-pass window after confirm+retry2: W45N7@84376800 still 404 after this run confirm 17:33:53 gt=84377394 and retry2 17:35:50 gt=84377422 (also still 404 after 17:00 just-published 17:02:32/17:04:06/17:04:57); no live ticks present, hole 100t 84376801..84376900; told=false, first recorded by the 17:00 half-hour, left to 1h patrol. NEW leftover official 404 W47N8@84377100 still 404 after confirm 17:33:54 gt=84377394 and retry2 17:35:51 gt=84377422; no live ticks present, hole 100t 84377101..84377200; told=false, first recorded by this 17:30 half-hour, left to 1h patrol. Official empty-no-creep in-window: none. W46N8/W45N8/W47N7 700/700; W47N8 600/700 (100 official 404); W45N7 600/700 (100 official 404).
just-published 84377300 at {jp.get("at")} game.time={jp.get("game_time")} all_five_200={all_five_200} actual_inserted={actual_total} ticks 84377301..84377400 ({jp_distinct}); script inserted={script_total}{" (" + mismatch_s + ")." if mismatch_s else "."} W47N7 30/100 is official empty-no-creep 70t 84377331..84377400 (GET 200, 34 creep rows), not a 404.
NEW box freeze 17:09:11-17:26:01 (1005s; box_pauses.jsonl); listener auto-restart 17:26:04, pid 1407596 started 17:26:13. STATS 84377041..84377289 (249t) wall 1050s from last STATS 84377040 at 17:08:58 to next STATS 84377290 at 17:26:28. Official-filled W46N8 249/249, W47N8 149/249, W45N8 249/249, W45N7 249/249, W47N7 249/249 via first pass through 84377300 plus W47N8/W45N8/W47N7@84377200 already present at confirm. W47N8 missing 84377101..84377200 (100t) because official 404 W47N8@84377100 still unfilled after confirm 17:33:54 gt=84377394 and retry2 17:35:51 gt=84377422 (no live ticks present; hole 84377101..84377200). told=false, first recorded by this 17:30 half-hour, left to 1h patrol. This run did not itself restart the listener. Concurrent 1h patrol _patrol_2026-11-20_1725 is running; this run did not write its folder.
Prior box freeze 16:45:36-16:56:32 (647s; box_pauses.jsonl); listener auto-restart 16:56:35, pid 1400927 started 16:56:45. STATS 84376701..84376869 (169t) wall 709s from last STATS 84376700 at 16:45:15 to next STATS 84376870 at 16:57:04. Official-filled W46N8 169/169, W47N8 169/169, W45N8 169/169, W45N7 100/169, W47N7 169/169. W45N7 missing 84376801..84376869 (69t) because official 404 W45N7@84376800 still unfilled. told=false, first recorded by the 17:00 half-hour, left to 1h patrol.
Prior box freeze 16:17:08-16:22:02 STATS 84376291..84376369 aged out of window start 84376601 (already told by the 16:31 1h patrol; official-filled all 5 79/79).
Prior box freeze 15:44:21-16:03:39 STATS 84375811..84376109 aged out of window start 84376601 (already told by the 16:31 1h patrol; official-fill remains W46N8 290/299, W47N8 299/299, W45N8 299/299, W45N7 273/299, W47N7 299/299).
Prior box freeze 15:15:12-15:26:38 STATS 84375391..84375569 aged out of window start 84376601 (already told by the 15:29 1h patrol).
listener single_slot=True roomSlot={live.get("roomSlot")} pid=1407596 started 17:26:13 after auto-restart 17:26:04; parent run_listener.sh pid 4035476 from Nov 13; this run did not restart listener or war_cmd/pulse; no second listener; yield absent. cpu_tip={tips["creep_cpu"]} path_tip={tips["path_arrivals"]} room_stats_tip={tips["room_stats"]}.
"""
(DIR / "verify.txt").write_text(verify)
shutil.copy2(DIR / "verify.txt", STATE / "_halfhour_backfill_verify.txt")
shutil.copy2(DIR / "backfill_retry2.txt", STATE / "_halfhour_backfill_retry2_1730.txt")

wrapup = f"""{AT} wrapup ok
wrote history_backfill.json history_backfill_now.txt verify.txt
inserted={INSERTED_FIRST}+0+0+just{actual_total} coverage=3300/3500 tick_s_in_use=4.25984
ok_line ok_quiet=True coverage=3300/3500 inserted_total={INSERTED_TOTAL}
"""
(DIR / "wrapup_run.txt").write_text(wrapup)
(DIR / "wrapup_run_stdout.txt").write_text(wrapup)
print(wrapup)
print("wrote wrapup ok")
