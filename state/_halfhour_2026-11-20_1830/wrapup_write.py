#!/usr/bin/env python3
from __future__ import annotations
import json, shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-20_1830")
STATE = Path("/workspace/screeps/state")
ROOT = Path("/workspace/screeps")
HK = ZoneInfo("Asia/Hong_Kong")
AT = datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")

cov = json.loads((DIR / "coverage_final.json").read_text())
jp = json.loads((DIR / "just_published_84378000.json").read_text())
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
mismatch_suffix = (" (" + mismatch_s + ").") if mismatch_s else "."

INSERTED_FIRST = 4333
INSERTED_CONFIRM = 0
INSERTED_RETRY2 = 0
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + actual_total

FILL_1645 = {"W46N8": "169/169", "W47N8": "169/169", "W45N8": "169/169", "W45N7": "100/169", "W47N7": "169/169"}

payload = {
    "at": AT,
    "ok_quiet": True,
    "game_time_first": 84378070,
    "published_bases": "84377300..84377900",
    "reconstructed": [84377301, 84378000],
    "ticks": 700,
    "creep_rows": 26536,
    "missing_chunks": 1,
    "already_in_db": 22203,
    "inserted_first": INSERTED_FIRST,
    "inserted_confirm": INSERTED_CONFIRM,
    "inserted_retry2": INSERTED_RETRY2,
    "inserted_just_script": script_total,
    "inserted_just_actual": actual_total,
    "inserted_window": INSERTED_WINDOW,
    "inserted_total": INSERTED_TOTAL,
    "first_pass_by": "reused from concurrent 1h patrol _patrol_2026-11-20_1819 history_backfill finished 18:22:09; this run did not start a second backfill",
    "tick_s_printed": 4.227,
    "tick_s_first": 4.22687,
    "tick_s_in_use": 4.22286,
    "tick_s_in_use_name": "span_mean",
    "ts_realigned_first": 4974,
    "corrective": 3332,
    "coverage_official_recovered": cov["official_recovered"],
    "coverage_expected": cov["expected"],
    "empty_no_creep": cov["empty_no_creep"],
    "official_404": cov["official_404_missing"],
    "per_room_new_first": {
        "W46N8": 815,
        "W47N8": 1976,
        "W45N8": 568,
        "W45N7": 287,
        "W47N7": 687,
    },
    "per_room_new_window": {
        "W46N8": 815,
        "W47N8": 1976,
        "W45N8": 568,
        "W45N7": 287,
        "W47N7": 687,
    },
    "in_window_404_after_retry2": ["W46N8@84377600"],
    "first_pass_404_recovered_before_confirm": [],
    "just_published_base": 84378000,
    "just_published_at": jp.get("at"),
    "just_published_gt": jp.get("game_time"),
    "just_published_all_five_200": all_five_200,
    "just_published_script_by_room": script_by,
    "just_published_actual_by_room": actual_by,
    "just_published_still_404": jp.get("still_404"),
    "new_box_freeze": None,
    "new_short_listener_gap": None,
    "already_told_box_freeze_in_window": None,
    "already_recorded_untold_box_freeze_in_window": {
        "from": "2026-11-20 17:43:34",
        "to": "2026-11-20 18:02:53",
        "sec": 1158,
        "why": "box frozen ~1158s since 2026-11-20 17:43:34 (VM hibernated; wall jumped, monotonic did not)",
        "listener_restart": "18:02:56",
        "listener_pid": 1419372,
        "listener_started": "18:03:05",
        "stats": "84377521..84377819",
        "span": 299,
        "last_stats": "84377520 at 17:42:38",
        "next_stats": "84377820 at 18:03:35",
        "wall_s": 1257,
        "official_fill": {room: gaps["freeze_1743"][room]["fill"] for room in ROOMS},
        "filled_by": (
            "First pass through 84378000 covers W47N8/W45N8/W45N7/W47N7 fully in this gap. "
            "W46N8 missing 84377601..84377700 (100t) because official 404 W46N8@84377600 remains unfilled "
            "after this run confirm 18:33:58 gt=84378246 and retry2 18:36:39 gt=84378285 "
            "(also still 404 after 18:00 confirm 18:07:40/retry2 18:09:52 and 1h patrol retry 18:23:38 gt=84378099; "
            "no live ticks present; hole 84377601..84377700)."
        ),
        "told": False,
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1800",
        "note": "Left to 1h patrol (concurrent _patrol_2026-11-20_1819 already retried the 404).",
    },
    "already_recorded_untold_short_listener_gap_in_window": None,
    "aged_out_already_told_short_listener_gap": None,
    "new_official_404": [
        {
            "chunk": "W47N7@84378000",
            "hole": "84378001..84378100",
            "live_ticks_present": "none (0t)",
            "still_404_after": "just-published GET 18:34:23 gt=84378249, retry 18:37:50 gt=84378302, and retry2 18:40:14 gt=84378336 (also 404 in concurrent patrol wrap_up GET ~18:30)",
            "db": holes["W47N7@84378000"],
            "told": False,
            "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1830",
            "kind": "just_published",
        }
    ],
    "already_recorded_untold_in_window_404": [
        {
            "chunk": "W46N8@84377600",
            "hole": "84377601..84377700",
            "live_ticks_present": "none (0t)",
            "still_404_after": "this run confirm 18:33:58 gt=84378246 and retry2 18:36:39 gt=84378285 (also still 404 after 18:00 confirm+retry2 and 1h patrol retry 18:23:38 gt=84378099)",
            "db": holes["W46N8@84377600"],
            "told": False,
            "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1800",
        }
    ],
    "already_told_in_window_404": [],
    "aged_out_already_told_404_not_retried": [
        "W47N8@84377100",
        "W45N7@84376800",
        "W46N8@84376100",
        "W45N8@84375300",
        "W45N7@84373700",
        "W47N8@84373800",
        "W45N7@84373300",
        "W47N7@84373200",
        "W46N8@84371600",
    ],
    "prior_told_box_freeze_aged_out": {
        "from": "2026-11-20 17:09:11",
        "to": "2026-11-20 17:26:01",
        "sec": 1005,
        "stats": "84377041..84377289",
        "span": 249,
        "official_fill": {room: gaps["freeze_1709"][room]["fill"] for room in ROOMS},
        "told": True,
        "told_by": "1h patrol _patrol_2026-11-20_1725 ~17:40",
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1730",
        "aged_out_of_window_start": 84377301,
        "note": "W47N8 still missing 84377101..84377200 (100t) because already-told official 404 W47N8@84377100 remains unfilled. Aged out of this window start 84377301 and was not retried.",
    },
    "also_prior_told_box_freeze_aged_out": {
        "from": "2026-11-20 16:45:36",
        "to": "2026-11-20 16:56:32",
        "sec": 647,
        "stats": "84376701..84376869",
        "span": 169,
        "official_fill": FILL_1645,
        "told": True,
        "told_by": "1h patrol _patrol_2026-11-20_1725 ~17:40",
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1700",
        "aged_out_of_window_start": 84377301,
        "note": "W45N7 still missing 84376801..84376869 (69t) because already-told official 404 W45N7@84376800 remains unfilled.",
    },
    "aged_out_already_told_box_freeze": {
        "from": "2026-11-20 16:17:08",
        "to": "2026-11-20 16:22:02",
        "sec": 289,
        "stats": "84376291..84376369",
        "span": 79,
        "told": True,
        "told_by": "1h patrol _patrol_2026-11-20_1624 ~16:31",
        "first_recorded_by": "1h patrol _patrol_2026-11-20_1624",
        "aged_out_of_window_start": 84377301,
    },
    "also_aged_out_already_told_box_freeze_1544": {
        "from": "2026-11-20 15:44:21",
        "to": "2026-11-20 16:03:39",
        "sec": 1152,
        "stats": "84375811..84376109",
        "span": 299,
        "told": True,
        "told_by": "1h patrol _patrol_2026-11-20_1624 ~16:31",
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1600",
        "aged_out_of_window_start": 84377301,
    },
    "also_aged_out_already_told_box_freeze_1515": {
        "from": "2026-11-20 15:15:12",
        "to": "2026-11-20 15:26:38",
        "sec": 686,
        "stats": "84375391..84375569",
        "span": 179,
        "told": True,
        "told_by": "1h patrol _patrol_2026-11-20_1526 ~15:29",
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1530",
        "aged_out_of_window_start": 84377301,
    },
    "listener": {
        "single_slot": True,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "pid": 1419372,
        "started": "18:03:05",
        "parent": 4035476,
        "yield": False,
        "restarted_this_run": False,
        "auto_restart": "18:02:56 after box freeze 17:43:34-18:02:53",
    },
    "war_cmd_pulse_restarted": False,
    "concurrent_1h_patrol": "_patrol_2026-11-20_1819 (first pass reused, finished 18:22:09; wrap_up justpub GET 84378000 ~18:30 observed W47N7 404; this run did not write the patrol folder)",
    "cpu_tip": tips["creep_cpu"],
    "path_tip": tips["path_arrivals"],
    "room_stats_tip": tips["room_stats"],
}

cur = STATE / "history_backfill.json"
if cur.exists():
    shutil.copy2(cur, STATE / "history_backfill.prev.json")

(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + chr(10))
shutil.copy2(DIR / "history_backfill.json", STATE / "history_backfill.json")

first = (DIR / "history_backfill_first_attempt.txt").read_text().rstrip()
if first.endswith("EXIT:0"):
    first = first[: -len("EXIT:0")].rstrip()
wrap = f"""
---- wrap {AT} ----
confirm 18:33:58 gt=84378246 still_404 W46N8@84377600 inserted=0. retry2 18:36:39 gt=84378285 still_404 W46N8@84377600 inserted=0. Already-recorded leftover official 404 W46N8@84377600 remains unfilled (hole 84377601..84377700, no live ticks; first recorded by the 18:00 half-hour, left to 1h patrol). Aged-out already-told 404s W47N8@84377100, W45N7@84376800, W46N8@84376100, W45N8@84375300, W45N7@84373700, W47N8@84373800, W45N7@84373300, W47N7@84373200, W46N8@84371600 were not retried.
tick_s_first=4.22687 printed=4.227 in_use=4.22286 (span_mean) ts_realigned_first=4974 corrective=3332 (later-mean-robust 4.23702 refused as worse vs live-anchor span_mean; after corrective over45=0)
coverage official_recovered=3281/3500 empty_no_creep=119 official_404=100
just-published 84378000 at {jp.get("at")} game.time={jp.get("game_time")} all_five_200={all_five_200} actual_inserted={actual_total} ticks 84378001..84378100 ({jp_distinct}); script inserted={script_total}{mismatch_suffix} W45N7 27/100 is official empty-no-creep 73t (84378027 and 84378029..84378100; GET 200). NEW leftover official 404 W47N7@84378000 still unfilled after just-published GET 18:34:23 gt=84378249, retry 18:37:50 gt=84378302, and retry2 18:40:14 gt=84378336 (hole 84378001..84378100, no live ticks).
inserted_window={INSERTED_WINDOW} inserted_total={INSERTED_TOTAL}
ok_quiet=True
"""
now_txt = first + chr(10) + wrap
(DIR / "history_backfill_now.txt").write_text(now_txt)
(DIR / "history_backfill.txt").write_text(first + chr(10))
shutil.copy2(DIR / "history_backfill_now.txt", STATE / "_halfhour_backfill_now.txt")

ua = cov["unique_after"]
fill1743 = gaps["freeze_1743"]
fill1709 = gaps["freeze_1709"]
verify = f"""{AT} verify
first pass game.time=84378070 published_bases=84377300..84377900 reconstructed 84377301..84378000 (700) creep_rows=26536 missing_chunks=1 W46N8@84377600
already_in_db=22203 inserted_first=4333 confirm=0 retry2=0 just_script={script_total} just_actual={actual_total} inserted_window={INSERTED_WINDOW} inserted_total={INSERTED_TOTAL}
per_room first W46N8:600t/815new W47N8:700t/1976new W45N8:700t/568new W45N7:700t/287new W47N7:700t/687new. First pass reused from concurrent 1h patrol _patrol_2026-11-20_1819 finished 18:22:09; this run did not start a second backfill. In-window official 404 after confirm+retry2: W46N8@84377600 (already recorded, untold).
tick_s_first=4.22687 printed=4.227 in_use=4.22286 (span_mean) ts_realigned_first=4974 corrective=3332 (later-mean-robust 4.23702 refused as worse vs live-anchor span_mean; after corrective over45=0)
coverage official_recovered=3281/3500 empty_no_creep=119 official_404=100 unique_room_ticks={ua["distinct_room_ticks"]} unique_creep_tick_rows={ua["unique_creep_tick_rows"]} (no dups).
Official 404 in this first-pass window after confirm+retry2: already-recorded leftover W46N8@84377600 still 404 after this run confirm 18:33:58 gt=84378246 and retry2 18:36:39 gt=84378285 (also still 404 after 18:00 confirm 18:07:40/retry2 18:09:52 and 1h patrol retry 18:23:38 gt=84378099); no live ticks present, hole 100t 84377601..84377700; told=false, first recorded by the 18:00 half-hour, left to 1h patrol. Official empty-no-creep in-window: W47N7 119t 84377331..84377449 (GET 200, not a 404). W47N8/W45N8/W45N7 700/700; W46N8 600/700 (100 official 404); W47N7 581/700 (119 official empty-no-creep).
just-published 84378000 at {jp.get("at")} game.time={jp.get("game_time")} all_five_200={all_five_200} actual_inserted={actual_total} ticks 84378001..84378100 ({jp_distinct}); script inserted={script_total}{mismatch_suffix} W45N7 27/100 is official empty-no-creep 73t (84378027 and 84378029..84378100; GET 200, 52 creep rows), not a 404. NEW leftover official 404 W47N7@84378000 still 404 after just-published GET 18:34:23 gt=84378249, retry 18:37:50 gt=84378302, and retry2 18:40:14 gt=84378336; no live ticks present, hole 100t 84378001..84378100; told=false, first recorded by this 18:30 half-hour, left to 1h patrol.
Already-recorded untold box freeze 17:43:34-18:02:53 (1158s; box_pauses.jsonl); listener auto-restart 18:02:56, pid 1419372 started 18:03:05. STATS 84377521..84377819 (299t) wall 1257s from last STATS 84377520 at 17:42:38 to next STATS 84377820 at 18:03:35. Official-filled W46N8 {fill1743["W46N8"]["fill"]}, W47N8 {fill1743["W47N8"]["fill"]}, W45N8 {fill1743["W45N8"]["fill"]}, W45N7 {fill1743["W45N7"]["fill"]}, W47N7 {fill1743["W47N7"]["fill"]} via first pass through 84378000. W46N8 missing 84377601..84377700 (100t) because official 404 W46N8@84377600 still unfilled after this run confirm+retry2 (no live ticks present; hole 84377601..84377700). told=false, first recorded by the 18:00 half-hour, left to 1h patrol. This run did not itself restart the listener. Concurrent 1h patrol _patrol_2026-11-20_1819 first pass reused.
Prior box freeze 17:09:11-17:26:01 STATS 84377041..84377289 aged out of window start 84377301 (already told by the 17:40 1h patrol; official-filled W46N8 {fill1709["W46N8"]["fill"]}, W47N8 {fill1709["W47N8"]["fill"]}, W45N8 {fill1709["W45N8"]["fill"]}, W45N7 {fill1709["W45N7"]["fill"]}, W47N7 {fill1709["W47N7"]["fill"]}). W47N8 missing 84377101..84377200 (100t) because already-told official 404 W47N8@84377100 still unfilled.
Prior box freeze 16:45:36-16:56:32 STATS 84376701..84376869 aged out of window start 84377301 (already told by the 17:40 1h patrol; official-fill remains W46N8 169/169, W47N8 169/169, W45N8 169/169, W45N7 100/169, W47N7 169/169). W45N7 missing 84376801..84376869 (69t) because already-told official 404 W45N7@84376800 still unfilled.
Prior box freeze 16:17:08-16:22:02 STATS 84376291..84376369 aged out of window start 84377301 (already told by the 16:31 1h patrol).
Prior box freeze 15:44:21-16:03:39 STATS 84375811..84376109 aged out of window start 84377301 (already told by the 16:31 1h patrol).
Prior box freeze 15:15:12-15:26:38 STATS 84375391..84375569 aged out of window start 84377301 (already told by the 15:29 1h patrol).
listener single_slot=True roomSlot={live.get("roomSlot")} pid=1419372 started 18:03:05 after auto-restart 18:02:56; parent run_listener.sh pid 4035476 from Nov 13; this run did not restart listener or war_cmd/pulse; no second listener; yield absent. cpu_tip={tips["creep_cpu"]} path_tip={tips["path_arrivals"]} room_stats_tip={tips["room_stats"]}.
"""
(DIR / "verify.txt").write_text(verify)
shutil.copy2(DIR / "verify.txt", STATE / "_halfhour_backfill_verify.txt")
shutil.copy2(DIR / "backfill_retry2.txt", STATE / "_halfhour_backfill_retry2_1830.txt")

wrapup = f"""{AT} wrapup ok
wrote history_backfill.json history_backfill_now.txt verify.txt
inserted={INSERTED_FIRST}+0+0+just{actual_total} coverage=3281/3500 tick_s_in_use=4.22286
ok_line ok_quiet=True coverage=3281/3500 inserted_total={INSERTED_TOTAL}
"""
(DIR / "wrapup_run.txt").write_text(wrapup)
(DIR / "wrapup_run_stdout.txt").write_text(wrapup)
print(wrapup)
print("wrote wrapup ok")
