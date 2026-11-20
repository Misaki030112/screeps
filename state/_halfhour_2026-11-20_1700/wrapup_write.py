#!/usr/bin/env python3
from __future__ import annotations
import json, shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-20_1700")
STATE = Path("/workspace/screeps/state")
HK = ZoneInfo("Asia/Hong_Kong")
AT = datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")

payload = {
    "at": AT,
    "ok_quiet": True,
    "game_time_first": 84376894,
    "published_bases": "84376100..84376700",
    "reconstructed": [84376101, 84376800],
    "ticks": 700,
    "creep_rows": 26347,
    "missing_chunks": 1,
    "already_in_db": 18485,
    "inserted_first": 7862,
    "inserted_confirm": 0,
    "inserted_retry2": 0,
    "inserted_just_script": 3053,
    "inserted_just_actual": 2831,
    "inserted_window": 7862,
    "inserted_total": 10693,
    "tick_s_printed": 4.190,
    "tick_s_first": 4.18958,
    "tick_s_in_use": 4.177346,
    "tick_s_in_use_name": "all_mean",
    "ts_realigned_first": 0,
    "corrective": 0,
    "coverage_official_recovered": 3356,
    "coverage_expected": 3500,
    "empty_no_creep": 88,
    "official_404": 56,
    "per_room_new_first": {
        "W46N8": 843,
        "W47N8": 3130,
        "W45N8": 1169,
        "W45N7": 600,
        "W47N7": 2120,
    },
    "per_room_new_window": {
        "W46N8": 843,
        "W47N8": 3130,
        "W45N8": 1169,
        "W45N7": 600,
        "W47N7": 2120,
    },
    "in_window_404_after_retry2": ["W46N8@84376100"],
    "just_published_base": 84376800,
    "just_published_at": "2026-11-20 17:02:18 Asia/Hong_Kong",
    "just_published_gt": 84376945,
    "just_published_all_five_200": False,
    "just_published_script_by_room": {
        "W46N8": 965,
        "W47N8": 1069,
        "W45N8": 518,
        "W45N7": 0,
        "W47N7": 501,
    },
    "just_published_actual_by_room": {
        "W46N8": 965,
        "W47N8": 1069,
        "W45N8": 296,
        "W45N7": 0,
        "W47N7": 501,
    },
    "new_box_freeze": {
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
        "official_fill": {
            "W46N8": "169/169",
            "W47N8": "169/169",
            "W45N8": "169/169",
            "W45N7": "100/169",
            "W47N7": "169/169",
        },
        "filled_by": (
            "First pass through 84376800 covers 84376701..84376800 (100t) for all 5. "
            "Just-published 84376800 covers remainder 84376801..84376869 (69t) for W46N8/W47N8/W45N8/W47N7. "
            "W45N7 missing 84376801..84376869 (69t) because official 404 W45N7@84376800 still unfilled after "
            "just-published GET 17:02:32 gt=84376945, retry 17:04:06 gt=84376971 and retry2 17:04:57 gt=84376983 "
            "(no live ticks present; hole 84376801..84376900)."
        ),
        "told": False,
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1700",
    },
    "new_short_listener_gap": None,
    "already_recorded_untold_short_listener_gap_in_window": None,
    "aged_out_already_told_short_listener_gap": None,
    "new_official_404": [
        {
            "chunk": "W45N7@84376800",
            "hole": "84376801..84376900",
            "live_ticks_present": "none (0t)",
            "still_404_after": "just-published 17:02:32 gt=84376945, retry 17:04:06 gt=84376971 and retry2 17:04:57 gt=84376983",
            "db": {"distinct": 0, "rows": 0, "min": None, "max": None},
            "told": False,
            "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1700",
        }
    ],
    "already_recorded_untold_in_window_404": [],
    "already_told_in_window_404": [
        {
            "chunk": "W46N8@84376100",
            "hole": "84376101..84376156",
            "live_ticks_present": "84376157..84376200 (44t)",
            "still_404_after": "this run confirm 17:00:23 gt=84376917 and retry2 17:02:05 gt=84376942 (also still 404 after 16:15 just-published/retry2, the 16:31 1h patrol retry at gt=84376466, and the 16:30 half-hour confirm/retry2)",
            "db": {"distinct": 44, "rows": 429, "min": 84376157, "max": 84376200},
            "told": True,
            "told_by": "1h patrol _patrol_2026-11-20_1624 ~16:31",
            "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1600",
        }
    ],
    "aged_out_already_told_404_not_retried": [
        "W45N8@84375300",
        "W45N7@84373700",
        "W47N8@84373800",
        "W45N7@84373300",
        "W47N7@84373200",
        "W46N8@84371600",
    ],
    "prior_told_box_freeze_in_window": {
        "from": "2026-11-20 16:17:08",
        "to": "2026-11-20 16:22:02",
        "sec": 289,
        "why": "box frozen ~289s since 2026-11-20 16:17:08 (VM hibernated; wall jumped, monotonic did not)",
        "listener_restart": "16:22:06",
        "listener_pid": 1387389,
        "listener_started": "16:22:15",
        "stats": "84376291..84376369",
        "span": 79,
        "last_stats": "84376290 at 16:16:54",
        "next_stats": "84376370 at 16:22:25",
        "official_fill": {
            "W46N8": "79/79",
            "W47N8": "79/79",
            "W45N8": "79/79",
            "W45N7": "79/79",
            "W47N7": "79/79",
        },
        "told": True,
        "told_by": "1h patrol _patrol_2026-11-20_1624 ~16:31",
        "first_recorded_by": "1h patrol _patrol_2026-11-20_1624",
    },
    "also_prior_told_box_freeze_partially_aged": {
        "from": "2026-11-20 15:44:21",
        "to": "2026-11-20 16:03:39",
        "sec": 1152,
        "stats": "84375811..84376109",
        "span": 299,
        "last_stats": "84375810 at 15:43:36",
        "next_stats": "84376110 at 16:04:19",
        "wall_s": 1243,
        "official_fill": {
            "W46N8": "290/299",
            "W47N8": "299/299",
            "W45N8": "299/299",
            "W45N7": "273/299",
            "W47N7": "299/299",
        },
        "window_overlap": "84376101..84376109 (9t) still in window start 84376101; earlier ticks aged out",
        "filled_by": (
            "Already filled by the 16:00 half-hour first pass plus just-published 84376100. "
            "W46N8 still missing 84376101..84376109 (9t) because leftover official 404 W46N8@84376100 remains unfilled "
            "after this run confirm 17:00:23 gt=84376917 and retry2 17:02:05 gt=84376942 "
            "(44 live ticks 84376157..84376200 present; hole 84376101..84376156). "
            "W45N7 shortfall is official empty-no-creep 84375818..84375843 (26t), not a 404; those empty ticks aged out of window start 84376101."
        ),
        "told": True,
        "told_by": "1h patrol _patrol_2026-11-20_1624 ~16:31",
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1600",
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
        "aged_out_of_window_start": 84376101,
    },
    "listener": {
        "single_slot": True,
        "roomSlot": "W47N8",
        "rot": {"i": 1, "room": "W47N8", "left": 94.9, "at": "2026-11-20 17:06:04"},
        "pid": 1400927,
        "started": "16:56:45",
        "parent": 4035476,
        "yield": False,
        "restarted_this_run": False,
        "auto_restart": "16:56:35 after box freeze 16:45:36-16:56:32",
    },
    "war_cmd_pulse_restarted": False,
    "concurrent_1h_patrol": None,
    "cpu_tip": 84376980,
    "path_tip": 84376976,
    "room_stats_tip": 84376990,
}

# rotate prev json
cur = STATE / "history_backfill.json"
if cur.exists():
    shutil.copy2(cur, STATE / "history_backfill.prev.json")

(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
shutil.copy2(DIR / "history_backfill.json", STATE / "history_backfill.json")

first = (DIR / "history_backfill_first_attempt.txt").read_text().rstrip()
wrap = f"""
---- wrap {AT} ----
confirm 17:00:23 gt=84376917 still_404 W46N8@84376100 inserted=0; retry2 17:02:05 gt=84376942 still_404 W46N8@84376100 inserted=0. Already-told leftover official 404 W46N8@84376100 remains unfilled (hole 84376101..84376156, 44 live ticks 84376157..84376200). Aged-out already-told 404s W45N8@84375300, W45N7@84373700, W47N8@84373800, W45N7@84373300, W47N7@84373200, W46N8@84371600 were not retried.
tick_s_first=4.18958 printed=4.190 in_use=4.17735 (all_mean) ts_realigned_first=0 corrective=0
coverage official_recovered=3356/3500 empty_no_creep=88 official_404=56
just-published 84376800 at 2026-11-20 17:02:18 Asia/Hong_Kong game.time=84376945 all_five_200=False actual_inserted=2831 ticks 84376801..84376900 (W46N8 100/100, W47N8 100/100, W45N8 100/100, W45N7 0/100, W47N7 100/100); script inserted=3053 (W45N8 script 518 vs actual 296). NEW leftover official 404 W45N7@84376800 still 404 after 17:02:32/17:04:06/17:04:57 (gt=84376945/84376971/84376983); no live ticks present, hole 84376801..84376900.
inserted_window=7862 inserted_total=10693
ok_quiet=True
"""
now_txt = first + "\n" + wrap
(DIR / "history_backfill_now.txt").write_text(now_txt)
(DIR / "history_backfill.txt").write_text(first + "\n")
shutil.copy2(DIR / "history_backfill_now.txt", STATE / "_halfhour_backfill_now.txt")

verify = f"""{AT} verify
first pass game.time=84376894 published_bases=84376100..84376700 reconstructed 84376101..84376800 (700) creep_rows=26347 missing_chunks=1 W46N8@84376100
already_in_db=18485 inserted_first=7862 confirm=0 retry2=0 just_script=3053 just_actual=2831 inserted_window=7862 inserted_total=10693
per_room first W46N8:600t/843new W47N8:700t/3130new W45N8:700t/1169new W45N7:700t/600new W47N7:700t/2120new. In-window official 404: W46N8@84376100 (already told). W45N7 official empty-no-creep 88t (84376413..84376500).
tick_s_first=4.18958 printed=4.190 in_use=4.17735 (all_mean) ts_realigned_first=0 corrective=0
coverage official_recovered=3356/3500 empty_no_creep=88 official_404=56 unique_room_ticks=3356 unique_creep_tick_rows=26536 (no dups).
Official 404 in this first-pass window after confirm+retry2: W46N8@84376100 still 404 after confirm 17:00:23 gt=84376917 and retry2 17:02:05 gt=84376942; 44 live ticks 84376157..84376200 present, hole 56t 84376101..84376156; already told by the 16:31 1h patrol (first recorded by the 16:00 half-hour). Official empty-no-creep: W45N7 88t. W46N8 644/700 (56 official 404); W47N8/W45N8/W47N7 700/700; W45N7 612/700 (88 empty).
just-published 84376800 at 2026-11-20 17:02:18 Asia/Hong_Kong game.time=84376945 all_five_200=False actual_inserted=2831 ticks 84376801..84376900 (W46N8 100/100, W47N8 100/100, W45N8 100/100, W45N7 0/100, W47N7 100/100); script inserted=3053 (W45N8 script 518 vs actual 296). NEW leftover official 404 W45N7@84376800 still 404 after 17:02:32/17:04:06/17:04:57 (gt=84376945/84376971/84376983); no live ticks present, hole 100t 84376801..84376900; told=false, first recorded by this 17:00 half-hour, left to 1h patrol.
NEW box freeze 16:45:36-16:56:32 (647s; box_pauses.jsonl); listener auto-restart 16:56:35, pid 1400927 started 16:56:45. STATS 84376701..84376869 (169t) wall 709s from last STATS 84376700 at 16:45:15 to next STATS 84376870 at 16:57:04. Official-filled W46N8 169/169, W47N8 169/169, W45N8 169/169, W45N7 100/169, W47N7 169/169 via first pass through 84376800 plus just-published 84376800 (ticks 84376801..84376900 covering remainder 84376801..84376869). W45N7 missing 84376801..84376869 (69t) because official 404 W45N7@84376800 still unfilled after just-published GET 17:02:32 gt=84376945, retry 17:04:06 gt=84376971 and retry2 17:04:57 gt=84376983 (no live ticks present; hole 84376801..84376900). told=false, first recorded by this 17:00 half-hour, left to 1h patrol. This run did not itself restart the listener. No concurrent 1h patrol.
Prior box freeze 16:17:08-16:22:02 (289s; box_pauses.jsonl); listener auto-restart 16:22:06, pid 1387389 started 16:22:15. STATS 84376291..84376369 (79t) last STATS 84376290 at 16:16:54 next STATS 84376370 at 16:22:25. Official-filled all 5 79/79. Already told by the 16:31 1h patrol.
Prior box freeze 15:44:21-16:03:39 STATS 84375811..84376109 mostly aged out of window start 84376101; remaining overlap 84376101..84376109 is the W46N8 official 404 hole (9t). Full-gap official-fill remains W46N8 290/299, W47N8 299/299, W45N8 299/299, W45N7 273/299, W47N7 299/299; W45N7 shortfall is official empty-no-creep 84375818..84375843 (26t), now aged out. Already recorded by the 16:00 half-hour and already told by the 16:31 1h patrol.
Prior box freeze 15:15:12-15:26:38 STATS 84375391..84375569 aged out of window start 84376101 (already told by the 15:29 1h patrol).
listener single_slot=True roomSlot=W47N8 pid=1400927 started 16:56:45 after auto-restart 16:56:35; parent run_listener.sh pid 4035476 from Nov 13; this run did not restart listener or war_cmd/pulse; no second listener; yield absent. cpu_tip=84376980 path_tip=84376976 room_stats_tip=84376990.
"""
(DIR / "verify.txt").write_text(verify)
shutil.copy2(DIR / "verify.txt", STATE / "_halfhour_backfill_verify.txt")

wrapup = f"""{AT} wrapup ok
wrote history_backfill.json history_backfill_now.txt verify.txt
inserted=7862+0+0+just2831 coverage=3356/3500 tick_s_in_use=4.17735
ok_line ok_quiet=True coverage=3356/3500 inserted_total=10693
"""
(DIR / "wrapup_run.txt").write_text(wrapup)
(DIR / "wrapup_run_stdout.txt").write_text(wrapup)
print(wrapup)
print("wrote all status files at", AT)
