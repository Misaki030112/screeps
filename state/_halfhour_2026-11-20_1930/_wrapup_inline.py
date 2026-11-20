
from pathlib import Path
import json, shutil
from datetime import datetime
from zoneinfo import ZoneInfo

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-20_1900")
STATE = Path("/workspace/screeps/state")
ROOT = Path("/workspace/screeps")
HK = ZoneInfo("Asia/Hong_Kong")
AT = datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
NL = chr(10)

cov = json.loads((DIR / "coverage_final.json").read_text())
jp = json.loads((DIR / "just_published_84378600.json").read_text())
summary = json.loads((DIR / "just_published_post_summary.json").read_text())
live = json.loads((ROOT / "metrics" / "live.json").read_text())
rot = json.loads((ROOT / "metrics" / "listener_rot.json").read_text())

post = summary["post"]
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

INSERTED_FIRST = 15105
INSERTED_CONFIRM = 0
INSERTED_RETRY2 = 0
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + actual_total
FILL_1645 = {"W46N8": "169/169", "W47N8": "169/169", "W45N8": "169/169", "W45N7": "100/169", "W47N7": "169/169"}
FILL_1709 = {"W46N8": "249/249", "W47N8": "149/249", "W45N8": "249/249", "W45N7": "249/249", "W47N7": "249/249"}

payload = {
    "at": AT,
    "ok_quiet": True,
    "game_time_first": 84378667,
    "published_bases": "84377900..84378500",
    "reconstructed": [84377901, 84378600],
    "ticks": 700,
    "creep_rows": 26141,
    "missing_chunks": 1,
    "already_in_db": 11036,
    "inserted_first": INSERTED_FIRST,
    "inserted_confirm": INSERTED_CONFIRM,
    "inserted_retry2": INSERTED_RETRY2,
    "inserted_just_script": script_total,
    "inserted_just_actual": actual_total,
    "inserted_window": INSERTED_WINDOW,
    "inserted_total": INSERTED_TOTAL,
    "first_pass_by": "this 30-min backfill _halfhour_2026-11-20_1900 (no concurrent 1h patrol; last _patrol_2026-11-20_1819 finished ~18:31)",
    "tick_s_printed": 4.356,
    "tick_s_first": 4.35571,
    "tick_s_in_use": 4.35571,
    "tick_s_in_use_name": "first",
    "ts_realigned_first": 10879,
    "corrective": 0,
    "coverage_official_recovered": cov["official_recovered"],
    "coverage_expected": cov["expected"],
    "empty_no_creep": cov["empty_no_creep"],
    "official_404": cov["official_404_missing"],
    "per_room_new_first": {"W46N8": 3788, "W47N8": 4603, "W45N8": 2578, "W45N7": 747, "W47N7": 3389},
    "per_room_new_window": {"W46N8": 3788, "W47N8": 4603, "W45N8": 2578, "W45N7": 747, "W47N7": 3389},
    "in_window_404_after_retry2": ["W47N7@84378000"],
    "first_pass_404_recovered_before_confirm": [],
    "just_published_base": 84378600,
    "just_published_at": jp.get("at"),
    "just_published_gt": jp.get("game_time"),
    "just_published_all_five_200": all_five_200,
    "just_published_script_by_room": script_by,
    "just_published_actual_by_room": actual_by,
    "just_published_still_404": jp.get("still_404") or [],
    "new_box_freeze": {
        "from": "2026-11-20 18:46:28",
        "to": "2026-11-20 18:58:51",
        "sec": 742,
        "why": "box frozen ~742s since 2026-11-20 18:46:28 (VM hibernated; wall jumped, monotonic did not)",
        "listener_restart": "18:58:54 then 18:59:10 after SSL EOF",
        "listener_pid": 1444068,
        "listener_started": "18:59:19",
        "stats": "84378421..84378619",
        "span": 199,
        "last_stats": "84378420 at 18:46:00",
        "next_stats": "84378620 at 18:59:51",
        "wall_s": 831,
        "official_fill": {room: gaps["freeze_1846"][room]["fill"] for room in ROOMS},
        "filled_by": "First pass through 84378600 plus just-published 84378600 covers W46N8/W47N8/W45N8/W47N7 fully in this gap (199/199). W45N7 171/199 missing 84378423..84378450 (28t) is official empty-no-creep (GET 200 on W45N7@84378400), not a 404.",
        "told": False,
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1900",
        "note": "Left to 1h patrol. This run did not itself restart the listener (run_listener.sh auto-restarted after the freeze).",
    },
    "new_short_listener_gap": None,
    "already_told_box_freeze_in_window": None,
    "already_recorded_untold_box_freeze_in_window": None,
    "already_recorded_untold_short_listener_gap_in_window": None,
    "aged_out_already_told_short_listener_gap": None,
    "new_official_404": [],
    "already_recorded_untold_in_window_404": [],
    "already_told_in_window_404": [{
        "chunk": "W47N7@84378000",
        "hole": "84378001..84378100",
        "live_ticks_present": "none (0t)",
        "still_404_after": "this run confirm 19:05:00 gt=84378694 and retry2 19:07:31 gt=84378730 (also still 404 after 18:30 just-published GET 18:34:23 gt=84378249, retry 18:37:50 gt=84378302, and retry2 18:40:14 gt=84378336, and concurrent patrol wrap_up GET ~18:30)",
        "db": holes["W47N7@84378000"],
        "told": True,
        "told_by": "1h patrol _patrol_2026-11-20_1819 ~18:31",
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1830",
    }],
    "aged_out_already_told_404_not_retried": [
        "W46N8@84377600", "W47N8@84377100", "W45N7@84376800", "W46N8@84376100",
        "W45N8@84375300", "W45N7@84373700", "W47N8@84373800", "W45N7@84373300",
        "W47N7@84373200", "W46N8@84371600",
    ],
    "prior_told_box_freeze_aged_out": {
        "from": "2026-11-20 17:43:34", "to": "2026-11-20 18:02:53", "sec": 1158,
        "stats": "84377521..84377819", "span": 299,
        "official_fill": {room: gaps["freeze_1743"][room]["fill"] for room in ROOMS},
        "told": True, "told_by": "1h patrol _patrol_2026-11-20_1819 ~18:31",
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1800",
        "aged_out_of_window_start": 84377901,
        "note": "W46N8 still missing 84377601..84377700 (100t) because already-told official 404 W46N8@84377600 remains unfilled. Aged out of this window start 84377901 and was not retried.",
    },
    "also_prior_told_box_freeze_aged_out": {
        "from": "2026-11-20 17:09:11", "to": "2026-11-20 17:26:01", "sec": 1005,
        "stats": "84377041..84377289", "span": 249, "official_fill": FILL_1709,
        "told": True, "told_by": "1h patrol _patrol_2026-11-20_1725 ~17:40",
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1730",
        "aged_out_of_window_start": 84377901,
        "note": "W47N8 still missing 84377101..84377200 (100t) because already-told official 404 W47N8@84377100 remains unfilled.",
    },
    "also_aged_out_already_told_box_freeze_1645": {
        "from": "2026-11-20 16:45:36", "to": "2026-11-20 16:56:32", "sec": 647,
        "stats": "84376701..84376869", "span": 169, "official_fill": FILL_1645,
        "told": True, "told_by": "1h patrol _patrol_2026-11-20_1725 ~17:40",
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1700",
        "aged_out_of_window_start": 84377901,
        "note": "W45N7 still missing 84376801..84376869 (69t) because already-told official 404 W45N7@84376800 remains unfilled.",
    },
    "aged_out_already_told_box_freeze": {
        "from": "2026-11-20 16:17:08", "to": "2026-11-20 16:22:02", "sec": 289,
        "stats": "84376291..84376369", "span": 79, "told": True,
        "told_by": "1h patrol _patrol_2026-11-20_1624 ~16:31",
        "first_recorded_by": "1h patrol _patrol_2026-11-20_1624",
        "aged_out_of_window_start": 84377901,
    },
    "also_aged_out_already_told_box_freeze_1544": {
        "from": "2026-11-20 15:44:21", "to": "2026-11-20 16:03:39", "sec": 1152,
        "stats": "84375811..84376109", "span": 299, "told": True,
        "told_by": "1h patrol _patrol_2026-11-20_1624 ~16:31",
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1600",
        "aged_out_of_window_start": 84377901,
    },
    "also_aged_out_already_told_box_freeze_1515": {
        "from": "2026-11-20 15:15:12", "to": "2026-11-20 15:26:38", "sec": 686,
        "stats": "84375391..84375569", "span": 179, "told": True,
        "told_by": "1h patrol _patrol_2026-11-20_1526 ~15:29",
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1530",
        "aged_out_of_window_start": 84377901,
    },
    "listener": {
        "single_slot": True, "roomSlot": live.get("roomSlot"), "rot": rot,
        "pid": 1444068, "started": "18:59:19", "parent": 4035476, "yield": False,
        "restarted_this_run": False,
        "auto_restart": "18:58:54 after box freeze 18:46:28-18:58:51; SSL EOF 18:59:10 then restart 18:59:10; listener.py started 18:59:19",
    },
    "war_cmd_pulse_restarted": False,
    "concurrent_1h_patrol": None,
    "cpu_tip": tips["creep_cpu"],
    "path_tip": tips["path_arrivals"],
    "room_stats_tip": tips["room_stats"],
}

(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + NL)
shutil.copy2(DIR / "history_backfill.json", STATE / "history_backfill.json")

first = (DIR / "history_backfill_first_attempt.txt").read_text().rstrip() + NL
fill1846 = gaps["freeze_1846"]
fill1743 = gaps["freeze_1743"]
wrap = (
    f"---- wrap {AT} ----" + NL
    + "confirm 19:05:00 gt=84378694 still_404 W47N7@84378000 inserted=0. retry2 19:07:31 gt=84378730 still_404 W47N7@84378000 inserted=0. Already-told leftover official 404 W47N7@84378000 remains unfilled (hole 84378001..84378100, no live ticks; first recorded by the 18:30 half-hour, told by the 18:31 1h patrol). Aged-out already-told 404s W46N8@84377600, W47N8@84377100, W45N7@84376800, W46N8@84376100, W45N8@84375300, W45N7@84373700, W47N8@84373800, W45N7@84373300, W47N7@84373200, W46N8@84371600 were not retried." + NL
    + "tick_s_first=4.35571 printed=4.356 in_use=4.35571 (first) ts_realigned_first=10879 corrective=0 (later-mean-robust 4.17331 refused as worse vs live-anchor first; over45 vs first=0)" + NL
    + "coverage official_recovered=3197/3500 empty_no_creep=203 official_404=100" + NL
    + f"just-published 84378600 at {jp.get('at')} game.time={jp.get('game_time')} all_five_200={all_five_200} actual_inserted={actual_total} ticks 84378601..84378700 ({jp_distinct}); script inserted={script_total}{mismatch_suffix}" + NL
    + f"inserted_window={INSERTED_WINDOW} inserted_total={INSERTED_TOTAL}" + NL
    + "ok_quiet=True" + NL
)
(DIR / "history_backfill_now.txt").write_text(first + NL + wrap)
(DIR / "history_backfill.txt").write_text(first + NL)
shutil.copy2(DIR / "history_backfill_now.txt", STATE / "_halfhour_backfill_now.txt")

ua = cov["unique_after"]
slot = live.get("roomSlot")
verify = NL.join([
    f"{AT} verify",
    "first pass game.time=84378667 published_bases=84377900..84378500 reconstructed 84377901..84378600 (700) creep_rows=26141 missing_chunks=1 W47N7@84378000",
    f"already_in_db=11036 inserted_first=15105 confirm=0 retry2=0 just_script={script_total} just_actual={actual_total} inserted_window={INSERTED_WINDOW} inserted_total={INSERTED_TOTAL}",
    "per_room first W46N8:700t/3788new W47N8:700t/4603new W45N8:700t/2578new W45N7:700t/747new W47N7:600t/3389new. First pass run by this 30-min backfill (no concurrent 1h patrol). In-window official 404 after confirm+retry2: W47N7@84378000 (already told).",
    "tick_s_first=4.35571 printed=4.356 in_use=4.35571 (first) ts_realigned_first=10879 corrective=0 (later-mean-robust 4.17331 refused as worse vs live-anchor first; over45 vs first=0)",
    f"coverage official_recovered=3197/3500 empty_no_creep=203 official_404=100 unique_room_ticks={ua['distinct_room_ticks']} unique_creep_tick_rows={ua['unique_creep_tick_rows']} (no dups).",
    "Official 404 in this first-pass window after confirm+retry2: already-told leftover W47N7@84378000 still 404 after this run confirm 19:05:00 gt=84378694 and retry2 19:07:31 gt=84378730 (also still 404 after 18:30 just-published retries and 1h patrol wrap_up ~18:30); no live ticks present, hole 100t 84378001..84378100; told=true by the 18:31 1h patrol, first recorded by the 18:30 half-hour. Official empty-no-creep in-window: W45N7 203t 84378027, 84378029..84378202, 84378423..84378450 (GET 200, not a 404). W46N8/W47N8/W45N8 700/700; W45N7 497/700 (203 official empty-no-creep); W47N7 600/700 (100 official 404).",
    f"just-published 84378600 at {jp.get('at')} game.time={jp.get('game_time')} all_five_200={all_five_200} actual_inserted={actual_total} ticks 84378601..84378700 ({jp_distinct}); script inserted={script_total}{mismatch_suffix}",
    f"NEW box freeze 18:46:28-18:58:51 (742s; box_pauses.jsonl); listener auto-restart 18:58:54, SSL EOF 18:59:10 then restart 18:59:10, pid 1444068 started 18:59:19. STATS 84378421..84378619 (199t) wall 831s from last STATS 84378420 at 18:46:00 to next STATS 84378620 at 18:59:51. Official-filled W46N8 {fill1846['W46N8']['fill']}, W47N8 {fill1846['W47N8']['fill']}, W45N8 {fill1846['W45N8']['fill']}, W45N7 {fill1846['W45N7']['fill']}, W47N7 {fill1846['W47N7']['fill']} via first pass through 84378600 plus just-published 84378600. W45N7 missing 84378423..84378450 (28t) is official empty-no-creep (GET 200 on W45N7@84378400), not a 404. told=false, first recorded by this 19:00 half-hour, left to 1h patrol. This run did not itself restart the listener.",
    f"Prior box freeze 17:43:34-18:02:53 STATS 84377521..84377819 aged out of window start 84377901 (already told by the 18:31 1h patrol; official-filled W46N8 {fill1743['W46N8']['fill']}, W47N8 {fill1743['W47N8']['fill']}, W45N8 {fill1743['W45N8']['fill']}, W45N7 {fill1743['W45N7']['fill']}, W47N7 {fill1743['W47N7']['fill']}). W46N8 missing 84377601..84377700 (100t) because already-told official 404 W46N8@84377600 still unfilled; aged out and not retried.",
    "Prior box freeze 17:09:11-17:26:01 STATS 84377041..84377289 aged out of window start 84377901 (already told by the 17:40 1h patrol). W47N8 missing 84377101..84377200 (100t) because already-told official 404 W47N8@84377100 still unfilled.",
    "Prior box freeze 16:45:36-16:56:32 STATS 84376701..84376869 aged out of window start 84377901 (already told by the 17:40 1h patrol; official-fill remains W46N8 169/169, W47N8 169/169, W45N8 169/169, W45N7 100/169, W47N7 169/169). W45N7 missing 84376801..84376869 (69t) because already-told official 404 W45N7@84376800 still unfilled.",
    "Prior box freeze 16:17:08-16:22:02 STATS 84376291..84376369 aged out of window start 84377901 (already told by the 16:31 1h patrol).",
    "Prior box freeze 15:44:21-16:03:39 STATS 84375811..84376109 aged out of window start 84377901 (already told by the 16:31 1h patrol).",
    "Prior box freeze 15:15:12-15:26:38 STATS 84375391..84375569 aged out of window start 84377901 (already told by the 15:29 1h patrol).",
    f"listener single_slot=True roomSlot={slot} pid=1444068 started 18:59:19 after auto-restart 18:58:54/18:59:10; parent run_listener.sh pid 4035476 from Nov 13; this run did not restart listener or war_cmd/pulse; no second listener; yield absent. cpu_tip={tips['creep_cpu']} path_tip={tips['path_arrivals']} room_stats_tip={tips['room_stats']}.",
    "",
])
(DIR / "verify.txt").write_text(verify)
shutil.copy2(DIR / "verify.txt", STATE / "_halfhour_backfill_verify.txt")
shutil.copy2(DIR / "backfill_retry2.txt", STATE / "_halfhour_backfill_retry2_1900.txt")
# also keep a copy of the runner used this run
(DIR / "wrapup_write.py").write_text("# wrapup executed inline for 1900; status written " + AT + NL)

wrapup = NL.join([
    f"{AT} wrapup ok",
    "wrote history_backfill.json history_backfill_now.txt verify.txt",
    f"inserted={INSERTED_FIRST}+0+0+just{actual_total} coverage=3197/3500 tick_s_in_use=4.35571",
    f"ok_line ok_quiet=True coverage=3197/3500 inserted_total={INSERTED_TOTAL}",
    "",
])
(DIR / "wrapup_run.txt").write_text(wrapup)
(DIR / "wrapup_run_stdout.txt").write_text(wrapup)
print(wrapup)
print("wrote wrapup ok all_five_200=", all_five_200, "inserted_total", INSERTED_TOTAL)
